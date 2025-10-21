import os
import httpx
import json
import base64
from dotenv import load_dotenv

load_dotenv()

# Test v2 endpoint
token_resp = httpx.post(
    'https://login.microsoftonline.com/2e9b0657-eef8-47af-8747-5e89476faaab/oauth2/v2.0/token',
    data={
        'grant_type': 'client_credentials',
        'client_id': os.getenv('ADVENTURE_WORKS_CLIENT_ID'),
        'client_secret': os.getenv('ADVENTURE_WORKS_CLIENT_SECRET'),
        'scope': 'api://17a97781-0078-4478-8b4e-fe5dda9e2400/.default'
    },
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)

print(f'Token Status: {token_resp.status_code}')
if token_resp.status_code == 200:
    token_data = token_resp.json()
    token = token_data.get('access_token', '')
    print(f'Token length: {len(token)}')
    
    # Decode JWT
    parts = token.split('.')
    payload = parts[1] + '=='
    decoded = json.loads(base64.b64decode(payload))
    print(f'Audience (aud): {decoded.get("aud")}')
    print(f'App ID (appid): {decoded.get("appid")}')
    
    # Test MCP server
    mcp_resp = httpx.post(
        os.getenv('ADVENTURE_WORKS_MCP_URL'),
        json={
            'jsonrpc': '2.0',
            'method': 'initialize',
            'id': 1,
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test', 'version': '1.0'}
            }
        },
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )
    print(f'\nMCP Response Status: {mcp_resp.status_code}')
    print(f'MCP Response: {mcp_resp.text[:500]}')
else:
    print(f'Error: {token_resp.text}')
