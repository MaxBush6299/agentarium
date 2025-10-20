# Project Plan: AI Agents Demo - Part 3

**Continuation with Phase 4: Observability, CI/CD, Testing, and Final Deployment**

---

## Phase 4: Observability, CI/CD, Security, and Production Readiness

**Objective:** Implement comprehensive observability, CI/CD pipelines, security hardening, cost controls, and production deployment.

### Detailed Checklist

#### 4.1 OpenTelemetry & Observability
- [ ] Implement OpenTelemetry configuration (`observability/otel_config.py`)
  - [ ] Azure Monitor exporter
  - [ ] Trace provider with sampling (90% in dev, 10% in prod)
  - [ ] Metrics provider
  - [ ] Resource attributes (service.name, service.version, deployment.environment)
- [ ] Implement FastAPI telemetry middleware (`observability/middleware.py`)
  - [ ] Trace all HTTP requests (method, path, status, duration)
  - [ ] Correlation ID propagation (X-Correlation-ID header)
  - [ ] User context (user ID, tenant ID from JWT)
  - [ ] Request/response body logging (configurable, PII redaction)
- [ ] Instrument agent execution
  - [ ] Span per agent run (agent name, thread ID, run ID)
  - [ ] Span per tool call (tool name, input hash, output hash, latency, tokens)
  - [ ] Span per MCP server call (server name, endpoint, latency)
  - [ ] Span per A2A call (agent name, endpoint, latency)
  - [ ] Attributes: `agent.name`, `tool.name`, `mcp.server`, `a2a.agent`, `token.input`, `token.output`, `token.total`, `cost.usd`
- [ ] Implement cost tracking (`observability/cost_tracker.py`)
  - [ ] Track token usage per agent, per user, per day
  - [ ] Calculate cost based on model pricing (GPT-4o, GPT-5)
  - [ ] Store cost metrics in Cosmos DB (`metrics` collection)
  - [ ] Alert on cost threshold (e.g., >$100/day)
- [ ] Implement PII redaction (`utils/pii_redaction.py`)
  - [ ] Regex patterns for emails, phone numbers, SSNs, credit cards
  - [ ] Redact before logging to Application Insights
  - [ ] Preserve structure (e.g., `email: ***@***.com`)
- [ ] Create Application Insights dashboards
  - [ ] Dashboard 1: **Agent Performance**
    - [ ] Chart: Requests per agent (bar chart)
    - [ ] Chart: Average response time per agent (line chart)
    - [ ] Chart: Token usage per agent (area chart)
    - [ ] Chart: Tool call latency distribution (histogram)
  - [ ] Dashboard 2: **A2A Orchestration**
    - [ ] Chart: A2A calls per agent (bar chart)
    - [ ] Chart: A2A call latency (line chart)
    - [ ] Chart: A2A success/failure rate (pie chart)
  - [ ] Dashboard 3: **MCP Performance**
    - [ ] Chart: MCP server calls per server (bar chart)
    - [ ] Chart: MCP server latency (line chart)
    - [ ] Chart: MCP server error rate (gauge)
  - [ ] Dashboard 4: **Cost & Usage**
    - [ ] Chart: Daily token usage (bar chart)
    - [ ] Chart: Daily cost (line chart)
    - [ ] Chart: Cost per user (table)
    - [ ] Chart: Cost per agent (pie chart)
- [ ] Configure Application Insights alerts
  - [ ] Alert: Response time > 10s (P3)
  - [ ] Alert: Error rate > 5% (P2)
  - [ ] Alert: Daily cost > $100 (P2)
  - [ ] Alert: MCP server unreachable (P3)
  - [ ] Alert: Cosmos DB RU consumption > 80% (P2)

#### 4.2 Cost Controls & Optimization
- [ ] Implement token budget enforcement
  - [ ] Per-user daily token limit (default: 100k tokens)
  - [ ] Per-agent per-request token limit (default: 10k tokens)
  - [ ] Return 429 (Too Many Requests) when limit exceeded
  - [ ] Store usage in Cosmos DB (`metrics` collection)
- [ ] Implement response truncation
  - [ ] Truncate tool outputs > 5KB (configurable)
  - [ ] Truncate trace payloads > 2KB in logs (expandable in UI)
  - [ ] Keep full payloads in Cosmos DB for replay
