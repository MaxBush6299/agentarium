# Agent Framework Backend

FastAPI backend for the AI Agent Framework Demo. Provides REST API endpoints for agent management, chat sessions, and tool integration.

## Project Structure

```
backend/
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration and environment variables
│   ├── agents/                 # Agent implementations (Phase 2)
│   ├── tools/                  # Tool integrations (MCP, OpenAPI, etc.)
│   ├── a2a/                    # Agent-to-Agent protocol implementation
│   ├── api/                    # FastAPI routes
│   │   ├── auth.py             # Entra ID authentication
│   │   ├── chat.py             # Chat endpoints (Phase 2)
│   │   ├── agents.py           # Agent management (Phase 2)
│   │   └── health.py           # Health check endpoint
│   ├── persistence/            # Data access layer
│   │   ├── cosmos_client.py    # Cosmos DB client
│   │   └── models.py           # Pydantic models (Phase 2)
│   ├── observability/          # Telemetry and tracing
│   ├── utils/
│   │   ├── secrets.py          # Key Vault integration
│   │   └── pii_redaction.py    # PII scrubbing (Phase 4)
├── tests/                      # Test suite
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image
└── README.md                   # This file
```

## Prerequisites

- Python 3.11+
- Azure subscription (for cloud resources)
- Azure CLI (for local authentication)
- Cosmos DB emulator (optional, for local development)

## Local Development Setup

### 1. Clone the repository

```bash
cd path/to/agent-demo
```

### 2. Create virtual environment

```bash
# Using venv
python -m venv venv
venv\Scripts\activate

# Or using conda
conda create -n agent-backend python=3.11
conda activate agent-backend
```

### 3. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure environment

Create a `.env.local` file from the template:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your Azure configuration:

```env
# Local development settings
ENVIRONMENT=development
LOCAL_DEV_MODE=true

# Azure Configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id

# Cosmos DB (use emulator for local dev)
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QB0c/Db2xCLFJxXvdGP3MqFH3w==

# Key Vault URL (can be empty for local dev)
KEYVAULT_URL=

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### 5. (Optional) Start Cosmos DB Emulator

For local testing without Azure resources:

```bash
# Install and start Cosmos DB emulator from:
# https://learn.microsoft.com/azure/cosmos-db/local-emulator

# Verify emulator is running
curl https://localhost:8081/_explorer/index.html
```

### 6. Run the backend

```bash
# Development mode (with auto-reload)
uvicorn src.main:app --reload

# Or using Python
python -m uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`
- API docs (Swagger): `http://localhost:8000/docs`
- Alternative docs (ReDoc): `http://localhost:8000/redoc`

## Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_config.py
```

## API Endpoints

### Current (Phase 1.2 Scaffolding)

- `GET /` - Root endpoint
- `GET /health` - Health check (Cosmos DB status)
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

### Upcoming (Phase 2+)

- `POST /api/agents/{agent_id}/chat` - Chat with agent (SSE streaming)
- `GET /api/agents` - List agents
- `POST /api/agents` - Create agent
- `PUT /api/agents/{agent_id}` - Update agent
- `DELETE /api/agents/{agent_id}` - Delete agent
- `GET /api/agents/{agent_id}/threads` - Get chat threads
- And more...

## Configuration Reference

### Environment Variables

**Application**
- `ENVIRONMENT` - `development`, `staging`, or `production`
- `LOCAL_DEV_MODE` - Boolean, enables local development mode
- `LOG_LEVEL` - `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Azure**
- `AZURE_SUBSCRIPTION_ID` - Azure subscription ID
- `AZURE_TENANT_ID` - Entra ID tenant ID
- `AZURE_REGION` - Azure region (default: `eastus`)

**Cosmos DB**
- `COSMOS_ENDPOINT` - Cosmos DB endpoint URL
- `COSMOS_DATABASE_NAME` - Database name (default: `agents-db`)
- `COSMOS_KEY` - Primary key (for key auth)
- `COSMOS_CONNECTION_STRING` - Connection string (alternative)

**Key Vault**
- `KEYVAULT_URL` - Key Vault URL (optional, for production)

**Authentication**
- `ENTRA_ID_CLIENT_ID` - Entra ID app client ID
- `ENTRA_ID_CLIENT_SECRET` - Client secret (if needed)
- `API_SCOPE` - API scope for token validation

