# -----------------------------------------------------------------------------
# PHASE 2: Index Creation (Hardened for SQLite Locks)
# -----------------------------------------------------------------------------

# Close the loading connection to release all locks
print("\nFinalizing data load and releasing database locks...")
connection.close()
engine.dispose()

# Buffer for the GitHub runner to release file handles
import time
time.sleep(3)

# Re-connect with a 60-second timeout for the indexing phase
print(f"Re-connecting for indexing...")
engine = create_engine(destination, connect_args={'timeout': 60})

print("\n" + "="*60)
print("Creating Indexes...")
print("="*60)

start_time = time.time()
index_count = 0
error_count = 0

for table_name, indexes in saved_indexes.items():
    if indexes:
        print(f"\nIndexing table: {table_name}")
        for index in indexes:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    index.create(engine)
                    index_count += 1
                    print(f"  ✓ Created index: {index.name}")
                    break
                except Exception as e:
                    if "locked" in str(e).lower() and attempt < max_retries - 1:
                        print(f"  ↻ Database locked, retrying {index.name}...")
                        time.sleep(2)
                    else:
                        error_count += 1
                        print(f"  ⚠ Warning: Could not create index {index.name}: {e}")
                        break

print(f"\nIndex creation complete! Created: {index_count}, Warnings: {error_count}")
engine.dispose()