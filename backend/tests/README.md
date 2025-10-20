# Backend Testing Guide

## Overview

This directory contains comprehensive tests for the AI Agents backend, including unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared pytest fixtures
├── unit/                       # Unit tests (fast, isolated)
│   └── test_mcp_tools.py      # MCP tool factory tests
├── integration/                # Integration tests (require external services)
│   └── (future tests)
└── e2e/                        # End-to-end tests
    └── (future tests)
```

## Running Tests

### Run All Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run Only Unit Tests (Fast)
```bash
python -m pytest tests/ -v -m "not integration"
```

### Run Only Integration Tests
```bash
python -m pytest tests/ -v -m integration
```

### Run Specific Test File
```bash
python -m pytest tests/unit/test_mcp_tools.py -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Markers

We use pytest markers to categorize tests:

- `@pytest.mark.integration` - Tests that require external services (MCP servers, databases, APIs)
- `@pytest.mark.unit` - Unit tests that run in isolation with mocks (default)
- `@pytest.mark.slow` - Tests that take a long time to run

## MCP Tool Tests

### Current Status (as of October 20, 2025)

**Unit Tests (12/12 passing):**
- ✅ Microsoft Learn tool instantiation and configuration
- ✅ Azure MCP tool instantiation and configuration
- ✅ Adventure Works tool instantiation and configuration
- ✅ News tool instantiation and configuration
- ✅ Factory pattern tests for all tools

**Integration Tests (2/5 passing, 3 skipped):**
- ✅ **Microsoft Learn MCP** - Successfully connected to live server
- ⊘ Azure MCP - Skipped (server not configured/running)
- ⊘ Adventure Works MCP - Skipped (server not available)
- ⊘ News MCP - Skipped (placeholder URL)
- ✅ **Smoke test** - At least one MCP server connected

### Test Philosophy

1. **Unit Tests**: Verify tool creation, configuration, and interfaces
   - Fast execution (< 1 second per test)
   - No external dependencies
   - Can run in CI/CD pipeline without setup

2. **Integration Tests**: Verify actual connectivity to MCP servers
   - Test real network connections
   - Verify MCP protocol handshake
   - Gracefully skip if servers unavailable
   - Run these before deploying new agents

### Adding New MCP Tools

When adding a new MCP tool, follow this pattern:

1. **Create the factory function** in `backend/tools/mcp_tools.py`
2. **Add unit tests** to verify instantiation
3. **Add integration test** to verify connectivity
4. **Document expected behavior** in test docstrings

Example:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_new_mcp_connection():
    """
    Integration test: Verify New MCP server is reachable.
    """
    tool = get_new_mcp_tool()
    
    try:
        async with tool as mcp:
            assert mcp is not None
            print(f"✓ Successfully connected to New MCP")
    except Exception as e:
        pytest.skip(f"New MCP server not available: {e}")
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

## Continuous Integration

In CI/CD pipelines:

1. **Unit tests**: Always run (fast, no dependencies)
2. **Integration tests**: Run when MCP servers are available
3. **Coverage threshold**: Maintain > 80% coverage for new code

## Future Test Plans

- [ ] Add integration tests for agent implementations
- [ ] Add E2E tests for chat workflows
- [ ] Add performance/load tests for MCP connections
- [ ] Add tests for A2A protocol
- [ ] Add tests for Cosmos DB persistence layer
- [ ] Add tests for authentication/authorization

## Troubleshooting

### Tests are slow
- Use `-m "not integration"` to skip integration tests
- Run specific test files instead of entire suite

### Integration tests failing
- Check if MCP servers are running
- Verify environment variables are set
- Check network connectivity
- Review server logs for errors

### Import errors
- Ensure you're running from `backend/` directory
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python path includes `backend/` directory

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [Agent Framework testing guide](https://learn.microsoft.com/en-us/azure/ai-foundry/testing)
