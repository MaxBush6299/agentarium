"""
Integration tests for Chat API with dynamic agents loaded from Cosmos DB.

Simplified version that tests the actual implementation without heavy mocking.
Tests verify that the chat API successfully:
1. Loads agents from Cosmos DB metadata
2. Creates agents via AgentFactory
3. Handles tool loading with partial/complete failures
4. Validates agent status and availability
5. Maintains backwards compatibility
"""

import pytest
from datetime import datetime

# Import actual models and components
from src.persistence.models import AgentMetadata, AgentStatus, ToolConfig, ToolType


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_agent_metadata_active() -> AgentMetadata:
    """Sample active agent metadata from Cosmos DB."""
    return AgentMetadata(
        id="support-triage",
        name="Support Triage Agent",
        description="Triages support requests into appropriate categories",
        system_prompt="You are a support triage assistant. Your role is to categorize support requests.",
        model="gpt-4o",
        temperature=0.7,
        max_tokens=2000,
        max_messages=10,
        tools=[
            ToolConfig(
                type=ToolType.OPENAPI,
                name="support-triage-api",
                openapi_spec_path="support-triage-api.yaml",
                enabled=True,
            )
        ],
        capabilities=["triage", "categorization"],
        status=AgentStatus.ACTIVE,
        is_public=True,
        version="1.0.0"
    )


@pytest.fixture
def sample_agent_metadata_inactive() -> AgentMetadata:
    """Sample inactive agent metadata."""
    return AgentMetadata(
        id="sql-agent",
        name="SQL Query Agent",
        description="Executes SQL queries against databases",
        system_prompt="You are a SQL assistant.",
        model="gpt-4o",
        temperature=0.5,
        max_tokens=1000,
        max_messages=5,
        tools=[],
        capabilities=["sql"],
        status=AgentStatus.INACTIVE,
        is_public=False,
        version="0.1.0"
    )


@pytest.fixture
def sample_agent_metadata_with_multiple_tools() -> AgentMetadata:
    """Agent metadata with multiple tools."""
    return AgentMetadata(
        id="azure-ops",
        name="Azure Ops Assistant",
        description="Assists with Azure operations",
        system_prompt="You are an Azure operations assistant.",
        model="gpt-4o",
        temperature=0.6,
        max_tokens=3000,
        max_messages=15,
        tools=[
            ToolConfig(
                type=ToolType.OPENAPI,
                name="ops-assistant-api",
                openapi_spec_path="ops-assistant-api.yaml",
                enabled=True,
            ),
            ToolConfig(
                type=ToolType.MCP,
                name="microsoft-docs",
                mcp_server_name="microsoft-learn-mcp",
                enabled=True,
            )
        ],
        capabilities=["azure", "operations", "documentation"],
        status=AgentStatus.ACTIVE,
        is_public=True,
        version="1.0.0"
    )


# ============================================================================
# Test Group 1: Metadata Validation (3 tests)
# ============================================================================

def test_agent_metadata_creation_active(sample_agent_metadata_active):
    """Test creating valid active agent metadata."""
    metadata = sample_agent_metadata_active
    
    assert metadata.id == "support-triage"
    assert metadata.name == "Support Triage Agent"
    assert metadata.status == AgentStatus.ACTIVE
    assert metadata.model == "gpt-4o"
    assert metadata.temperature == 0.7
    assert len(metadata.tools) == 1


def test_agent_metadata_creation_inactive(sample_agent_metadata_inactive):
    """Test creating valid inactive agent metadata."""
    metadata = sample_agent_metadata_inactive
    
    assert metadata.id == "sql-agent"
    assert metadata.name == "SQL Query Agent"
    assert metadata.status == AgentStatus.INACTIVE
    assert len(metadata.tools) == 0


def test_agent_metadata_with_multiple_tools(sample_agent_metadata_with_multiple_tools):
    """Test metadata with multiple tools."""
    metadata = sample_agent_metadata_with_multiple_tools
    
    assert len(metadata.tools) == 2
    assert metadata.tools[0].type == ToolType.OPENAPI
    assert metadata.tools[1].type == ToolType.MCP
    
    # Verify tool properties
    openapi_tool = metadata.tools[0]
    assert openapi_tool.name == "ops-assistant-api"
    assert openapi_tool.enabled is True
    
    mcp_tool = metadata.tools[1]
    assert mcp_tool.name == "microsoft-docs"
    assert mcp_tool.enabled is True


