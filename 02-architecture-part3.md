# Architecture Documentation: AI Agents Demo - Part 3

**Networking, Security, Scalability, and Operations**

---

## Table of Contents

1. [Detailed Networking Architecture](#detailed-networking-architecture)
2. [Security Architecture](#security-architecture)
3. [Scalability & Performance](#scalability--performance)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Failure Modes & Resilience](#failure-modes--resilience)
6. [Operational Procedures](#operational-procedures)

---

## Detailed Networking Architecture

### VNet Topology

```
Azure Region: East US
Resource Group: rg-agents-demo

VNet: vnet-agents-demo (10.0.0.0/16)
├─ Address Space: 10.0.0.0/16 (65,536 IPs)
├─ DNS: Azure-provided DNS + Private DNS Zones
└─ Subnets:
   ├─ snet-container-apps (10.0.1.0/24, 256 IPs)
   │  Purpose: Container Apps Environment
   │  NSG: nsg-container-apps
   │  Service Endpoints: None (uses private endpoints)
   │  Delegations: Microsoft.App/environments
   │
   ├─ snet-private-endpoints (10.0.2.0/24, 256 IPs)
   │  Purpose: Private endpoints for data services
   │  NSG: nsg-private-endpoints
   │  Service Endpoints: None
   │  Private Endpoints:
   │    - Cosmos DB (10.0.2.10)
   │    - Key Vault (10.0.2.11)
   │    - Storage Account (10.0.2.12)
   │    - App Configuration (10.0.2.13)
   │    - Azure OpenAI (10.0.2.14)
   │    - API Management (10.0.2.15)
   │
   └─ snet-integration (10.0.3.0/24, 256 IPs)
      Purpose: Reserved for future Azure services integration
      NSG: nsg-integration
```

### Traffic Flow Patterns

#### Pattern 1: User → Frontend (Public Internet)

```
User Browser (Internet)
   │ HTTPS (443)
   ↓
Azure Front Door / Traffic Manager (optional, future)
   │
   ↓
Container Apps Ingress Controller (Public)
   │ TLS Termination
   ↓
Frontend Container (nginx)
   │ Port 80 (HTTP, internal)
   └─ Static files served
```

**Security Controls:**
- TLS 1.2+ enforced
- Entra ID authentication (MSAL redirect)
- CORS restricted to known origins
- Rate limiting at ingress (1000 req/min per IP)
- DDoS Protection (Standard tier, optional)

#### Pattern 2: Frontend → Backend (VNet Internal)

```
Frontend Container (10.0.1.50)
   │ HTTPS (443) - Internal TLS
   ↓
Container Apps Ingress Controller (Internal)
   │
   ↓
Backend Container (10.0.1.51)
   │ Port 8000 (HTTP, internal)
   │ JWT validation
   └─ FastAPI endpoints
```

**Security Controls:**
- Internal ingress only (no public IP)
- JWT token validation (RS256)
- Role-based authorization (Admin, User)
- Request size limits (10 MB max)
- Rate limiting per user (100 req/min)

#### Pattern 3: Backend → Private Endpoints

```
Backend Container (10.0.1.51)
   │
   ├─ Cosmos DB (10.0.2.10:443)
   │  Protocol: HTTPS
   │  Auth: Managed Identity (RBAC)
   │  DNS: privatelink.documents.azure.com
   │
   ├─ Key Vault (10.0.2.11:443)
   │  Protocol: HTTPS
   │  Auth: Managed Identity
   │  DNS: privatelink.vaultcore.azure.net
   │
   ├─ Storage (10.0.2.12:443)
   │  Protocol: HTTPS
   │  Auth: Managed Identity
   │  DNS: privatelink.blob.core.windows.net
   │
   ├─ Azure OpenAI (10.0.2.14:443)
   │  Protocol: HTTPS
   │  Auth: Managed Identity
   │  DNS: privatelink.openai.azure.com
   │
   └─ API Management (10.0.2.15:443)
      Protocol: HTTPS
      Auth: Subscription key (from Key Vault)
      DNS: privatelink.azure-api.net
```

**Security Controls:**
- All traffic stays within VNet (no public egress)
- Managed Identity for authentication (no secrets in code)
- Private DNS resolution
- NSG rules enforce traffic flow
- Service-to-service encryption in transit

#### Pattern 4: Backend → External MCP Servers

```
Backend Container (10.0.1.51)
   │ NAT Gateway (optional) or Container Apps egress IP
   ↓ HTTPS (443) - Public Internet
   │
   ├─ Microsoft Learn MCP (learn.microsoft.com)
   │  Auth: None
   │  Caching: 1 hour (in-memory LRU)
   │
   └─ adventure-mcp (mssqlmcp.azure-api.net)
      Auth: OAuth2 (token cached)
      Endpoint: APIM-fronted SQL MCP
```

**Security Controls:**
- TLS 1.2+ enforced
- OAuth2 token stored in Key Vault
- Response caching to reduce external calls
- Timeout: 30s per request
- Retry policy: 3 attempts with exponential backoff

#### Pattern 5: Backend ↔ Azure MCP Server (Sidecar)

```
Backend Container (10.0.1.51)
   │ localhost (127.0.0.1:3000)
   ↓ HTTP (no TLS needed, same pod)
Azure MCP Server Sidecar (localhost:3000)
   │ Uses Backend's Managed Identity
   ↓ HTTPS (443) to Azure Resource Manager
Azure Subscription
   ├─ List resources (Reader role, subscription)
   └─ Deploy resources (Contributor role, demo RG only)
```

**Security Controls:**
- Sidecar shares Managed Identity with backend
- No network exposure (localhost only)
- RBAC enforced at Azure API level
- Audit logs for all Azure operations

### Network Security Groups (NSG Rules)

#### NSG: nsg-container-apps

**Inbound Rules (Priority Order):**

| Priority | Name | Source | Dest | Port | Protocol | Action | Description |
|----------|------|--------|------|------|----------|--------|-------------|
| 100 | AllowHttpsFromInternet | Internet | 10.0.1.0/24 | 443 | TCP | Allow | Public HTTPS to frontend |
| 200 | AllowVNetInbound | VirtualNetwork | 10.0.1.0/24 | * | * | Allow | Internal VNet traffic |
| 300 | AllowAzureLoadBalancer | AzureLoadBalancer | 10.0.1.0/24 | * | * | Allow | Health probes |
| 4096 | DenyAllInbound | * | * | * | * | Deny | Default deny |

**Outbound Rules:**

| Priority | Name | Source | Dest | Port | Protocol | Action | Description |
|----------|------|--------|------|------|----------|--------|-------------|
| 100 | AllowHttpsToInternet | 10.0.1.0/24 | Internet | 443 | TCP | Allow | External MCP servers |
| 200 | AllowVNetOutbound | 10.0.1.0/24 | VirtualNetwork | * | * | Allow | Private endpoints |
| 300 | AllowAzureMonitor | 10.0.1.0/24 | AzureMonitor | 443 | TCP | Allow | Telemetry |
| 4096 | DenyAllOutbound | * | * | * | * | Deny | Default deny |

#### NSG: nsg-private-endpoints

**Inbound Rules:**

| Priority | Name | Source | Dest | Port | Protocol | Action | Description |
|----------|------|--------|------|------|----------|--------|-------------|
| 100 | AllowContainerApps | 10.0.1.0/24 | 10.0.2.0/24 | 443 | TCP | Allow | Backend → data services |
| 4096 | DenyAllInbound | * | * | * | * | Deny | Default deny |

**Outbound Rules:**

| Priority | Name | Source | Dest | Port | Protocol | Action | Description |
|----------|------|--------|------|------|----------|--------|-------------|
| 100 | AllowAll | 10.0.2.0/24 | * | * | * | Allow | Response traffic |

### Private DNS Configuration

**Private DNS Zones (linked to VNet):**

| Service | Private DNS Zone | Example Record |
|---------|------------------|----------------|
| Cosmos DB | `privatelink.documents.azure.com` | `cosmos-agents-demo.privatelink.documents.azure.com` → 10.0.2.10 |
| Key Vault | `privatelink.vaultcore.azure.net` | `kv-agents-demo.privatelink.vaultcore.azure.net` → 10.0.2.11 |
| Storage | `privatelink.blob.core.windows.net` | `stagentsdemo.privatelink.blob.core.windows.net` → 10.0.2.12 |
| App Config | `privatelink.azconfig.io` | `appconfig-agents-demo.privatelink.azconfig.io` → 10.0.2.13 |
| Azure OpenAI | `privatelink.openai.azure.com` | `openai-agents-demo.privatelink.openai.azure.com` → 10.0.2.14 |
| APIM | `privatelink.azure-api.net` | `apim-agents-demo.privatelink.azure-api.net` → 10.0.2.15 |

**DNS Resolution Flow:**

```
Backend Container requests: cosmos-agents-demo.documents.azure.com
   ↓
Azure DNS (168.63.129.16)
   ↓
Check VNet-linked Private DNS Zones
   ↓
Match: privatelink.documents.azure.com
   ↓
Return: 10.0.2.10 (Private Endpoint IP)
   ↓
Backend connects to Cosmos DB via private IP (no internet egress)
```

---

## Security Architecture

### Defense in Depth Layers

```
Layer 7: Application Security
├─ Input validation (XSS, SQL injection prevention)
├─ Output encoding (PII redaction)
├─ Rate limiting per user (token budget enforcement)
├─ CSRF protection (SameSite cookies)
└─ Security headers (CSP, HSTS, X-Frame-Options)

Layer 6: Authentication & Authorization
├─ Entra ID authentication (MSAL, OAuth2 + OIDC)
├─ JWT token validation (RS256, signature verification)
├─ Role-based access control (Admin, User)
├─ Token expiration enforcement (1 hour)
└─ User context propagation (correlation IDs)

Layer 5: API Security
├─ API Management (rate limiting, quotas, IP filtering)
├─ TLS 1.2+ enforcement
├─ API key rotation (90 days)
├─ OpenAPI spec validation
└─ Mock backends for placeholder APIs

Layer 4: Network Security
├─ VNet isolation (private subnets)
├─ NSG rules (least privilege)
├─ Private endpoints (no public IPs for data services)
├─ No RDP/SSH (Container Apps, no shell access)
└─ DDoS protection (optional, Standard tier)

Layer 3: Identity & Access Management
├─ Managed Identity (no secrets in code)
├─ RBAC (least privilege roles)
├─ Key Vault (secret management)
├─ Conditional Access (optional, require MFA)
└─ Privileged Identity Management (optional, JIT admin access)

Layer 2: Data Security
├─ Encryption at rest (Cosmos DB, Storage, all Azure services)
├─ Encryption in transit (TLS 1.2+ everywhere)
├─ PII redaction (before logging)
├─ Data retention policies (TTL in Cosmos DB)
└─ Audit logging (all admin actions)

Layer 1: Monitoring & Response
├─ Application Insights (centralized logging)
├─ Security alerts (anomalous activity)
├─ Audit logs (Cosmos DB, Azure Activity Log)
├─ Cost alerts (budget thresholds)
└─ Incident response runbooks
```

### RBAC Assignments

#### Managed Identity: `id-agents-demo`

| Scope | Role | Purpose |
|-------|------|---------|
| Subscription (East US) | Reader | List all resources for Azure MCP Server |
| Resource Group: rg-agents-demo | Contributor | Deploy/manage resources in demo RG |
| Cosmos DB: cosmos-agents-demo | Cosmos DB Data Contributor | Read/write threads, runs, agents, metrics |
| Key Vault: kv-agents-demo | Key Vault Secrets User | Read secrets (no write/delete) |
| Storage: stagentsdemo | Storage Blob Data Contributor | Write logs, exports |
| Azure OpenAI: openai-agents-demo | Cognitive Services OpenAI User | Model inference |
| App Insights: appi-agents-demo | Monitoring Metrics Publisher | Send telemetry |

#### Admin Users (Human)

| Scope | Role | Purpose |
|-------|------|---------|
| Resource Group: rg-agents-demo | Owner | Full control for demo setup/teardown |
| Key Vault: kv-agents-demo | Key Vault Administrator | Manage secrets (rotation, deletion) |

#### Regular Users (Human)

| Scope | Role | Purpose |
|-------|------|---------|
| Application (Entra ID) | User | Chat with agents (no admin actions) |
| No direct Azure access | - | All operations via agents |

### Secrets Management

**Key Vault Secrets:**

| Secret Name | Description | Rotation Period | Access |
|-------------|-------------|-----------------|--------|
| `cosmos-connection-string` | Cosmos DB connection string (fallback if RBAC fails) | 90 days | Managed Identity |
| `adventure-mcp-client-id` | OAuth2 client ID for adventure-mcp | 180 days | Managed Identity |
| `adventure-mcp-client-secret` | OAuth2 client secret for adventure-mcp | 90 days | Managed Identity |
| `bing-search-api-key` | Bing Search API key (if not using Managed Identity) | 90 days | Managed Identity |
| `apim-subscription-key` | API Management subscription key | 90 days | Managed Identity |

**Secret Retrieval (Local Dev vs. Production):**

```python
# utils/secrets.py

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.keyvault.secrets import SecretClient
from config import settings

def get_secret_client() -> SecretClient:
    if settings.LOCAL_DEV_MODE:
        # Local dev: use Azure CLI credentials
        credential = AzureCliCredential()
    else:
        # Production: use Managed Identity
        credential = DefaultAzureCredential()
    
    return SecretClient(
        vault_url=settings.KEY_VAULT_URL,
        credential=credential
    )

_secret_cache = {}  # In-memory cache (TTL: 1 hour)

def get_secret(secret_name: str) -> str:
    if secret_name in _secret_cache:
        return _secret_cache[secret_name]
    
    client = get_secret_client()
    secret = client.get_secret(secret_name)
    _secret_cache[secret_name] = secret.value
    return secret.value
```

### Input Validation & Sanitization

**User Message Validation:**

```python
# api/chat.py

from pydantic import BaseModel, validator, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    thread_id: str | None = Field(None, regex=r"^thread-[a-z0-9\-]+$")
    
    @validator("message")
    def sanitize_message(cls, v):
        # Strip HTML tags
        v = re.sub(r"<[^>]+>", "", v)
        # Limit consecutive newlines
        v = re.sub(r"\n{3,}", "\n\n", v)
        return v.strip()
```

**SQL Query Validation (SQL Agent):**

```python
# agents/sql_agent.py

BLOCKED_SQL_KEYWORDS = [
    "DROP", "TRUNCATE", "DELETE FROM", "ALTER", "CREATE", "GRANT", "REVOKE"
]

def validate_sql_query(query: str) -> bool:
    query_upper = query.upper()
    for keyword in BLOCKED_SQL_KEYWORDS:
        if keyword in query_upper:
            raise ValueError(f"SQL query contains blocked keyword: {keyword}")
    return True
```

### PII Redaction

```python
# utils/pii_redaction.py

import re

PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"
}

def redact_pii(text: str) -> str:
    for pii_type, pattern in PII_PATTERNS.items():
        if pii_type == "email":
            text = re.sub(pattern, "***@***.com", text)
        elif pii_type == "phone":
            text = re.sub(pattern, "***-***-****", text)
        elif pii_type == "ssn":
            text = re.sub(pattern, "***-**-****", text)
        elif pii_type == "credit_card":
            text = re.sub(pattern, "****-****-****-****", text)
    return text
```

---

## Scalability & Performance

### Container Apps Scaling Configuration

**Frontend Container App:**

```yaml
resources:
  cpu: 0.5
  memory: 1Gi

scale:
  minReplicas: 2  # Always-on for demo
  maxReplicas: 10
  rules:
    - name: http-rule
      http:
        metadata:
          concurrentRequests: 50  # Scale out at 50 concurrent requests
    - name: cpu-rule
      custom:
        type: cpu
        metadata:
          type: Utilization
          value: 70  # Scale out at 70% CPU
```

**Backend Container App:**

```yaml
resources:
  cpu: 1.0
  memory: 2Gi

scale:
  minReplicas: 2  # HA for demo
  maxReplicas: 20
  rules:
    - name: http-rule
      http:
        metadata:
          concurrentRequests: 20  # More resource-intensive (LLM calls)
    - name: cpu-rule
      custom:
        type: cpu
        metadata:
          type: Utilization
          value: 70
```

### Cosmos DB Scaling

**Throughput Configuration:**

```bicep
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: 'cosmos-agents-demo'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'  // Balance between consistency and performance
    }
    locations: [
      {
        locationName: 'East US'
        failoverPriority: 0
        isZoneRedundant: false  // Set to true for production
      }
    ]
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: 'AgentState'
  properties: {
    resource: {
      id: 'AgentState'
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 4000  // Autoscale from 400 to 4000 RU/s
      }
    }
  }
}
```

**Partition Key Strategy:**

| Collection | Partition Key | Rationale | Expected RU/s |
|------------|---------------|-----------|---------------|
| threads | `/userId` | Queries filtered by user | 400-1000 |
| runs | `/threadId` | Queries filtered by thread | 400-1000 |
| steps | `/runId` | Queries filtered by run | 400-800 |
| toolCalls | `/stepId` | Queries filtered by step | 400-800 |
| agents | `/id` | Small collection, even distribution | 400 |
| metrics | `/date` | Time-series queries | 400-2000 |

**Query Optimization:**

```python
# Good: Uses partition key
query = "SELECT * FROM c WHERE c.userId = @userId AND c.agentId = @agentId"
parameters = [
    {"name": "@userId", "value": user_id},
    {"name": "@agentId", "value": agent_id}
]

# Bad: Cross-partition query (expensive)
query = "SELECT * FROM c WHERE c.agentId = @agentId"  # No userId filter
```

### Caching Strategy

**1. Agent Registry Cache (In-Memory)**

```python
# agents/registry.py

from functools import lru_cache

@lru_cache(maxsize=100)
def get_agent(agent_id: str) -> AIAgent:
    """Cache agent instances (reloaded on config change)"""
    agent_config = cosmos_client.get_agent(agent_id)
    return create_agent_from_config(agent_config)
```

**2. MCP Tool Schema Cache (In-Memory)**

```python
# tools/mcp_client.py

_tool_schema_cache = {}  # TTL: 1 hour

async def discover_tools(self) -> dict:
    cache_key = f"{self.endpoint}:tools"
    if cache_key in _tool_schema_cache:
        cached_at, schemas = _tool_schema_cache[cache_key]
        if (datetime.now() - cached_at).seconds < 3600:
            return schemas
    
    schemas = await self._fetch_tool_schemas()
    _tool_schema_cache[cache_key] = (datetime.now(), schemas)
    return schemas
```

**3. MCP Response Cache (Microsoft Learn Only)**

```python
# tools/mcp_servers/microsoft_learn.py

from functools import lru_cache

@lru_cache(maxsize=1000)
def search_docs(query: str) -> dict:
    """Cache Microsoft Learn searches (docs don't change frequently)"""
    return self.client.call_tool("search_docs", {"query": query})
```

**4. OAuth2 Token Cache**

```python
# tools/mcp_servers/adventure_mcp.py

_token_cache = {}  # {client_id: (token, expiry)}

async def get_access_token(self) -> str:
    if self.client_id in _token_cache:
        token, expiry = _token_cache[self.client_id]
        if expiry > datetime.now() + timedelta(minutes=5):
            return token  # Use cached token
    
    # Request new token
    token = await self._request_token()
    expiry = datetime.now() + timedelta(seconds=token["expires_in"])
    _token_cache[self.client_id] = (token["access_token"], expiry)
    return token["access_token"]
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to First Token (TTFT) | < 1s | SSE first token event |
| Full Response Time (p95) | < 3s | SSE done event |
| MCP Tool Call Latency (p95) | < 2s | Trace end event |
| A2A Call Latency (p95) | < 5s | Hierarchical trace |
| Cosmos DB Query Latency (p95) | < 50ms | OpenTelemetry span |
| Concurrent Users Supported | 100 | Load test (10 min) |
| Requests per Second (RPS) | 50 | Load test (1 min burst) |

---

## Cost Optimization Strategies

### 1. Token Budget Enforcement

**Per-User Daily Limit:**

```python
# observability/cost_tracker.py

DAILY_TOKEN_LIMIT = 100_000  # 100K tokens per user per day

async def check_token_budget(user_id: str) -> bool:
    today = datetime.now().date()
    usage = await metrics_repo.get_usage_by_user(user_id, today, today)
    total_tokens = sum(m["totalTokens"] for m in usage)
    
    if total_tokens >= DAILY_TOKEN_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Daily token limit ({DAILY_TOKEN_LIMIT}) exceeded. Resets at midnight."
        )
    return True
```

**Per-Agent Per-Request Limit:**

```python
# agents/base.py

MAX_TOKENS_PER_REQUEST = 10_000

async def run(self, message: str) -> str:
    if self.estimate_tokens(message) > MAX_TOKENS_PER_REQUEST:
        raise ValueError(f"Request exceeds token limit ({MAX_TOKENS_PER_REQUEST})")
    
    response = await self.agent.generate_response(message, max_tokens=MAX_TOKENS_PER_REQUEST)
    return response
```

### 2. Response Truncation

```python
# tools/mcp_client.py

MAX_TOOL_OUTPUT_SIZE = 5120  # 5 KB

async def call_tool(self, tool_name: str, parameters: dict) -> dict:
    result = await self._invoke_tool(tool_name, parameters)
    
    # Truncate large outputs
    if isinstance(result, dict) and "output" in result:
        output_str = str(result["output"])
        if len(output_str) > MAX_TOOL_OUTPUT_SIZE:
            result["output"] = output_str[:MAX_TOOL_OUTPUT_SIZE] + "... (truncated)"
            result["_truncated"] = True
    
    return result
```

### 3. Telemetry Sampling

```python
# observability/otel_config.py

from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

if settings.LOCAL_DEV_MODE:
    sampler = TraceIdRatioBased(0.9)  # 90% sampling in dev
else:
    sampler = TraceIdRatioBased(0.1)  # 10% sampling in prod

# Always sample errors and high-latency requests
class SmartSampler(TraceIdRatioBased):
    def should_sample(self, context, trace_id, name, kind, attributes):
        # Always sample errors
        if attributes.get("error"):
            return SamplingResult(Decision.RECORD_AND_SAMPLE)
        
        # Always sample high-latency requests
        if attributes.get("duration_ms", 0) > 5000:
            return SamplingResult(Decision.RECORD_AND_SAMPLE)
        
        # Otherwise, use ratio-based sampling
        return super().should_sample(context, trace_id, name, kind, attributes)
```

### 4. Cosmos DB TTL

```python
# persistence/models.py

class Thread(BaseModel):
    id: str
    userId: str
    agentId: str
    createdAt: datetime
    ttl: int = 7776000  # 90 days (in seconds)

class Metric(BaseModel):
    id: str
    date: str
    userId: str
    agentId: str
    cost: float
    ttl: int = 15552000  # 180 days (cost data kept longer)
```

### 5. API Management Rate Limiting

```xml
<!-- APIM Policy for OpenAPI Tools -->
<policies>
    <inbound>
        <rate-limit-by-key calls="100" renewal-period="60" counter-key="@(context.Request.Headers.GetValueOrDefault("Authorization"))" />
        <quota-by-key calls="1000" renewal-period="86400" counter-key="@(context.Request.Headers.GetValueOrDefault("Authorization"))" />
        <cache-lookup vary-by-developer="true" vary-by-developer-groups="false" />
    </inbound>
    <backend>
        <forward-request />
    </backend>
    <outbound>
        <cache-store duration="300" />  <!-- 5 min cache -->
    </outbound>
</policies>
```

### 6. Cost Monitoring & Alerts

**Application Insights Alert Rules:**

```bicep
resource costAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = {
  name: 'alert-daily-cost-threshold'
  location: 'eastus'
  properties: {
    displayName: 'Daily Cost Exceeds $100'
    description: 'Alert when daily LLM costs exceed $100'
    severity: 2
    enabled: true
    evaluationFrequency: 'PT1H'  // Every hour
    windowSize: 'P1D'  // Look at last 24 hours
    criteria: {
      allOf: [
        {
          query: '''
            customMetrics
            | where name == "agent.cost"
            | where timestamp > ago(1d)
            | summarize TotalCost = sum(value)
            | where TotalCost > 100
          '''
          threshold: 100
          operator: 'GreaterThan'
        }
      ]
    }
    actions: {
      actionGroups: ['/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Insights/actionGroups/ag-alerts']
    }
  }
}
```

### Estimated Monthly Costs (100 users, 1000 messages/day)

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| Container Apps (Frontend) | 2-10 replicas, 0.5 vCPU, 1Gi | $30-150 |
| Container Apps (Backend) | 2-20 replicas, 1 vCPU, 2Gi | $60-600 |
| Cosmos DB | Autoscale 400-4000 RU/s | $25-200 |
| Azure OpenAI (GPT-4o) | 500K tokens/day avg | $75 (input) + $225 (output) = $300 |
| Storage | 10 GB logs/exports | $0.50 |
| Key Vault | 10K operations/month | $0.50 |
| App Configuration | Standard tier | $1 |
| Application Insights | 5 GB ingestion/month | $10 |
| API Management | Developer tier | $50 |
| Virtual Network | Standard | $0 (included) |
| Private Endpoints | 6 endpoints | $6 |
| **Total** | | **$558-1,543/month** |

**Cost Optimization Target:** < $500/month via:
- Token budget enforcement (reduce GPT-4o usage by 30%)
- Telemetry sampling (reduce App Insights by 50%)
- Caching MCP responses (reduce external calls by 20%)

---

## Failure Modes & Resilience

### Failure Scenarios & Mitigations

| Failure | Impact | Detection | Mitigation | Recovery Time |
|---------|--------|-----------|------------|---------------|
| **Azure OpenAI Outage** | Agents can't generate responses | Health check fails, 503 errors | Retry with exponential backoff, fallback to GPT-4.1 if GPT-5 unavailable | 1-5 min (automatic) |
| **Cosmos DB Outage** | Can't persist/retrieve state | Connection errors, 503 | Retry logic, circuit breaker | 5-15 min (Azure SLA) |
| **Key Vault Outage** | Can't retrieve secrets | Auth errors | Use cached secrets (1 hour TTL) | 5-15 min (Azure SLA) |
| **MCP Server Unreachable** | Tool calls fail | HTTP timeouts, 503 | Graceful degradation (agent works without tool) | Depends on MCP server |
| **adventure-mcp OAuth2 Failure** | SQL Agent can't query | 401 errors | Refresh token, fallback to mock data | 1 min (token refresh) |
| **Backend Container Crash** | Requests fail | Health check fails | Container Apps auto-restart, reroute to healthy replicas | 10-30 sec |
| **Frontend Container Crash** | UI unavailable | Health check fails | Container Apps auto-restart, reroute | 10-30 sec |
| **VNet Connectivity Issue** | Private endpoints unreachable | Network errors | NSG rule review, reboot NICs | 5-30 min (manual) |
| **Entra ID Auth Failure** | Users can't login | MSAL errors | Retry login, check Entra ID status | 1-5 min (Azure SLA) |

### Retry Policies

**Cosmos DB:**

```python
# persistence/cosmos_client.py

from azure.cosmos import CosmosClient, exceptions
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def query_items(container, query, partition_key):
    try:
        items = list(container.query_items(
            query=query,
            partition_key=partition_key,
            enable_cross_partition_query=False
        ))
        return items
    except exceptions.CosmosHttpResponseError as e:
        if e.status_code == 429:  # Rate limited
            raise  # Retry
        elif e.status_code >= 500:  # Server error
            raise  # Retry
        else:
            raise  # Don't retry client errors
```

**MCP Client:**

```python
# tools/mcp_client.py

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True
)
async def call_tool(self, tool_name: str, parameters: dict) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{self.endpoint}/tools/{tool_name}",
            json=parameters,
            headers=self.auth_headers
        )
        response.raise_for_status()
        return response.json()
```

### Circuit Breaker Pattern

```python
# tools/circuit_breaker.py

from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures exceed threshold, stop requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.now()
            
            if self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
            
            raise

# Usage
adventure_mcp_breaker = CircuitBreaker(failure_threshold=3, timeout=60)

async def query_sql(query: str):
    return adventure_mcp_breaker.call(adventure_mcp.query_sql, query)
```

---

## Operational Procedures

### Deployment Procedure

```bash
# 1. Deploy infrastructure (Bicep)
cd infra
az deployment group create \
  --resource-group rg-agents-demo \
  --template-file main.bicep \
  --parameters parameters/prod.bicepparam

# 2. Store secrets in Key Vault
az keyvault secret set --vault-name kv-agents-demo \
  --name adventure-mcp-client-secret --value "<secret>"

# 3. Build and push container images
cd backend
docker build -t acragentsdemo.azurecr.io/backend:latest .
docker push acragentsdemo.azurecr.io/backend:latest

cd ../frontend
docker build -t acragentsdemo.azurecr.io/frontend:latest .
docker push acragentsdemo.azurecr.io/frontend:latest

# 4. Deploy containers to Container Apps
az containerapp update \
  --name ca-agents-backend \
  --resource-group rg-agents-demo \
  --image acragentsdemo.azurecr.io/backend:latest

az containerapp update \
  --name ca-agents-frontend \
  --resource-group rg-agents-demo \
  --image acragentsdemo.azurecr.io/frontend:latest

# 5. Seed default agents
python scripts/seed-agents.py

# 6. Run smoke tests
pytest tests/e2e/test_health.py
```

### Monitoring & Alerts

**Key Dashboards (Application Insights):**

1. **Agent Performance Dashboard**
   - Requests per agent (bar chart)
   - Average response time (line chart)
   - Token usage (area chart)
   - Tool call latency (histogram)

2. **A2A Orchestration Dashboard**
   - A2A calls per agent (bar chart)
   - A2A call latency (line chart)
   - Success/failure rate (pie chart)

3. **Cost & Usage Dashboard**
   - Daily token usage (bar chart)
   - Daily cost (line chart)
   - Cost per user (table)
   - Cost per agent (pie chart)

**KQL Queries:**

```kql
// Top 10 slowest requests
requests
| where timestamp > ago(1h)
| summarize avg(duration) by name
| top 10 by avg_duration desc

// A2A call success rate
dependencies
| where name startswith "a2a."
| summarize Total = count(), Failures = countif(success == false) by name
| extend SuccessRate = (Total - Failures) * 100.0 / Total

// Daily token usage by agent
customMetrics
| where name == "agent.tokens"
| where timestamp > ago(7d)
| summarize TotalTokens = sum(value) by bin(timestamp, 1d), tostring(customDimensions.agent_id)
| render columnchart
```

### Incident Response Runbook

**Scenario: High Latency (p95 > 10s)**

1. Check Application Insights:
   - Identify slow requests (KQL: `requests | where duration > 10000`)
   - Check dependencies (Cosmos DB, Azure OpenAI, MCP servers)

2. Check Azure OpenAI:
   - Go to Azure OpenAI resource → Metrics → Token Usage
   - Check for rate limiting (429 errors)
   - If rate limited: increase quota or reduce load

3. Check Cosmos DB:
   - Go to Cosmos DB → Metrics → Request Units
   - Check for throttling (429 errors)
   - If throttled: increase RU/s or optimize queries

4. Check MCP Servers:
   - Test Microsoft Learn MCP: `curl https://learn.microsoft.com/api/mcp/health`
   - Test adventure-mcp: `curl https://mssqlmcp.azure-api.net/health`
   - If unreachable: enable circuit breaker, notify MCP server owner

5. Scale Container Apps:
   - Temporarily increase max replicas: `az containerapp update --max-replicas 30`

**Scenario: High Cost (>$100/day)**

1. Check Application Insights Cost Dashboard:
   - Identify top users by token usage
   - Identify top agents by token usage

2. Enforce token budgets:
   - Lower daily token limit: `DAILY_TOKEN_LIMIT = 50_000`
   - Notify high-usage users via email

3. Optimize prompts:
   - Review agent system prompts for verbosity
   - Reduce `max_tokens` parameter

4. Increase caching:
   - Cache more MCP responses (extend TTL)
   - Cache Azure OpenAI responses (if possible)

### Maintenance Windows

**Weekly Maintenance (Sundays, 2-4 AM UTC):**
- Check for Azure service updates
- Rotate API keys (if needed)
- Review audit logs for anomalies
- Clean up old test data (if not handled by TTL)

**Monthly Maintenance:**
- Review cost trends and optimize
- Update Bicep templates with new features
- Test disaster recovery procedures (backup/restore)
- Refresh Entra ID app registrations (if needed)

---

## Conclusion

This architecture provides a production-ready, secure, scalable, and cost-effective platform for showcasing AI agents with Microsoft's Agent Framework SDK. Key architectural highlights:

- **Azure-only infrastructure** with private networking and Managed Identity
- **5 fully functional agents** demonstrating MCP, OpenAPI, and A2A protocols
- **Real-time streaming** with inline trace visualization
- **Comprehensive observability** with cost tracking and PII redaction
- **Defense-in-depth security** with multiple layers of protection
- **Autoscaling** to handle variable workloads
- **Cost controls** to keep monthly spend under $500

The architecture is designed to be both **impressive for customer demos** and **reusable for POCs**, with clear separation of concerns, extensive documentation, and operational runbooks.

**Next Steps**: Proceed to `03-overview.md` for the executive summary and quickstart guide (README).

---

*End of Architecture Documentation (3 parts completed).*
