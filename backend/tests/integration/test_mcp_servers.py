"""
Integration tests for MCP (Model Context Protocol) servers.

These tests verify that MCP tools can connect to real MCP servers and perform operations.
They do NOT call Azure OpenAI (no AI costs), but they do require:
- Network connectivity to MCP servers
- Proper authentication/credentials (if required)
- MCP servers to be running/accessible

Run these tests to validate MCP connectivity:
    pytest tests/integration/test_mcp_servers.py -v
    
Skip if not needed:
    pytest tests/ -v -m "not integration"
"""

import os
import pytest

from src.tools.mcp_tools import (
    get_microsoft_learn_tool,
    get_azure_mcp_tool,
    get_adventure_works_tool,
    get_news_tool
)


class TestMicrosoftLearnMCPIntegration:
    """
    Integration tests for Microsoft Learn MCP server.
    
    Microsoft Learn MCP is typically publicly accessible, so these tests
    should work without additional configuration.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_microsoft_learn_mcp_connection(self):
        """
        Integration test: Verify Microsoft Learn MCP server is reachable and functional.
        
        This test validates:
        - MCP tool can be instantiated
        - Connection to Microsoft Learn MCP server succeeds
        - Context manager protocol works (async with)
        
        Cost: $0 (no AI calls)
        Time: 2-5 seconds
        """
        # Get the Microsoft Learn MCP tool
        tool = get_microsoft_learn_tool()
        
        assert tool is not None, "Microsoft Learn tool should be instantiated"
        
        try:
            # Test connection using context manager
            async with tool as mcp_client:
                assert mcp_client is not None, "MCP client should be established"
                print(f"\n✓ Successfully connected to Microsoft Learn MCP server")
                print(f"✓ Tool type: {type(tool).__name__}")
                
        except Exception as e:
            # If connection fails, provide helpful error message
            pytest.fail(
                f"Failed to connect to Microsoft Learn MCP server: {e}\n"
                f"Check network connectivity and MCP server availability."
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_microsoft_learn_mcp_multiple_connections(self):
        """
        Integration test: Verify Microsoft Learn MCP can handle multiple connections.
        
        This validates that the MCP tool properly manages connection lifecycle
        and doesn't have resource leaks.
        
        Cost: $0 (no AI calls)
        Time: 5-10 seconds
        """
        tool = get_microsoft_learn_tool()
        
        # Connect multiple times to verify proper resource management
        connection_count = 3
        
        for i in range(connection_count):
            try:
                async with tool as mcp_client:
                    assert mcp_client is not None
                    print(f"✓ Connection {i+1}/{connection_count} successful")
                    
            except Exception as e:
                pytest.fail(
                    f"Connection {i+1} failed: {e}\n"
                    f"MCP tool may have resource management issues."
                )
        
        print(f"\n✓ All {connection_count} connections succeeded")
        print(f"✓ Resource management working correctly")


class TestAdventureWorksMCPIntegration:
    """
    Integration tests for Adventure Works MCP server.
    
    These tests require Adventure Works MCP server to be configured and running.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("ADVENTURE_WORKS_MCP_URL"),
        reason="Adventure Works MCP not configured (set ADVENTURE_WORKS_MCP_URL)"
    )
    async def test_adventure_works_mcp_connection(self):
        """
        Integration test: Verify Adventure Works MCP server is reachable.
        
        This test validates:
        - Adventure Works MCP tool can be instantiated with custom URL
        - Connection to the configured MCP server succeeds
        - Context manager protocol works
        
        Cost: $0 (no AI calls)
        Time: 2-5 seconds
        """
        # Get the Adventure Works MCP tool (uses ADVENTURE_WORKS_MCP_URL from env)
        tool = get_adventure_works_tool()
        
        assert tool is not None, "Adventure Works tool should be instantiated"
        
        try:
            async with tool as mcp_client:
                assert mcp_client is not None
                print(f"\n✓ Successfully connected to Adventure Works MCP server")
                print(f"✓ Server URL: {os.getenv('ADVENTURE_WORKS_MCP_URL')}")
                
        except Exception as e:
            pytest.fail(
                f"Failed to connect to Adventure Works MCP: {e}\n"
                f"URL: {os.getenv('ADVENTURE_WORKS_MCP_URL')}\n"
                f"Verify server is running and URL is correct."
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("ADVENTURE_WORKS_MCP_URL"),
        reason="Adventure Works MCP not configured"
    )
    async def test_adventure_works_mcp_with_authentication(self):
        """
        Integration test: Verify Adventure Works MCP OAuth 2.0 authentication works.
        
        Adventure Works uses OAuth 2.0 authentication (not API key).
        This test validates that OAuth credentials are properly configured and accepted.
        
        Cost: $0 (no AI calls)
        Time: 2-5 seconds
        """
        # Check for OAuth 2.0 credentials
        client_id = os.getenv("ADVENTURE_WORKS_CLIENT_ID")
        client_secret = os.getenv("ADVENTURE_WORKS_CLIENT_SECRET")
        
        if not (client_id and client_secret):
            pytest.skip("ADVENTURE_WORKS_CLIENT_ID and ADVENTURE_WORKS_CLIENT_SECRET not configured for OAuth 2.0")
        
        # The tool should use OAuth 2.0 credentials from environment
        tool = get_adventure_works_tool()
        
        try:
            async with tool as mcp_client:
                assert mcp_client is not None
                print(f"\n✓ OAuth 2.0 authentication successful with Adventure Works MCP")
                print(f"✓ Client ID configured: {client_id[:8]}...")
                
        except Exception as e:
            pytest.fail(
                f"OAuth 2.0 authentication failed with Adventure Works MCP: {e}\n"
                f"Verify ADVENTURE_WORKS_CLIENT_ID, ADVENTURE_WORKS_CLIENT_SECRET, "
                f"and ADVENTURE_WORKS_OAUTH_TOKEN_URL are correct."
            )


