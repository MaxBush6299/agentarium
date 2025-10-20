# AI Agents Demo - Infrastructure Setup

> **⚠️ IMPORTANT**: Due to an Azure CLI bug with `.bicepparam` files, use the PowerShell deployment script which includes automatic workarounds:
> ```powershell
> .\infra\deploy.ps1 -Environment dev
> ```
> This script automatically creates all resources including Cosmos DB collections.

## Quick Start

### Option 1: PowerShell Script (Recommended ✅)

```powershell
# Deploy to development environment
.\infra\deploy.ps1 -Environment dev

# Deploy to production environment  
.\infra\deploy.ps1 -Environment prod
```

**Benefits:**
- ✅ Handles Azure CLI deployment bugs automatically
- ✅ Creates Cosmos DB collections if deployment skips them
- ✅ Validates all resources post-deployment
- ✅ Provides clear error messages and next steps

### Option 2: Manual Azure CLI (Advanced Users)

### 1. **Setup Environment Variables**

```bash
# Copy the template
cp .env.template .env

# Edit .env with your actual values
nano .env  # or use your preferred editor
```

**Key variables to set:**
- `AZURE_SUBSCRIPTION_ID` - Your Azure subscription ID
- `AZURE_RESOURCE_GROUP` - Name for the resource group to create
- `AZURE_REGION` - Azure region (default: eastus)
- `ENVIRONMENT_NAME` - dev, staging, or prod
- `OPENAI_API_KEY` - Your OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - If using Azure OpenAI
- `AZURE_OPENAI_API_KEY` - If using Azure OpenAI

### 2. **Deploy Infrastructure**

```bash
# Validate the deployment
az bicep build --file infra/main.bicep

# Deploy using dev parameters
az deployment group create \
  --resource-group $(grep AZURE_RESOURCE_GROUP .env | cut -d'=' -f2) \
  --template-file infra/main.bicep \
  --parameters @infra/parameters/dev.bicepparam

# Or deploy using prod parameters
az deployment group create \
  --resource-group $(grep AZURE_RESOURCE_GROUP .env | cut -d'=' -f2) \
  --template-file infra/main.bicep \
  --parameters @infra/parameters/prod.bicepparam
```

## Project Structure

```
.
├── .env                          # ❌ DO NOT COMMIT - Local environment variables
├── .env.template                 # ✅ Template for environment setup
├── .gitignore                    # Prevents .env from being committed
├── infra/
│   ├── bicep.config.json         # Bicep compiler configuration
│   ├── main.bicep                # Main orchestration template
│   ├── modules/
│   │   ├── network.bicep         # VNet, subnets, NSGs
│   │   ├── cosmos-db.bicep       # Cosmos DB with 6 collections
│   │   ├── key-vault.bicep       # Key Vault with RBAC
│   │   ├── storage.bicep         # Storage account for logs/exports
│   │   ├── private-endpoints.bicep # Private endpoints & DNS zones
│   │   ├── container-apps.bicep  # Container Apps environment
│   │   └── observability.bicep   # Log Analytics + App Insights
│   └── parameters/
│       ├── dev.bicepparam        # Development environment
│       └── prod.bicepparam       # Production environment
└── documentation/                # Architecture and design docs
```

## Bicep File Reference

### main.bicep
**Purpose:** Orchestration template that coordinates all modules  
**Key Outputs:**
- VNet resource ID
- Cosmos DB endpoint
- Key Vault URI
- Container Apps FQDNs

### Network Module (network.bicep)
**Deploys:**
- Virtual Network (10.0.0.0/16)
- 3 Subnets (Container Apps, Private Endpoints, Integration)
- Network Security Groups with least-privilege rules

**Parameters:**
- `vnetAddressSpace` - VNet CIDR block
- `containerAppsSubnetAddressSpace` - Container Apps subnet CIDR
- `privateEndpointsSubnetAddressSpace` - PE subnet CIDR
- `integrationSubnetAddressSpace` - Integration subnet CIDR

