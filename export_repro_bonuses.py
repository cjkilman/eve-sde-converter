import sqlite3
import csv
import os

# --- CONFIGURATION ---
DB_NAME = "eve.db"
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
                multiplier = 1.0 + (raw_bonus / 100.0)
                writer.writerow([name, category, round(multiplier, 4)])

            # --- Base Components ---
            writer.writerow(['Base Yield', 'Base_Value', 0.50])
            
            # --- Structures ---
            writer.writerow(['Athanor', 'Structure_Bonus', 1.02])
            writer.writerow(['Tatara', 'Structure_Bonus', 1.04])

            # --- Rigs ---
            writer.writerow(['T1 Refining Rig', 'Rig_Multiplier', 1.01])
            writer.writerow(['T2 Refining Rig', 'Rig_Multiplier', 1.03])

            # --- Security Zone Multipliers ---
            writer.writerow(['High Sec', 'Security_Multiplier', 1.00])
            writer.writerow(['Low Sec', 'Security_Multiplier', 1.06])
            writer.writerow(['Null/WH', 'Security_Multiplier', 1.12])
            
            # --- Pre-Calculated Presets ---
            writer.writerow(['NPC Station', 'Net_Facility_Base', 0.50])
            writer.writerow(['Athanor T2 HighSec', 'Net_Facility_Base', 0.5202]) # 0.5 * 1.02 * 1.02
            writer.writerow(['Tatara T2 HighSec', 'Net_Facility_Base', 0.5408])  # 0.5 * 1.04 * 1.04

        print(f"  -> Success! Wrote {len(results) + 9} modifiers to {file_path}")
        
    except Exception as e:
        print(f"  [!] Error generating repro bonuses: {e}")

def export_all_tables():
    if not os.path.exists(DB_NAME):
        print(f"CRITICAL ERROR: {DB_NAME} not found.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table_tuple in tables:
        table_name = table_tuple[0]
        if table_name.startswith("sqlite_") or table_name == "alembic_version":
            continue

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
    conn.close()

if __name__ == "__main__":
    export_all_tables()