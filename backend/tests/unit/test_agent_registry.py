"""Unit tests for the AgentRegistry class."""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Any

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from src.agents.registry import AgentRegistry
from src.agents.base import DemoBaseAgent


@pytest.fixture
def mock_cosmos_client():
    """Create a mock Cosmos DB client."""
    client = AsyncMock()
    database = AsyncMock()
    container = AsyncMock()
    
    client.get_database_client = Mock(return_value=database)
    database.get_container_client = Mock(return_value=container)
    
    return client, container


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration."""
    return {
        "id": "support-triage",
        "name": "Support Triage Agent",
        "type": "support",
        "description": "Agent for triaging support tickets",
        "instructions": "You are a support triage specialist.",
        "model": "gpt-4o",
        "max_messages": 20,
        "temperature": 0.7,
        "tools": [
            {"type": "mcp", "name": "microsoft-learn"},
            {"type": "openapi", "name": "support-triage"}
        ]
    }


@pytest.fixture
async def registry(mock_cosmos_client):
    """Create an AgentRegistry instance with mocked Cosmos client."""
    client_mock, container_mock = mock_cosmos_client
    
    # Create registry
    registry = AgentRegistry(
        cosmos_endpoint="https://test.documents.azure.com:443/",
        cosmos_database="test-db",
        cosmos_container="test-container"
    )
    
    # Inject mocked client
    registry._cosmos_client = client_mock
    registry._container = container_mock
    
    yield registry
    
    # Cleanup
    await registry.close()


class TestAgentRegistryInitialization:
    """Tests for AgentRegistry initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default credential."""
        registry = AgentRegistry(
            cosmos_endpoint="https://test.documents.azure.com:443/",
            cosmos_database="agents-db",
            cosmos_container="agent-configs"
        )
        
        assert registry.cosmos_endpoint == "https://test.documents.azure.com:443/"
        assert registry.cosmos_database == "agents-db"
        assert registry.cosmos_container == "agent-configs"
        assert registry._cosmos_client is None  # Lazy initialization
        assert len(registry._cache) == 0
    
    def test_init_with_custom_credential(self):
        """Test initialization with custom credential."""
        mock_credential = Mock()
        
        registry = AgentRegistry(
            cosmos_endpoint="https://test.documents.azure.com:443/",
            cosmos_database="agents-db",
            cosmos_container="agent-configs",
            credential=mock_credential
        )
        
        assert registry._credential == mock_credential
    
    def test_init_creates_empty_cache(self):
        """Test that initialization creates an empty cache."""
        registry = AgentRegistry(
            cosmos_endpoint="https://test.documents.azure.com:443/",
            cosmos_database="agents-db",
            cosmos_container="agent-configs"
        )
        
        assert isinstance(registry._cache, dict)
        assert len(registry._cache) == 0


class TestAgentRegistryCosmosClient:
    """Tests for Cosmos DB client management."""
    
    @pytest.mark.asyncio
    async def test_ensure_cosmos_client_lazy_initialization(self):
        """Test that Cosmos client is initialized on first use."""
        registry = AgentRegistry(
            cosmos_endpoint="https://test.documents.azure.com:443/",
            cosmos_database="test-db",
            cosmos_container="test-container"
        )
        
        assert registry._cosmos_client is None
        
        with patch('src.agents.registry.CosmosClient') as mock_cosmos:
            mock_client = Mock()  # Not async - CosmosClient itself is not async
            mock_database = Mock()
            mock_container = Mock()
            
            mock_cosmos.return_value = mock_client
            mock_client.get_database_client.return_value = mock_database
            mock_database.get_container_client.return_value = mock_container
            
            await registry._ensure_cosmos_client()
            
            assert registry._cosmos_client is not None
            assert registry._container is not None
            mock_cosmos.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_cosmos_client_idempotent(self):
        """Test that multiple calls don't recreate the client."""
        registry = AgentRegistry(
            cosmos_endpoint="https://test.documents.azure.com:443/",
            cosmos_database="test-db",
            cosmos_container="test-container"
        )
        
        with patch('src.agents.registry.CosmosClient') as mock_cosmos:
            mock_client = Mock()  # Not async - CosmosClient itself is not async
            mock_database = Mock()
            mock_container = Mock()
            
            mock_cosmos.return_value = mock_client
            mock_client.get_database_client.return_value = mock_database
            mock_database.get_container_client.return_value = mock_container
            
            # Call multiple times
            await registry._ensure_cosmos_client()
            await registry._ensure_cosmos_client()
            await registry._ensure_cosmos_client()
            
            # Should only initialize once
            mock_cosmos.assert_called_once()


