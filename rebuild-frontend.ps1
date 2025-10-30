#!/usr/bin/env pwsh

<#
.SYNOPSIS
Rebuild and deploy frontend with correct VITE_API_URL

.DESCRIPTION
Rebuilds the frontend Docker image with the HTTPS backend URL and pushes to ACR, then updates the container app.

.PARAMETER Environment
Environment to deploy (dev or prod)

.PARAMETER Registry
Container Registry URL (e.g., agentdemoacr.azurecr.io)

.EXAMPLE
.\rebuild-frontend.ps1 -Environment dev -Registry agentdemoacr.azurecr.io
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory = $true)]
    [string]$Registry
)

$ErrorActionPreference = 'Stop'

# ============================================================================
# Configuration
# ============================================================================

$ResourceGroup = "rg-agentdemo-$Environment"
$FrontendAppName = "ca-frontend-$Environment"
$BackendAppName = "ca-backend-$Environment"
$ImageTag = "frontend:latest"
$FullImageName = "$Registry/$ImageTag"

# Get backend FQDN
Write-Host "Retrieving backend FQDN..." -ForegroundColor Blue
$BackendFQDN = az containerapp show --resource-group $ResourceGroup --name $BackendAppName --query "properties.configuration.ingress.fqdn" -o tsv

if (-not $BackendFQDN) {
    Write-Host "[ERROR] Could not retrieve backend FQDN" -ForegroundColor Red
    exit 1
}

$BackendURL = "https://$BackendFQDN/api"
Write-Host "[OK] Backend URL: $BackendURL" -ForegroundColor Green

# ============================================================================
# Build Frontend Image
# ============================================================================

Write-Host "`n>>> Building frontend Docker image..." -ForegroundColor Blue
$frontendDir = Split-Path -Parent $MyInvocation.MyCommand.Path | Join-Path -ChildPath "frontend"

Push-Location $frontendDir
try {
    docker build `
        --build-arg "VITE_API_URL=$BackendURL" `
        -t $FullImageName `
        .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Docker build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Frontend image built successfully" -ForegroundColor Green
}
finally {
    Pop-Location
}

# ============================================================================
# Push to ACR
# ============================================================================

Write-Host "`n>>> Pushing image to Azure Container Registry..." -ForegroundColor Blue
docker push $FullImageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker push failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Image pushed successfully" -ForegroundColor Green

# ============================================================================
# Update Container App
# ============================================================================

Write-Host "`n>>> Updating container app..." -ForegroundColor Blue
az containerapp update `
    --resource-group $ResourceGroup `
    --name $FrontendAppName `
    --image $FullImageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Container app update failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Container app updated successfully" -ForegroundColor Green

# ============================================================================
# Verify Deployment
# ============================================================================

Write-Host "`n>>> Waiting for deployment to complete..." -ForegroundColor Blue
Start-Sleep -Seconds 10

$FrontendFQDN = az containerapp show --resource-group $ResourceGroup --name $FrontendAppName --query "properties.configuration.ingress.fqdn" -o tsv
$FrontendURL = "https://$FrontendFQDN"

Write-Host "`n=========================================================================="
Write-Host "[OK] Frontend Deployment Complete" -ForegroundColor Green
Write-Host "=========================================================================="
Write-Host "Frontend URL: $FrontendURL" -ForegroundColor Cyan
Write-Host "Backend URL: $BackendURL" -ForegroundColor Cyan
Write-Host ""
