# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd

def generate_final_master():
    conn = sqlite3.connect('eve.db')
    cursor = conn.cursor()
    
    # 1. Detect the correct column name for 'level' in agtAgents
    cursor.execute("PRAGMA table_info(agtAgents)")
    columns = [col[1] for col in cursor.fetchall()]
    level_col = 'level' if 'level' in columns else 'agentLevel'
    print(f"Detected level column name: {level_col}")

    # 2. The Final Master Query with fuzzy racial matching
    query = f"""
    SELECT 
        ra.typeID AS science_id,
        it_skill.typeName AS science_type,
        it_core.typeID AS datacore_id,
        it_core.typeName AS datacore_name,
        ra.agentID,
        n_agent.itemName AS agent_name,
        a.{level_col} AS agent_level
    FROM agtResearchAgents ra
    JOIN invTypes it_skill ON ra.typeID = it_skill.typeID
    JOIN agtAgents a ON ra.agentID = a.agentID
    JOIN invNames n_agent ON ra.agentID = n_agent.itemID
    JOIN invTypes it_core ON (
        it_core.typeName LIKE 'Datacore - %'
        AND (
            -- This catches standard matches and handles the Gallentean/Amarr quirks
            it_core.typeName LIKE '%' || REPLACE(REPLACE(it_skill.typeName, ' Methods', ''), ' Engineering', '') || '%'
            OR (it_skill.typeName LIKE 'Amarr%' AND it_core.typeName LIKE 'Datacore - Amarr%')
            OR (it_skill.typeName LIKE 'Gallente%' AND it_core.typeName LIKE 'Datacore - Gallentean%')
        )
    )
    ORDER BY it_skill.typeName ASC, a.{level_col} DESC;
    """
    
    print("Finalizing the Research Farm Master List...")
    try:
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            df.to_csv('research_farm_final.csv', index=False)
            print(f"SUCCESS! Created research_farm_final.csv with {len(df)} rows.")
            
            # Print a quick audit to confirm Amarr/Gallente are present
            summary = df['science_type'].str.extract(r'(Amarr|Caldari|Gallente|Minmatar)', expand=False).value_counts()
            print("\n--- Racial Agent Audit ---")
            print(summary)
        else:
            print("Query returned no data. Your SDE might have very unusual naming.")

    except Exception as e:
        print(f"Error during final extraction: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    generate_final_master()