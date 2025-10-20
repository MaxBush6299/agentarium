#!/usr/bin/env pwsh

<#
.SYNOPSIS
Deploy Agent Demo infrastructure to Azure using Bicep templates

.DESCRIPTION
Deploys all Azure resources including Container Apps, Cosmos DB, Key Vault, Storage, and networking.
Supports dev and prod environments with parameter files.

.PARAMETER Environment
Environment to deploy (dev or prod)

.PARAMETER SubscriptionId
Azure subscription ID (defaults to current context if not provided)

.PARAMETER ResourceGroupName
Resource group name (defaults to 'rg-agentdemo-{environment}')

.PARAMETER Location
Azure region (defaults to 'eastus')

.PARAMETER SkipValidation
Skip template validation

.PARAMETER WhatIf
Show what would be deployed without making changes

.EXAMPLE
.\deploy.ps1 -Environment dev
Deploy to dev environment in current subscription

.EXAMPLE
.\deploy.ps1 -Environment prod -SubscriptionId "xxxx-xxxx-xxxx" -Location "westus2"
Deploy to prod environment in specified subscription and region
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId,

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory = $false)]
    [ValidateSet('eastus', 'westus', 'westus2', 'eastus2', 'centralus', 'northeurope', 'westeurope')]
    [string]$Location = 'eastus',

    [Parameter(Mandatory = $false)]
    [switch]$SkipValidation,

    [Parameter(Mandatory = $false)]
    [switch]$WhatIf
)

# Set error action preference
$ErrorActionPreference = 'Stop'

# Colors for output
$colors = @{
    Reset   = "`e[0m"
    Green   = "`e[32m"
    Yellow  = "`e[33m"
    Red     = "`e[31m"
    Blue    = "`e[34m"
    Cyan    = "`e[36m"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'Reset'
    )
    Write-Host "$($colors[$Color])$Message$($colors.Reset)"
}

function Write-Header {
    param([string]$Title)
    Write-ColorOutput "`n$('=' * 80)" 'Cyan'
    Write-ColorOutput "  $Title" 'Cyan'
    Write-ColorOutput "$('=' * 80)`n" 'Cyan'
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "► $Message" 'Blue'
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" 'Green'
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" 'Yellow'
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" 'Red'
}

# ============================================================================
# Validation and Setup
# ============================================================================

Write-Header "Agent Demo Infrastructure Deployment - $Environment Environment"

# Check if Azure CLI is installed
Write-Step "Checking Azure CLI installation..."
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI is not installed. Please install it from https://aka.ms/azurecli"
    exit 1
}
Write-Success "Azure CLI found"

# Get current subscription if not provided
if (-not $SubscriptionId) {
    Write-Step "Getting current Azure subscription..."
    $currentSub = az account show --query id -o tsv
    if (-not $currentSub) {
        Write-Error "Not authenticated with Azure. Run 'az login' first."
        exit 1
    }
    $SubscriptionId = $currentSub
    Write-Success "Using subscription: $SubscriptionId"
} else {
    Write-Step "Setting subscription to: $SubscriptionId"
    az account set --subscription $SubscriptionId
}

# Set default resource group name
if (-not $ResourceGroupName) {
    $ResourceGroupName = "rg-agentdemo-$Environment"
}

Write-ColorOutput "`nDeployment Configuration:" 'Cyan'
Write-ColorOutput "  Environment: $Environment"
Write-ColorOutput "  Subscription: $SubscriptionId"
Write-ColorOutput "  Resource Group: $ResourceGroupName"
Write-ColorOutput "  Location: $Location"
Write-ColorOutput "  WhatIf Mode: $WhatIf`n"

# Confirm deployment
Write-Warning "About to deploy infrastructure to Azure"
$confirm = Read-Host "Continue? (yes/no)"
if ($confirm -ne 'yes') {
    Write-ColorOutput "Deployment cancelled." 'Yellow'
    exit 0
}

# ============================================================================
# Pre-Deployment Checks
# ============================================================================

Write-Header "Pre-Deployment Validation"

# Check if template files exist
Write-Step "Checking template files..."
$templatePath = Join-Path $PSScriptRoot "main.bicep"
$parameterPath = Join-Path $PSScriptRoot "parameters" "$Environment.bicepparam"

if (-not (Test-Path $templatePath)) {
    Write-Error "Template file not found: $templatePath"
    exit 1
}
Write-Success "Main template found: $templatePath"

if (-not (Test-Path $parameterPath)) {
    Write-Error "Parameter file not found: $parameterPath"
    exit 1
}
Write-Success "Parameter file found: $parameterPath"

# Validate Bicep template
if (-not $SkipValidation) {
    Write-Step "Validating Bicep template..."
    try {
        $validation = az bicep build --file $templatePath --outdir $([System.IO.Path]::GetTempPath()) 2>&1
        Write-Success "Template validation successful"
    } catch {
        Write-Error "Template validation failed: $_"
        exit 1
    }
}

# Create resource group if it doesn't exist
Write-Step "Ensuring resource group exists..."
$rgExists = az group exists --name $ResourceGroupName --query value -o tsv

