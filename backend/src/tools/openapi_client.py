"""OpenAPI Tool Factory Functions.

This module provides factory functions for creating OpenAPI tool instances.
These tools wrap OpenAPI-based backend services to provide agent capabilities.

Available OpenAPI Tools:
- support-triage: Support ticket triage and routing service
- ops-assistant: Operations and incident management service
"""

import logging

logger = logging.getLogger(__name__)


def get_support_triage_tool():
    """Create and return a Support Triage OpenAPI tool.
    
    This tool provides access to the support ticket triage service,
    enabling agents to analyze and route support tickets.
    
    Returns:
        OpenAPITool: Configured Support Triage tool instance
        
    Raises:
        ValueError: If tool configuration is invalid
        ConnectionError: If unable to connect to API endpoint
    """
    logger.info("Creating Support Triage OpenAPI tool")
    
    # TODO: Implement actual OpenAPI tool creation
    # This will be implemented in Phase 2.5 when we add Support Triage Agent
    from unittest.mock import Mock
    return Mock(name="support_triage_tool")


def get_ops_assistant_tool():
    """Create and return an Ops Assistant OpenAPI tool.
    
    This tool provides access to the operations and incident management service,
    enabling agents to handle operational tasks and incidents.
    
    Returns:
        OpenAPITool: Configured Ops Assistant tool instance
        
    Raises:
        ValueError: If tool configuration is invalid
        ConnectionError: If unable to connect to API endpoint
    """
    logger.info("Creating Ops Assistant OpenAPI tool")
    
    # TODO: Implement actual OpenAPI tool creation
    # This will be implemented in Phase 2.6 when we add Azure Ops Assistant
    from unittest.mock import Mock
    return Mock(name="ops_assistant_tool")
