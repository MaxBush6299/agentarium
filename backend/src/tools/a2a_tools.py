"""
A2A (Agent-to-Agent) tool implementations for multi-agent orchestration.

This module provides factories for creating A2A tools that allow agents to call
remote specialist agents via the A2A protocol using the Microsoft Agent Framework.

A2A tools enable the Router Agent to delegate queries to specialized agents:
- SQL Agent: Database queries and operations
- Azure Ops Agent: Azure resource management
- Support Triage Agent: Support ticket analysis
- Data Analytics Agent: Data analysis and insights

Each A2A tool wraps an Agent Framework A2AAgent instance configured with the
remote agent's URL and capabilities.

Usage:
    ```python
    from src.tools.a2a_tools import create_a2a_tool
    
    # Create a tool that calls the SQL Agent
    sql_tool = create_a2a_tool(
        agent_url="http://localhost:8000",
        agent_name="sql-agent",
        agent_description="SQL Query Agent"
    )
    
    # Call the tool
    result = await sql_tool("SELECT * FROM customers")
    ```
"""

from typing import Dict, Any, Optional, Callable, Awaitable
import logging
import httpx
import uuid
from functools import lru_cache

logger = logging.getLogger(__name__)


def create_a2a_tool(
    agent_url: str,
    agent_name: str,
    agent_description: str = ""
) -> Callable[[str], Awaitable[Dict[str, Any]]]:
    """
    Create an A2A tool that calls a remote agent via Agent Framework.
    
    This factory creates a callable tool that sends queries to a remote agent
    using the A2A protocol through the Agent Framework's A2AAgent class.
    
    Args:
        agent_url: Base URL of the remote A2A agent
                   (e.g., "http://localhost:8000")
        agent_name: Name/ID of the agent (e.g., "sql-agent")
        agent_description: Human-readable description of the agent
        
    Returns:
        Async callable that sends queries to the remote agent.
        Returns dict with keys: status, response (or error), agent
        
    Raises:
        ImportError: If agent_framework is not installed
        
    Example:
        ```python
        tool = create_a2a_tool(
            agent_url="http://localhost:8000",
            agent_name="sql-agent",
            agent_description="SQL Query Agent for database operations"
        )
        
        result = await tool("Show top 10 customers")
        # Returns: {
        #     "status": "success",
        #     "response": "Customer data...",
        #     "agent": "sql-agent"
        # }
        ```
    """
    
    async def call_remote_agent(query: str) -> Dict[str, Any]:
        """
        Call a remote agent via A2A protocol.
        
        Uses direct HTTP POST with agent_name in the request to ensure
        proper routing to the correct specialist agent.
        
        Args:
            query: The query/message to send to the remote agent
            
        Returns:
            Dict with:
                - status: "success" or "error"
                - response: Agent's response (if successful)
                - error: Error message (if failed)
                - agent: Name of the agent called
        """
        try:
            logger.debug(f"[A2A] Calling {agent_name} at {agent_url}")
            
            # Build A2A JSON-RPC message with agent name in metadata
            # This allows the A2A endpoint to route to the correct agent
            from datetime import datetime
            
            # Create A2A message per spec Section 7.1
            a2a_message = {
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": query
                    }
                ],
                "messageId": str(uuid.uuid4()),
                "contextId": str(uuid.uuid4()),
                "metadata": {
                    "agent_name": agent_name  # Pass agent name in metadata for routing
                }
            }
            
            # Build JSON-RPC 2.0 request per spec Section 3
            rpc_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "message/send",
                "params": {
                    "message": a2a_message
                }
            }
            
            logger.debug(f"[A2A] Sending JSON-RPC request to {agent_url} with agent_name={agent_name}")
            
            # Send via direct HTTP POST
            async with httpx.AsyncClient(timeout=60.0) as client:
                # agent_url is already the complete /a2a endpoint
                endpoint = agent_url if agent_url.endswith("/a2a") else f"{agent_url}/a2a"
                response = await client.post(
                    endpoint,
                    json=rpc_request,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract response from A2A JSON-RPC response
                if "result" in result and result["result"]:
                    task = result["result"]
                    # Get last message from task history
                    if "history" in task and task["history"]:
                        last_msg = task["history"][-1]
                        if "parts" in last_msg and last_msg["parts"]:
                            response_text = last_msg["parts"][0].get("text", str(last_msg))
                        else:
                            response_text = str(last_msg)
                    else:
                        response_text = str(task)
                    
                    logger.info(f"[A2A] ✓ {agent_name} responded successfully")
                    return {
                        "status": "success",
                        "response": response_text,
                        "agent": agent_name
                    }
                elif "error" in result:
                    error = result["error"]
                    error_msg = error.get("message", "Unknown error")
                    logger.error(f"[A2A] Error from {agent_name}: {error_msg}")
                    return {
                        "status": "error",
                        "error": error_msg,
                        "agent": agent_name
                    }
                else:
                    logger.error(f"[A2A] Unexpected response format from {agent_name}")
                    return {
                        "status": "error",
                        "error": "Unexpected response format",
                        "agent": agent_name,
                        "details": str(result)
                    }
                    
        except httpx.HTTPError as e:
            logger.error(f"[A2A] HTTP error calling {agent_name}: {e}")
            return {
                "status": "error",
                "error": f"HTTP error: {str(e)}",
                "agent": agent_name,
                "details": f"Failed to reach {agent_url}"
            }
        except Exception as e:
            logger.error(f"[A2A] Error calling {agent_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "agent": agent_name
            }
    
    return call_remote_agent


# ============================================================================
# Pre-configured A2A tool factories for specialist agents
# ============================================================================
# These are convenience factories that create A2A tools for specific agents.
# They can be registered in the tool registry for automatic discovery.


def get_sql_agent_tool() -> Callable[[str], Awaitable[Dict[str, Any]]]:
    """
    Get A2A tool for SQL Agent.
    
    The SQL Agent handles:
    - Database queries
    - Data retrieval and analysis
    - Schema exploration
    - Query optimization
    
    Returns:
        Async callable that sends queries to the SQL Agent
    """
    return create_a2a_tool(
        agent_url="http://localhost:8000/a2a",  # Use /a2a endpoint
        agent_name="sql-agent",
        agent_description="SQL Query Agent for database operations and data retrieval"
    )


def get_azure_ops_agent_tool() -> Callable[[str], Awaitable[Dict[str, Any]]]:
    """
    Get A2A tool for Azure Ops Agent.
    
    The Azure Ops Agent handles:
    - Azure resource management
    - Deployment operations
    - Infrastructure queries
    - Cloud operation tasks
    
    Returns:
        Async callable that sends queries to the Azure Ops Agent
    """
    return create_a2a_tool(
        agent_url="http://localhost:8000/a2a",  # Use /a2a endpoint
        agent_name="azure-ops",
        agent_description="Azure Operations Agent for resource management and deployments"
    )


def get_support_triage_agent_tool() -> Callable[[str], Awaitable[Dict[str, Any]]]:
    """
    Get A2A tool for Support Triage Agent.
    
    The Support Triage Agent handles:
    - Support ticket analysis
    - Issue categorization
    - Knowledge base search
    - Ticket routing
    
    Returns:
        Async callable that sends queries to the Support Triage Agent
    """
    return create_a2a_tool(
        agent_url="http://localhost:8000/a2a",  # Use /a2a endpoint
        agent_name="support-triage",
        agent_description="Support Triage Agent for ticket analysis and knowledge base search"
    )


def get_data_analytics_agent_tool() -> Callable[[str], Awaitable[Dict[str, Any]]]:
    """
    Get A2A tool for Data Analytics Agent.
    
    The Data Analytics Agent handles:
    - Data analysis and insights
    - Trend analysis
    - Predictive analytics
    - Report generation
    
    Returns:
        Async callable that sends queries to the Data Analytics Agent
    """
    return create_a2a_tool(
        agent_url="http://localhost:8000/a2a",  # Use /a2a endpoint
        agent_name="data-analytics",
        agent_description="Data Analytics Agent for analysis, trends, and insights"
    )


# ============================================================================
# Tool registry mapping
# ============================================================================
# Maps agent names to their factory functions for convenient lookup


A2A_TOOL_FACTORIES = {
    "sql-agent": get_sql_agent_tool,
    "azure-ops": get_azure_ops_agent_tool,
    "support-triage": get_support_triage_agent_tool,
    "data-analytics": get_data_analytics_agent_tool,
}


def get_a2a_tool_factory(agent_name: str) -> Optional[Callable]:
    """
    Get the factory function for an A2A tool by agent name.
    
    Args:
        agent_name: Name of the agent (e.g., "sql-agent")
        
    Returns:
        Factory function if found, None otherwise
    """
    return A2A_TOOL_FACTORIES.get(agent_name)
