"""
Agent registry for managing and instantiating agents.

This module provides a factory-based registry for creating and caching agent instances.
Agent configurations are loaded from Cosmos DB and agents are instantiated on-demand.
"""
from typing import Any, Optional
import logging
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

from .base import DemoBaseAgent
from ..tools.mcp_tools import (
    get_microsoft_learn_tool,
    get_azure_mcp_tool,
    get_adventure_works_tool,
)
from ..tools.openapi_client import (
    get_support_triage_tool,
    get_ops_assistant_tool,
)

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for creating and managing agent instances.
    
    This class provides a factory pattern for creating agents from configurations
    stored in Cosmos DB. It caches active agents to avoid recreation on every request
    and supports lazy loading of agent instances.
    
    Features:
    - Load agent configurations from Cosmos DB
    - Create agents on-demand with appropriate tools
    - Cache active agents for reuse
    - Support for all agent types (Support Triage, Azure Ops, SQL, News, Business Impact)
    
    Usage:
        ```python
        # Initialize registry
        registry = AgentRegistry(
            cosmos_endpoint="https://...",
            cosmos_database="agents-db",
            cosmos_container="agent-configs"
        )
        
        # Get or create an agent
        agent = await registry.get_agent("support-triage")
        
        # List all available agents
        agents = await registry.list_agents()
        
        # Reload agent configuration
        await registry.reload_agent("support-triage")
        
        # Clear cache
        registry.clear_cache()
        ```
    """
    
    def __init__(
        self,
        cosmos_endpoint: str,
        cosmos_database: str,
        cosmos_container: str,
        credential: Optional[Any] = None
    ):
        """
        Initialize the agent registry.
        
        Args:
            cosmos_endpoint: Cosmos DB endpoint URL
            cosmos_database: Database name containing agent configurations
            cosmos_container: Container name for agent configurations
            credential: Azure credential (default: DefaultAzureCredential)
        """
        self.cosmos_endpoint = cosmos_endpoint
        self.cosmos_database = cosmos_database
        self.cosmos_container = cosmos_container
        
        # Use provided credential or default to DefaultAzureCredential
        self._credential = credential or DefaultAzureCredential()
        
        # Lazy-initialized Cosmos client
        self._cosmos_client: Optional[CosmosClient] = None
        self._container = None
        
        # Cache for active agent instances
        self._cache: dict[str, DemoBaseAgent] = {}
        
        logger.info(f"Initialized AgentRegistry with database '{cosmos_database}', container '{cosmos_container}'")
    
    async def _ensure_cosmos_client(self) -> None:
        """Ensure Cosmos DB client is initialized."""
        if self._cosmos_client is None:
            self._cosmos_client = CosmosClient(
                url=self.cosmos_endpoint,
                credential=self._credential
            )
            database = self._cosmos_client.get_database_client(self.cosmos_database)
            self._container = database.get_container_client(self.cosmos_container)
            logger.debug("Cosmos DB client initialized")
    
    async def get_agent(self, agent_name: str) -> DemoBaseAgent:
        """
        Get or create an agent by name.
        
        If the agent is already in cache, returns the cached instance.
        Otherwise, loads configuration from Cosmos DB and creates a new instance.
        
        Args:
            agent_name: Name/ID of the agent to retrieve
            
        Returns:
            DemoBaseAgent instance
            
        Raises:
            ValueError: If agent configuration not found
            Exception: If agent creation fails
        """
        # Check cache first
        if agent_name in self._cache:
            logger.debug(f"Returning cached agent: {agent_name}")
            return self._cache[agent_name]
        
        # Load configuration and create agent
        logger.info(f"Loading agent configuration for: {agent_name}")
        config = await self._load_config(agent_name)
        
        if not config:
            raise ValueError(f"Agent configuration not found: {agent_name}")
        
        # Create agent from configuration
        agent = await self._create_agent(config)
        
        # Cache the agent
        self._cache[agent_name] = agent
        logger.info(f"Created and cached agent: {agent_name}")
        
        return agent
    
    async def list_agents(self) -> list[dict[str, Any]]:
        """
        List all available agent configurations.
        
        Returns:
            List of agent configuration dictionaries (minimal metadata)
        """
        await self._ensure_cosmos_client()
        
        query = "SELECT c.id, c.name, c.type, c.description FROM c"
        
        agents = []
        async for item in self._container.query_items(query=query, enable_cross_partition_query=True):
            agents.append(item)
        
        logger.debug(f"Listed {len(agents)} agent configurations")
        return agents
    
    async def reload_agent(self, agent_name: str) -> DemoBaseAgent:
        """
        Reload an agent's configuration from Cosmos DB.
        
        Removes the agent from cache and recreates it with fresh configuration.
        
        Args:
            agent_name: Name/ID of the agent to reload
            
        Returns:
            Newly created DemoBaseAgent instance
        """
        logger.info(f"Reloading agent: {agent_name}")
        
        # Remove from cache if present
        if agent_name in self._cache:
            del self._cache[agent_name]
            logger.debug(f"Removed {agent_name} from cache")
        
        # Get fresh instance
        return await self.get_agent(agent_name)
    
    def clear_cache(self) -> None:
        """Clear all cached agent instances."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared agent cache ({count} agents)")
    
    async def _load_config(self, agent_name: str) -> Optional[dict[str, Any]]:
        """
        Load agent configuration from Cosmos DB.
        
        Args:
            agent_name: Name/ID of the agent
            
        Returns:
            Agent configuration dictionary or None if not found
        """
        await self._ensure_cosmos_client()
        
        try:
            item = await self._container.read_item(
                item=agent_name,
                partition_key=agent_name
            )
            logger.debug(f"Loaded configuration for agent: {agent_name}")
            return item
        except Exception as e:
            logger.warning(f"Failed to load configuration for {agent_name}: {e}")
            return None
    
    async def _create_agent(self, config: dict[str, Any]) -> DemoBaseAgent:
        """
        Create an agent instance from configuration.
        
        Args:
            config: Agent configuration dictionary
            
        Returns:
            DemoBaseAgent instance
            
        Raises:
            ValueError: If required configuration fields are missing
        """
        # Extract required fields
        name = config.get("name")
        instructions = config.get("instructions")
        
        if not name or not instructions:
            raise ValueError("Agent configuration must include 'name' and 'instructions'")
        
        # Extract optional fields with defaults
        model = config.get("model", "gpt-4o")
        max_messages = config.get("max_messages", 20)
        max_tokens = config.get("max_tokens")
        temperature = config.get("temperature", 0.7)
        
        # Create tools based on configuration
        tools = await self._create_tools(config.get("tools", []))
        
        # Create the agent
        logger.debug(f"Creating agent '{name}' with {len(tools)} tools")
        
        agent = DemoBaseAgent(
            name=name,
            instructions=instructions,
            tools=tools,
            model=model,
            max_messages=max_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return agent
    
    async def _create_tools(self, tool_configs: list[dict[str, Any]]) -> list[Any]:
        """
        Create tool instances based on configuration.
        
        Args:
            tool_configs: List of tool configuration dictionaries
            
        Returns:
            List of tool instances
        """
        tools = []
        
        for tool_config in tool_configs:
            tool_type = tool_config.get("type")
            tool_name = tool_config.get("name")
            
            if not tool_type:
                logger.warning(f"Tool configuration missing 'type': {tool_config}")
                continue
            
            try:
                tool = await self._create_tool(tool_type, tool_name, tool_config)
                if tool:
                    tools.append(tool)
                    logger.debug(f"Created tool: {tool_type}/{tool_name}")
            except Exception as e:
                logger.error(f"Failed to create tool {tool_type}/{tool_name}: {e}")
        
        return tools
    
    async def _create_tool(
        self,
        tool_type: str,
        tool_name: Optional[str],
        tool_config: dict[str, Any]
    ) -> Optional[Any]:
        """
        Create a single tool instance.
        
        Args:
            tool_type: Type of tool (mcp, openapi, function)
            tool_name: Name of the tool
            tool_config: Tool configuration dictionary
            
        Returns:
            Tool instance or None if creation fails
        """
        if tool_type == "mcp":
            return await self._create_mcp_tool(tool_name)
        elif tool_type == "openapi":
            return await self._create_openapi_tool(tool_name)
        elif tool_type == "function":
            # Function tools would be registered separately
            logger.warning(f"Function tool support not yet implemented: {tool_name}")
            return None
        else:
            logger.warning(f"Unknown tool type: {tool_type}")
            return None
    
    async def _create_mcp_tool(self, tool_name: Optional[str]) -> Optional[Any]:
        """
        Create an MCP tool instance.
        
        Args:
            tool_name: Name of the MCP tool
            
        Returns:
            MCP tool instance or None
        """
        if tool_name == "microsoft-learn":
            return get_microsoft_learn_tool()
        elif tool_name == "azure-mcp":
            return get_azure_mcp_tool()
        elif tool_name == "adventure-works":
            return get_adventure_works_tool()
        else:
            logger.warning(f"Unknown MCP tool: {tool_name}")
            return None
    
    async def _create_openapi_tool(self, tool_name: Optional[str]) -> Optional[Any]:
        """
        Create an OpenAPI tool instance.
        
        Args:
            tool_name: Name of the OpenAPI tool
            
        Returns:
            OpenAPI tool instance or None
        """
        if tool_name == "support-triage":
            return get_support_triage_tool()
        elif tool_name == "ops-assistant":
            return get_ops_assistant_tool()
        else:
            logger.warning(f"Unknown OpenAPI tool: {tool_name}")
            return None
    
    async def close(self) -> None:
        """Close Cosmos DB client and cleanup resources."""
        if self._cosmos_client:
            await self._cosmos_client.close()
            logger.debug("Closed Cosmos DB client")
