import sqlite3
import pandas as pd

query = """
SELECT 
    a.agentID,
    n_agent.itemName AS agentName,
    ra.typeID AS datacoreTypeID,
    n_core.itemName AS datacoreName,
    a.level AS agentLevel,
    corp.itemName AS corporationName
FROM agtResearchAgents ra
JOIN agtAgents a ON ra.agentID = a.agentID
JOIN invNames n_agent ON ra.agentID = n_agent.itemID
JOIN invNames n_core ON ra.typeID = n_core.itemID
LEFT JOIN invNames corp ON a.corporationID = corp.itemID
ORDER BY n_agent.itemName ASC;
"""

def generate_datacore_csv():
    print("Connecting to eve.db...")
    conn = sqlite3.connect('eve.db')
    
    print("Extracting Data Core mappings...")
    df = pd.read_sql_query(query, conn)
    
    # Optional: Clean up names (e.g., removing 'Datacore - ' prefix if you want it leaner)
    # df['datacoreName'] = df['datacoreName'].str.replace('Datacore - ', '')

    output_file = 'datacore_lookup.csv'
    df.to_csv(output_file, index=False)
    
    print(f"SUCCESS! Created {output_file} with {len(df)} mappings.")
    conn.close()

if __name__ == "__main__":
    generate_datacore_csv()