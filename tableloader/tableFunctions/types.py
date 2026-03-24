# -*- coding: utf-8 -*-
from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

import os
from sqlalchemy import Table

def importyaml(connection,metadata,sourcePath,language='en'):
    invTypes = Table('invTypes',metadata)
    trnTranslations = Table('trnTranslations',metadata)
    invMetaTypes = Table('invMetaTypes',metadata)
    print("Importing Types")

    targetPath = os.path.join(sourcePath, 'types.yaml')
    if not os.path.exists(targetPath):
        targetPath = os.path.join(sourcePath, 'sde', 'fsd', 'types.yaml')

    if connection.in_transaction():
        trans = None
    else:
        trans = connection.begin()

    with open(targetPath,'r', encoding='utf-8') as yamlstream:
        typeids=load(yamlstream,Loader=SafeLoader)
        print(f"  Processing {len(typeids)} types")

        type_rows = []
        translation_rows = []
        meta_type_rows = []

        for typeid in typeids:
            type_rows.append({
                'typeID': typeid,
                'groupID': typeids[typeid].get('groupID',0),
                'typeName': typeids[typeid].get('name',{}).get(language,''),
                'description': typeids[typeid].get('description',{}).get(language,''),
                'mass': typeids[typeid].get('mass',0),
                'volume': typeids[typeid].get('volume',0),
                'capacity': typeids[typeid].get('capacity',0),
                'portionSize': typeids[typeid].get('portionSize'),
                'raceID': typeids[typeid].get('raceID'),
                'basePrice': typeids[typeid].get('basePrice'),
                'published': typeids[typeid].get('published',0),
                'marketGroupID': typeids[typeid].get('marketGroupID'),
                'graphicID': typeids[typeid].get('graphicID',0),
                'iconID': typeids[typeid].get('iconID'),
                'soundID': typeids[typeid].get('soundID')
            })

            if 'name' in typeids[typeid]:
                for lang in typeids[typeid]['name']:
                    translation_rows.append({
                        'tcID': 8, 'keyID': typeid, 'languageID': lang, 'text': typeids[typeid]['name'][lang]
                    })

            if 'description' in typeids[typeid]:
                for lang in typeids[typeid]['description']:
                    translation_rows.append({
                        'tcID': 33, 'keyID': typeid, 'languageID': lang, 'text': typeids[typeid]['description'][lang]
                    })

            if 'metaGroupID' in typeids[typeid] or 'variationParentTypeID' in typeids[typeid]:
                meta_type_rows.append({
                    'typeID': typeid,
                    'metaGroupID': typeids[typeid].get('metaGroupID'),
                    'parentTypeID': typeids[typeid].get('variationParentTypeID')
                })

        if type_rows:
            connection.execute(invTypes.insert(), type_rows)
            print(f"  Inserted {len(type_rows)} types")

        if translation_rows:
            connection.execute(trnTranslations.insert(), translation_rows)
            print(f"  Inserted {len(translation_rows)} translations")

        if meta_type_rows:
            connection.execute(invMetaTypes.insert(), meta_type_rows)
            print(f"  Inserted {len(meta_type_rows)} meta types")
    
    if trans:
        trans.commit()
    print("  Done")