### Cosmos DB Module (cosmos-db.bicep)
**Deploys:**
- Cosmos DB SQL API account
- Database with 6 collections:
  - `threads` - Conversation threads (partition: agentId)
  - `runs` - Agent executions (partition: threadId)
  - `steps` - Execution steps (partition: runId)
  - `toolCalls` - Tool invocations (partition: stepId)
  - `agents` - Agent metadata (partition: agentType)
  - `metrics` - Performance metrics (partition: timestamp)

**Collections Features:**
- Automatic TTL (90 days for data, 60 days for metrics)
- Autoscale throughput (400-4000 RU/s)
- Unique key constraints on collection IDs
- Comprehensive indexing

**Parameters:**
- `accountName` - Cosmos DB account name
- `throughputMode` - "manual" or "autoscale"
- `autoscaleMaxThroughput` - Max RU/s for autoscale
- `databaseName` - Database name
- `enableBackupRedundancy` - Geo-redundant backups

### Key Vault Module (key-vault.bicep)
**Deploys:**
- Azure Key Vault with RBAC
- 5 Placeholder secrets:
  - openai-api-key
  - cosmosdb-connection-string
  - appconfig-connection-string
  - storage-connection-string
  - apim-subscription-key
- Role assignments for Managed Identity

**Features:**
- Soft delete enabled (90 days retention)
- Purge protection optional
- Network ACLs for private endpoints
- RBAC-based access control

### Storage Module (storage.bicep)
**Deploys:**
- StorageV2 account with Hot tier
- Private endpoint support
- 3 Blob containers (logs, artifacts, exports)

**Parameters:**
- `accountName` - Storage account name
- `enableHierarchicalNamespace` - HNS for Data Lake
- `minimumTlsVersion` - TLS1_2 or higher
- `privateEndpointsEnabled` - Enable PE support

### Private Endpoints Module (private-endpoints.bicep)
**Deploys:**
- 3 Private endpoints:
  - Cosmos DB (SQL)
  - Key Vault (vault)
  - Storage (blob)
- 3 Private DNS zones with A records:
  - privatelink.documents.azure.com
  - privatelink.vaultcore.azure.net
  - privatelink.blob.core.windows.net
- VNet DNS zone links

### Container Apps Module (container-apps.bicep)
**Deploys:**
- Container Apps Environment in VNet
- Frontend app (0.5 vCPU, 1 Gi, 1-3 replicas)
- Backend app (1 vCPU, 2 Gi, 1-5 replicas)
- Application Insights integration

**Features:**
- Auto-scaling based on HTTP concurrency
- VNet integration for private connectivity
- Log Analytics workspace integration

### Observability Module (observability.bicep)
**Deploys:**
- Log Analytics Workspace
- Application Insights
- Container Insights solution

**Parameters:**
- `logAnalyticsWorkspaceName` - LAW name
- `appInsightsName` - App Insights name
- `logRetentionDays` - Retention period
- `appInsightsDailyCapGb` - Daily data cap

## Environment Configuration

### Development (.bicepparam)
- **Cosmos DB:** Manual 400 RU/s
- **Key Vault:** Soft delete without purge protection
- **Storage:** Standard LRS
- **Container Apps:** 0.5 vCPU frontend, 1 vCPU backend
- **Monitoring:** 7-day retention

### Production (.bicepparam)
- **Cosmos DB:** Autoscale 400-4000 RU/s with geo-backup
- **Key Vault:** Soft delete with purge protection, private endpoints
- **Storage:** Premium tier with HNS enabled
- **Container Apps:** 1 vCPU frontend, 2 vCPU backend
- **Monitoring:** 30-day retention, 10 GB daily cap

## Security Best Practices

✅ **Implemented:**
- Network Security Groups with least-privilege rules
- Private endpoints for all data services
- Private DNS zones to block public resolution
- RBAC for Key Vault access
- Managed Identity support
- TLS 1.2+ enforcement
- Soft delete and purge protection for Key Vault
- Network ACLs on all resources

