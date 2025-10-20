# Agent Tools - MCP Infrastructure

This directory contains MCP (Model Context Protocol) tool factories for connecting agents to various data sources and services.

Uses **Agent Framework's built-in MCP support** - no custom client code needed!

## Quick Start

```python
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from tools import get_microsoft_learn_tool

async def example():
    async with get_microsoft_learn_tool() as learn_tool:
        async with ChatAgent(
            chat_client=OpenAIChatClient(),
            name="DocsAgent",
            instructions="You help with Microsoft documentation.",
            tools=learn_tool  # Pass MCP tool directly
        ) as agent:
            result = await agent.run("How to create Azure storage account?")
            print(result)
```

## Architecture

```
tools/
├── __init__.py          # Package exports
├── mcp_tools.py         # MCP tool factory functions
└── README.md            # This file
```

## MCP Tool Types

Agent Framework provides **native MCP support** through three tool types:

| Tool Type | Use Case | Connection Method |
|-----------|----------|-------------------|
| `MCPStdioTool` | Local MCP servers | Standard input/output (command-line) |
| `MCPStreamableHTTPTool` | Remote HTTP MCP servers | HTTP with Server-Sent Events (SSE) |
| `MCPWebsocketTool` | Real-time MCP servers | WebSocket connections |

## Available Factory Functions

### 1. `get_microsoft_learn_tool()` ⭐

**Type:** `MCPStreamableHTTPTool` (HTTP/SSE)

Connects to Microsoft Learn documentation MCP server for technical documentation search.

```python
from tools import get_microsoft_learn_tool

async with get_microsoft_learn_tool() as learn_tool:
    async with ChatAgent(
        chat_client=OpenAIChatClient(),
        tools=learn_tool
    ) as agent:
        result = await agent.run("How to deploy Bicep templates?")
```

**Capabilities:**
- Search Microsoft technical documentation
- Get code examples and samples
- Find how-to guides and tutorials
- Access API references

**Parameters:**
- `url` (str): MCP server URL (default: `https://learn.microsoft.com/api/mcp`)
- `auth_token` (Optional[str]): Authentication token if required

---

### 2. `get_azure_mcp_tool()` ⭐

**Type:** `MCPStreamableHTTPTool` (HTTP/SSE)

Connects to Azure MCP server for Azure resource management operations.

```python
from tools import get_azure_mcp_tool

async with get_azure_mcp_tool() as azure_tool:
    async with ChatAgent(
        chat_client=OpenAIChatClient(),
        tools=azure_tool
    ) as agent:
        result = await agent.run("List all storage accounts")
```

**Capabilities:**
- Query Azure resources
- Get resource properties
- List resources by type
- Check resource status

**Parameters:**
- `server_url` (Optional[str]): Azure MCP server URL (default: `http://localhost:8080/mcp`)
- `subscription_id` (Optional[str]): Azure subscription ID

**Notes:**
- Assumes Azure MCP server is running (sidecar container or local)
- Uses managed identity for authentication in Azure
- Defaults to localhost:8080 for development

---

### 3. `get_adventure_works_tool()`

**Type:** `MCPStdioTool` (Local command-line)

Connects to Adventure Works database through a local MCP server for SQL queries.

```python
from tools import get_adventure_works_tool

async with get_adventure_works_tool() as aw_tool:
    async with ChatAgent(
        chat_client=OpenAIChatClient(),
        tools=aw_tool
    ) as agent:
        result = await agent.run("What were total sales last quarter?")
```

**Capabilities:**
- Query sales data
- Get product information
- Retrieve customer details
- Generate business reports

**Parameters:**
- `server_command` (str): Command to run MCP server (default: `"python"`)
- `server_path` (str): Path to MCP server script (default: `"./mcp-servers/adventure-works-mcp.py"`)

**Requirements:**
- Adventure Works MCP server script must be installed
- Database connection configured in server script
- Python executable must be available

---

### 4. `get_news_tool()`

**Type:** `MCPStreamableHTTPTool` (HTTP/SSE)

Connects to news aggregation API through MCP for latest news retrieval.

```python
from tools import get_news_tool

async with get_news_tool(api_key="your-key") as news_tool:
    async with ChatAgent(
        chat_client=OpenAIChatClient(),
        tools=news_tool
    ) as agent:
        result = await agent.run("What are today's top tech stories?")
```

**Capabilities:**
- Search latest news
- Filter by category/topic
- Get trending stories
- Retrieve article summaries

**Parameters:**
- `api_url` (str): News MCP server URL (default: `https://api.news-aggregator.com/mcp`)
- `api_key` (Optional[str]): API key for authentication

## Usage Patterns

### Single MCP Tool

```python
async with get_microsoft_learn_tool() as tool:
    async with ChatAgent(
        chat_client=OpenAIChatClient(),
        tools=tool
    ) as agent:
        result = await agent.run("Your query")
```

### Multiple MCP Tools

```python
async with (
    get_microsoft_learn_tool() as learn_tool,
    get_azure_mcp_tool() as azure_tool,
):
    async with ChatAgent(
        chat_client=OpenAIChatClient(),
        tools=[learn_tool, azure_tool]  # Pass as list
    ) as agent:
        result = await agent.run("Your query")
```

### With Azure Credentials

```python
from azure.identity.aio import AzureCliCredential
from agent_framework.azure import AzureAIAgentClient

async with AzureCliCredential() as credential:
    async with get_azure_mcp_tool() as azure_tool:
        async with ChatAgent(
            chat_client=AzureAIAgentClient(async_credential=credential),
            tools=azure_tool
        ) as agent:
            result = await agent.run("Your query")
```

## Key Benefits

✅ **No Custom Client Code** - Uses Agent Framework's built-in MCP support  
✅ **Async Context Managers** - Proper resource lifecycle management  
✅ **Direct Integration** - Pass tools directly to agent's `tools` parameter  
✅ **Multiple Transports** - Stdio, HTTP/SSE, and WebSocket support  
✅ **Official Servers** - Connects to Microsoft's official MCP servers  
✅ **Type Safety** - Fully typed with proper hints  

## Resources

- [Agent Framework MCP Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/model-context-protocol/using-mcp-tools)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [Official MCP Servers](https://github.com/modelcontextprotocol)
- [Azure MCP Server](https://github.com/microsoft/azure-mcp-server)