- [ ] Implement caching for MCP calls
  - [ ] Cache Microsoft Learn MCP responses (TTL: 1 hour)
  - [ ] Cache Azure MCP resource listings (TTL: 5 minutes)
  - [ ] Cache key: hash of tool name + input parameters
  - [ ] Use in-memory cache (lru_cache) or Redis if needed
- [ ] Configure APIM rate limiting
  - [ ] 100 requests/min per user for OpenAPI tools
  - [ ] 1000 requests/day per user for Bing News
  - [ ] Return 429 with Retry-After header
- [ ] Configure Cosmos DB RU optimization
  - [ ] Autoscale RU/s (min: 400, max: 4000)
  - [ ] Partition key design review for hot partitions
  - [ ] Query optimization (use partition key in WHERE clause)
- [ ] Implement telemetry sampling
  - [ ] Development: 90% sampling (high visibility)
  - [ ] Production: 10% sampling (cost-effective)
  - [ ] Always capture errors (100%)
  - [ ] Always capture high-latency requests (>5s, 100%)

#### 4.3 Security Hardening
- [ ] Implement input validation
  - [ ] Sanitize user messages (strip HTML, limit length)
  - [ ] Validate agent configuration (system prompt length, tool list)
  - [ ] Validate MCP server URLs (HTTPS only, whitelist domains)
  - [ ] Validate OpenAPI spec URLs (HTTPS only, whitelist domains)
- [ ] Implement output validation
  - [ ] Scan assistant responses for PII (email, phone, SSN)
  - [ ] Redact or warn user if PII detected
  - [ ] Scan SQL queries for destructive operations (DROP, TRUNCATE, DELETE without WHERE)
- [ ] Configure Key Vault access policies
  - [ ] Managed Identity: Get/List secrets only (no Set/Delete)
  - [ ] Admin users: Full access (for manual secret rotation)
- [ ] Configure RBAC for Azure resources
  - [ ] Container App Managed Identity:
    - [ ] Reader (subscription-level)
    - [ ] Contributor (demo resource group only)
    - [ ] Key Vault Secrets User
    - [ ] Cosmos DB Data Contributor
    - [ ] Storage Blob Data Contributor
  - [ ] Admin users:
    - [ ] Owner (resource group)
  - [ ] Regular users:
    - [ ] No direct Azure access (only via agents)
- [ ] Configure network security
  - [ ] NSG rules: deny all inbound except frontend ingress
  - [ ] Private endpoints for all data services (Cosmos, Storage, Key Vault)
  - [ ] No public IPs except frontend Container App
  - [ ] VNet integration for backend Container App
- [ ] Configure CORS
  - [ ] Allow frontend origin only (e.g., `https://agents-demo-frontend.azurecontainerapps.io`)
  - [ ] Allow credentials (cookies, Authorization header)
  - [ ] Disallow wildcard origins
- [ ] Implement security headers
  - [ ] Content-Security-Policy (CSP)
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] Strict-Transport-Security (HSTS)
- [ ] Implement audit logging
  - [ ] Log all agent CRUD operations (create, update, delete)
  - [ ] Log all admin actions (secret access, RBAC changes)
  - [ ] Store audit logs in Cosmos DB (`audit` collection)
  - [ ] Retention: 1 year

#### 4.4 CI/CD Pipelines (GitHub Actions)
- [ ] Configure OIDC federation with Azure
  - [ ] Create GitHub federated credential in Entra ID
  - [ ] Grant GitHub Actions service principal access to subscription
  - [ ] Store subscription ID, tenant ID, client ID in GitHub Secrets
- [ ] Create workflow: `deploy-infra.yml`
  - [ ] Trigger: push to `main` branch, `infra/**` path filter
  - [ ] Steps:
    - [ ] Checkout code
    - [ ] Authenticate to Azure (OIDC)
    - [ ] Validate Bicep templates (`az bicep build`)
    - [ ] Deploy Bicep (`az deployment group create`)
    - [ ] Output resource IDs and URLs
  - [ ] Environments: `dev`, `prod` (manual approval for prod)
