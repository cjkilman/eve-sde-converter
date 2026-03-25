import sqlite3
import csv
import os

# --- CONFIGURATION ---
# Matches the standard output of the eve-sde-converter project
DB_NAME = "eve.db"
OUTPUT_DIR = "../eve-sde-dump" 

def export_repro_bonuses(conn, output_dir):
    """
    Generates specializedReprocessingBonuses.csv by querying the SDE 
    dogma system for dynamic multipliers.
    """
    print("Generating specializedReprocessingBonuses.csv (Fully Dynamic)...")
    cursor = conn.cursor()
    all_bonus_rows = []

    try:
        # 1. Global Skills & Implants
        # Attribute 379: refiningYieldMutator
        query_global = """
            SELECT t.typeName, c.categoryName, COALESCE(a.valueFloat, a.valueInt) as bonus
            FROM dgmTypeAttributes a
            JOIN invTypes t ON a.typeID = t.typeID
            JOIN invGroups g ON t.groupID = g.groupID
            JOIN invCategories c ON g.categoryID = c.categoryID
            WHERE a.attributeID = 379 AND t.published = 1 AND c.categoryName IN ('Skill', 'Implant')
        """
        cursor.execute(query_global)
        for name, cat, val in cursor.fetchall():
            all_bonus_rows.append([name, cat, round(1.0 + (val / 100.0), 4)])

        # 2. Specialized Ore/Ice Skills (Veldspar Processing, etc.)
        # Attribute 158: refiningYieldPercent
        query_ore_skills = """
            SELECT t.typeName, 'Skill_Specialized', COALESCE(a.valueFloat, a.valueInt) as bonus
            FROM dgmTypeAttributes a
            JOIN invTypes t ON a.typeID = t.typeID
            WHERE a.attributeID = 158 AND t.published = 1
        """
        cursor.execute(query_ore_skills)
        for name, cat, val in cursor.fetchall():
            all_bonus_rows.append([name, cat, round(1.0 + (val / 100.0), 4)])

        # 3. Structure Hull Bonuses (Athanor/Tatara Role Bonuses)
        # Attribute 2795: strRefiningYieldBonus
        query_hulls = """
            SELECT t.typeName, 'Hull_Bonus', COALESCE(a.valueFloat, a.valueInt) as bonus
            FROM dgmTypeAttributes a
            JOIN invTypes t ON a.typeID = t.typeID
            WHERE a.attributeID = 2795 AND t.published = 1 AND t.typeName IN ('Athanor', 'Tatara')
        """
        cursor.execute(query_hulls)
        for name, cat, val in cursor.fetchall():
            all_bonus_rows.append([name, cat, round(1.0 + (val / 100.0), 4)])

        # 4. Rig Tier Bonuses (Standup Refining Rigs)
        # Attribute 717: reprocessingYieldBonus
        query_rigs = """
            SELECT 
                CASE WHEN t.typeName LIKE '% II' THEN 'Tech 2 Refining Rig' ELSE 'Tech 1 Refining Rig' END as Tier,
                'Rig_Tier_Bonus',
                MAX(COALESCE(a.valueFloat, a.valueInt)) as bonus
            FROM dgmTypeAttributes a
            JOIN invTypes t ON a.typeID = t.typeID
            WHERE a.attributeID = 717 AND t.published = 1 AND t.typeName LIKE 'Standup % Reprocessing %'
            GROUP BY Tier
        """
        cursor.execute(query_rigs)
        for name, cat, val in cursor.fetchall():
            all_bonus_rows.append([name, cat, round(val / 100.0, 4)])

        # 5. Core Constants (Unchangeables in SDE)
        all_bonus_rows.append(['Base Yield', 'Base_Value', 0.50])
        all_bonus_rows.append(['High Sec', 'Sec_Multiplier', 1.00])
        all_bonus_rows.append(['Low Sec', 'Sec_Multiplier', 1.06])
        all_bonus_rows.append(['Null/WH', 'Sec_Multiplier', 1.12])

        # 6. Faction/Special Edition Rigs (Thukker, Outpost, etc.)
        query_faction_rigs = """
            SELECT 
                t.typeName, 
                'Rig_Faction_Bonus', 
                COALESCE(a.valueFloat, a.valueInt) / 100.0
            FROM dgmTypeAttributes a
            JOIN invTypes t ON a.typeID = t.typeID
            WHERE a.attributeID = 717 
            AND t.published = 1 
            AND t.typeName LIKE 'Standup %'
            AND t.typeName NOT LIKE '% I' 
            AND t.typeName NOT LIKE '% II'
        """
        cursor.execute(query_faction_rigs)
        for name, cat, val in cursor.fetchall():
            all_bonus_rows.append([name, cat, round(val, 4)])

        # Write to CSV
        file_path = os.path.join(output_dir, "specializedReprocessingBonuses.csv")
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ItemName', 'Category', 'Multiplier'])
            writer.writerows(all_bonus_rows)

        print(f"  -> Success! Wrote {len(all_bonus_rows)} modifiers to {file_path}")

    except Exception as e:
        print(f"  [!] Error generating repro bonuses: {e}")

def export_all_tables():
    """Loops through all SQLite tables and exports them to individual CSV files."""
    if not os.path.exists(DB_NAME):
        print(f"CRITICAL ERROR: {DB_NAME} not found. Build the database first.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get list of all user-defined tables
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
            print(f"Exported {table_name}.csv")
        except Exception as e:
            print(f"  [!] Error exporting {table_name}: {e}")

    print("\n--- Starting Custom Data Exports ---")
    export_repro_bonuses(conn, OUTPUT_DIR)
    conn.close()

if __name__ == "__main__":
    export_all_tables()