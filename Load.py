# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, Table
import warnings
import sys
import configparser
import os
import time

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

print("Connecting to DB...")
engine = create_engine(destination)
connection = engine.connect()

schema = "evesde" if database == "postgresschema" else None
metadata = metadataCreator(schema)

# 2. TABLE CREATION (PRESERVE INDEXES)
print("Creating Tables (indexes will be created after data load)...")
metadata.drop_all(engine, checkfirst=True)

saved_indexes = {}
for table in metadata.sorted_tables:
    if table.indexes:
        saved_indexes[table.name] = list(table.indexes)
        table.indexes.clear()

metadata.create_all(engine, checkfirst=True)
print("Tables created (without indexes).")

# 3. DATA IMPORT PHASE
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

# 4. PHASE 2: INDEX CREATION (HANDLING SQLITE LOCKS)
print("\nFinalizing data load and releasing database locks...")
connection.close()
engine.dispose()

# Wait for file handles to clear
time.sleep(3)

print(f"Re-connecting for indexing phase...")
engine = create_engine(destination, connect_args={'timeout': 60})

print("\n" + "="*60)
print("Creating Indexes...")
print("="*60)

start_time = time.time()
index_count = 0
for table_name, indexes in saved_indexes.items():
    if indexes:
        print(f"\nIndexing table: {table_name}")
        for index in indexes:
            try:
                index.create(engine)
                index_count += 1
                print(f"  ✓ Created index: {index.name}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not create index {index.name}: {e}")

print(f"\nIndex creation complete! Created {index_count} indexes in {time.time()-start_time:.2f}s.")

# 5. OPTIONAL: STRIPPED DATABASE CREATION
if create_stripped and database == 'sqlite':
    import shutil
    import sqlite3
    
    source_db = 'eve.db'
    dest_db = 'eve-stripped.db'
    
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

    if os.path.exists(source_db):
        print(f"\nCreating stripped database: {dest_db}")
        shutil.copy2(source_db, dest_db)
        conn = sqlite3.connect(dest_db, timeout=60)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        for table in [t for t in all_tables if t not in TABLES_TO_KEEP]:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        print("  Optimizing (VACUUM)...")
        conn.commit()
        cursor.execute("VACUUM")
        conn.close()
        print("  Stripped database ready.")

engine.dispose()
print("\nConversion Process Finished Successfully.")