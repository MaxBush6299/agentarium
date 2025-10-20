"""
MCP Tool Factories

Provides factory functions to create MCP tool instances for use with Agent Framework agents.
Each function returns a configured MCP tool (Stdio, HTTP, or WebSocket) that can be passed
directly to an agent's tools parameter.

Usage:
    async with get_microsoft_learn_tool() as mcp_tool:
        async with ChatAgent(
            chat_client=OpenAIChatClient(),
            tools=mcp_tool
        ) as agent:
            result = await agent.run("How do I create an Azure storage account?")
"""

from typing import Optional
from agent_framework import MCPStdioTool, MCPStreamableHTTPTool


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
# Adventure Works Database MCP Tool (Local)
# =============================================================================

def get_adventure_works_tool(
    server_command: str = "python",
    server_path: str = "./mcp-servers/adventure-works-mcp.py"
) -> MCPStdioTool:
    """
    Create an MCP tool for Adventure Works database queries.
    
    Provides access to the Adventure Works sample database through a local
    MCP server running via stdio. Agents can use this to:
    - Query sales data
    - Get product information
    - Retrieve customer details
    - Generate business reports
    
    Args:
        server_command: Command to run the MCP server (python, python3, etc.)
        server_path: Path to the Adventure Works MCP server script
        
    Returns:
        MCPStdioTool configured for Adventure Works database
        
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
        - Requires Adventure Works MCP server to be installed
        - Server must be executable via the specified command
        - Database connection string configured in server script
        - Uses stdio transport (local process communication)
    """
    return MCPStdioTool(
        name="Adventure Works Database",
        command=server_command,
        args=[server_path],
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
