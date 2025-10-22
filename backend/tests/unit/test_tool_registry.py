"""
Unit tests for ToolRegistry.

Tests cover:
- Tool registration and lookup
- Tool creation and factory invocation
- Error handling and graceful failure
- Registry state management
"""

import pytest
from unittest.mock import Mock, patch
from src.agents.tool_registry import (
    ToolRegistry,
    ToolDefinition,
    get_tool_registry,
    register_default_tools,
)


@pytest.fixture
def registry():
    """Provide a fresh tool registry for each test."""
    return ToolRegistry()


@pytest.fixture
def mock_tool_definition():
    """Provide a mock tool definition."""
    return ToolDefinition(
        type="test",
        name="mock-tool",
        description="A mock tool for testing",
        factory=lambda cfg: Mock(name="MockTool"),
        required_config={},
        optional_config={"setting": "A test setting"},
    )


# Tests: Tool Registration

def test_register_tool(registry, mock_tool_definition):
    """Test that tools can be registered."""
    registry.register(mock_tool_definition)
    assert "test:mock-tool" in registry.tools
    assert registry.tools["test:mock-tool"] == mock_tool_definition


def test_register_multiple_tools(registry):
    """Test registering multiple tools."""
    tool1 = ToolDefinition(
        type="mcp", name="tool1", description="Tool 1",
        factory=lambda cfg: Mock()
    )
    tool2 = ToolDefinition(
        type="openapi", name="tool2", description="Tool 2",
        factory=lambda cfg: Mock()
    )
    
    registry.register(tool1)
    registry.register(tool2)
    
    assert len(registry.tools) == 2
    assert registry.get("mcp", "tool1") == tool1
    assert registry.get("openapi", "tool2") == tool2


def test_register_overwrite_existing(registry, mock_tool_definition):
    """Test that registering a tool twice overwrites the first."""
    registry.register(mock_tool_definition)
    
    new_definition = ToolDefinition(
        type="test", name="mock-tool", description="Updated tool",
        factory=lambda cfg: Mock(name="UpdatedMockTool")
    )
    registry.register(new_definition)
    
    assert registry.get("test", "mock-tool") == new_definition


# Tests: Tool Lookup

def test_get_existing_tool(registry, mock_tool_definition):
    """Test retrieving a registered tool."""
    registry.register(mock_tool_definition)
    retrieved = registry.get("test", "mock-tool")
    
    assert retrieved is not None
    assert retrieved == mock_tool_definition


def test_get_nonexistent_tool(registry):
    """Test that getting non-existent tool returns None."""
    result = registry.get("fake", "nonexistent")
    assert result is None


def test_get_wrong_type(registry, mock_tool_definition):
    """Test that wrong type returns None even if name matches."""
    registry.register(mock_tool_definition)
    result = registry.get("wrong", "mock-tool")
    assert result is None


def test_get_wrong_name(registry, mock_tool_definition):
    """Test that wrong name returns None even if type matches."""
    registry.register(mock_tool_definition)
    result = registry.get("test", "wrong-name")
    assert result is None


# Tests: Tool Creation

def test_create_tool_success(registry, mock_tool_definition):
    """Test successful tool creation."""
    registry.register(mock_tool_definition)
    
    tool = registry.create_tool("test", "mock-tool", {})
    
    assert tool is not None
    # Tool is a mock object, just verify it was created
    assert tool is not None


def test_create_tool_with_config(registry):
    """Test tool creation passes config to factory."""
    config_received = {}
    
    def factory(cfg):
        config_received.update(cfg)
        return Mock()
    
    tool_def = ToolDefinition(
        type="test", name="tool", description="Tool",
        factory=factory
    )
    registry.register(tool_def)
    
    test_config = {"key": "value", "setting": "enabled"}
    tool = registry.create_tool("test", "tool", test_config)
    
    assert tool is not None
    assert config_received == test_config


def test_create_tool_not_found(registry):
    """Test creating non-existent tool returns None."""
    tool = registry.create_tool("fake", "tool", {})
    assert tool is None


def test_create_tool_factory_returns_none(registry):
    """Test when factory returns None."""
    tool_def = ToolDefinition(
        type="test", name="tool", description="Tool",
        factory=lambda cfg: None
    )
    registry.register(tool_def)
    
    tool = registry.create_tool("test", "tool", {})
    assert tool is None


def test_create_tool_factory_exception(registry):
    """Test graceful failure when factory raises exception."""
    def failing_factory(cfg):
        raise ValueError("Factory failed!")
    
    tool_def = ToolDefinition(
        type="test", name="tool", description="Tool",
        factory=failing_factory
    )
    registry.register(tool_def)
    
    # Should return None, not raise
    tool = registry.create_tool("test", "tool", {})
    assert tool is None


