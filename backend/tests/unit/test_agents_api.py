"""
Unit tests for Agent Management API endpoints
Tests request/response models, validation, and error handling.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.persistence.models import (
    AgentMetadata,
    AgentStatus,
    ToolType,
    ToolConfig,
    AgentCreateRequest,
    AgentUpdateRequest
)


def test_agent_metadata_model():
    """Test AgentMetadata model creation."""
    agent = AgentMetadata(
        id="test-agent",
        name="Test Agent",
        description="Test agent description",
        system_prompt="You are a test agent",
        model="gpt-4o",
        temperature=0.7,
        tools=[
            ToolConfig(
                type=ToolType.MCP,
                name="test-tool",
                mcp_server_name="test-server"
            )
        ],
        capabilities=["test-capability"],
        status=AgentStatus.ACTIVE
    )
    
    assert agent.id == "test-agent"
    assert agent.name == "Test Agent"
    assert agent.status == AgentStatus.ACTIVE
    assert len(agent.tools) == 1
    assert agent.tools[0].type == ToolType.MCP
    assert agent.total_runs == 0
    assert agent.total_tokens == 0


def test_tool_config_model():
    """Test ToolConfig model with different tool types."""
    # MCP tool
    mcp_tool = ToolConfig(
        type=ToolType.MCP,
        name="microsoft-docs",
        mcp_server_name="microsoft-learn-mcp"
    )
    assert mcp_tool.type == ToolType.MCP
    assert mcp_tool.mcp_server_name == "microsoft-learn-mcp"
    
    # OpenAPI tool
    openapi_tool = ToolConfig(
        type=ToolType.OPENAPI,
        name="api-tool",
        openapi_spec_path="/path/to/spec.yaml"
    )
    assert openapi_tool.type == ToolType.OPENAPI
    assert openapi_tool.openapi_spec_path == "/path/to/spec.yaml"
    
    # A2A tool
    a2a_tool = ToolConfig(
        type=ToolType.A2A,
        name="remote-agent",
        a2a_agent_id="other-agent"
    )
    assert a2a_tool.type == ToolType.A2A
    assert a2a_tool.a2a_agent_id == "other-agent"


def test_agent_create_request():
    """Test AgentCreateRequest model."""
    request = AgentCreateRequest(
        id="new-agent",
        name="New Agent",
        description="New agent description",
        system_prompt="System prompt",
        model="gpt-4o",
        temperature=0.8,
        tools=[],
        capabilities=["capability1", "capability2"]
    )
    
    assert request.id == "new-agent"
    assert request.temperature == 0.8
    assert len(request.capabilities) == 2


def test_agent_update_request():
    """Test AgentUpdateRequest model with partial updates."""
    # All fields optional
    request = AgentUpdateRequest(
        name="Updated Name",
        temperature=0.5
    )
    
    assert request.name == "Updated Name"
    assert request.temperature == 0.5
    assert request.description is None  # Not provided
    assert request.system_prompt is None  # Not provided
    
    # Test model_dump(exclude_none=True)
    update_dict = request.model_dump(exclude_none=True)
    assert "name" in update_dict
    assert "temperature" in update_dict
    assert "description" not in update_dict


def test_agent_status_enum():
    """Test AgentStatus enum values."""
    assert AgentStatus.ACTIVE.value == "active"
    assert AgentStatus.INACTIVE.value == "inactive"
    assert AgentStatus.MAINTENANCE.value == "maintenance"


def test_tool_type_enum():
    """Test ToolType enum values."""
    assert ToolType.MCP.value == "mcp"
    assert ToolType.OPENAPI.value == "openapi"
    assert ToolType.A2A.value == "a2a"
    assert ToolType.BUILTIN.value == "builtin"


# ============================================================================
# API Endpoint Tests (with mocked repository)
# ============================================================================

@pytest.fixture
def mock_agent_repo():
    """Mock agent repository for testing."""
    with patch('src.api.agents.get_agent_repository') as mock:
        repo = Mock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def test_agent():
    """Sample agent for testing."""
    return AgentMetadata(
        id="test-agent",
        name="Test Agent",
        description="Test agent description",
        system_prompt="You are a test agent",
        model="gpt-4o",
        temperature=0.7,
        tools=[],
        capabilities=["test"],
        status=AgentStatus.ACTIVE
    )


def test_list_agents_endpoint(mock_agent_repo, test_agent):
    """Test GET /api/agents endpoint."""
    from src.api.agents import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock repository response
    mock_agent_repo.list.return_value = [test_agent]
    mock_agent_repo.count.return_value = 1
    
    # Make request
    response = client.get("/api/agents")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["agents"]) == 1
    assert data["agents"][0]["id"] == "test-agent"


def test_get_agent_endpoint(mock_agent_repo, test_agent):
    """Test GET /api/agents/{agent_id} endpoint."""
    from src.api.agents import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock repository response
    mock_agent_repo.get.return_value = test_agent
    
    # Make request
    response = client.get("/api/agents/test-agent")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-agent"
    assert data["name"] == "Test Agent"


def test_get_agent_not_found(mock_agent_repo):
    """Test GET /api/agents/{agent_id} with non-existent agent."""
    from src.api.agents import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock repository response
    mock_agent_repo.get.return_value = None
    
    # Make request
    response = client.get("/api/agents/nonexistent")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_agent_endpoint(mock_agent_repo, test_agent):
    """Test POST /api/agents endpoint."""
    from src.api.agents import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock repository responses
    mock_agent_repo.get.return_value = None  # Agent doesn't exist
    mock_agent_repo.create.return_value = test_agent
    
    # Make request
    request_data = {
        "id": "test-agent",
        "name": "Test Agent",
        "description": "Test agent description",
        "system_prompt": "You are a test agent",
        "model": "gpt-4o",
        "temperature": 0.7,
        "tools": [],
        "capabilities": ["test"]
    }
    response = client.post("/api/agents", json=request_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test-agent"


def test_create_agent_already_exists(mock_agent_repo, test_agent):
    """Test POST /api/agents with existing agent ID."""
    from src.api.agents import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock repository response - agent exists
    mock_agent_repo.get.return_value = test_agent
    
    # Make request
    request_data = {
        "id": "test-agent",
        "name": "Test Agent",
        "description": "Test agent description",
        "system_prompt": "You are a test agent"
    }
    response = client.post("/api/agents", json=request_data)
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_update_agent_endpoint(mock_agent_repo, test_agent):
    """Test PUT /api/agents/{agent_id} endpoint."""
    from src.api.agents import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock repository response
    updated_agent = test_agent.model_copy()
    updated_agent.name = "Updated Name"
    mock_agent_repo.update.return_value = updated_agent
    
    # Make request
    request_data = {"name": "Updated Name"}
    response = client.put("/api/agents/test-agent", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


def test_delete_agent_endpoint(mock_agent_repo):
    """Test DELETE /api/agents/{agent_id} endpoint."""
    from src.api.agents import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock repository response
    mock_agent_repo.delete.return_value = True
    
    # Make request
    response = client.delete("/api/agents/test-agent")
    
    assert response.status_code == 204


def test_activate_agent_endpoint(mock_agent_repo, test_agent):
    """Test POST /api/agents/{agent_id}/activate endpoint."""
    from src.api.agents import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock repository responses
    mock_agent_repo.activate.return_value = True
    mock_agent_repo.get.return_value = test_agent
    
    # Make request
    response = client.post("/api/agents/test-agent/activate")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-agent"


def test_deactivate_agent_endpoint(mock_agent_repo, test_agent):
    """Test POST /api/agents/{agent_id}/deactivate endpoint."""
    from src.api.agents import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock repository responses
    mock_agent_repo.deactivate.return_value = True
    inactive_agent = test_agent.model_copy()
    inactive_agent.status = AgentStatus.INACTIVE
    mock_agent_repo.get.return_value = inactive_agent
    
    # Make request
    response = client.post("/api/agents/test-agent/deactivate")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-agent"
    assert data["status"] == "inactive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