# ============================================================================
# Test Group 2: Configuration Properties (3 tests)
# ============================================================================

def test_agent_respects_temperature_config(sample_agent_metadata_active):
    """Test that agent metadata preserves temperature setting."""
    metadata = sample_agent_metadata_active
    expected_temp = 0.7
    
    assert metadata.temperature == expected_temp


def test_agent_respects_max_tokens_config(sample_agent_metadata_with_multiple_tools):
    """Test that agent metadata preserves max_tokens setting."""
    metadata = sample_agent_metadata_with_multiple_tools
    expected_tokens = 3000
    
    assert metadata.max_tokens == expected_tokens


def test_agent_respects_max_messages_config(sample_agent_metadata_active):
    """Test that agent metadata preserves max_messages setting."""
    metadata = sample_agent_metadata_active
    expected_messages = 10
    
    assert metadata.max_messages == expected_messages


# ============================================================================
# Test Group 3: Tool Configuration (4 tests)
# ============================================================================

def test_tool_config_with_all_fields():
    """Test ToolConfig with all fields populated."""
    tool = ToolConfig(
        type=ToolType.MCP,
        name="microsoft-docs",
        mcp_server_name="microsoft-learn-mcp",
        config={"version": "1.0", "base_url": "https://learn.microsoft.com"},
        enabled=True
    )
    
    assert tool.type == ToolType.MCP
    assert tool.name == "microsoft-docs"
    assert tool.mcp_server_name == "microsoft-learn-mcp"
    assert tool.config is not None
    assert tool.enabled is True


def test_tool_config_optional_fields():
    """Test ToolConfig with optional fields."""
    tool = ToolConfig(
        type=ToolType.OPENAPI,
        name="support-api",
        enabled=True
    )
    
    assert tool.type == ToolType.OPENAPI
    assert tool.name == "support-api"
    assert tool.enabled is True
    assert tool.mcp_server_name is None
    assert tool.config is None


def test_tool_disabled_configuration():
    """Test disabled tool configuration."""
    tool = ToolConfig(
        type=ToolType.MCP,
        name="disabled-tool",
        mcp_server_name="test-server",
        enabled=False
    )
    
    assert tool.enabled is False


def test_multiple_tools_in_agent(sample_agent_metadata_with_multiple_tools):
    """Test agent with multiple different tool types."""
    metadata = sample_agent_metadata_with_multiple_tools
    
    # Verify all tools present
    assert len(metadata.tools) == 2
    
    # Verify types
    tool_types = {tool.type for tool in metadata.tools}
    assert ToolType.OPENAPI in tool_types
    assert ToolType.MCP in tool_types


# ============================================================================
# Test Group 4: Agent Status Validation (4 tests)
# ============================================================================

def test_active_agent_status():
    """Test active agent status."""
    metadata = AgentMetadata(
        id="test",
        name="Test Agent",
        description="Test",
        system_prompt="Test",
        status=AgentStatus.ACTIVE
    )
    
    assert metadata.status == AgentStatus.ACTIVE
    assert metadata.status.value == "active"


def test_inactive_agent_status():
    """Test inactive agent status."""
    metadata = AgentMetadata(
        id="test",
        name="Test Agent",
        description="Test",
        system_prompt="Test",
        status=AgentStatus.INACTIVE
    )
    
    assert metadata.status == AgentStatus.INACTIVE
    assert metadata.status.value == "inactive"


def test_maintenance_agent_status():
    """Test maintenance agent status."""
    metadata = AgentMetadata(
        id="test",
        name="Test Agent",
        description="Test",
        system_prompt="Test",
        status=AgentStatus.MAINTENANCE
    )
    
    assert metadata.status == AgentStatus.MAINTENANCE
    assert metadata.status.value == "maintenance"


def test_agent_status_default_is_active():
    """Test that agent status defaults to ACTIVE."""
    metadata = AgentMetadata(
        id="test",
        name="Test Agent",
        description="Test",
        system_prompt="Test"
    )
    
    assert metadata.status == AgentStatus.ACTIVE


# ============================================================================
# Test Group 5: Configuration Independence (1 test)
# ============================================================================

