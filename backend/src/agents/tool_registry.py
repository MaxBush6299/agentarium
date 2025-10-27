"""
Tool Registry for centralized tool factory management.

This module provides a registry pattern for tool instantiation, enabling:
- Lazy loading of tools on demand
- Graceful failure handling (tool failures don't crash agent)
- Easy registration of new tool types
- Dynamic tool discovery and configuration

The registry maps (tool_type, tool_name) to factory functions that create tool instances.
"""

from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """
    Metadata about a tool for discovery and configuration.
    
    Attributes:
        type: Tool type (e.g., "mcp", "openapi", "a2a", "builtin")
        name: Tool name (e.g., "microsoft-learn", "support-triage-api")
        description: Human-readable description
        factory: Factory function to instantiate the tool
        required_config: Dict of required config keys and descriptions
        optional_config: Dict of optional config keys and descriptions
    """
    type: str
    name: str
    description: str
    factory: Callable[[Dict[str, Any]], Any]
    required_config: Dict[str, str] = field(default_factory=dict)
    optional_config: Dict[str, str] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Full tool identifier (type:name)."""
        return f"{self.type}:{self.name}"


class ToolRegistry:
    """
    Registry for available tools with factory functions.
    
    Maps (tool_type, tool_name) → factory function for lazy initialization.
    Provides graceful error handling: tool failures don't crash agent creation.
    
    Usage:
        ```python
        registry = ToolRegistry()
        
        # Register a tool
        registry.register(ToolDefinition(
            type="mcp",
            name="microsoft-learn",
            description="Microsoft Learn documentation search",
            factory=lambda cfg: get_microsoft_learn_tool(),
            required_config={},
            optional_config={"endpoint": "MCP server endpoint"}
        ))
        
        # Create a tool instance
        tool = registry.create_tool("mcp", "microsoft-learn", {})
        if tool:
            print("Tool created successfully")
        else:
            print("Tool failed to initialize")
        ```
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self.tools: Dict[str, ToolDefinition] = {}
        logger.debug("Tool registry initialized")
    
    def register(self, definition: ToolDefinition) -> None:
        """
        Register a tool factory.
        
        Args:
            definition: ToolDefinition with factory function
            
        Raises:
            ValueError: If tool already registered (can be overridden)
        """
        key = definition.full_name
        if key in self.tools:
            logger.warning(f"Overwriting existing tool registration: {key}")
        
        self.tools[key] = definition
        logger.info(f"Registered tool: {key}")
    
    def get(self, tool_type: str, tool_name: str) -> Optional[ToolDefinition]:
        """
        Get tool definition by type and name.
        
        Args:
            tool_type: Type of tool (e.g., "mcp", "openapi")
            tool_name: Name of tool (e.g., "microsoft-learn")
            
        Returns:
            ToolDefinition if found, None otherwise
        """
        key = f"{tool_type}:{tool_name}"
        return self.tools.get(key)
    
    def list_all(self) -> Dict[str, ToolDefinition]:
        """
        Get all registered tools.
        
        Returns:
            Dictionary of all registered tools
        """
        return dict(self.tools)
    
    def list_by_type(self, tool_type: str) -> Dict[str, ToolDefinition]:
        """
        Get all tools of a specific type.
        
        Args:
            tool_type: Type to filter by
            
        Returns:
            Dictionary of tools matching the type
        """
        return {
            key: defn
            for key, defn in self.tools.items()
            if defn.type == tool_type
        }
    
    def create_tool(
        self,
        tool_type: str,
        tool_name: str,
        config: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Instantiate a tool with given configuration.
        
        This is the main interface for tool creation. It handles:
        - Lookup in registry
        - Factory invocation
        - Exception handling
        - Graceful failure
        
        Args:
            tool_type: Type of tool
            tool_name: Name of tool
            config: Configuration dictionary for the tool
            
        Returns:
            Tool instance if successful, None if tool not found or factory fails
            
        Note:
            - Tool not found? Logs warning, returns None
            - Factory raises exception? Logs error, returns None
            - Agent should handle None gracefully and continue with other tools
        """
        definition = self.get(tool_type, tool_name)
        
        if not definition:
            logger.warning(
                f"Tool not found in registry: {tool_type}:{tool_name}"
            )
            return None
        
        try:
            logger.debug(f"Creating tool {definition.full_name} with config: {config}")
            tool = definition.factory(config)
            logger.info(f"✓ Successfully created tool: {definition.full_name}")
            return tool
        except Exception as e:
            logger.error(
                f"✗ Failed to create tool {definition.full_name}: {type(e).__name__}: {e}",
                exc_info=False
            )
            return None


# Global singleton instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry singleton.
    
    Returns:
        ToolRegistry instance
    """
    global _tool_registry
    print(f"[GET_TOOL_REGISTRY] Called. Current _tool_registry: {_tool_registry}")
    if _tool_registry is None:
        print("[GET_TOOL_REGISTRY] _tool_registry is None, creating new instance")
        _tool_registry = ToolRegistry()
        print(f"[GET_TOOL_REGISTRY] Created new instance: {_tool_registry}")
    else:
        print(f"[GET_TOOL_REGISTRY] Returning existing instance: {_tool_registry}")
        all_tools = _tool_registry.list_all()
        print(f"[GET_TOOL_REGISTRY] Existing registry has {len(all_tools)} tools: {list(all_tools.keys())}")
    return _tool_registry


def register_default_tools() -> None:
    """
    Register all built-in tools.
    
    Called during application startup to populate the registry with
    all available tool implementations.
    
    Tools registered:
    - MCP: microsoft-learn, azure-mcp
    - OpenAPI: support-triage-api, ops-assistant-api
    
    Note: If a tool factory is unavailable, it's skipped with a warning.
    """
    print("[TOOL_REGISTRY] register_default_tools() called")
    registry = get_tool_registry()
    print(f"[TOOL_REGISTRY] Got registry: {registry}")
    
    # Gracefully handle tool factory imports
    try:
        print("[TOOL_REGISTRY] Attempting to import MCP tools...")
        from src.tools.mcp_tools import (
            get_microsoft_learn_tool,
            get_azure_mcp_tool,
            get_mssql_tool,
        )
        print("[TOOL_REGISTRY] ✓ MCP tools imported successfully")
        
        # Microsoft Learn MCP Tool
        print("[TOOL_REGISTRY] Registering microsoft-learn tool...")
        registry.register(ToolDefinition(
            type="mcp",
            name="microsoft-learn",
            description="Search Microsoft Learn documentation and get articles",
            factory=lambda cfg: get_microsoft_learn_tool(),
            required_config={},
            optional_config={
                "endpoint": "Microsoft Learn MCP server endpoint (uses default if not specified)"
            }
        ))
        print("[TOOL_REGISTRY] ✓ microsoft-learn tool registered")
        
        # Azure MCP Tool
        print("[TOOL_REGISTRY] Registering azure-mcp tool...")
        registry.register(ToolDefinition(
            type="mcp",
            name="azure-mcp",
            description="List and query Azure resources, monitor logs",
            factory=lambda cfg: get_azure_mcp_tool(),
            required_config={},
            optional_config={
                "endpoint": "Azure MCP server endpoint (uses default if not specified)"
            }
        ))
        print("[TOOL_REGISTRY] ✓ azure-mcp tool registered")
        
        # MSSQL MCP Tool (Wide World Importers with OAuth)
        print("[TOOL_REGISTRY] Registering mssql-mcp tool...")
        registry.register(ToolDefinition(
            type="mcp",
            name="mssql-mcp",
            description="Query Wide World Importers database via OAuth-secured MCP server",
            factory=lambda cfg: get_mssql_tool(),
            required_config={},
            optional_config={
                "server_url": "MSSQL MCP server URL",
                "client_id": "OAuth client ID",
                "client_secret": "OAuth client secret",
                "token_url": "OAuth token endpoint",
                "scope": "OAuth scope"
            }
        ))
        print("[TOOL_REGISTRY] ✓ mssql-mcp tool registered")
        
        logger.info("✓ Registered MCP tools")
    except Exception as e:
        print(f"[TOOL_REGISTRY] ✗ Failed to register MCP tools: {e}")
        logger.warning(f"Failed to register MCP tools: {e}")
    
    try:
        print("[TOOL_REGISTRY] Attempting to import OpenAPI tools...")
        from src.tools.openapi_client import (
            get_support_triage_tool,
            get_ops_assistant_tool,
        )
        print("[TOOL_REGISTRY] ✓ OpenAPI tools imported successfully")
        
        # Support Triage OpenAPI Tool
        print("[TOOL_REGISTRY] Registering support-triage-api tool...")
        registry.register(ToolDefinition(
            type="openapi",
            name="support-triage-api",
            description="Search support tickets and knowledge base articles",
            factory=lambda cfg: get_support_triage_tool(),
            required_config={},
            optional_config={
                "base_url": "Support Triage API base URL (uses env var if not specified)",
                "api_key": "API key for authentication (uses env var if not specified)"
            }
        ))
        print("[TOOL_REGISTRY] ✓ support-triage-api tool registered")
        
        # Ops Assistant OpenAPI Tool
        print("[TOOL_REGISTRY] Registering ops-assistant-api tool...")
        registry.register(ToolDefinition(
            type="openapi",
            name="ops-assistant-api",
            description="Check deployment status, manage deployments, view history",
            factory=lambda cfg: get_ops_assistant_tool(),
            required_config={},
            optional_config={
                "base_url": "Ops Assistant API base URL (uses env var if not specified)",
                "api_key": "API key for authentication (uses env var if not specified)"
            }
        ))
        print("[TOOL_REGISTRY] ✓ ops-assistant-api tool registered")
        
        logger.info("✓ Registered OpenAPI tools")
    except Exception as e:
        print(f"[TOOL_REGISTRY] ✗ Failed to register OpenAPI tools: {e}")
        logger.warning(f"Failed to register OpenAPI tools: {e}")
    
    # A2A tools are NOT registered here anymore
    # Instead, specialist agents are directly passed as tools to Router Agent
    # using agent.as_tool() pattern from Agent Framework
    # See: factory.py load_specialist_agents_as_tools()
    
    all_tools = registry.list_all()
    print(f"[TOOL_REGISTRY] Tool registration complete: {len(all_tools)} tools registered")
    for key, tool in all_tools.items():
        print(f"[TOOL_REGISTRY]   - {tool.full_name}")
    logger.info(f"Tool registry initialized with {len(all_tools)} tools")
