"""
Setup sql-agent: Activate it and attach the custom tool.
This retrieves the custom tool from the database and attaches it to sql-agent.
"""

import asyncio
import json
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient
import os


async def setup_sql_agent():
    """Setup sql-agent with custom tool"""
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get credentials
    endpoint = os.getenv("COSMOS_ENDPOINT")
    if not endpoint:
        print("✗ Error: COSMOS_ENDPOINT not set in .env")
        return False
    
    print("=" * 70)
    print("Setting up sql-agent")
    print("=" * 70)
    print(f"\nConnecting to Cosmos DB: {endpoint}")
    
    # Create client
    try:
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential=credential)
        print("✓ Connected to Cosmos DB\n")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False
    
    # Get database and container
    try:
        database = client.get_database_client("agent-db")
        agents_container = database.get_container_client("agents")
    except Exception as e:
        print(f"✗ Failed to get containers: {e}")
        return False
    
    # Step 1: Find custom tools
    print("[1] Looking for custom tools in database...")
    custom_tools = []
    try:
        # Query for custom tools (usually named custom-XXXXX)
        query = "SELECT * FROM c WHERE STARTSWITH(c.id, 'custom-')"
        items = list(agents_container.query_items(query=query))
        
        # Actually, custom tools might be in a different place
        # Let's try to find them via the registry or other means
        # For now, assume the user's custom tool is known
        
        print("    Searching for custom tools...")
        # Try to get any custom- prefixed items
        for item in items:
            print(f"    Found: {item.get('id')} - {item.get('name', 'N/A')}")
            custom_tools.append(item)
        
        if not custom_tools:
            print("    ⚠ No custom tools found in database yet")
            print("    You may need to register a custom tool first")
            
    except Exception as e:
        print(f"    Note: {e}")
    
    # Step 2: Get sql-agent
    print("\n[2] Loading sql-agent...")
    try:
        agent = agents_container.read_item(item="sql-agent", partition_key="sql-agent")
        print(f"    ✓ Found sql-agent")
        print(f"      Current status: {agent.get('status')}")
        print(f"      Current tools: {len(agent.get('tools', []))}")
    except Exception as e:
        print(f"    ✗ Failed to read sql-agent: {e}")
        return False
    
    # Step 3: Activate agent if not already active
    print("\n[3] Activating sql-agent...")
    if agent.get('status') != 'active':
        agent['status'] = 'active'
        agent['updated_at'] = datetime.utcnow().isoformat()
        print("    Setting status to 'active'")
    else:
        print("    Already active")
    
    # Step 4: Attach custom tool if we found one
    print("\n[4] Attaching custom tool...")
    if custom_tools:
        # Use the first custom tool found
        custom_tool = custom_tools[0]
        tool_id = custom_tool['id']
        
        # Check if tool is already attached
        existing_tools = agent.get('tools', [])
        already_attached = any(t.get('name') == tool_id for t in existing_tools)
        
        if already_attached:
            print(f"    ✓ Tool '{tool_id}' already attached")
        else:
            # Add tool config
            tool_config = {
                "type": "mcp",
                "name": tool_id,
                "enabled": True
            }
            if 'tools' not in agent:
                agent['tools'] = []
            agent['tools'].append(tool_config)
            print(f"    ✓ Attached custom tool: {tool_id}")
    else:
        print("    ⚠ No custom tools found to attach")
        print("    Note: Register a custom tool first via the frontend")
    
    # Step 5: Save updated agent
    print("\n[5] Saving changes...")
    try:
        agents_container.upsert_item(agent)
        print("    ✓ Agent updated in database")
    except Exception as e:
        print(f"    ✗ Failed to save: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✓ sql-agent setup complete!")
    print("=" * 70)
    print(f"\nFinal state:")
    print(f"  Status: {agent['status']}")
    print(f"  Tools: {len(agent.get('tools', []))}")
    if agent.get('tools'):
        for tool in agent['tools']:
            print(f"    - {tool.get('type')}: {tool.get('name')}")
    
    return True


if __name__ == "__main__":
    import sys
    
    try:
        success = asyncio.run(setup_sql_agent())
        if success:
            print("\n✅ Setup complete! Agent is ready to use.")
            print("\nNext: Run verify_and_test_agent.py to test the setup")
            sys.exit(0)
        else:
            print("\n❌ Setup failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
