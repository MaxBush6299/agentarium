"""
Agent Factory for creating agents from configuration.

This module provides a factory pattern for creating agents from stored configuration
(AgentMetadata in Cosmos DB), enabling:
- Dynamic agent instantiation without hardcoded agent classes
- Lazy tool loading with graceful failure handling
- Configuration-driven agent creation
- Extensible tool support

The factory is the bridge between agent metadata (data) and agent instances (objects).
"""

from typing import Optional, List, Any
import logging

from src.persistence.models import AgentMetadata, AgentStatus, ToolConfig
from src.agents.base import DemoBaseAgent
from src.agents.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating agents from stored configuration.
    
    Creates agent instances from AgentMetadata (stored in Cosmos DB) with:
    - Dynamic tool loading from registry
    - Graceful failure: tool failures don't prevent agent creation
    - Partial functionality: agent works with available tools
    - Clear logging: detailed trace of what loaded/failed
    
    Usage:
        ```python
        from src.persistence.agents import get_agent_repository
        
        repo = get_agent_repository()
        agent_config = repo.get("support-triage")
        
        if agent_config:
            agent = AgentFactory.create_from_metadata(agent_config)
            if agent:
                print("Agent created successfully")
                # Use agent for chat
            else:
                print("Failed to create agent")
        else:
            print("Agent config not found")
        ```
    """
    
    @staticmethod
    def create_from_metadata(agent_config: AgentMetadata) -> Optional[DemoBaseAgent]:
        """
        Create an agent instance from stored metadata.
        
        This is the main factory method. It:
        1. Validates configuration
        2. Loads tools from registry
        3. Handles tool loading failures gracefully
        4. Creates DemoBaseAgent with available tools
        5. Logs the entire process for debugging
        
        Args:
            agent_config: AgentMetadata from Cosmos DB
            
        Returns:
            DemoBaseAgent instance if creation succeeds, None if it fails
            
        Behavior:
            - Tools that load successfully are added to agent
            - Tools that fail to load are logged but don't prevent creation
            - Agent is created even if NO tools load (partial functionality)
            - Returns None only if agent instantiation itself fails
            
        Raises:
            Logs warnings/errors but doesn't raise exceptions
        """
        agent_id = agent_config.id
        logger.info(f"Creating agent '{agent_id}' from metadata")
        logger.debug(f"  Model: {agent_config.model}")
        logger.debug(f"  Name: {agent_config.name}")
        logger.debug(f"  Tools configured: {len(agent_config.tools)}")
        
        # Load tools with graceful failure
        tools: List[Any] = []
        registry = get_tool_registry()
        
        print(f"[FACTORY] Starting tool loading for agent '{agent_id}'")
        print(f"[FACTORY] Tool registry: {registry}")
        print(f"[FACTORY] Number of tools configured: {len(agent_config.tools) if agent_config.tools else 0}")
        
        if agent_config.tools:
            logger.info(f"  Loading {len(agent_config.tools)} tools...")
            print(f"[FACTORY] Agent has {len(agent_config.tools)} tools to load")
            
            for tool_config in agent_config.tools:
                print(f"[FACTORY] Processing tool: {tool_config.type}:{tool_config.name}")
                
                # Skip disabled tools
                if not tool_config.enabled:
                    logger.debug(f"    Tool {tool_config.type}:{tool_config.name} is disabled, skipping")
                    print(f"[FACTORY] Tool {tool_config.type}:{tool_config.name} is disabled, skipping")
                    continue
                
                try:
                    logger.debug(
                        f"    Attempting to load {tool_config.type}:{tool_config.name}..."
                    )
                    print(f"[FACTORY] Attempting to load {tool_config.type}:{tool_config.name}...")
                    
                    tool = registry.create_tool(
                        tool_type=tool_config.type.value,  # Convert enum to string value
                        tool_name=tool_config.name,
                        config=tool_config.config or {}
                    )
                    
                    print(f"[FACTORY] Tool creation result: {tool}")
                    
                    if tool:
                        # OpenAPITool instances need to have their callables extracted
                        if hasattr(tool, 'get_tools') and callable(getattr(tool, 'get_tools')):
                            print(f"[FACTORY] Extracting tools from OpenAPITool: {tool}")
                            openapi_tools = tool.get_tools()
                            print(f"[FACTORY] Extracted {len(openapi_tools)} callable(s) from OpenAPITool")
                            tools.extend(openapi_tools)
                        else:
                            # MCPStreamableHTTPTool and other ToolProtocol instances
                            print(f"[FACTORY] Adding tool directly (ToolProtocol): {tool}")
                            tools.append(tool)
                        
                        logger.info(
                            f"    ✓ Successfully loaded tool {tool_config.type}:{tool_config.name}"
                        )
                        print(f"[FACTORY] ✓ Successfully loaded tool {tool_config.type}:{tool_config.name}")
                    else:
                        logger.warning(
                            f"    ⚠ Tool factory returned None: {tool_config.type}:{tool_config.name}"
                        )
                        print(f"[FACTORY] ⚠ Tool factory returned None: {tool_config.type}:{tool_config.name}")
                
                except Exception as e:
                    logger.error(
                        f"    ✗ Exception loading {tool_config.type}:{tool_config.name}: "
                        f"{type(e).__name__}: {e}",
                        exc_info=False
                    )
                    print(f"[FACTORY] ✗ Exception loading {tool_config.type}:{tool_config.name}: {type(e).__name__}: {e}")
                    # Continue with other tools - don't let one failure stop the show
            
            logger.info(f"  Tool loading complete: {len(tools)}/{len(agent_config.tools)} tools loaded")
            print(f"[FACTORY] Tool loading complete: {len(tools)}/{len(agent_config.tools)} tools loaded")
        else:
            logger.warning(f"  Agent has no tools configured")
            print(f"[FACTORY] Agent has no tools configured")
        
        # Create DemoBaseAgent
        try:
            logger.info(f"  Creating DemoBaseAgent with {len(tools)} tool(s)...")
            
            agent = DemoBaseAgent(
                name=agent_config.name,
                instructions=agent_config.system_prompt,
                tools=tools if tools else None,
                model=agent_config.model,
                max_messages=agent_config.max_messages,
                temperature=agent_config.temperature,
                max_tokens=agent_config.max_tokens,
            )
            
            logger.info(f"✓ Agent '{agent_id}' created successfully")
            return agent
        
        except Exception as e:
            logger.error(
                f"✗ Failed to create DemoBaseAgent for '{agent_id}': "
                f"{type(e).__name__}: {e}",
                exc_info=True
            )
            return None
    
    @staticmethod
    def validate_config(agent_config: AgentMetadata) -> tuple[bool, str]:
        """
        Validate agent configuration before creation.
        
        Args:
            agent_config: AgentMetadata to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Check required fields
        if not agent_config.id:
            return False, "Agent ID is required"
        
        if not agent_config.name:
            return False, "Agent name is required"
        
        if not agent_config.model:
            return False, "Model is required"
        
        if not agent_config.system_prompt:
            return False, "System prompt is required"
        
        # Warn if no tools
        if not agent_config.tools:
            logger.warning(f"Agent '{agent_config.id}' has no tools configured")
        
        return True, ""
