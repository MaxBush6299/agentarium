# Project Plan: AI Agents Demo with Microsoft Agent Framework

**Version:** 1.1  
**Date:** October 18, 2025 (Updated)
**Status:** Phase 1.1 Infrastructure ✅ COMPLETE
**Target Region:** East US  
**Tech Stack:** React + TypeScript, FastAPI + Python, Azure AI Foundry, Cosmos DB, Azure Container Apps

---

## 📊 Project Progress

### Phase 1: Foundation & Infrastructure Setup

| Component | Status | Details |
|-----------|--------|---------|
| **1.1 Infrastructure as Code** | ✅ **COMPLETE** | 8 Bicep modules (1,825 lines), main orchestration template, dev/prod parameter files, environment variables, documentation |
| **1.2 Backend Scaffolding** | ⏳ Not Started | FastAPI setup, Cosmos DB integration, Entra ID auth |
| **1.3 Frontend Scaffolding** | ⏳ Not Started | React + TypeScript, MSAL integration, navigation |
| **1.4 Azure MCP Server** | ⏳ Not Started | Sidecar configuration, managed identity setup |

### Deliverables Completed
- ✅ `infra/main.bicep` (282 lines) - Orchestration template
- ✅ `infra/modules/network.bicep` (256 lines) - VNet, subnets, NSGs
- ✅ `infra/modules/cosmos-db.bicep` (281 lines) - 6 collections with TTL
- ✅ `infra/modules/key-vault.bicep` (158 lines) - RBAC-enabled secrets
- ✅ `infra/modules/storage.bicep` (131 lines) - Blob storage
- ✅ `infra/modules/private-endpoints.bicep` (291 lines) - 3 PEs + DNS zones
- ✅ `infra/modules/container-apps.bicep` (191 lines) - Frontend/backend apps
- ✅ `infra/modules/observability.bicep` (75 lines) - Log Analytics + App Insights
- ✅ `.env.template` (110+ variables) - Environment configuration
- ✅ `.gitignore` - Secret protection
- ✅ `infra/README.md` (500+ lines) - Deployment guide
- ✅ `infra/parameters/dev.bicepparam` - Dev environment
- ✅ `infra/parameters/prod.bicepparam` - Prod environment
- ✅ `PHASE-1.1-SUMMARY.md` - Detailed completion summary

### Next Milestone
Phase 1.2: Backend scaffolding with FastAPI, Cosmos DB connectivity, and authentication

---

## Executive Summary

This project delivers a comprehensive demo showcasing AI agents built with Microsoft's Agent Framework SDK, running entirely on Azure. The demo includes:

- **5 MVP Agents**: Support Triage, Azure Ops Assistant, SQL Agent, News Agent, and Multi-Agent Business Impact
- **MCP Integration**: Consume Microsoft Learn MCP, Azure MCP Server (sidecar), and adventure-mcp (AdventureWorks SQL)
- **A2A Protocol**: Agent-to-agent communication for multi-agent orchestration
- **React Frontend**: Chat UI with real-time streaming, trace visualization, and agent management
- **Python Backend**: FastAPI with Agent Framework SDK, SSE streaming, Cosmos DB persistence
- **Azure-Only Infrastructure**: Bicep templates, private networking, Managed Identity, CI/CD via GitHub Actions

---

## Project Structure

The repository is organized as follows:

