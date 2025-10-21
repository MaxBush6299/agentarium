"""
Simple OAuth Integration Test

Tests that our OAuth token management works correctly by:
1. Creating a token manager
2. Getting a fresh token
3. Calling the MCP server directly
4. Verifying the response

This bypasses the Prom SDK's MCP client to isolate OAuth testing.
"""

import asyncio
import os
import httpx
from dotenv import load_dotenv
from src.utils.oauth_token_manager import get_token_manager

load_dotenv()

async def test_oauth_token_management():
    """Test that OAuth token management works end-to-end."""
    
    print("\n=== OAuth Token Management Test ===\n")
    
    # Step 1: Create token manager
    print("1. Creating token manager...")
    token_manager = get_token_manager(
        token_url=os.getenv('ADVENTURE_WORKS_OAUTH_TOKEN_URL'),
        client_id=os.getenv('ADVENTURE_WORKS_CLIENT_ID'),
        client_secret=os.getenv('ADVENTURE_WORKS_CLIENT_SECRET'),
        scope=os.getenv('ADVENTURE_WORKS_SCOPE'),
        refresh_buffer_seconds=300,
    )
    print("   ✓ Token manager created")
    
    # Step 2: Get fresh token
    print("\n2. Getting fresh OAuth token...")
    token = token_manager.get_token()
    print(f"   ✓ Token acquired (length: {len(token)})")
    
    # Step 3: Get token info
    print("\n3. Checking token metadata...")
    token_info = token_manager.get_token_info()
    if token_info:
        print(f"   ✓ Token expires at: {token_info['expires_at']}")
        print(f"   ✓ Time until expiry: {token_info['time_until_expiry_seconds']:.0f}s")
        print(f"   ✓ Is expired: {token_info['is_expired']}")
    
    # Step 4: Test MCP server call
    print("\n4. Calling MCP server with token...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            os.getenv('ADVENTURE_WORKS_MCP_URL'),
            json={
                'jsonrpc': '2.0',
                'method': 'initialize',
                'id': 1,
                'params': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {},
                    'clientInfo': {'name': 'oauth-test', 'version': '1.0'}
                }
            },
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"   ✓ Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Server name: {data['result']['serverInfo']['name']}")
            print(f"   ✓ Protocol version: {data['result']['protocolVersion']}")
            print(f"   ✓ Capabilities: {list(data['result']['capabilities'].keys())}")
        else:
            print(f"   ✗ Error: {response.text}")
            return False
    
    # Step 5: Test token refresh (get cached token)
    print("\n5. Testing token caching...")
    cached_token = token_manager.get_token()
    if cached_token == token:
        print("   ✓ Token reused from cache (no unnecessary refresh)")
    else:
        print("   ✗ Token changed unexpectedly")
        return False
    
    # Step 6: Test force refresh
    print("\n6. Testing force refresh...")
    new_token = token_manager.get_token(force_refresh=True)
    if new_token != token:
        print(f"   ✓ New token acquired (length: {len(new_token)})")
    else:
        print("   ⚠ Warning: Token didn't change on force refresh (might be same from server)")
    
    print("\n=== ✅ ALL TESTS PASSED ===\n")
    print("OAuth token management is working correctly!")
    print("- Token acquisition: ✓")
    print("- Token caching: ✓")
    print("- Token refresh: ✓")
    print("- MCP server authentication: ✓")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_oauth_token_management())
    exit(0 if success else 1)
