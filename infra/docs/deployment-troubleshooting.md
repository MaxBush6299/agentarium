# Infrastructure Deployment Troubleshooting Guide

Common issues and solutions for Phase 1.5 infrastructure deployment.

## Deployment Failures

### Error: "Insufficient quota to create resource"

**Cause:** Azure subscription has hit quota limits for certain resource types.

**Solution:**
```bash
# Check current usage and quotas
az vm list-usage --location eastus

# Request quota increase if needed
# 1. Go to Azure Portal > Help + support > New support request
# 2. Select "Service and subscription limits (quotas)"
# 3. Request increase for needed resources
```

### Error: "Resource already exists"

**Cause:** Resource group or resources from previous deployment still exist.

**Solution:**
```bash
# Check existing resources
az resource list --resource-group rg-agentdemo-dev

# Option 1: Delete entire resource group and redeploy
az group delete --name rg-agentdemo-dev --yes
# Then rerun deploy.ps1

# Option 2: Use different resource group name
.\deploy.ps1 -Environment dev -ResourceGroupName rg-agentdemo-dev-v2
```

### Error: "Template validation failed"

**Cause:** Bicep template has syntax errors or validation issues.

**Solution:**
```bash
# Build template to check for errors
az bicep build --file infra/main.bicep

# Validate more thoroughly
az deployment group validate --resource-group rg-agentdemo-dev \
  --template-file infra/main.bicep \
  --parameters infra/parameters/dev.bicepparam

# Check for:
# - Invalid property names
# - Type mismatches
# - Missing required parameters
# - Syntax errors in conditions/loops
```

### Error: "Deployment failed - Internal Server Error"

**Cause:** Azure backend service issue or resource provider temporary failure.

**Solution:**
```bash
# Wait a few minutes and retry
.\deploy.ps1 -Environment dev

# If persistent, check operation details
az deployment group list --resource-group rg-agentdemo-dev --query "[0].name"
az deployment group show --name <deployment-name> --resource-group rg-agentdemo-dev

# Check operation errors
az deployment operation list --name <deployment-name> \
  --resource-group rg-agentdemo-dev --query "[?properties.provisioningState=='Failed']"
```

## Resource-Specific Issues

### Cosmos DB Fails to Create

**Symptom:** Deployment hangs or fails at Cosmos DB creation

**Cause:** Usually quota or naming issues (Cosmos DB account names must be globally unique)

**Solution:**
```bash
# Check if name is available (globally unique)
az cosmosdb check-name-exists --name cosmos-agentdemo

# If taken, use different name in parameters/dev.bicepparam
# Update: "cosmosDbAccountName": "cosmos-agentdemo-unique-suffix"

# Verify no quota issues
az provider show --namespace Microsoft.DocumentDB \
  --query "resourceTypes[?resourceType=='databaseAccounts'].locations"
```

### Storage Account Fails to Create

**Symptom:** Storage account creation times out or fails

**Cause:** Storage account names must be globally unique and 3-24 characters, lowercase letters and numbers only

**Solution:**
```bash
# Check if name is available
az storage account check-name --name storageagentdemo

# Rename in parameters file if needed
# Update: "storageAccountName": "storageagentdemo<random>"
```

### Container Apps Fail to Deploy

**Symptom:** Container apps stay in "Creating" state or reach "Failed" state

**Cause:** Usually image registry access or missing required settings

**Solution:**
```bash
# Check container app state and events
az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo --query properties.provisioningState

# View recent events
az containerapp logs show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo --tail 50

# Common causes:
# 1. Image not found in registry
# 2. Registry credentials invalid
# 3. Environment variables missing
# 4. Insufficient CPU/memory specified
# 5. Health check endpoint failing

# Fix by updating container app
az containerapp update --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --image <registry>/<image>:<tag>
```

### Private Endpoints Not Resolving

**Symptom:** "Cannot resolve [resource].documents.azure.com" from within VNet

**Cause:** Private DNS zone not linked to VNet, or A records not created

