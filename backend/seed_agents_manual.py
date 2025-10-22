#!/usr/bin/env python
"""
Quick script to verify and seed agents to Cosmos DB.
Run this to ensure agents are in the database.
"""
import sys
import os
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Initialize Cosmos and seed agents."""
    try:
        # Import after path is set
        from src.config import settings
        from src.persistence.cosmos_client import initialize_cosmos, get_cosmos
        from src.persistence.seed_agents import seed_agents, list_seeded_agents
        
        print("\n" + "="*60)
        print("AGENT SEEDING UTILITY")
        print("="*60)
        
        # Initialize Cosmos
        print("\n1️⃣  Initializing Cosmos DB...")
        cosmos_client = initialize_cosmos(
            endpoint=settings.COSMOS_ENDPOINT,
            database_name=settings.COSMOS_DATABASE_NAME,
            key=settings.COSMOS_KEY,
            connection_string=settings.COSMOS_CONNECTION_STRING,
        )
        
        if cosmos_client.health_check():
            print("   ✅ Cosmos DB connected and healthy")
        else:
            print("   ❌ Cosmos DB health check failed")
            return False
        
        # Seed agents
        print("\n2️⃣  Seeding agents...")
        result = seed_agents()
        print(f"   ✅ Created: {result['created']}")
        print(f"   ⏭️  Skipped: {result['skipped']}")
        print(f"   📊 Total: {result['total']}")
        
        # List seeded agents
        print("\n3️⃣  Verifying seeded agents...")
        agents = list_seeded_agents()
        for agent in agents:
            status_emoji = "✅" if agent.status.value == "active" else "⏸️"
            tools_count = len(agent.tools)
            print(f"   {status_emoji} {agent.id}: {agent.name}")
            print(f"      Status: {agent.status.value} | Tools: {tools_count}")
        
        print("\n" + "="*60)
        print("✅ SEEDING COMPLETE")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during seeding: {e}", exc_info=True)
        print(f"\n❌ Failed to seed agents: {e}\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
