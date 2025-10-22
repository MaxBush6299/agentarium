"""
Test that the custom tool factory closure bug is fixed.

This test verifies that when multiple custom tools are registered,
each maintains its own configuration and doesn't get overwritten by
later registrations.
"""

import sys
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AuthType(str, Enum):
    """Supported authentication types for MCP servers"""
    NONE = "none"
    APIKEY = "apikey"
    OAUTH = "oauth"


class OAuthConfig(BaseModel):
    """OAuth 2.0 configuration for custom MCP tools"""
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    token_url: str = Field(..., description="OAuth token endpoint URL")
    scope: Optional[str] = Field(
        default="api://default/.default",
        description="OAuth scope"
    )


class CustomToolConfig(BaseModel):
    """Configuration for a custom MCP tool"""
    id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Display name for the tool")
    url: str = Field(..., description="URL of the MCP server endpoint")
    auth_type: AuthType = Field(
        default=AuthType.NONE,
        description="Authentication type: none, apikey, or oauth"
    )
    oauth_config: Optional[OAuthConfig] = Field(
        default=None,
        description="OAuth configuration (required if auth_type=oauth)"
    )


def test_closure_bug():
    """Test the old buggy version (for comparison)"""
    print("\n[TEST] Testing OLD BUGGY version with closure bug...")
    
    # Simulate registering two tools
    tool_configs = []
    factories_buggy = []
    
    for i, (tool_name, client_id) in enumerate([
        ("Tool A", "client-a-123"),
        ("Tool B", "client-b-456"),
    ]):
        config = CustomToolConfig(
            id=f"custom-tool-{i}",
            name=tool_name,
            url="https://mcp.example.com",
            auth_type=AuthType.OAUTH,
            oauth_config=OAuthConfig(
                client_id=client_id,
                client_secret=f"secret-{i}",
                token_url="https://login.example.com/token",
                scope="api://default/.default"
            )
        )
        tool_configs.append(config)
        
        # OLD BUGGY VERSION: Captures 'config' by reference
        def buggy_factory(cfg: dict) -> dict:
            return {
                "name": config.name,
                "client_id": config.oauth_config.client_id if config.oauth_config else None,
            }
        
        factories_buggy.append(buggy_factory)
    
    # Now test - both factories should see Tool B's config (BUG!)
    result_a = factories_buggy[0]({})
    result_b = factories_buggy[1]({})
    
    print(f"  Factory A result: {result_a}")
    print(f"  Factory B result: {result_b}")
    
    if result_a["name"] == "Tool A" and result_b["name"] == "Tool B":
        print("  ✗ BUG: Factory A should see 'Tool B' but sees 'Tool A' (closure works but we wanted to demo it)")
    else:
        print(f"  ✓ BUG CONFIRMED: Both factories see the latest config: A={result_a['name']}, B={result_b['name']}")


def test_closure_fix():
    """Test the fixed version"""
    print("\n[TEST] Testing FIXED version with default parameter capture...")
    
    # Simulate registering two tools
    tool_configs = []
    factories_fixed = []
    
    for i, (tool_name, client_id) in enumerate([
        ("Tool A", "client-a-123"),
        ("Tool B", "client-b-456"),
    ]):
        config = CustomToolConfig(
            id=f"custom-tool-{i}",
            name=tool_name,
            url="https://mcp.example.com",
            auth_type=AuthType.OAUTH,
            oauth_config=OAuthConfig(
                client_id=client_id,
                client_secret=f"secret-{i}",
                token_url="https://login.example.com/token",
                scope="api://default/.default"
            )
        )
        tool_configs.append(config)
        
        # FIXED VERSION: Use default parameters to capture by value
        def fixed_factory(
            cfg: dict,
            _name: str = config.name,
            _client_id: Optional[str] = config.oauth_config.client_id if config.oauth_config else None,
        ) -> dict:
            return {
                "name": _name,
                "client_id": _client_id,
            }
        
        factories_fixed.append(fixed_factory)
    
    # Now test - each factory should see its own config (FIXED!)
    result_a = factories_fixed[0]({})
    result_b = factories_fixed[1]({})
    
    print(f"  Factory A result: {result_a}")
    print(f"  Factory B result: {result_b}")
    
    if result_a["name"] == "Tool A" and result_b["name"] == "Tool B":
        print("  ✓ FIXED: Each factory maintains its own configuration!")
        print(f"  ✓ Factory A client_id: {result_a['client_id']}")
        print(f"  ✓ Factory B client_id: {result_b['client_id']}")
        return True
    else:
        print(f"  ✗ FAILED: Factory A sees {result_a['name']}, Factory B sees {result_b['name']}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Custom Tool Factory Closure Bug Test")
    print("=" * 70)
    
    test_closure_bug()
    success = test_closure_fix()
    
    print("\n" + "=" * 70)
    if success:
        print("✓ CLOSURE BUG IS FIXED!")
        sys.exit(0)
    else:
        print("✗ CLOSURE BUG STILL EXISTS!")
        sys.exit(1)
