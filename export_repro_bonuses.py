def export_repro_bonuses(conn, output_dir):
    """Generates the custom specializedReprocessingBonuses.csv by querying the SDE for every multiplier."""
    print("Generating specializedReprocessingBonuses.csv (Fully Dynamic Omni-Map)...")
    cursor = conn.cursor()
    
    # We will collect all results into this list to write at once
    all_bonus_rows = []

    # 1. Global Skills & Implants (Reprocessing / Reprocessing Efficiency)
    # Attribute 379: refiningYieldMutator (values like 2.0 or 4.0)
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
    # Attribute 158: refiningYieldPercent (values like 2.0)
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
    # Attribute 2795: strRefiningYieldBonus (values like 2.0 or 4.0)
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
    # Attribute 717: reprocessingYieldBonus (values like 1.0 or 3.0)
    # We group by the Rig Name to handle Medium/Large/XL variations automatically
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
        all_bonus_rows.append([name, cat, round(val / 100.0, 4)]) # Rigs are exported as raw 0.01/0.03 for the stacking formula

    # 5. The "Unchangeables" (Hardcoded)
    # These are environmental or core constants not stored as item attributes
    all_bonus_rows.append(['Base Yield', 'Base_Value', 0.50])
    all_bonus_rows.append(['High Sec', 'Sec_Multiplier', 1.00])
    all_bonus_rows.append(['Low Sec', 'Sec_Multiplier', 1.06])
    all_bonus_rows.append(['Null/WH', 'Sec_Multiplier', 1.12])

    # Write final CSV
    file_path = os.path.join(output_dir, "specializedReprocessingBonuses.csv")
    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ItemName', 'Category', 'Multiplier'])
        writer.writerows(all_bonus_rows)

    print(f"  -> Success! Wrote {len(all_bonus_rows)} dynamic and core entries to {file_path}")