- [ ] Create workflow: `deploy-backend.yml`
  - [ ] Trigger: push to `main` branch, `backend/**` path filter
  - [ ] Jobs:
    - [ ] **Test Job**:
      - [ ] Setup Python 3.11
      - [ ] Install dependencies
      - [ ] Run pytest (unit + integration tests)
      - [ ] Upload test results and coverage report
    - [ ] **Build Job** (depends on Test):
      - [ ] Build Docker image
      - [ ] Tag with commit SHA and `latest`
      - [ ] Push to Azure Container Registry
    - [ ] **Deploy Job** (depends on Build):
      - [ ] Authenticate to Azure (OIDC)
      - [ ] Deploy to Container Apps (`az containerapp update`)
      - [ ] Run smoke tests (call `/health` endpoint)
  - [ ] Environments: `dev`, `prod` (manual approval for prod)
- [ ] Create workflow: `deploy-frontend.yml`
  - [ ] Trigger: push to `main` branch, `frontend/**` path filter
  - [ ] Jobs:
    - [ ] **Test Job**:
      - [ ] Setup Node.js 20
      - [ ] Install dependencies
      - [ ] Run unit tests (Jest)
      - [ ] Upload test results
    - [ ] **Build Job** (depends on Test):
      - [ ] Build Docker image (Vite build + nginx)
      - [ ] Tag with commit SHA and `latest`
      - [ ] Push to Azure Container Registry
    - [ ] **Deploy Job** (depends on Build):
      - [ ] Authenticate to Azure (OIDC)
      - [ ] Deploy to Container Apps (`az containerapp update`)
      - [ ] Run smoke tests (call frontend URL, verify 200)
  - [ ] Environments: `dev`, `prod` (manual approval for prod)
- [ ] Create workflow: `e2e-tests.yml`
  - [ ] Trigger: completion of `deploy-backend.yml` and `deploy-frontend.yml`
  - [ ] Steps:
    - [ ] Setup Node.js 20
    - [ ] Install Playwright
    - [ ] Run E2E tests against deployed environment
    - [ ] Upload Playwright test results and videos
    - [ ] Fail deployment if E2E tests fail
- [ ] Create workflow: `security-scan.yml`
  - [ ] Trigger: push to `main` branch
  - [ ] Steps:
    - [ ] Run Dependabot security scan (backend + frontend)
    - [ ] Run Bandit (Python security linter)
    - [ ] Run ESLint security plugin (JavaScript/TypeScript)
    - [ ] Fail if critical vulnerabilities found

#### 4.5 Data Retention & Cleanup
- [ ] Configure Cosmos DB TTL
  - [ ] `threads` collection: 90 days (session-only memory per requirements)
  - [ ] `runs` collection: 90 days
  - [ ] `steps` collection: 90 days
  - [ ] `toolCalls` collection: 90 days
  - [ ] `metrics` collection: 180 days (cost tracking)
  - [ ] `audit` collection: 365 days (compliance)
- [ ] Configure Application Insights retention
  - [ ] Default: 30 days (cost-effective)
  - [ ] Traces with errors: 90 days (continuous export to Storage)
- [ ] Implement cleanup script (`scripts/cleanup-old-data.py`)
  - [ ] Scheduled job (Azure Functions or Container Apps scheduled job)
  - [ ] Run daily: delete traces/conversations older than TTL
  - [ ] Archive to Blob Storage before deletion (optional)

#### 4.6 Deployment & Environment Configuration
- [ ] Configure environment-specific parameters
  - [ ] **Dev environment** (`infra/parameters/dev.bicepparam`):
    - [ ] Smaller SKUs (Container Apps: 0.5 vCPU, Cosmos: 400 RU/s)
    - [ ] Higher telemetry sampling (90%)
    - [ ] Longer retention (90 days)
    - [ ] `LOCAL_DEV_MODE=false`
  - [ ] **Prod environment** (`infra/parameters/prod.bicepparam`):
    - [ ] Larger SKUs (Container Apps: 2 vCPU, Cosmos: autoscale)
    - [ ] Lower telemetry sampling (10%)
    - [ ] Standard retention (30 days App Insights, 90 days Cosmos)
    - [ ] `LOCAL_DEV_MODE=false`
