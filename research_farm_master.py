import sqlite3
import pandas as pd

def generate_research_lookup():
    conn = sqlite3.connect('eve.db')
    
    # Logic:
    # 1. Start with the mapping of Agent to Science Skill (agtResearchAgents)
    # 2. Get the Skill Name from invTypes
    # 3. Find the Datacore that matches that Skill Name in invTypes
    # 4. Get the Agent Name from invNames
    query = """
    SELECT 
        it_skill.typeID AS science_id,
        it_skill.typeName AS science_type,
        it_core.typeID AS datacore_id,
        it_core.typeName AS datacore_name,
        ra.agentID,
        n_agent.itemName AS agent_name,
        a.level AS agent_level
    FROM agtResearchAgents ra
    JOIN invTypes it_skill ON ra.typeID = it_skill.typeID
    JOIN invTypes it_core ON it_core.typeName = 'Datacore - ' || it_skill.typeName
    JOIN agtAgents a ON ra.agentID = a.agentID
    JOIN invNames n_agent ON ra.agentID = n_agent.itemID
    ORDER BY it_skill.typeName ASC, a.level DESC;
    """
    
    print("Generating Research Farm Lookup Table...")
    try:
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            output_file = 'research_farm_master.csv'
            df.to_csv(output_file, index=False)
            print(f"SUCCESS! Created {output_file}")
            print(f"Found {len(df)} total agent/science combinations.")
        else:
            print("Query returned no data. Trying fallback string match...")
            # Fallback for some SDE versions that use 'Datacore – ' (long dash)
            query_alt = query.replace("'Datacore - '", "'Datacore % '")
            df = pd.read_sql_query(query_alt, conn)
            df.to_csv('research_farm_master.csv', index=False)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    generate_research_lookup()