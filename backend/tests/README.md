# Backend Testing Guide

## Overview

This directory contains comprehensive tests for the AI Agents backend, including unit tests, integration tests, and end-to-end tests.

**Current Status:**
- ✅ **116 unit tests** passing (mocked, fast)
- ✅ **3 skipped** (external MCP servers)
- 🔄 **Integration tests** folder created, tests pending
- ⏳ **E2E tests** planned for Phase 3

## Test Structure

```
tests/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Shared pytest fixtures
├── README.md                       # This file
├── unit/                           # Unit tests (fast, isolated, mocked)
│   ├── test_agent_registry.py     # 35 tests - Agent registry with Cosmos DB mocking
│   ├── test_base_agent.py         # 26 tests - Base agent functionality
│   ├── test_mcp_tools.py          # 17 tests - MCP tool factories (12 unit + 5 integration)
│   ├── test_openapi_client.py     # 16 tests - OpenAPI client and tools
│   └── test_support_triage_agent.py # 25 tests - Support Triage Agent
└── integration/                    # Integration tests (real external services)
    ├── __init__.py                 # Integration test fixtures
    ├── test_agent_e2e.py          # (PENDING) Real AI calls with Azure OpenAI
    ├── test_cosmos_db.py          # (PENDING) Real Cosmos DB operations
    ├── test_mcp_servers.py        # (PENDING) Comprehensive MCP server tests
    ├── test_openapi_backends.py   # (PENDING) Real OpenAPI backend calls
    └── test_agent_registry_live.py # (PENDING) Registry with real Cosmos DB
```

## Environment Variables for Integration Tests

Integration tests require specific environment variables to connect to real Azure services and APIs. Set these in your local `.env` file or CI/CD environment:

### Azure OpenAI (Required for Agent Integration Tests)
```bash
# Azure OpenAI endpoint and authentication
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
# Or use Azure AD authentication (recommended for production)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Model deployment names
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o  # Default deployment
AZURE_OPENAI_API_VERSION=2024-08-01-preview  # API version
```

### Cosmos DB (Required for Agent Registry Integration Tests)
```bash
# Cosmos DB endpoint and authentication
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key-here
COSMOS_DATABASE=agent-demo  # Database name
COSMOS_CONTAINER=agents  # Container name for agent configurations
```

### OpenAPI Backend Services (Required for Tool Integration Tests)
```bash
# Support Triage API
SUPPORT_API_URL=https://your-support-api.com
SUPPORT_API_KEY=your-support-api-key  # If authentication required

# Azure Ops Assistant API
OPS_API_URL=https://your-ops-api.com
OPS_API_KEY=your-ops-api-key  # If authentication required
```

### MCP Server Configuration (Required for MCP Tool Integration Tests)
```bash
# Microsoft Learn MCP (usually publicly available)
MICROSOFT_LEARN_MCP_URL=https://learn.microsoft.com/api/mcp

# Azure MCP Server (if using custom deployment)
AZURE_MCP_URL=http://localhost:8000

# Adventure Works MCP (if available)
ADVENTURE_WORKS_MCP_URL=http://localhost:8001

# News MCP (custom implementation)
NEWS_MCP_URL=http://localhost:8002
```

### Test Control Flags
```bash
# Enable/disable integration tests globally
USE_REAL_API=true  # Set to "false" to skip all integration tests

# Cost control: Set maximum tokens per test run
MAX_TOKENS_PER_TEST=1000  # Prevents runaway costs

# Timeout settings
INTEGRATION_TEST_TIMEOUT=30  # Seconds before test times out
```

### Setting Up for Local Development

1. **Copy the example env file:**
   ```bash
   cp .env.example .env
   ```

2. **Configure Azure OpenAI** (minimum requirement):
   - Create an Azure OpenAI resource in Azure Portal
   - Deploy GPT-4o model
   - Copy endpoint and API key to `.env`

3. **Optional: Configure other services** (skip for unit tests only):
   - Cosmos DB for agent registry tests
   - OpenAPI backends for tool tests
   - MCP servers for MCP tool tests

4. **Verify configuration:**
   ```bash
   # Test with a single integration test
   pytest tests/integration/test_agent_e2e.py::test_support_triage_basic -v
   ```

### CI/CD Configuration

For GitHub Actions or Azure DevOps, set these as **repository secrets** (not committed to git):

