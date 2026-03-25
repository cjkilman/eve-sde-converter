import sqlite3
import csv
import os

# --- CONFIGURATION ---
DB_NAME = "eve.db"
OUTPUT_DIR = "../eve-sde-dump" 

def is_tq_safe(name, description):
    """Checks for Serenity keywords and non-ASCII litter."""
    if not name: return False
    desc_text = str(description or "").lower()
    if "available on serenity" in desc_text or "designed for serenity" in desc_text:
        return False
    try:
        name.encode('ascii')
    except UnicodeEncodeError:
        return False 
    return True

def get_serenity_blacklist(conn):
    """Returns a SET of typeIDs that are flagged as Serenity-only."""
    print("Scanning invTypes to build Serenity Blacklist...")
    blacklist = set()
    cursor = conn.cursor()
    # We grab ID, Name, and Description to run our safety check
    cursor.execute("SELECT typeID, typeName, description FROM invTypes")
    for tid, name, desc in cursor.fetchall():
        if not is_tq_safe(name, desc):
            blacklist.add(tid)
    print(f" -> Found {len(blacklist)} Serenity-only items to prune.")
    return blacklist

def export_all_tables():
    """Loops through all tables and prunes any row referencing a Blacklisted typeID."""
    if not os.path.exists(DB_NAME):
        print(f"CRITICAL ERROR: {DB_NAME} not found.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    conn = sqlite3.connect(DB_NAME)
    
    # STEP 1: Build the Blacklist
    blacklist = get_serenity_blacklist(conn)
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table_tuple in tables:
        table_name = table_tuple[0]
        if table_name.startswith("sqlite_") or table_name == "alembic_version":
            continue

        file_path = os.path.join(OUTPUT_DIR, f"{table_name}.csv")
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            headers = [description[0] for description in cursor.description]
            
            # STEP 2: Check if this table uses typeID
            # If it does, we filter the rows based on our blacklist
            if "typeID" in headers:
                tid_idx = headers.index("typeID")
                pre_count = len(rows)
                rows = [r for r in rows if r[tid_idx] not in blacklist]
                post_count = len(rows)
                if pre_count != post_count:
                    print(f"Exporting {table_name}.csv (Pruned {pre_count - post_count} Serenity rows)")
                else:
                    print(f"Exported {table_name}.csv")
            else:
                print(f"Exported {table_name}.csv (No typeID column)")

            # STEP 3: Write the (now clean) data to CSV
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                if rows:
                    # Optional: Round floats here if you want to kill ISK artifacts
                    writer.writerows(rows)
            
        except Exception as e:
            print(f"  [!] Error exporting {table_name}: {e}")

    conn.close()

if __name__ == "__main__":
    export_all_tables()