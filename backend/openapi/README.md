# OpenAPI Specifications

This directory contains OpenAPI 3.0 specifications for mock APIs used in the AI Agents Demo.

## Available APIs

### 1. Support Triage API (`support-triage-api.yaml`)

Mock API for searching support tickets and knowledge base articles.

**Endpoints:**
- `GET /tickets/search` - Search support tickets
- `GET /tickets/{ticketId}` - Get ticket details
- `GET /kb/search` - Search knowledge base articles

**Use Case:** Support Triage Agent uses this API to:
- Find similar existing tickets
- Search KB articles for solutions
- Ground responses in actual support data

**Example Usage:**
```bash
# Search for Azure Storage tickets
curl -H "X-API-Key: demo-key" \
  "https://api.example.com/support/tickets/search?query=Azure+Storage+connection&status=open"

# Search KB for troubleshooting articles
curl -H "X-API-Key: demo-key" \
  "https://api.example.com/support/kb/search?query=authentication+errors"
```

### 2. Ops Assistant API (`ops-assistant-api.yaml`)

Mock API for managing Azure deployments and operations.

**Endpoints:**
- `GET /deployments/status` - Get current deployment status
- `GET /deployments/history` - Get deployment history
- `POST /deployments/rollback` - Initiate a rollback
- `GET /deployments/{rollbackId}` - Get rollback status

**Use Case:** Azure Ops Assistant Agent uses this API to:
- Check deployment health
- Review deployment history
- Execute rollbacks when needed
- Monitor ongoing operations

**Example Usage:**
```bash
# Get production deployment status
curl -H "X-API-Key: demo-key" \
  "https://api.example.com/ops/deployments/status?environment=production"

# Initiate a rollback
curl -X POST -H "X-API-Key: demo-key" -H "Content-Type: application/json" \
  -d '{"service": "backend-api", "version": "v2.4.8", "environment": "production"}' \
  "https://api.example.com/ops/deployments/rollback"
```

## Implementation Options

### Option 1: Mock Server (Development)

For local development and testing, use a mock server:

```bash
# Using Prism (recommended)
npm install -g @stoplight/prism-cli
prism mock openapi/support-triage-api.yaml --port 8001
prism mock openapi/ops-assistant-api.yaml --port 8002
```

### Option 2: Azure API Management (Production)

For production deployment:

1. **Create API Management instance** (via Bicep)
2. **Import OpenAPI specs** to APIM
3. **Configure mock backends** with example responses
4. **Set policies**:
   - Rate limiting (100 req/min per user)
   - Caching (5 min for KB searches)
   - API key authentication
5. **Store API keys** in Key Vault

### Option 3: Simple Express Mock Server

For quick testing, use a simple Express server:

```javascript
// mock-server.js
const express = require('express');
const app = express();

app.get('/support/tickets/search', (req, res) => {
  res.json({
    total: 3,
    tickets: [/* ... example data ... */]
  });
});

app.listen(8000);
```

## Validation

Validate the OpenAPI specs:

```bash
# Using openapi-cli
npm install -g @redocly/openapi-cli
openapi validate openapi/support-triage-api.yaml
openapi validate openapi/ops-assistant-api.yaml
```

## Authentication

Both APIs use API Key authentication:
- Header: `X-API-Key`
- Value: API key (stored in Key Vault)

**Development:** Use a dummy key like `demo-key`
**Production:** Generate secure keys and store in Key Vault

## Testing with the APIs

Example test scenarios:

### Support Triage Agent
```
User: "Find tickets about Azure Storage authentication errors"
Agent: Uses /tickets/search with query="Azure Storage authentication"
Agent: Returns summary of matching tickets
```

### Azure Ops Assistant
```
User: "What's the status of our production deployments?"
Agent: Calls /deployments/status?environment=production
Agent: Reports on health and any issues
```

## Next Steps

1. ✅ Create OpenAPI specs (completed)
2. 🔄 Implement OpenAPI client in Python
3. 🔄 Write tests for OpenAPI client
4. ⏭️ Deploy mock server or APIM
5. ⏭️ Integrate with agents

## Resources

- [OpenAPI 3.0 Specification](https://swagger.io/specification/)
- [Prism Mock Server](https://stoplight.io/open-source/prism)
- [Azure API Management](https://learn.microsoft.com/en-us/azure/api-management/)
