# -*- coding: utf-8 -*-
from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

import os
from sqlalchemy import Table

def importyaml(connection, metadata, sourcePath, language='en'):
    agtAgents = Table('agtAgents', metadata)
    agtAgentsInSpace = Table('agtAgentsInSpace', metadata)
    agtResearchAgents = Table('agtResearchAgents', metadata)
    agtAgentTypes = Table('agtAgentTypes', metadata)
    invNames = Table('invNames', metadata)

    def find_file(filename):
        candidates = [
            os.path.join(sourcePath, filename),
            os.path.join(sourcePath, 'fsd', filename),
            os.path.join(sourcePath, 'sde', 'fsd', filename)
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    # ONE TRANSACTION FOR THE WHOLE FUNCTION
    if connection.in_transaction():
        trans = None
    else:
        trans = connection.begin()

    try:
        # 1. IMPORT AGENTS & NAMES
        print("Importing Agents")
        targetPath = find_file('npcCharacters.yaml') or find_file('agents.yaml')
        if targetPath:
            with open(targetPath, 'r', encoding='utf-8') as yamlstream:
                npcCharacters = load(yamlstream, Loader=SafeLoader)
                agent_rows = []
                name_rows = []
                for characterID, charData in npcCharacters.items():
                    if 'agent' in charData:
                        agent_data = charData['agent']
                        agent_rows.append({
                            'agentID': characterID,
                            'divisionID': agent_data.get('divisionID'),
                            'corporationID': charData.get('corporationID'),
                            'isLocator': agent_data.get('isLocator'),
                            'level': agent_data.get('level'),
                            'locationID': charData.get('locationID'),
                            'agentTypeID': agent_data.get('agentTypeID')
                        })
                        if 'name' in charData:
                            raw_name = charData['name']
                            name_str = raw_name.get(language, raw_name.get('en', '')) if isinstance(raw_name, dict) else raw_name
                            name_rows.append({'itemID': characterID, 'itemName': name_str})

                if agent_rows:
                    connection.execute(agtAgents.insert(), agent_rows)
                if name_rows:
                    connection.execute(invNames.insert(), name_rows)
            print("  Done Agents")

        # 2. IMPORT AGENTS IN SPACE
        print("Importing AgentsInSpace")
        targetPath = find_file('agentsInSpace.yaml')
        if targetPath:
            with open(targetPath, 'r', encoding='utf-8') as yamlstream:
                agents = load(yamlstream, Loader=SafeLoader)
                space_rows = [{'agentID': aid, 'dungeonID': d.get('dungeonID'), 'solarSystemID': d.get('solarSystemID'), 
                               'spawnPointID': d.get('spawnPointID'), 'typeID': d.get('typeID')} for aid, d in agents.items()]
                if space_rows:
                    connection.execute(agtAgentsInSpace.insert(), space_rows)
            print("  Done AgentsInSpace")

        # 3. IMPORT RESEARCH AGENTS (uses npcCharacters again)
        print("Importing Research Agents")
        targetPath = find_file('npcCharacters.yaml')
        if targetPath:
            with open(targetPath, 'r', encoding='utf-8') as yamlstream:
                npcCharacters = load(yamlstream, Loader=SafeLoader)
                research_rows = []
                for characterID, charData in npcCharacters.items():
                    if charData.get('agent', {}).get('agentTypeID') == 4 and 'skills' in charData:
                        for skill in charData['skills']:
                            research_rows.append({'agentID': characterID, 'typeID': skill.get('typeID')})
                if research_rows:
                    connection.execute(agtResearchAgents.insert(), research_rows)
            print("  Done Research Agents")

        # 4. IMPORT AGENT TYPES
        print("Importing Agent Types")
        targetPath = find_file('agentTypes.yaml')
        if targetPath:
            with open(targetPath, 'r', encoding='utf-8') as yamlstream:
                aTypes = load(yamlstream, Loader=SafeLoader)
                type_rows = [{'agentTypeID': tid, 'agentType': d.get('name')} for tid, d in aTypes.items()]
                if type_rows:
                    connection.execute(agtAgentTypes.insert(), type_rows)
            print("  Done Agent Types")

        if trans:
            trans.commit()

    except Exception as e:
        if trans:
            trans.rollback()
        print(f"Error in Agents import: {e}")
        raise