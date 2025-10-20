# Project Plan: AI Agents Demo - Part 2

**Continuation of Phase 2 and Phase 3**

---

## Phase 2: Agent Implementation & Tool Integration

**Objective:** Implement all 5 MVP agents, MCP integrations, OpenAPI tools, A2A protocol, and streaming capabilities.

### Detailed Checklist

#### 2.1 MCP Client Infrastructure
- [ ] Implement MCP client wrapper (`tools/mcp_client.py`)
  - [ ] HTTP/SSE transport for remote MCP servers
  - [ ] Tool discovery and schema caching
  - [ ] Error handling and retries
  - [ ] Request/response logging for observability
- [ ] Implement Microsoft Learn MCP connector (`tools/mcp_servers/microsoft_learn.py`)
  - [ ] Endpoint: `https://learn.microsoft.com/api/mcp`
  - [ ] No authentication required
  - [ ] Tool: `search_docs`, `get_article`, `get_code_samples`
  - [ ] Test with sample queries
- [ ] Implement adventure-mcp connector (`tools/mcp_servers/adventure_mcp.py`)
  - [ ] Endpoint: `https://mssqlmcp.azure-api.net`
  - [ ] OAuth2 authentication flow
  - [ ] Token acquisition and refresh from Key Vault
  - [ ] Tools: `query_sql`, `get_schema`, `list_tables`
  - [ ] Test with AdventureWorks sample queries
- [ ] Implement Azure MCP client wrapper (`tools/mcp_servers/azure_mcp.py`)
  - [ ] Connect to sidecar at `http://localhost:3000` (local) or sidecar URL (production)
  - [ ] Tools: `list_resources`, `get_resource`, `deploy_resource`, `query_logs`
  - [ ] Managed Identity authentication (handled by sidecar)
  - [ ] Test with resource listing and log queries

#### 2.2 OpenAPI Tool Integration
- [ ] Create placeholder OpenAPI specs
  - [ ] `openapi/support-triage-api.yaml`
    - [ ] Endpoints: `/api/tickets/search`, `/api/tickets/{id}`, `/api/kb/search`
    - [ ] Mock responses with sample ticket data
  - [ ] `openapi/ops-assistant-api.yaml`
    - [ ] Endpoints: `/api/deployments/status`, `/api/deployments/rollback`
    - [ ] Mock responses with deployment status
- [ ] Deploy OpenAPI specs to Azure API Management (`infra/modules/apim.bicep`)
  - [ ] Create API definitions from OpenAPI specs
  - [ ] Configure mock backend policies
  - [ ] Set rate limiting (100 requests/min per user)
  - [ ] Set caching policy (5 min for KB searches)
  - [ ] Generate API keys and store in Key Vault
- [ ] Implement OpenAPI client (`tools/openapi_client.py`)
  - [ ] Generic OpenAPI spec parser
  - [ ] Dynamic tool registration from spec
  - [ ] API key authentication from Key Vault
  - [ ] Request/response logging
- [ ] Test OpenAPI tools with mock responses

#### 2.3 Bing News Grounding Tool
- [ ] Implement Bing News integration (`tools/bing_grounding.py`)
  - [ ] Use Azure AI Foundry Agent Service Bing grounding tool
  - [ ] Configure search parameters (market, freshness, category)
  - [ ] Result formatting and summarization
  - [ ] Test with current events queries
- [ ] Deploy Bing Search resource in Bicep (`infra/modules/openai.bicep`)
  - [ ] Bing Search API v7
  - [ ] Store API key in Key Vault
  - [ ] Private endpoint if available

#### 2.4 Agent Base Implementation
- [ ] Create base agent class (`agents/base.py`)
  - [ ] Inherit from Agent Framework SDK base class
  - [ ] Common methods: `initialize()`, `run()`, `stream_response()`
  - [ ] Tool registration interface
  - [ ] Memory management (sliding window, last 20 messages)
  - [ ] Token counting and budget enforcement
- [ ] Implement agent registry (`agents/registry.py`)
  - [ ] Agent factory pattern
  - [ ] Load agent configurations from Cosmos DB
  - [ ] Dynamic agent instantiation
  - [ ] Agent lifecycle management (start, stop, reload)

