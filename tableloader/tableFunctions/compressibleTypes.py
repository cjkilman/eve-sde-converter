# -*- coding: utf-8 -*-
from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

import os
from sqlalchemy import Table

def importyaml(connection, metadata, sourcePath, language='en'):
    print("Importing Compressible Types")
    invCompressibleTypes = Table('invCompressibleTypes', metadata)

    target_file = None
    for subpath in ['', 'fsd', os.path.join('sde', 'fsd')]:
        candidate = os.path.join(sourcePath, subpath, 'compressibleTypes.yaml') if subpath else os.path.join(sourcePath, 'compressibleTypes.yaml')
        if os.path.exists(candidate):
            target_file = candidate
            break

    if not target_file:
        print("  Warning: Could not find compressibleTypes.yaml — skipping")
        return

    print(f"  Opening {target_file}")

    with open(target_file, 'r', encoding='utf-8') as yamlstream:
        data = load(yamlstream, Loader=SafeLoader)

    # The YAML is a list of typeIDs
    if isinstance(data, list):
        type_ids = data
    elif isinstance(data, dict):
        type_ids = list(data.keys())
    else:
        print(f"  Warning: Unexpected compressibleTypes.yaml format ({type(data).__name__}) — skipping")
        return

    print(f"  Processing {len(type_ids)} compressible types")

    rows = [{'typeID': tid} for tid in type_ids]

    trans = connection.begin()
    if rows:
        connection.execute(invCompressibleTypes.insert(), rows)
        print(f"  Inserted {len(rows)} compressible types")
    trans.commit()
    print("  Done")
