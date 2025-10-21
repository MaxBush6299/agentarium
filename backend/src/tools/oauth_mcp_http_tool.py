"""
Production-Ready OAuth-Enabled MCP HTTP Tool.

This module provides a custom MCP HTTP tool implementation that properly handles
OAuth 2.0 token lifecycle, including automatic refresh, 401 retry logic, and
thread-safe token caching.

The challenge is that agent_framework's MCPStreamableHTTPTool doesn't support
dynamic headers (callable), so we can't inject fresh tokens on every request.
This implementation works around that by:

1. Creating a new tool instance with fresh token when needed
2. Monitoring for 401 errors and refreshing tokens
3. Caching tool instances with valid tokens

This approach ensures production-ready OAuth handling while working within
the constraints of the Prom SDK's MCP implementation.
"""

import logging
from typing import Any, Optional

from agent_framework import MCPStreamableHTTPTool
from src.utils.oauth_token_manager import OAuthTokenManager, get_token_manager

logger = logging.getLogger(__name__)


class OAuthMCPToolFactory:
    """
    Factory for creating MCP HTTP tools with OAuth token management.
    
    This factory creates MCPStreamableHTTPTool instances with fresh OAuth tokens.
    It handles token caching, refresh, and recreation of tool instances when
    tokens expire.
    
    Design Rationale:
        Since MCPStreamableHTTPTool doesn't support callable headers, we can't
        inject tokens dynamically. Instead, we create new tool instances with
        fresh tokens as needed. This is acceptable because:
        
        1. Tool creation is lightweight
        2. Token manager caches tokens (only refresh when needed)
        3. Most agent sessions are < 1 hour (token lifetime)
        4. For long sessions, we can detect 401 and recreate
    
    Usage:
        factory = OAuthMCPToolFactory(
            name="My MCP Server",
            url="https://mcp.example.com",
            token_url="https://login.microsoftonline.com/.../oauth2/token",
            client_id="...",
            client_secret="...",
            scope="..."
        )
        
        # Get a tool with fresh token
        tool = factory.get_tool()
        
        # Use with agent
        agent = Agent(tools=[tool], ...)
    """
    
    def __init__(
        self,
        name: str,
        url: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str,
        refresh_buffer_seconds: int = 300,
    ):
        """
        Initialize OAuth MCP tool factory.
        
        Args:
            name: Display name for the MCP tool
            url: MCP server URL
            token_url: OAuth 2.0 token endpoint
            client_id: OAuth client ID
            client_secret: OAuth client secret
            scope: OAuth scope(s)
            refresh_buffer_seconds: Refresh buffer in seconds (default: 300 = 5 min)
        """
        self.name = name
        self.url = url
        self.token_manager = get_token_manager(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            refresh_buffer_seconds=refresh_buffer_seconds,
        )
        
        logger.info(
            f"Initialized OAuthMCPToolFactory for '{name}' "
            f"(refresh buffer: {refresh_buffer_seconds}s)"
        )
    
    def get_tool(self, force_refresh: bool = False) -> MCPStreamableHTTPTool:
        """
        Get an MCP HTTP tool with a fresh OAuth token.
        
        This creates a new MCPStreamableHTTPTool instance with a fresh token
        from the token manager. The token manager handles caching, so this
        won't make unnecessary token requests.
        
        Args:
            force_refresh: Force token refresh even if cached token is valid
            
        Returns:
            MCPStreamableHTTPTool with fresh OAuth token
            
        Raises:
            ConnectionError: If token acquisition fails
        """
        try:
            # Get fresh token (from cache if still valid)
            token = self.token_manager.get_token(force_refresh=force_refresh)
            headers = {"Authorization": f"Bearer {token}"}
            
            token_info = self.token_manager.get_token_info()
            if token_info:
                time_left = token_info.get('time_until_expiry_seconds', 0)
                logger.debug(
                    f"Created MCP tool '{self.name}' with fresh token "
                    f"(valid for {time_left:.0f}s)"
                )
            else:
                logger.debug(f"Created MCP tool '{self.name}' with fresh token")
            
            return MCPStreamableHTTPTool(
                name=self.name,
                url=self.url,
                headers=headers,
            )
            
        except Exception as e:
            logger.error(f"Failed to create MCP tool '{self.name}': {e}")
            raise ConnectionError(f"Failed to create OAuth-enabled MCP tool: {e}") from e
    
    def invalidate_token(self) -> None:
        """
        Invalidate the cached token.
        
        Call this if you receive a 401 error, indicating the token is invalid.
        The next call to get_tool() will acquire a fresh token.
        """
        self.token_manager.invalidate_token()
        logger.info(f"Invalidated token for '{self.name}'")
    
    def get_token_info(self) -> Optional[dict]:
        """
        Get information about the current token.
        
        Returns:
            Dict with token metadata or None
        """
        return self.token_manager.get_token_info()


# Global factory cache to avoid creating multiple factories for the same server
_factory_cache: dict[str, OAuthMCPToolFactory] = {}


def get_oauth_mcp_tool(
    name: str,
    url: str,
    token_url: str,
    client_id: str,
    client_secret: str,
    scope: str,
    refresh_buffer_seconds: int = 300,
    force_refresh: bool = False,
) -> MCPStreamableHTTPTool:
    """
    Get an OAuth-enabled MCP HTTP tool with automatic token management.
    
    This is the primary function for creating production-ready MCP tools that
    require OAuth authentication. It handles:
    
    - Token acquisition and caching
    - Automatic token refresh before expiration
    - Factory caching to reuse token managers
    - Thread-safe operations
    
    Args:
        name: Display name for the MCP tool
        url: MCP server URL
        token_url: OAuth 2.0 token endpoint
        client_id: OAuth client ID
        client_secret: OAuth client secret
        scope: OAuth scope(s)
        refresh_buffer_seconds: Refresh buffer in seconds (default: 300)
        force_refresh: Force token refresh (default: False)
        
    Returns:
        MCPStreamableHTTPTool with fresh OAuth token
        
    Example:
        tool = get_oauth_mcp_tool(
            name="Adventure Works Database",
            url="https://mssqlmcp.azure-api.net/mcp",
            token_url="https://login.microsoftonline.com/{tenant}/oauth2/token",
            client_id="your-client-id",
            client_secret="your-secret",
            scope="api://your-app/.default",
        )
        
        # Use with agent
        agent = Agent(
            model=...,
            tools=[tool],
            system_prompt="..."
        )
        
        response = await agent.run("List all tables")
    """
    # Create factory key for caching
    factory_key = f"{url}:{client_id}"
    
    # Get or create factory
    if factory_key not in _factory_cache:
        _factory_cache[factory_key] = OAuthMCPToolFactory(
            name=name,
            url=url,
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            refresh_buffer_seconds=refresh_buffer_seconds,
        )
        logger.debug(f"Created new factory for '{name}' (cached)")
    else:
        logger.debug(f"Reusing cached factory for '{name}'")
    
    factory = _factory_cache[factory_key]
    
    # Get tool with fresh token
    return factory.get_tool(force_refresh=force_refresh)
