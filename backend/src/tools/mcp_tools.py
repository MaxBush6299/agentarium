"""
MCP Tool Factories

Provides factory functions to create MCP tool instances for use with Agent Framework agents.
Each function returns a configured MCP tool (Stdio, HTTP, or WebSocket) that can be passed
directly to an agent's tools parameter.

For OAuth-enabled MCP tools, see oauth_mcp_http_tool.py for production-ready token management.

Usage:
    async with get_microsoft_learn_tool() as mcp_tool:
        async with ChatAgent(
            chat_client=OpenAIChatClient(),
            tools=mcp_tool
        ) as agent:
            result = await agent.run("How do I create an Azure storage account?")
"""

import logging
from typing import Optional
from agent_framework import MCPStdioTool, MCPStreamableHTTPTool

logger = logging.getLogger(__name__)


# =============================================================================
# Microsoft Learn Documentation MCP Tool
# =============================================================================

def get_microsoft_learn_tool(
    url: str = "https://learn.microsoft.com/api/mcp",
    auth_token: Optional[str] = None
) -> MCPStreamableHTTPTool:
    """
    Create an MCP tool for Microsoft Learn documentation search.
    
    Provides access to official Microsoft documentation through the
    Microsoft Learn MCP server. Agents can use this to:
    - Search technical documentation
    - Get code examples
    - Find how-to guides
    - Access API references
    
    Args:
        url: The Microsoft Learn MCP server URL
        auth_token: Optional authentication token (if required)
        
    Returns:
        MCPStreamableHTTPTool configured for Microsoft Learn
        
    Example:
        ```python
        async with get_microsoft_learn_tool() as learn_tool:
            async with ChatAgent(
                chat_client=OpenAIChatClient(),
                name="DocsAgent",
                instructions="You help with Microsoft documentation.",
                tools=learn_tool
            ) as agent:
                result = await agent.run(
                    "How to create Azure storage account?"
                )
        ```
    
    Note:
        - URL may change based on Microsoft Learn API availability
        - Check https://learn.microsoft.com for current MCP endpoint
        - May require authentication in the future
    """
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    return MCPStreamableHTTPTool(
        name="Microsoft Learn Documentation",
        url=url,
        headers=headers if headers else None,
    )


# =============================================================================
# Azure MCP Tool
# =============================================================================