- [ ] Store secrets in Key Vault
  - [ ] Cosmos DB connection string
  - [ ] Azure OpenAI API key (if not using Managed Identity)
  - [ ] Bing Search API key
  - [ ] APIM subscription key
  - [ ] adventure-mcp OAuth2 client secret
  - [ ] Entra ID client secret (if using client credentials flow)
- [ ] Configure App Configuration feature flags
  - [ ] `EnableA2A`: true (enable A2A protocol)
  - [ ] `EnableMCP`: true (enable MCP integrations)
  - [ ] `EnableCostTracking`: true (enable cost tracking)
  - [ ] `EnableTelemetrySampling`: true (enable sampling)
- [ ] Deploy to Azure
  - [ ] Run `infra/scripts/deploy.ps1 -Environment dev`
  - [ ] Verify all resources are created
  - [ ] Run `scripts/seed-agents.py` to create default agents
  - [ ] Test each agent manually
  - [ ] Deploy to prod with manual approval

#### 4.7 Documentation & Runbooks
- [ ] Create runbook: **Incident Response**
  - [ ] Agent not responding → check Application Insights for errors
  - [ ] High latency → check MCP server health, Cosmos DB RU consumption
  - [ ] Cost spike → check token usage per user, disable high-usage users
  - [ ] Security incident → revoke tokens, rotate secrets, audit logs
- [ ] Create runbook: **Agent Management**
  - [ ] How to create a new agent
  - [ ] How to add a custom MCP server
  - [ ] How to add a custom OpenAPI API
  - [ ] How to update system prompts
  - [ ] How to deploy model changes
- [ ] Create runbook: **Scaling & Performance**
  - [ ] How to scale Container Apps (manual vs. autoscale)
  - [ ] How to scale Cosmos DB RU/s
  - [ ] How to optimize queries
  - [ ] How to reduce costs (sampling, caching, truncation)
- [ ] Create runbook: **Disaster Recovery**
  - [ ] Cosmos DB backup/restore procedures
  - [ ] Key Vault secret rotation
  - [ ] Rollback procedures (revert to previous container image)
  - [ ] Data export/import procedures

### Acceptance Criteria (Phase 4)

- [ ] OpenTelemetry is configured and traces are visible in Application Insights
- [ ] All spans include agent, tool, MCP, and A2A metadata
- [ ] PII is redacted from logs
- [ ] Cost tracking is functional and accurate
- [ ] Application Insights dashboards display key metrics
- [ ] Alerts are configured and firing correctly (test with synthetic errors)
- [ ] Token budget enforcement prevents over-usage
- [ ] APIM rate limiting is enforced
- [ ] Cosmos DB TTL is configured and old data is deleted
- [ ] CI/CD pipelines deploy successfully to dev and prod
- [ ] E2E tests pass after deployment
- [ ] Security scans pass with no critical vulnerabilities
- [ ] Network security is enforced (private endpoints, NSGs)
- [ ] RBAC is configured correctly (least privilege)
- [ ] Audit logs capture all admin actions
- [ ] Runbooks are complete and tested

### Test Plan (Phase 4)

#### Observability Tests
- [ ] Generate synthetic agent runs and verify traces in Application Insights
- [ ] Verify correlation IDs propagate across services
- [ ] Verify tool call spans include all required attributes
- [ ] Verify A2A call spans include hierarchical structure
- [ ] Verify cost tracking calculates correct costs
- [ ] Trigger PII redaction and verify no PII in logs
- [ ] Trigger alerts and verify notifications (email, webhook)

#### Cost Control Tests
- [ ] Exceed per-user token limit and verify 429 response
- [ ] Exceed per-agent token limit and verify 429 response
- [ ] Verify response truncation works (send large tool output)
- [ ] Verify MCP response caching works (call same tool twice, verify cache hit)
- [ ] Verify APIM rate limiting (send 101 requests/min, verify 429)

#### Security Tests
- [ ] Attempt to access backend without JWT → verify 401
- [ ] Attempt to access Key Vault directly → verify denied
- [ ] Attempt to access Cosmos DB directly → verify denied
- [ ] Attempt to send SQL DROP query via SQL Agent → verify blocked
- [ ] Attempt to add malicious MCP server (HTTP, not HTTPS) → verify rejected
- [ ] Verify CORS rejects requests from unknown origins
- [ ] Verify security headers are present (CSP, HSTS, etc.)