```yaml
# GitHub Actions example
env:
  AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
  AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
  COSMOS_ENDPOINT: ${{ secrets.COSMOS_ENDPOINT }}
  COSMOS_KEY: ${{ secrets.COSMOS_KEY }}
  USE_REAL_API: true  # Only for integration test workflows
```

**Security Note:** Never commit API keys or secrets to git. Always use environment variables or secret management services.

### Quick Start

```bash
cd backend

# Run all unit tests (fast, no external dependencies)
pytest tests/unit/ -v

# Run full test suite (unit + integration)
pytest tests/ -v

# Run with coverage report
pytest tests/unit/ --cov=src --cov-report=html --cov-report=term
```

### Unit Tests (Default)

Unit tests are **fast, isolated, and fully mocked**. They don't call external services.

```bash
# All unit tests (~85 seconds)
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_support_triage_agent.py -v

# Specific test class
pytest tests/unit/test_base_agent.py::TestDemoBaseAgentRun -v

# Specific test function
pytest tests/unit/test_base_agent.py::TestDemoBaseAgentRun::test_run_without_thread -v

# Run with keyword filter
pytest tests/unit/ -v -k "agent"
```

### Integration Tests (Requires Configuration)

Integration tests connect to **real external services** and may incur costs.

```bash
# All integration tests (requires env vars)
pytest tests/integration/ -v -m integration

# Skip integration tests (default for CI/CD)
pytest tests/ -v -m "not integration"

# Run only fast integration tests (MCP, OpenAPI - no AI)
pytest tests/integration/ -v -m "integration and not slow"

# Run AI integration tests (requires Azure OpenAI, incurs costs)
pytest tests/integration/ -v -m "integration and slow"

# Run specific integration test file
pytest tests/integration/test_cosmos_db.py -v
```

### Test Selection by Marker

```bash
# Only unit tests
pytest tests/ -v -m unit

# Only integration tests
pytest tests/ -v -m integration

# Exclude slow tests (AI calls)
pytest tests/ -v -m "not slow"

# Only slow tests
pytest tests/ -v -m slow
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/unit/ -v -n 4
```

### Coverage Analysis

```bash
# Generate HTML coverage report
pytest tests/unit/ --cov=src --cov-report=html

# View coverage in terminal
pytest tests/unit/ --cov=src --cov-report=term-missing

# Coverage with minimum threshold
pytest tests/unit/ --cov=src --cov-fail-under=80
```

## Test Markers

We use pytest markers to categorize and filter tests:

### Standard Markers

- `@pytest.mark.unit` - Fast unit tests with mocks (default, no external dependencies)
- `@pytest.mark.integration` - Tests requiring external services (MCP, APIs, databases)
- `@pytest.mark.slow` - Tests taking >5 seconds (typically AI calls with Azure OpenAI)
- `@pytest.mark.asyncio` - Async tests requiring event loop

### Custom Skip Conditions

```python
@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_ENDPOINT"),
    reason="Azure OpenAI not configured"
)
```

### Example Usage

```python
import pytest

@pytest.mark.unit
def test_agent_creation():
    """Fast unit test with mocking."""
    agent = SupportTriageAgent.create()
    assert agent is not None

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_ENDPOINT"),
    reason="Azure OpenAI credentials required"
)
async def test_real_agent_query():
    """Integration test with real Azure OpenAI API."""
    agent = SupportTriageAgent.create()
    response = await agent.run("Test query")
    assert len(response.messages) > 0
```

## Current Test Coverage

### Phase 2.4: Agent Registry ✅
**Files:** `src/agents/registry.py`  
**Tests:** `tests/unit/test_agent_registry.py` (35 tests)

- ✅ Agent registry initialization and configuration
- ✅ Cosmos DB client lazy initialization (mocked)
- ✅ Agent retrieval (cache hits, cache misses, not found)
- ✅ Agent listing from Cosmos DB
- ✅ Agent reloading and cache invalidation
- ✅ Cache management
- ✅ Agent creation from configuration
- ✅ Tool creation (MCP + OpenAPI)
- ✅ Error handling and validation
- ✅ Cleanup and resource management
- ✅ Integration workflows

### Phase 2.4: Base Agent ✅
**Files:** `src/agents/base.py`  
**Tests:** `tests/unit/test_base_agent.py` (26 tests)

