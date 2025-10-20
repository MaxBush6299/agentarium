#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Post-deployment script to create child resources that may not be created by Bicep modules
    
.DESCRIPTION
    This script ensures all child resources are created even if the Bicep module deployment
    encounters the "DeploymentNotFound" Azure CLI bug. Run this after any deployment to ensure
    complete infrastructure setup.
    
.PARAMETER Environment
    The environment to deploy to (dev, staging, prod)
    
.PARAMETER ResourceGroup
    The resource group name (defaults to rg-agentdemo-{Environment})
    
.EXAMPLE
    .\post-deploy-setup.ps1 -Environment dev
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "rg-agentdemo-$Environment"
)

$ErrorActionPreference = "Continue"

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     POST-DEPLOYMENT SETUP - ENVIRONMENT: $($Environment.ToUpper())          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Load parameter file to get resource names
$paramFile = "infra/parameters/$Environment.bicepparam"
if (-not (Test-Path $paramFile)) {
    Write-Error "Parameter file not found: $paramFile"
    exit 1
}

Write-Host "Reading configuration from: $paramFile" -ForegroundColor Yellow

# Parse bicepparam file for resource names (simple parsing)
$paramContent = Get-Content $paramFile -Raw
$cosmosAccountName = if ($paramContent -match "param cosmosDbAccountName = '([^']+)'") { $matches[1] } else { "cosmosdb-agents-$Environment" }
$databaseName = if ($paramContent -match "param cosmosDbDatabaseName = '([^']+)'") { $matches[1] } else { "agents-db" }

Write-Host "`nConfiguration:" -ForegroundColor Cyan
Write-Host "  Resource Group: $ResourceGroup"
Write-Host "  Cosmos Account: $cosmosAccountName"
Write-Host "  Database Name: $databaseName"

# ============================================================================
# VERIFY RESOURCE GROUP EXISTS
# ============================================================================

Write-Host "`n[1/3] Verifying resource group..." -ForegroundColor Cyan
$rgExists = az group exists --name $ResourceGroup
if ($rgExists -eq 'true') {
    Write-Host "  ✓ Resource group exists" -ForegroundColor Green
} else {
    Write-Error "  ✗ Resource group '$ResourceGroup' not found. Run deployment first."
    exit 1
}

# ============================================================================
# CREATE COSMOS DB COLLECTIONS
# ============================================================================

Write-Host "`n[2/3] Ensuring Cosmos DB collections exist..." -ForegroundColor Cyan

# Check if Cosmos account exists
$cosmosExists = az cosmosdb show --name $cosmosAccountName --resource-group $ResourceGroup --query "id" -o tsv 2>$null
if (-not $cosmosExists) {
    Write-Warning "  ⚠ Cosmos DB account '$cosmosAccountName' not found. Skipping collection creation."
} else {
    Write-Host "  ✓ Cosmos DB account found" -ForegroundColor Green
    
    # Check if database exists
    $dbExists = az cosmosdb sql database show --account-name $cosmosAccountName --name $databaseName --resource-group $ResourceGroup --query "id" -o tsv 2>$null
    if (-not $dbExists) {
        Write-Host "  Creating database: $databaseName..." -ForegroundColor Yellow
        az cosmosdb sql database create `
            --account-name $cosmosAccountName `
            --name $databaseName `
            --resource-group $ResourceGroup `
            --output none
        Write-Host "  ✓ Database created" -ForegroundColor Green
    } else {
        Write-Host "  ✓ Database exists" -ForegroundColor Green
    }
    
    # Collections configuration
    $collections = @(
        @{ Name = "threads"; PartitionKey = "/agentId"; Description = "Conversation threads" },
        @{ Name = "runs"; PartitionKey = "/threadId"; Description = "Agent run executions" },
        @{ Name = "steps"; PartitionKey = "/runId"; Description = "Individual execution steps" },
        @{ Name = "toolCalls"; PartitionKey = "/runId"; Description = "Tool invocations and results" },
        @{ Name = "agents"; PartitionKey = "/agentId"; Description = "Agent configurations" },
        @{ Name = "messages"; PartitionKey = "/threadId"; Description = "Conversation messages" }
    )
    
    $createdCount = 0
    $skippedCount = 0
    
    foreach ($collection in $collections) {
        # Check if collection exists
        $containerExists = az cosmosdb sql container show `
            --account-name $cosmosAccountName `
            --database-name $databaseName `
            --name $collection.Name `
            --resource-group $ResourceGroup `
            --query "id" -o tsv 2>$null
        
        if ($containerExists) {
            Write-Host "  ✓ Collection '$($collection.Name)' already exists" -ForegroundColor Gray
            $skippedCount++
        } else {
            Write-Host "  Creating collection: $($collection.Name) - $($collection.Description)..." -ForegroundColor Yellow
            
            az cosmosdb sql container create `
                --account-name $cosmosAccountName `
                --database-name $databaseName `
                --name $collection.Name `
                --partition-key-path $collection.PartitionKey `
                --resource-group $ResourceGroup `
                --ttl 7776000 `
                --output none
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✓ Created successfully" -ForegroundColor Green
                $createdCount++
            } else {
                Write-Warning "    ✗ Failed to create collection"
            }
        }
    }
    
    Write-Host "`n  Summary: $createdCount created, $skippedCount skipped" -ForegroundColor Cyan
}

# ============================================================================
# VERIFY CONTAINER APPS
# ============================================================================

Write-Host "`n[3/3] Verifying Container Apps..." -ForegroundColor Cyan

$containerApps = az containerapp list --resource-group $ResourceGroup --query "[].{Name:name, State:properties.provisioningState}" -o json 2>$null | ConvertFrom-Json

if ($containerApps -and $containerApps.Count -gt 0) {
    Write-Host "  ✓ Found $($containerApps.Count) Container Apps:" -ForegroundColor Green
    foreach ($app in $containerApps) {
        Write-Host "    - $($app.Name): $($app.State)" -ForegroundColor Gray
    }
} else {
    Write-Warning "  ⚠ No Container Apps found. Deployment may be incomplete."
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║            POST-DEPLOYMENT SETUP COMPLETE                  ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run post-deployment validation: .\infra\docs\post-deployment-validation.md"
Write-Host "  2. Enable Cosmos DB public access (dev only):"
Write-Host "     az cosmosdb update --name $cosmosAccountName --resource-group $ResourceGroup --enable-public-network true"
Write-Host "  3. Configure Container Apps managed identity access to Key Vault"
Write-Host "  4. Deploy application container images"
Write-Host ""
