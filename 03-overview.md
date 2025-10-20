# AI Agents Demo: Complete Customer Showcase

**Demonstrating AI Agents with Microsoft's Agent Framework SDK on Azure**

---

## Overview

This project is a **comprehensive, production-ready demonstration** of AI agents built using **Microsoft's Agent Framework SDK** (aka.ms/agentframework) and deployed entirely on Azure. It showcases how to build intelligent, multi-agent systems that can collaborate, call tools via **Model Context Protocol (MCP)**, orchestrate through **Agent-to-Agent (A2A) protocol**, and provide real-time transparency through streaming traces.

**Purpose**: Educate customers on building AI agent solutions with Microsoft technologies, demonstrating best practices for architecture, security, observability, and cost management.

**Target Audience**:
- Enterprise architects evaluating AI agent platforms
- Developers building agentic AI applications
- Technical decision-makers exploring Azure AI capabilities
- POC/MVP teams needing a production-ready template

---

## What You'll See

### 🤖 **5 Fully Functional AI Agents**

1. **Support Triage Agent**
   - Classifies customer support tickets by urgency, category, and sentiment
   - Uses OpenAPI tools to create Jira tickets
   - Demonstrates single-agent workflow with external API integration

2. **Azure Operations Agent**
   - Lists and manages Azure resources via **Azure MCP Server** (sidecar container)
   - Uses Managed Identity for secure Azure API access
   - Demonstrates MCP integration with privileged operations

3. **SQL Agent**
   - Queries AdventureWorks database via **adventure-mcp** (OAuth2)
   - Translates natural language to SQL
   - Demonstrates MCP integration with authentication

4. **News Agent**
   - Searches and analyzes recent news via Bing Search API
   - Provides summarized insights with citations
   - Demonstrates OpenAPI tool integration

5. **Business Impact Agent** ⭐ **Multi-Agent Orchestrator**
   - **Showcases Agent-to-Agent (A2A) Protocol**
   - Orchestrates News Agent and SQL Agent to answer complex questions
   - Example: "How did the latest tech news impact our sales in Q4?"
   - Provides hierarchical traces showing orchestration flow
   - **Prominently highlighted in UI** with "Multi-Agent" badge

### 🛠️ **Tool Integration Patterns**

- **MCP Servers**: Microsoft Learn MCP (public), adventure-mcp (OAuth2), Azure MCP Server (sidecar)
- **OpenAPI Tools**: Bing Search, Jira API (mock), custom tool creation
- **A2A Protocol**: Hierarchical agent orchestration for complex workflows

### 💬 **Interactive Chat Interface**

- React frontend with Fluent UI v9
- Real-time streaming responses (Server-Sent Events)
- Inline collapsible trace panels showing:
  - Agent reasoning steps
  - Tool calls with parameters and results
  - **Hierarchical A2A calls** (parent → child agents)
  - Token usage and cost per message
- Dedicated page per agent with usage guidance
- Agent configuration editor (create, edit, delete agents)

### 🔐 **Enterprise-Grade Security**

- Entra ID authentication (MSAL React)
- VNet-isolated Azure infrastructure with private endpoints
- Managed Identity for all Azure service connections
- PII redaction in logs and traces
- Role-based access control (Admin, User)
- No secrets in code (Key Vault + Managed Identity)

### 📊 **Complete Observability**

