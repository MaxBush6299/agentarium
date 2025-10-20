#!/usr/bin/env pwsh
# Script to manually create Cosmos DB collections
# Run this if the Bicep deployment fails but the account exists

param(
    [string]$ResourceGroup = "rg-agentdemo-dev",
    [string]$AccountName = "cosmosdb-agents-dev-20251020",
    [string]$DatabaseName = "agents-db"
)

Write-Host "Creating Cosmos DB collections in $AccountName..." -ForegroundColor Cyan

# Collections configuration
$collections = @(
    @{
        Name = "threads"
        PartitionKey = "/agentId"
    },
    @{
        Name = "runs"
        PartitionKey = "/threadId"
    },
    @{
        Name = "steps"
        PartitionKey = "/runId"
    },
    @{
        Name = "toolCalls"
        PartitionKey = "/runId"
    },
    @{
        Name = "agents"
        PartitionKey = "/agentId"
    },
    @{
        Name = "messages"
        PartitionKey = "/threadId"
    }
)

foreach ($collection in $collections) {
    Write-Host "`nCreating collection: $($collection.Name)..." -ForegroundColor Yellow
    
    try {
        az cosmosdb sql container create `
            --account-name $AccountName `
            --database-name $DatabaseName `
            --name $collection.Name `
            --partition-key-path $collection.PartitionKey `
            --resource-group $ResourceGroup `
            --ttl 7776000 `
            --output none
        
        Write-Host "  ✓ Created $($collection.Name)" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ Failed to create $($collection.Name): $_" -ForegroundColor Red
    }
}

Write-Host "`nVerifying collections..." -ForegroundColor Cyan
az cosmosdb sql container list `
    --account-name $AccountName `
    --database-name $DatabaseName `
    --resource-group $ResourceGroup `
    --query "[].{Name:name, PartitionKey:resource.partitionKey.paths[0]}" `
    --output table

Write-Host "`nDone!" -ForegroundColor Green