**Solution:**
```bash
# Check private DNS zone exists
az network private-dns zone list --resource-group rg-agentdemo-dev

# Check VNet links
az network private-dns link vnet list \
  --resource-group rg-agentdemo-dev \
  --zone-name privatelink.documents.azure.com

# If missing, create link
az network private-dns link vnet create \
  --resource-group rg-agentdemo-dev \
  --zone-name privatelink.documents.azure.com \
  --name vnet-link \
  --virtual-network vnet-agentdemo \
  --registration-enabled false

# Verify A records
az network private-dns record-set a list \
  --resource-group rg-agentdemo-dev \
  --zone-name privatelink.documents.azure.com
```

### Managed Identity Not Found

**Symptom:** Container apps can't access Key Vault or Cosmos DB

**Cause:** Managed identity not created or not assigned to container app

**Solution:**
```bash
# List identities
az identity list --resource-group rg-agentdemo-dev

# Check identity system-assigned to container app
az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --query identity.principalId

# Verify RBAC assignments
PRINCIPAL_ID=$(az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo --query identity.principalId -o tsv)

az role assignment list --assignee $PRINCIPAL_ID

# If missing, create assignments
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Key Vault Secrets Officer" \
  --scope /subscriptions/<sub>/resourceGroups/rg-agentdemo-dev/providers/Microsoft.KeyVault/vaults/kv-agentdemo
```

## Network-Related Issues

### VNet Peering Not Working

**Symptom:** Resources in different subnets can't communicate

**Cause:** NSG rules or routing not configured

**Solution:**
```bash
# Check NSG rules
az network nsg rule list --resource-group rg-agentdemo-dev --nsg-name nsg-agentdemo

# Verify ingress rules allow traffic between subnets
# Should have rules allowing:
# - Source: 10.0.0.0/24 (containers subnet)
# - Destination: 10.0.1.0/24 (Cosmos subnet)
# - Protocol: All
# - Action: Allow

# Test connectivity (if you have a bastion or VM)
nslookup cosmos-agentdemo.documents.azure.com
# Should resolve to private IP (10.x.x.x)
```

### Public Ingress Not Working

**Symptom:** Can't access Container Apps FQDN from internet

**Cause:** Ingress not properly configured or Network Access Control List (NACL) blocking

**Solution:**
```bash
# Check ingress configuration
az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --query properties.configuration.ingress

# Enable ingress if not present
az containerapp ingress enable --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --type external \
  --target-port 8000

# Get FQDN
az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --query properties.configuration.ingress.fqdn

# Test from external client
FQDN=$(az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo --query properties.configuration.ingress.fqdn -o tsv)
curl https://$FQDN/health
```

## Deployment Cleanup & Recovery

### Partial Deployment - Some Resources Missing

**Symptom:** Only some resources created, others failed silently

**Cause:** Deployment stopped mid-execution, or parallel deployment conflicts

**Solution:**
```bash
# Check what resources exist
az resource list --resource-group rg-agentdemo-dev --output table

# Option 1: Complete the deployment by running again
.\deploy.ps1 -Environment dev
# (Idempotent - will create missing resources)

# Option 2: Start fresh
az group delete --name rg-agentdemo-dev --yes
# Wait for deletion to complete
# Then run deploy.ps1 again
```

### Delete and Redeploy

```bash
# Delete entire resource group
az group delete --name rg-agentdemo-dev --yes --no-wait

# Wait for deletion (typically 5-15 minutes)
# Monitor deletion
az group wait --deleted --name rg-agentdemo-dev

# Redeploy
.\deploy.ps1 -Environment dev -ResourceGroupName rg-agentdemo-dev
```

### Preserve Specific Resources

If you want to keep certain resources and redeploy others:

```bash
# Export existing resources
az resource export --ids /subscriptions/<sub>/resourceGroups/rg-agentdemo-dev

# Modify Bicep template to skip those resources
# Or manually delete specific resources

az resource delete --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --resource-type "Microsoft.App/containerApps"

# Redeploy
.\deploy.ps1 -Environment dev
```

## Debugging Tips

### Enable Verbose Logging

```bash
# Azure CLI debug output
az --debug deployment group create ...

# Or set environment variable
$env:AZURE_CLI_TELEMETRY_ENABLED = $true
```

### Check Deployment State