#### CI/CD Tests
- [ ] Make a change to backend code → push to main → verify pipeline deploys
- [ ] Make a change to frontend code → push to main → verify pipeline deploys
- [ ] Make a change to Bicep → push to main → verify infrastructure updates
- [ ] Trigger E2E tests after deployment → verify they pass
- [ ] Introduce a failing test → verify pipeline fails and blocks deployment
- [ ] Trigger manual approval for prod deployment → verify approval workflow

#### Disaster Recovery Tests
- [ ] Simulate Cosmos DB outage → verify error handling and retry
- [ ] Simulate Key Vault outage → verify cached secrets work for limited time
- [ ] Simulate Azure OpenAI outage → verify graceful degradation
- [ ] Simulate MCP server outage → verify agent handles failure gracefully
- [ ] Rollback to previous container image → verify app still works

---

## Testing Strategy (All Phases)

### Unit Tests
- **Backend** (pytest):
  - [ ] Test agent base class
  - [ ] Test MCP client
  - [ ] Test OpenAPI client
  - [ ] Test A2A client
  - [ ] Test Cosmos DB repositories
  - [ ] Test PII redaction
  - [ ] Test cost tracking
  - [ ] Test token budget enforcement
- **Frontend** (Jest + React Testing Library):
  - [ ] Test chat components
  - [ ] Test trace components
  - [ ] Test agent editor components
  - [ ] Test SSE hook
  - [ ] Test auth hook

### Integration Tests
- **Backend**:
  - [ ] Test full chat flow (message → agent → tools → response → persist)
  - [ ] Test MCP integrations (live endpoints)
  - [ ] Test OpenAPI integrations (APIM mock backends)
  - [ ] Test A2A orchestration (Business Impact → News + SQL)
  - [ ] Test Cosmos DB persistence (create, read, update, delete)
- **Frontend**:
  - [ ] Test chat flow with mock backend
  - [ ] Test agent CRUD with mock backend

### E2E Tests (Playwright)
- [ ] **User Journey 1: Support Triage Agent**
  - [ ] Login with Entra ID
  - [ ] Navigate to Support Triage chat
  - [ ] Send message: "How do I reset my Azure AD password?"
  - [ ] Verify response with Microsoft Learn grounding
  - [ ] Verify traces show Microsoft Learn MCP call
  - [ ] Export conversation to CSV
- [ ] **User Journey 2: Azure Ops Assistant**
  - [ ] Navigate to Azure Ops chat
  - [ ] Send message: "List all Container Apps in the resource group"
  - [ ] Verify response with resource list
  - [ ] Verify traces show Azure MCP call
- [ ] **User Journey 3: SQL Agent**
  - [ ] Navigate to SQL Agent chat
  - [ ] Send message: "What are the top 5 customers by sales?"
  - [ ] Verify response with SQL query and results
  - [ ] Verify traces show adventure-mcp call
- [ ] **User Journey 4: News Agent**
  - [ ] Navigate to News Agent chat
  - [ ] Send message: "What is the latest news about AI?"
  - [ ] Verify response with news articles
  - [ ] Verify traces show Bing News call
- [ ] **User Journey 5: Business Impact Multi-Agent (A2A)**
  - [ ] Navigate to Business Impact chat
  - [ ] Verify A2A callout is visible
  - [ ] Send message: "How did recent tech news impact our sales?"
  - [ ] Verify response combines news and SQL data
  - [ ] Verify hierarchical traces show:
    - [ ] Parent: Business Impact agent
    - [ ] Child 1: News Agent call (via A2A)
    - [ ] Child 2: SQL Agent call (via A2A)
  - [ ] Verify A2A traces are visually distinct
- [ ] **User Journey 6: Agent Management (Admin)**
  - [ ] Navigate to Agents Directory
  - [ ] Create new agent with custom system prompt
  - [ ] Add custom MCP server
  - [ ] Save and verify agent appears in directory
  - [ ] Open agent chat page and test
  - [ ] Edit agent (update system prompt)
  - [ ] Verify changes persist
  - [ ] Delete agent

