# -*- coding: utf-8 -*-
import os
import math
from sqlalchemy import Table
from yaml import load

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

# ==========================================
# CUSTOM MATERIAL INJECTIONS
# Still kept for items that have no blueprint at all
# ==========================================
CUSTOM_INJECTIONS = {
    # Manual overrides if needed
}

def importyaml(connection,metadata,sourcePath,language='en'):
    print("Importing Type Materials")
    invTypeMaterials = Table('invTypeMaterials',metadata)
    
    # Path Resolution
    targetPath = os.path.join(sourcePath, 'typeMaterials.yaml')
    if not os.path.exists(targetPath):
        targetPath = os.path.join(sourcePath, 'sde', 'fsd', 'typeMaterials.yaml')

    blueprintPath = os.path.join(sourcePath, 'blueprints.yaml')
    if not os.path.exists(blueprintPath):
        blueprintPath = os.path.join(sourcePath, 'sde', 'fsd', 'blueprints.yaml')

    if connection.in_transaction():
        trans = None
    else:
        trans = connection.begin()

    # 1. LOAD OFFICIAL MATERIALS
    material_rows = []
    processed_types = set()
    
    print(f"  Opening {targetPath}")
    with open(targetPath,'r', encoding='utf-8') as yamlstream:
        materials = load(yamlstream, Loader=SafeLoader)
        print(f"  Processing {len(materials)} official type materials")
        for typeid in materials:
            if 'materials' in materials[typeid]:
                processed_types.add(typeid)
                for material in materials[typeid]['materials']:
                    material_rows.append({
                        'typeID': typeid,
                        'materialTypeID': material['materialTypeID'],
                        'quantity': material['quantity']
                    })

    # 2. BLUEPRINT FALLBACK (AUTO-GRAB MISSING ITEMS)
    # Most deployables use 50% of manufacturing inputs as reprocessing yield
    if os.path.exists(blueprintPath):
        print(f"  Opening {blueprintPath} for fallback yields...")
        with open(blueprintPath, 'r', encoding='utf-8') as bpstream:
            blueprints = load(bpstream, Loader=SafeLoader)
            fallback_count = 0
            
            for bpID in blueprints:
                # Activity 1 is Manufacturing
                activities = blueprints[bpID].get('activities', {})
                manuf = activities.get('manufacturing', {})
                
                products = manuf.get('products', [])
                mats = manuf.get('materials', [])
                
                if products and mats:
                    # Identify what this blueprint actually makes
                    productTypeID = products[0]['typeID']
                    
                    # If this item is MISSING from typeMaterials.yaml, generate 50% yield
                    if productTypeID not in processed_types:
                        processed_types.add(productTypeID)
                        fallback_count += 1
                        for m in mats:
                            material_rows.append({
                                'typeID': productTypeID,
                                'materialTypeID': m['typeID'],
                                'quantity': math.floor(m['quantity'] * 0.5)
                            })
            print(f"  Auto-generated fallback yields for {fallback_count} items from blueprints.")

    # 3. MANUAL INJECTIONS
    for custom_typeid, custom_mats in CUSTOM_INJECTIONS.items():
        if custom_typeid not in processed_types:
            for mat in custom_mats:
                material_rows.append({
                    'typeID': custom_typeid,
                    'materialTypeID': mat['materialTypeID'],
                    'quantity': mat['quantity']
                })

    # 4. BULK INSERT
    if material_rows:
        connection.execute(invTypeMaterials.insert(), material_rows)
        print(f"  Inserted {len(material_rows)} total rows into invTypeMaterials.")

    if trans:
        trans.commit()
    print("  Done")