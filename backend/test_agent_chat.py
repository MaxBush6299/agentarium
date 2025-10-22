"""
Test the sql-agent chat endpoint with the custom MCP tool.
This verifies if the closure bug fix resolved the 30-second timeout.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime


async def test_agent_chat():
    """Test the sql-agent with a simple query"""
    
    payload = {
        'message': 'What tables are in the database?',
        'thread_id': None,
        'stream': False
    }
    
    url = 'http://localhost:8000/api/agents/sql-agent/chat'
    
    print("=" * 70)
    print("Testing sql-agent with custom MCP tool")
    print("=" * 70)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sending chat request to sql-agent...")
    print(f"Message: {payload['message']}")
    print(f"URL: {url}\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Use 60 second timeout
            timeout = aiohttp.ClientTimeout(total=60)
            start = datetime.now()
            
            async with session.post(url, json=payload, timeout=timeout) as resp:
                result = await resp.json()
                elapsed = (datetime.now() - start).total_seconds()
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Response received!")
                print(f"Time elapsed: {elapsed:.1f} seconds")
                print(f"HTTP Status: {resp.status}\n")
                
                if resp.status == 200:
                    print("✓ SUCCESS: Agent responded without timeout!")
                    print("\nResponse:")
                    print(json.dumps(result, indent=2))
                    return True
                else:
                    print(f"✗ ERROR: HTTP {resp.status}")
                    print(f"Response: {json.dumps(result, indent=2)}")
                    return False
                    
        except asyncio.TimeoutError:
            elapsed = (datetime.now() - start).total_seconds()
            print(f"\n✗ TIMEOUT: Agent did not respond within {elapsed:.0f} seconds")
            print("The 30-second timeout issue may still exist.")
            return False
            
        except aiohttp.ClientError as e:
            print(f"\n✗ Connection Error: {e}")
            return False
            
        except Exception as e:
            print(f"\n✗ Unexpected Error: {type(e).__name__}: {e}")
            return False


async def main():
    """Run the test"""
    try:
        success = await test_agent_chat()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
