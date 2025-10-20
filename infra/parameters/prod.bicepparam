using '../main.bicep'

// Production environment parameters for AI Agents Demo
// These values are optimized for production workloads with HA and redundancy

param location = 'eastus'

param environmentName = 'prod'

param resourcePrefix = 'agents-demo'

param tags = {
  Environment: 'Production'
  Project: 'AIAgents'
  ManagedBy: 'Infrastructure'
  'Cost-Center': 'Engineering'
  'Backup-Required': 'true'
  'DR-Required': 'true'
}

// ============================================================================
// NETWORK
// ============================================================================

param vnetAddressSpace = '10.0.0.0/16'
param containerAppsSubnetAddressSpace = '10.0.1.0/24'
param privateEndpointsSubnetAddressSpace = '10.0.2.0/24'
param integrationSubnetAddressSpace = '10.0.3.0/24'

// ============================================================================
// COSMOS DB - Production (autoscale, geo-redundant)
// ============================================================================

param cosmosDbAccountName = 'cosmosdb-agents-prod'
param cosmosDbThroughputMode = 'autoscale'
param cosmosDbManualProvisionedThroughput = 400
param cosmosDbAutoscaleMaxThroughput = 4000
param cosmosDbDatabaseName = 'agents-db'
param cosmosDbEnableBackupRedundancy = true

// ============================================================================
// KEY VAULT - Production (maximum security)
// ============================================================================

param keyVaultName = 'kv-agents-prod'
param keyVaultEnableSoftDelete = true
param keyVaultPrivateEndpointsEnabled = true

// ============================================================================
// STORAGE ACCOUNT - Production
// ============================================================================

param storageAccountName = 'stgagentsprod'
param storageEnableHierarchicalNamespace = true
param storageMinimumTlsVersion = 'TLS1_2'
param storagePrivateEndpointsEnabled = true

// ============================================================================
// CONTAINER APPS - Production (HA configuration)
// ============================================================================

// Note: Container Apps configuration is hardcoded in the container-apps.bicep module
// For custom container images, update the module directly

// ============================================================================
// MONITORING & OBSERVABILITY - Production (extended retention)
// ============================================================================

param logAnalyticsWorkspaceName = 'law-agents-prod'
param appInsightsName = 'appi-agents-prod'
param logRetentionDays = 90
param appInsightsDailyCapGb = 50

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