class TestAgentRegistryGetAgent:
    """Tests for getting agents from the registry."""
    
    @pytest.mark.asyncio
    async def test_get_agent_from_cosmos(self, registry, sample_agent_config):
        """Test getting an agent that's not in cache."""
        # Mock Cosmos response
        registry._container.read_item = AsyncMock(return_value=sample_agent_config)
        
        # Mock tool creation
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.registry.get_support_triage_tool') as mock_triage:
            
            mock_learn.return_value = Mock()
            mock_triage.return_value = Mock()
            
            agent = await registry.get_agent("support-triage")
            
            assert isinstance(agent, DemoBaseAgent)
            assert agent.name == "Support Triage Agent"
            assert "support-triage" in registry._cache
    
    @pytest.mark.asyncio
    async def test_get_agent_from_cache(self, registry, sample_agent_config):
        """Test getting an agent that's already cached."""
        # Create and cache an agent
        mock_agent = Mock(spec=DemoBaseAgent)
        registry._cache["support-triage"] = mock_agent
        
        # Get the agent
        agent = await registry.get_agent("support-triage")
        
        # Should return cached instance without calling Cosmos
        assert agent == mock_agent
        registry._container.read_item.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, registry):
        """Test getting an agent that doesn't exist."""
        registry._container.read_item = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Agent configuration not found"):
            await registry.get_agent("non-existent")
    
    @pytest.mark.asyncio
    async def test_get_agent_caches_instance(self, registry, sample_agent_config):
        """Test that created agents are cached."""
        registry._container.read_item = AsyncMock(return_value=sample_agent_config)
        
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.registry.get_support_triage_tool') as mock_triage:
            
            mock_learn.return_value = Mock()
            mock_triage.return_value = Mock()
            
            # Get agent first time
            agent1 = await registry.get_agent("support-triage")
            
            # Get agent second time
            agent2 = await registry.get_agent("support-triage")
            
            # Should be same instance
            assert agent1 is agent2
            # Cosmos should only be called once
            registry._container.read_item.assert_called_once()


class TestAgentRegistryListAgents:
    """Tests for listing agents."""
    
    @pytest.mark.asyncio
    async def test_list_agents_empty(self, registry):
        """Test listing agents when none exist."""
        # Mock empty result
        async def mock_query(*args, **kwargs):
            return
            yield  # Make it an async generator
        
        registry._container.query_items = mock_query
        
        agents = await registry.list_agents()
        
        assert isinstance(agents, list)
        assert len(agents) == 0
    
    @pytest.mark.asyncio
    async def test_list_agents_with_results(self, registry):
        """Test listing agents with results."""
        # Mock agent list
        agent_list = [
            {"id": "agent1", "name": "Agent 1", "type": "support", "description": "First agent"},
            {"id": "agent2", "name": "Agent 2", "type": "ops", "description": "Second agent"},
            {"id": "agent3", "name": "Agent 3", "type": "sql", "description": "Third agent"},
        ]
        
        async def mock_query(*args, **kwargs):
            for agent in agent_list:
                yield agent
        
        registry._container.query_items = mock_query
        
        agents = await registry.list_agents()
        
        assert len(agents) == 3
        assert agents[0]["id"] == "agent1"
        assert agents[1]["name"] == "Agent 2"
        assert agents[2]["type"] == "sql"


