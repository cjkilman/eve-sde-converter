import sqlite3
import csv
import os

# Updated to match the standard output of the converter project
def build_repro_bonuses(db_path="eve.db", output_file="specializedReprocessingBonuses.csv"):
    if not os.path.exists(db_path):
        # Fallback check for common SDE filenames
        if os.path.exists("eve-stripped.db"):
            db_path = "eve-stripped.db"
        else:
            print(f"Error: {db_path} not found.")
            return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Attribute 379: 'refiningYieldMutator'
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

    cursor.execute(query)
    results = cursor.fetchall()

    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ItemName', 'Category', 'Multiplier'])

        for row in results:
            name, category, raw_bonus = row
            # Converts SDE format (5.0) to multiplier format (1.05)
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
        
        # --- Pre-Calculated Presets (Optional but helpful) ---
        writer.writerow(['NPC Station', 'Net_Facility_Base', 0.50])
        writer.writerow(['Tatara T2 HighSec', 'Net_Facility_Base', 0.5408]) # 0.5 * 1.04 * 1.04

    print(f"Generated {output_file} with {len(results) + 8} modifiers.")
    conn.close()

if __name__ == "__main__":
    build_repro_bonuses()