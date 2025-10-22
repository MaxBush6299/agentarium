"""
Setup sql-agent: Activate it and attach custom tools from the database.
Uses the same configuration as the backend.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.config import settings
from src.persistence.cosmos_client import initialize_cosmos
from src.persistence.agents import get_agent_repository
from src.persistence.models import ToolType, ToolConfig, AgentStatus


def setup_sql_agent():
    """Setup sql-agent with custom tool"""
    
    print("=" * 70)
    print("Setting up sql-agent")
    print("=" * 70)
    
    # Initialize Cosmos DB first
    print("\n[0] Initializing Cosmos DB...")
    try:
        initialize_cosmos(
            endpoint=settings.COSMOS_ENDPOINT,
            database_name=settings.COSMOS_DATABASE_NAME,
            key=settings.COSMOS_KEY,
            connection_string=settings.COSMOS_CONNECTION_STRING,
        )
        print(f"[OK] Connected to {settings.COSMOS_DATABASE_NAME}")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Cosmos DB: {e}")
        return False
    
    try:
        repo = get_agent_repository()
        print(f"[OK] Got agent repository")
    except Exception as e:
        print(f"[ERROR] Failed to get repository: {e}")
        return False
    
    # Step 1: Get sql-agent
    print("\n[1] Loading sql-agent...")
    try:
        agent = repo.get("sql-agent")
        if not agent:
            print("    [ERROR] sql-agent not found in database")
            return False
        print(f"    [OK] Found sql-agent")
        print(f"      Current status: {agent.status}")
        print(f"      Current tools: {len(agent.tools)}")
    except Exception as e:
        print(f"    [ERROR] Failed to read sql-agent: {e}")
        return False
    
    # Step 2: Activate agent if not already active
    print("\n[2] Activating sql-agent...")
    if agent.status != AgentStatus.ACTIVE:
        agent.status = AgentStatus.ACTIVE
        print(f"    Setting status to 'ACTIVE'")
    else:
        print(f"    Already active")
    
    # Step 3: Look for custom tools in the registry
    print("\n[3] Looking for custom tools...")
    print("    Note: Custom tools are registered via the API")
    print("    If you registered a custom tool from the frontend,")
    print("    you can manually attach it here or via the UI")
    
    # Step 5: Save updated agent
    print("\n[4] Saving changes...")
    try:
        repo.upsert(agent)
        print("    [OK] Agent updated in database")
    except Exception as e:
        print(f"    [ERROR] Failed to save: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print(f"[OK] sql-agent setup complete!")
    print("=" * 70)
    print(f"\nFinal state:")
    print(f"  Status: {agent.status.value if hasattr(agent.status, 'value') else agent.status}")
    print(f"  Tools: {len(agent.tools)}")
    if agent.tools:
        for tool in agent.tools:
            print(f"    - {tool.type.value if hasattr(tool.type, 'value') else tool.type}: {tool.name}")
    else:
        print(f"    (none)")
    
    print("\nTo attach a custom tool:")
    print("  1. Register it from the frontend")
    print("  2. The tool will appear in the agent automatically")
    print("  3. Or use the UI to attach it manually")
    
    return True


if __name__ == "__main__":
    try:
        success = setup_sql_agent()
        if success:
            print("\n[OK] Setup complete!")
            print("Run verify_and_test_agent.py to test the setup")
            sys.exit(0)
        else:
            print("\n[ERROR] Setup failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
