# -*- coding: utf-8 -*-
import os
from sqlalchemy import Table

from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

# ==========================================
# CUSTOM MATERIAL INJECTIONS
# Add any items here that CCP forgot to put in typeMaterials.yaml
# Format: { Item_TypeID: [ {materialTypeID: qty}, ... ] }
# ==========================================
CUSTOM_INJECTIONS = {
    27: [ # Station Container
        {'materialTypeID': 34, 'quantity': 10000}, # Replace 10000 with the actual Base Tritanium yield
        {'materialTypeID': 35, 'quantity': 2000},  # Replace with Base Pyerite
        {'materialTypeID': 36, 'quantity': 500}    # Replace with Base Mexallon (Add more lines as needed)
    ]
}

def importyaml(connection,metadata,sourcePath,language='en'):
    print("Importing Type Materials")
    invTypeMaterials = Table('invTypeMaterials',metadata)
    
    targetPath = os.path.join(sourcePath, 'typeMaterials.yaml')
    if not os.path.exists(targetPath):
        targetPath = os.path.join(sourcePath, 'fsd', 'typeMaterials.yaml')
    if not os.path.exists(targetPath):
        targetPath = os.path.join(sourcePath, 'sde', 'fsd', 'typeMaterials.yaml')

    print(f"  Opening {targetPath}")

    if connection.in_transaction():
        trans = None
    else:
        trans = connection.begin()

    with open(targetPath,'r', encoding='utf-8') as yamlstream:
        materials=load(yamlstream,Loader=SafeLoader)
        print(f"  Processing {len(materials)} type materials")

        material_rows = []
        processed_types = set()

        # 1. Load CCP's Official Data
        for typeid in materials:
            if 'materials' in materials[typeid]:
                processed_types.add(typeid)
                for material in materials[typeid]['materials']:
                    material_rows.append({
                        'typeID': typeid,
                        'materialTypeID': material['materialTypeID'],
                        'quantity': material['quantity']
                    })

        # 2. Inject Custom Data (Only if CCP didn't already provide it)
        injected_count = 0
        for custom_typeid, custom_mats in CUSTOM_INJECTIONS.items():
            if custom_typeid not in processed_types:
                for mat in custom_mats:
                    material_rows.append({
                        'typeID': custom_typeid,
                        'materialTypeID': mat['materialTypeID'],
                        'quantity': mat['quantity']
                    })
                injected_count += 1

        # BULK INSERT
        if material_rows:
            connection.execute(invTypeMaterials.insert(), material_rows)
            print(f"  Inserted {len(material_rows)} type materials (Included {injected_count} custom item injections)")

    if trans:
        trans.commit()

    print("  Done")