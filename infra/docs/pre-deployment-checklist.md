# Pre-Deployment Checklist

Use this checklist before deploying Phase 1.5 infrastructure to Azure.

## Environment Setup

- [ ] **Azure CLI Installed**
  - [ ] Run `az version` to verify
  - [ ] If not installed, download from https://aka.ms/azurecli

- [ ] **Authenticated with Azure**
  - [ ] Run `az login` if not authenticated
  - [ ] Verify correct subscription: `az account show`
  - [ ] Have required permissions:
    - [ ] Subscription owner or contributor role
    - [ ] Permission to create resource groups
    - [ ] Permission to create all resource types (containers, databases, networking, etc.)

- [ ] **Correct Subscription Selected**
  - [ ] Current subscription ID: `az account show --query id`
  - [ ] Intended for dev or prod environment

## Repository Ready

- [ ] **All Bicep Files Present**
  - [ ] `infra/main.bicep` exists
  - [ ] `infra/modules/` directory contains all 8 modules:
    - [ ] `network.bicep`
    - [ ] `container-apps.bicep`
    - [ ] `cosmos-db.bicep`
    - [ ] `key-vault.bicep`
    - [ ] `storage.bicep`
    - [ ] `private-endpoints.bicep`
    - [ ] `observability.bicep`
    - [ ] `identity.bicep`
  - [ ] `infra/parameters/dev.bicepparam` exists
  - [ ] `infra/parameters/prod.bicepparam` exists

- [ ] **Latest Code Committed**
  - [ ] All backend code committed: `git status`
  - [ ] All frontend code committed
  - [ ] All MCP server code committed
  - [ ] Project plan updated

- [ ] **No Uncommitted Changes**
  - [ ] Run `git status` and verify clean working directory
  - [ ] If changes exist, commit or discard them

## Infrastructure Configuration

- [ ] **Environment Parameters Verified**
  - [ ] Subscription ID correct in parameter files
  - [ ] Environment set correctly (dev or prod)
  - [ ] Location is available and correct:
    - [ ] Development: `eastus` (recommended)
    - [ ] Production: `eastus` or `westus2`
  - [ ] Resource naming conventions followed
  - [ ] No resource name conflicts:
    - [ ] Cosmos DB account name (globally unique)
    - [ ] Storage account name (globally unique)
    - [ ] Key Vault name (globally unique)
    - [ ] Container Registry name (globally unique)

- [ ] **Azure Quotas Verified**
  - [ ] Check subscription quotas: `az vm list-usage --location eastus`
  - [ ] Sufficient quota for:
    - [ ] Virtual Networks (default: 50 per region)
    - [ ] Container Apps (default: 10 per subscription)
    - [ ] Cosmos DB accounts (default: 10 per subscription)
    - [ ] Storage accounts (default: 250 per subscription)
    - [ ] Key Vaults (default: 200 per subscription)
    - [ ] Private Endpoints (no hard limit)

## Security Preparation

- [ ] **RBAC Roles Prepared**
  - [ ] Managed identity will have `Reader` role for resource listing
  - [ ] Managed identity will have database operator role for Cosmos DB
  - [ ] Managed identity will have secret officer role for Key Vault
  - [ ] No hardcoded credentials in templates

- [ ] **Secrets Planning**
  - [ ] List of secrets to populate in Key Vault:
    - [ ] `db-connection-string`
    - [ ] `openai-api-key`
    - [ ] `backend-jwt-secret`
    - [ ] Others as needed
  - [ ] Secrets stored securely (not in repository)
  - [ ] Access plan after deployment

- [ ] **Network Security**
  - [ ] Private endpoints will be created for:
    - [ ] Cosmos DB
    - [ ] Storage Account
    - [ ] Key Vault
  - [ ] NSG rules configured for security
  - [ ] Public internet access restricted

## Resource Planning

- [ ] **Container Apps**
  - [ ] Backend container image prepared/pushed to registry
  - [ ] Frontend container image prepared/pushed to registry
  - [ ] Container image tags recorded
  - [ ] Container registry credentials ready

