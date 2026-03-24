# -*- coding: utf-8 -*-
import os
import sys
import time
import configparser
import warnings
from sqlalchemy import create_engine, Table

# Suppress SQLAlchemy warnings
warnings.filterwarnings('ignore', '^Unicode type received non-unicode bind param value')

# 1. INITIAL SETUP & ARGUMENT PARSING
if len(sys.argv) < 2:
    print("Usage: Load.py <destination_db_type> [language] [--create-stripped]")
    exit()

database = sys.argv[1]
create_stripped = '--create-stripped' in sys.argv
sys.argv = [arg for arg in sys.argv if arg != '--create-stripped']
language = sys.argv[2] if len(sys.argv) == 3 else 'en'

# Load Configuration
fileLocation = os.path.dirname(os.path.realpath(__file__))
inifile = os.path.join(fileLocation, 'sdeloader.cfg')
config = configparser.ConfigParser()
config.read(inifile)

destination = config.get('Database', database)
sourcePath = config.get('Files', 'sourcePath')

from tableloader.tableFunctions import *
from tableloader.tables import metadataCreator

# 2. DATABASE CONNECTION
print("connecting to DB")
connection = None
saved_indexes = {}  # Initialize early so it exists for the indexing phase

try:
    engine = create_engine(destination)
    connection = engine.connect()

    schema = "evesde" if database == "postgresschema" else None
    metadata = metadataCreator(schema)

    # 3. TABLE PREPARATION
    print("Creating Tables (indexes will be created after data load)")
    metadata.drop_all(engine, checkfirst=True)

    # Store all indexes for later creation
    for table in metadata.sorted_tables:
        if table.indexes:
            saved_indexes[table.name] = list(table.indexes)
            table.indexes.clear()

    metadata.create_all(engine, checkfirst=True)
    print("Tables created (without indexes)")

    # 4. DATA IMPORT PHASE
    factions.importyaml(connection, metadata, sourcePath, language)
    ancestries.importyaml(connection, metadata, sourcePath, language)
    bloodlines.importyaml(connection, metadata, sourcePath, language)
    npccorporations.importyaml(connection, metadata, sourcePath, language)
    npcDivisions.importyaml(connection, metadata, sourcePath, language)
    characterAttributes.importyaml(connection, metadata, sourcePath, language)
    agents.importyaml(connection, metadata, sourcePath, language)

    # Capture Agent IDs for filtering
    result = connection.execute(metadata.tables['agtAgents'].select())
    valid_agent_ids = {row[0] for row in result}

    typeMaterials.importyaml(connection, metadata, sourcePath, language)
    dogmaTypes.importyaml(connection, metadata, sourcePath, language)
    dogmaEffects.importyaml(connection, metadata, sourcePath, language)
    dogmaAttributes.importyaml(connection, metadata, sourcePath, language)
    dogmaAttributeCategories.importyaml(connection, metadata, sourcePath, language)
    blueprints.importyaml(connection, metadata, sourcePath)
    marketGroups.importyaml(connection, metadata, sourcePath, language)
    metaGroups.importyaml(connection, metadata, sourcePath, language)
    controlTowerResources.importyaml(connection, metadata, sourcePath, language)
    categories.importyaml(connection, metadata, sourcePath, language)
    graphics.importyaml(connection, metadata, sourcePath)
    groups.importyaml(connection, metadata, sourcePath, language)
    certificates.importyaml(connection, metadata, sourcePath, language)
    icons.importyaml(connection, metadata, sourcePath)
    skins.importyaml(connection, metadata, sourcePath)
    types.importyaml(connection, metadata, sourcePath, language)
    typeBonus.importyaml(connection, metadata, sourcePath, language)
    masteries.importyaml(connection, metadata, sourcePath, language)
    eveUnits.importyaml(connection, metadata, sourcePath, language)
    planetary.importyaml(connection, metadata, sourcePath, language)
    volumes.importVolumes(connection, metadata, sourcePath)
    universe.importyaml(connection, metadata, sourcePath, language)
    universe.buildJumps(connection, metadata)
    stations.importyaml(connection, metadata, sourcePath, language)
    universe.fixStationNames(connection, metadata)
    invNames.importyaml(connection, metadata, sourcePath, language)
    invItems.importyaml(connection, metadata, sourcePath, language)
    rigAffectedProductGroups.importRigMappings(connection, metadata)

except Exception as e:
    print(f"An error occurred during data load: {e}")
    sys.exit(1)

finally:
    # 5. PHASE 2: INDEX CREATION
    if connection is not None:
        print("\nFinalizing data load and releasing database locks...")
        connection.close()
    
    if 'engine' in locals():
        engine.dispose()

# Wait for file handles to clear
time.sleep(3)

# Re-connect specifically for indexing
print("Re-connecting for indexing phase...")
engine = create_engine(destination, connect_args={'timeout': 60})

print("\n" + "="*60)
print("Creating Indexes...")
print("="*60)

index_count = 0
for table_name, indexes in saved_indexes.items():
    if indexes:
        print("\nIndexing table: {}".format(table_name))
        for index in indexes:
            try:
                index.create(engine)
                index_count += 1
                print("  ✓ Created index: {}".format(index.name))
            except Exception as e:
                print("  ⚠ Warning: Could not create index {}: {}".format(index.name, e))

print("\nIndex creation complete! Created {} indexes.".format(index_count))

# 6. OPTIONAL: STRIPPED DATABASE CREATION
if create_stripped and database == 'sqlite':
    import shutil
    import sqlite3
    
    source_db_path = 'eve.db'
    dest_db_path = 'eve-stripped.db'
    
    TABLES_TO_KEEP = {
        'invTypes', 'invGroups', 'invCategories', 'invMetaTypes', 'invVolumes',
        'industryActivityMaterials', 'industryActivityProducts', 'industryActivity',
        'industryActivityProbabilities', 'industryActivitySkills',
        'dgmTypeAttributes', 'dgmAttributeTypes', 'dgmTypeEffects', 'dgmEffects',
        'dgmAttributeCategories', 'dgmExpressions',
        'mapRegions', 'mapSolarSystems', 'staStations',
        'invTypeMaterials', 'invMarketGroups', 'industryBlueprints',
        'planetSchematics', 'planetSchematicsPinMap', 'planetSchematicsTypeMap',
        'invTypeReactions', 'rigAffectedProductGroups', 'rigIndustryModifierSources'
    }

    if os.path.exists(source_db_path):
        print("\nCreating stripped database: {}".format(dest_db_path))
        shutil.copy2(source_db_path, dest_db_path)
        conn = sqlite3.connect(dest_db_path, timeout=60)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        for table in [t for t in all_tables if t not in TABLES_TO_KEEP]:
            cursor.execute("DROP TABLE IF EXISTS {}".format(table))
        
        print("  Optimizing (VACUUM)...")
        conn.commit()
        cursor.execute("VACUUM")
        conn.close()

engine.dispose()
print("\nProcess complete.")