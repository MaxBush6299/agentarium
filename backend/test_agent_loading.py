#!/usr/bin/env python3
"""Test script to verify agents exist in Cosmos DB and can be loaded."""

import asyncio
import sys
from src.persistence.agents import get_agent_repository
from src.agents.factory import AgentFactory

async def test_agent_loading():
    """Test loading all required agents."""
    required_agents = ["router", "data-agent", "analyst", "order-agent", "evaluator"]
    
    print("Testing agent loading from Cosmos DB...")
    print("=" * 60)
    
    try:
        repo = get_agent_repository()
        loaded = {}
        
        for agent_id in required_agents:
            try:
                metadata = repo.get(agent_id)
                if metadata:
                    agent = AgentFactory.create_from_metadata(metadata)
                    if agent:
                        loaded[agent_id] = agent
                        print(f"✓ {agent_id}: Loaded successfully")
                    else:
                        print(f"✗ {agent_id}: Failed to instantiate")
                else:
                    print(f"✗ {agent_id}: Not found in repository")
            except Exception as e:
                print(f"✗ {agent_id}: Error - {str(e)}")
        
        print("=" * 60)
        print(f"Summary: {len(loaded)}/{len(required_agents)} agents loaded")
        
        if len(loaded) >= 4:  # Need at least router + 3 specialists
            print("✓ Sufficient agents for handoff workflow!")
            return True
        else:
            print("✗ Insufficient agents for handoff workflow")
            print(f"  Missing: {[a for a in required_agents if a not in loaded]}")
            return False
            
    except Exception as e:
        print(f"✗ Error connecting to Cosmos DB: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_agent_loading())
    sys.exit(0 if result else 1)
