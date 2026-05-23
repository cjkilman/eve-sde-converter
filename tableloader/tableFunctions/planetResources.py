# -*- coding: utf-8 -*-
import os
from sqlalchemy import Table

from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


def importyaml(connection, metadata, sourcePath, language='en'):
    print("Importing Planet Resources")
    planetResources = Table('planetResources', metadata)
    planetResourceReagents = Table('planetResourceReagents', metadata)

    targetPath = os.path.join(sourcePath, 'planetResources.yaml')
    if not os.path.exists(targetPath):
        targetPath = os.path.join(sourcePath, 'fsd', 'planetResources.yaml')
    if not os.path.exists(targetPath):
        targetPath = os.path.join(sourcePath, 'sde', 'fsd', 'planetResources.yaml')

    print(f"  Opening {targetPath}")

    trans = connection.begin()
    with open(targetPath, 'r', encoding='utf-8') as yamlstream:
        data = load(yamlstream, Loader=SafeLoader)
        print(f"  Populating Planet Resource tables with {len(data)} entries")

        resource_rows = []
        reagent_rows = []

        for planetID, entry in data.items():
            if 'workforce' in entry:
                resource_rows.append({
                    'planetID': planetID,
                    'resourceType': 'workforce',
                    'workforce': entry['workforce'],
                    'power': None,
                })
            elif 'power' in entry:
                resource_rows.append({
                    'planetID': planetID,
                    'resourceType': 'power',
                    'workforce': None,
                    'power': entry['power'],
                })
            elif 'reagent' in entry:
                r = entry['reagent']
                resource_rows.append({
                    'planetID': planetID,
                    'resourceType': 'reagent',
                    'workforce': None,
                    'power': None,
                })
                reagent_rows.append({
                    'planetID': planetID,
                    'typeID': r['type_id'],
                    'amountPerCycle': r['amount_per_cycle'],
                    'cyclePeriod': r['cycle_period'],
                    'securedCapacity': r['secured_capacity'],
                    'unsecuredCapacity': r['unsecured_capacity'],
                })

        if resource_rows:
            connection.execute(planetResources.insert(), resource_rows)
            print(f"  Inserted {len(resource_rows)} planet resource rows")

        if reagent_rows:
            connection.execute(planetResourceReagents.insert(), reagent_rows)
            print(f"  Inserted {len(reagent_rows)} planet reagent rows")

    trans.commit()
    print("  Done")