#### 2.5 Support Triage Agent
- [ ] Implement Support Triage agent (`agents/support_triage.py`)
  - [ ] System prompt: "You are a Microsoft product support triage specialist. Use Microsoft Learn documentation to ground your responses and the Support Triage API to search for similar tickets."
  - [ ] Tools:
    - [ ] Microsoft Learn MCP: `search_docs`, `get_article`
    - [ ] OpenAPI: Support Triage API
  - [ ] Model: GPT-4o (or GPT-5 if available)
  - [ ] Sliding window memory (20 messages)
- [ ] Create A2A endpoint for Support Triage (`a2a/server.py`)
  - [ ] Endpoint: `/a2a/support-triage`
  - [ ] Agent card: `/.well-known/agent-card.json`
- [ ] Test Support Triage agent with sample queries
  - [ ] "How do I troubleshoot Azure AD authentication issues?"
  - [ ] "Find similar tickets about Azure Storage connection errors"

#### 2.6 Azure Ops Assistant Agent
- [ ] Implement Azure Ops Assistant (`agents/azure_ops.py`)
  - [ ] System prompt: "You are an Azure operations assistant. Use Azure MCP tools to inspect, diagnose, and manage Azure resources. Provide clear explanations and recommendations."
  - [ ] Tools:
    - [ ] Azure MCP: `list_resources`, `get_resource`, `deploy_resource`, `query_logs`
    - [ ] OpenAPI: Ops Assistant API
  - [ ] Model: GPT-4o (or GPT-5 if available)
  - [ ] Sliding window memory (20 messages)
- [ ] Create A2A endpoint for Azure Ops Assistant (`a2a/server.py`)
  - [ ] Endpoint: `/a2a/azure-ops`
  - [ ] Agent card: `/.well-known/agent-card.json`
- [ ] Test Azure Ops Assistant with sample queries
  - [ ] "List all Container Apps in the demo resource group"
  - [ ] "Show me the logs for the backend Container App from the last hour"
  - [ ] "What is the current RU consumption of the Cosmos DB account?"

#### 2.7 SQL Agent
- [ ] Implement SQL Agent (`agents/sql_agent.py`)
  - [ ] System prompt: "You are a data analyst with access to the AdventureWorks database. Use SQL queries to answer questions about customers, products, sales, and orders. Always explain your queries and results clearly."
  - [ ] Tools:
    - [ ] adventure-mcp: `query_sql`, `get_schema`, `list_tables`
  - [ ] Model: GPT-4o (or GPT-5 if available)
  - [ ] Sliding window memory (20 messages)
  - [ ] SQL query validation (prevent DROP, TRUNCATE, etc.)
- [ ] Create A2A endpoint for SQL Agent (`a2a/server.py`)
  - [ ] Endpoint: `/a2a/sql-agent`
  - [ ] Agent card: `/.well-known/agent-card.json`
- [ ] Test SQL Agent with sample queries
  - [ ] "What are the top 5 customers by total sales?"
  - [ ] "Show me the product categories with the highest revenue"
  - [ ] "How many orders were placed in Q1 2024?"

#### 2.8 News Agent
- [ ] Implement News Agent (`agents/news_agent.py`)
  - [ ] System prompt: "You are a news analyst. Use Bing News Search to find recent news articles about companies, industries, or topics. Summarize key findings and trends."
  - [ ] Tools:
    - [ ] Bing News grounding tool
  - [ ] Model: GPT-4o (or GPT-5 if available)
  - [ ] Sliding window memory (20 messages)
- [ ] Create A2A endpoint for News Agent (`a2a/server.py`)
  - [ ] Endpoint: `/a2a/news-agent`
  - [ ] Agent card: `/.well-known/agent-card.json`
- [ ] Test News Agent with sample queries
  - [ ] "What is the latest news about Microsoft Azure?"
  - [ ] "Find recent articles about AI and automation in retail"
  - [ ] "What are the top tech news stories this week?"

#### 2.9 Business Impact Multi-Agent (A2A Orchestration)
- [ ] Implement A2A client (`a2a/client.py`)
  - [ ] Agent discovery via agent card (`.well-known/agent-card.json`)
  - [ ] A2A protocol message formatting
  - [ ] Request/response handling
  - [ ] Error handling and fallback
