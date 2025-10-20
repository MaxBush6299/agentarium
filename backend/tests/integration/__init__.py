"""
Integration Tests for AI Agents Demo

Integration tests verify end-to-end functionality with real external services.
These tests are slower and may incur costs (Azure OpenAI API calls).

Test Categories:
1. Agent E2E - Full agent workflows with real AI responses
2. MCP Integration - Connections to MCP servers
3. OpenAPI Integration - Calls to OpenAPI backend services
4. Cosmos DB - Real database operations
5. Agent Registry - Loading agents from Cosmos DB
6. A2A Protocol - Agent-to-agent communication

Running Integration Tests:
--------------------------

Run all integration tests:
    pytest tests/integration/ -m integration -v

Run only fast integration tests (MCP, OpenAPI, Cosmos):
    pytest tests/integration/ -m integration -v -k "not slow"

Run AI tests (requires Azure OpenAI credentials):
    pytest tests/integration/ -m "integration and slow" -v

Run specific test file:
    pytest tests/integration/test_agent_e2e.py -v

Skip integration tests (default for CI/CD):
    pytest tests/ -m "not integration"

Environment Variables Required:
-------------------------------

For AI Tests (Agent E2E):
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_DEPLOYMENT (or model name)
- AZURE_CLIENT_ID (for Managed Identity, or API key)

For MCP Tests:
- MICROSOFT_LEARN_MCP_URL (optional, has default)
- AZURE_MCP_URL (for Azure MCP sidecar)
- ADVENTURE_WORKS_PATH (path to MCP server script)

For OpenAPI Tests:
- SUPPORT_API_URL
- SUPPORT_API_KEY
- OPS_API_URL
- OPS_API_KEY

For Cosmos DB Tests:
- COSMOS_ENDPOINT
- COSMOS_DATABASE
- COSMOS_CONTAINER
- AZURE_CLIENT_ID (for Managed Identity)

Test Markers:
-------------

@pytest.mark.integration - All integration tests
@pytest.mark.slow - Tests that take >5 seconds (AI calls)
@pytest.mark.skipif - Conditional skip based on environment

Cost Considerations:
-------------------

Azure OpenAI API costs (rough estimates):
- GPT-4o: ~$0.005-0.015 per test (depending on tokens)
- Full E2E test suite: ~$0.50-2.00 per run
- Recommendation: Run locally before commit, not on every CI/CD run

Tips:
-----

1. Use smaller models for integration tests (gpt-3.5-turbo) to reduce costs
2. Mock expensive operations when possible
3. Use test fixtures to reuse agent instances
4. Clean up test data in Cosmos DB after tests
5. Set shorter timeouts for integration tests (30s max)
"""

import os
import pytest


@pytest.fixture(scope="session")
def azure_openai_available():
    """Check if Azure OpenAI credentials are configured."""
    return bool(
        os.getenv("AZURE_OPENAI_ENDPOINT") and
        (os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_CLIENT_ID"))
    )


@pytest.fixture(scope="session")
def cosmos_db_available():
    """Check if Cosmos DB credentials are configured."""
    return bool(
        os.getenv("COSMOS_ENDPOINT") and
        os.getenv("COSMOS_DATABASE")
    )


@pytest.fixture(scope="session")
def support_api_available():
    """Check if Support Triage API is available."""
    return bool(os.getenv("SUPPORT_API_URL"))


@pytest.fixture(scope="session")
def ops_api_available():
    """Check if Ops Assistant API is available."""
    return bool(os.getenv("OPS_API_URL"))


@pytest.fixture(scope="session")
def use_real_api():
    """Determine if tests should use real API calls."""
    return os.getenv("USE_REAL_API", "false").lower() == "true"