- ✅ Agent initialization with Azure OpenAI
- ✅ Thread management (create, serialize, deserialize)
- ✅ Sliding window memory management
- ✅ Run methods (sync with mocked responses)
- ✅ Streaming methods (async generators)
- ✅ Tool management
- ✅ Full conversation workflows
- ✅ Thread persistence

### Phase 2.5: Support Triage Agent ✅
**Files:** `src/agents/support_triage.py`  
**Tests:** `tests/unit/test_support_triage_agent.py` (25 tests)

- ✅ Agent creation with factory pattern
- ✅ Custom configuration (model, temperature, max_messages)
- ✅ Tool initialization (Microsoft Learn MCP + Support Triage OpenAPI)
- ✅ System prompt validation
- ✅ Thread management delegation
- ✅ Run and streaming methods
- ✅ Error handling
- ✅ Full conversation flow
- ✅ Thread persistence workflow

### Phase 2.1-2.3: Tools ✅
**Files:** `src/tools/mcp_tools.py`, `src/tools/openapi_client.py`  
**Tests:** `tests/unit/test_mcp_tools.py` (17 tests), `tests/unit/test_openapi_client.py` (16 tests)

**MCP Tools (12 unit + 5 integration):**
- ✅ Microsoft Learn tool factory
- ✅ Azure MCP tool factory
- ✅ Adventure Works tool factory
- ✅ News tool factory
- ✅ Factory pattern tests
- ✅ Context manager protocol
- ✅ Microsoft Learn MCP live connection (integration)
- ⊘ Azure MCP (skipped - not configured)
- ⊘ Adventure Works (skipped - not available)
- ⊘ News MCP (skipped - placeholder)

**OpenAPI Tools (16 unit):**
- ✅ Spec loading and parsing
- ✅ Operation discovery
- ✅ URL building with path parameters
- ✅ Query parameter handling
- ✅ Request body handling
- ✅ Factory functions (Support Triage, Ops Assistant)
- ✅ Environment variable configuration
- ✅ String representation

### Coverage Summary
```
Total: 116 tests
✅ Passing: 116
⊘ Skipped: 3 (external MCP servers not available)
❌ Failed: 0
⏱️ Time: ~85 seconds
```

## Test Configuration

Configuration is managed in `pytest.ini`:

```ini
[pytest]
markers =
    integration: Integration tests requiring external services
    unit: Unit tests that run in isolation
    slow: Tests that take a long time
    
asyncio_mode = auto
```

## Environment Variables for Tests

Tests use environment variables for configuration:

- `LEARN_MCP_URL` - Microsoft Learn MCP server URL
- `LEARN_API_KEY` - Microsoft Learn API key (if required)
- `AZURE_MCP_URL` - Azure MCP server URL
- `AZURE_SUBSCRIPTION_ID` - Azure subscription for testing
- `NEWS_MCP_URL` - News MCP server URL
- `NEWS_API_KEY` - News API key

Set these in `.env` file or export them before running tests.

## Cost Analysis for Integration Tests

Integration tests that call Azure OpenAI APIs incur real costs. Understanding the cost structure helps you balance thorough testing with budget constraints.

### Azure OpenAI Pricing (GPT-4o - as of 2025)

**Input Tokens:** ~$2.50 per 1M tokens  
**Output Tokens:** ~$10.00 per 1M tokens

Typical test conversation:
- System prompt: ~200 tokens
- User message: ~50 tokens
- Assistant response: ~150 tokens
- Tool calls: ~100 tokens (per call)
- **Total per test:** ~500-1000 tokens

### Estimated Costs per Test Run

#### Single Agent E2E Test (1 conversation)
- Tokens: ~1,000 tokens (500 input, 500 output)
- Cost: ~$0.0025 input + $0.005 output = **$0.0075 per test**

#### Full Agent Test Suite (5 conversations per agent)
- Tokens: ~5,000 tokens per agent
- Cost: **$0.0375 per agent**
- All 5 agents (Phases 2.4-2.8): **$0.19 per full run**

#### MCP Tool Integration Tests (10 queries)
- Tokens: ~2,000 tokens (documentation searches)
- Cost: **$0.015 per tool test**

#### OpenAPI Backend Tests (20 API calls)
- Tokens: Minimal (mostly HTTP, not AI)
- Cost: **$0.001 per backend test**

