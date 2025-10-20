# Phase 1.5 Deployment Runbook

Quick start guide for deploying Agent Demo infrastructure to Azure.

## Prerequisites

```bash
# 1. Install Azure CLI (if not already installed)
# Visit: https://aka.ms/azurecli
# Or on Windows:
choco install azure-cli

# 2. Verify installation
az version

# 3. Authenticate with Azure
az login

# 4. Verify correct subscription
az account show
# Note the subscription ID and tenant ID
```

## Quick Deployment (5-10 minutes)

### Step 1: Navigate to Infrastructure Directory

```bash
cd infra
```

### Step 2: Review Parameters

```bash
# For development
cat parameters/dev.bicepparam

# Update if needed:
# - subscriptionId
# - location (default: eastus)
# - environment (dev or prod)
```

### Step 3: Optional - Run WhatIf First

```bash
# See what would be deployed without making changes
.\deploy.ps1 -Environment dev -WhatIf
```

### Step 4: Deploy Infrastructure

```bash
# Deploy to dev environment (default: eastus)
.\deploy.ps1 -Environment dev

# Deploy to prod (alternative)
.\deploy.ps1 -Environment prod

# Deploy to alternative region
.\deploy.ps1 -Environment dev -Location westus2

# Deploy to specific subscription
.\deploy.ps1 -Environment dev -SubscriptionId "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

The script will:
1. ✓ Validate Azure CLI and authentication
2. ✓ Check template files exist
3. ✓ Validate Bicep template
4. ✓ Create resource group if needed
5. ✓ Deploy all resources via Bicep
6. ✓ Validate deployment success
7. ✓ List created resources

### Step 5: Wait for Deployment

Deployment typically takes **5-10 minutes**. The script shows real-time progress.

## Validate Deployment

```bash
# Run validation immediately after deployment completes
source ./docs/post-deployment-validation.md

# Quick health checks
az group show --name rg-agentdemo-dev --query location
az resource list --resource-group rg-agentdemo-dev --query "length([*])"
az containerapp list --resource-group rg-agentdemo-dev
```

## Common Variations

### Deploy to Production

```bash
.\deploy.ps1 -Environment prod -Location eastus
```

### Deploy to Different Region

```bash
# Available regions: eastus, westus, westus2, eastus2, centralus, northeurope, westeurope
.\deploy.ps1 -Environment dev -Location westus2
```

### Deploy with Custom Resource Group Name

```bash
.\deploy.ps1 -Environment dev -ResourceGroupName "rg-my-custom-name"
```

### Deploy to Specific Subscription

```bash
.\deploy.ps1 -Environment dev -SubscriptionId "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### Skip Template Validation (Not Recommended)

```bash
.\deploy.ps1 -Environment dev -SkipValidation
```

## If Deployment Fails

```bash
# Check deployment logs
az deployment group show --name <deployment-id> \
  --resource-group rg-agentdemo-dev

# View detailed errors
az deployment operation list --name <deployment-id> \
  --resource-group rg-agentdemo-dev \
  --query "[?properties.provisioningState=='Failed']"

# See troubleshooting guide
cat docs/deployment-troubleshooting.md
```

## After Successful Deployment

### 1. Configure Secrets

```bash
# Add secrets to Key Vault
az keyvault secret set --vault-name kv-agentdemo \
  --name "db-connection-string" \
  --value "your-cosmos-connection-string"

az keyvault secret set --vault-name kv-agentdemo \
  --name "openai-api-key" \
  --value "your-openai-key"
```

### 2. Deploy Application Containers

```bash
# Build and push backend image
cd ../backend
docker build -t agentdemo-backend:latest .
docker tag agentdemo-backend:latest <registry>/agentdemo-backend:latest
docker push <registry>/agentdemo-backend:latest

# Build and push frontend image
cd ../frontend
docker build -t agentdemo-frontend:latest .
docker tag agentdemo-frontend:latest <registry>/agentdemo-frontend:latest
docker push <registry>/agentdemo-frontend:latest

# Update Container Apps
az containerapp update --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --image <registry>/agentdemo-backend:latest

az containerapp update --resource-group rg-agentdemo-dev \
  --name ca-frontend-agentdemo \
  --image <registry>/agentdemo-frontend:latest
```