class TestAzureMCPIntegration:
    """
    Integration tests for Azure MCP server.
    
    These tests require Azure MCP server to be running (typically locally or in Azure).
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("AZURE_MCP_URL"),
        reason="Azure MCP not configured (set AZURE_MCP_URL)"
    )
    async def test_azure_mcp_connection(self):
        """
        Integration test: Verify Azure MCP server is reachable.
        
        Cost: $0 (no AI calls)
        Time: 2-5 seconds
        """
        tool = get_azure_mcp_tool()
        
        assert tool is not None
        
        try:
            async with tool as mcp_client:
                assert mcp_client is not None
                print(f"\n✓ Successfully connected to Azure MCP server")
                print(f"✓ Server URL: {os.getenv('AZURE_MCP_URL')}")
                
        except Exception as e:
            pytest.fail(
                f"Failed to connect to Azure MCP: {e}\n"
                f"URL: {os.getenv('AZURE_MCP_URL')}\n"
                f"Verify server is running and URL is correct."
            )


class TestNewsMCPIntegration:
    """
    Integration tests for News MCP server.
    
    These tests require News MCP server to be configured and running.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("NEWS_MCP_URL"),
        reason="News MCP not configured (set NEWS_MCP_URL)"
    )
    async def test_news_mcp_connection(self):
        """
        Integration test: Verify News MCP server is reachable.
        
        Cost: $0 (no AI calls)
        Time: 2-5 seconds
        """
        tool = get_news_tool()
        
        assert tool is not None
        
        try:
            async with tool as mcp_client:
                assert mcp_client is not None
                print(f"\n✓ Successfully connected to News MCP server")
                print(f"✓ Server URL: {os.getenv('NEWS_MCP_URL')}")
                
        except Exception as e:
            pytest.fail(
                f"Failed to connect to News MCP: {e}\n"
                f"URL: {os.getenv('NEWS_MCP_URL')}\n"
                f"Verify server is running and URL is correct."
            )


class TestMCPServerConnectivitySummary:
    """
    Summary test that checks which MCP servers are available.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_servers_availability_summary(self):
        """
        Integration test: Check availability of all configured MCP servers.
        
        This is a "smoke test" that provides an overview of which MCP servers
        are accessible. Useful for quickly diagnosing connectivity issues.
        
        Cost: $0 (no AI calls)
        Time: 10-15 seconds
        """
        results = {
            "Microsoft Learn MCP": {"configured": True, "connected": False, "url": "public"},
            "Adventure Works MCP": {"configured": bool(os.getenv("ADVENTURE_WORKS_MCP_URL")), "connected": False, "url": os.getenv("ADVENTURE_WORKS_MCP_URL", "not set")},
            "Azure MCP": {"configured": bool(os.getenv("AZURE_MCP_URL")), "connected": False, "url": os.getenv("AZURE_MCP_URL", "not set")},
            "News MCP": {"configured": bool(os.getenv("NEWS_MCP_URL")), "connected": False, "url": os.getenv("NEWS_MCP_URL", "not set")},
        }
        
        # Test Microsoft Learn MCP
        try:
            tool = get_microsoft_learn_tool()
            async with tool as mcp_client:
                if mcp_client:
                    results["Microsoft Learn MCP"]["connected"] = True
        except Exception:
            pass
        
        # Test Adventure Works MCP (if configured)
        if results["Adventure Works MCP"]["configured"]:
            try:
                tool = get_adventure_works_tool()
                async with tool as mcp_client:
                    if mcp_client:
                        results["Adventure Works MCP"]["connected"] = True
            except Exception:
                pass
        
        # Test Azure MCP (if configured)
        if results["Azure MCP"]["configured"]:
            try:
                tool = get_azure_mcp_tool()
                async with tool as mcp_client:
                    if mcp_client:
                        results["Azure MCP"]["connected"] = True
            except Exception:
                pass
        
        # Test News MCP (if configured)
        if results["News MCP"]["configured"]:
            try:
                tool = get_news_tool()
                async with tool as mcp_client:
                    if mcp_client:
                        results["News MCP"]["connected"] = True
            except Exception:
                pass
        
        # Print summary
        print("\n" + "="*70)
        print("MCP SERVER CONNECTIVITY SUMMARY")
        print("="*70)
        
        for server_name, status in results.items():
            configured = "✓" if status["configured"] else "✗"
            connected = "✓" if status["connected"] else "✗"
            url = status["url"]
            
            print(f"\n{server_name}:")
            print(f"  Configured: {configured}")
            print(f"  Connected:  {connected}")
            print(f"  URL:        {url}")
        
        print("\n" + "="*70)
        
        # Count results
        total_configured = sum(1 for s in results.values() if s["configured"])
        total_connected = sum(1 for s in results.values() if s["connected"])
        
        print(f"\nConfigured: {total_configured}/4 servers")
        print(f"Connected:  {total_connected}/4 servers")
        
        # Test should pass if at least one MCP server is connected
        assert total_connected >= 1, (
            f"No MCP servers are accessible. "
            f"At least one MCP server should be reachable.\n"
            f"Check network connectivity and server configurations."
        )
        
        print(f"\n✓ At least one MCP server is accessible")
        print(f"✓ MCP connectivity test passed")