def get_azure_mcp_tool(
    server_url: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> MCPStreamableHTTPTool:
    """
    Create an MCP tool for Azure operations.
    
    Provides access to Azure management operations through the Azure MCP server.
    Agents can use this to:
    - Query Azure resources
    - Get resource properties
    - List resources by type
    - Check resource status
    
    Args:
        server_url: URL of the Azure MCP server (defaults to sidecar container)
        subscription_id: Azure subscription ID to use
        
    Returns:
        MCPStreamableHTTPTool configured for Azure operations
        
    Example:
        ```python
        async with get_azure_mcp_tool() as azure_tool:
            async with ChatAgent(
                chat_client=OpenAIChatClient(),
                name="AzureOpsAgent",
                instructions="You help manage Azure resources.",
                tools=azure_tool
            ) as agent:
                result = await agent.run(
                    "List all storage accounts in my subscription"
                )
        ```
    
    Note:
        - Assumes Azure MCP server is running (e.g., sidecar container)
        - Uses managed identity for authentication when in Azure
        - Defaults to http://localhost:8080 for local development
    """
    # Default to sidecar container in production, localhost in dev
    url = server_url or "http://localhost:8080/mcp"
    
    headers = {}
    if subscription_id:
        headers["X-Azure-Subscription-Id"] = subscription_id
    
    return MCPStreamableHTTPTool(
        name="Azure Management",
        url=url,
        headers=headers if headers else None,
    )


# =============================================================================
# Adventure Works Database MCP Tool (HTTP with OAuth)
# =============================================================================

def get_adventure_works_tool(
    server_url: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    token_url: Optional[str] = None,
    scope: Optional[str] = None,
) -> MCPStreamableHTTPTool:
    """
    Create an MCP tool for Adventure Works database queries.
    
    Provides access to the Adventure Works sample database through a deployed
    MCP server using OAuth 2.0 authentication. Agents can use this to:
    - Query sales data
    - Get product information
    - Retrieve customer details
    - Generate business reports
    - Execute SQL queries safely
    
    Args:
        server_url: URL of the Adventure Works MCP server 
                   (defaults to ADVENTURE_WORKS_MCP_URL from env)
        client_id: OAuth client ID (defaults to env var)
        client_secret: OAuth client secret (defaults to env var)
        token_url: OAuth token endpoint (defaults to env var)
        scope: OAuth scope (defaults to env var)
        
    Returns:
        MCPStreamableHTTPTool configured for Adventure Works database
        
    Example:
        ```python
        async with get_adventure_works_tool() as aw_tool:
            async with ChatAgent(
                chat_client=OpenAIChatClient(),
                name="SalesAgent",
                instructions="You analyze sales data from Adventure Works.",
                tools=aw_tool
            ) as agent:
                result = await agent.run(
                    "What were total sales last quarter?"
                )
        ```
    
    Note:
        - Uses OAuth 2.0 client credentials flow with automatic token refresh
        - Tokens cached and refreshed automatically 5 minutes before expiration
        - Deployed MCP server handles database connections
        - SQL injection protection built into MCP server
        - Read-only access to database
        - Production-ready: handles token expiration, 401 errors, concurrent requests
    """
    import os
    from src.tools.oauth_mcp_http_tool import get_oauth_mcp_tool
    
    # Get configuration from environment or parameters
    url = server_url or os.getenv("ADVENTURE_WORKS_MCP_URL", "https://mssqlmcp.azure-api.net/mcp")
    oauth_client_id = client_id or os.getenv("ADVENTURE_WORKS_CLIENT_ID")
    oauth_client_secret = client_secret or os.getenv("ADVENTURE_WORKS_CLIENT_SECRET")
    oauth_token_url = token_url or os.getenv("ADVENTURE_WORKS_OAUTH_TOKEN_URL")
    oauth_scope = scope or os.getenv("ADVENTURE_WORKS_SCOPE", "api://17a97781-0078-4478-8b4e-fe5dda9e2400/.default")
    
    # Configure OAuth with automatic token refresh
    if oauth_client_id and oauth_client_secret and oauth_token_url:
        logger.info("Creating Adventure Works MCP tool with production OAuth token management")
        
        # Use the production-ready OAuth MCP tool factory
        return get_oauth_mcp_tool(
            name="Adventure Works Database",
            url=url,
            token_url=oauth_token_url,
            client_id=oauth_client_id,
            client_secret=oauth_client_secret,
            scope=oauth_scope,
            refresh_buffer_seconds=300,  # Refresh 5 minutes before expiration
        )
    else:
        # Fallback to no auth (for local development)
        logger.warning("Adventure Works OAuth credentials not configured, using unauthenticated connection")
        return MCPStreamableHTTPTool(
            name="Adventure Works Database",
            url=url,
        )


def get_mssql_tool(
    server_url: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    token_url: Optional[str] = None,
    scope: Optional[str] = None,
) -> MCPStreamableHTTPTool:
    """
    Create a generic MCP tool for MSSQL database queries.
    
    This is a generic wrapper that connects to any MSSQL database configured
    in the MCP server. The tool supports dynamic tool discovery, allowing agents
    to discover available operations like list_tables, describe_table, read_data, etc.
    
    Configuration:
    - Uses same environment variables as Adventure Works tool
    - Database selection happens at the MCP server level
    - Changing the database doesn't require agent code changes
    
    Args:
        server_url: URL of the MSSQL MCP server 
                   (defaults to ADVENTURE_WORKS_MCP_URL from env)
        client_id: OAuth client ID (defaults to env var)
        client_secret: OAuth client secret (defaults to env var)
        token_url: OAuth token endpoint (defaults to env var)
        scope: OAuth scope (defaults to env var)
        
    Returns:
        MCPStreamableHTTPTool configured for MSSQL database operations
        
    Example:
        ```python
        # Create agent with MSSQL tool
        mssql_tool = get_mssql_tool()
        agent = SQLAgent.create()
        
        # Agent can discover schema and query any configured database
        response = await agent.run("What tables are available?")
        response = await agent.run("Describe the Sales.Customer table")
        response = await agent.run("What are the top 10 customers?")
        ```
    
    Note:
        - Uses dynamic tool discovery for flexibility
        - OAuth 2.0 client credentials flow for security
        - Database-agnostic - works with any MSSQL database
        - Read-only access enforced by MCP server
    """
    # Reuse the same implementation as Adventure Works tool since they connect to same server
    # The difference is conceptual - this is database-agnostic
    return get_adventure_works_tool(
        server_url=server_url,
        client_id=client_id,
        client_secret=client_secret,
        token_url=token_url,
        scope=scope,
    )


# =============================================================================
# News API MCP Tool (if using external news service)
# =============================================================================

def get_news_tool(
    api_url: str = "https://api.news-aggregator.com/mcp",
    api_key: Optional[str] = None
) -> MCPStreamableHTTPTool:
    """
    Create an MCP tool for news aggregation.
    
    Provides access to news APIs through an MCP server. Agents can use this to:
    - Search latest news
    - Filter by category/topic
    - Get trending stories
    - Retrieve article summaries
    
    Args:
        api_url: URL of the news MCP server
        api_key: API key for authentication
        
    Returns:
        MCPStreamableHTTPTool configured for news access
        
    Example:
        ```python
        async with get_news_tool(api_key="your-key") as news_tool:
            async with ChatAgent(
                chat_client=OpenAIChatClient(),
                name="NewsAgent",
                instructions="You provide latest news summaries.",
                tools=news_tool
            ) as agent:
                result = await agent.run(
                    "What are today's top tech stories?"
                )
        ```
    
    Note:
        - Requires valid API key from news provider
        - May have rate limits depending on provider
        - Consider caching for frequently requested topics
    """
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    
    return MCPStreamableHTTPTool(
        name="News Aggregator",
        url=api_url,
        headers=headers if headers else None,
    )


# =============================================================================
# Custom MCP Tool Factory
# =============================================================================

def get_custom_mcp_tool(
    name: str,
    url: str,
    auth_type: str = "none",
    api_key: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    token_url: Optional[str] = None,
    scope: Optional[str] = None,
) -> MCPStreamableHTTPTool:
    """
    Create a custom MCP tool with flexible authentication support.
    
    Allows registration of any HTTP-based MCP server with support for:
    - No authentication
    - API Key (header-based)
    - OAuth 2.0 client credentials
    
    Args:
        name: Display name for the custom MCP tool
        url: URL of the MCP server endpoint
        auth_type: Authentication type: "none", "apikey", or "oauth"
        api_key: API key for header-based auth (required if auth_type="apikey")
        client_id: OAuth client ID (required if auth_type="oauth")
        client_secret: OAuth client secret (required if auth_type="oauth")
        token_url: OAuth token endpoint (required if auth_type="oauth")
        scope: OAuth scope (optional, defaults to standard scope)
        
    Returns:
        MCPStreamableHTTPTool configured for the custom MCP server
        
    Example:
        ```python
        # No auth
        async with get_custom_mcp_tool(
            name="My Custom Database",
            url="http://localhost:8001/mcp",
            auth_type="none"
        ) as tool:
            async with ChatAgent(tools=tool) as agent:
                result = await agent.run("Query my database...")
        
        # With API Key
        async with get_custom_mcp_tool(
            name="Premium API",
            url="https://api.example.com/mcp",
            auth_type="apikey",
            api_key="sk-1234567890"
        ) as tool:
            async with ChatAgent(tools=tool) as agent:
                result = await agent.run("Query the premium API...")
        
        # With OAuth
        async with get_custom_mcp_tool(
            name="Adventure Works",
            url="https://mssqlmcp.azure-api.net/mcp",
            auth_type="oauth",
            client_id="17a97781-0078-4478-8b4e-fe5dda9e2400",
            client_secret="Kyb8Q~FL6eva5m6pbe...",
            token_url="https://login.microsoftonline.com/.../oauth2/v2.0/token",
            scope="api://17a97781-0078-4478-8b4e-fe5dda9e2400/.default"
        ) as tool:
            async with ChatAgent(tools=tool) as agent:
                result = await agent.run("Query Adventure Works...")
        ```
    
    Note:
        - OAuth credentials are handled securely with automatic token refresh
        - API keys are passed in X-API-Key header
        - All credentials should come from secure configuration (env vars, Key Vault)
        - Production deployments should use Key Vault for credential storage
    """
    from src.tools.oauth_mcp_http_tool import get_oauth_mcp_tool
    
    logger.info(f"Creating custom MCP tool '{name}' with auth_type='{auth_type}'")
    
    if auth_type.lower() == "oauth":
        if not all([client_id, client_secret, token_url]):
            raise ValueError(
                f"OAuth auth_type requires client_id, client_secret, and token_url. "
                f"Got: client_id={bool(client_id)}, client_secret={bool(client_secret)}, "
                f"token_url={bool(token_url)}"
            )
        
        # Use OAuth MCP tool with automatic token management
        return get_oauth_mcp_tool(
            name=name,
            url=url,
            token_url=token_url,  # type: ignore
            client_id=client_id,  # type: ignore
            client_secret=client_secret,  # type: ignore
            scope=scope or "api://default/.default",
            refresh_buffer_seconds=300,
        )
    
    elif auth_type.lower() == "apikey":
        if not api_key:
            raise ValueError("API Key auth_type requires api_key parameter")
        
        headers = {"X-API-Key": api_key}
        return MCPStreamableHTTPTool(
            name=name,
            url=url,
            headers=headers,
        )
    
    elif auth_type.lower() == "none":
        # No authentication
        return MCPStreamableHTTPTool(
            name=name,
            url=url,
        )
    
    else:
        raise ValueError(
            f"Unsupported auth_type '{auth_type}'. "
            f"Supported values: 'none', 'apikey', 'oauth'"
        )