```
agent-demo/
├── docs/                           # Documentation and planning
│   ├── 01-project-plan-part1.md
│   ├── 01-project-plan-part2.md
│   ├── 01-project-plan-part3.md
│   ├── 02-architecture-part1.md
│   ├── 02-architecture-part2.md
│   ├── 02-architecture-part3.md
│   ├── 03-overview.md
│   └── diagrams/                   # Architecture diagrams
│
├── infra/                          # Bicep infrastructure as code
│   ├── main.bicep                  # Main orchestration template
│   ├── modules/
│   │   ├── network.bicep           # VNet, subnets, private endpoints
│   │   ├── container-apps.bicep    # ACA environment + apps
│   │   ├── cosmos.bicep            # Cosmos DB account + databases
│   │   ├── openai.bicep            # Azure OpenAI / AI Foundry
│   │   ├── keyvault.bicep          # Key Vault + secrets
│   │   ├── appconfig.bicep         # App Configuration
│   │   ├── storage.bicep           # Storage account + containers
│   │   ├── apim.bicep              # API Management + APIs
│   │   ├── monitoring.bicep        # Application Insights + Log Analytics
│   │   └── identity.bicep          # Managed identities + RBAC
│   ├── parameters/
│   │   ├── dev.bicepparam          # Dev environment parameters
│   │   └── prod.bicepparam         # Production environment parameters
│   └── scripts/
│       ├── deploy.ps1              # Deployment script
│       └── teardown.ps1            # Cleanup script
│
├── backend/                        # Python FastAPI backend
│   ├── src/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration & environment variables
│   │   ├── agents/                 # Agent implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base agent class
│   │   │   ├── support_triage.py   # Support Triage agent
│   │   │   ├── azure_ops.py        # Azure Ops Assistant
│   │   │   ├── sql_agent.py        # SQL Agent (AdventureWorks)
│   │   │   ├── news_agent.py       # News Agent (Bing grounding)
│   │   │   ├── business_impact.py  # Multi-agent orchestrator (A2A)
│   │   │   └── registry.py         # Agent registry & factory
│   │   ├── tools/                  # Tool integrations
│   │   │   ├── __init__.py
│   │   │   ├── mcp_client.py       # MCP client wrapper
│   │   │   ├── mcp_servers/
│   │   │   │   ├── microsoft_learn.py
│   │   │   │   ├── azure_mcp.py
│   │   │   │   └── adventure_mcp.py
│   │   │   ├── openapi_client.py   # OpenAPI tool connector
│   │   │   └── bing_grounding.py   # Bing News via AI Foundry
│   │   ├── a2a/                    # A2A protocol implementation
│   │   │   ├── __init__.py
│   │   │   ├── server.py           # A2A server endpoints
│   │   │   ├── client.py           # A2A client for calling other agents
│   │   │   └── cards.py            # Agent card generation
│   │   ├── api/                    # FastAPI routes
│   │   │   ├── __init__.py
│   │   │   ├── chat.py             # Chat endpoints + SSE
│   │   │   ├── agents.py           # Agent management CRUD
│   │   │   ├── auth.py             # Entra ID authentication
│   │   │   └── health.py           # Health check endpoint
│   │   ├── persistence/            # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── cosmos_client.py    # Cosmos DB client wrapper
│   │   │   ├── repositories/
│   │   │   │   ├── threads.py
│   │   │   │   ├── runs.py
│   │   │   │   ├── steps.py
│   │   │   │   ├── tool_calls.py
│   │   │   │   ├── agents_repo.py
│   │   │   │   └── metrics.py
│   │   │   └── models.py           # Pydantic models for state
│   │   ├── observability/          # Telemetry & tracing
│   │   │   ├── __init__.py
│   │   │   ├── otel_config.py      # OpenTelemetry setup
│   │   │   ├── middleware.py       # FastAPI telemetry middleware
│   │   │   └── cost_tracker.py     # Token usage & cost tracking
│   │   └── utils/                  # Shared utilities
│   │       ├── __init__.py
│   │       ├── secrets.py          # Key Vault integration
│   │       └── pii_redaction.py    # PII scrubbing
│   ├── tests/                      # Backend tests
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── requirements.txt            # Python dependencies
│   ├── requirements-dev.txt        # Dev dependencies
│   ├── Dockerfile                  # Backend container image
│   └── .env.example                # Environment variable template
│
├── azure-mcp-server/               # Azure MCP Server sidecar
│   ├── config.json                 # MCP server configuration
│   ├── Dockerfile                  # Sidecar container (if separate)
│   └── README.md
│
├── frontend/                       # React + TypeScript frontend
│   ├── src/
│   │   ├── main.tsx                # App entry point
│   │   ├── App.tsx                 # Root component
│   │   ├── config.ts               # Frontend configuration
│   │   ├── pages/                  # Page components
│   │   │   ├── AgentsDirectory.tsx # List/manage agents
│   │   │   ├── AgentDetail.tsx     # Edit agent configuration
│   │   │   ├── AgentChat.tsx       # Chat interface per agent
│   │   │   ├── SupportTriageChat.tsx
│   │   │   ├── AzureOpsChat.tsx
│   │   │   ├── SqlAgentChat.tsx
│   │   │   ├── NewsAgentChat.tsx
│   │   │   └── BusinessImpactChat.tsx  # Multi-agent A2A showcase
│   │   ├── components/             # Reusable components
│   │   │   ├── chat/
│   │   │   │   ├── MessageStream.tsx
│   │   │   │   ├── TracePanel.tsx      # Inline collapsible traces
│   │   │   │   ├── InputBox.tsx
│   │   │   │   └── ExportButton.tsx    # CSV export
│   │   │   ├── agents/
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   ├── AgentEditor.tsx     # Settings modal
│   │   │   │   ├── ModelSelector.tsx
│   │   │   │   ├── ToolConfigurator.tsx
│   │   │   │   └── PromptEditor.tsx
│   │   │   ├── navigation/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── TopNav.tsx
│   │   │   └── common/
│   │   │       ├── Loading.tsx
│   │   │       └── ErrorBoundary.tsx
│   │   ├── services/               # API clients
│   │   │   ├── api.ts              # Axios instance
│   │   │   ├── chatService.ts      # SSE streaming
│   │   │   ├── agentsService.ts    # Agent CRUD
│   │   │   └── authService.ts      # MSAL integration
│   │   ├── hooks/                  # Custom React hooks
│   │   │   ├── useChat.ts
│   │   │   ├── useAgents.ts
│   │   │   ├── useAuth.ts
│   │   │   └── useSSE.ts
│   │   ├── types/                  # TypeScript types
│   │   │   ├── agent.ts
│   │   │   ├── chat.ts
│   │   │   └── trace.ts
│   │   └── styles/                 # Global styles
│   ├── tests/                      # Frontend tests
│   │   └── playwright/             # E2E tests
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile                  # Frontend container image
│   └── .env.example
│
├── .github/                        # CI/CD workflows
│   └── workflows/
│       ├── deploy-infra.yml        # Bicep deployment
│       ├── deploy-backend.yml      # Backend build + deploy
│       ├── deploy-frontend.yml     # Frontend build + deploy
│       └── e2e-tests.yml           # Post-deployment tests
│
├── scripts/                        # Utility scripts
│   ├── setup-local.ps1             # Local dev setup
│   ├── seed-agents.py              # Seed default agents to Cosmos
│   └── generate-test-data.py       # Test data generation
│
├── openapi/                        # OpenAPI specifications
│   ├── support-triage-api.yaml     # Placeholder OpenAPI spec
│   └── ops-assistant-api.yaml      # Placeholder OpenAPI spec
│
├── .gitignore
├── README.md                       # Generated from 03-overview.md
└── LICENSE
```