### 3. Test Connectivity

```bash
# Get backend URL
BACKEND=$(az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --query properties.configuration.ingress.fqdn -o tsv)

# Test health endpoint
curl https://$BACKEND/health

# Get frontend URL
FRONTEND=$(az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-frontend-agentdemo \
  --query properties.configuration.ingress.fqdn -o tsv)

# Test frontend (should return HTML)
curl https://$FRONTEND | head -20
```

### 4. Proceed to Phase 2

Infrastructure deployment complete! Proceed with:
- Agent implementation
- API endpoint development
- Integration testing

## Monitoring After Deployment

### View Container Logs

```bash
# Backend logs
az containerapp logs show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo --tail 50

# Frontend logs
az containerapp logs show --resource-group rg-agentdemo-dev \
  --name ca-frontend-agentdemo --tail 50
```

### Check Resource Status

```bash
# All resources in resource group
az resource list --resource-group rg-agentdemo-dev \
  --output table

# Container Apps status
az containerapp show --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo \
  --query "{Name: name, State: properties.provisioningState, Replicas: properties.template.scale.minReplicas}"
```

### View Metrics

```bash
# Get metrics for Container App
az monitor metrics list --resource /subscriptions/<sub>/resourceGroups/rg-agentdemo-dev/providers/Microsoft.App/containerApps/ca-backend-agentdemo \
  --metric "RestartCount"
```

## Cleanup (If Needed)

```bash
# Delete entire resource group (deletes all resources)
az group delete --name rg-agentdemo-dev --yes

# Or delete specific resources
az containerapp delete --resource-group rg-agentdemo-dev \
  --name ca-backend-agentdemo --yes
```

## Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| "Insufficient quota" | See `deployment-troubleshooting.md` - Quota Section |
| "Resource already exists" | Delete RG or use different name |
| "Template validation failed" | Run `az bicep build --file main.bicep` |
| "Authentication failed" | Run `az login` |
| "Container app won't start" | Check logs: `az containerapp logs show ...` |
| "Database connection fails" | Verify private endpoint DNS resolution |
| "Key Vault access denied" | Verify managed identity RBAC assignment |

See full troubleshooting guide: `docs/deployment-troubleshooting.md`

## Deployment Times (Typical)

| Component | Time |
|-----------|------|
| Validation & setup | 30 seconds |
| Network resources | 1-2 minutes |
| Cosmos DB | 2-3 minutes |
| Container Apps | 1-2 minutes |
| Storage & monitoring | 1-2 minutes |
| **Total** | **5-10 minutes** |

## Getting Help

- **Pre-deployment questions:** See `docs/pre-deployment-checklist.md`
- **Validation questions:** See `docs/post-deployment-validation.md`
- **Troubleshooting:** See `docs/deployment-troubleshooting.md`
- **Full documentation:** See `README.md`

---

## Deployment Decision Tree

```
Start here
  │
  ├─ First time deploying?
  │  └─ Yes → Follow "Quick Deployment" section above
  │
  ├─ Deploying to production?
  │  └─ Yes → Use: .\deploy.ps1 -Environment prod
  │
  ├─ Need to deploy to different region?
  │  └─ Yes → Use: .\deploy.ps1 -Environment dev -Location westus2
  │
  ├─ Want to test before deploying?
  │  └─ Yes → Use: .\deploy.ps1 -Environment dev -WhatIf
  │
  ├─ Previous deployment failed?
  │  └─ Yes → See "If Deployment Fails" section above
  │
  └─ Ready to proceed?
     └─ Yes → .\deploy.ps1 -Environment dev
```

---

Last updated: October 20, 2025
