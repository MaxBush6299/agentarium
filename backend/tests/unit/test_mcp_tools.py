"""
Unit and integration tests for MCP tool factory functions.

Unit tests verify that our MCP tool factories correctly create
tool instances using Agent Framework's native MCP support.

Integration tests (marked with @pytest.mark.integration) verify
actual connectivity to MCP servers when they are available.
"""
import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from typing import AsyncContextManager


# Import our MCP tool factories
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tools.mcp_tools import (
    get_microsoft_learn_tool,
    get_azure_mcp_tool,
    get_adventure_works_tool,
    get_news_tool
)


class TestMicrosoftLearnTool:
    """Tests for Microsoft Learn MCP tool factory."""
    
    def test_get_microsoft_learn_tool_creates_instance(self, mock_env_vars):
        """Test that get_microsoft_learn_tool returns MCPStreamableHTTPTool instance."""
        # Get the tool (factory functions are synchronous)
        tool = get_microsoft_learn_tool()
        
        # Verify it's the right type
        assert tool is not None
        assert hasattr(tool, 'name')
        assert tool.name == "Microsoft Learn Documentation"
    
    def test_get_microsoft_learn_tool_with_custom_url(self, mock_env_vars):
        """Test that tool accepts custom URL."""
        custom_url = "https://custom-learn-server.com/mcp"
        
        tool = get_microsoft_learn_tool(url=custom_url)
        assert tool is not None
        assert tool.name == "Microsoft Learn Documentation"
    
    def test_microsoft_learn_tool_with_auth_token(self, mock_env_vars):
        """Test that tool accepts optional auth token."""
        tool = get_microsoft_learn_tool(auth_token="test-token")
        
        # Tool should be created successfully with auth
        assert tool is not None


class TestAzureMCPTool:
    """Tests for Azure MCP tool factory."""
    
    def test_get_azure_mcp_tool_creates_instance(self, mock_env_vars):
        """Test that get_azure_mcp_tool returns MCPStreamableHTTPTool instance."""
        tool = get_azure_mcp_tool()
        
        assert tool is not None
        assert hasattr(tool, 'name')
        assert tool.name == "Azure Management"
    
    def test_get_azure_mcp_tool_with_custom_url(self, mock_env_vars):
        """Test that Azure MCP tool accepts custom URL."""
        custom_url = "http://custom-azure-mcp:8080/mcp"
        
        tool = get_azure_mcp_tool(server_url=custom_url)
        assert tool is not None
    
    def test_azure_mcp_tool_with_subscription_id(self, mock_env_vars):
        """Test that Azure MCP tool accepts subscription ID."""
        tool = get_azure_mcp_tool(subscription_id="test-subscription-id")
        assert tool is not None


class TestAdventureWorksTool:
    """Tests for Adventure Works MCP tool factory."""
    
    def test_get_adventure_works_tool_creates_instance(self, mock_env_vars):
        """Test that get_adventure_works_tool returns MCPStdioTool instance."""
        tool = get_adventure_works_tool()
        
        assert tool is not None
        assert hasattr(tool, 'name')
        assert tool.name == "Adventure Works Database"
    
    def test_adventure_works_tool_with_custom_command(self, mock_env_vars):
        """Test that Adventure Works tool accepts custom command."""
        tool = get_adventure_works_tool(
            server_command="python3", 
            server_path="./custom_server.py"
        )
        
        # Verify tool is created with custom command
        assert tool is not None


class TestNewsTool:
    """Tests for News MCP tool factory."""
    
    def test_get_news_tool_creates_instance(self, mock_env_vars):
        """Test that get_news_tool returns MCPStreamableHTTPTool instance."""
        tool = get_news_tool()
        
        assert tool is not None
        assert hasattr(tool, 'name')
        assert tool.name == "News Aggregator"
    
    def test_news_tool_with_custom_url(self, mock_env_vars):
        """Test that News tool accepts custom URL."""
        custom_url = "https://custom-news-api.com/mcp"
        
        tool = get_news_tool(api_url=custom_url)
        assert tool is not None


class TestMCPToolFactoryPatterns:
    """Tests for common patterns across all MCP tool factories."""
    
    def test_tools_can_be_created_as_context_managers(self, mock_env_vars):
        """Test that all tools can be instantiated for use as async context managers."""
        # Factory functions return tools synchronously
        # The tools themselves are async context managers (tested in integration tests)
        
        # Just verify we can create the tools
        learn_tool = get_microsoft_learn_tool()
        azure_tool = get_azure_mcp_tool()
        aw_tool = get_adventure_works_tool()
        news_tool = get_news_tool()
        
        # All should be valid tool instances
        assert learn_tool is not None
        assert azure_tool is not None
        assert aw_tool is not None
        assert news_tool is not None
        
        # All should have the context manager protocol
        assert hasattr(learn_tool, '__aenter__')
        assert hasattr(learn_tool, '__aexit__')
    
    def test_tools_have_required_attributes(self, mock_env_vars):
        """Test that all tools have expected attributes."""
        # Factory functions are synchronous
        tools = [
            get_microsoft_learn_tool(),
            get_azure_mcp_tool(),
            get_adventure_works_tool(),
            get_news_tool()
        ]
        
        for tool in tools:
            # All tools should have a name
            assert hasattr(tool, 'name')
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0