#### Full Integration Test Suite
```
Agent E2E tests:         $0.19
MCP tool tests:          $0.06
OpenAPI backend tests:   $0.02
Cosmos DB tests:         $0.00 (no AI calls)
-------------------------
Total per full run:      ~$0.27
```

### Monthly Cost Estimates

| Scenario | Runs per Month | Monthly Cost |
|----------|----------------|--------------|
| Developer (local) | 10 full runs | **$2.70** |
| CI/CD (PR validation) | 100 test runs | **$27.00** |
| CI/CD (nightly full) | 30 full runs | **$8.10** |
| Combined (typical) | — | **$35-50/month** |

### Cost Optimization Strategies

#### 1. Use Smaller Models for Non-Critical Tests
```python
# Use GPT-4o-mini for basic validation ($0.15 per 1M input tokens)
@pytest.mark.integration
async def test_agent_basic_response():
    agent = SupportTriageAgent.create(
        model="gpt-4o-mini",  # 10x cheaper than GPT-4o
        temperature=0.7
    )
```

#### 2. Mock Expensive Operations
```python
# Mock tool calls after first integration test validates them
@pytest.mark.integration
async def test_agent_with_mocked_tools(mocker):
    # Real AI call
    agent = SupportTriageAgent.create()
    
    # But mock expensive tool operations
    mocker.patch("src.tools.mcp_tools.get_microsoft_learn_tool", return_value=mock_tool)
```

#### 3. Use Cached Responses for Repeated Tests
```python
# Cache common queries to avoid re-running identical tests
@pytest.fixture(scope="session")
def cached_agent_response():
    """Run once per test session, reuse result."""
    return run_expensive_query()
```

#### 4. Limit Token Generation
```python
# Set max_tokens to prevent runaway generation
agent.run(
    message="Test query",
    max_tokens=100,  # Limit response length
    temperature=0    # Deterministic for testing
)
```

#### 5. Run Integration Tests Selectively
```bash
# Only run integration tests before releases, not on every commit
pytest tests/unit/ -v  # Fast, free, always run

# Weekly full integration test
pytest tests/ -v --run-integration  # Slow, costly, scheduled
```

#### 6. Use Test Markers to Control Execution
```python
# Mark expensive tests explicitly
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.expensive  # Custom marker for high-cost tests
async def test_complex_multi_turn_conversation():
    # This test costs ~$0.05, only run when necessary
    pass
```

Run only cheap tests:
```bash
pytest tests/integration/ -v -m "not expensive"
```

### Budget Alerting

Consider setting up Azure budget alerts:

1. **Azure Portal** → **Cost Management** → **Budgets**
2. Create budget: $50/month for OpenAI testing
3. Set alerts at 50%, 80%, 100%
4. Review monthly spend in Cost Analysis

### Best Practices Summary

✅ **Always run unit tests** (free, fast, comprehensive)  
✅ **Run integration tests** before major releases  
✅ **Use smaller models** for basic validation  
✅ **Mock external services** after initial validation  
✅ **Cache common responses** to avoid duplicate API calls  
✅ **Set token limits** to prevent runaway costs  
✅ **Monitor spend** with Azure cost management  
✅ **Document expensive tests** with `@pytest.mark.expensive`

With these strategies, you can maintain **comprehensive integration testing** while keeping costs under **$20-30/month** for typical development workflows.

## Continuous Integration

In CI/CD pipelines:

1. **Unit tests**: Always run (fast, no dependencies)
2. **Integration tests**: Run when MCP servers are available
3. **Coverage threshold**: Maintain > 80% coverage for new code

## Integration Test Recommendations

The integration test infrastructure is now in place. Here are recommended test cases to implement:

### Phase 2.5: Support Triage Agent Integration Tests

**File:** `tests/integration/test_support_triage_e2e.py`

```python
@pytest.mark.integration
@pytest.mark.slow
async def test_support_triage_basic_query(azure_openai_available, use_real_api):
    """E2E: Support Triage Agent handles basic product question."""
    # Query: "How do I reset my password in Azure AD?"
    # Expected: Uses Microsoft Learn tool, provides step-by-step answer
    # Cost: ~$0.01

@pytest.mark.integration
@pytest.mark.slow
async def test_support_triage_historical_tickets(support_api_available, use_real_api):
    """E2E: Support Triage Agent searches historical tickets."""
    # Query: "Show me similar tickets for Exchange connectivity issues"
    # Expected: Calls Support Triage OpenAPI, returns relevant tickets
    # Cost: ~$0.01

@pytest.mark.integration
@pytest.mark.expensive
async def test_support_triage_multi_turn_conversation(azure_openai_available, use_real_api):
    """E2E: Support Triage Agent handles multi-turn conversation with thread persistence."""
    # Query 1: "I'm having issues with Teams calling"
    # Query 2: "What about audio quality specifically?"
    # Query 3: "Can you show me related tickets?"
    # Expected: Maintains context, uses both tools appropriately
    # Cost: ~$0.03
```