class TestAgentRegistryReloadAgent:
    """Tests for reloading agents."""
    
    @pytest.mark.asyncio
    async def test_reload_agent_clears_cache(self, registry, sample_agent_config):
        """Test that reload removes agent from cache."""
        # Cache an agent
        mock_agent = Mock(spec=DemoBaseAgent)
        registry._cache["support-triage"] = mock_agent
        
        # Mock Cosmos response for reload
        registry._container.read_item = AsyncMock(return_value=sample_agent_config)
        
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.registry.get_support_triage_tool') as mock_triage:
            
            mock_learn.return_value = Mock()
            mock_triage.return_value = Mock()
            
            # Reload agent
            new_agent = await registry.reload_agent("support-triage")
            
            # Should be a new instance
            assert new_agent is not mock_agent
            assert isinstance(new_agent, DemoBaseAgent)
    
    @pytest.mark.asyncio
    async def test_reload_agent_not_in_cache(self, registry, sample_agent_config):
        """Test reloading an agent that's not cached."""
        registry._container.read_item = AsyncMock(return_value=sample_agent_config)
        
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.registry.get_support_triage_tool') as mock_triage:
            
            mock_learn.return_value = Mock()
            mock_triage.return_value = Mock()
            
            # Reload agent (not in cache)
            agent = await registry.reload_agent("support-triage")
            
            assert isinstance(agent, DemoBaseAgent)


class TestAgentRegistryCacheManagement:
    """Tests for cache management."""
    
    def test_clear_cache_empty(self, registry):
        """Test clearing an empty cache."""
        registry.clear_cache()
        
        assert len(registry._cache) == 0
    
    def test_clear_cache_with_agents(self, registry):
        """Test clearing cache with agents."""
        # Add some mock agents to cache
        registry._cache["agent1"] = Mock(spec=DemoBaseAgent)
        registry._cache["agent2"] = Mock(spec=DemoBaseAgent)
        registry._cache["agent3"] = Mock(spec=DemoBaseAgent)
        
        assert len(registry._cache) == 3
        
        registry.clear_cache()
        
        assert len(registry._cache) == 0


class TestAgentRegistryAgentCreation:
    """Tests for agent creation from configuration."""
    
    @pytest.mark.asyncio
    async def test_create_agent_with_minimal_config(self, registry):
        """Test creating agent with minimal configuration."""
        config = {
            "name": "Test Agent",
            "instructions": "Test instructions",
            "tools": []
        }
        
        agent = await registry._create_agent(config)
        
        assert isinstance(agent, DemoBaseAgent)
        assert agent.name == "Test Agent"
        assert agent.instructions == "Test instructions"
        assert agent.model == "gpt-4o"  # Default
        assert agent.max_messages == 20  # Default
        assert agent.temperature == 0.7  # Default
    
    @pytest.mark.asyncio
    async def test_create_agent_with_full_config(self, registry):
        """Test creating agent with full configuration."""
        config = {
            "name": "Custom Agent",
            "instructions": "Custom instructions",
            "model": "gpt-4",
            "max_messages": 50,
            "max_tokens": 4096,
            "temperature": 0.9,
            "tools": []
        }
        
        agent = await registry._create_agent(config)
        
        assert agent.name == "Custom Agent"
        assert agent.model == "gpt-4"
        assert agent.max_messages == 50
        assert agent.max_tokens == 4096
        assert agent.temperature == 0.9
    
    @pytest.mark.asyncio
    async def test_create_agent_missing_name(self, registry):
        """Test that missing name raises ValueError."""
        config = {
            "instructions": "Test instructions"
        }
        
        with pytest.raises(ValueError, match="must include 'name' and 'instructions'"):
            await registry._create_agent(config)
    
    @pytest.mark.asyncio
    async def test_create_agent_missing_instructions(self, registry):
        """Test that missing instructions raises ValueError."""
        config = {
            "name": "Test Agent"
        }
        
        with pytest.raises(ValueError, match="must include 'name' and 'instructions'"):
            await registry._create_agent(config)


