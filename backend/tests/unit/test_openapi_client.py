"""
Unit tests for OpenAPI client.

Tests verify:
1. OpenAPI spec loading and parsing
2. Operation discovery
3. URL building and parameter handling
4. Factory functions for common APIs
"""
import pytest
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from tools.openapi_client import OpenAPITool, get_support_triage_tool, get_ops_assistant_tool


@pytest.fixture
def support_spec_path():
    """Path to support triage API spec."""
    return str(Path(__file__).parent.parent.parent / "openapi" / "support-triage-api.yaml")


@pytest.fixture
def ops_spec_path():
    """Path to ops assistant API spec."""
    return str(Path(__file__).parent.parent.parent / "openapi" / "ops-assistant-api.yaml")


class TestOpenAPIToolInit:
    """Test OpenAPITool initialization and spec parsing."""
    
    def test_init_lazy_loads_spec(self, support_spec_path):
        """Test that initialization does NOT load spec (lazy loading)."""
        # Create tool but don't access spec yet
        tool = OpenAPITool(spec_path=support_spec_path)
        
        # Spec should not be loaded yet
        assert tool._spec is None
        assert tool._operations is None
        assert tool._title is None
        assert tool._version is None
    
    def test_spec_loaded_on_first_access(self, support_spec_path):
        """Test that spec is loaded on first access (lazy loading)."""
        tool = OpenAPITool(spec_path=support_spec_path)
        
        # Access spec via property - should trigger load
        spec = tool.spec
        
        assert spec is not None
        assert tool.title == "Support Triage API"
        assert tool.version == "1.0.0"
        assert tool.base_url is not None
    
    def test_operations_loaded_on_first_access(self, support_spec_path):
        """Test that operations are loaded on first access."""
        tool = OpenAPITool(spec_path=support_spec_path)
        
        # Operations should not be loaded yet
        assert tool._operations is None
        
        # Access operations via property
        ops = tool.operations
        
        assert ops is not None
        assert len(ops) > 0
        assert all("operation_id" in op for op in ops)
    
    def test_spec_cached_after_first_load(self, support_spec_path):
        """Test that spec is cached and not reloaded."""
        tool = OpenAPITool(spec_path=support_spec_path)
        
        spec1 = tool.spec
        spec2 = tool.spec
        
        # Should be the exact same object (cached)
        assert spec1 is spec2
    
    def test_operations_cached_after_first_load(self, support_spec_path):
        """Test that operations are cached and not reparsed."""
        tool = OpenAPITool(spec_path=support_spec_path)
        
        ops1 = tool.operations
        ops2 = tool.operations
        
        # Should be the exact same object (cached)
        assert ops1 is ops2
    
    def test_load_support_spec(self, support_spec_path):
        """Test loading Support Triage API specification."""
        tool = OpenAPITool(spec_path=support_spec_path)
        
        assert tool.title == "Support Triage API"
        assert tool.version == "1.0.0"
        assert len(tool.operations) > 0
        assert tool.base_url is not None
    
    def test_load_ops_spec(self, ops_spec_path):
        """Test loading Ops Assistant API specification."""
        tool = OpenAPITool(spec_path=ops_spec_path)
        
        assert tool.title == "Ops Assistant API"
        assert tool.version == "1.0.0"
        assert len(tool.operations) > 0
        assert tool.base_url is not None
    
    def test_custom_base_url(self, support_spec_path):
        """Test custom base URL overrides spec."""
        custom_url = "https://custom.example.com/api"
        tool = OpenAPITool(
            spec_path=support_spec_path,
            base_url=custom_url
        )
        
        assert tool.base_url == custom_url
    
    def test_custom_api_key(self, support_spec_path):
        """Test custom API key configuration."""
        tool = OpenAPITool(
            spec_path=support_spec_path,
            api_key="test-key-123",
            api_key_header="X-Custom-Key"
        )
        
        assert tool.api_key == "test-key-123"
        assert tool.api_key_header == "X-Custom-Key"
    
    def test_invalid_spec_path(self):
        """Test that invalid spec path raises error on spec access."""
        tool = OpenAPITool(spec_path="/nonexistent/spec.yaml")
        
        # Initialization should not raise
        assert tool is not None
        
        # But accessing spec should raise
        with pytest.raises(FileNotFoundError):
            _ = tool.spec