- OpenTelemetry integration → Application Insights
- Cost tracking per user, per agent, per request
- Token usage monitoring with daily budgets
- Real-time dashboards for latency, errors, A2A orchestration
- Alerts for high costs and anomalies

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                        │
│                    (Entra ID Auth via MSAL)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Frontend (React + TypeScript)                  │
│          Container Apps - Public Ingress (VNet)             │
│      • Chat UI  • Trace Visualization  • Agent Config      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS (Internal)
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI + Python)                     │
│       Container Apps - Internal Ingress (VNet)              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Agent Framework SDK  │  A2A Protocol  │  MCP      │    │
│  │  • 5 AI Agents        │  • Orchestration│  • Tools │    │
│  └────────────────────────────────────────────────────┘    │
│       ↓                   ↓                    ↓            │
│   Cosmos DB          Azure OpenAI        MCP Servers        │
│   (State/Traces)     (GPT-4o/GPT-5)     (localhost:3000)   │
│   [Private EP]       [Private EP]       [Sidecar]          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                External Integrations                        │
│  • Microsoft Learn MCP (https://learn.microsoft.com)       │
│  • adventure-mcp (https://mssqlmcp.azure-api.net)          │
│  • Bing Search API                                          │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Principles**:
- **Azure-only**: All services are Azure-native (Container Apps, Cosmos DB, Key Vault, OpenAI, etc.)
- **Private networking**: VNet with private endpoints for data services, no public IPs
- **Zero-trust security**: Managed Identity, Entra ID auth, NSG rules, PII redaction
- **Streaming by default**: SSE for real-time responses and trace updates
- **Session-only memory**: Sliding window (20 messages) per thread, no long-term memory
- **Cost-conscious**: Token budgets, response caching, telemetry sampling (<$500/month target)

---

## Quick Start

### Prerequisites

1. **Azure Subscription** with sufficient quota (Container Apps, Cosmos DB, OpenAI)
2. **Azure CLI** (v2.50+): `az --version`
3. **Docker** (for local development): `docker --version`
4. **Node.js** (v18+): `node --version`
5. **Python** (3.11+): `python --version`
6. **Git**: `git --version`

### Clone the Repository

```bash
git clone https://github.com/your-org/ai-agents-demo.git
cd ai-agents-demo
```

### Deploy to Azure (Automated)

**Option 1: Using GitHub Actions (Recommended)**

1. Fork this repository to your GitHub account

2. Configure GitHub OIDC with Azure:
   ```bash
   # Create service principal for GitHub Actions
   az ad sp create-for-rbac --name "sp-github-agents-demo" \
     --role owner \
     --scopes /subscriptions/{subscription-id} \
     --sdk-auth
   
   # Store output JSON in GitHub secret: AZURE_CREDENTIALS
   ```

3. Set GitHub repository secrets:
   - `AZURE_CREDENTIALS`: Service principal JSON from step 2
   - `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID
   - `AZURE_TENANT_ID`: Your Entra ID tenant ID
   - `ADVENTURE_MCP_CLIENT_SECRET`: OAuth2 client secret for adventure-mcp

4. Trigger deployment workflow:
   ```bash
   # Push to main branch or manually trigger "Deploy Infrastructure"
   git push origin main
   ```

5. Workflows will run in order:
   - `01-deploy-infrastructure.yml` (Bicep → Azure resources)
   - `02-deploy-backend.yml` (Build → Push → Deploy backend container)
   - `03-deploy-frontend.yml` (Build → Push → Deploy frontend container)

6. Access the app:
   - Frontend URL will be in workflow output: `https://ca-agents-frontend.{random}.eastus.azurecontainerapps.io`

**Option 2: Manual Deployment**

```bash
# 1. Login to Azure
az login
az account set --subscription {subscription-id}

# 2. Deploy infrastructure
cd infra
az deployment group create \
  --resource-group rg-agents-demo \
  --template-file main.bicep \
  --parameters parameters/prod.bicepparam

# 3. Store secrets in Key Vault
az keyvault secret set --vault-name kv-agents-demo \
  --name adventure-mcp-client-secret --value "<your-secret>"

# 4. Build and push backend
cd ../backend
az acr login --name acragentsdemo
docker build -t acragentsdemo.azurecr.io/backend:v1.0.0 .
docker push acragentsdemo.azurecr.io/backend:v1.0.0

# 5. Build and push frontend
cd ../frontend
docker build -t acragentsdemo.azurecr.io/frontend:v1.0.0 .
docker push acragentsdemo.azurecr.io/frontend:v1.0.0

# 6. Deploy containers
az containerapp update \
  --name ca-agents-backend \
  --resource-group rg-agents-demo \
  --image acragentsdemo.azurecr.io/backend:v1.0.0

az containerapp update \
  --name ca-agents-frontend \
  --resource-group rg-agents-demo \
  --image acragentsdemo.azurecr.io/frontend:v1.0.0

# 7. Seed default agents
python scripts/seed-agents.py

# 8. Test the deployment
curl https://ca-agents-backend.{random}.eastus.azurecontainerapps.io/health
```

---

## Local Development

### Run Locally (Full Stack)

**Terminal 1: Backend**

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export LOCAL_DEV_MODE=true
export AZURE_SUBSCRIPTION_ID={your-subscription-id}
export KEY_VAULT_URL=https://kv-agents-demo.vault.azure.net/
export COSMOS_ENDPOINT=https://cosmos-agents-demo.documents.azure.com/
export OPENAI_ENDPOINT=https://openai-agents-demo.openai.azure.com/
export OPENAI_DEPLOYMENT=gpt-4o

# Login with Azure CLI (for local Managed Identity simulation)
az login

# Run FastAPI server
uvicorn main:app --reload --port 8000
```

**Terminal 2: Azure MCP Server (Sidecar)**

```bash
cd backend/sidecar

# Install Azure MCP Server (Node.js)
npm install -g @microsoft/azure-mcp-server

# Run sidecar (uses Azure CLI credentials)
azure-mcp-server --port 3000
```

**Terminal 3: Frontend**

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
export VITE_API_URL=http://localhost:8000
export VITE_ENTRA_CLIENT_ID={your-entra-app-client-id}
export VITE_ENTRA_TENANT_ID={your-tenant-id}

# Run Vite dev server
npm run dev
```

**Access the app**: `http://localhost:5173`

### Run Tests

```bash
# Backend unit tests
cd backend
pytest tests/unit -v

# Backend integration tests (requires Azure resources)
pytest tests/integration -v

# Frontend unit tests
cd frontend
npm run test

# E2E tests (requires full stack running)
npm run test:e2e
```

---

## Configuration Guide

### Add a New Agent

1. **Create agent configuration** (`backend/agents/configs/new_agent.yaml`):

```yaml
id: agent-new
name: "New Agent"
description: "Description of what this agent does"
systemPrompt: |
  You are a helpful assistant that...
model: gpt-4o
temperature: 0.7
maxTokens: 2000
tools:
  - type: mcp
    server: microsoft-learn
    tools: ["search_docs"]
  - type: openapi
    name: custom_api
    spec_url: https://example.com/openapi.json
```

2. **Register agent** in `backend/agents/registry.py`:

```python
from agents.implementations.new_agent import NewAgent

AGENT_REGISTRY = {
    # ... existing agents
    "agent-new": NewAgent,
}
```

3. **Implement agent** (`backend/agents/implementations/new_agent.py`):

```python
from agents.base import BaseAgent

class NewAgent(BaseAgent):
    async def process_message(self, message: str, context: dict) -> str:
        # Your agent logic here
        response = await self.agent_sdk.generate_response(message)
        return response
```

4. **Seed agent to Cosmos DB**:

```bash
python scripts/seed-agents.py --agent new_agent
```

5. **Add frontend page** (`frontend/src/pages/NewAgentPage.tsx`):

```tsx
export function NewAgentPage() {
  return (
    <AgentPageLayout
      agentId="agent-new"
      title="New Agent"
      description="What this agent can do..."
      examples={[
        "Example prompt 1",
        "Example prompt 2",
      ]}
    />
  );
}
```

### Add a New MCP Server

1. **Configure MCP server** in `backend/tools/mcp_servers/new_server.py`:

```python
from tools.mcp_client import MCPClient

class NewMCPServer(MCPClient):
    def __init__(self):
        super().__init__(
            endpoint="https://your-mcp-server.com",
            auth_type="bearer",  # or "oauth2", "none"
        )
    
    async def authenticate(self):
        # OAuth2 or API key logic
        pass
```

2. **Register in `backend/tools/mcp_registry.py`**:

```python
from tools.mcp_servers.new_server import NewMCPServer

MCP_SERVERS = {
    # ... existing servers
    "new-server": NewMCPServer(),
}
```

3. **Use in agent configuration**:

```yaml
tools:
  - type: mcp
    server: new-server
    tools: ["tool_name"]
```

### Add a New OpenAPI Tool

1. **Place OpenAPI spec** in `backend/tools/openapi_specs/new_api.yaml`

2. **Register in agent configuration**:

```yaml
tools:
  - type: openapi
    name: new_api
    spec_url: file://tools/openapi_specs/new_api.yaml
    auth:
      type: api_key
      key_name: X-API-Key
      key_secret_name: new-api-key  # From Key Vault
```

3. **Store API key in Key Vault**:

```bash
az keyvault secret set --vault-name kv-agents-demo \
  --name new-api-key --value "<your-api-key>"
```

---

## Key Features Explained

### Why Not Show Chain-of-Thought?

**We deliberately do NOT expose the agent's internal reasoning (chain-of-thought) to users**. Instead:

- **Show traces**: Tool calls, parameters, results, and timing
- **Show steps**: High-level actions the agent takes (e.g., "Searching documentation...", "Querying database...")
- **Hide reasoning**: The "thinking" tokens that LLMs generate internally

**Rationale**:
- Chain-of-thought can be confusing for non-technical users
- Traces provide actionable transparency (what the agent DID, not what it THOUGHT)
- Reduces token costs (reasoning tokens are not streamed to frontend)
- Aligns with Microsoft's responsible AI principles (transparency without cognitive overload)

**Implementation**:
- Agent Framework SDK supports structured outputs (tool calls, steps)
- We stream these as separate SSE events
- Frontend renders them in collapsible trace panels
- Chain-of-thought remains in Application Insights for debugging

### Why Emphasize A2A Protocol?

**Agent-to-Agent (A2A) protocol is a key differentiator** for Microsoft's Agent Framework SDK:

- **Hierarchical orchestration**: One agent can delegate subtasks to specialized agents
- **Composability**: Build complex workflows by combining simpler agents
- **Observability**: Hierarchical traces show parent → child agent calls
- **Not MCP**: A2A is purpose-built for agent orchestration (MCP is for tool access)

**Where it's highlighted**:
- Business Impact agent page has a **"Multi-Agent Orchestration"** banner
- Trace panel shows **nested agent calls** with indentation
- Architecture docs explain A2A vs. MCP (when to use each)

---

## Cost & Security Considerations

### Expected Costs

**Monthly cost estimate for 100 users, 1000 messages/day**:

| Service | Cost |
|---------|------|
| Azure OpenAI (GPT-4o) | $300 |
| Container Apps | $90-750 |
| Cosmos DB | $25-200 |
| Other (Storage, Key Vault, App Insights) | $68 |
| **Total** | **$558-1,543/month** |

**Cost optimization strategies**:
- Token budgets: 100K tokens/user/day
- Response caching: 1-hour TTL for Microsoft Learn MCP
- Telemetry sampling: 10% in production
- Cosmos DB TTL: 90 days for threads, 180 days for metrics

### Security Best Practices

✅ **Entra ID authentication** (no anonymous access)  
✅ **Managed Identity** (no secrets in code)  
✅ **Private endpoints** (VNet-isolated data services)  
✅ **PII redaction** (email, phone, SSN removed from logs)  
✅ **Input validation** (SQL injection, XSS prevention)  
✅ **Rate limiting** (100 req/min per user)  
✅ **Audit logging** (all admin actions tracked)  
✅ **TLS 1.2+** (encryption in transit everywhere)  

---

## Project Structure

```
ai-agents-demo/
├── backend/                      # FastAPI backend
│   ├── agents/                   # Agent implementations
│   │   ├── base.py               # Base agent class
│   │   ├── implementations/      # 5 agent implementations
│   │   ├── configs/              # Agent YAML configs
│   │   └── registry.py           # Agent registry
│   ├── tools/                    # MCP & OpenAPI tools
│   │   ├── mcp_client.py         # MCP client base
│   │   ├── mcp_servers/          # 3 MCP server integrations
│   │   ├── openapi_specs/        # OpenAPI specs (Bing, Jira)
│   │   └── circuit_breaker.py    # Failure resilience
│   ├── a2a/                      # A2A protocol
│   │   ├── server.py             # Expose agents as A2A servers
│   │   └── client.py             # Call other agents
│   ├── api/                      # FastAPI routes
│   │   ├── chat.py               # Chat endpoint (SSE)
│   │   ├── agents.py             # Agent CRUD
│   │   └── health.py             # Health checks
│   ├── persistence/              # Cosmos DB
│   │   ├── cosmos_client.py      # Client with retry logic
│   │   ├── repositories/         # 6 collection repositories
│   │   └── models.py             # Pydantic models
│   ├── observability/            # OpenTelemetry
│   │   ├── otel_config.py        # Tracer, meter, exporter
│   │   ├── cost_tracker.py       # Token budget enforcement
│   │   └── pii_redaction.py      # PII removal
│   ├── utils/                    # Shared utilities
│   │   ├── secrets.py            # Key Vault client
│   │   └── config.py             # Settings (env vars)
│   ├── sidecar/                  # Azure MCP Server sidecar
│   │   └── Dockerfile            # Sidecar container
│   ├── main.py                   # FastAPI app entry point
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Backend container
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── pages/                # 6 agent pages + home
│   │   ├── components/           # Reusable UI components
│   │   │   ├── ChatInterface.tsx # Chat UI with SSE
│   │   │   ├── TracePanel.tsx    # Collapsible trace viewer
│   │   │   ├── AgentCard.tsx     # Agent cards on home page
│   │   │   └── AgentEditor.tsx   # Agent config editor
│   │   ├── services/             # API clients
│   │   │   ├── apiClient.ts      # Axios wrapper
│   │   │   └── authService.ts    # MSAL wrapper
│   │   ├── hooks/                # React hooks
│   │   │   ├── useSSE.ts         # SSE event handling
│   │   │   └── useAuth.ts        # Entra ID auth
│   │   ├── types/                # TypeScript types
│   │   │   ├── agent.ts          # Agent, Thread, Run types
│   │   │   └── sse.ts            # SSE event types
│   │   ├── App.tsx               # Root component
│   │   └── main.tsx              # React entry point
│   ├── package.json              # Node dependencies
│   ├── vite.config.ts            # Vite config
│   └── Dockerfile                # Frontend container (nginx)
├── infra/                        # Bicep infrastructure
│   ├── main.bicep                # Main orchestration
│   ├── modules/                  # Reusable modules
│   │   ├── container-apps.bicep  # Frontend + Backend
│   │   ├── cosmos-db.bicep       # Cosmos DB + collections
│   │   ├── key-vault.bicep       # Key Vault + secrets
│   │   ├── network.bicep         # VNet + subnets + NSGs
│   │   ├── private-endpoints.bicep # 6 private endpoints
│   │   ├── openai.bicep          # Azure OpenAI
│   │   └── observability.bicep   # App Insights + Log Analytics
│   └── parameters/
│       ├── dev.bicepparam        # Dev environment
│       └── prod.bicepparam       # Production environment
├── .github/
│   └── workflows/                # CI/CD pipelines
│       ├── 01-deploy-infrastructure.yml
│       ├── 02-deploy-backend.yml
│       └── 03-deploy-frontend.yml
├── scripts/
│   └── seed-agents.py            # Seed default agents to Cosmos DB
├── tests/
│   ├── unit/                     # Unit tests (pytest)
│   ├── integration/              # Integration tests
│   └── e2e/                      # E2E tests (Playwright)
├── docs/
│   ├── 01-project-plan-part1.md  # Project plan (Phase 1)
│   ├── 01-project-plan-part2.md  # Project plan (Phase 2-3)
│   ├── 01-project-plan-part3.md  # Project plan (Phase 4)
│   ├── 02-architecture-part1.md  # Architecture (Overview)
│   ├── 02-architecture-part2.md  # Architecture (Details)
│   └── 02-architecture-part3.md  # Architecture (Operations)
├── .gitignore
├── README.md                     # This file
└── LICENSE
```

---

## Timeline & Milestones

**Total Duration**: 10 weeks (can be compressed to 6-8 weeks with parallel work)

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1**: Foundation & Infrastructure | 2 weeks | Bicep modules, VNet, Cosmos DB, Container Apps skeleton |
| **Phase 2**: Agent Implementation | 3 weeks | 5 agents, MCP integration, A2A protocol, SSE streaming |
| **Phase 3**: Frontend Development | 2 weeks | Chat UI, trace visualization, agent pages, auth |
| **Phase 4**: Observability, Security, CI/CD | 2 weeks | OpenTelemetry, cost tracking, GitHub Actions, testing |
| **Final**: Testing & Documentation | 1 week | E2E tests, performance tests, README, runbooks |

---

## Success Metrics

**Demo Effectiveness**:
- ✅ All 5 agents functional and responsive (<3s p95 latency)
- ✅ A2A protocol visibly demonstrated with hierarchical traces
- ✅ MCP integration working with all 3 servers
- ✅ Real-time streaming with trace updates
- ✅ Cost tracking visible in UI (<$500/month for demo workload)

**Customer Engagement**:
- ✅ Clear differentiation of A2A vs. MCP (when to use each)
- ✅ Comprehensive documentation (architecture, setup, operations)
- ✅ Reusable for POCs (well-structured, modular, extensible)
- ✅ Secure by default (Entra ID, Managed Identity, private networking)

---

## Contributing

This is a **demonstration project** maintained by Microsoft. For production use cases, please consult the official [Microsoft Agent Framework SDK documentation](https://aka.ms/agentframework).

**Feedback & Issues**:
- Report issues in GitHub Issues
- Suggest improvements via Pull Requests
- Ask questions in Discussions

---

## License

MIT License. See `LICENSE` file for details.

---

## Resources

- **Microsoft Agent Framework SDK**: [aka.ms/agentframework](https://aka.ms/agentframework)
- **Model Context Protocol (MCP)**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Agent-to-Agent Protocol**: See Microsoft Learn docs (A2A protocol specification)
- **Azure Container Apps**: [docs.microsoft.com/azure/container-apps](https://docs.microsoft.com/azure/container-apps)
- **Azure OpenAI**: [docs.microsoft.com/azure/cognitive-services/openai](https://docs.microsoft.com/azure/cognitive-services/openai)
- **Fluent UI v9**: [react.fluentui.dev](https://react.fluentui.dev)

---

## Contact

For questions or demo requests, contact: [your-email@microsoft.com]

---

**🎉 You're now ready to build production-grade AI agents with Microsoft's Agent Framework SDK on Azure!**

*For detailed architecture and implementation guides, see the `docs/` folder.*