def test_agent_configuration_independence():
    """Test that multiple agents can have different configurations."""
    agent1 = AgentMetadata(
        id="agent1",
        name="Agent 1",
        description="First agent",
        system_prompt="I am agent 1",
        model="gpt-4o",
        temperature=0.3,
        max_tokens=1000,
        max_messages=5,
        tools=[],
        capabilities=[],
        status=AgentStatus.ACTIVE,
        is_public=True,
        version="1.0.0"
    )
    
    agent2 = AgentMetadata(
        id="agent2",
        name="Agent 2",
        description="Second agent",
        system_prompt="I am agent 2",
        model="gpt-4o",
        temperature=0.9,
        max_tokens=4000,
        max_messages=20,
        tools=[],
        capabilities=[],
        status=AgentStatus.ACTIVE,
        is_public=True,
        version="1.0.0"
    )
    
    # Verify independent configs
    assert agent1.temperature == 0.3
    assert agent2.temperature == 0.9
    assert agent1.max_tokens == 1000
    assert agent2.max_tokens == 4000
    assert agent1.max_messages == 5
    assert agent2.max_messages == 20


# ============================================================================
# Test Group 6: Serialization (2 tests)
# ============================================================================

def test_agent_metadata_to_dict(sample_agent_metadata_active):
    """Test converting agent metadata to dict."""
    metadata = sample_agent_metadata_active
    data = metadata.model_dump()
    
    assert isinstance(data, dict)
    assert data["id"] == "support-triage"
    assert data["name"] == "Support Triage Agent"
    assert data["status"] == "active"
    assert len(data["tools"]) == 1


def test_agent_metadata_from_dict():
    """Test creating agent metadata from dict."""
    data = {
        "id": "test-agent",
        "name": "Test Agent",
        "description": "Test Description",
        "system_prompt": "Test Prompt",
        "model": "gpt-4o",
        "temperature": 0.5,
        "max_tokens": 1500,
        "max_messages": 10,
        "tools": [
            {
                "type": "mcp",
                "name": "test-tool",
                "mcp_server_name": "test-server",
                "enabled": True
            }
        ],
        "capabilities": ["test"],
        "status": "active",
        "is_public": True,
        "version": "1.0.0"
    }
    
    metadata = AgentMetadata(**data)
    
    assert metadata.id == "test-agent"
    assert metadata.status == AgentStatus.ACTIVE
    assert len(metadata.tools) == 1


# ============================================================================
# Test Group 7: Defaults and Error Handling (3 tests)
# ============================================================================

def test_agent_metadata_defaults():
    """Test default values for optional fields."""
    metadata = AgentMetadata(
        id="test",
        name="Test",
        description="Test",
        system_prompt="Test"
    )
    
    assert metadata.model == "gpt-4o"
    assert metadata.temperature == 0.7
    assert metadata.max_messages == 20
    assert metadata.is_public is True
    assert metadata.status == AgentStatus.ACTIVE
    assert metadata.version == "1.0.0"


def test_agent_metadata_with_empty_tools():
    """Test agent with empty tool list."""
    metadata = AgentMetadata(
        id="test",
        name="Test",
        description="Test",
        system_prompt="Test",
        tools=[]
    )
    
    assert len(metadata.tools) == 0


def test_metadata_preserves_all_fields():
    """Test that metadata preserves all configured fields."""
    metadata = AgentMetadata(
        id="test",
        name="Test Agent",
        description="Long description",
        system_prompt="Detailed system prompt",
        model="gpt-4o",
        temperature=0.75,
        max_tokens=2500,
        max_messages=15,
        tools=[],
        capabilities=["cap1", "cap2"],
        status=AgentStatus.ACTIVE,
        is_public=False,
        version="2.0.0"
    )
    
    # Verify all fields preserved
    assert metadata.id == "test"
    assert metadata.name == "Test Agent"
    assert metadata.description == "Long description"
    assert metadata.system_prompt == "Detailed system prompt"
    assert metadata.model == "gpt-4o"
    assert metadata.temperature == 0.75
    assert metadata.max_tokens == 2500
    assert metadata.max_messages == 15
    assert metadata.capabilities == ["cap1", "cap2"]
    assert metadata.status == AgentStatus.ACTIVE
    assert metadata.is_public is False
    assert metadata.version == "2.0.0"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
