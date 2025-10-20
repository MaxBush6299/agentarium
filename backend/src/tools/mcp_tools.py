"""MCP Tool Factory Functions.

This module provides factory functions for creating MCP (Model Context Protocol) tool instances.
These tools connect agents to external MCP servers for enhanced capabilities.

Available MCP Tools:
- microsoft-learn: Microsoft Learn documentation and samples
- azure-mcp: Azure-specific MCP services
- adventure-works: Adventure Works sample data and scenarios
"""

import logging

logger = logging.getLogger(__name__)


def get_microsoft_learn_tool():
    """Create and return a Microsoft Learn MCP tool.
    
    This tool provides access to Microsoft Learn documentation, code samples,
    and learning resources.
    
    Returns:
        MCPTool: Configured Microsoft Learn MCP tool instance
        
    Raises:
        ValueError: If tool configuration is invalid
        ConnectionError: If unable to connect to MCP server
    """
    logger.info("Creating Microsoft Learn MCP tool")
    
    # TODO: Implement actual MCP tool creation
    # This will be implemented in Phase 2.6 when we add MCP support
    from unittest.mock import Mock
    return Mock(name="microsoft_learn_tool")


def get_azure_mcp_tool():
    """Create and return an Azure MCP tool.
    
    This tool provides access to Azure-specific documentation, services,
    and resource management through MCP.
    
    Returns:
        MCPTool: Configured Azure MCP tool instance
        
    Raises:
        ValueError: If tool configuration is invalid
        ConnectionError: If unable to connect to MCP server
    """
    logger.info("Creating Azure MCP tool")
    
    # TODO: Implement actual MCP tool creation
    # This will be implemented in Phase 2.6 when we add MCP support
    from unittest.mock import Mock
    return Mock(name="azure_mcp_tool")


def get_adventure_works_tool():
    """Create and return an Adventure Works MCP tool.
    
    This tool provides access to Adventure Works sample database data
    and business scenarios through MCP.
    
    Returns:
        MCPTool: Configured Adventure Works MCP tool instance
        
    Raises:
        ValueError: If tool configuration is invalid
        ConnectionError: If unable to connect to MCP server
    """
    logger.info("Creating Adventure Works MCP tool")
    
    # TODO: Implement actual MCP tool creation
    # This will be implemented in Phase 2.6 when we add MCP support
    from unittest.mock import Mock
    return Mock(name="adventure_works_tool")