- [ ] Implement Business Impact agent (`agents/business_impact.py`)
  - [ ] System prompt: "You are a business analyst. Use the News Agent to find recent news about a company or industry, and the SQL Agent to analyze business metrics from the AdventureWorks database. Correlate news events with business performance and provide insights."
  - [ ] Tools (A2A protocol):
    - [ ] News Agent (via A2A)
    - [ ] SQL Agent (via A2A)
  - [ ] Orchestration: Dynamic (LLM-driven tool calling)
  - [ ] Model: GPT-4o (or GPT-5 if available)
  - [ ] Sliding window memory (20 messages)
- [ ] Create A2A endpoint for Business Impact agent (`a2a/server.py`)
  - [ ] Endpoint: `/a2a/business-impact`
  - [ ] Agent card: `/.well-known/agent-card.json`
- [ ] Implement hierarchical trace logging for A2A calls
  - [ ] Parent trace: Business Impact agent
  - [ ] Child traces: News Agent call, SQL Agent call
  - [ ] Trace metadata: agent name, A2A endpoint, latency, token usage
- [ ] Test Business Impact agent with sample queries
  - [ ] "How did Microsoft's latest AI announcements impact our sales?"
  - [ ] "Find news about supply chain disruptions and analyze impact on our orders"
  - [ ] "What is the correlation between tech news trends and our product sales?"

#### 2.10 Agent Chat API & Streaming
- [ ] Implement chat endpoint (`api/chat.py`)
  - [ ] POST `/api/agents/{agent_id}/chat`
  - [ ] Request body: `{ "message": "...", "thread_id": "..." }`
  - [ ] SSE streaming response
  - [ ] Trace events interleaved with token stream
- [ ] Implement SSE streaming logic
  - [ ] Event types: `token`, `trace_start`, `trace_update`, `trace_end`, `done`, `error`
  - [ ] Buffering and flush strategies
  - [ ] Connection keep-alive
- [ ] Implement trace event generation
  - [ ] Tool call start: `{ "type": "trace_start", "tool": "...", "input": "...", "timestamp": "..." }`
  - [ ] Tool call end: `{ "type": "trace_end", "tool": "...", "output": "...", "latency_ms": ..., "tokens": ... }`
  - [ ] Nested traces for A2A calls
- [ ] Persist threads, runs, steps to Cosmos DB
  - [ ] Repositories: `threads.py`, `runs.py`, `steps.py`, `tool_calls.py`
  - [ ] Models: `Thread`, `Run`, `Step`, `ToolCall` (Pydantic)
- [ ] Test streaming end-to-end
  - [ ] Start chat, send message, verify SSE stream
  - [ ] Verify trace events are sent in real-time
  - [ ] Verify final response and persistence to Cosmos DB

#### 2.11 Agent Management API
- [ ] Implement agent CRUD endpoints (`api/agents.py`)
  - [ ] GET `/api/agents` - List all agents
  - [ ] GET `/api/agents/{agent_id}` - Get agent details
  - [ ] POST `/api/agents` - Create new agent
  - [ ] PUT `/api/agents/{agent_id}` - Update agent
  - [ ] DELETE `/api/agents/{agent_id}` - Delete agent
- [ ] Implement agent validation
  - [ ] System prompt not empty
  - [ ] Model deployment exists
  - [ ] Tools are valid (MCP server reachable, OpenAPI spec valid)
- [ ] Implement agent deployment
  - [ ] Save agent config to Cosmos DB
  - [ ] Reload agent registry
  - [ ] Create A2A endpoint dynamically
  - [ ] Generate agent card
- [ ] Seed default 5 agents on startup (`scripts/seed-agents.py`)
  - [ ] Check if agents exist in Cosmos DB
  - [ ] Create default agent configs if missing
  - [ ] Run on container startup (init container or startup script)

### Acceptance Criteria (Phase 2)

- [ ] All 5 agents are implemented and functional
- [ ] All MCP servers are integrated and accessible
- [ ] OpenAPI tools are deployed to APIM and callable
- [ ] Bing News grounding tool works with News Agent
- [ ] A2A protocol is implemented for agent-to-agent communication
- [ ] Business Impact agent successfully orchestrates News and SQL agents via A2A
- [ ] Chat API streams tokens and trace events in real-time
- [ ] Threads, runs, steps, and tool calls are persisted to Cosmos DB
- [ ] Agent management API supports CRUD operations
- [ ] Default 5 agents are seeded on first run
- [ ] Hierarchical traces are generated for A2A calls