class TestAgentRegistryToolCreation:
    """Tests for tool creation."""
    
    @pytest.mark.asyncio
    async def test_create_mcp_tools(self, registry):
        """Test creating MCP tools."""
        tool_configs = [
            {"type": "mcp", "name": "microsoft-learn"},
            {"type": "mcp", "name": "azure-mcp"}
        ]
        
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.registry.get_azure_mcp_tool') as mock_azure:
            
            mock_learn.return_value = Mock(name="learn_tool")
            mock_azure.return_value = Mock(name="azure_tool")
            
            tools = await registry._create_tools(tool_configs)
            
            assert len(tools) == 2
            mock_learn.assert_called_once()
            mock_azure.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_openapi_tools(self, registry):
        """Test creating OpenAPI tools."""
        tool_configs = [
            {"type": "openapi", "name": "support-triage"},
            {"type": "openapi", "name": "ops-assistant"}
        ]
        
        with patch('src.agents.registry.get_support_triage_tool') as mock_support, \
             patch('src.agents.registry.get_ops_assistant_tool') as mock_ops:
            
            mock_support.return_value = Mock(name="support_tool")
            mock_ops.return_value = Mock(name="ops_tool")
            
            tools = await registry._create_tools(tool_configs)
            
            assert len(tools) == 2
            mock_support.assert_called_once()
            mock_ops.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_mixed_tools(self, registry):
        """Test creating mix of MCP and OpenAPI tools."""
        tool_configs = [
            {"type": "mcp", "name": "microsoft-learn"},
            {"type": "openapi", "name": "support-triage"},
            {"type": "mcp", "name": "adventure-works"}
        ]
        
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.registry.get_support_triage_tool') as mock_support, \
             patch('src.agents.registry.get_adventure_works_tool') as mock_adventure:
            
            mock_learn.return_value = Mock()
            mock_support.return_value = Mock()
            mock_adventure.return_value = Mock()
            
            tools = await registry._create_tools(tool_configs)
            
            assert len(tools) == 3
    
    @pytest.mark.asyncio
    async def test_create_tools_unknown_type(self, registry):
        """Test that unknown tool types are skipped."""
        tool_configs = [
            {"type": "unknown", "name": "test"},
            {"type": "mcp", "name": "microsoft-learn"}
        ]
        
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn:
            mock_learn.return_value = Mock()
            
            tools = await registry._create_tools(tool_configs)
            
            # Should only create the valid tool
            assert len(tools) == 1
    
    @pytest.mark.asyncio
    async def test_create_tools_missing_type(self, registry):
        """Test that tools without type are skipped."""
        tool_configs = [
            {"name": "test"},  # Missing type
            {"type": "mcp", "name": "microsoft-learn"}
        ]
        
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn:
            mock_learn.return_value = Mock()
            
            tools = await registry._create_tools(tool_configs)
            
            assert len(tools) == 1
    
    @pytest.mark.asyncio
    async def test_create_tools_handles_exceptions(self, registry):
        """Test that tool creation exceptions are handled gracefully."""
        tool_configs = [
            {"type": "mcp", "name": "microsoft-learn"},
            {"type": "mcp", "name": "failing-tool"}
        ]
        
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn:
            mock_learn.return_value = Mock()
            
            # Second tool will fail (not implemented)
            tools = await registry._create_tools(tool_configs)
            
            # Should still create the valid tool
            assert len(tools) == 1