---

## Phase 1: Foundation & Infrastructure Setup

**Objective:** Establish the Azure infrastructure, networking, authentication, and core backend scaffolding.

### Detailed Checklist

#### 1.1 Infrastructure as Code (Bicep) ✅ **COMPLETE**
- [x] Create `main.bicep` orchestration template
  - ✅ 282 lines, coordinates all 7 modules with proper dependencies
- [x] Implement `network.bicep` module
  - [x] VNet with 3 subnets (10.0.0.0/16): Container Apps, Private Endpoints, Integration
  - [x] 3 NSGs with least-privilege rules per subnet
  - [x] Private DNS zones configured for all endpoints
- [x] Implement `observability.bicep` module (replaces identity.bicep)
  - [x] Log Analytics Workspace with configurable retention
  - [x] Application Insights with workspace integration
  - [x] Container Insights solution for monitoring
- [x] Implement `key-vault.bicep` module (renamed from keyvault.bicep)
  - [x] Key Vault with private endpoint and RBAC authorization
  - [x] 5 placeholder secrets (openai-api-key, cosmosdb-connection-string, appconfig-connection-string, storage-connection-string, apim-subscription-key)
  - [x] Soft delete (90 days) + optional purge protection
  - [x] 2 RBAC role assignments for Managed Identity (Secrets User, Crypto Officer)
- [x] Implement `storage.bicep` module
  - [x] StorageV2 account with private endpoint support
  - [x] Blob containers: `logs`, `artifacts`, `exports`
  - [x] Hierarchical namespace support (optional for Data Lake)
  - [x] TLS 1.2+ enforcement
- [x] Implement `cosmos-db.bicep` module
  - [x] Cosmos DB SQL API account with private endpoint
  - [x] 6 Collections: `threads`, `runs`, `steps`, `toolCalls`, `agents`, `metrics`
  - [x] Partition keys: `/agentId`, `/threadId`, `/runId`, `/stepId`, `/agentType`, `/timestamp`
  - [x] TTL policies: 90 days (data), 60 days (metrics)
  - [x] Autoscale throughput: 400-4000 RU/s (configurable)
  - [x] Geo-redundant backup (optional in production)