### Phase 2.6: Azure Ops Assistant Integration Tests

**File:** `tests/integration/test_azure_ops_e2e.py`

```python
@pytest.mark.integration
@pytest.mark.slow
async def test_azure_ops_list_resources(azure_openai_available, use_real_api):
    """E2E: Azure Ops Assistant lists Azure resources using Azure MCP."""
    # Query: "List all virtual machines in my subscription"
    # Expected: Calls Azure MCP tool, returns VM list
    # Cost: ~$0.01

@pytest.mark.integration
@pytest.mark.slow
async def test_azure_ops_troubleshooting(ops_api_available, use_real_api):
    """E2E: Azure Ops Assistant troubleshoots deployment failure."""
    # Query: "Why did my last deployment fail?"
    # Expected: Calls Ops Assistant OpenAPI for logs, provides diagnosis
    # Cost: ~$0.01
```

### Phase 2.7: Agent Registry Integration Tests

**File:** `tests/integration/test_agent_registry_cosmos.py`

```python
@pytest.mark.integration
async def test_registry_cosmos_db_connection(cosmos_db_available):
    """Integration: Verify Agent Registry connects to real Cosmos DB."""
    # Test: Initialize registry, list agents from Cosmos
    # Expected: No errors, returns agent configurations
    # Cost: $0 (Cosmos DB RU consumption only)

@pytest.mark.integration
async def test_registry_agent_loading_from_cosmos(cosmos_db_available, azure_openai_available):
    """Integration: Load and instantiate agent from Cosmos DB configuration."""
    # Test: Load Support Triage Agent config from DB, create agent instance
    # Expected: Agent created successfully with correct tools
    # Cost: ~$0 (no AI calls)
```

### MCP Tool Integration Tests

**File:** `tests/integration/test_mcp_servers.py`

```python
@pytest.mark.integration
async def test_microsoft_learn_mcp_comprehensive():
    """Integration: Comprehensive test of Microsoft Learn MCP server."""
    # Test all operations: list-tools, search documentation, retrieve articles
    # Expected: All operations succeed with meaningful results
    # Cost: $0 (MCP server, no AI)

@pytest.mark.integration
async def test_azure_mcp_list_resources():
    """Integration: Azure MCP lists subscription resources."""
    # Test: Connect to Azure MCP, list resources
    # Expected: Returns actual Azure resources from subscription
    # Cost: $0 (MCP server, no AI)
```

### OpenAPI Backend Integration Tests

**File:** `tests/integration/test_openapi_backends.py`

```python
@pytest.mark.integration
async def test_support_api_search_tickets(support_api_available):
    """Integration: Support Triage API searches tickets."""
    # Test: Search for tickets by keyword
    # Expected: Returns JSON array of tickets
    # Cost: $0 (HTTP API, no AI)

@pytest.mark.integration
async def test_ops_api_get_deployment_logs(ops_api_available):
    """Integration: Ops Assistant API retrieves deployment logs."""
    # Test: Get logs for recent deployment
    # Expected: Returns log entries in JSON format
    # Cost: $0 (HTTP API, no AI)
```

### Recommended Implementation Order

1. **Start with MCP tests** (no AI costs, validates connectivity)
   - `test_mcp_servers.py` - Microsoft Learn, Azure MCP
   
2. **Add OpenAPI backend tests** (no AI costs, validates APIs)
   - `test_openapi_backends.py` - Support API, Ops API

3. **Add Cosmos DB tests** (minimal costs, validates storage)
   - `test_agent_registry_cosmos.py` - Agent loading

4. **Add basic agent E2E tests** (low cost, validates core functionality)
   - `test_support_triage_e2e.py::test_support_triage_basic_query`
   - `test_azure_ops_e2e.py::test_azure_ops_list_resources`

