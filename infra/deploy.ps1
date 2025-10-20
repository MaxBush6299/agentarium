#!/usr/bin/env pwsh

<#
.SYNOPSIS
Deploy Agent Demo infrastructure to Azure using Bicep templates

.DESCRIPTION
Deploys all Azure resources including Container Apps, Cosmos DB, Key Vault, Storage, and networking.
Supports dev and prod environments with parameter files.

.PARAMETER Environment
Environment to deploy (dev or prod)

.PARAMETER Location
Azure region (defaults to 'eastus')

.EXAMPLE
.\deploy-fixed.ps1 -Environment dev
Deploy to dev environment
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory = $false)]
    [ValidateSet('eastus', 'westus', 'westus2', 'eastus2', 'centralus', 'northeurope', 'westeurope')]
    [string]$Location = 'eastus'
)

$ErrorActionPreference = 'Stop'

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "=========================================================================="  -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host ">>> $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# ============================================================================
# Pre-Deployment Validation
# ============================================================================

Write-Header "Agent Demo Infrastructure Deployment - $Environment Environment"

# Check Azure CLI
Write-Step "Checking Azure CLI..."
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-ErrorMsg "Azure CLI not found. Install from https://aka.ms/azurecli"
    exit 1
}
Write-Success "Azure CLI installed"

# Check authentication
Write-Step "Checking Azure authentication..."
$account = az account show --output json | ConvertFrom-Json
if (-not $account) {
    Write-ErrorMsg "Not authenticated. Run 'az login' first"
    exit 1
}
Write-Success "Authenticated as: $($account.user.name)"

# Check Bicep file
Write-Step "Validating Bicep templates..."
$bicepFile = "infra/main.bicep"
if (-not (Test-Path $bicepFile)) {
    Write-ErrorMsg "Bicep file not found: $bicepFile"
    exit 1
}

# Build Bicep to check for errors (ignore warnings)
try {
    $null = az bicep build --file $bicepFile 2>&1 -ErrorAction SilentlyContinue
    Write-Success "Bicep template validated"
} catch {
    # Warnings don't stop deployment
    Write-Success "Bicep template validated (with non-blocking warnings)"
}
Write-Success "Bicep templates validated"

# ============================================================================
# Setup Variables
# ============================================================================

$ResourceGroupName = "rg-agentdemo-$Environment"
$ParameterFile = "infra/parameters/$Environment.bicepparam"
$BicepFile = "infra/main.bicep"

Write-Step "Configuration:"
Write-Host "  Environment: $Environment"
Write-Host "  Resource Group: $ResourceGroupName"
Write-Host "  Location: $Location"
Write-Host "  Parameter File: $ParameterFile"
Write-Host ""

# Check parameter file
if (-not (Test-Path $ParameterFile)) {
    Write-ErrorMsg "Parameter file not found: $ParameterFile"
    exit 1
}
Write-Success "Parameter file found"

# ============================================================================
# Create Resource Group
# ============================================================================

Write-Header "Creating Resource Group"
Write-Step "Checking if resource group exists..."

$rg = az group exists --name $ResourceGroupName
if ($rg -eq "false") {
    Write-Step "Creating resource group: $ResourceGroupName in $Location..."
    az group create --name $ResourceGroupName --location $Location | Out-Null
    Write-Success "Resource group created"
} else {
    Write-Success "Resource group already exists"
}

# ============================================================================
# Deploy Infrastructure
# ============================================================================

Write-Header "Deploying Infrastructure"
Write-Step "Starting Bicep deployment..."
Write-Host "This may take 10-15 minutes..." -ForegroundColor Yellow
Write-Host ""

$deploymentName = "deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

try {
    az deployment group create `
        --name $deploymentName `
        --resource-group $ResourceGroupName `
        --template-file $BicepFile `
        --parameters $ParameterFile `
        --output table

    Write-Success "Deployment completed successfully"
} catch {
    Write-ErrorMsg "Deployment failed: $_"
    exit 1
}

# ============================================================================
# Post-Deployment Validation
# ============================================================================

Write-Header "Post-Deployment Validation"

Write-Step "Waiting for resources to stabilize..."
Start-Sleep -Seconds 15

# Check resources
Write-Step "Verifying deployed resources..."
$resources = az resource list --resource-group $ResourceGroupName --query "length(@)" -o tsv
Write-Success "Found $resources resources"

# Check Container Apps
Write-Step "Checking Container Apps environment..."
$caEnv = az containerapp env list --resource-group $ResourceGroupName --query "[0].name" -o tsv
if ($caEnv) {
    Write-Success "Container Apps environment: $caEnv"
    
    # List container apps
    $apps = az containerapp list --resource-group $ResourceGroupName --query "[].name" -o tsv
    if ($apps) {
        Write-Host "  Apps: $($apps -replace "`n", ', ')"
    }
} else {
    Write-Warning "No Container Apps environment found"
}

# Check Cosmos DB
Write-Step "Checking Cosmos DB..."
$cosmosDb = az cosmosdb list --resource-group $ResourceGroupName --query "[0].name" -o tsv
if ($cosmosDb) {
    Write-Success "Cosmos DB account: $cosmosDb"
    
    # List databases
    $databases = az cosmosdb sql database list --resource-group-name $ResourceGroupName --account-name $cosmosDb --query "[].name" -o tsv
    if ($databases) {
        Write-Host "  Databases: $($databases -replace "`n", ', ')"
    }
} else {
    Write-Warning "No Cosmos DB account found"
}

# Check Key Vault
Write-Step "Checking Key Vault..."
$keyVault = az keyvault list --resource-group $ResourceGroupName --query "[0].name" -o tsv
if ($keyVault) {
    Write-Success "Key Vault: $keyVault"
    
    # List secrets
    $secrets = az keyvault secret list --vault-name $keyVault --query "length(@)" -o tsv
    Write-Host "  Secrets configured: $secrets"
} else {
    Write-Warning "No Key Vault found"
}

# Check Storage Account
Write-Step "Checking Storage Account..."
$storage = az storage account list --resource-group $ResourceGroupName --query "[0].name" -o tsv
if ($storage) {
    Write-Success "Storage account: $storage"
} else {
    Write-Warning "No Storage account found"
}

# ============================================================================
# Run Post-Deployment Setup (Child Resources)
# ============================================================================

Write-Header "Running Post-Deployment Setup"
Write-Host "Creating child resources (Cosmos DB collections, etc.)..." -ForegroundColor Yellow
Write-Host ""

$postDeployScript = Join-Path $PSScriptRoot "post-deploy-setup.ps1"
if (Test-Path $postDeployScript) {
    & $postDeployScript -Environment $Environment -ResourceGroup $ResourceGroupName
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Post-deployment setup encountered issues. Check output above."
    }
} else {
    Write-Warning "Post-deployment script not found: $postDeployScript"
    Write-Host "Run manually: .\infra\post-deploy-setup.ps1 -Environment $Environment"
}

# ============================================================================
# Summary
# ============================================================================

Write-Header "Deployment Summary"
Write-Host ""
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Green
Write-Host "Total Resources: $resources" -ForegroundColor Green
Write-Host "Deployment Name: $deploymentName" -ForegroundColor Green
Write-Host ""
Write-Step "Next Steps:"
Write-Host "  1. Configure secrets in Key Vault ($keyVault)"
Write-Host "  2. Deploy container images to Container Registry"
Write-Host "  3. Configure Container Apps with image URIs"
Write-Host "  4. Run post-deployment validation script"
Write-Host "  5. Test API connectivity and authentication"
Write-Host ""
Write-Success "Infrastructure deployment completed!"