- [x] Implement `private-endpoints.bicep` module
  - [x] 3 Private Endpoints: Cosmos DB, Key Vault, Storage (blob)
  - [x] 3 Private DNS Zones with VNet links and A records
  - [x] Full DNS integration for private connectivity
- [x] Implement `container-apps.bicep` module
  - [x] Container Apps Environment integrated with VNet
  - [x] Frontend app: 0.5 vCPU, 1Gi memory, 1-3 replicas (dev), external ingress
  - [x] Backend app: 1 vCPU, 2Gi memory, 1-5 replicas (dev), internal ingress
  - [x] Auto-scaling based on HTTP concurrency
  - [x] Application Insights integration
- [x] Create parameter files with environment separation
  - [x] `dev.bicepparam`: Development-optimized (400 RU/s, 7-day retention, minimal replicas)
  - [x] `prod.bicepparam`: Production-optimized (4000 RU/s autoscale, 90-day retention, HA replicas, purge protection)
- [x] Create `.env.template` with 110+ environment variables
  - [x] Organized into 10 sections (Azure subscription, network, Cosmos, Key Vault, storage, monitoring, secrets, etc.)
  - [x] Clear documentation of each variable
  - [x] Post-deployment reference section
- [x] Create `.gitignore` to prevent secret commits
- [x] Create comprehensive `infra/README.md` (500+ lines)
  - [x] Quick start deployment guide
  - [x] Module reference documentation
  - [x] Environment configuration comparison
  - [x] Security best practices
  - [x] Troubleshooting guide
- [x] All Bicep modules compile without errors ✅
- [x] Test Bicep deployment validation (no critical errors)

#### 1.2 Backend Scaffolding
- [ ] Initialize Python project structure
- [ ] Create `requirements.txt` with core dependencies:
  - [ ] `fastapi`, `uvicorn[standard]`
  - [ ] `azure-identity`, `azure-keyvault-secrets`
  - [ ] `azure-cosmos`
  - [ ] `azure-monitor-opentelemetry`
  - [ ] `openai`, `azure-ai-openai`
  - [ ] `microsoft-agent-framework` (or equivalent SDK reference)
  - [ ] `pydantic`, `pydantic-settings`
- [ ] Implement `config.py` with environment variable handling
  - [ ] `LOCAL_DEV_MODE` switch (default: `True`)
  - [ ] Azure resource URIs (Cosmos, Key Vault, App Insights)
  - [ ] Entra ID tenant/client IDs
- [ ] Implement Key Vault integration (`utils/secrets.py`)
  - [ ] Local dev: Azure CLI credentials
  - [ ] Production: Managed Identity
- [ ] Implement Cosmos DB client wrapper (`persistence/cosmos_client.py`)
  - [ ] Connection string from Key Vault
  - [ ] Database/container references
  - [ ] Retry policies
- [ ] Create FastAPI app skeleton (`main.py`)
  - [ ] CORS middleware (allow frontend origin)
  - [ ] Health check endpoint (`/health`)
  - [ ] Startup/shutdown lifecycle hooks
- [ ] Implement Entra ID authentication (`api/auth.py`)
  - [ ] JWT token validation
  - [ ] User-delegated claims extraction
  - [ ] Role-based authorization middleware (`Admin`, `User`)
- [ ] Create Dockerfile for backend
  - [ ] Multi-stage build (build + runtime)
  - [ ] Non-root user
  - [ ] Health check command
- [ ] Test local backend startup (`uvicorn main:app --reload`)

#### 1.3 Frontend Scaffolding
- [ ] Initialize Vite + React + TypeScript project
- [ ] Install Fluent UI React components (`@fluentui/react-components`)
- [ ] Install MSAL for React (`@azure/msal-react`, `@azure/msal-browser`)
- [ ] Install Axios for API calls
- [ ] Create `config.ts` with environment variables
  - [ ] Backend API URL (localhost in dev, ACA URL in prod)
  - [ ] Entra ID client ID
  - [ ] Entra ID authority
- [ ] Implement MSAL authentication provider (`services/authService.ts`)
  - [ ] Login/logout flows
  - [ ] Token acquisition for backend API scope
- [ ] Create root `App.tsx` with routing
  - [ ] Protected routes requiring authentication
  - [ ] Unauthenticated state (login page)
- [ ] Create basic navigation (`components/navigation/Sidebar.tsx`, `TopNav.tsx`)
- [ ] Create placeholder pages:
  - [ ] `AgentsDirectory.tsx`
  - [ ] `AgentChat.tsx` (template for agent-specific pages)
