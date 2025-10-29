using '../main.bicep'

// Development environment parameters for AI Agents Demo
// These values are optimized for development/testing

param location = 'westus'

param environmentName = 'dev'

param resourcePrefix = 'agents-demo'

param tags = {
  Environment: 'Development'
  Project: 'AIAgents'
  ManagedBy: 'Infrastructure'
  'Cost-Center': 'Engineering'
}

// ============================================================================
// NETWORK
// ============================================================================

param vnetAddressSpace = '10.0.0.0/16'
param containerAppsSubnetAddressSpace = '10.0.1.0/24'
param privateEndpointsSubnetAddressSpace = '10.0.2.0/24'
param integrationSubnetAddressSpace = '10.0.3.0/24'

// ============================================================================
// COSMOS DB - Development (lower throughput)
// ============================================================================

param cosmosDbAccountName = 'cosmosdb-agents-dev-20251020'
param cosmosDbThroughputMode = 'manual'
param cosmosDbManualProvisionedThroughput = 400
param cosmosDbAutoscaleMaxThroughput = 4000
param cosmosDbDatabaseName = 'agents-db'
param cosmosDbEnableBackupRedundancy = false

// ============================================================================
// KEY VAULT
// ============================================================================

param keyVaultName = 'kv-agentsdev-20251020'
param keyVaultEnableSoftDelete = true
param keyVaultPrivateEndpointsEnabled = false

// ============================================================================
// STORAGE ACCOUNT - Development
// ============================================================================

param storageAccountName = 'stgagentsdev'
param storageEnableHierarchicalNamespace = false
param storageMinimumTlsVersion = 'TLS1_2'
param storagePrivateEndpointsEnabled = false

// ============================================================================
// CONTAINER APPS - Development
// ============================================================================

// Note: Container Apps configuration is hardcoded in the container-apps.bicep module
// For custom container images, update the module directly

// ============================================================================
// MONITORING & OBSERVABILITY - Development
// ============================================================================

param logAnalyticsWorkspaceName = 'law-agents-dev'
param appInsightsName = 'appi-agents-dev'
param logRetentionDays = 30
param appInsightsDailyCapGb = 1

// ============================================================================
// EXTERNAL SECRETS (Replace with actual values)
// ============================================================================

@secure()
@description('OpenAI API Key - get from https://platform.openai.com/api-keys')
param openaiApiKey = ''

@secure()
@description('Azure OpenAI endpoint URL')
param azureOpenaiEndpoint = ''

@secure()
@description('Azure OpenAI API key')
param azureOpenaiApiKey = ''

@secure()
@description('MSSQL MCP URL')
param mssqlMcpUrl = 'https://mssqlmcp.azure-api.net/mcp'

@secure()
@description('MSSQL OAuth token URL')
param mssqlOAuthTokenUrl = 'https://login.microsoftonline.com/2e9b0657-eef8-47af-8747-5e89476faaab/oauth2/v2.0/token'

@secure()
@description('MSSQL OAuth client ID')
param mssqlClientId = '17a97781-0078-4478-8b4e-fe5dda9e2400'

@secure()
@description('MSSQL OAuth client secret')
param mssqlClientSecret = 'Kyb8Q~FL6eva5m6pbe.23y9g8ttWZ1UMFSHUZcJn'

@secure()
@description('MSSQL OAuth scope')
param mssqlScope = 'api://17a97781-0078-4478-8b4e-fe5dda9e2400/.default'