**Models**
- `DEFAULT_MODEL` - Default LLM model (default: `gpt-4`)
- `DEFAULT_TEMPERATURE` - Temperature for responses (default: `0.7`)
- `DEFAULT_MAX_TOKENS` - Max tokens per response (default: `2048`)

**Cost Control**
- `TOKEN_BUDGET_PER_USER_PER_DAY` - Daily token limit (default: `100000`)
- `MAX_RESPONSE_TOKENS` - Max tokens per single response (default: `2048`)

**Feature Flags**
- `ENABLE_TELEMETRY_SAMPLING` - Enable telemetry sampling (default: `true`)
- `ENABLE_A2A_PROTOCOL` - Enable agent-to-agent protocol (default: `true`)
- `ENABLE_TOOL_CACHING` - Enable MCP tool caching (default: `true`)

## Authentication

### Local Development

In local dev mode (`LOCAL_DEV_MODE=true`), JWT tokens are parsed without signature verification. This is **for testing only**.

To test authentication locally:
1. Get a valid JWT token from your Entra ID tenant
2. Pass it in the `Authorization: Bearer <token>` header
3. The token will be parsed and user claims extracted

Example using curl:
```bash
curl -H "Authorization: Bearer your-jwt-token" \
  http://localhost:8000/health
```

### Production

In production, JWT tokens are validated against Azure AD public keys (requires implementation).

## Database Schema

### Collections (Cosmos DB)

- **threads** - Chat threads/conversations
  - Partition key: `/agentId`
  - TTL: 90 days
  
- **runs** - Agent execution runs
  - Partition key: `/threadId`
  - TTL: 90 days
  
- **steps** - Tool calls and LLM steps
  - Partition key: `/runId`
  - TTL: 90 days
  
- **toolCalls** - Detailed tool invocation logs
  - Partition key: `/stepId`
  - TTL: 60 days
  
- **agents** - Agent configuration
  - Partition key: `/agentType`
  
- **metrics** - Usage metrics and cost tracking
  - Partition key: `/timestamp`
  - TTL: 60 days

*(Data models are defined in Phase 2)*

## Development Workflow

### Phase 1.2 (Current)
- [x] Project structure
- [x] Configuration system
- [x] Key Vault integration
- [x] Cosmos DB client
- [x] Authentication framework
- [x] Health check endpoint
- [ ] Run and test locally
- [ ] Integrate with Phase 1.3 frontend

### Phase 2
- [ ] Agent implementations
- [ ] MCP client integration
- [ ] Chat streaming endpoints
- [ ] Agent management API
- [ ] Cosmos DB repositories

### Phase 3
- [ ] Frontend integration tests
- [ ] E2E tests with frontend

### Phase 4
- [ ] OpenTelemetry integration
- [ ] Cost tracking
- [ ] CI/CD pipelines
- [ ] Production deployment

## Troubleshooting

### Import Errors

If you see import errors, ensure dependencies are installed:
```bash
pip install -r requirements.txt
```

### Cosmos DB Connection Failed

Check your configuration:
```bash
# Test Cosmos DB connection
python -c "from src.persistence.cosmos_client import initialize_cosmos; initialize_cosmos('https://localhost:8081', 'agents-db', 'C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QB0c/Db2xCLFJxXvdGP3MqFH3w==')"
```

### Port Already in Use

If port 8000 is in use, specify a different port:
```bash
uvicorn src.main:app --port 8001 --reload
```

### CORS Errors

CORS is configured for the `FRONTEND_URL` environment variable. Ensure:
1. Frontend is running at the configured URL
2. `FRONTEND_URL` is set correctly in `.env.local`

## Deployment

### Docker

Build and run the backend in a container:

```bash
# Build image
docker build -t agent-backend:latest .

# Run container
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e AZURE_SUBSCRIPTION_ID=your-id \
  agent-backend:latest
```

### Azure Container Apps

Deployment to Azure Container Apps is handled in Phase 4 via Bicep templates and CI/CD pipelines.

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and write tests
3. Run tests: `pytest`
4. Commit and push
5. Create a pull request

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Azure Cosmos DB Python SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/sdk-python)
- [Azure Identity Python SDK](https://learn.microsoft.com/python/api/overview/azure/identity-readme)
- [Microsoft Agent Framework](https://aka.ms/agentframework)

## License

MIT