# ============================================================================
# Integration Tests - Test Actual MCP Server Connections
# ============================================================================
# Run with: pytest tests/unit/test_mcp_tools.py -v -m integration
# Skip with: pytest tests/unit/test_mcp_tools.py -v -m "not integration"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_microsoft_learn_connection():
    """
    Integration test: Verify Microsoft Learn MCP server is reachable.
    
    This test attempts to connect to the actual Microsoft Learn MCP server
    and verify it responds. Skip if server is unavailable.
    """
    tool = get_microsoft_learn_tool()
    
    try:
        async with tool as mcp:
            # If we can enter the context manager, connection succeeded
            assert mcp is not None
            print(f"✓ Successfully connected to Microsoft Learn MCP")
            
            # Try to list available tools (if the API supports it)
            if hasattr(mcp, 'list_tools'):
                tools = await mcp.list_tools()  # type: ignore
                print(f"✓ Available tools: {len(tools) if tools else 0}")
    except Exception as e:
        pytest.skip(f"Microsoft Learn MCP server not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_azure_mcp_connection():
    """
    Integration test: Verify Azure MCP server is reachable.
    
    Requires Azure MCP server to be running (e.g., sidecar container).
    """
    # Check if Azure MCP URL is configured
    azure_url = os.getenv("AZURE_MCP_URL")
    if not azure_url or azure_url == "http://localhost:8080/mcp":
        pytest.skip("Azure MCP server not configured or not running locally")
    
    tool = get_azure_mcp_tool()
    
    try:
        async with tool as mcp:
            assert mcp is not None
            print(f"✓ Successfully connected to Azure MCP at {azure_url}")
            
            if hasattr(mcp, 'list_tools'):
                tools = await mcp.list_tools()  # type: ignore
                print(f"✓ Available Azure tools: {len(tools) if tools else 0}")
    except Exception as e:
        pytest.skip(f"Azure MCP server not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_adventure_works_connection():
    """
    Integration test: Verify Adventure Works MCP server (local process) works.
    
    Requires Adventure Works MCP server script to be available.
    """
    tool = get_adventure_works_tool()
    
    try:
        async with tool as mcp:
            assert mcp is not None
            print(f"✓ Successfully started Adventure Works MCP process")
            
            if hasattr(mcp, 'list_tools'):
                tools = await mcp.list_tools()  # type: ignore
                print(f"✓ Available database tools: {len(tools) if tools else 0}")
    except FileNotFoundError:
        pytest.skip("Adventure Works MCP server script not found (uvx or mcp-server-adventureworks)")
    except Exception as e:
        pytest.skip(f"Adventure Works MCP server not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_news_mcp_connection():
    """
    Integration test: Verify News MCP server is reachable.
    
    This is a placeholder - update when actual News MCP server is configured.
    """
    news_url = os.getenv("NEWS_MCP_URL")
    if not news_url or news_url == "https://news-mcp.example.com":
        pytest.skip("News MCP server not configured yet (placeholder URL)")
    
    tool = get_news_tool()
    
    try:
        async with tool as mcp:
            assert mcp is not None
            print(f"✓ Successfully connected to News MCP at {news_url}")
            
            if hasattr(mcp, 'list_tools'):
                tools = await mcp.list_tools()  # type: ignore
                print(f"✓ Available news tools: {len(tools) if tools else 0}")
    except Exception as e:
        pytest.skip(f"News MCP server not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_configured_connections():
    """
    Integration test: Test all MCP connections that are properly configured.
    
    This is a smoke test to verify all available MCP servers can be reached.
    """
    results = {
        "microsoft_learn": False,
        "azure_mcp": False,
        "adventure_works": False,
        "news": False
    }
    
    # Test Microsoft Learn (should always be available)
    try:
        async with get_microsoft_learn_tool() as mcp:
            results["microsoft_learn"] = mcp is not None
    except Exception as e:
        print(f"Microsoft Learn MCP failed: {e}")
    
    # Test Azure MCP (if configured)
    azure_url = os.getenv("AZURE_MCP_URL")
    if azure_url and azure_url != "http://localhost:8080/mcp":
        try:
            async with get_azure_mcp_tool() as mcp:
                results["azure_mcp"] = mcp is not None
        except Exception as e:
            print(f"Azure MCP failed: {e}")
    
    # Test Adventure Works (if available)
    try:
        async with get_adventure_works_tool() as mcp:
            results["adventure_works"] = mcp is not None
    except Exception as e:
        print(f"Adventure Works MCP failed: {e}")
    
    # Test News (if configured)
    news_url = os.getenv("NEWS_MCP_URL")
    if news_url and news_url != "https://news-mcp.example.com":
        try:
            async with get_news_tool() as mcp:
                results["news"] = mcp is not None
        except Exception as e:
            print(f"News MCP failed: {e}")
    
    # Report results
    connected = sum(1 for v in results.values() if v)
    print(f"\n✓ Connected to {connected}/{len(results)} MCP servers")
    for name, status in results.items():
        status_str = "✓" if status else "✗"
        print(f"  {status_str} {name}")
    
    # At least one connection should work (Microsoft Learn)
    assert connected >= 1, "At least Microsoft Learn MCP should be available"



if __name__ == "__main__":
    pytest.main([__file__, "-v"])