5. **Add expensive multi-turn tests** (higher cost, comprehensive validation)
   - `test_support_triage_e2e.py::test_support_triage_multi_turn_conversation`
   - Only run before releases or manually

### CI/CD Strategy

**Pull Request Validation:**
```bash
# Fast unit tests only
pytest tests/unit/ -v
```

**Nightly Build:**
```bash
# Unit tests + cheap integration tests
pytest tests/ -v -m "unit or (integration and not expensive)"
```

**Release Validation:**
```bash
# Full test suite including expensive integration tests
pytest tests/ -v
```

This strategy keeps development fast and free while ensuring comprehensive testing before production releases.

## Future Test Plans

- [x] Integration test infrastructure (fixtures, markers, documentation)
- [ ] Implement recommended integration tests (see above)
- [ ] Add performance/load tests for agent throughput
- [ ] Add chaos/resilience tests (network failures, timeouts)
- [ ] Add security tests (input validation, injection attacks)
- [ ] Add A2A protocol integration tests (Phase 3)
- [ ] Add observability tests (logging, tracing, metrics)
- [ ] Automated cost reporting for integration test runs

## Troubleshooting

### Tests are slow

**Problem:** Test suite takes too long to run during development.

**Solutions:**
```bash
# Skip integration tests (fastest)
pytest tests/ -v -m "not integration"

# Skip slow tests (AI calls)
pytest tests/ -v -m "not slow"

# Run specific test file
pytest tests/unit/test_support_triage_agent.py -v

# Run specific test
pytest tests/unit/test_support_triage_agent.py::test_agent_creation -v

# Run in parallel (requires pytest-xdist)
pytest tests/unit/ -v -n 4
```

**Expected times:**
- Unit tests: ~85 seconds for 116 tests
- Integration tests: ~5-10 minutes (depends on network and API response times)

### Integration tests failing

**Problem:** Integration tests fail with connection errors or timeouts.

**Checklist:**
1. ✅ Check environment variables are set (see "Environment Variables" section)
2. ✅ Verify services are running:
   - Azure OpenAI endpoint is accessible
   - MCP servers are running (if testing locally)
   - OpenAPI backends are deployed
   - Cosmos DB is accessible
3. ✅ Check network connectivity (firewall, VPN, proxy)
4. ✅ Verify API keys are valid and not expired
5. ✅ Check service quotas and rate limits (Azure OpenAI TPM)
6. ✅ Review service logs for errors

**Common errors:**

```bash
# Error: "Azure OpenAI endpoint not configured"
# Solution: Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your-key-here

# Error: "Connection refused" for MCP servers
# Solution: Start MCP servers locally or use remote URLs
python -m src.mcp_servers.microsoft_learn  # Example

# Error: "Rate limit exceeded"
# Solution: Wait 60 seconds or increase rate limit in Azure Portal
pytest tests/integration/ -v --tb=short  # See full error details
```

### Import errors

**Problem:** Tests fail with `ModuleNotFoundError` or import errors.

**Solutions:**
```bash
# Ensure you're in the backend directory
cd backend/

# Verify PYTHONPATH includes backend directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install all dependencies
pip install -r requirements.txt

# Install in editable mode (recommended)
pip install -e .

# Verify pytest can find your modules
pytest --collect-only tests/unit/
```

**Common import issues:**

```python
# ❌ Wrong: Absolute import from workspace root
from backend.src.agents.base import DemoBaseAgent

# ✅ Correct: Relative import from backend/
from src.agents.base import DemoBaseAgent

# ❌ Wrong: Running tests from workspace root
cd /path/to/agent-demo/
pytest backend/tests/unit/

# ✅ Correct: Running tests from backend/
cd /path/to/agent-demo/backend/
pytest tests/unit/
```

### Azure OpenAI authentication errors

**Problem:** Tests fail with "Unauthorized" or "Invalid credentials".

**Solutions:**

1. **Verify API key is correct:**
   ```bash
   # Test with curl
   curl https://your-resource.openai.azure.com/openai/deployments?api-version=2024-08-01-preview \
     -H "api-key: YOUR_API_KEY"
   ```

2. **Check API version:**
   ```python
   # In .env or environment
   AZURE_OPENAI_API_VERSION=2024-08-01-preview  # Must match deployment
   ```

