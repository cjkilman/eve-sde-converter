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
# Safety net for items with no blueprints
# ==========================================
CUSTOM_INJECTIONS = {
    27: [ 
        {'materialTypeID': 34, 'quantity': 2224},
        {'materialTypeID': 35, 'quantity': 2224},
        {'materialTypeID': 36, 'quantity': 368}
    ]
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

    material_rows = []
    processed_types = set()
    
    # 1. LOAD OFFICIAL MATERIALS
    if os.path.exists(targetPath):
        print(f"  Opening {targetPath}")
        with open(targetPath,'r', encoding='utf-8') as yamlstream:
            materials = load(yamlstream, Loader=SafeLoader)
            if materials:
                print(f"  Processing {len(materials)} official type materials")
                for typeid in materials:
                    if 'materials' in materials[typeid]:
                        # Ensure ID is an integer for set lookups
                        t_id = int(typeid)
                        processed_types.add(t_id)
                        for material in materials[typeid]['materials']:
                            material_rows.append({
                                'typeID': t_id,
                                'materialTypeID': int(material['materialTypeID']),
                                'quantity': int(material['quantity'])
                            })
            else:
                print("  Warning: typeMaterials.yaml is empty.")
    else:
        print(f"  Warning: {targetPath} not found.")

    # 2. BLUEPRINT FALLBACK
    if os.path.exists(blueprintPath):
        print(f"  Opening {blueprintPath} for fallback yields...")
        with open(blueprintPath, 'r', encoding='utf-8') as bpstream:
            blueprints = load(bpstream, Loader=SafeLoader)
            if blueprints:
                fallback_count = 0
                for bpID in blueprints:
                    activities = blueprints[bpID].get('activities', {})
                    manuf = activities.get('manufacturing', {})
                    
                    products = manuf.get('products', [])
                    mats = manuf.get('materials', [])
                    
                    if products and mats:
                        # Safety check: ensure at least one product exists
                        productTypeID = int(products[0]['typeID'])
                        
                        if productTypeID not in processed_types:
                            processed_types.add(productTypeID)
                            fallback_count += 1
                            for m in mats:
                                material_rows.append({
                                    'typeID': productTypeID,
                                    'materialTypeID': int(m['typeID']),
                                    'quantity': int(math.floor(m['quantity'] * 0.5))
                                })
                print(f"  Auto-generated fallback yields for {fallback_count} items.")
            else:
                print("  Warning: blueprints.yaml is empty.")

    # 3. MANUAL INJECTIONS
    for custom_typeid, custom_mats in CUSTOM_INJECTIONS.items():
        c_id = int(custom_typeid)
        if c_id not in processed_types:
            for mat in custom_mats:
                material_rows.append({
                    'typeID': c_id,
                    'materialTypeID': int(mat['materialTypeID']),
                    'quantity': int(mat['quantity'])
                })

    # 4. BULK INSERT
    if material_rows:
        connection.execute(invTypeMaterials.insert(), material_rows)
        print(f"  Inserted {len(material_rows)} total rows into invTypeMaterials.")

    if trans:
        trans.commit()
    print("  Done")