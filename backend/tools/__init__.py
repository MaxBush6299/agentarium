"""
Agent Tools Module

This module provides MCP (Model Context Protocol) tool connections for agents.
Uses Agent Framework's built-in MCPStdioTool, MCPStreamableHTTPTool, and MCPWebsocketTool.
"""

from .mcp_tools import (
    get_microsoft_learn_tool,
    get_azure_mcp_tool,
    get_adventure_works_tool,
)

__all__ = [
    "get_microsoft_learn_tool",
    "get_azure_mcp_tool", 
    "get_adventure_works_tool",
]
