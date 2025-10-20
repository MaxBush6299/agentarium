# Post-Deployment Validation Guide

This guide validates that Phase 1.5 infrastructure deployment was successful and all components are functioning correctly.

## Quick Health Check

Run this immediately after deployment:

```bash
# Set variables
ENVIRONMENT=dev
RESOURCE_GROUP=rg-agentdemo-dev
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Quick validation
echo "Checking resource group..."
az group show --name $RESOURCE_GROUP

echo "Counting resources..."
az resource list --resource-group $RESOURCE_GROUP --query "length([*])"

echo "Checking Container Apps..."
az containerapp list --resource-group $RESOURCE_GROUP

echo "Checking Cosmos DB..."
az cosmosdb list --resource-group $RESOURCE_GROUP

echo "Checking Key Vault..."
az keyvault list --resource-group $RESOURCE_GROUP
```

## Detailed Validation Checklist

### 1. Resource Group & Subscription

- [ ] **Resource Group Created**
  ```bash
  az group show --name rg-agentdemo-dev
  ```
  Expected: Group exists with correct location

- [ ] **Correct Subscription**
  ```bash
  az group show --name rg-agentdemo-dev --query managedBy
  ```
  Expected: Shows subscription path

### 2. Networking Resources

- [ ] **Virtual Network Created**
  ```bash
  VNET_ID=$(az network vnet list --resource-group rg-agentdemo-dev --query "[0].id" -o tsv)
  az network vnet show --ids $VNET_ID
  ```
  Expected: VNet exists with 3 subnets

- [ ] **Subnets Exist**
  ```bash
  az network vnet subnet list --resource-group rg-agentdemo-dev --vnet-name vnet-agentdemo
  ```
  Expected: 3 subnets present:
  - `subnet-containers`
  - `subnet-cosmos`
  - `subnet-storage`

- [ ] **Network Security Groups**
  ```bash
  az network nsg list --resource-group rg-agentdemo-dev
  ```
  Expected: NSGs created and rules configured

- [ ] **Private Endpoints**
  ```bash
  az network private-endpoint list --resource-group rg-agentdemo-dev
  ```
  Expected: 3 private endpoints:
  - Cosmos DB PE
  - Storage Account PE
  - Key Vault PE

- [ ] **Private DNS Zones**
  ```bash
  az network private-dns zone list --resource-group rg-agentdemo-dev
  ```
  Expected: 3 DNS zones for private endpoints

### 3. Container Apps

- [ ] **Container Apps Environment**
  ```bash
  az containerapp env list --resource-group rg-agentdemo-dev
  ```
  Expected: Environment exists and provisioning state is "Succeeded"

- [ ] **Backend Container App**
  ```bash
  az containerapp show --resource-group rg-agentdemo-dev --name ca-backend-agentdemo
  ```
  Expected: State is "Provisioned"

- [ ] **Frontend Container App**
  ```bash
  az containerapp show --resource-group rg-agentdemo-dev --name ca-frontend-agentdemo
  ```
  Expected: State is "Provisioned"

- [ ] **MCP Server Container App** (if deployed)
  ```bash
  az containerapp show --resource-group rg-agentdemo-dev --name ca-mcp-server-agentdemo
  ```
  Expected: State is "Provisioned"

- [ ] **Container App Revisions**
  ```bash
  az containerapp revision list --resource-group rg-agentdemo-dev --name ca-backend-agentdemo
  ```
  Expected: Latest revision in "Active" state

### 4. Database - Cosmos DB

- [ ] **Cosmos DB Account Created**
  ```bash
  az cosmosdb show --resource-group rg-agentdemo-dev --name cosmos-agentdemo
  ```
  Expected: Account in "Succeeded" state

- [ ] **Primary Region**
  ```bash
  az cosmosdb show --resource-group rg-agentdemo-dev --name cosmos-agentdemo \
    --query "locations[0].{region: locationName, status: failoverPriority}"
  ```
  Expected: Primary region is "East US"

- [ ] **Database Created**
  ```bash
  az cosmosdb sql database show --resource-group rg-agentdemo-dev \
    --account-name cosmos-agentdemo --name agentdemo
  ```
  Expected: Database exists with "Provisioned" status

- [ ] **Collections Exist**
  ```bash
  az cosmosdb sql container list --resource-group rg-agentdemo-dev \
    --account-name cosmos-agentdemo --database-name agentdemo
  ```
  Expected: 6 containers with correct partition keys:
  - `chat-threads` (partition: `/userId`)
  - `chat-runs` (partition: `/threadId`)
  - `chat-steps` (partition: `/runId`)
  - `tool-calls` (partition: `/stepId`)
  - `agents` (partition: `/name`)
  - `metrics` (partition: `/date`)

