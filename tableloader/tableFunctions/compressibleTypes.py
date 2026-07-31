# -*- coding: utf-8 -*-
import os
from sqlalchemy import Table

from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

def importyaml(connection, metadata, sourcePath, language='en'):
    print("Importing Compressible Types")
    compressibleTypes = Table('invCompressibleTypes', metadata)

    targetPath = os.path.join(sourcePath, 'compressibleTypes.yaml')
    if not os.path.exists(targetPath):
        targetPath = os.path.join(sourcePath, 'sde', 'fsd', 'compressibleTypes.yaml')
    if not os.path.exists(targetPath):
        targetPath = os.path.join(sourcePath, 'sde', 'fsd', 'compressibleTypes.yaml')

    print(f"  Opening {targetPath}")

    # FIX: Safely check for existing transaction
    if connection.in_transaction():
        trans = None
    else:
        trans = connection.begin()

    with open(targetPath, 'r', encoding='utf-8') as yamlstream:
        data = load(yamlstream, Loader=SafeLoader)
        print(f"  Processing {len(data)} compressible types")

        rows = []
        for type_id, entry in data.items():
            if 'compressToTypeID' in entry:
                rows.append({
                    'typeID': type_id,
                    'compressToTypeID': entry['compressToTypeID'],
                    'compressQuantity': entry.get('compressQuantity', 1) # Default to 1 if missing
                })

        if rows:
            connection.execute(compressibleTypes.insert(), rows)
            print(f"  Inserted {len(rows)} compressible types")

    # FIX: Only commit if we started the transaction
    if trans:
        trans.commit()
    print("  Done")