#!/usr/bin/env python3
"""
Test script to verify tool call logging from specialist agents.

This script sends a message to the router agent and checks that we see:
1. Router agent's tool call to sql_agent
2. SQL agent's tool call to MSSQL MCP
"""

import asyncio
import httpx
import json

async def test_tool_call_logging():
    """Test tool call logging by querying the router agent."""
    
    base_url = "http://localhost:8000"
    
    # Step 1: Create a thread for the router agent
    print("[TEST] Creating thread for router agent...")
    async with httpx.AsyncClient() as client:
        thread_response = await client.post(
            f"{base_url}/api/agents/router/threads"
        )
        if thread_response.status_code != 200:
            print(f"[ERROR] Failed to create thread: {thread_response.status_code}")
            print(thread_response.text)
            return
        
        thread_data = thread_response.json()
        thread_id = thread_data.get("id")
        print(f"[SUCCESS] Created thread: {thread_id}")
        
        # Step 2: Send a message that will trigger tool calls
        print("\n[TEST] Sending query to router agent...")
        print("[TEST] Query: 'what tables are available in my database?'")
        print("[TEST] Expected: Router -> SQL Agent -> MSSQL MCP tool")
        print()
        
        # Use streaming endpoint to see logs
        async with client.stream(
            "POST",
            f"{base_url}/api/agents/router/chat",
            json={
                "message": "what tables are available in my database?",
                "thread_id": thread_id
            },
            timeout=120.0
        ) as response:
            if response.status_code != 200:
                print(f"[ERROR] Chat request failed: {response.status_code}")
                text = await response.aread()
                print(text.decode())
                return
            
            print("[RESPONSE] Streaming response:")
            async for line in response.aiter_lines():
                if line.strip():
                    print(f"  {line}")
        
        print("\n[SUCCESS] Query completed")
        print("[TEST] Check logs above for:")
        print("  - [ROUTER AGENT_RUN] logs")
        print("  - [SQL_AGENT_TOOL_INVOKED] logs")
        print("  - [SQL QUERY AGENT_TOOL_INVOKED] logs (NEW - these are MSSQL tool calls!)")

if __name__ == "__main__":
    asyncio.run(test_tool_call_logging())