- [ ] **Cosmos DB**
  - [ ] Database name: `agentdemo`
  - [ ] Containers and partition keys planned:
    - [ ] `chat-threads` (partition key: `/userId`)
    - [ ] `chat-runs` (partition key: `/threadId`)
    - [ ] `chat-steps` (partition key: `/runId`)
    - [ ] `tool-calls` (partition key: `/stepId`)
    - [ ] `agents` (partition key: `/name`)
    - [ ] `metrics` (partition key: `/date`)
  - [ ] TTL policies understood

- [ ] **Storage Account**
  - [ ] Purpose: Audit logs, file uploads
  - [ ] Containers to create:
    - [ ] `logs`
    - [ ] `uploads`
    - [ ] `exports`

- [ ] **Key Vault**
  - [ ] Location: Same region as other resources
  - [ ] Access policies will be configured via RBAC
  - [ ] Soft delete enabled (default)

## Monitoring & Logging

- [ ] **Log Analytics Workspace**
  - [ ] Will be created in same region
  - [ ] Retention policy: 30 days (default, configurable)
  - [ ] All resources will send logs here

- [ ] **Application Insights**
  - [ ] Will be created for monitoring
  - [ ] Connected to Container Apps
  - [ ] Sample rate: 100% (no sampling for now)

## Deployment Readiness

- [ ] **Script Validation**
  - [ ] `deploy.ps1` script exists and is executable
  - [ ] Script has read permissions
  - [ ] Running PowerShell 5.1+ or PowerShell Core

- [ ] **Backup & Recovery**
  - [ ] Current state documented if redeploying
  - [ ] Resource group name backed up in notes
  - [ ] Deployment ID will be recorded for reference

- [ ] **Communication**
  - [ ] Stakeholders notified of deployment time
  - [ ] Downtime window communicated (if applicable)
  - [ ] Rollback plan understood

## Deployment Execution

- [ ] **Ready to Deploy**
  - [ ] All items above completed
  - [ ] No blocking issues remaining
  - [ ] Team consensus to proceed

- [ ] **Deployment Command Prepared**
  - [ ] Command: `.\deploy.ps1 -Environment dev -Location eastus`
  - [ ] Alternative for prod: `.\deploy.ps1 -Environment prod -Location eastus`
  - [ ] What-If test first: `.\deploy.ps1 -Environment dev -WhatIf`

## Post-Deployment (After Checklist Completion)

- [ ] **Immediate Validation** (see post-deployment-validation.md)
  - [ ] Resources created successfully
  - [ ] All 27 resources present
  - [ ] No resources in failed state

- [ ] **Connectivity Testing**
  - [ ] Backend can access Key Vault
  - [ ] Backend can access Cosmos DB
  - [ ] Frontend can reach backend API
  - [ ] MCP server can access Azure resources

- [ ] **Application Testing**
  - [ ] Backend health check endpoint responds
  - [ ] Frontend loads and authenticates
  - [ ] Chat endpoint operational
  - [ ] Agent endpoints responsive

- [ ] **Monitoring Setup**
  - [ ] Logs flowing to Log Analytics
  - [ ] Application Insights tracking requests
  - [ ] Alerts configured (if applicable)

---

## Sign-Off

- **Deployment Date:** _______________
- **Environment:** [ ] Dev  [ ] Prod
- **Executed By:** _______________
- **Reviewed By:** _______________
- **Issues Encountered:** 
  
  ___________________________________________________________________
  
  ___________________________________________________________________

- **Resolution:** 

  ___________________________________________________________________
  
  ___________________________________________________________________

- **Approved to Proceed:** [ ] Yes  [ ] No

---

## Rollback Plan

If deployment fails or issues arise:

1. **Immediate Response**
   - Document error messages and state
   - Do not proceed with additional deployments
   - Contact team lead

2. **Rollback Options**
   - **Option A**: Delete resource group and redeploy
     ```powershell
     az group delete --name rg-agentdemo-dev --yes
     ```
   - **Option B**: Selective resource deletion
     - Identify failed resources
     - Delete and redeploy individually

3. **Investigation**
   - Check deployment logs: `az deployment group show --name <deployment-id>`
   - Review resource-specific errors
   - Check Azure CLI version compatibility
   - Verify Bicep syntax

4. **Recovery Steps**
   - Fix identified issues
   - Rerun deployment
   - Validate again

---

**For help or questions, see `infra/README.md` or contact the team.**