### Performance Tests (optional for MVP, recommended for production)
- [ ] Load test: 50 concurrent users, 5 agents, 10 min duration
- [ ] Measure: response time (p50, p95, p99), error rate, RU/s consumption
- [ ] Verify: no memory leaks, no connection pool exhaustion
- [ ] Verify: autoscaling works (Container Apps scale out, Cosmos RU scales up)

### Security Tests (automated + manual)
- [ ] OWASP ZAP scan on frontend and backend APIs
- [ ] Penetration testing (external consultant, optional)
- [ ] Dependency vulnerability scanning (Dependabot, Snyk)
- [ ] Secret scanning (GitHub Secret Scanning, TruffleHog)

---

## Milestones & Timeline

| Phase | Duration | Key Deliverables | Success Criteria |
|-------|----------|------------------|------------------|
| **Phase 1: Foundation** | 2 weeks | Infrastructure, backend/frontend scaffolding, auth | All resources deployed, local dev functional |
| **Phase 2: Agents & Tools** | 3 weeks | 5 agents, MCP/OpenAPI/A2A integration, streaming | All agents respond correctly, A2A orchestration works |
| **Phase 3: Frontend** | 3 weeks | Chat UI, traces, agent management | Full UI functional, A2A traces visible |
| **Phase 4: Observability & Deployment** | 2 weeks | Telemetry, CI/CD, security, production deployment | Deployed to prod, dashboards live, tests passing |
| **Total** | **10 weeks** | **Full demo ready** | **Customer-facing demo ready** |

---

## Risk Assessment & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GPT-5 not available in East US | Medium | Medium | Fallback to GPT-4.1 or GPT-4o |
| adventure-mcp OAuth2 issues | Medium | Medium | Implement robust token refresh, fallback to mock data |
| Azure MCP Server sidecar instability | Low | High | Test thoroughly, implement health checks and restarts |
| A2A protocol complexity | Medium | Medium | Start simple (sequential calls), iterate to dynamic |
| High Cosmos DB costs | Medium | High | Enforce TTL, optimize partition keys, monitor RU/s |
| Slow MCP server responses | Medium | Medium | Implement timeouts, caching, and fallback |
| Entra ID authentication issues | Low | High | Test with multiple users, implement clear error messages |
| CI/CD pipeline failures | Low | Medium | Test pipelines in dev, use manual approval for prod |

---

## Post-MVP Enhancements (Future Work)

- **Agent Capabilities**:
  - [ ] Add file upload support (attach documents to chat)
  - [ ] Add image generation agent (DALL-E integration)
  - [ ] Add code execution agent (sandboxed Python/JavaScript execution)
  - [ ] Add web search agent (Bing Web Search, not just news)
- **Multi-Agent Orchestration**:
  - [ ] Add Concurrent orchestration pattern (parallel agent execution)
  - [ ] Add Handoff orchestration pattern (dynamic agent routing)
  - [ ] Add Group Chat orchestration (multiple agents in conversation)
- **Conversational Memory**:
  - [ ] Upgrade to semantic memory (embed + retrieve relevant history)
  - [ ] Add persistent memory across sessions (user preference)
  - [ ] Add shared memory across agents (knowledge graph)
- **UI Enhancements**:
  - [ ] Add dark mode
  - [ ] Add mobile-responsive design
  - [ ] Add voice input (Speech-to-Text)
  - [ ] Add voice output (Text-to-Speech)
  - [ ] Add real-time collaboration (multiple users in same chat)
- **Admin Portal**:
  - [ ] Add user management (invite users, assign roles)
  - [ ] Add usage analytics dashboard (per-user, per-agent)
  - [ ] Add cost allocation and chargeback
  - [ ] Add audit log viewer
- **Security & Compliance**:
  - [ ] Add data residency controls (multi-region deployment)
  - [ ] Add GDPR compliance (data export, right to be forgotten)
  - [ ] Add SOC 2 compliance (audit logs, access controls)
- **Performance & Scalability**:
  - [ ] Add Redis cache for high-traffic scenarios
  - [ ] Add Azure Front Door for global load balancing
  - [ ] Add multi-region deployment (active-active)
  - [ ] Add Azure CDN for frontend assets