### Test Plan (Phase 2)

#### Unit Tests
- [ ] Test MCP client tool discovery
- [ ] Test OpenAPI client spec parsing
- [ ] Test agent base class methods
- [ ] Test sliding window memory management
- [ ] Test A2A client message formatting
- [ ] Test trace event generation

#### Integration Tests
- [ ] Test Microsoft Learn MCP with live endpoint
- [ ] Test adventure-mcp with OAuth2 authentication
- [ ] Test Azure MCP with managed identity
- [ ] Test OpenAPI tools with APIM mock backends
- [ ] Test Bing News grounding with live API
- [ ] Test each agent with sample queries
- [ ] Test A2A calls between Business Impact, News, and SQL agents
- [ ] Test SSE streaming with chat endpoint
- [ ] Test Cosmos DB persistence for all entities

#### E2E Tests
- [ ] Start a chat with Support Triage agent
- [ ] Send a message requiring Microsoft Learn lookup
- [ ] Verify SSE stream returns tokens and traces
- [ ] Verify response is persisted to Cosmos DB
- [ ] Repeat for all 5 agents
- [ ] Test Business Impact agent with multi-step A2A orchestration
- [ ] Verify hierarchical traces appear in real-time
- [ ] Test agent creation, update, and deletion via management API

#### Performance Tests
- [ ] Test concurrent chat sessions (10 users, 5 agents)
- [ ] Measure token latency (time to first token, total response time)
- [ ] Measure MCP tool call latency
- [ ] Measure A2A call latency
- [ ] Measure Cosmos DB write latency
- [ ] Verify no memory leaks with long-running sessions

---

## Phase 3: Frontend Development & User Experience

**Objective:** Build the React frontend with chat UI, trace visualization, and agent management pages.

### Detailed Checklist

#### 3.1 Chat UI Components
- [ ] Implement `MessageStream.tsx`
  - [ ] Display user messages and assistant responses
  - [ ] Support markdown rendering (code blocks, lists, links)
  - [ ] Show loading indicators during streaming
  - [ ] Auto-scroll to latest message
- [ ] Implement `TracePanel.tsx`
  - [ ] Inline trace blocks within message stream
  - [ ] Collapsible/expandable trace sections
  - [ ] Display trace metadata:
    - [ ] Tool name
    - [ ] Status (running, complete, error)
    - [ ] Latency (ms)
    - [ ] Token counts (input, output, total)
    - [ ] Input/output payloads (truncated with expand)
    - [ ] MCP server metadata (server name, endpoint)
    - [ ] A2A metadata (agent name, endpoint)
  - [ ] Hierarchical display for nested A2A traces
  - [ ] Real-time updates during streaming
  - [ ] Fluent UI styling (colors, icons, spacing)
- [ ] Implement `InputBox.tsx`
  - [ ] Text input with send button
  - [ ] Support multi-line input (Shift+Enter for new line, Enter to send)
  - [ ] Disable during streaming
  - [ ] Character count indicator
- [ ] Implement `ExportButton.tsx`
  - [ ] Export conversation and traces to CSV
  - [ ] Columns: timestamp, role (user/assistant/trace), content, metadata
  - [ ] Download as `conversation-{agent}-{timestamp}.csv`

#### 3.2 Agent-Specific Chat Pages
- [ ] Create `SupportTriageChat.tsx`
  - [ ] Load Support Triage agent config
  - [ ] Render chat UI with MessageStream, TracePanel, InputBox
  - [ ] Settings button → open `AgentEditor` modal
  - [ ] Export button
- [ ] Create `AzureOpsChat.tsx`
  - [ ] Load Azure Ops Assistant agent config
  - [ ] Render chat UI
  - [ ] Settings button → open `AgentEditor` modal
  - [ ] Export button
- [ ] Create `SqlAgentChat.tsx`
  - [ ] Load SQL Agent config
  - [ ] Render chat UI
  - [ ] Settings button → open `AgentEditor` modal
  - [ ] Export button
- [ ] Create `NewsAgentChat.tsx`
  - [ ] Load News Agent config
  - [ ] Render chat UI
  - [ ] Settings button → open `AgentEditor` modal
  - [ ] Export button
