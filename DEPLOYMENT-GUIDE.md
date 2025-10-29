# Deployment Guide

## Overview

This project uses two deployment mechanisms:

1. **GitHub Actions** - Automated deployments for code changes (image-only updates)
2. **Bicep Templates** - Full infrastructure deployments including environment variables

## GitHub Actions (Automatic)

GitHub Actions automatically deploy when you push code changes:

- **Backend**: Triggers on `[backend]` or `[all]` in commit message
- **Frontend**: Triggers on `[frontend]` or `[all]` in commit message

**What it does:**
- Builds Docker images
- Pushes to Azure Container Registry
- Updates Container Apps with new image

**What it DOES NOT do:**
- Update environment variables
- Modify infrastructure configuration
- Change networking or scaling settings

## Bicep Deployment (Manual)

Use Bicep deployment when you need to:
- Add/modify environment variables
- Change infrastructure configuration
- Initial setup of resources
- Update networking, scaling, or other infrastructure settings

### Running Bicep Deployment

```powershell
cd infra
.\deploy.ps1 -Environment dev
```

**Important:** Bicep deployment will:
- Create/update all Azure resources
- Configure environment variables from `infra/parameters/dev.bicepparam`
- Override any manual changes made via Azure Portal or CLI

## Environment Variables Configuration

### Local Development (.env file)

The `backend/.env` file is for **local development only**. It is NOT deployed to production.

Example:
```
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_OPENAI_KEY=your-key
MSSQL_MCP_URL=https://mssqlmcp.azure-api.net/mcp
MSSQL_CLIENT_ID=your-client-id
MSSQL_CLIENT_SECRET=your-client-secret
```

### Production (Azure Container Apps)

Production environment variables are configured in:
- `infra/modules/container-apps.bicep` (parameter definitions)
- `infra/main.bicep` (parameter passing)
- `infra/parameters/dev.bicepparam` (actual values)

**To add a new environment variable:**

1. Add parameter to `infra/modules/container-apps.bicep`:
   ```bicep
   @description('My new variable')
   param myNewVariable string = ''
   ```

2. Add to container environment variables section:
   ```bicep
   {
     name: 'MY_NEW_VARIABLE'
     value: myNewVariable
   }
   ```

3. Add parameter to `infra/main.bicep`:
   ```bicep
   @description('My new variable')
   param myNewVariable string = ''
   ```

4. Pass to module in `infra/main.bicep`:
   ```bicep
   module containerAppsModule './modules/container-apps.bicep' = {
     params: {
       ...
       myNewVariable: myNewVariable
     }
   }
   ```

5. Add value to `infra/parameters/dev.bicepparam`:
   ```bicep
   param myNewVariable = 'my-value'
   ```

6. Run Bicep deployment:
   ```powershell
   cd infra
   .\deploy.ps1 -Environment dev
   ```

## Sensitive Values

For sensitive values (API keys, secrets):

1. Mark parameter as `@secure()` in Bicep files
2. Store actual values in:
   - `infra/parameters/dev.bicepparam` (for dev)
   - GitHub Secrets (for CI/CD if needed)
   - Azure Key Vault (for production)

Example:
```bicep
@secure()
@description('API key')
param apiKey string = ''
```

## Current Environment Variables

### Azure OpenAI (Required)
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL
- `AZURE_OPENAI_KEY` - Azure OpenAI API key (secret)
- `AZURE_OPENAI_API_VERSION` - API version (default: 2025-03-01-preview)

### MSSQL MCP OAuth (Required for Sales Agent)
- `MSSQL_MCP_URL` - MSSQL MCP server URL
- `MSSQL_OAUTH_TOKEN_URL` - OAuth token endpoint
- `MSSQL_CLIENT_ID` - OAuth client ID
- `MSSQL_CLIENT_SECRET` - OAuth client secret (secret)
- `MSSQL_SCOPE` - OAuth scope

### Cosmos DB (Automatic)
- `COSMOS_ENDPOINT` - Cosmos DB endpoint (auto-configured)
- `COSMOS_DATABASE_NAME` - Database name (default: agents-db)

### Application Insights (Automatic)
- `APPLICATIONINSIGHTS_INSTRUMENTATION_KEY` - App Insights key (secret)

## Troubleshooting

### "Environment variable not set in production"

**Symptoms:** Works locally but not in Azure Container Apps

**Cause:** `.env` file only applies to local development

**Solution:** Add environment variable to Bicep templates and run full deployment

### "Agent hangs or times out"

**Symptoms:** Agent initialization succeeds but `agent.run()` hangs

**Possible Causes:**
1. Missing OAuth credentials for MCP tools
2. Network connectivity issues
3. Invalid API keys

**Solution:**
1. Check Container App environment variables: `az containerapp show --name ca-backend-dev --resource-group rg-agentdemo-dev --query "properties.template.containers[0].env"`
2. Verify OAuth credentials are configured
3. Check Container App logs: `az containerapp logs show --name ca-backend-dev --resource-group rg-agentdemo-dev --follow`

### "GitHub Actions deployment doesn't include my changes"

**Symptoms:** Environment variable changes don't appear after GitHub Actions runs

**Cause:** GitHub Actions only updates the container image, not infrastructure

**Solution:** Run Bicep deployment manually for infrastructure changes

## Best Practices

1. **Always add environment variables to both:**
   - Backend `.env` (for local development)
   - Bicep templates (for production)

2. **Commit message tags:**
   - `[backend]` - Deploy backend changes
   - `[frontend]` - Deploy frontend changes
   - `[all]` - Deploy both
   - `[infra]` - Infrastructure changes (manual deployment required)

3. **Test locally first:**
   - Verify changes work with `.env` configuration
   - Then add to Bicep templates
   - Deploy to Azure

4. **Keep secrets secure:**
   - Never commit actual secrets to Git
   - Use placeholder values in committed files
   - Store real secrets in Azure Key Vault or parameter files (gitignored)

5. **Version your deployments:**
   - GitHub Actions automatically versions images
   - Bicep deployments are named with timestamp
   - Container Apps keeps revision history
