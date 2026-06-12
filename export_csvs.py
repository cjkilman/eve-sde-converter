import sqlite3
import csv
import os

# --- CONFIGURATION ---
DB_NAME = "eve.db"
OUTPUT_DIR = "../eve-sde-dump" 

def is_tq_safe(text):
    if not text: return True
    return all(ord(char) < 128 for char in text)

def export_repro_bonuses(conn, output_dir):
    """Generates the custom specializedReprocessingBonuses.csv for the Google Sheet Omni-Map."""
    print("Generating specializedReprocessingBonuses.csv (Custom Omni-Map)...")
    cursor = conn.cursor()
    
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
                if not is_tq_safe(name):
                    continue
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

def export_pi_structures(conn, output_dir):
    """Generates SDE_PI_Structures.csv for Planetary Infrastructure pins."""
    print("Generating SDE_PI_Structures.csv (Planetary Infrastructure)...")
    cursor = conn.cursor()
    
    query = """
        SELECT 
            t.typeID,
            t.groupID,
            t.typeName,
            t.volume,
            t.capacity
        FROM invTypes t
        JOIN invGroups g ON t.groupID = g.groupID
        WHERE g.categoryID = 41
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        file_path = os.path.join(output_dir, "SDE_PI_Structures.csv")
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['typeID', 'groupID', 'typeName', 'volume', 'capacity'])
            writer.writerows(results)

        print(f"  -> Success! Wrote {len(results)} PI structures to {file_path}")
    except Exception as e:
        print(f"  [!] Error generating PI structures map: {e}")

def export_encryptor_matrix(conn, output_dir):
    """Generates the custom SDE_Encryptor_Matrix.csv mapping Type IDs to their Dogma multipliers."""
    print("Generating SDE_Encryptor_Matrix.csv (The Encryptor Matrix)...")
    cursor = conn.cursor()
    
    # Using Market Group 1873 (Decryptors) to ensure clean data
    query = """
        SELECT 
            t.typeID,
            t.typeName,
            MAX(CASE WHEN ta.attributeID = 1112 THEN COALESCE(ta.valueFloat, ta.valueInt) END) as probModifier,
            MAX(CASE WHEN ta.attributeID = 1124 THEN COALESCE(ta.valueFloat, ta.valueInt) END) as runModifier,
            MAX(CASE WHEN ta.attributeID = 1113 THEN COALESCE(ta.valueFloat, ta.valueInt) END) as meModifier,
            MAX(CASE WHEN ta.attributeID = 1114 THEN COALESCE(ta.valueFloat, ta.valueInt) END) as teModifier
        FROM invTypes t
        LEFT JOIN dgmTypeAttributes ta ON t.typeID = ta.typeID
        WHERE t.marketGroupID = 1873 
        AND t.published = 1
        GROUP BY t.typeID, t.typeName
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        file_path = os.path.join(output_dir, "SDE_Encryptor_Matrix.csv")
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['typeID', 'typeName', 'probModifier', 'runModifier', 'meModifier', 'teModifier'])
            writer.writerow([0, 'None', 1.0, 0, 0, 0])
            
            for row in results:
                type_id, name, prob, run, me, te = row
                if not is_tq_safe(name): continue
                    
                prob_val = round(prob, 2) if prob is not None else 1.0
                run_val  = int(run) if run is not None else 0
                me_val   = int(me) if me is not None else 0
                te_val   = int(te) if te is not None else 0
                writer.writerow([type_id, name, prob_val, run_val, me_val, te_val])
                
        print(f"  -> Success! Wrote {len(results)} encryptor profiles to {file_path}")
    except Exception as e:
        print(f"  [!] Error generating encryptor matrix: {e}")

def export_all_tables():
    if not os.path.exists(DB_NAME):
        print(f"CRITICAL ERROR: {DB_NAME} not found.")
        print("Please run the builder (run_windows.ps1) first.")
        return

    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"Created output directory: {OUTPUT_DIR}")
        except OSError as e:
            print(f"Error creating directory {OUTPUT_DIR}: {e}")
            return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"--- Found {len(tables)} tables. Exporting to '{OUTPUT_DIR}'... ---")

    for table_tuple in tables:
        table_name = table_tuple[0]
        
        if table_name.startswith("sqlite_") or table_name == "alembic_version":
            continue

        print(f"Exporting {table_name}.csv...")
        file_path = os.path.join(OUTPUT_DIR, f"{table_name}.csv")
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            headers = [description[0] for description in cursor.description]
            
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                if rows:
                    writer.writerows(rows)
                
        except Exception as e:
            print(f"  [!] Error exporting {table_name}: {e}")

    print("\n--- Starting Custom Data Exports ---")
    export_repro_bonuses(conn, OUTPUT_DIR)
    export_slim_planets(conn, OUTPUT_DIR)
    export_ore_skill_map(conn, OUTPUT_DIR)
    export_pi_structures(conn, OUTPUT_DIR)
    export_encryptor_matrix(conn, OUTPUT_DIR)
    
    conn.close()
    print(f"\n--- Full Export Complete. Check the folder: {OUTPUT_DIR} ---")

if __name__ == "__main__":
    export_all_tables()