- [ ] Create `BusinessImpactChat.tsx`
  - [ ] Load Business Impact agent config
  - [ ] Render chat UI with **special A2A callout**:
    - [ ] Banner/info box: "This agent uses A2A protocol to orchestrate News Agent and SQL Agent"
    - [ ] Highlight A2A traces with distinct styling
  - [ ] Settings button → open `AgentEditor` modal
  - [ ] Export button

#### 3.3 SSE Streaming Hook
- [ ] Implement `useSSE.ts` custom hook
  - [ ] Establish EventSource connection to `/api/agents/{agent_id}/chat`
  - [ ] Parse SSE events: `token`, `trace_start`, `trace_update`, `trace_end`, `done`, `error`
  - [ ] Update React state for messages and traces
  - [ ] Handle reconnection on disconnect
  - [ ] Close connection on component unmount
- [ ] Test SSE hook with all agent types

#### 3.4 Agents Directory Page
- [ ] Implement `AgentsDirectory.tsx`
  - [ ] Fetch agent list from `/api/agents`
  - [ ] Display agent cards in grid layout
  - [ ] Each card shows:
    - [ ] Agent name
    - [ ] Agent description
    - [ ] Model (e.g., "GPT-4o")
    - [ ] Tool count (e.g., "3 tools")
    - [ ] Status (active/inactive)
  - [ ] Filter/sort controls:
    - [ ] Filter by tool type (MCP, OpenAPI, A2A)
    - [ ] Sort by name, date created
  - [ ] "Create New Agent" button → navigate to agent creation flow
  - [ ] Click card → navigate to agent chat page

#### 3.5 Agent Editor & Configuration
- [ ] Implement `AgentEditor.tsx` modal
  - [ ] Form fields:
    - [ ] Agent name (text input)
    - [ ] Agent description (textarea)
    - [ ] System prompt (code editor or large textarea)
    - [ ] Model selector (dropdown)
    - [ ] Tools configurator (see below)
  - [ ] Save button → validate and call PUT `/api/agents/{agent_id}`
  - [ ] Cancel button → close modal
- [ ] Implement `ModelSelector.tsx`
  - [ ] Dropdown with deployed models (fetch from backend or config)
  - [ ] Options: GPT-4o, GPT-4.1, GPT-5 (if available)
  - [ ] "Add New Model Deployment" button → open model deployment form
    - [ ] Fields: model name, deployment name, endpoint, API version
    - [ ] Save → update config (App Config or Cosmos DB)
- [ ] Implement `ToolConfigurator.tsx`
  - [ ] List of available tools (MCP servers, OpenAPI APIs, A2A agents)
  - [ ] Checkboxes to enable/disable tools
  - [ ] Sections:
    - [ ] **MCP Servers**
      - [ ] Microsoft Learn MCP (checkbox)
      - [ ] Azure MCP Server (checkbox)
      - [ ] adventure-mcp (checkbox)
      - [ ] "Add Custom MCP Server" button → open MCP server form
        - [ ] Fields: server name, description, URL, auth type (None, API Key, OAuth2)
        - [ ] Auth fields: API key OR OAuth2 config (client ID, secret, token URL, scopes)
        - [ ] Save → register MCP server
    - [ ] **OpenAPI APIs**
      - [ ] Support Triage API (checkbox)
      - [ ] Ops Assistant API (checkbox)
      - [ ] "Add Custom OpenAPI API" button → open OpenAPI form
        - [ ] Fields: API name, description, OpenAPI spec URL or file upload, auth type
        - [ ] Save → register OpenAPI API
    - [ ] **A2A Agents** (for orchestrators like Business Impact)
      - [ ] List of available A2A agents (News Agent, SQL Agent, etc.)
      - [ ] Checkboxes to enable/disable
  - [ ] Validation: ensure at least one tool is selected
- [ ] Implement `PromptEditor.tsx`
  - [ ] Code editor component (monaco-editor or textarea)
  - [ ] Syntax highlighting for system prompts
  - [ ] Character count and token estimate

#### 3.6 Navigation & Layout
- [ ] Implement `Sidebar.tsx`
  - [ ] Links to:
    - [ ] Agents Directory
    - [ ] Support Triage Chat
    - [ ] Azure Ops Chat
    - [ ] SQL Agent Chat
    - [ ] News Agent Chat
    - [ ] Business Impact Chat (with A2A badge/icon)
  - [ ] User profile section (name, logout button)