3. **Verify deployment name:**
   ```python
   # Deployment name must exist in your Azure OpenAI resource
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o  # Check Azure Portal
   ```

4. **Use Azure AD authentication (recommended):**
   ```bash
   # Instead of API key, use managed identity or service principal
   export AZURE_TENANT_ID=your-tenant-id
   export AZURE_CLIENT_ID=your-client-id
   export AZURE_CLIENT_SECRET=your-client-secret
   # Remove or unset AZURE_OPENAI_API_KEY
   ```

### Cosmos DB connection errors

**Problem:** Agent Registry tests fail to connect to Cosmos DB.

**Solutions:**

1. **Verify connection string:**
   ```bash
   # Check endpoint and key are correct
   export COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
   export COSMOS_KEY=your-primary-key-here
   ```

2. **Check database and container exist:**
   ```bash
   # In Azure Portal: Cosmos DB → Data Explorer
   # Verify database: "agent-demo"
   # Verify container: "agents"
   ```

3. **Verify firewall rules:**
   ```bash
   # In Azure Portal: Cosmos DB → Networking
   # Add your IP address or enable "Accept connections from Azure datacenters"
   ```

4. **Test connection manually:**
   ```python
   from azure.cosmos import CosmosClient
   
   client = CosmosClient(
       os.getenv("COSMOS_ENDPOINT"),
       credential=os.getenv("COSMOS_KEY")
   )
   database = client.get_database_client("agent-demo")
   container = database.get_container_client("agents")
   print(f"Connected to container: {container.id}")
   ```

### Mock objects not working

**Problem:** Unit tests fail because mocks aren't behaving as expected.

**Solutions:**

1. **Check mock path is correct:**
   ```python
   # ❌ Wrong: Mocking at import site
   mocker.patch("test_support_triage_agent.get_microsoft_learn_tool")
   
   # ✅ Correct: Mocking at definition site
   mocker.patch("src.tools.mcp_tools.get_microsoft_learn_tool")
   ```

2. **Use correct mock type for async:**
   ```python
   # ❌ Wrong: Regular Mock for async function
   mock_tool = Mock(return_value=some_value)
   
   # ✅ Correct: AsyncMock for async function
   mock_tool = AsyncMock(return_value=some_value)
   ```

3. **Set return values properly:**
   ```python
   # For async context manager (__aenter__)
   mock_tool.__aenter__.return_value = mock_client
   
   # For async method calls
   mock_client.run.return_value = mock_response
   ```

4. **Verify mock was called:**
   ```python
   # Check if mock was called with expected arguments
   mock_tool.assert_called_once_with(
       model="gpt-4o",
       temperature=0.7
   )
   
   # Or check any call
   assert mock_tool.called
   assert mock_tool.call_count == 2
   ```

### Test discovery issues

**Problem:** pytest doesn't find your tests.

**Solutions:**

```bash
# Check pytest configuration
pytest --collect-only tests/

# Verify test file naming
# ✅ Correct: test_*.py or *_test.py
# ❌ Wrong: my_tests.py

# Verify test function naming
# ✅ Correct: def test_something():
# ❌ Wrong: def check_something():

# Check pytest.ini configuration
cat pytest.ini
```

### Coverage reports empty

**Problem:** Coverage report shows 0% coverage or missing files.

**Solutions:**

```bash
# Specify source directory explicitly
pytest tests/unit/ --cov=src --cov-report=term-missing

# Check .coveragerc configuration
cat .coveragerc

# Ensure source files are imported
# Coverage only tracks files that are imported by tests

# Run with verbose coverage
pytest tests/unit/ --cov=src --cov-report=term --cov-report=html -v
```

### Need help?

**Check test output carefully:**
```bash
# Verbose output with full error traces
pytest tests/ -vv --tb=long

# Show all print statements
pytest tests/ -v -s

# Stop at first failure
pytest tests/ -v -x

# Show locals in traceback
pytest tests/ -v --tb=long --showlocals
```

**Review test documentation:**
- This README for test structure and best practices
- Test file docstrings for specific test purpose
- Fixture definitions in `tests/integration/__init__.py`

**Contact the team:**
- Open GitHub issue with full error output
- Include pytest version: `pytest --version`
- Include Python version: `python --version`
- Include environment: "local dev" or "CI/CD"

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [Agent Framework testing guide](https://learn.microsoft.com/en-us/azure/ai-foundry/testing)
