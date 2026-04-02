import sqlite3
import csv
import os

# --- CONFIGURATION ---
DB_NAME = "eve.db"

# Points to your clean repo next door
OUTPUT_DIR = "../eve-sde-dump" 

def is_tq_safe(text):
    if not text: return True
    return all(ord(char) < 128 for char in text)

def export_repro_bonuses(conn, output_dir):
    """Generates the custom specializedReprocessingBonuses.csv for the Google Sheet Omni-Map."""
    print("Generating specializedReprocessingBonuses.csv (Custom Omni-Map)...")
    cursor = conn.cursor()
    
    # Query Dogma for Attribute 379: 'refiningYieldMutator' (Skills & Implants)
    query = """
        SELECT 
            t.typeName, 
            c.categoryName, 
            COALESCE(a.valueFloat, a.valueInt) as bonusValue
        FROM dgmTypeAttributes a
        JOIN invTypes t ON a.typeID = t.typeID
        JOIN invGroups g ON t.groupID = g.groupID
        JOIN invCategories c ON g.categoryID = c.categoryID
        WHERE a.attributeID = 379 
        AND t.published = 1
        AND c.categoryName IN ('Skill', 'Implant')
    """
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        file_path = os.path.join(output_dir, "specializedReprocessingBonuses.csv")
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ItemName', 'Category', 'Multiplier'])

            for row in results:
                name, category, raw_bonus = row

                # THE GATEKEEPER: Ensure no "Serenity" artifacts hit the Google Sheet
                if not is_tq_safe(name):
                    continue
                
                # Convert EVE's integer percentage (e.g., 4.0) to multiplier (1.04)
                multiplier = 1.0 + (raw_bonus / 100.0)
                writer.writerow([name, category, round(multiplier, 4)])

            # --- Inject Static Structure/Rig Base Yields ---
            writer.writerow(['Standard NPC Station', 'Rig_Base_Scrap', 0.50])
            writer.writerow(['Unrigged Structure', 'Rig_Base_Scrap', 0.50])
            writer.writerow(['Athanor (T1 Ore Rig - High Sec)', 'Rig_Base_Ore', 0.51])
            writer.writerow(['Athanor (T2 Ore Rig - High Sec)', 'Rig_Base_Ore', 0.52])
            writer.writerow(['Tatara (T1 Ore Rig - High Sec)', 'Rig_Base_Ore', 0.52])
            writer.writerow(['Tatara (T2 Ore Rig - High Sec)', 'Rig_Base_Ore', 0.54])
            writer.writerow(['Tatara (T2 Ore Rig - Low/Null/WH)', 'Rig_Base_Ore', 0.552])

        print(f"  -> Success! Wrote {len(results)} dynamic modifiers and structure bases to {file_path}")
        
    except Exception as e:
        print(f"  [!] Error generating repro bonuses: {e}")

def export_slim_planets(conn, output_dir):
    """Generates a lean SDE_Planets.csv for Google Sheets name resolution."""
    print("Generating SDE_Planets.csv (Slim Celestial Map)...")
    cursor = conn.cursor()
    
    # We join mapDenormalize with mapSolarSystems to get clean human names
    # Modern SDE often stores Planet Name as [System Name] + [Celestial Index]
    query = """
        SELECT 
            d.itemID as planetID,
            s.solarSystemName || ' ' || 
            CASE d.celestialIndex 
                WHEN 1 THEN 'I' WHEN 2 THEN 'II' WHEN 3 THEN 'III' WHEN 4 THEN 'IV' 
                WHEN 5 THEN 'V' WHEN 6 THEN 'VI' WHEN 7 THEN 'VII' WHEN 8 THEN 'VIII' 
                WHEN 9 THEN 'IX' WHEN 10 THEN 'X' ELSE d.celestialIndex END as planetName,
            s.solarSystemName
        FROM mapDenormalize d
        JOIN mapSolarSystems s ON d.solarSystemID = s.solarSystemID
        WHERE d.groupID = (SELECT groupID FROM invGroups WHERE groupName = 'Planet')
    """
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        file_path = os.path.join(output_dir, "SDE_Planets.csv")
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['planetID', 'planetName', 'solarSystemName'])
            writer.writerows(results)
            
        print(f"  -> Success! Wrote {len(results)} planets to {file_path}")
    except Exception as e:
        print(f"  [!] Error generating slim planets: {e}")

def export_ore_skill_map(conn, output_dir):
    """Generates the bridge between Ore/Ice and the 2% bonus skills."""
    print("Generating SDE_oreProcessingGroups.csv (The Skill Bridge)...")
    cursor = conn.cursor()
    
    query = """
    SELECT 
        it.typeID,
        CASE 
            WHEN ig.groupID IN (450, 451, 452, 453) THEN 'Simple Ore Processing'
            WHEN ig.groupID IN (454, 455, 456, 457, 458) THEN 'Coherent Ore Processing'
            WHEN ig.groupID IN (459, 460, 461) THEN 'Variegated Ore Processing'
            WHEN ig.groupID IN (467, 468, 469) THEN 'Complex Ore Processing'
            WHEN ig.groupID = 465 THEN 'Ice Processing'
            WHEN ig.categoryID = 65 THEN 'Moon Ore Processing'
            WHEN ig.categoryID = 16 THEN 'Gas Cloud Harvesting'
            ELSE 'Scrapmetal Processing'
        END as requiredSkill
    FROM invTypes it
    JOIN invGroups ig ON it.groupID = ig.groupID
    WHERE ig.categoryID IN (16, 25, 42, 65) 
    AND ig.groupID != 4030 
    """
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        file_path = os.path.join(output_dir, "SDE_oreProcessingGroups.csv")
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['typeID', 'requiredSkill'])
            writer.writerows(results)
            
        print(f"  -> Success! Wrote {len(results)} skill mappings to {file_path}")
    except Exception as e:
        print(f"  [!] Error generating skill map: {e}")

def export_all_tables():
    # 1. Check for Database
    if not os.path.exists(DB_NAME):
        print(f"CRITICAL ERROR: {DB_NAME} not found.")
        print("Please run the builder (run_windows.ps1) first.")
        return

    # 2. Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"Created output directory: {OUTPUT_DIR}")
        except OSError as e:
            print(f"Error creating directory {OUTPUT_DIR}: {e}")
            return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 3. Get list of ALL tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"--- Found {len(tables)} tables. Exporting to '{OUTPUT_DIR}'... ---")

    for table_tuple in tables:
        table_name = table_tuple[0]
        
        # Skip internal system tables
        if table_name.startswith("sqlite_") or table_name == "alembic_version":
            continue

        print(f"Exporting {table_name}.csv...")
        
        # Define the full path to the separate folder
        file_path = os.path.join(OUTPUT_DIR, f"{table_name}.csv")
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Get Headers
            headers = [description[0] for description in cursor.description]
            
            # Write Data to the SPECIFIC path
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                if rows:
                    writer.writerows(rows)
                
        except Exception as e:
            print(f"  [!] Error exporting {table_name}: {e}")

    # --- 4. GENERATE CUSTOM OMNI-MAP CSV ---
    print("\n--- Starting Custom Data Exports ---")
    export_repro_bonuses(conn, OUTPUT_DIR)
    export_slim_planets(conn, OUTPUT_DIR)
    export_ore_skill_map(conn, OUTPUT_DIR)
    
    conn.close()
    print(f"\n--- Full Export Complete. Check the folder: {OUTPUT_DIR} ---")

if __name__ == "__main__":
    export_all_tables()