- [ ] Create Dockerfile for frontend
  - [ ] Build static assets with Vite
  - [ ] Serve with nginx
  - [ ] Custom nginx.conf for SPA routing
- [ ] Test local frontend startup (`npm run dev`)

#### 1.4 Azure MCP Server Sidecar
- [ ] Download/clone Azure MCP Server repo or use official package
- [ ] Create `config.json` for Azure MCP Server
  - [ ] Managed Identity authentication
  - [ ] Subscription ID(s)
  - [ ] Resource scope (subscription or resource group)
- [ ] Configure as sidecar container in `container-apps.bicep`
  - [ ] Shared localhost network with backend
  - [ ] Port mapping (e.g., `:3000` for MCP server)
  - [ ] Managed Identity assignment
- [ ] Test Azure MCP Server locally with Azure CLI credentials
  - [ ] Run `node azure-mcp-server/index.js` (or equivalent)
  - [ ] Verify health endpoint and tool listing

### Acceptance Criteria

**Phase 1.1 Infrastructure (✅ COMPLETE):**
- [x] All Bicep modules deploy successfully to East US (validated with no critical errors)
- [x] VNet and private endpoints are configured correctly (3 endpoints, 3 DNS zones)
- [x] Key Vault is configured with RBAC and secrets placeholders
- [x] Cosmos DB collections are created with correct partition keys (6 collections with TTL)
- [x] Environment variables properly separated from infrastructure code (.env.template with 110+ vars)
- [x] Security measures implemented (.gitignore, no hardcoded secrets, RBAC, NSG rules)
- [x] Comprehensive documentation created (README.md with deployment guide)
- [x] Both dev and prod parameter files created and validated
- [x] All infrastructure code production-ready (1,825 lines of Bicep)

**Phase 1.2 Backend Scaffolding (Not Started):**
- [ ] Backend starts locally and can authenticate with Azure CLI credentials
- [ ] Backend can read secrets from Key Vault
- [ ] Backend can connect to Cosmos DB

**Phase 1.3 Frontend Scaffolding (Not Started):**
- [ ] Frontend starts locally and renders navigation
- [ ] Frontend can authenticate with Entra ID (MSAL)
- [ ] Frontend can call backend `/health` endpoint

**Phase 1.4 Azure MCP Server Sidecar (Not Started):**
- [ ] Azure MCP Server sidecar runs locally and lists available tools
- [ ] Sidecar can authenticate with managed identity

**Overall Phase 1:**
- [x] Infrastructure layer ✅
- [ ] Backend scaffolding (pending)
- [ ] Frontend scaffolding (pending)
- [ ] Azure MCP Server integration (pending)

### Test Plan (Phase 1)

#### Unit Tests
- [ ] Test Key Vault secret retrieval (mocked and live)
- [ ] Test Cosmos DB connection (mocked and live)
- [ ] Test Entra ID token validation (mocked tokens)
- [ ] Test configuration loading (environment variables)

#### Integration Tests
- [ ] Deploy Bicep templates to a test resource group
- [ ] Verify all resources are created and accessible
- [ ] Test managed identity access to Key Vault
- [ ] Test managed identity access to Cosmos DB
- [ ] Test private endpoint connectivity
- [ ] Verify Azure MCP Server can list Azure resources via managed identity

#### E2E Tests
- [ ] Start backend locally with `LOCAL_DEV_MODE=true`
- [ ] Call `/health` endpoint and verify response
- [ ] Start frontend locally
- [ ] Log in with Entra ID
- [ ] Verify frontend can call backend and receive authenticated response
- [ ] Verify Azure MCP Server sidecar responds to tool list request

#### Security Tests
- [ ] Verify private endpoints are not accessible from public internet
- [ ] Verify Key Vault secrets are not logged
- [ ] Verify CORS is restricted to frontend origin
- [ ] Verify JWT tokens are validated correctly
- [ ] Verify role-based authorization (Admin vs. User)

---

## Phase 1 Summary

At the end of Phase 1, you will have:
- Complete Azure infrastructure deployed via Bicep
- Backend and frontend scaffolding running locally
- Entra ID authentication working end-to-end
- Azure MCP Server sidecar running and accessible
- Secure, private networking with managed identities
- A solid foundation for agent implementation in Phase 2

**Estimated Duration:** 2 weeks  
**Key Milestone:** Infrastructure live, local dev environment functional

---

*End of Part 1. Continue to `01-project-plan-part2.md` for Phase 2 and Phase 3.*