def test_create_tool_timeout_exception(registry):
    """Test handling of timeout exceptions."""
    def timeout_factory(cfg):
        raise TimeoutError("Connection timeout")
    
    tool_def = ToolDefinition(
        type="mcp", name="slow-tool", description="Slow tool",
        factory=timeout_factory
    )
    registry.register(tool_def)
    
    tool = registry.create_tool("mcp", "slow-tool", {})
    assert tool is None


# Tests: Registry State

def test_list_all_tools(registry):
    """Test listing all tools."""
    tool1 = ToolDefinition(
        type="mcp", name="tool1", description="Tool 1",
        factory=lambda cfg: Mock()
    )
    tool2 = ToolDefinition(
        type="openapi", name="tool2", description="Tool 2",
        factory=lambda cfg: Mock()
    )
    
    registry.register(tool1)
    registry.register(tool2)
    
    all_tools = registry.list_all()
    assert len(all_tools) == 2
    assert "mcp:tool1" in all_tools
    assert "openapi:tool2" in all_tools


def test_list_by_type(registry):
    """Test listing tools by type."""
    mcp_tool = ToolDefinition(
        type="mcp", name="mcp-tool", description="MCP",
        factory=lambda cfg: Mock()
    )
    openapi_tool = ToolDefinition(
        type="openapi", name="api-tool", description="API",
        factory=lambda cfg: Mock()
    )
    
    registry.register(mcp_tool)
    registry.register(openapi_tool)
    
    mcp_tools = registry.list_by_type("mcp")
    assert len(mcp_tools) == 1
    assert "mcp:mcp-tool" in mcp_tools
    
    api_tools = registry.list_by_type("openapi")
    assert len(api_tools) == 1
    assert "openapi:api-tool" in api_tools


def test_list_by_type_empty(registry):
    """Test listing by type with no matches."""
    result = registry.list_by_type("nonexistent")
    assert result == {}


# Tests: ToolDefinition

def test_tool_definition_full_name(mock_tool_definition):
    """Test full_name property."""
    assert mock_tool_definition.full_name == "test:mock-tool"


def test_tool_definition_defaults():
    """Test ToolDefinition with default values."""
    tool_def = ToolDefinition(
        type="test", name="tool", description="Test",
        factory=lambda cfg: Mock()
    )
    
    assert tool_def.required_config == {}
    assert tool_def.optional_config == {}


# Tests: Singleton

def test_get_tool_registry_singleton():
    """Test that get_tool_registry returns singleton."""
    registry1 = get_tool_registry()
    registry2 = get_tool_registry()
    
    assert registry1 is registry2


def test_singleton_state_persists():
    """Test that singleton maintains state."""
    registry = get_tool_registry()
    
    tool_def = ToolDefinition(
        type="test", name="persistent", description="Test",
        factory=lambda cfg: Mock()
    )
    registry.register(tool_def)
    
    # Get singleton again
    registry2 = get_tool_registry()
    assert registry2.get("test", "persistent") is not None


# Tests: Default Tools Registration

@pytest.mark.integration
def test_register_default_tools_succeeds():
    """Test that default tools register successfully."""
    # Create fresh registry
    fresh_registry = ToolRegistry()
    
    # Manually register defaults
    from src.agents.tool_registry import register_default_tools
    
    # This should not raise
    register_default_tools()
    
    # Check that at least some tools are registered
    default_registry = get_tool_registry()
    assert len(default_registry.list_all()) > 0


@pytest.mark.integration
def test_default_tools_are_accessible():
    """Test that default tools can be created."""
    registry = get_tool_registry()
    
    # Should have MCP tools
    mcp_tools = registry.list_by_type("mcp")
    assert len(mcp_tools) > 0
    
    # Should have OpenAPI tools
    api_tools = registry.list_by_type("openapi")
    assert len(api_tools) > 0


# Tests: Error Handling and Logging

def test_create_tool_logs_error(registry, caplog):
    """Test that failures are logged."""
    import logging
    caplog.set_level(logging.ERROR)
    
    def failing_factory(cfg):
        raise RuntimeError("Intentional error")
    
    tool_def = ToolDefinition(
        type="test", name="tool", description="Tool",
        factory=failing_factory
    )
    registry.register(tool_def)
    
    tool = registry.create_tool("test", "tool", {})
    
    assert tool is None
    assert "Failed to create tool" in caplog.text
    assert "Intentional error" in caplog.text


def test_register_tool_logs_info(registry, caplog):
    """Test that registration is logged."""
    import logging
    caplog.set_level(logging.INFO)
    
    tool_def = ToolDefinition(
        type="test", name="tool", description="Tool",
        factory=lambda cfg: Mock()
    )
    registry.register(tool_def)
    
    assert "Registered tool: test:tool" in caplog.text


def test_tool_not_found_logs_warning(registry, caplog):
    """Test that missing tools are logged as warnings."""
    import logging
    caplog.set_level(logging.WARNING)
    
    tool = registry.create_tool("fake", "tool", {})
    
    assert tool is None
    assert "Tool not found in registry" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
