# Azure MCP Server - Agentarium

Model Context Protocol (MCP) server for Azure resource access. Enables LLM agents to discover and interact with Azure resources including App Services, Virtual Machines, Cosmos DB, Storage Accounts, Key Vaults, and more.

## Overview

This MCP server runs as a sidecar container alongside the backend API and provides Azure resource tools accessible to agent implementations. It uses the Model Context Protocol to expose Azure operations through a standardized interface.

### Features

- **Multiple Authentication Methods**
  - Managed Identity (production default)
  - Service Principal
  - Azure CLI Credential (local development)

- **Azure Resource Tools**
  - List resources with filtering
  - Resource group operations
  - App Service management
  - Virtual Machine operations
  - Cosmos DB queries
  - Storage Account access
  - Key Vault operations (listing only)
  - Log Analytics queries

- **Production-Ready**
  - Health checks and monitoring
  - Request/response logging
  - Response caching with TTL
  - Rate limiting
  - Error handling and recovery
  - Multi-stage Docker build
  - Non-root container user

## Prerequisites

- Node.js 18+ (for local development)
- Docker (for containerized deployment)
- Azure subscription with appropriate permissions
- Azure CLI (for local development with Azure CLI credential)

### Authentication Requirements

**For Local Development:**
```bash
az login
```

**For Managed Identity (Production):**
- Assign the managed identity the appropriate Azure RBAC roles:
  - `Reader` role for resource listing
  - Specific roles for resource modifications

**For Service Principal (Alternative):**
- Create a service principal and assign appropriate RBAC roles
- Set environment variables: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`

## Installation

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Update the required variables:
- `AZURE_SUBSCRIPTION_ID` - Your Azure subscription ID
- `NODE_ENV` - Set to `development` or `production`

### 3. Select Configuration

The server loads configuration from `config/dev.json` or `config/prod.json` based on `NODE_ENV`:

```bash
# Development (uses Azure CLI credentials)
NODE_ENV=development npm start

# Production (uses Managed Identity)
NODE_ENV=production npm start
```

## Configuration

### Configuration Files

- **`config/schema.json`** - JSON schema defining all configuration options
- **`config/dev.json`** - Development environment configuration
- **`config/prod.json`** - Production environment configuration

### Configuration Structure

```json
{
  "server": {
    "port": 3000,
    "host": "0.0.0.0",
    "protocol": "http"
  },
  "authentication": {
    "type": "managedIdentity",
    "managedIdentity": {}
  },
  "azure": {
    "subscriptionId": "${AZURE_SUBSCRIPTION_ID}",
    "resourceScope": "subscription",
    "environment": "AzureCloud"
  },
  "tools": {
    "resources": true,
    "resourceGroups": true,
    "appServices": true,
    "containerInstances": true,
    "virtualMachines": true,
    "cosmos": true,
    "storage": true,
    "keyVault": true,
    "monitoring": true
  },
  "logging": {
    "level": "info",
    "format": "json"
  },
  "caching": {
    "enabled": true,
    "ttlSeconds": 300
  },
  "rateLimit": {
    "enabled": true,
    "requestsPerSecond": 10,
    "burstSize": 20
  }
}
```

### Environment Variable Substitution

Configuration files support environment variable substitution using `${VAR_NAME}` syntax:

```json
{
  "azure": {
    "subscriptionId": "${AZURE_SUBSCRIPTION_ID}"
  }
}
```

Environment variables are replaced when configuration is loaded.

## Running the Server

### Local Development

```bash
# Using Azure CLI credentials
npm run dev

# Server will be available at http://localhost:3000
```

### Production

```bash
npm run prod
```

### Docker

```bash
# Build image
npm run docker:build

# Run with development credentials
npm run docker:run:dev

# Run in production mode (detached)
npm run docker:run:prod
```

### Docker Compose

```bash
# Start MCP server with Docker Compose
docker-compose up -d mcp-server

# Start with backend API for integration testing
docker-compose --profile with-backend up -d

# View logs
docker-compose logs -f mcp-server

# Stop
docker-compose down
```

## API Endpoints

### Health Check

```bash
curl http://localhost:3000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-20T12:00:00.000Z",
  "config": {
    "authentication": "managedIdentity",
    "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "resourceScope": "subscription"
  }
}
```

### List Tools

```bash
curl http://localhost:3000/tools
```

Response:
```json
{
  "tools": [
    {
      "name": "list_resources",
      "description": "List all Azure resources in the subscription",
      "inputSchema": { ... }
    },
    ...
  ],
  "count": 8
}
```

### List Resources

```bash
curl -X POST http://localhost:3000/tools/list_resources \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

### List Resource Groups

```bash
curl -X POST http://localhost:3000/tools/list_resource_groups \
  -H "Content-Type: application/json" \
  -d '{"limit": 50}'
```

### List App Services

```bash
curl -X POST http://localhost:3000/tools/list_app_services \
  -H "Content-Type: application/json" \
  -d '{"resourceGroup": "my-rg"}'
```

## Available Tools

The server exposes the following MCP tools (configurable):

