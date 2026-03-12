import sqlite3

def debug_db():
    conn = sqlite3.connect('eve.db')
    cursor = conn.cursor()

    tables = ['agtResearchAgents', 'agtAgents', 'invNames', 'invTypes']
    print("--- Database Row Counts ---")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count} rows")
        except Exception as e:
            print(f"{table}: TABLE MISSING OR ERROR ({e})")

    # Check for specific Datacore names
    print("\n--- Searching for 'Datacore' in invNames ---")
    cursor.execute("SELECT itemID, itemName FROM invNames WHERE itemName LIKE 'Datacore%' LIMIT 5")
    names = cursor.fetchall()
    if not names:
        print("RESULT: No names starting with 'Datacore' found in invNames.")
    else:
        for n in names:
            print(f"Found: {n[1]} (ID: {n[0]})")

    conn.close()

if __name__ == "__main__":
    debug_db()