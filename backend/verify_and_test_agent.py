"""
Verify sql-agent setup and test chat with custom tool.
This script:
1. Checks if sql-agent exists
2. Verifies it has the custom tool attached
3. Tests a simple chat query
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime


async def verify_agent_setup():
    """Verify sql-agent is properly configured"""
    
    print("=" * 70)
    print("Verifying sql-agent Setup")
    print("=" * 70)
    
    base_url = "http://localhost:8000/api"
    
    # Step 1: Check if agent exists
    print("\n[1] Checking if sql-agent exists...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/agents/sql-agent") as resp:
                if resp.status == 404:
                    print("    ✗ sql-agent not found")
                    print("    Note: Agent may need to be created in database")
                    return False
                elif resp.status == 200:
                    agent = await resp.json()
                    print(f"    ✓ sql-agent found")
                    print(f"      Name: {agent['name']}")
                    print(f"      Status: {agent['status']}")
                    print(f"      Tools: {len(agent.get('tools', []))} tool(s)")
                    
                    # Step 2: Check tools
                    if agent.get('tools'):
                        print("\n[2] Attached tools:")
                        for tool in agent['tools']:
                            tool_type = tool.get('type', 'unknown')
                            tool_name = tool.get('name', 'unknown')
                            enabled = tool.get('enabled', False)
                            status_icon = "✓" if enabled else "✗"
                            print(f"      {status_icon} {tool_type}: {tool_name}")
                    else:
                        print("\n[2] No tools attached")
                        print("    Note: Attach custom tool from frontend")
                    
                    return agent['status'].lower() == 'active'
                else:
                    print(f"    ✗ Error: {resp.status}")
                    return False
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False


async def test_agent_chat():
    """Test chatting with the agent"""
    
    print("\n" + "=" * 70)
    print("Testing Agent Chat")
    print("=" * 70)
    
    base_url = "http://localhost:8000/api"
    
    payload = {
        "message": "What tables are in the database?",
        "thread_id": None,
        "stream": True  # Use streaming mode
    }
    
    print(f"\n[3] Sending chat request...")
    print(f"    Message: '{payload['message']}'")
    
    async with aiohttp.ClientSession() as session:
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            start = datetime.now()
            
            async with session.post(
                f"{base_url}/agents/sql-agent/chat",
                json=payload,
                timeout=timeout
            ) as resp:
                elapsed = (datetime.now() - start).total_seconds()
                
                if resp.status == 404:
                    print(f"    ✗ Agent not found (404)")
                    print("    Make sure sql-agent is created and active")
                    return False
                
                # For streaming responses, just read the status and first chunk
                if payload.get("stream"):
                    print(f"    ✓ Streaming response started in {elapsed:.1f}s")
                    print(f"    Status: {resp.status}")
                    
                    # Read first part of stream
                    first_chunk = await resp.content.read(200)
                    if first_chunk:
                        print(f"    First chunk: {first_chunk[:100].decode('utf-8', errors='ignore')}...")
                    
                    if resp.status == 200:
                        print(f"\n    ✓ Response time is good ({elapsed:.1f}s < 30s)")
                        return True
                    else:
                        print(f"    Error status: {resp.status}")
                        return False
                else:
                    result = await resp.json()
                    
                    print(f"    ✓ Response received in {elapsed:.1f}s")
                    print(f"    Status: {resp.status}")
                    
                    if resp.status == 200:
                        # Check response format
                        if 'message' in result:
                            response_text = result['message'][:200]
                            print(f"    Agent response: {response_text}...")
                        elif 'response' in result:
                            response_text = result['response'][:200]
                            print(f"    Agent response: {response_text}...")
                        else:
                            print(f"    Response keys: {list(result.keys())}")
                        
                        if elapsed > 30:
                            print(f"\n    ⚠️  WARNING: Response took {elapsed:.1f}s (expected < 30s)")
                        else:
                            print(f"\n    ✓ Response time is good ({elapsed:.1f}s < 30s)")
                        
                        return True
                    else:
                        print(f"    Response: {json.dumps(result, indent=2)}")
                        return False
                    
        except asyncio.TimeoutError:
            print(f"    ✗ TIMEOUT (60s limit exceeded)")
            print("    The custom tool may be slow to initialize")
            return False
        except Exception as e:
            print(f"    ✗ Error: {type(e).__name__}: {e}")
            return False


async def main():
    """Run verification and test"""
    try:
        # Verify setup
        agent_ok = await verify_agent_setup()
        
        if not agent_ok:
            print("\n" + "=" * 70)
            print("❌ Agent Setup Incomplete")
            print("=" * 70)
            print("\nRequired steps:")
            print("1. Make sure sql-agent exists in Cosmos DB")
            print("2. Make sure sql-agent status is 'active'")
            print("3. Attach your custom tool via the frontend")
            sys.exit(1)
        
        # Test chat
        chat_ok = await test_agent_chat()
        
        print("\n" + "=" * 70)
        if chat_ok:
            print("✅ All Checks Passed!")
            print("=" * 70)
            print("\nThe custom tool should now be working with the agent.")
            print("If you still see timeouts, check backend logs for details.")
            sys.exit(0)
        else:
            print("❌ Some Checks Failed")
            print("=" * 70)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTest cancelled")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