| Tool | Enabled | Description |
|------|---------|-------------|
| `list_resources` | ✓ | List all resources in subscription |
| `list_resource_groups` | ✓ | List resource groups |
| `list_app_services` | ✓ | List App Services |
| `list_virtual_machines` | ✓ | List VMs |
| `list_cosmos_accounts` | ✓ | List Cosmos DB accounts |
| `list_storage_accounts` | ✓ | List Storage accounts |
| `list_key_vaults` | ✓ | List Key Vaults |
| `query_logs` | ✓ | Query Log Analytics |

To disable specific tools, modify `config/dev.json` or `config/prod.json` and set tool to `false`.

## Development

### Project Structure

```
mcp-server/
├── server.js              # Main server application
├── config-loader.js       # Configuration loader with validation
├── package.json           # Node.js project config
├── Dockerfile             # Container image
├── docker-compose.yml     # Local testing setup
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
├── config/
│   ├── schema.json        # Configuration JSON schema
│   ├── dev.json           # Development configuration
│   └── prod.json          # Production configuration
├── tests/                 # Test files (to be created)
└── README.md              # This file
```

### Configuration Validation

Validate configuration without starting the server:

```bash
# Validate and print dev configuration
npm run config:show:dev

# Validate and print prod configuration
npm run config:show:prod

# Validate configuration
npm run config:validate
```

### Health Monitoring

Check server health:

```bash
npm run health
```

### List Available Tools

Check what tools are available:

```bash
npm run tools:list
```

### Logging

The server logs all requests and errors using Pino logger. Configure logging level in configuration:

- **debug** - Detailed request/response information
- **info** - General operational information
- **warn** - Warning messages
- **error** - Error messages only

Output format can be:
- **json** - Machine-readable JSON format
- **text** - Human-readable text format (default for development)

## Security Considerations

### Authentication

- **Managed Identity (Production)**: Recommended. Uses Azure-assigned managed identity with no credentials to manage.
- **Service Principal**: Requires secure credential storage. Use Key Vault for production.
- **Azure CLI (Development)**: For local development only. Never use in production.

### Network Security

- Container runs on `127.0.0.1` in production (localhost only - access via backend)
- Container runs on `0.0.0.0` in development (accessible from external clients)
- Private networking via shared container network

### RBAC

- MCP server should have minimal required permissions
- Recommended role: `Reader` for resource listing
- For modifications: Assign specific resource roles as needed

### Key Vault

- Key Vault tool lists vaults only - secrets are not retrieved
- Use backend API for secure secret access via managed identity

## Troubleshooting

### "Configuration missing required field"

Ensure all required fields are present in configuration file:
- `server.port`, `server.host`, `server.protocol`
- `authentication.type`
- `azure.subscriptionId`

### "Failed to acquire token"

Development:
```bash
# Ensure Azure CLI is authenticated
az login
az account show
```

Production:
```bash
# Ensure managed identity is assigned to container app
# Check RBAC role assignments
```

### "Cannot connect to server"

Check if server is running:
```bash
curl http://localhost:3000/health
```

### "Rate limit exceeded"

The server enforces rate limiting. Adjust `rateLimit` in configuration:

```json
{
  "rateLimit": {
    "requestsPerSecond": 20,
    "burstSize": 50
  }
}
```

### "Tool returns no results"

1. Verify authentication has appropriate permissions
2. Check Azure subscription ID is correct
3. Verify resource scope in configuration

## Testing

### Manual Testing

```bash
# Start the server
npm run dev

# In another terminal, test endpoints
curl http://localhost:3000/health
curl http://localhost:3000/tools
curl -X POST http://localhost:3000/tools/list_resources -H "Content-Type: application/json" -d '{}'
```

### Integration Testing

```bash
# Start with backend API
docker-compose --profile with-backend up -d

# Test MCP server can reach backend
curl http://localhost:3000/health
```

### Docker Testing

```bash
# Build and run container
docker build -t agentdemo-mcp-server .
docker run -e AZURE_SUBSCRIPTION_ID=your-sub-id agentdemo-mcp-server npm run dev
```

## Performance Tuning

### Caching

Enable response caching for frequently accessed data:

```json
{
  "caching": {
    "enabled": true,
    "ttlSeconds": 600
  }
}
```

### Rate Limiting

Adjust rate limits based on expected load:

```json
{
  "rateLimit": {
    "requestsPerSecond": 20,
    "burstSize": 100
  }
}
```

### Logging

Reduce verbosity in production:

```json
{
  "logging": {
    "level": "info",
    "format": "json"
  }
}
```

## Deployment

### Azure Container Apps

The MCP server is deployed as a sidecar container alongside the backend API in Azure Container Apps:

1. Configured in `infra/modules/container-apps.bicep`
2. Uses managed identity for authentication
3. Shared localhost network with backend
4. Health checks configured for monitoring

### Environment

- **Dev**: Uses Azure CLI credentials for local testing
- **Prod**: Uses system-assigned managed identity

## Contributing

When adding new tools:

1. Define the tool in `/tools` endpoint
2. Add handler in the appropriate POST endpoint
3. Add configuration flag to enable/disable
4. Update schema.json
5. Update this README

## License

See LICENSE file in project root.

## Next Steps

1. Install dependencies: `npm install`
2. Configure subscription: `cp .env.example .env && edit .env`
3. Test locally: `npm run dev`
4. Check tools: `npm run tools:list`
5. Deploy in Phase 1.5 infrastructure deployment