class TestOpenAPIOperations:
    """Test operation parsing and discovery."""
    
    def test_support_api_operations(self, support_spec_path):
        """Test Support Triage API operations are parsed."""
        tool = OpenAPITool(spec_path=support_spec_path)
        
        # Should have operations for tickets and KB search
        op_ids = [op["operation_id"] for op in tool.operations]
        
        assert "searchTickets" in op_ids
        assert "getTicketById" in op_ids
        assert "searchKnowledgeBase" in op_ids
    
    def test_ops_api_operations(self, ops_spec_path):
        """Test Ops Assistant API operations are parsed."""
        tool = OpenAPITool(spec_path=ops_spec_path)
        
        op_ids = [op["operation_id"] for op in tool.operations]
        
        assert "getDeploymentStatus" in op_ids
        assert "getDeploymentHistory" in op_ids
        assert "rollbackDeployment" in op_ids
        assert "getRollbackStatus" in op_ids
    
    def test_get_operations_info(self, support_spec_path):
        """Test getting operation information."""
        tool = OpenAPITool(spec_path=support_spec_path)
        
        operations = tool.get_operations_info()
        
        assert len(operations) > 0
        for op in operations:
            assert "operation_id" in op
            assert "method" in op
            assert "path" in op
            assert "summary" in op
    
    def test_operation_details(self, support_spec_path):
        """Test operation has required details."""
        tool = OpenAPITool(spec_path=support_spec_path)
        
        # Find searchTickets operation
        search_op = next(op for op in tool.operations if op["operation_id"] == "searchTickets")
        
        assert search_op["method"] == "GET"
        assert search_op["path"] == "/tickets/search"
        assert "summary" in search_op
        assert "parameters" in search_op
        assert len(search_op["parameters"]) > 0  # Should have query params


class TestFactoryFunctions:
    """Test factory functions for common APIs."""
    
    def test_get_support_triage_tool(self):
        """Test Support Triage tool factory."""
        tool = get_support_triage_tool()
        
        assert isinstance(tool, OpenAPITool)
        assert tool.title == "Support Triage API"
        assert len(tool.operations) > 0
    
    def test_get_support_triage_tool_with_custom_url(self):
        """Test Support Triage tool with custom URL."""
        tool = get_support_triage_tool(base_url="https://custom.com/support")
        
        assert tool.base_url == "https://custom.com/support"
    
    def test_get_support_triage_tool_with_env_var(self):
        """Test Support Triage tool uses environment variables."""
        with patch.dict(os.environ, {
            "SUPPORT_API_URL": "https://env.example.com/support",
            "SUPPORT_API_KEY": "env-key-123"
        }):
            tool = get_support_triage_tool()
            
            assert tool.base_url == "https://env.example.com/support"
            assert tool.api_key == "env-key-123"
    
    def test_get_ops_assistant_tool(self):
        """Test Ops Assistant tool factory."""
        tool = get_ops_assistant_tool()
        
        assert isinstance(tool, OpenAPITool)
        assert tool.title == "Ops Assistant API"
        assert len(tool.operations) > 0
    
    def test_get_ops_assistant_tool_with_custom_url(self):
        """Test Ops Assistant tool with custom URL."""
        tool = get_ops_assistant_tool(base_url="https://custom.com/ops")
        
        assert tool.base_url == "https://custom.com/ops"
    
    def test_get_ops_assistant_tool_with_env_var(self):
        """Test Ops Assistant tool uses environment variables."""
        with patch.dict(os.environ, {
            "OPS_API_URL": "https://env.example.com/ops",
            "OPS_API_KEY": "env-key-456"
        }):
            tool = get_ops_assistant_tool()
            
            assert tool.base_url == "https://env.example.com/ops"
            assert tool.api_key == "env-key-456"


class TestOpenAPIToolRepresentation:
    """Test string representation and debugging."""
    
    def test_repr(self, support_spec_path):
        """Test string representation."""
        tool = OpenAPITool(spec_path=support_spec_path)
        
        repr_str = repr(tool)
        assert "OpenAPITool" in repr_str
        assert "Support Triage API" in repr_str
        assert "operations=" in repr_str
