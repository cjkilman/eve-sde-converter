import sqlite3
import csv
import os

def build_repro_bonuses(db_path="sqlite-latest.sqlite", output_file="specializedReprocessingBonuses.csv"):
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found. Run the main SDE converter first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Attribute 379: 'refiningYieldMutator' (Used by Skills and Implants)
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
            
            # EVE stores 4% as 4.0. We convert this to the 1.04 format for the spreadsheet math.
            multiplier = 1.0 + (raw_bonus / 100.0)
            writer.writerow([name, category, round(multiplier, 4)])

        # --- Structure/Rig Base Yields ---
        # Structures use location-based dogma that is brutal to query cleanly.
        # Injecting the known base yields here keeps the Google Sheet Omni-Map perfect.
        writer.writerow(['Standard NPC Station', 'Rig_Base_Scrap', 0.50])
        writer.writerow(['Unrigged Structure', 'Rig_Base_Scrap', 0.50])
        writer.writerow(['Athanor (T1 Ore Rig - High Sec)', 'Rig_Base_Ore', 0.51])
        writer.writerow(['Athanor (T2 Ore Rig - High Sec)', 'Rig_Base_Ore', 0.52])
        writer.writerow(['Tatara (T1 Ore Rig - High Sec)', 'Rig_Base_Ore', 0.52])
        writer.writerow(['Tatara (T2 Ore Rig - High Sec)', 'Rig_Base_Ore', 0.54])
        writer.writerow(['Tatara (T2 Ore Rig - Low/Null/WH)', 'Rig_Base_Ore', 0.552])

    print(f"Generated {output_file} with {len(results)} dynamic modifiers.")
    conn.close()

if __name__ == "__main__":
    build_repro_bonuses()