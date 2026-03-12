# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd

def export_agent_names(db_path='eve.db', output_file='agentNames.csv'):
    print(f"Connecting to {db_path} to generate Agent Names...")
    
    # 1. Connect to your SQLite database created by Load.py
    conn = sqlite3.connect(db_path)
    
    # 2. The "Tycoon Join": 
    # We take agtAgents (the structural data) and join it to invNames (the strings)
    # We only keep the ID and the Name to keep the CSV tiny.
    query = """
    SELECT 
        a.agentID, 
        n.itemName as agentName
    FROM agtAgents a
    JOIN invNames n ON a.agentID = n.itemID
    """
    
    print("Executing SQL Join...")
    df = pd.read_sql_query(query, conn)
    
    # 3. Export to a fresh, lean CSV
    df.to_csv(output_file, index=False)
    
    print(f"Success! Created {output_file} with {len(df)} agents.")
    conn.close()

if __name__ == "__main__":
    export_agent_names()




