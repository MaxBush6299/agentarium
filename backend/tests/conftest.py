"""
Pytest configuration and shared fixtures for backend tests.
"""
import os
import sys
import pytest
from typing import AsyncGenerator
from pathlib import Path

# Add src directory to path for all tests
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    # Set test mode
    os.environ["TESTING"] = "true"
    os.environ["LOCAL_DEV_MODE"] = "true"
    
    # Mock Azure resources for testing
    os.environ["AZURE_TENANT_ID"] = "test-tenant-id"
    os.environ["AZURE_CLIENT_ID"] = "test-client-id"
    os.environ["KEY_VAULT_URI"] = "https://test-kv.vault.azure.net/"
    os.environ["COSMOS_DB_ENDPOINT"] = "https://test-cosmos.documents.azure.com:443/"
    
    yield
    
    # Cleanup
    os.environ.pop("TESTING", None)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for tests."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOCAL_DEV_MODE", "true")
    return monkeypatch


@pytest.fixture
def sample_microsoft_learn_response():
    """Sample response from Microsoft Learn MCP server."""
    return {
        "tools": [
            {
                "name": "search_docs",
                "description": "Search Microsoft Learn documentation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    }
                }
            }
        ]
    }


@pytest.fixture
def sample_azure_mcp_response():
    """Sample response from Azure MCP server."""
    return {
        "tools": [
            {
                "name": "list_resources",
                "description": "List Azure resources",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_group": {"type": "string"}
                    }
                }
            }
        ]
    }