class TestAgentRegistrySpecificTools:
    """Tests for specific tool creation."""
    
    @pytest.mark.asyncio
    async def test_create_microsoft_learn_tool(self, registry):
        """Test creating Microsoft Learn MCP tool."""
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_tool:
            mock_tool.return_value = Mock(name="learn_tool")
            
            tool = await registry._create_mcp_tool("microsoft-learn")
            
            assert tool is not None
            mock_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_azure_mcp_tool(self, registry):
        """Test creating Azure MCP tool."""
        with patch('src.agents.registry.get_azure_mcp_tool') as mock_tool:
            mock_tool.return_value = Mock(name="azure_tool")
            
            tool = await registry._create_mcp_tool("azure-mcp")
            
            assert tool is not None
            mock_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_unknown_mcp_tool(self, registry):
        """Test creating unknown MCP tool returns None."""
        tool = await registry._create_mcp_tool("unknown-mcp")
        
        assert tool is None
    
    @pytest.mark.asyncio
    async def test_create_support_triage_tool(self, registry):
        """Test creating Support Triage OpenAPI tool."""
        with patch('src.agents.registry.get_support_triage_tool') as mock_tool:
            mock_tool.return_value = Mock(name="support_tool")
            
            tool = await registry._create_openapi_tool("support-triage")
            
            assert tool is not None
            mock_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_ops_assistant_tool(self, registry):
        """Test creating Ops Assistant OpenAPI tool."""
        with patch('src.agents.registry.get_ops_assistant_tool') as mock_tool:
            mock_tool.return_value = Mock(name="ops_tool")
            
            tool = await registry._create_openapi_tool("ops-assistant")
            
            assert tool is not None
            mock_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_unknown_openapi_tool(self, registry):
        """Test creating unknown OpenAPI tool returns None."""
        tool = await registry._create_openapi_tool("unknown-api")
        
        assert tool is None


class TestAgentRegistryCleanup:
    """Tests for cleanup and resource management."""
    
    @pytest.mark.asyncio
    async def test_close_with_client(self):
        """Test closing registry with initialized client."""
        registry = AgentRegistry(
            cosmos_endpoint="https://test.documents.azure.com:443/",
            cosmos_database="test-db",
            cosmos_container="test-container"
        )
        
        # Mock client
        mock_client = AsyncMock()
        registry._cosmos_client = mock_client
        
        await registry.close()
        
        mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test closing registry without initialized client."""
        registry = AgentRegistry(
            cosmos_endpoint="https://test.documents.azure.com:443/",
            cosmos_database="test-db",
            cosmos_container="test-container"
        )
        
        # Should not raise exception
        await registry.close()


class TestAgentRegistryIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self, registry, sample_agent_config):
        """Test complete agent lifecycle: create, cache, reload."""
        # Mock Cosmos and tools
        registry._container.read_item = AsyncMock(return_value=sample_agent_config)
        
        with patch('src.agents.registry.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.registry.get_support_triage_tool') as mock_triage:
            
            mock_learn.return_value = Mock()
            mock_triage.return_value = Mock()
            
            # Get agent (creates and caches)
            agent1 = await registry.get_agent("support-triage")
            assert isinstance(agent1, DemoBaseAgent)
            assert "support-triage" in registry._cache
            
            # Get again (from cache)
            agent2 = await registry.get_agent("support-triage")
            assert agent1 is agent2
            
            # Reload (clears cache and recreates)
            agent3 = await registry.reload_agent("support-triage")
            assert agent1 is not agent3
            assert isinstance(agent3, DemoBaseAgent)
    
    @pytest.mark.asyncio
    async def test_multiple_agents(self, registry):
        """Test managing multiple agents."""
        configs = {
            "agent1": {
                "name": "Agent 1",
                "instructions": "Instructions 1",
                "tools": []
            },
            "agent2": {
                "name": "Agent 2",
                "instructions": "Instructions 2",
                "tools": []
            },
            "agent3": {
                "name": "Agent 3",
                "instructions": "Instructions 3",
                "tools": []
            }
        }
        
        async def mock_read_item(item, partition_key):
            return configs.get(item)
        
        registry._container.read_item = mock_read_item
        
        # Get all agents
        agent1 = await registry.get_agent("agent1")
        agent2 = await registry.get_agent("agent2")
        agent3 = await registry.get_agent("agent3")
        
        # Verify all cached
        assert len(registry._cache) == 3
        assert agent1.name == "Agent 1"
        assert agent2.name == "Agent 2"
        assert agent3.name == "Agent 3"
        
        # Clear cache
        registry.clear_cache()
        assert len(registry._cache) == 0
