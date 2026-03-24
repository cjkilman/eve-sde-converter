import sqlite3
import csv
import os

# --- CONFIGURATION ---
DB_NAME = "eve.db"

# Points to your clean repo next door
OUTPUT_DIR = "../eve-sde-dump" 

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

    conn.close()
    print(f"\n--- Full Export Complete. Check the folder: {OUTPUT_DIR} ---")

if __name__ == "__main__":
    export_all_tables()