- [ ] Implement `TopNav.tsx`
  - [ ] App title/logo
  - [ ] Breadcrumb navigation
  - [ ] Settings button (future: global settings)
- [ ] Implement responsive layout (desktop + tablet)

#### 3.7 Authentication & Authorization
- [ ] Implement `useAuth.ts` hook
  - [ ] MSAL login/logout
  - [ ] Token acquisition for backend API
  - [ ] User claims (roles: Admin, User)
- [ ] Protect routes based on authentication
  - [ ] Redirect unauthenticated users to login page
  - [ ] Show loading state during authentication
- [ ] Implement role-based UI elements
  - [ ] Admin-only: Create/edit/delete agents
  - [ ] User: Chat with agents (read-only agent configs)

#### 3.8 Error Handling & Loading States
- [ ] Implement `ErrorBoundary.tsx`
  - [ ] Catch React errors
  - [ ] Display error message with retry button
- [ ] Implement loading spinners for:
  - [ ] Agent list loading
  - [ ] Chat initialization
  - [ ] Message streaming
  - [ ] Agent save/update
- [ ] Implement error toasts for:
  - [ ] API errors
  - [ ] SSE connection failures
  - [ ] Validation errors

### Acceptance Criteria (Phase 3)

- [ ] All 5 agent chat pages are functional
- [ ] Chat UI displays messages and traces in real-time
- [ ] Traces are collapsible and show full metadata
- [ ] A2A traces are visually distinct and hierarchical
- [ ] Business Impact chat page has A2A protocol callout
- [ ] Export to CSV works for all conversations
- [ ] Agents Directory displays all agents with filter/sort
- [ ] Agent Editor modal allows full configuration of agents
- [ ] Model selector and tool configurator are functional
- [ ] Users can add custom MCP servers and OpenAPI APIs
- [ ] Navigation works across all pages
- [ ] Entra ID authentication protects all routes
- [ ] Admin vs. User roles are enforced
- [ ] Error handling and loading states are polished

### Test Plan (Phase 3)

#### Unit Tests (Jest + React Testing Library)
- [ ] Test MessageStream component renders messages correctly
- [ ] Test TracePanel component displays and collapses traces
- [ ] Test InputBox component sends messages on Enter
- [ ] Test ExportButton generates correct CSV
- [ ] Test useSSE hook parses SSE events correctly
- [ ] Test useAuth hook handles login/logout flows

#### Integration Tests
- [ ] Test chat flow: send message → receive SSE stream → display tokens + traces
- [ ] Test agent editor: update agent config → save → reload agent
- [ ] Test model selector: add new model → verify it appears in dropdown
- [ ] Test tool configurator: add custom MCP server → verify it's registered
- [ ] Test A2A trace display: trigger Business Impact agent → verify nested traces

#### E2E Tests (Playwright)
- [ ] Login with Entra ID
- [ ] Navigate to Agents Directory
- [ ] Click on Support Triage agent card
- [ ] Send a message and verify streaming response
- [ ] Verify traces appear inline and are collapsible
- [ ] Export conversation to CSV and verify file contents
- [ ] Navigate to Business Impact agent
- [ ] Send a message that triggers A2A orchestration
- [ ] Verify hierarchical traces appear with News Agent and SQL Agent calls
- [ ] Open agent settings and update system prompt
- [ ] Save and verify changes persist
- [ ] Logout and verify redirect to login page

#### Accessibility Tests
- [ ] Verify keyboard navigation works (Tab, Enter, Esc)
- [ ] Verify screen reader compatibility (ARIA labels, roles)
- [ ] Verify color contrast meets WCAG AA standards
- [ ] Verify focus indicators are visible

---

## Phase 3 Summary

At the end of Phase 3, you will have:
- Complete React frontend with all 5 agent chat pages
- Real-time SSE streaming with token and trace display
- Agents Directory with filter/sort capabilities
- Full agent management (create, edit, delete)
- A2A protocol prominently showcased on Business Impact agent page
- CSV export for conversations
- Entra ID authentication and role-based access control
- Polished UI with Fluent UI styling

**Estimated Duration:** 3 weeks  
**Key Milestone:** Full end-to-end demo functional (backend + frontend + agents)

---

*End of Part 2. Continue to `01-project-plan-part3.md` for Phase 4 (Observability, Deployment, and Testing).*