---

## Success Metrics

### Technical Metrics
- [ ] **Availability**: 99.9% uptime (measured over 30 days)
- [ ] **Latency**: p95 response time < 3s for agent responses
- [ ] **Error Rate**: < 1% of requests result in errors
- [ ] **Cost**: < $500/month for demo workload (100 users, 1000 messages/day)
- [ ] **Token Efficiency**: Average 500 tokens per message (input + output)

### Business Metrics
- [ ] **User Adoption**: 80% of demo users try at least 3 agents
- [ ] **Engagement**: Average 5 messages per session
- [ ] **A2A Awareness**: 100% of users understand A2A from Business Impact agent demo
- [ ] **Customer Feedback**: 4.5/5 satisfaction rating for demo clarity and quality

### Demo Effectiveness Metrics
- [ ] **Clarity**: Users understand how agents, MCP, and A2A work
- [ ] **Completeness**: Demo covers all key Agent Framework features
- [ ] **Credibility**: Demo runs reliably without errors during customer presentations
- [ ] **Reusability**: Demo code can be adapted for customer POCs

---

## Appendix: Key Technologies & References

### Azure Services
- **Azure Container Apps**: Hosting frontend and backend
- **Azure Cosmos DB**: State persistence (threads, runs, steps, metrics)
- **Azure OpenAI / AI Foundry**: Model inference (GPT-4o, GPT-5)
- **Azure Key Vault**: Secret management
- **Azure App Configuration**: Feature flags and configuration
- **Azure Storage**: Blob storage for logs and exports
- **Azure API Management**: OpenAPI tool hosting
- **Azure Monitor / Application Insights**: Observability
- **Azure Virtual Network**: Private networking
- **Azure Entra ID**: Authentication and authorization

### Frameworks & SDKs
- **Microsoft Agent Framework SDK**: Core agent implementation ([aka.ms/agentframework](https://aka.ms/agentframework))
- **FastAPI**: Python web framework
- **React + TypeScript**: Frontend framework
- **Fluent UI**: Microsoft design system
- **MSAL**: Microsoft Authentication Library
- **OpenTelemetry**: Distributed tracing
- **Playwright**: E2E testing

### Protocols & Standards
- **MCP (Model Context Protocol)**: Tool integration standard
- **A2A (Agent-to-Agent)**: Agent communication protocol
- **OpenAPI**: API specification standard
- **SSE (Server-Sent Events)**: Real-time streaming
- **OAuth 2.0**: Authentication protocol

### External Integrations
- **Microsoft Learn MCP**: https://learn.microsoft.com/api/mcp
- **Azure MCP Server**: Sidecar for Azure operations
- **adventure-mcp**: https://mssqlmcp.azure-api.net (AdventureWorks SQL)
- **Bing News Search**: Via Azure AI Foundry grounding tool

### Documentation References
- Agent Framework Overview: https://aka.ms/agentframework
- MCP Integration Tutorials: https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/agent-as-mcp-tool
- A2A Protocol: https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/a2a-agent
- Azure MCP Server: https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/
- Develop AI Agents on Azure (Learning Path): https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-on-azure/

---

## Conclusion

This project plan provides a comprehensive roadmap for building a production-ready AI agents demo using Microsoft's Agent Framework SDK. By following the phased approach and detailed checklists, you will deliver a compelling demo that showcases:

- **All 5 agent types** with real-world use cases
- **MCP integration** with Microsoft Learn, Azure MCP Server, and custom SQL MCP
- **A2A protocol** for multi-agent orchestration (visibly highlighted in UI)
- **Real-time streaming** with inline trace visualization
- **Agent management** with full CRUD and customization
- **Azure-only infrastructure** with private networking and Managed Identity
- **Comprehensive observability** with cost tracking and PII redaction
- **CI/CD pipelines** for automated deployment
- **Security hardening** with RBAC, Key Vault, and network isolation

The demo is designed to be both **impressive for customers** and **reusable for POCs**, with clean architecture, thorough testing, and production-ready practices.

**Next Steps**: Proceed to `02-architecture-part1.md` for detailed architecture and implementation guidance.

---

*End of Part 3. This completes the Project Plan. Continue to Architecture documentation.*
