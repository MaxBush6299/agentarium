"""
Pytest configuration and shared fixtures for backend tests.
"""
import os
import sys
import pytest
from typing import AsyncGenerator
from pathlib import Path
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

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


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def azure_openai_available():
    """
    Check if Azure OpenAI is configured and available for integration tests.
    
    Returns True if AZURE_OPENAI_ENDPOINT is set, False otherwise.
    
    Usage:
        @pytest.mark.skipif(not azure_openai_available, reason="Azure OpenAI not configured")
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_KEY")
    return bool(endpoint and key)


@pytest.fixture(scope="session")
def cosmos_db_available():
    """
    Check if Cosmos DB is configured and available for integration tests.
    
    Returns True if COSMOS_ENDPOINT and COSMOS_DATABASE are set.
    """
    endpoint = os.getenv("COSMOS_ENDPOINT")
    database = os.getenv("COSMOS_DATABASE_NAME")
    return bool(endpoint and database)


@pytest.fixture(scope="session")
def support_api_available():
    """
    Check if Support API backend is configured and available.
    
    Returns True if SUPPORT_API_URL is set.
    """
    return bool(os.getenv("SUPPORT_API_URL"))


@pytest.fixture(scope="session")
def ops_api_available():
    """
    Check if Ops API backend is configured and available.
    
    Returns True if OPS_API_URL is set.
    """
    return bool(os.getenv("OPS_API_URL"))


@pytest.fixture(scope="session")
def use_real_api():
    """
    Check if integration tests should use real APIs or be skipped.
    
    Returns True if USE_REAL_API environment variable is set to "true".
    Set to false in CI/CD to avoid costs, true for manual validation.
    """
    return os.getenv("USE_REAL_API", "true").lower() == "true"


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP test client for FastAPI app.
    
    Provides an AsyncClient configured with ASGITransport for testing
    the FastAPI application endpoints, including A2A protocol endpoints.
    """
    from src.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