```bash
# List all deployments
az deployment group list --resource-group rg-agentdemo-dev

# Get specific deployment details
DEPLOY_NAME=$(az deployment group list --resource-group rg-agentdemo-dev \
  --query "[-1].name" -o tsv)

az deployment group show --name $DEPLOY_NAME --resource-group rg-agentdemo-dev

# Get operations that failed
az deployment operation list --name $DEPLOY_NAME \
  --resource-group rg-agentdemo-dev \
  --query "[?properties.provisioningState=='Failed']"
```

### Check Resource Logs

```bash
# Get all logs for a resource group (last hour)
az monitor activity-log list --resource-group rg-agentdemo-dev \
  --start-time $(date -d '-1 hour' -u +%Y-%m-%dT%H:%M:%S) \
  --output table

# Filter for errors
az monitor activity-log list --resource-group rg-agentdemo-dev \
  --start-time $(date -d '-1 hour' -u +%Y-%m-%dT%H:%M:%S) \
  --query "[?level=='Error']" \
  --output table
```

## Performance Issues

### Deployment Extremely Slow

**Solution:**
```bash
# Run deployment in WhatIf mode first to catch errors early
.\deploy.ps1 -Environment dev -WhatIf

# If very slow, check current resource group load
az resource list --resource-group rg-agentdemo-dev \
  --query "length([*])"

# Check for stuck operations
az deployment operation list --name <deployment-name> \
  --resource-group rg-agentdemo-dev \
  --query "[?properties.provisioningState=='Running']"
```

### High Resource Utilization During Deployment

**Solution:**
```bash
# Monitor resource group quotas
az vm list-usage --location eastus

# Consider deploying to less-congested region if errors occur
.\deploy.ps1 -Environment dev -Location westus2
```

## Validation Failures

### Health Check Endpoint Fails

```bash
# Get backend FQDN
BACKEND=$(az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo --query properties.configuration.ingress.fqdn -o tsv)

# Test health endpoint
curl -v https://$BACKEND/health

# If failed, check logs
az containerapp logs show --name ca-backend-agentdemo \
  --resource-group rg-agentdemo-dev --tail 100

# Common issues:
# - Application not started (check container startup logs)
# - Port not exposed (verify ingress configuration)
# - Health endpoint not implemented (code issue)
```

### Database Connectivity Issues

```bash
# Test Cosmos DB connection from container
az containerapp exec --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --command "/bin/sh" \
  --exec-command "curl -v 'https://cosmos-agentdemo.documents.azure.com/'"

# Or check connection string
az cosmosdb keys list --resource-group rg-agentdemo-dev \
  --name cosmos-agentdemo

# Verify private endpoint
az network private-endpoint show --resource-group rg-agentdemo-dev \
  --name pe-cosmos-agentdemo
```

## Getting Help

If issues persist:

1. **Check Azure Service Health**
   - Visit https://status.azure.com/
   - Verify no known issues affecting your region

2. **Review Bicep Template**
   - Check `infra/main.bicep` for syntax
   - Verify all modules are present
   - Check parameter files for correct values

3. **Contact Azure Support**
   - For resource limits: Create quota increase request
   - For service issues: Create support incident
   - Include deployment logs and error details

4. **Review Full Logs**
   ```bash
   # Export deployment logs for detailed analysis
   az deployment group show --name <deployment-name> \
     --resource-group rg-agentdemo-dev \
     > deployment-logs.json
   ```

---

## Quick Reference - Common Commands

```bash
# Check deployment status
az deployment group show --name <name> --resource-group <rg> \
  --query properties.provisioningState

# View deployment errors
az deployment operation list --name <name> --resource-group <rg> \
  --query "[?properties.provisioningState=='Failed'].{Name: properties.targetResource.resourceName, Error: properties.statusMessage}"

# View resource state
az resource show --ids /subscriptions/<sub>/resourceGroups/<rg>/providers/<provider>/<type>/<name>

# Get logs from container app
az containerapp logs show --name <app-name> --resource-group <rg>

# Check role assignments
az role assignment list --resource-group <rg> --output table

# Verify Bicep syntax
az bicep build --file infra/main.bicep

# List all resources
az resource list --resource-group <rg> --output table
```

---

For additional help, see:
- `infra/README.md` - Full infrastructure documentation
- `infra/docs/pre-deployment-checklist.md` - Pre-deployment steps
- `infra/docs/post-deployment-validation.md` - Validation steps
- Azure Bicep documentation: https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/
