# Architecture Documentation: AI Agents Demo - Part 1

**High-Level Architecture, Tech Stack, and Component Responsibilities**

---

## Table of Contents

1. [Executive Architecture Overview](#executive-architecture-overview)
2. [High-Level Architecture Diagram](#high-level-architecture-diagram)
3. [Technology Stack](#technology-stack)
4. [Component Responsibilities](#component-responsibilities)
5. [Network Architecture](#network-architecture)
6. [Authentication & Authorization Flow](#authentication--authorization-flow)

---

## Executive Architecture Overview

This AI agents demo is built on a modern, cloud-native architecture using Azure services exclusively. The system follows a three-tier architecture with clear separation of concerns:

### Architecture Principles

1. **Azure-Only Infrastructure**: All components run on Azure services with no external cloud dependencies
2. **Private by Default**: All data services and backend components are isolated in a VNet with private endpoints
3. **Identity-Driven Security**: Managed Identity for service-to-service auth, Entra ID for user auth
4. **Observable & Cost-Conscious**: Comprehensive telemetry with cost tracking and budget enforcement
5. **Scalable & Resilient**: Container-based deployment with autoscaling and health checks
6. **Developer-Friendly**: Local development mode with Azure CLI credentials

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION TIER                             │
│  React + TypeScript Frontend (Azure Container Apps - Public)    │
│  - Chat UI with SSE streaming                                   │
│  - Inline trace visualization                                   │
│  - Agent management & configuration                             │
│  - Entra ID authentication (MSAL)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS (authenticated)
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION TIER                              │
│  FastAPI Backend + Azure MCP Sidecar (ACA - Private)            │
│  - Agent orchestration (Agent Framework SDK)                    │
│  - MCP client (Microsoft Learn, adventure-mcp, Azure MCP)       │
│  - A2A server & client (agent-to-agent protocol)                │
│  - OpenAPI tool integration (via APIM)                          │
│  - SSE streaming endpoints                                      │
│  - OpenTelemetry instrumentation                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Private Endpoints
┌─────────────────────────────────────────────────────────────────┐
│                       DATA TIER                                  │
│  Azure Cosmos DB (NoSQL) - State & Metrics                      │
│  Azure Storage (Blob) - Logs & Exports                          │
│  Azure Key Vault - Secrets                                      │
│  Azure App Configuration - Feature Flags                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## High-Level Architecture Diagram

### System Context Diagram

```
┌──────────────┐
│   End User   │ (Authenticated via Entra ID)
└──────┬───────┘
       │ HTTPS
       ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      AZURE SUBSCRIPTION (East US)                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    RESOURCE GROUP: rg-agents-demo               │    │
│  │                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────┐      │    │
│  │  │  Container Apps Environment (VNet-integrated)         │      │    │
│  │  │                                                        │      │    │
│  │  │  ┌────────────────────┐      ┌──────────────────┐   │      │    │
│  │  │  │ Frontend Container │      │ Backend Container│   │      │    │
│  │  │  │  (React + nginx)   │◄────►│   (FastAPI)      │   │      │    │
│  │  │  │  Public Ingress    │      │   Private Only   │   │      │    │
│  │  │  └────────────────────┘      └────────┬─────────┘   │      │    │
│  │  │                                        │              │      │    │
│  │  │                              ┌─────────▼─────────┐   │      │    │
│  │  │                              │ Azure MCP Server  │   │      │    │
│  │  │                              │    (Sidecar)      │   │      │    │
│  │  │                              └───────────────────┘   │      │    │
│  │  └──────────────────────────────────────────────────────┘      │    │
│  │                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────┐      │    │
│  │  │              Private Endpoint Subnet                  │      │    │
│  │  │                                                        │      │    │
│  │  │  [Cosmos DB]  [Key Vault]  [Storage]  [App Config]  │      │    │
│  │  │  [AI Foundry] [APIM]       [App Insights]            │      │    │
│  │  └──────────────────────────────────────────────────────┘      │    │
│  │                                                                  │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  External MCP Servers (accessed via HTTPS):                           │
│  - Microsoft Learn MCP: learn.microsoft.com/api/mcp                   │
│  - adventure-mcp: mssqlmcp.azure-api.net (OAuth2)                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Agent Interaction Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Send message
     ↓
┌──────────────────┐
│  Frontend (ACA)  │
└────┬─────────────┘
     │ 2. POST /api/agents/{id}/chat (SSE)
     ↓
┌──────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                          │
│                                                               │
│  ┌─────────────────────────────────────────────────┐        │
│  │          Agent Framework Orchestration          │        │
│  │                                                  │        │
│  │  ┌──────────────┐         ┌──────────────┐     │        │
│  │  │ Support      │         │ Azure Ops    │     │        │
│  │  │ Triage Agent │         │ Assistant    │     │        │
│  │  └──────┬───────┘         └──────┬───────┘     │        │
│  │         │                        │              │        │
│  │         │  ┌──────────────┐     │              │        │
│  │         │  │ SQL Agent    │     │              │        │
│  │         │  └──────┬───────┘     │              │        │
│  │         │         │              │              │        │
│  │  ┌──────▼─────────▼──────────────▼─────┐       │        │
│  │  │     News Agent                      │       │        │
│  │  └──────────────┬──────────────────────┘       │        │
│  │                 │                               │        │
│  │  ┌──────────────▼───────────────────────┐      │        │
│  │  │  Business Impact Multi-Agent (A2A)   │      │        │
│  │  │  - Calls News & SQL via A2A protocol │      │        │
│  │  └──────────────────────────────────────┘      │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  3. Tool Selection (Agent Framework decides which tools)    │
│     ↓              ↓              ↓              ↓          │
│  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │MS Learn│  │adventure-│  │Azure MCP │  │OpenAPI   │     │
│  │  MCP   │  │   mcp    │  │ (Sidecar)│  │  (APIM)  │     │
│  └────────┘  └──────────┘  └──────────┘  └──────────┘     │
│      ↓             ↓             ↓             ↓           │
│  [External]   [External]   [Localhost]   [Private EP]     │
└──────────────────────────────────────────────────────────────┘
     │
     │ 4. Stream tokens + traces via SSE
     ↓
┌──────────────────┐
│  Frontend (ACA)  │ - Render messages
│                  │ - Display inline traces
└──────────────────┘
     │
     │ 5. Persist to Cosmos DB
     ↓
┌──────────────────┐
│   Cosmos DB      │ - threads, runs, steps, toolCalls, metrics
└──────────────────┘
```

### A2A Protocol Flow (Business Impact Agent)

```
User Message: "How did AI news impact our sales?"
     │
     ↓
┌────────────────────────────────────────────────────────┐
│         Business Impact Agent (Orchestrator)           │
│  System Prompt: "Use News Agent and SQL Agent via A2A │
│                  to correlate news with metrics"       │
└─────────────────┬──────────────────────────────────────┘
                  │
     ┌────────────┴────────────┐
     ↓                         ↓
┌─────────────────┐    ┌─────────────────┐
│   A2A Client    │    │   A2A Client    │
│  (News Agent)   │    │  (SQL Agent)    │
└────────┬────────┘    └────────┬────────┘
         │                      │
         │ POST /a2a/news-agent │ POST /a2a/sql-agent
         ↓                      ↓
┌─────────────────┐    ┌─────────────────┐
│  News Agent     │    │  SQL Agent      │
│  (A2A Server)   │    │  (A2A Server)   │
│                 │    │                 │
│  Tools:         │    │  Tools:         │
│  - Bing News    │    │  - adventure-mcp│
└────────┬────────┘    └────────┬────────┘
         │                      │
         │ Bing Search          │ SQL Query
         ↓                      ↓
    [Azure AI                [adventure-mcp]
     Foundry]               (APIM endpoint)
         │                      │
         └──────────┬───────────┘
                    │
         ┌──────────▼─────────────┐
         │  Business Impact Agent │
         │  Synthesizes results   │
         └────────────────────────┘
                    │
                    ↓
            Stream to User:
            "Recent AI announcements
             correlated with 15% 
             sales increase in Q3..."
             
            Traces (hierarchical):
            ├─ Business Impact Agent
            │  ├─ News Agent (A2A) ✓
            │  │  └─ Bing News: 5 articles
            │  ├─ SQL Agent (A2A) ✓
            │  │  └─ Query: SELECT sales...
            │  └─ Synthesis: correlation found
```

---

## Technology Stack

### Frontend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | React 18 + TypeScript | UI components and state management |
| **Build Tool** | Vite | Fast dev server and optimized builds |
| **UI Library** | Fluent UI v9 (`@fluentui/react-components`) | Microsoft design system |
| **Authentication** | MSAL React (`@azure/msal-react`) | Entra ID authentication |
| **HTTP Client** | Axios | API calls to backend |
| **Streaming** | EventSource (native) | SSE streaming for chat |
| **Routing** | React Router v6 | SPA navigation |
| **State Management** | React Context + Hooks | Global state (auth, agents) |
| **Testing** | Jest + React Testing Library | Unit tests |
| **E2E Testing** | Playwright | End-to-end tests |
| **Hosting** | Azure Container Apps (nginx) | Static file serving |

### Backend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.110+ | Web framework with async support |
| **Runtime** | Python 3.11 | Language runtime |
| **Agent SDK** | Microsoft Agent Framework SDK | Core agent implementation |
| **AI Models** | Azure OpenAI (GPT-4o, GPT-5) | LLM inference via Azure AI Foundry |
| **MCP Client** | `modelcontextprotocol` (Python SDK) | MCP protocol client |
| **A2A Protocol** | Agent Framework A2A module | Agent-to-agent communication |
| **Authentication** | `python-jose`, `cryptography` | JWT validation |
| **Database** | `azure-cosmos` SDK | Cosmos DB client |
| **Secrets** | `azure-keyvault-secrets` | Key Vault integration |
| **Telemetry** | `azure-monitor-opentelemetry` | OpenTelemetry exporter |
| **HTTP Client** | `httpx` | Async HTTP for MCP/OpenAPI calls |
| **Validation** | Pydantic v2 | Request/response validation |
| **Testing** | pytest + pytest-asyncio | Unit and integration tests |
| **Hosting** | Azure Container Apps (Uvicorn) | ASGI server |

### Infrastructure Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **IaC** | Bicep | Infrastructure as Code |
| **Compute** | Azure Container Apps | Serverless containers (frontend + backend) |
| **Database** | Azure Cosmos DB (NoSQL API) | State persistence (threads, runs, agents) |
| **Storage** | Azure Blob Storage | Log exports, file attachments |
| **Secrets** | Azure Key Vault | Secret management |
| **Configuration** | Azure App Configuration | Feature flags, app settings |
| **Networking** | Azure Virtual Network | VNet with subnets and private endpoints |
| **API Gateway** | Azure API Management | OpenAPI tool hosting |
| **AI Platform** | Azure AI Foundry / Azure OpenAI | Model hosting (GPT-4o, GPT-5, Bing grounding) |
| **Observability** | Application Insights + Log Analytics | Telemetry, logs, metrics |
| **Identity** | Azure Entra ID | User authentication |
| **Identity (Apps)** | Managed Identity | Service-to-service authentication |
| **CI/CD** | GitHub Actions | Automated deployment |
| **Registry** | Azure Container Registry | Container image storage |

### External Integrations

| Service | Endpoint | Authentication | Purpose |
|---------|----------|----------------|---------|
| **Microsoft Learn MCP** | `https://learn.microsoft.com/api/mcp` | None | Documentation grounding for Support Triage |
| **adventure-mcp** | `https://mssqlmcp.azure-api.net` | OAuth2 | AdventureWorks SQL queries for SQL Agent |
| **Azure MCP Server** | `http://localhost:3000` (sidecar) | Managed Identity | Azure resource operations for Azure Ops Assistant |
| **Bing News Search** | Via Azure AI Foundry Agent Service | API Key | News grounding for News Agent |

---

## Component Responsibilities

### Frontend Components

#### 1. **App Shell** (`App.tsx`)
- **Responsibilities**:
  - Root component with routing
  - MSAL authentication provider wrapper
  - Global error boundary
  - Theme provider (Fluent UI)
  - Navigation layout (Sidebar + TopNav)
- **Key Dependencies**: `react-router-dom`, `@azure/msal-react`, `@fluentui/react-components`

#### 2. **Authentication Service** (`services/authService.ts`)
- **Responsibilities**:
  - MSAL configuration (client ID, authority, scopes)
  - Login/logout flows
  - Token acquisition for backend API calls
  - User profile retrieval (name, roles)
- **Key Dependencies**: `@azure/msal-browser`

#### 3. **Chat Service** (`services/chatService.ts`)
- **Responsibilities**:
  - Establish SSE connection to `/api/agents/{id}/chat`
  - Parse SSE events (`token`, `trace_start`, `trace_update`, `trace_end`, `done`, `error`)
  - Emit events to React components via callbacks
  - Handle reconnection on disconnect
- **Key Dependencies**: Native `EventSource` API

#### 4. **Agent Service** (`services/agentsService.ts`)
- **Responsibilities**:
  - Fetch agent list (`GET /api/agents`)
  - Fetch agent details (`GET /api/agents/{id}`)
  - Create agent (`POST /api/agents`)
  - Update agent (`PUT /api/agents/{id}`)
  - Delete agent (`DELETE /api/agents/{id}`)
- **Key Dependencies**: `axios`

#### 5. **Message Stream Component** (`components/chat/MessageStream.tsx`)
- **Responsibilities**:
  - Render user and assistant messages
  - Support markdown rendering (code blocks, tables, links)
  - Auto-scroll to latest message
  - Show typing indicator during streaming
- **Key Dependencies**: `react-markdown`, `@fluentui/react-components`

#### 6. **Trace Panel Component** (`components/chat/TracePanel.tsx`)
- **Responsibilities**:
  - Display inline trace blocks within message stream
  - Collapsible/expandable sections
  - Show trace metadata (tool name, status, latency, tokens, input/output)
  - Hierarchical display for A2A traces (parent/child structure)
  - Real-time updates during streaming
  - Visual distinction for A2A traces (special styling/icons)
- **Key Dependencies**: `@fluentui/react-components`

#### 7. **Agent Editor Component** (`components/agents/AgentEditor.tsx`)
- **Responsibilities**:
  - Modal dialog for agent configuration
  - Form fields: name, description, system prompt, model, tools
  - Validation before save
  - Call backend API to persist changes
- **Key Dependencies**: `@fluentui/react-components`

#### 8. **Tool Configurator Component** (`components/agents/ToolConfigurator.tsx`)
- **Responsibilities**:
  - List available tools (MCP servers, OpenAPI APIs, A2A agents)
  - Enable/disable tools via checkboxes
  - Add custom MCP server (URL, auth config)
  - Add custom OpenAPI API (spec URL, auth config)
  - Validation (at least one tool selected)
- **Key Dependencies**: `@fluentui/react-components`

---

### Backend Components

#### 1. **FastAPI Application** (`main.py`)
- **Responsibilities**:
  - Initialize FastAPI app with CORS middleware
  - Register routers (`/api/chat`, `/api/agents`, `/a2a`, `/health`)
  - OpenTelemetry instrumentation middleware
  - Startup hook: connect to Cosmos DB, load agents, seed defaults
  - Shutdown hook: close connections
- **Key Dependencies**: `fastapi`, `uvicorn`, `azure-monitor-opentelemetry`

#### 2. **Configuration Manager** (`config.py`)
- **Responsibilities**:
  - Load environment variables (with `.env` support for local dev)
  - Manage `LOCAL_DEV_MODE` flag (affects auth, telemetry)
  - Azure resource URIs (Cosmos, Key Vault, AI Foundry, etc.)
  - Model deployment names and endpoints
  - Feature flags from App Configuration
- **Key Dependencies**: `pydantic-settings`

#### 3. **Agent Registry** (`agents/registry.py`)
- **Responsibilities**:
  - Load agent configurations from Cosmos DB
  - Agent factory: instantiate agents by ID
  - Agent lifecycle: start, stop, reload
  - Dynamic A2A endpoint registration
  - Cache agent instances for performance
- **Key Dependencies**: `agent_framework` SDK

#### 4. **Agent Base Class** (`agents/base.py`)
- **Responsibilities**:
  - Common interface for all agents
  - Methods: `initialize()`, `run()`, `stream_response()`
  - Tool registration interface
  - Sliding window memory management (last 20 messages)
  - Token counting and budget enforcement
  - Trace event generation
- **Key Dependencies**: `agent_framework` SDK, `opentelemetry`

#### 5. **MCP Client Wrapper** (`tools/mcp_client.py`)
- **Responsibilities**:
  - HTTP/SSE transport for MCP protocol
  - Tool discovery via MCP `tools/list` endpoint
  - Schema caching for performance
  - Tool invocation via MCP `tools/call` endpoint
  - Error handling and retries (3 retries with exponential backoff)
  - Request/response logging for observability
- **Key Dependencies**: `httpx`, `modelcontextprotocol` SDK

#### 6. **A2A Server** (`a2a/server.py`)
- **Responsibilities**:
  - Expose agents as A2A endpoints (`/a2a/{agent_id}`)
  - Serve agent cards at `/.well-known/agent-card.json`
  - Handle A2A protocol requests (JSON-RPC style)
  - Convert agent responses to A2A format
  - Trace A2A calls as child spans
- **Key Dependencies**: `agent_framework.a2a` module

#### 7. **A2A Client** (`a2a/client.py`)
- **Responsibilities**:
  - Discover agents via agent card (`.well-known/agent-card.json`)
  - Format A2A protocol messages
  - Send requests to A2A endpoints
  - Parse A2A responses
  - Error handling and fallback
- **Key Dependencies**: `httpx`, `agent_framework.a2a` module

#### 8. **Chat API** (`api/chat.py`)
- **Responsibilities**:
  - `POST /api/agents/{agent_id}/chat` endpoint
  - Validate request (message, optional thread_id)
  - Load agent from registry
  - Invoke agent with streaming
  - Send SSE events: `token`, `trace_start`, `trace_update`, `trace_end`, `done`, `error`
  - Persist thread, run, steps, tool calls to Cosmos DB
- **Key Dependencies**: `fastapi`, `sse-starlette`

#### 9. **Agents Management API** (`api/agents.py`)
- **Responsibilities**:
  - `GET /api/agents` - List all agents
  - `GET /api/agents/{id}` - Get agent details
  - `POST /api/agents` - Create new agent
  - `PUT /api/agents/{id}` - Update agent
  - `DELETE /api/agents/{id}` - Delete agent
  - Validation: system prompt, model exists, tools are valid
  - Reload agent registry on create/update
- **Key Dependencies**: `fastapi`, Cosmos DB repositories

#### 10. **Cosmos DB Repositories** (`persistence/repositories/`)
- **Responsibilities**:
  - **threads.py**: CRUD for conversation threads
  - **runs.py**: CRUD for agent runs
  - **steps.py**: CRUD for run steps (tool calls)
  - **tool_calls.py**: CRUD for tool call details
  - **agents_repo.py**: CRUD for agent configurations
  - **metrics.py**: Store token usage, costs, latency
  - Partitioning strategy: `/agentId`, `/threadId`, `/userId`
  - Query optimization (use partition key in WHERE clause)
- **Key Dependencies**: `azure-cosmos`

#### 11. **OpenTelemetry Middleware** (`observability/middleware.py`)
- **Responsibilities**:
  - Trace HTTP requests (method, path, status, duration)
  - Extract and propagate correlation IDs (X-Correlation-ID)
  - Extract user context from JWT (user ID, tenant ID)
  - Attach custom attributes to spans
  - PII redaction before logging
- **Key Dependencies**: `opentelemetry`, `azure-monitor-opentelemetry`

#### 12. **Cost Tracker** (`observability/cost_tracker.py`)
- **Responsibilities**:
  - Track token usage per request (input, output, total)
  - Calculate cost based on model pricing (GPT-4o: $0.005/1K, GPT-5: TBD)
  - Aggregate costs per user, per agent, per day
  - Store in Cosmos DB `metrics` collection
  - Alert on threshold breach (>$100/day)
- **Key Dependencies**: `azure-cosmos`, Pydantic

#### 13. **Azure MCP Server Sidecar** (Separate container)
- **Responsibilities**:
  - Run Azure MCP Server process (Node.js or equivalent)
  - Expose MCP tools: `list_resources`, `get_resource`, `deploy_resource`, `query_logs`
  - Authenticate to Azure using Container App Managed Identity
  - Listen on `localhost:3000` for backend requests
  - Health check endpoint: `/health`
- **Key Dependencies**: Azure MCP Server package, Azure SDK

---

## Network Architecture

### VNet Layout

```
VNet: vnet-agents-demo (10.0.0.0/16)
│
├── Subnet: snet-container-apps (10.0.1.0/24)
│   ├── Container Apps Environment
│   │   ├── Frontend Container App (public ingress)
│   │   └── Backend Container App (internal ingress)
│   └── Azure MCP Server (sidecar, same pod as backend)
│
├── Subnet: snet-private-endpoints (10.0.2.0/24)
│   ├── Cosmos DB Private Endpoint
│   ├── Key Vault Private Endpoint
│   ├── Storage Account Private Endpoint
│   ├── App Configuration Private Endpoint
│   ├── Azure OpenAI Private Endpoint
│   └── APIM Private Endpoint
│
└── Subnet: snet-integration (10.0.3.0/24)
    └── Reserved for future integrations (Azure Functions, Logic Apps)
```

### Network Security Groups (NSG)

**NSG: nsg-container-apps**
- **Inbound Rules**:
  - Allow HTTPS (443) from Internet to frontend (public ingress)
  - Allow all from VNet to backend (internal communication)
  - Deny all other inbound
- **Outbound Rules**:
  - Allow HTTPS (443) to Internet (for external MCP servers: Microsoft Learn, adventure-mcp)
  - Allow all to VNet (for private endpoints)
  - Deny all other outbound

**NSG: nsg-private-endpoints**
- **Inbound Rules**:
  - Allow all from snet-container-apps (backend → data services)
  - Deny all other inbound
- **Outbound Rules**:
  - Allow all (no restrictions on responses)

### Private DNS Zones

Private DNS zones for private endpoint resolution:

- `privatelink.documents.azure.com` → Cosmos DB
- `privatelink.vaultcore.azure.net` → Key Vault
- `privatelink.blob.core.windows.net` → Storage Account
- `privatelink.azconfig.io` → App Configuration
- `privatelink.openai.azure.com` → Azure OpenAI
- `privatelink.azure-api.net` → API Management

### Ingress Configuration

**Frontend Container App:**
- Ingress: **External** (public internet)
- Port: 443 (HTTPS)
- Traffic: 100% to latest revision
- Allowed origins: `*` (CORS handled at app level)
- Custom domain: Optional (`agents-demo.yourdomain.com`)

**Backend Container App:**
- Ingress: **Internal** (VNet only)
- Port: 8000 (HTTP, TLS termination at ingress controller)
- Traffic: 100% to latest revision
- Allowed origins: Frontend Container App URL only

**Azure MCP Server (Sidecar):**
- No external ingress (communicates with backend via `localhost`)
- Port: 3000 (HTTP, internal only)

---

## Authentication & Authorization Flow

### User Authentication (Frontend → Backend)

```
1. User navigates to https://agents-demo-frontend.azurecontainerapps.io
   │
   ↓
2. Frontend (MSAL) redirects to Entra ID login
   │
   ↓
3. User authenticates with Entra ID (Microsoft account)
   │
   ↓
4. Entra ID issues ID token + access token
   │
   ↓
5. Frontend stores tokens in session storage (MSAL)
   │
   ↓
6. Frontend calls backend: POST /api/agents/{id}/chat
   Authorization: Bearer <access_token>
   │
   ↓
7. Backend validates JWT token:
   - Verify signature (public key from Entra ID)
   - Verify issuer (https://login.microsoftonline.com/{tenant_id})
   - Verify audience (backend API client ID)
   - Verify expiration (exp claim)
   │
   ↓
8. Backend extracts user context:
   - User ID (oid claim)
   - User email (preferred_username claim)
   - Roles (roles claim): Admin, User
   │
   ↓
9. Backend authorizes request:
   - Admin: Can create/edit/delete agents
   - User: Can chat with agents (read-only)
   │
   ↓
10. Backend processes request and returns response
```

### Service Authentication (Backend → Azure Services)

**Cosmos DB:**
```
Backend → Managed Identity → Cosmos DB
- Backend uses DefaultAzureCredential (resolves to Managed Identity in ACA)
- Managed Identity has "Cosmos DB Data Contributor" role on Cosmos account
- No connection string needed (uses RBAC)
```

**Key Vault:**
```
Backend → Managed Identity → Key Vault
- Backend uses DefaultAzureCredential
- Managed Identity has "Key Vault Secrets User" role
- Secrets retrieved via Key Vault SDK
```

**Azure OpenAI:**
```
Backend → Managed Identity → Azure OpenAI
- Backend uses DefaultAzureCredential
- Managed Identity has "Cognitive Services OpenAI User" role
- No API key needed (uses Entra ID auth)
```

**Azure MCP Server → Azure Resources:**
```
Azure MCP Server (Sidecar) → Managed Identity → Azure Subscription
- Sidecar shares Managed Identity with backend (same pod)
- Managed Identity has:
  - "Reader" role (subscription-level, for resource listing)
  - "Contributor" role (demo resource group only, for deployments)
- Azure MCP Server uses Azure SDK with DefaultAzureCredential
```

**adventure-mcp (External):**
```
Backend → OAuth2 → adventure-mcp (APIM)
1. Backend retrieves client ID + secret from Key Vault
2. Backend requests access token from OAuth2 token endpoint
3. Backend caches token (TTL: token expiration - 5 min)
4. Backend calls adventure-mcp with Authorization: Bearer <token>
5. Token refresh on expiration
```

### Local Development Authentication

**LOCAL_DEV_MODE=true:**
```
Backend → Azure CLI Credential → Azure Services
- Developer runs `az login` locally
- Backend uses DefaultAzureCredential (falls back to Azure CLI)
- Works with Cosmos DB, Key Vault, OpenAI (if Azure CLI has access)

Frontend → MSAL (localhost redirect)
- Entra ID app registration has redirect URI: http://localhost:5173
- Developer logs in with personal Microsoft account or work account
- MSAL acquires tokens for backend API scope
```

---

*End of Part 1. Continue to `02-architecture-part2.md` for detailed file structure, state model, and application flow.*
