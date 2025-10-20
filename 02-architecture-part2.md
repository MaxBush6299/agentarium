# Architecture Documentation: AI Agents Demo - Part 2

**Detailed Structure, State Model, and Application Flow**

---

## Table of Contents

1. [Detailed File Structure](#detailed-file-structure)
2. [State Model & Data Schema](#state-model--data-schema)
3. [Application Flow](#application-flow)
4. [MCP Integration Patterns](#mcp-integration-patterns)
5. [A2A Protocol Implementation](#a2a-protocol-implementation)
6. [Streaming Architecture](#streaming-architecture)

---

## Detailed File Structure

### Backend Module Organization

```python
backend/
├── src/
│   ├── main.py                          # FastAPI application entry point
│   │   # - Initialize FastAPI app
│   │   # - Register middleware (CORS, telemetry, auth)
│   │   # - Register routers
│   │   # - Startup: connect to Cosmos, load agents, seed defaults
│   │   # - Shutdown: close connections
│   │
│   ├── config.py                        # Configuration management
│   │   # - Pydantic Settings model
│   │   # - Environment variables (LOCAL_DEV_MODE, AZURE_* URIs)
│   │   # - Feature flags from App Configuration
│   │   # - Model deployment configs
│   │
│   ├── agents/                          # Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py                      # Base agent class
│   │   │   # - AIAgent wrapper
│   │   │   # - Sliding window memory (last 20 messages)
│   │   │   # - Token counting and budget enforcement
│   │   │   # - Trace event generation
│   │   │   # - Common methods: initialize(), run(), stream_response()
│   │   │
│   │   ├── registry.py                  # Agent registry & factory
│   │   │   # - Load agent configs from Cosmos DB
│   │   │   # - Agent factory: create_agent(agent_id) -> AIAgent
│   │   │   # - Agent lifecycle: start(), stop(), reload()
│   │   │   # - Cache agent instances (LRU cache)
│   │   │   # - Dynamic A2A endpoint registration
│   │   │
│   │   ├── support_triage.py            # Support Triage agent
│   │   │   # - System prompt: Microsoft product support specialist
│   │   │   # - Tools: Microsoft Learn MCP, Support Triage OpenAPI
│   │   │   # - Model: GPT-4o (or GPT-5)
│   │   │
│   │   ├── azure_ops.py                 # Azure Ops Assistant
│   │   │   # - System prompt: Azure operations assistant
│   │   │   # - Tools: Azure MCP Server, Ops Assistant OpenAPI
│   │   │   # - Model: GPT-4o (or GPT-5)
│   │   │
│   │   ├── sql_agent.py                 # SQL Agent
│   │   │   # - System prompt: AdventureWorks data analyst
│   │   │   # - Tools: adventure-mcp
│   │   │   # - SQL query validation (block DROP, TRUNCATE, etc.)
│   │   │   # - Model: GPT-4o (or GPT-5)
│   │   │
│   │   ├── news_agent.py                # News Agent
│   │   │   # - System prompt: News analyst
│   │   │   # - Tools: Bing News grounding (Azure AI Foundry)
│   │   │   # - Model: GPT-4o (or GPT-5)
│   │   │
│   │   └── business_impact.py           # Business Impact Multi-Agent
│   │       # - System prompt: Business analyst, use A2A to orchestrate
│   │       # - Tools: News Agent (A2A), SQL Agent (A2A)
│   │       # - Orchestration: Dynamic (LLM-driven)
│   │       # - Hierarchical trace logging
│   │       # - Model: GPT-4o (or GPT-5)
│   │
│   ├── tools/                           # Tool integrations
│   │   ├── __init__.py
│   │   ├── mcp_client.py                # MCP client wrapper
│   │   │   # - MCPClient class
│   │   │   # - HTTP/SSE transport
│   │   │   # - Tool discovery: GET /mcp/tools
│   │   │   # - Tool invocation: POST /mcp/tools/{tool_name}
│   │   │   # - Schema caching (in-memory LRU)
│   │   │   # - Error handling and retries (3x with exp backoff)
│   │   │   # - Request/response logging
│   │   │
│   │   ├── mcp_servers/
│   │   │   ├── microsoft_learn.py       # Microsoft Learn MCP connector
│   │   │   │   # - Endpoint: https://learn.microsoft.com/api/mcp
│   │   │   │   # - Auth: None
│   │   │   │   # - Tools: search_docs, get_article, get_code_samples
│   │   │   │
│   │   │   ├── azure_mcp.py             # Azure MCP Server connector
│   │   │   │   # - Endpoint: http://localhost:3000 (sidecar)
│   │   │   │   # - Auth: None (Managed Identity in sidecar)
│   │   │   │   # - Tools: list_resources, get_resource, deploy_resource, query_logs
│   │   │   │
│   │   │   └── adventure_mcp.py         # adventure-mcp connector
│   │   │       # - Endpoint: https://mssqlmcp.azure-api.net
│   │   │       # - Auth: OAuth2 (client credentials)
│   │   │       # - Token management: acquire, cache, refresh
│   │   │       # - Tools: query_sql, get_schema, list_tables
│   │   │
│   │   ├── openapi_client.py            # OpenAPI tool connector
│   │   │   # - OpenAPIClient class
│   │   │   # - Parse OpenAPI spec (YAML or JSON)
│   │   │   # - Dynamic tool registration from spec
│   │   │   # - API key authentication (from Key Vault)
│   │   │   # - Request/response logging
│   │   │
│   │   └── bing_grounding.py            # Bing News grounding tool
│   │       # - BingNewsClient class
│   │       # - Azure AI Foundry Agent Service Bing grounding tool
│   │       # - Search parameters: market, freshness, category
│   │       # - Result formatting and summarization
│   │
│   ├── a2a/                             # A2A protocol implementation
│   │   ├── __init__.py
│   │   ├── server.py                    # A2A server endpoints
│   │   │   # - POST /a2a/{agent_id}
│   │   │   # - GET /.well-known/agent-card.json
│   │   │   # - A2A protocol message handling (JSON-RPC style)
│   │   │   # - Convert agent responses to A2A format
│   │   │   # - Trace A2A calls as child spans
│   │   │
│   │   ├── client.py                    # A2A client
│   │   │   # - A2AClient class
│   │   │   # - Agent discovery: GET /.well-known/agent-card.json
│   │   │   # - A2A message formatting
│   │   │   # - POST request to A2A endpoint
│   │   │   # - Response parsing
│   │   │   # - Error handling and fallback
│   │   │
│   │   └── cards.py                     # Agent card generation
│   │       # - generate_agent_card(agent) -> dict
│   │       # - Agent card schema: name, description, capabilities, endpoint
│   │
│   ├── api/                             # FastAPI routes
│   │   ├── __init__.py
│   │   ├── chat.py                      # Chat endpoints
│   │   │   # - POST /api/agents/{agent_id}/chat
│   │   │   # - Request: ChatRequest(message, thread_id?)
│   │   │   # - Response: SSE stream (tokens + traces)
│   │   │   # - Load agent from registry
│   │   │   # - Invoke agent.stream_response()
│   │   │   # - Emit SSE events: token, trace_start, trace_update, trace_end, done
│   │   │   # - Persist thread/run/steps to Cosmos DB
│   │   │
│   │   ├── agents.py                    # Agent management CRUD
│   │   │   # - GET /api/agents (list all)
│   │   │   # - GET /api/agents/{id} (get details)
│   │   │   # - POST /api/agents (create)
│   │   │   # - PUT /api/agents/{id} (update)
│   │   │   # - DELETE /api/agents/{id} (delete)
│   │   │   # - Validation: system prompt, model, tools
│   │   │   # - Reload agent registry on create/update
│   │   │
│   │   ├── auth.py                      # Authentication & authorization
│   │   │   # - JWT token validation middleware
│   │   │   # - extract_user_context(token) -> UserContext
│   │   │   # - Role-based authorization decorators: @require_admin, @require_user
│   │   │
│   │   └── health.py                    # Health check endpoint
│   │       # - GET /health
│   │       # - Check: Cosmos DB, Key Vault, Azure OpenAI, MCP servers
│   │       # - Return: {"status": "healthy", "dependencies": {...}}
│   │
│   ├── persistence/                     # Data access layer
│   │   ├── __init__.py
│   │   ├── cosmos_client.py             # Cosmos DB client wrapper
│   │   │   # - CosmosClient singleton
│   │   │   # - Connection string from Key Vault
│   │   │   # - Database/container references
│   │   │   # - Retry policies (3x with exp backoff)
│   │   │
│   │   ├── models.py                    # Pydantic models
│   │   │   # - Thread, Run, Step, ToolCall, Agent, Metric
│   │   │   # - Validation rules
│   │   │   # - Serialization to Cosmos DB format
│   │   │
│   │   └── repositories/
│   │       ├── threads.py               # Thread repository
│   │       │   # - create_thread(thread: Thread)
│   │       │   # - get_thread(thread_id: str)
│   │       │   # - list_threads(user_id: str, agent_id: str)
│   │       │   # - Partition key: /userId
│   │       │
│   │       ├── runs.py                  # Run repository
│   │       │   # - create_run(run: Run)
│   │       │   # - get_run(run_id: str)
│   │       │   # - list_runs(thread_id: str)
│   │       │   # - update_run_status(run_id, status)
│   │       │   # - Partition key: /threadId
│   │       │
│   │       ├── steps.py                 # Step repository
│   │       │   # - create_step(step: Step)
│   │       │   # - get_step(step_id: str)
│   │       │   # - list_steps(run_id: str)
│   │       │   # - Partition key: /runId
│   │       │
│   │       ├── tool_calls.py            # Tool call repository
│   │       │   # - create_tool_call(tool_call: ToolCall)
│   │       │   # - get_tool_call(tool_call_id: str)
│   │       │   # - list_tool_calls(step_id: str)
│   │       │   # - Partition key: /stepId
│   │       │
│   │       ├── agents_repo.py           # Agent repository
│   │       │   # - create_agent(agent: Agent)
│   │       │   # - get_agent(agent_id: str)
│   │       │   # - list_agents()
│   │       │   # - update_agent(agent_id, agent: Agent)
│   │       │   # - delete_agent(agent_id: str)
│   │       │   # - Partition key: /agentId
│   │       │
│   │       └── metrics.py               # Metrics repository
│   │           # - record_token_usage(run_id, tokens, cost)
│   │           # - get_usage_by_user(user_id, start_date, end_date)
│   │           # - get_usage_by_agent(agent_id, start_date, end_date)
│   │           # - get_daily_costs()
│   │           # - Partition key: /date
│   │
│   ├── observability/                   # Telemetry & tracing
│   │   ├── __init__.py
│   │   ├── otel_config.py               # OpenTelemetry configuration
│   │   │   # - Azure Monitor exporter
│   │   │   # - Trace provider with sampling (90% dev, 10% prod)
│   │   │   # - Metrics provider
│   │   │   # - Resource attributes (service.name, deployment.environment)
│   │   │
│   │   ├── middleware.py                # FastAPI telemetry middleware
│   │   │   # - Trace HTTP requests (method, path, status, duration)
│   │   │   # - Correlation ID propagation (X-Correlation-ID)
│   │   │   # - User context (user_id, tenant_id from JWT)
│   │   │   # - Request/response body logging (configurable)
│   │   │   # - PII redaction
│   │   │
│   │   └── cost_tracker.py              # Token usage & cost tracking
│   │       # - track_token_usage(run_id, model, input_tokens, output_tokens)
│   │       # - calculate_cost(model, tokens) -> float
│   │       # - Model pricing: GPT-4o ($0.005/1K input, $0.015/1K output)
│   │       # - Store in Cosmos DB metrics collection
│   │       # - Alert on threshold (>$100/day)
│   │
│   └── utils/                           # Shared utilities
│       ├── __init__.py
│       ├── secrets.py                   # Key Vault integration
│       │   # - get_secret(secret_name: str) -> str
│       │   # - DefaultAzureCredential (Azure CLI in dev, Managed Identity in prod)
│       │   # - Secret caching (in-memory, TTL: 1 hour)
│       │
│       └── pii_redaction.py             # PII scrubbing
│           # - redact_pii(text: str) -> str
│           # - Regex patterns: email, phone, SSN, credit card
│           # - Preserve structure (e.g., email: ***@***.com)
│
├── tests/
│   ├── unit/
│   │   ├── test_agents.py
│   │   ├── test_mcp_client.py
│   │   ├── test_a2a_client.py
│   │   └── test_repositories.py
│   ├── integration/
│   │   ├── test_chat_flow.py
│   │   ├── test_mcp_integrations.py
│   │   └── test_cosmos_persistence.py
│   └── e2e/
│       └── test_full_scenarios.py
│
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
└── .env.example
```

### Frontend Module Organization

```typescript
frontend/
├── src/
│   ├── main.tsx                         // App entry point
│   │   // - React.StrictMode wrapper
│   │   // - MSAL provider wrapper
│   │   // - Render <App />
│   │
│   ├── App.tsx                          // Root component
│   │   // - BrowserRouter
│   │   // - AuthProvider (MSAL)
│   │   // - ErrorBoundary
│   │   // - FluentProvider (theme)
│   │   // - Layout (Sidebar + TopNav + Outlet)
│   │   // - Routes
│   │
│   ├── config.ts                        // Frontend configuration
│   │   // - BACKEND_API_URL (env var)
│   │   // - ENTRA_CLIENT_ID (env var)
│   │   // - ENTRA_AUTHORITY (env var)
│   │   // - API_SCOPES
│   │
│   ├── pages/
│   │   ├── AgentsDirectory.tsx          // List/manage agents
│   │   │   // - Fetch agents via agentsService
│   │   │   // - Display agent cards (grid)
│   │   │   // - Filter/sort controls
│   │   │   // - "Create New Agent" button
│   │   │   // - Navigate to agent chat on card click
│   │   │
│   │   ├── AgentDetail.tsx              // Edit agent configuration (standalone page)
│   │   │   // - Fetch agent details
│   │   │   // - AgentEditor component
│   │   │   // - Save/cancel buttons
│   │   │
│   │   ├── AgentChat.tsx                // Generic agent chat template
│   │   │   // - useParams to get agent_id
│   │   │   // - Load agent config
│   │   │   // - MessageStream + TracePanel + InputBox
│   │   │   // - Settings button → AgentEditor modal
│   │   │   // - Export button
│   │   │
│   │   ├── SupportTriageChat.tsx        // Support Triage agent page
│   │   │   // - Extends AgentChat with agent_id="support-triage"
│   │   │
│   │   ├── AzureOpsChat.tsx             // Azure Ops Assistant page
│   │   │   // - Extends AgentChat with agent_id="azure-ops"
│   │   │
│   │   ├── SqlAgentChat.tsx             // SQL Agent page
│   │   │   // - Extends AgentChat with agent_id="sql-agent"
│   │   │
│   │   ├── NewsAgentChat.tsx            // News Agent page
│   │   │   // - Extends AgentChat with agent_id="news-agent"
│   │   │
│   │   └── BusinessImpactChat.tsx       // Business Impact Multi-Agent page
│   │       // - Extends AgentChat with agent_id="business-impact"
│   │       // - A2A CALLOUT BANNER: "This agent uses A2A protocol..."
│   │       // - Special styling for A2A traces (badge, color)
│   │
│   ├── components/
│   │   ├── chat/
│   │   │   ├── MessageStream.tsx        // Message list component
│   │   │   │   // - Props: messages[], isStreaming
│   │   │   │   // - Map messages to UserMessage | AssistantMessage
│   │   │   │   // - Markdown rendering (react-markdown)
│   │   │   │   // - Auto-scroll to bottom
│   │   │   │
│   │   │   ├── TracePanel.tsx           // Inline trace component
│   │   │   │   // - Props: trace (TraceEvent), isA2A
│   │   │   │   // - Collapsible Accordion (Fluent UI)
│   │   │   │   // - Header: tool name, status icon, latency, tokens
│   │   │   │   // - Body: input/output (truncated with "Show more")
│   │   │   │   // - Hierarchical display for A2A (nested TracePanel)
│   │   │   │   // - A2A badge/icon if isA2A=true
│   │   │   │
│   │   │   ├── InputBox.tsx             // Message input component
│   │   │   │   // - Props: onSendMessage, disabled
│   │   │   │   // - Textarea with auto-resize
│   │   │   │   // - Send button (disabled during streaming)
│   │   │   │   // - Shift+Enter: new line, Enter: send
│   │   │   │   // - Character count indicator
│   │   │   │
│   │   │   └── ExportButton.tsx         // CSV export button
│   │   │       // - Props: messages[], traces[]
│   │   │       // - Generate CSV: timestamp, role, content, metadata
│   │   │       // - Download as conversation-{agent}-{timestamp}.csv
│   │   │
│   │   ├── agents/
│   │   │   ├── AgentCard.tsx            // Agent card for directory
│   │   │   │   // - Props: agent (Agent)
│   │   │   │   // - Card: name, description, model, tool count
│   │   │   │   // - Click → navigate to agent chat
│   │   │   │
│   │   │   ├── AgentEditor.tsx          // Agent configuration modal
│   │   │   │   // - Props: agent, onSave, onCancel
│   │   │   │   // - Form: name, description, system prompt, model, tools
│   │   │   │   // - Validation before save
│   │   │   │   // - Call agentsService.updateAgent()
│   │   │   │
│   │   │   ├── ModelSelector.tsx        // Model dropdown
│   │   │   │   // - Props: selectedModel, models[], onChange
│   │   │   │   // - Dropdown (Fluent UI)
│   │   │   │   // - "Add New Model" button → modal
│   │   │   │
│   │   │   ├── ToolConfigurator.tsx     // Tool selection UI
│   │   │   │   // - Props: selectedTools[], availableTools[], onChange
│   │   │   │   // - Sections: MCP Servers, OpenAPI APIs, A2A Agents
│   │   │   │   // - Checkboxes for each tool
│   │   │   │   // - "Add Custom MCP Server" button → modal
│   │   │   │   // - "Add Custom OpenAPI API" button → modal
│   │   │   │
│   │   │   └── PromptEditor.tsx         // System prompt editor
│   │   │       // - Props: prompt, onChange
│   │   │       // - Textarea with syntax highlighting (optional)
│   │   │       // - Character count and token estimate
│   │   │
│   │   ├── navigation/
│   │   │   ├── Sidebar.tsx              // Left sidebar navigation
│   │   │   │   // - NavLinks to all agent pages
│   │   │   │   // - A2A badge next to Business Impact agent
│   │   │   │   // - User profile section (name, logout)
│   │   │   │
│   │   │   └── TopNav.tsx               // Top navigation bar
│   │   │       // - App title/logo
│   │   │       // - Breadcrumb navigation
│   │   │       // - Settings button (future)
│   │   │
│   │   └── common/
│   │       ├── Loading.tsx              // Loading spinner
│   │       └── ErrorBoundary.tsx        // Error boundary component
│   │
│   ├── services/
│   │   ├── api.ts                       // Axios instance
│   │   │   // - baseURL: BACKEND_API_URL
│   │   │   // - Interceptors: add Authorization header (MSAL token)
│   │   │   // - Interceptors: handle 401 (redirect to login)
│   │   │
│   │   ├── chatService.ts               // SSE streaming service
│   │   │   // - startChat(agentId, message, threadId?)
│   │   │   // - EventSource connection to /api/agents/{id}/chat
│   │   │   // - Event handlers: token, trace_start, trace_update, trace_end, done, error
│   │   │   // - Return: { onToken, onTrace, onDone, onError, close }
│   │   │
│   │   ├── agentsService.ts             // Agent CRUD service
│   │   │   // - listAgents() -> Agent[]
│   │   │   // - getAgent(agentId) -> Agent
│   │   │   // - createAgent(agent) -> Agent
│   │   │   // - updateAgent(agentId, agent) -> Agent
│   │   │   // - deleteAgent(agentId) -> void
│   │   │
│   │   └── authService.ts               // MSAL integration
│   │       // - msalConfig (clientId, authority, redirectUri)
│   │       // - login() -> void
│   │       // - logout() -> void
│   │       // - getAccessToken() -> Promise<string>
│   │       // - getUserProfile() -> UserProfile
│   │
│   ├── hooks/
│   │   ├── useChat.ts                   // Chat state management hook
│   │   │   // - State: messages[], traces[], isStreaming
│   │   │   // - sendMessage(message)
│   │   │   // - useEffect: setup SSE connection
│   │   │   // - Cleanup: close SSE on unmount
│   │   │
│   │   ├── useAgents.ts                 // Agents list hook
│   │   │   // - State: agents[], loading, error
│   │   │   // - fetchAgents()
│   │   │   // - createAgent(agent)
│   │   │   // - updateAgent(agentId, agent)
│   │   │   // - deleteAgent(agentId)
│   │   │
│   │   ├── useAuth.ts                   // Authentication hook
│   │   │   // - useMsal()
│   │   │   // - State: isAuthenticated, user, roles
│   │   │   // - login(), logout()
│   │   │   // - getAccessToken()
│   │   │
│   │   └── useSSE.ts                    // SSE connection hook
│   │       // - useEffect: create EventSource
│   │       // - Parse SSE events
│   │       // - Handle reconnection
│   │       // - Cleanup: close on unmount
│   │
│   ├── types/
│   │   ├── agent.ts                     // Agent types
│   │   │   // - Agent, AgentConfig, Tool, Model
│   │   │
│   │   ├── chat.ts                      // Chat types
│   │   │   // - Message, Thread, Run
│   │   │
│   │   └── trace.ts                     // Trace types
│   │       // - TraceEvent, ToolCall, A2ATrace
│   │
│   └── styles/
│       └── global.css                   // Global styles
│
├── tests/
│   └── playwright/
│       ├── auth.spec.ts
│       ├── chat.spec.ts
│       ├── agents.spec.ts
│       └── a2a.spec.ts
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── Dockerfile
└── .env.example
```

---

## State Model & Data Schema

### Cosmos DB Collections

**Database: `AgentState`**

#### Collection: `threads`
**Purpose**: Conversation threads (session-level, not persistent across sessions)

```json
{
  "id": "thread-uuid-1234",
  "userId": "user@example.com",
  "agentId": "support-triage",
  "createdAt": "2025-10-17T10:00:00Z",
  "lastMessageAt": "2025-10-17T10:15:00Z",
  "messageCount": 5,
  "status": "active",
  "ttl": 7776000  // 90 days in seconds
}
```
**Partition Key**: `/userId`  
**Indexes**: `agentId`, `createdAt`

#### Collection: `runs`
**Purpose**: Individual agent runs within a thread

```json
{
  "id": "run-uuid-5678",
  "threadId": "thread-uuid-1234",
  "agentId": "support-triage",
  "userId": "user@example.com",
  "status": "completed",  // queued, in_progress, completed, failed, cancelled
  "createdAt": "2025-10-17T10:10:00Z",
  "completedAt": "2025-10-17T10:10:15Z",
  "model": "gpt-4o",
  "inputTokens": 150,
  "outputTokens": 300,
  "totalTokens": 450,
  "cost": 0.00525,  // USD
  "latencyMs": 1500,
  "errorMessage": null,
  "ttl": 7776000
}
```
**Partition Key**: `/threadId`  
**Indexes**: `agentId`, `userId`, `createdAt`, `status`

#### Collection: `steps`
**Purpose**: Individual steps within a run (tool calls, agent reasoning)

```json
{
  "id": "step-uuid-9012",
  "runId": "run-uuid-5678",
  "threadId": "thread-uuid-1234",
  "type": "tool_call",  // tool_call, message, reasoning
  "status": "completed",  // in_progress, completed, failed
  "createdAt": "2025-10-17T10:10:02Z",
  "completedAt": "2025-10-17T10:10:05Z",
  "latencyMs": 3000,
  "ttl": 7776000
}
```
**Partition Key**: `/runId`  
**Indexes**: `threadId`, `createdAt`, `type`

#### Collection: `toolCalls`
**Purpose**: Detailed tool call information

```json
{
  "id": "toolcall-uuid-3456",
  "stepId": "step-uuid-9012",
  "runId": "run-uuid-5678",
  "toolName": "search_docs",
  "toolType": "mcp",  // mcp, openapi, a2a
  "mcpServer": "microsoft-learn",  // if toolType=mcp
  "a2aAgent": null,  // if toolType=a2a, agent name
  "input": {
    "query": "How to reset Azure AD password"
  },
  "output": {
    "results": [
      {"title": "Reset user password", "url": "https://learn.microsoft.com/..."}
    ]
  },
  "inputHash": "sha256-...",  // for caching
  "outputHash": "sha256-...",
  "status": "completed",  // in_progress, completed, failed
  "createdAt": "2025-10-17T10:10:02Z",
  "completedAt": "2025-10-17T10:10:05Z",
  "latencyMs": 3000,
  "errorMessage": null,
  "cached": false,
  "ttl": 7776000
}
```
**Partition Key**: `/stepId`  
**Indexes**: `runId`, `toolName`, `mcpServer`, `a2aAgent`, `createdAt`

#### Collection: `agents`
**Purpose**: Agent configurations (persistent)

```json
{
  "id": "support-triage",
  "name": "Support Triage Agent",
  "description": "Microsoft product support triage specialist",
  "systemPrompt": "You are a Microsoft product support triage specialist...",
  "model": "gpt-4o",
  "deployment": "gpt-4o-deployment-eastus",
  "tools": [
    {
      "type": "mcp",
      "server": "microsoft-learn",
      "enabled": true
    },
    {
      "type": "openapi",
      "api": "support-triage-api",
      "enabled": true
    }
  ],
  "settings": {
    "temperature": 0.7,
    "maxTokens": 2000,
    "topP": 0.9
  },
  "createdAt": "2025-10-17T09:00:00Z",
  "updatedAt": "2025-10-17T09:00:00Z",
  "createdBy": "admin@example.com",
  "status": "active",  // active, inactive
  "a2aEndpoint": "/a2a/support-triage"
}
```
**Partition Key**: `/id`  
**Indexes**: `status`, `createdAt`

**Database: `Observability`**

#### Collection: `metrics`
**Purpose**: Token usage, costs, and performance metrics

```json
{
  "id": "metric-uuid-7890",
  "date": "2025-10-17",
  "userId": "user@example.com",
  "agentId": "support-triage",
  "runId": "run-uuid-5678",
  "model": "gpt-4o",
  "inputTokens": 150,
  "outputTokens": 300,
  "totalTokens": 450,
  "cost": 0.00525,
  "latencyMs": 1500,
  "timestamp": "2025-10-17T10:10:15Z",
  "ttl": 15552000  // 180 days
}
```
**Partition Key**: `/date`  
**Indexes**: `userId`, `agentId`, `timestamp`

#### Collection: `audit`
**Purpose**: Audit logs for admin actions (persistent)

```json
{
  "id": "audit-uuid-1111",
  "action": "agent_updated",  // agent_created, agent_updated, agent_deleted, secret_accessed
  "userId": "admin@example.com",
  "agentId": "support-triage",
  "timestamp": "2025-10-17T10:00:00Z",
  "details": {
    "field": "systemPrompt",
    "oldValue": "...",
    "newValue": "..."
  },
  "ipAddress": "1.2.3.4",
  "userAgent": "Mozilla/5.0...",
  "ttl": 31536000  // 365 days
}
```
**Partition Key**: `/userId`  
**Indexes**: `action`, `timestamp`, `agentId`

---

## Application Flow

### End-to-End Chat Flow

```
1. USER ACTION: User opens "Support Triage Agent" page
   │
   ├─> Frontend: GET /api/agents/support-triage
   │   └─> Backend: Load agent config from Cosmos DB (agents collection)
   │       └─> Return: Agent config (name, system prompt, tools, model)
   │
   └─> Frontend: Render chat UI (empty message list)

2. USER ACTION: User types "How do I reset my Azure AD password?" and clicks Send
   │
   └─> Frontend: POST /api/agents/support-triage/chat
       Request Body: { "message": "How do I reset my Azure AD password?" }
       Headers: Authorization: Bearer <access_token>

3. BACKEND: Receive chat request
   │
   ├─> Validate JWT token (auth.py)
   │   └─> Extract user context: userId, roles
   │
   ├─> Load agent from registry (registry.py)
   │   └─> Get agent instance (cached or create new)
   │
   ├─> Create thread (if new conversation)
   │   └─> Cosmos DB: INSERT into threads collection
   │       └─> threadId = "thread-uuid-1234"
   │
   ├─> Create run
   │   └─> Cosmos DB: INSERT into runs collection
   │       └─> runId = "run-uuid-5678", status = "in_progress"
   │
   └─> Start SSE stream (api/chat.py)
       └─> Return: text/event-stream

4. AGENT EXECUTION: Agent Framework processes message
   │
   ├─> Agent Framework: Decide which tools to call
   │   └─> Decision: "Use Microsoft Learn MCP to search docs"
   │
   ├─> TOOL CALL 1: Microsoft Learn MCP
   │   │
   │   ├─> Emit SSE event: trace_start
   │   │   data: {"type":"trace_start","tool":"search_docs","mcp_server":"microsoft-learn","timestamp":"..."}
   │   │
   │   ├─> MCP Client: POST https://learn.microsoft.com/api/mcp/tools/search_docs
   │   │   Body: {"query": "reset Azure AD password"}
   │   │
   │   ├─> Microsoft Learn MCP: Search documentation
   │   │   └─> Return: [{"title":"Reset user password","url":"..."}]
   │   │
   │   ├─> Emit SSE event: trace_end
   │   │   data: {"type":"trace_end","tool":"search_docs","latency_ms":3000,"tokens":0,"output_preview":"Found 3 articles"}
   │   │
   │   └─> Cosmos DB: INSERT into steps, toolCalls collections
   │       └─> stepId = "step-uuid-9012", toolCallId = "toolcall-uuid-3456"
   │
   ├─> Agent Framework: Generate response based on tool results
   │   │
   │   ├─> Azure OpenAI: POST /chat/completions (streaming)
   │   │   System Prompt: "You are a Microsoft product support triage specialist..."
   │   │   Tools: [Microsoft Learn MCP results]
   │   │   User Message: "How do I reset my Azure AD password?"
   │   │
   │   └─> Azure OpenAI: Stream tokens
   │       └─> For each token:
   │           └─> Emit SSE event: token
   │               data: {"type":"token","content":"To"}
   │               data: {"type":"token","content":" reset"}
   │               data: {"type":"token","content":" your"}
   │               ...
   │
   └─> Complete run
       ├─> Update run status: "completed"
       ├─> Track token usage and cost
       ├─> Cosmos DB: UPDATE runs collection
       └─> Emit SSE event: done
           data: {"type":"done","run_id":"run-uuid-5678"}

5. FRONTEND: Receive SSE events
   │
   ├─> On "token" event:
   │   └─> Append token to current message
   │       └─> Re-render MessageStream (incremental update)
   │
   ├─> On "trace_start" event:
   │   └─> Add trace block to message stream (status: "in_progress")
   │       └─> Re-render TracePanel (loading spinner)
   │
   ├─> On "trace_end" event:
   │   └─> Update trace block (status: "completed", latency, output)
   │       └─> Re-render TracePanel (show results)
   │
   └─> On "done" event:
       └─> Stop streaming indicator
           └─> Enable input box for next message

6. USER ACTION: User reviews response and trace panel
   │
   ├─> Trace Panel shows:
   │   └─> [MCP] search_docs (microsoft-learn) ✓ 3.0s
   │       Input: {"query": "reset Azure AD password"}
   │       Output: Found 3 articles (expandable)
   │
   └─> Message shows: "To reset your Azure AD password, follow these steps..."
```

### Business Impact Multi-Agent Flow (A2A)

```
1. USER ACTION: User opens "Business Impact Agent" page
   │
   └─> Frontend: Display A2A callout banner
       "⚡ This agent uses Agent-to-Agent (A2A) protocol to orchestrate
        News Agent and SQL Agent for comprehensive analysis."

2. USER ACTION: User types "How did AI news impact our sales in Q3?"
   │
   └─> Frontend: POST /api/agents/business-impact/chat

3. BACKEND: Business Impact Agent processes message
   │
   ├─> Agent Framework: Decide to call News Agent and SQL Agent (A2A)
   │
   ├─> TOOL CALL 1: News Agent (A2A)
   │   │
   │   ├─> Emit SSE event: trace_start
   │   │   data: {"type":"trace_start","tool":"news_agent","tool_type":"a2a","a2a_agent":"news-agent","timestamp":"..."}
   │   │
   │   ├─> A2A Client: Discover News Agent
   │   │   └─> GET http://localhost:8000/.well-known/agent-card.json?agent=news-agent
   │   │       └─> Return: {"name":"News Agent","endpoint":"/a2a/news-agent"}
   │   │
   │   ├─> A2A Client: Call News Agent
   │   │   └─> POST http://localhost:8000/a2a/news-agent
   │   │       Body: {"message": "Find recent AI news"}
   │   │       └─> News Agent executes:
   │   │           ├─> Call Bing News grounding tool
   │   │           └─> Return: {"response": "Found 5 AI news articles..."}
   │   │
   │   ├─> Emit SSE event: trace_end
   │   │   data: {"type":"trace_end","tool":"news_agent","latency_ms":2000,"a2a_metadata":{"agent":"news-agent","sub_tools":["bing_news"]}}
   │   │
   │   └─> Cosmos DB: INSERT into toolCalls (toolType="a2a", a2aAgent="news-agent")
   │
   ├─> TOOL CALL 2: SQL Agent (A2A)
   │   │
   │   ├─> Emit SSE event: trace_start
   │   │   data: {"type":"trace_start","tool":"sql_agent","tool_type":"a2a","a2a_agent":"sql-agent","timestamp":"..."}
   │   │
   │   ├─> A2A Client: Discover SQL Agent
   │   │   └─> GET /.well-known/agent-card.json?agent=sql-agent
   │   │
   │   ├─> A2A Client: Call SQL Agent
   │   │   └─> POST /a2a/sql-agent
   │   │       Body: {"message": "Get Q3 sales data"}
   │   │       └─> SQL Agent executes:
   │   │           ├─> Call adventure-mcp (query_sql)
   │   │           └─> Return: {"response": "Q3 sales: $5.2M, up 15% YoY"}
   │   │
   │   ├─> Emit SSE event: trace_end
   │   │   data: {"type":"trace_end","tool":"sql_agent","latency_ms":4000,"a2a_metadata":{"agent":"sql-agent","sub_tools":["adventure-mcp"]}}
   │   │
   │   └─> Cosmos DB: INSERT into toolCalls (toolType="a2a", a2aAgent="sql-agent")
   │
   └─> Agent Framework: Synthesize results
       ├─> Azure OpenAI: Generate final response
       │   Input: News results + SQL results
       │   Output: "Recent AI announcements correlated with 15% sales increase..."
       │
       └─> Stream tokens to frontend (SSE)

4. FRONTEND: Render hierarchical traces
   │
   └─> TracePanel displays:
       ├─ [A2A] Business Impact Agent ⚡
       │  ├─ [A2A] News Agent ✓ 2.0s
       │  │  └─ [MCP] bing_news (Azure AI Foundry) ✓ 1.5s
       │  │     Output: 5 articles found
       │  ├─ [A2A] SQL Agent ✓ 4.0s
       │  │  └─ [MCP] query_sql (adventure-mcp) ✓ 3.8s
       │  │     Output: Q3 sales: $5.2M (+15% YoY)
       │  └─ Synthesis ✓ 1.0s
       │     Output: Correlation analysis complete
```

---

## MCP Integration Patterns

### Pattern 1: Microsoft Learn MCP (Public, No Auth)

```python
# tools/mcp_servers/microsoft_learn.py

from tools.mcp_client import MCPClient

class MicrosoftLearnMCP:
    def __init__(self):
        self.client = MCPClient(
            endpoint="https://learn.microsoft.com/api/mcp",
            auth=None
        )
        self.tools = None
    
    async def initialize(self):
        """Discover available tools"""
        self.tools = await self.client.discover_tools()
        # Expected tools: search_docs, get_article, get_code_samples
    
    async def search_docs(self, query: str) -> dict:
        """Search Microsoft Learn documentation"""
        return await self.client.call_tool(
            tool_name="search_docs",
            parameters={"query": query}
        )
```

### Pattern 2: adventure-mcp (OAuth2)

```python
# tools/mcp_servers/adventure_mcp.py

from tools.mcp_client import MCPClient
from utils.secrets import get_secret
import httpx

class AdventureMCP:
    def __init__(self):
        self.endpoint = "https://mssqlmcp.azure-api.net"
        self.client_id = get_secret("adventure-mcp-client-id")
        self.client_secret = get_secret("adventure-mcp-client-secret")
        self.token_url = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        self.access_token = None
        self.token_expiry = None
        self.client = None
    
    async def get_access_token(self) -> str:
        """Acquire or refresh OAuth2 token"""
        if self.access_token and self.token_expiry > datetime.now():
            return self.access_token
        
        # Request new token
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://mssqlmcp.azure-api.net/.default"
                }
            )
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"] - 300)
            return self.access_token
    
    async def initialize(self):
        """Initialize MCP client with OAuth2 token"""
        token = await self.get_access_token()
        self.client = MCPClient(
            endpoint=self.endpoint,
            auth={"type": "bearer", "token": token}
        )
        self.tools = await self.client.discover_tools()
    
    async def query_sql(self, query: str) -> dict:
        """Execute SQL query via adventure-mcp"""
        # Validate query (no DROP, TRUNCATE, etc.)
        if any(keyword in query.upper() for keyword in ["DROP", "TRUNCATE", "DELETE FROM"]):
            raise ValueError("Destructive SQL operations not allowed")
        
        return await self.client.call_tool(
            tool_name="query_sql",
            parameters={"query": query}
        )
```

### Pattern 3: Azure MCP Server (Sidecar, Localhost)

```python
# tools/mcp_servers/azure_mcp.py

from tools.mcp_client import MCPClient

class AzureMCP:
    def __init__(self):
        # Sidecar runs on localhost:3000 (same pod)
        self.client = MCPClient(
            endpoint="http://localhost:3000",
            auth=None  # Managed Identity handled by sidecar
        )
        self.tools = None
    
    async def initialize(self):
        """Discover available Azure MCP tools"""
        self.tools = await self.client.discover_tools()
        # Expected tools: list_resources, get_resource, deploy_resource, query_logs
    
    async def list_resources(self, resource_type: str, resource_group: str = None) -> dict:
        """List Azure resources"""
        return await self.client.call_tool(
            tool_name="list_resources",
            parameters={
                "resource_type": resource_type,
                "resource_group": resource_group
            }
        )
```

---

## A2A Protocol Implementation

### A2A Server (Expose Agent)

```python
# a2a/server.py

from fastapi import APIRouter, Request
from agents.registry import agent_registry
from a2a.cards import generate_agent_card

router = APIRouter(prefix="/a2a")

@router.get("/.well-known/agent-card.json")
async def get_agent_card(agent: str):
    """Serve agent card for A2A discovery"""
    agent_instance = agent_registry.get_agent(agent)
    if not agent_instance:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return generate_agent_card(agent_instance)

@router.post("/{agent_id}")
async def invoke_agent_a2a(agent_id: str, request: Request):
    """A2A endpoint for agent invocation"""
    body = await request.json()
    message = body.get("message")
    
    # Load agent
    agent = agent_registry.get_agent(agent_id)
    
    # Create span for A2A call (child of caller's span)
    with tracer.start_as_current_span(f"a2a.{agent_id}") as span:
        span.set_attribute("a2a.agent", agent_id)
        span.set_attribute("a2a.message", message[:100])
        
        # Invoke agent
        response = await agent.run(message)
        
        span.set_attribute("a2a.response_length", len(response))
    
    # Return A2A format response
    return {
        "agent": agent_id,
        "response": response,
        "metadata": {
            "model": agent.model,
            "tokens": agent.last_run_tokens
        }
    }
```

### A2A Client (Call Agent)

```python
# a2a/client.py

import httpx
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class A2AClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.http_client = httpx.AsyncClient()
    
    async def discover_agent(self, agent_id: str) -> dict:
        """Discover agent via agent card"""
        url = f"{self.base_url}/.well-known/agent-card.json?agent={agent_id}"
        response = await self.http_client.get(url)
        return response.json()
    
    async def call_agent(self, agent_id: str, message: str) -> dict:
        """Call agent via A2A protocol"""
        # Discover agent first (cache this in production)
        agent_card = await self.discover_agent(agent_id)
        endpoint = agent_card["endpoint"]
        
        # Create span for A2A call
        with tracer.start_as_current_span(f"a2a.call.{agent_id}") as span:
            span.set_attribute("a2a.agent", agent_id)
            span.set_attribute("a2a.endpoint", endpoint)
            
            # Make A2A request
            response = await self.http_client.post(
                f"{self.base_url}{endpoint}",
                json={"message": message}
            )
            
            result = response.json()
            span.set_attribute("a2a.response_length", len(result.get("response", "")))
            
            return result
```

---

## Streaming Architecture

### SSE Event Types

```typescript
// frontend/src/types/streaming.ts

export type SSEEvent = 
  | TokenEvent 
  | TraceStartEvent 
  | TraceUpdateEvent 
  | TraceEndEvent 
  | DoneEvent 
  | ErrorEvent;

export interface TokenEvent {
  type: "token";
  content: string;
}

export interface TraceStartEvent {
  type: "trace_start";
  trace_id: string;
  tool: string;
  tool_type: "mcp" | "openapi" | "a2a";
  mcp_server?: string;
  a2a_agent?: string;
  timestamp: string;
}

export interface TraceUpdateEvent {
  type: "trace_update";
  trace_id: string;
  status: "in_progress" | "waiting";
  message?: string;
}

export interface TraceEndEvent {
  type: "trace_end";
  trace_id: string;
  tool: string;
  tool_type: "mcp" | "openapi" | "a2a";
  status: "completed" | "failed";
  latency_ms: number;
  tokens?: {
    input: number;
    output: number;
    total: number;
  };
  input_preview?: string;
  output_preview?: string;
  a2a_metadata?: {
    agent: string;
    sub_tools: string[];
  };
  error_message?: string;
}

export interface DoneEvent {
  type: "done";
  run_id: string;
}

export interface ErrorEvent {
  type: "error";
  message: string;
  code?: string;
}
```

### Backend SSE Implementation

```python
# api/chat.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/agents")

@router.post("/{agent_id}/chat")
async def chat(agent_id: str, request: ChatRequest, user: User = Depends(get_current_user)):
    """Chat with agent (SSE streaming)"""
    
    agent = agent_registry.get_agent(agent_id)
    
    async def event_generator():
        try:
            # Create thread and run
            thread_id = request.thread_id or create_thread(user.id, agent_id)
            run_id = create_run(thread_id, agent_id, user.id)
            
            # Stream agent response
            async for event in agent.stream_response(request.message, thread_id):
                if event["type"] == "token":
                    yield {
                        "event": "message",
                        "data": json.dumps({"type": "token", "content": event["content"]})
                    }
                
                elif event["type"] == "trace_start":
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "trace_start",
                            "trace_id": event["trace_id"],
                            "tool": event["tool"],
                            "tool_type": event["tool_type"],
                            "mcp_server": event.get("mcp_server"),
                            "a2a_agent": event.get("a2a_agent"),
                            "timestamp": event["timestamp"]
                        })
                    }
                
                elif event["type"] == "trace_end":
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "trace_end",
                            "trace_id": event["trace_id"],
                            "tool": event["tool"],
                            "status": event["status"],
                            "latency_ms": event["latency_ms"],
                            "tokens": event.get("tokens"),
                            "a2a_metadata": event.get("a2a_metadata")
                        })
                    }
            
            # Complete run
            complete_run(run_id)
            
            yield {
                "event": "message",
                "data": json.dumps({"type": "done", "run_id": run_id})
            }
        
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            yield {
                "event": "message",
                "data": json.dumps({"type": "error", "message": str(e)})
            }
    
    return EventSourceResponse(event_generator())
```

---

*End of Part 2. Continue to `02-architecture-part3.md` for networking, security, scalability, and operational details.*