- [ ] **TTL Configured**
  ```bash
  az cosmosdb sql container show --resource-group rg-agentdemo-dev \
    --account-name cosmos-agentdemo --database-name agentdemo \
    --name chat-threads --query defaultTtl
  ```
  Expected: TTL values set (typically 86400 for 24 hours or -1 for no expiry)

- [ ] **Throughput Settings**
  ```bash
  az cosmosdb sql container show --resource-group rg-agentdemo-dev \
    --account-name cosmos-agentdemo --database-name agentdemo \
    --name chat-threads --query throughputSettings
  ```
  Expected: Autoscale or provisioned throughput configured

### 5. Key Vault

- [ ] **Key Vault Created**
  ```bash
  az keyvault show --resource-group rg-agentdemo-dev --name kv-agentdemo
  ```
  Expected: Vault exists and is in "Enabled" state

- [ ] **RBAC Enabled**
  ```bash
  az keyvault show --resource-group rg-agentdemo-dev --name kv-agentdemo \
    --query properties.enableRbacAuthorization
  ```
  Expected: true

- [ ] **Purge Protection Enabled**
  ```bash
  az keyvault show --resource-group rg-agentdemo-dev --name kv-agentdemo \
    --query properties.enablePurgeProtection
  ```
  Expected: true (for production) or false (for dev)

- [ ] **Soft Delete Enabled**
  ```bash
  az keyvault show --resource-group rg-agentdemo-dev --name kv-agentdemo \
    --query properties.enableSoftDelete
  ```
  Expected: true

- [ ] **Access Policy/RBAC**
  ```bash
  az role assignment list --resource-group rg-agentdemo-dev \
    --query "[?scope=~'kv-agentdemo']"
  ```
  Expected: Managed identity has "Key Vault Secrets Officer" or "Key Vault Administrator" role

### 6. Storage Account

- [ ] **Storage Account Created**
  ```bash
  az storage account show --resource-group rg-agentdemo-dev --name storageagentdemo
  ```
  Expected: Storage account exists in "Succeeded" provisioning state

- [ ] **Access Tier**
  ```bash
  az storage account show --resource-group rg-agentdemo-dev --name storageagentdemo \
    --query accessTier
  ```
  Expected: "Hot" for dev, "Cool" for prod

- [ ] **Containers Exist**
  ```bash
  az storage container list --account-name storageagentdemo --auth-mode login
  ```
  Expected: At least these containers:
  - `logs`
  - `exports`

- [ ] **HTTPS Only**
  ```bash
  az storage account show --resource-group rg-agentdemo-dev --name storageagentdemo \
    --query supportsHttpsTrafficOnly
  ```
  Expected: true

### 7. Managed Identity & RBAC

- [ ] **Managed Identity Created**
  ```bash
  az identity list --resource-group rg-agentdemo-dev
  ```
  Expected: System-assigned identity for Container Apps

- [ ] **Identity Has Proper Roles**
  ```bash
  IDENTITY_ID=$(az identity list --resource-group rg-agentdemo-dev --query "[0].id" -o tsv)
  az role assignment list --assignee $IDENTITY_ID
  ```
  Expected: Roles assigned:
  - `Reader` (for resource listing)
  - `Cosmos DB Built-in Data Contributor` (for Cosmos DB access)
  - `Key Vault Secrets Officer` (for Key Vault access)

### 8. Observability

- [ ] **Log Analytics Workspace**
  ```bash
  az monitor log-analytics workspace list --resource-group rg-agentdemo-dev
  ```
  Expected: Workspace created and operational

- [ ] **Application Insights**
  ```bash
  az monitor app-insights component list --resource-group rg-agentdemo-dev
  ```
  Expected: App Insights instance exists

- [ ] **Workspace Linked**
  ```bash
  az monitor log-analytics workspace show --resource-group rg-agentdemo-dev \
    --name laws-agentdemo --query properties.retentionInDays
  ```
  Expected: Retention period configured (typically 30 days)

### 9. Connectivity Tests

- [ ] **Private Endpoint DNS Resolution**
  ```bash
  # From a VM in the VNet (or via Azure Bastion)
  nslookup cosmos-agentdemo.documents.azure.com
  # Should resolve to private IP (10.x.x.x), not public IP
  ```

- [ ] **Cosmos DB Connectivity**
  ```bash
  # From Container App or local with correct credentials
  az cosmosdb keys list --resource-group rg-agentdemo-dev --name cosmos-agentdemo
  ```
  Expected: Primary and secondary keys available

- [ ] **Key Vault Access**
  ```bash
  # If managed identity is properly assigned
  az keyvault secret list --vault-name kv-agentdemo
  ```
  Expected: Can list (not retrieve) secrets

### 10. Security Validation