⚠️ **Post-Deployment Actions:**
1. Update Key Vault secrets with actual values
2. Configure private DNS resolver for hybrid scenarios
3. Set up Network Watcher diagnostics
4. Configure backup and disaster recovery
5. Implement monitoring alerts and dashboards

## Troubleshooting

### ⚠️ "DeploymentNotFound" Error (Known Issue)

**Symptom:** Deployment returns `{"error":{"code":"DeploymentNotFound"}}` but resources appear in Azure Portal.

**Cause:** Known Azure CLI bug with `.bicepparam` files (tracked issue #31709, fixed in v2.76.0+ but still occurs intermittently).

**Solution:** Use `deploy.ps1` which handles this automatically, or run the post-deploy script manually:
```powershell
.\infra\post-deploy-setup.ps1 -Environment dev
```

This will:
- ✅ Verify all resources exist
- ✅ Create missing Cosmos DB collections
- ✅ Validate Container Apps

### Missing Cosmos DB Collections

**Symptom:** Cosmos DB account exists but has no collections.

**Cause:** Side effect of the DeploymentNotFound bug.

**Automatic Fix:** The `deploy.ps1` script runs `post-deploy-setup.ps1` automatically.

**Manual Fix:**
```powershell
# Run post-deployment setup
.\infra\post-deploy-setup.ps1 -Environment dev

# Verify collections
az cosmosdb sql container list \
  --account-name <cosmos-account-name> \
  --database-name agents-db \
  --resource-group rg-agentdemo-dev \
  --output table
```

Should show 6 collections: `threads`, `runs`, `steps`, `toolCalls`, `agents`, `messages`

### Container Apps Can't Connect to Cosmos DB

**Symptom:** Container Apps fail with connection errors to Cosmos DB.

**Cause:** Cosmos DB deployed with `publicNetworkAccess: 'Disabled'` but no private endpoints.

**Temporary Fix (Development):**
```powershell
az cosmosdb update \
  --name <cosmos-account-name> \
  --resource-group rg-agentdemo-dev \
  --enable-public-network true
```

**Permanent Fix (Production):** Create private endpoints (see docs/private-endpoints.md)

### Bicep Compilation Issues
```bash
# Validate Bicep syntax
az bicep build --file infra/main.bicep

# Check Bicep configuration
cat infra/bicep.config.json
```

### Deployment Failures
```bash
# Check deployment status
az deployment group show -g <resource-group> -n <deployment-name>

# View detailed error logs
az deployment group show -g <resource-group> -n <deployment-name> --query properties.error
```

### Future Deployments

**Q: Will these issues happen again?**

**A:** The Bicep template fixes are permanent, but the Azure CLI bug may persist:
- ✅ **Bicep errors**: Fixed permanently (Key Vault, Cosmos DB, Log Analytics)
- ✅ **Collections**: `post-deploy-setup.ps1` runs automatically with `deploy.ps1`
- ⚠️ **CLI bug**: May still occur until Microsoft fixes it (use `deploy.ps1` script)

**Best Practice:** Always use `.\infra\deploy.ps1` which includes automatic workarounds.

### Accessing Secrets After Deployment
```bash
# List secrets in Key Vault
az keyvault secret list --vault-name <key-vault-name>

# Get secret value
az keyvault secret show --vault-name <key-vault-name> --name openai-api-key --query value -o tsv
```

## Next Steps

1. **Deploy Infrastructure:** Follow the Quick Start steps
2. **Configure Secrets:** Update Key Vault with actual credentials
3. **Deploy Applications:** Push Container Apps to the deployed environment
4. **Setup Monitoring:** Configure alerts and dashboards in App Insights
5. **Test Connectivity:** Verify private endpoints and DNS resolution
6. **Security Review:** Validate NSG rules and access controls

## References

- [Azure Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Cosmos DB Best Practices](https://learn.microsoft.com/azure/cosmos-db/best-practices)
- [Key Vault Best Practices](https://learn.microsoft.com/azure/key-vault/general/best-practices)
