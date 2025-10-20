using '../main.bicep'

// Development environment parameters for AI Agents Demo
// These values are optimized for development/testing

param location = 'eastus'

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

param cosmosDbAccountName = 'cosmosdb-agents-dev'
param cosmosDbThroughputMode = 'manual'
param cosmosDbManualProvisionedThroughput = 400
param cosmosDbAutoscaleMaxThroughput = 4000
param cosmosDbDatabaseName = 'agents-db'
param cosmosDbEnableBackupRedundancy = false

// ============================================================================
// KEY VAULT
// ============================================================================

param keyVaultName = 'kv-agents-dev'
param keyVaultEnableSoftDelete = true
param keyVaultEnablePurgeProtection = false
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
param logRetentionDays = 7
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