- [ ] **Public Endpoint Disabled** (if applicable)
  ```bash
  az cosmosdb show --resource-group rg-agentdemo-dev --name cosmos-agentdemo \
    --query publicNetworkAccess
  ```
  Expected: "Disabled" for production, can be "Enabled" for dev

- [ ] **Firewall Rules**
  ```bash
  az cosmosdb show --resource-group rg-agentdemo-dev --name cosmos-agentdemo \
    --query ipRules
  ```
  Expected: IP rules configured if needed

- [ ] **NSG Rules Reviewed**
  ```bash
  az network nsg rule list --resource-group rg-agentdemo-dev \
    --nsg-name nsg-agentdemo
  ```
  Expected: Restrictive rules preventing unauthorized access

## Functional Validation

### Backend API Tests

```bash
# Get backend container app URL
BACKEND_URL=$(az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo --query properties.configuration.ingress.fqdn -o tsv)

# Test health endpoint
curl https://$BACKEND_URL/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-10-20T...", "config": {...}}
```

### Frontend Tests

```bash
# Get frontend container app URL
FRONTEND_URL=$(az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-frontend-agentdemo --query properties.configuration.ingress.fqdn -o tsv)

# Test frontend accessibility
curl https://$FRONTEND_URL

# Expected: HTML content returned
```

### MCP Server Tests (if deployed)

```bash
# Test MCP server health
curl http://ca-mcp-server-agentdemo:3000/health

# Test tool listing
curl http://ca-mcp-server-agentdemo:3000/tools
```

## Monitoring Setup Validation

- [ ] **Logs Flowing**
  ```bash
  # Check for recent logs in Log Analytics
  az monitor log-analytics workspace query --resource-group rg-agentdemo-dev \
    --workspace-name laws-agentdemo \
    --analytics-query "ContainerAppSystemLogs | take 10"
  ```

- [ ] **Application Insights Tracking**
  ```bash
  # Verify requests are being tracked
  az monitor app-insights component show --resource-group rg-agentdemo-dev \
    --app insights-agentdemo --query id
  ```

## Resource Count Summary

Total expected resources: **27** (may vary based on configuration)

Breakdown by type:
- Networking: 7+ (VNet, subnets, NSGs, private endpoints, DNS zones)
- Compute: 3 (Container Apps environment + apps)
- Database: 1+ (Cosmos DB with collections)
- Storage: 1 (Storage account)
- Security: 1+ (Key Vault, managed identity)
- Monitoring: 2+ (Log Analytics, App Insights)
- Other: Supporting resources

```bash
# Verify total count
az resource list --resource-group rg-agentdemo-dev --query "length([*])"
```

## Common Issues & Solutions

### Issue: Container App not reaching healthy state

**Solution:**
- Check container image: `az containerapp show --name ca-backend-agentdemo | jq '.properties.template.containers'`
- View logs: `az containerapp logs show --name ca-backend-agentdemo`
- Verify image registry access and credentials
- Check environment variables passed to container

### Issue: Cosmos DB connection fails

**Solution:**
- Verify managed identity has correct role: `az role assignment list --assignee <identity-id>`
- Check private endpoint connectivity
- Verify firewall rules (if enabled)
- Confirm connection string has private endpoint DNS

### Issue: Key Vault access denied

**Solution:**
- Verify managed identity exists: `az identity show --ids <identity-id>`
- Check RBAC assignment: `az role assignment list --assignee <identity-id> --scope <keyvault-id>`
- Verify RBAC is enabled: `az keyvault show --query properties.enableRbacAuthorization`

### Issue: Private endpoints not resolving

**Solution:**
- Check private DNS zone records: `az network private-dns record-set a list --zone-name privatelink.documents.azure.com`
- Verify VNet link: `az network private-dns link vnet list --zone-name privatelink.documents.azure.com`
- Test DNS from within VNet (may require bastion or VM)

## Sign-Off

- **Validation Date:** _______________
- **Environment:** [ ] Dev  [ ] Prod
- **Validated By:** _______________
- **All Checks Passed:** [ ] Yes  [ ] No

**Issues Found:**
_____________________________________________________________________________
_____________________________________________________________________________

**Resolution:**
_____________________________________________________________________________
_____________________________________________________________________________

---

## Next Steps

After validation passes:

1. **Configure Secrets in Key Vault**
   - Add database connection strings
   - Add API keys
   - Add JWT secrets

2. **Deploy Application Containers**
   - Build and push backend Docker image
   - Build and push frontend Docker image
   - Update Container App revisions

3. **Run End-to-End Tests**
   - Test authentication flow
   - Test API calls
   - Test database connectivity

4. **Enable Monitoring & Alerts**
   - Configure alert rules
   - Set up dashboards
   - Enable diagnostic logging

5. **Proceed to Phase 2: Agent Implementation**

For detailed troubleshooting, see the infra/ README.md or contact the deployment team.
