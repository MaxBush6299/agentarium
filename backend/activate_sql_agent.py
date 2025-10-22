"""
Activate the sql-agent so it can be used.
"""

import asyncio
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient
import os


async def activate_sql_agent():
    """Activate the sql-agent in Cosmos DB"""
    
    # Get credentials
    endpoint = os.getenv("COSMOS_DB_ENDPOINT")
    if not endpoint:
        print("✗ Error: COSMOS_DB_ENDPOINT not set")
        return False
    
    print(f"Connecting to Cosmos DB: {endpoint}")
    
    # Create client using Azure CLI credentials
    try:
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential=credential)
        print("✓ Connected to Cosmos DB")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False
    
    # Get database and container
    try:
        database = client.get_database_client("agent-db")
        container = database.get_container_client("agents")
        print("✓ Got agents container")
    except Exception as e:
        print(f"✗ Failed to get container: {e}")
        return False
    
    # Read the sql-agent
    try:
        agent = container.read_item(item="sql-agent", partition_key="sql-agent")
        print(f"✓ Found sql-agent")
        print(f"  Current status: {agent.get('status')}")
    except Exception as e:
        print(f"✗ Failed to read sql-agent: {e}")
        return False
    
    # Update status to active
    if agent.get('status') != 'active':
        try:
            agent['status'] = 'active'
            agent['updated_at'] = datetime.utcnow().isoformat()
            
            container.upsert_item(agent)
            print(f"✓ Activated sql-agent (status: {agent['status']})")
            return True
        except Exception as e:
            print(f"✗ Failed to activate: {e}")
            return False
    else:
        print(f"✓ sql-agent is already active")
        return True


if __name__ == "__main__":
    from datetime import datetime
    
    print("=" * 70)
    print("Activating sql-agent")
    print("=" * 70)
    print()
    
    success = asyncio.run(activate_sql_agent())
    
    print()
    if success:
        print("✓ sql-agent is now active and ready to use")
    else:
        print("✗ Failed to activate sql-agent")
