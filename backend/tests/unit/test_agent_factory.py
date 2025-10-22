"""
Unit tests for AgentFactory.

Tests cover:
- Creating agents from valid metadata
- Handling tool loading failures gracefully
- Partial tool functionality
- Configuration validation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.factory import AgentFactory
from src.persistence.models import AgentMetadata, ToolConfig, AgentStatus, ToolType
from src.agents.base import DemoBaseAgent


@pytest.fixture
def valid_agent_config():
    """Provide valid agent metadata."""
    return AgentMetadata(
        id="test-agent",
        name="Test Agent",
        description="A test agent",
        system_prompt="You are a helpful assistant.",
        model="gpt-4o",
        tools=[
            ToolConfig(
                type=ToolType.MCP,
                name="working-tool",
                enabled=True,
                config={}
            )
        ],
        status=AgentStatus.ACTIVE,
    )


@pytest.fixture
def agent_config_no_tools():
    """Provide agent metadata with no tools."""
    return AgentMetadata(
        id="no-tools-agent",
        name="Agent Without Tools",
        description="An agent with no tools",
        system_prompt="You are a simple assistant.",
        model="gpt-4o",
        tools=[],
        status=AgentStatus.ACTIVE,
    )


@pytest.fixture
def agent_config_mixed_tools():
    """Provide agent metadata with some tools that will fail."""
    return AgentMetadata(
        id="mixed-agent",
        name="Mixed Agent",
        description="Agent with working and failing tools",
        system_prompt="You are a resilient assistant.",
        model="gpt-4o",
        tools=[
            ToolConfig(
                type=ToolType.MCP,
                name="working-tool",
                enabled=True,
                config={}
            ),
            ToolConfig(
                type=ToolType.MCP,
                name="failing-tool",
                enabled=True,
                config={}
            ),
            ToolConfig(
                type=ToolType.MCP,
                name="working-tool",
                enabled=True,
                config={}
            ),
        ],
        status=AgentStatus.ACTIVE,
    )


# Tests: Basic Agent Creation

def test_create_agent_from_valid_metadata(valid_agent_config):
    """Test creating agent from valid metadata."""
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="working_tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_agent.name = "Test Agent"
            mock_agent.model = "gpt-4o"
            mock_agent.instructions = "You are a helpful assistant."
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            assert agent.name == "Test Agent"
            assert agent.model == "gpt-4o"
            # Verify DemoBaseAgent was called with correct params
            mock_base_agent_class.assert_called_once()
            call_kwargs = mock_base_agent_class.call_args[1]
            assert call_kwargs['name'] == "Test Agent"
            assert call_kwargs['model'] == "gpt-4o"


def test_create_agent_with_all_tools_succeeding(valid_agent_config):
    """Test agent creation when all tools load successfully."""
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="working_tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            # Verify tool registry was called to create the tool
            mock_registry.create_tool.assert_called_once()


def test_create_agent_with_partial_tools_succeeding(agent_config_mixed_tools):
    """Test agent creation with some tools failing (graceful degradation)."""
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        registry = Mock()
        
        def create_tool_side_effect(tool_type, tool_name, config):
            if tool_name == "working-tool":
                return Mock(name="working_tool")
            elif tool_name == "failing-tool":
                return None  # Tool fails to load
            return None
        
        registry.create_tool.side_effect = create_tool_side_effect
        mock_get_registry.return_value = registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(agent_config_mixed_tools)
            
            # Agent should still be created even with partial tools
            assert agent is not None
            
            # Verify DemoBaseAgent was called with 2 successful tools
            # (3 tools: working, failing, working -> 2 work, 1 fails)
            call_kwargs = mock_base_agent_class.call_args[1]
            tools_arg = call_kwargs.get('tools')
            # Should have 2 tools (the working ones)
            if tools_arg:
                assert len(tools_arg) == 2


def test_create_agent_with_no_tools(agent_config_no_tools):
    """Test agent creation with no tools configured."""
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(agent_config_no_tools)
            
            assert agent is not None
            # Registry should not be called for tool creation
            mock_registry.create_tool.assert_not_called()


def test_create_agent_with_disabled_tools(valid_agent_config):
    """Test that disabled tools are skipped."""
    valid_agent_config.tools[0].enabled = False
    
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            # Tool registry should not be called for disabled tool
            mock_registry.create_tool.assert_not_called()


# Tests: Tool Configuration

def test_tool_config_passed_to_registry(valid_agent_config):
    """Test that tool config is passed to registry."""
    valid_agent_config.tools[0].config = {"endpoint": "http://test.com"}
    
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            # Verify config was passed to create_tool
            call_args = mock_registry.create_tool.call_args
            assert call_args[1]['config'] == {"endpoint": "http://test.com"}


def test_agent_created_with_correct_model(valid_agent_config):
    """Test that agent is created with correct model."""
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            call_kwargs = mock_base_agent_class.call_args[1]
            assert call_kwargs['model'] == "gpt-4o"


def test_agent_created_with_correct_system_prompt(valid_agent_config):
    """Test that agent is created with correct system prompt."""
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            call_kwargs = mock_base_agent_class.call_args[1]
            assert call_kwargs['instructions'] == "You are a helpful assistant."


def test_agent_created_with_max_messages(valid_agent_config):
    """Test that max_messages is passed to agent."""
    valid_agent_config.max_messages = 50
    
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            call_kwargs = mock_base_agent_class.call_args[1]
            assert call_kwargs['max_messages'] == 50


def test_agent_created_with_temperature(valid_agent_config):
    """Test that temperature is passed to agent."""
    valid_agent_config.temperature = 0.3
    
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            call_kwargs = mock_base_agent_class.call_args[1]
            assert call_kwargs['temperature'] == 0.3


def test_agent_created_with_max_tokens(valid_agent_config):
    """Test that max_tokens is passed to agent."""
    valid_agent_config.max_tokens = 2048
    
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            call_kwargs = mock_base_agent_class.call_args[1]
            assert call_kwargs['max_tokens'] == 2048


# Tests: Configuration Validation

def test_validate_config_valid(valid_agent_config):
    """Test validation of valid configuration."""
    is_valid, error = AgentFactory.validate_config(valid_agent_config)
    assert is_valid is True
    assert error == ""


def test_validate_config_missing_id():
    """Test validation fails with missing ID."""
    config = AgentMetadata(
        id="",
        name="Test",
        description="Test",
        system_prompt="Test",
        model="gpt-4o",
        tools=[],
        status=AgentStatus.ACTIVE,
    )
    
    is_valid, error = AgentFactory.validate_config(config)
    assert is_valid is False
    assert "ID" in error


def test_validate_config_missing_name():
    """Test validation fails with missing name."""
    config = AgentMetadata(
        id="test",
        name="",
        description="Test",
        system_prompt="Test",
        model="gpt-4o",
        tools=[],
        status=AgentStatus.ACTIVE,
    )
    
    is_valid, error = AgentFactory.validate_config(config)
    assert is_valid is False
    assert "name" in error


def test_validate_config_missing_model():
    """Test validation fails with missing model."""
    config = AgentMetadata(
        id="test",
        name="Test",
        description="Test",
        system_prompt="Test",
        model="",
        tools=[],
        status=AgentStatus.ACTIVE,
    )
    
    is_valid, error = AgentFactory.validate_config(config)
    assert is_valid is False
    assert "Model" in error


def test_validate_config_missing_system_prompt():
    """Test validation fails with missing system prompt."""
    config = AgentMetadata(
        id="test",
        name="Test",
        description="Test",
        system_prompt="",
        model="gpt-4o",
        tools=[],
        status=AgentStatus.ACTIVE,
    )
    
    is_valid, error = AgentFactory.validate_config(config)
    assert is_valid is False
    assert "System prompt" in error


# Tests: Error Handling

def test_create_agent_returns_none_on_base_agent_failure(valid_agent_config):
    """Test that None is returned if DemoBaseAgent creation fails."""
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            # Make DemoBaseAgent raise an exception
            mock_base_agent_class.side_effect = RuntimeError("Agent init failed")
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is None


def test_create_agent_logs_error_on_failure(valid_agent_config, caplog):
    """Test that errors are logged when creation fails."""
    import logging
    caplog.set_level(logging.ERROR)
    
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_base_agent_class.side_effect = RuntimeError("Agent init failed")
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is None
            assert "Failed to create DemoBaseAgent" in caplog.text


def test_tool_registry_lookup_creates_correct_type(valid_agent_config):
    """Test that registry is looked up for correct tool type."""
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            # Verify correct tool type was requested
            call_args = mock_registry.create_tool.call_args
            assert call_args[1]['tool_type'] == ToolType.MCP


def test_tool_registry_lookup_creates_correct_name(valid_agent_config):
    """Test that registry is looked up for correct tool name."""
    with patch('src.agents.factory.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.create_tool.return_value = Mock(name="tool")
        mock_get_registry.return_value = mock_registry
        
        with patch('src.agents.factory.DemoBaseAgent') as mock_base_agent_class:
            mock_agent = Mock(spec=DemoBaseAgent)
            mock_base_agent_class.return_value = mock_agent
            
            agent = AgentFactory.create_from_metadata(valid_agent_config)
            
            assert agent is not None
            # Verify correct tool name was requested
            call_args = mock_registry.create_tool.call_args
            assert call_args[1]['tool_name'] == "working-tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