if ($rgExists -eq 'false') {
    Write-ColorOutput "Creating resource group: $ResourceGroupName" 'Yellow'
    az group create --name $ResourceGroupName --location $Location
    Write-Success "Resource group created"
} else {
    Write-Success "Resource group already exists: $ResourceGroupName"
}

# ============================================================================
# Deployment
# ============================================================================

Write-Header "Deploying Infrastructure"

$deploymentName = "deploy-agentdemo-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Step "Starting deployment: $deploymentName"

$deployParams = @(
    '--name', $deploymentName
    '--resource-group', $ResourceGroupName
    '--template-file', $templatePath
    '--parameters', $parameterPath
    '--output', 'json'
)

if ($WhatIf) {
    $deployParams += '--what-if'
    Write-ColorOutput "Running in What-If mode..." 'Yellow'
}

try {
    $deployment = az deployment group create @deployParams | ConvertFrom-Json
    
    if ($deployment.properties.provisioningState -eq 'Succeeded' -or $WhatIf) {
        Write-Success "Deployment completed successfully!"
        
        if (-not $WhatIf) {
            # Extract deployment outputs
            Write-Header "Deployment Outputs"
            
            if ($deployment.properties.outputs) {
                foreach ($output in $deployment.properties.outputs.PSObject.Properties) {
                    Write-ColorOutput "$($output.Name): $($output.Value.value)" 'Green'
                }
            }
        }
    } else {
        Write-Error "Deployment failed with state: $($deployment.properties.provisioningState)"
        exit 1
    }
} catch {
    Write-Error "Deployment error: $_"
    exit 1
}

# ============================================================================
# Post-Deployment Validation
# ============================================================================

if (-not $WhatIf) {
    Write-Header "Post-Deployment Validation"

    # Wait for resources to stabilize
    Write-Step "Waiting for resources to stabilize (30 seconds)..."
    Start-Sleep -Seconds 30

    # Check resource group
    Write-Step "Verifying resources..."
    $resources = az resource list --resource-group $ResourceGroupName --query "length([*])" -o tsv
    Write-Success "Found $resources resources in resource group"

    # Check Container Apps
    Write-Step "Checking Container Apps environment..."
    $caEnv = az containerapp env list --resource-group $ResourceGroupName --query "[0].name" -o tsv
    if ($caEnv) {
        Write-Success "Container Apps environment: $caEnv"
    } else {
        Write-Warning "No Container Apps environment found"
    }

    # Check Cosmos DB
    Write-Step "Checking Cosmos DB account..."
    $cosmosDb = az cosmosdb list --resource-group $ResourceGroupName --query "[0].name" -o tsv
    if ($cosmosDb) {
        Write-Success "Cosmos DB account: $cosmosDb"
        
        # List databases
        $databases = az cosmosdb sql database list --resource-group-name $ResourceGroupName --account-name $cosmosDb --query "[].name" -o tsv
        Write-ColorOutput "  Databases: $($databases -join ', ')"
    } else {
        Write-Warning "No Cosmos DB account found"
    }

    # Check Key Vault
    Write-Step "Checking Key Vault..."
    $keyVault = az keyvault list --resource-group $ResourceGroupName --query "[0].name" -o tsv
    if ($keyVault) {
        Write-Success "Key Vault: $keyVault"
        
        # List secrets
        $secrets = az keyvault secret list --vault-name $keyVault --query "length([*])" -o tsv
        Write-ColorOutput "  Secrets: $secrets"
    } else {
        Write-Warning "No Key Vault found"
    }

    # Check Container App instances
    Write-Step "Checking Container App instances..."
    $apps = az containerapp list --resource-group $ResourceGroupName --query "[].name" -o tsv
    if ($apps) {
        Write-Success "Container Apps:"
        foreach ($app in $apps.Split("`n")) {
            if ($app) {
                $status = az containerapp show --resource-group $ResourceGroupName --name $app --query "properties.provisioningState" -o tsv
                Write-ColorOutput "  - $app (Status: $status)"
            }
        }
    } else {
        Write-Warning "No Container Apps found"
    }

    # Check Log Analytics
    Write-Step "Checking Log Analytics workspace..."
    $logWs = az monitor log-analytics workspace list --resource-group $ResourceGroupName --query "[0].name" -o tsv
    if ($logWs) {
        Write-Success "Log Analytics workspace: $logWs"
    } else {
        Write-Warning "No Log Analytics workspace found"
    }

    # Summary
    Write-Header "Deployment Summary"
    Write-ColorOutput "Environment: $Environment" 'Green'
    Write-ColorOutput "Resource Group: $ResourceGroupName" 'Green'
    Write-ColorOutput "Subscription: $SubscriptionId" 'Green'
    Write-ColorOutput "Location: $Location" 'Green'
    Write-ColorOutput "`nDeployment completed at $(Get-Date)" 'Green'
    
    Write-ColorOutput "`nNext steps:" 'Cyan'
    Write-ColorOutput "1. Configure secrets in Key Vault"
    Write-ColorOutput "2. Deploy container images to Container Registry"
    Write-ColorOutput "3. Test backend API connectivity"
    Write-ColorOutput "4. Run post-deployment validation script"
    Write-ColorOutput "`nFor more information, see README.md in the infra/ directory"
}

Write-Success "`nDeployment script completed successfully!"
