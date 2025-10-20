// Main orchestration template for AI Agents Demo
// This template coordinates all modules and manages dependencies

metadata name = 'AI Agents Demo - Infrastructure'
metadata description = 'Complete infrastructure deployment for AI agents platform'
metadata version = '1.0.0'

@description('Azure region for all resources')
param location string

@description('Environment name (dev/staging/prod)')
param environmentName string

@description('Resource naming prefix')
param resourcePrefix string

@description('Tags to apply to all resources')
param tags object

// ============================================================================
// NETWORK PARAMETERS
// ============================================================================

@description('VNet address space')
param vnetAddressSpace string

@description('Container Apps subnet address space')
param containerAppsSubnetAddressSpace string

@description('Private endpoints subnet address space')
param privateEndpointsSubnetAddressSpace string

@description('Integration subnet address space')
param integrationSubnetAddressSpace string

// ============================================================================
// COSMOS DB PARAMETERS
// ============================================================================

@description('Cosmos DB account name')
param cosmosDbAccountName string

@description('Cosmos DB throughput mode')
param cosmosDbThroughputMode string = 'autoscale'

@description('Cosmos DB manual throughput')
param cosmosDbManualProvisionedThroughput int = 400

@description('Cosmos DB autoscale max throughput')
param cosmosDbAutoscaleMaxThroughput int = 4000

@description('Cosmos DB database name')
param cosmosDbDatabaseName string

@description('Enable Cosmos DB geo-redundant backup')
param cosmosDbEnableBackupRedundancy bool = false

// ============================================================================
// KEY VAULT PARAMETERS
// ============================================================================

@description('Key Vault name')
param keyVaultName string

@description('Enable Key Vault soft delete')
param keyVaultEnableSoftDelete bool = true

@description('Enable Key Vault purge protection')
param keyVaultEnablePurgeProtection bool = true

@description('Enable Key Vault private endpoints')
param keyVaultPrivateEndpointsEnabled bool = true

// ============================================================================
// STORAGE PARAMETERS
// ============================================================================

@description('Storage account name')
param storageAccountName string

@description('Enable storage hierarchical namespace')
param storageEnableHierarchicalNamespace bool = false

@description('Storage minimum TLS version')
param storageMinimumTlsVersion string = 'TLS1_2'

@description('Enable storage private endpoints')
param storagePrivateEndpointsEnabled bool = true

// ============================================================================
// OBSERVABILITY PARAMETERS
// ============================================================================

@description('Log Analytics workspace name')
param logAnalyticsWorkspaceName string

@description('Application Insights name')
param appInsightsName string

@description('Log retention in days')
param logRetentionDays int = 30

@description('App Insights daily cap in GB')
param appInsightsDailyCapGb int = 10

// ============================================================================
// SECRETS PARAMETERS
// ============================================================================

@secure()
@description('OpenAI API Key')
param openaiApiKey string = ''

@secure()
@description('Azure OpenAI endpoint')
param azureOpenaiEndpoint string = ''

@secure()
@description('Azure OpenAI API key')
param azureOpenaiApiKey string = ''

// ============================================================================
// DEPLOY NETWORK MODULE
// ============================================================================

module networkModule './modules/network.bicep' = {
  name: 'network-${uniqueString(resourceGroup().id)}'
  params: {
    location: location
    tags: tags
    vnetAddressSpace: vnetAddressSpace
    containerAppsSubnetAddressSpace: containerAppsSubnetAddressSpace
    privateEndpointsSubnetAddressSpace: privateEndpointsSubnetAddressSpace
    integrationSubnetAddressSpace: integrationSubnetAddressSpace
  }
}

// ============================================================================
// DEPLOY OBSERVABILITY MODULE (Log Analytics + App Insights)
// ============================================================================

module observabilityModule './modules/observability.bicep' = {
  name: 'observability-${uniqueString(resourceGroup().id)}'
  params: {
    location: location
    tags: tags
    logAnalyticsWorkspaceName: logAnalyticsWorkspaceName
    appInsightsName: appInsightsName
    logRetentionDays: logRetentionDays
    appInsightsDailyCapGb: appInsightsDailyCapGb
  }
}

// ============================================================================
// DEPLOY COSMOS DB MODULE
// ============================================================================

module cosmosDbModule './modules/cosmos-db.bicep' = {
  name: 'cosmos-${uniqueString(resourceGroup().id)}'
  params: {
    location: location
    tags: tags
    accountName: cosmosDbAccountName
    throughputMode: cosmosDbThroughputMode
    manualProvisionedThroughput: cosmosDbManualProvisionedThroughput
    autoscaleMaxThroughput: cosmosDbAutoscaleMaxThroughput
    databaseName: cosmosDbDatabaseName
    enableBackupRedundancy: cosmosDbEnableBackupRedundancy
  }
}

// ============================================================================
// DEPLOY STORAGE MODULE
// ============================================================================

module storageModule './modules/storage.bicep' = {
  name: 'storage-${uniqueString(resourceGroup().id)}'
  params: {
    location: location
    tags: tags
    accountName: storageAccountName
    enableHierarchicalNamespace: storageEnableHierarchicalNamespace
    minimumTlsVersion: storageMinimumTlsVersion
    privateEndpointsEnabled: storagePrivateEndpointsEnabled
  }
}

// ============================================================================
// DEPLOY KEY VAULT MODULE
// ============================================================================

// Note: In production, this should be obtained from a managed identity
// For now, using a placeholder
var keyVaultAccessPrincipalId = subscription().tenantId

module keyVaultModule './modules/key-vault.bicep' = {
  name: 'keyvault-${uniqueString(resourceGroup().id)}'
  params: {
    location: location
    tags: tags
    vaultName: keyVaultName
    managedIdentityPrincipalId: keyVaultAccessPrincipalId
    enableSoftDelete: keyVaultEnableSoftDelete
    enablePurgeProtection: keyVaultEnablePurgeProtection
    privateEndpointsEnabled: keyVaultPrivateEndpointsEnabled
  }
}

// ============================================================================
// DEPLOY PRIVATE ENDPOINTS MODULE
// ============================================================================

module privateEndpointsModule './modules/private-endpoints.bicep' = {
  name: 'endpoints-${uniqueString(resourceGroup().id)}'
  params: {
    location: location
    tags: tags
    privateEndpointsSubnetResourceId: networkModule.outputs.privateEndpointsSubnetResourceId
    vnetResourceId: networkModule.outputs.vnetResourceId
    cosmosDbAccountId: cosmosDbModule.outputs.cosmosDbAccountId
    cosmosDbAccountName: cosmosDbModule.outputs.cosmosDbAccountName
    keyVaultId: keyVaultModule.outputs.keyVaultId
    keyVaultName: keyVaultModule.outputs.keyVaultName
    storageAccountId: storageModule.outputs.storageAccountId
    storageAccountName: storageModule.outputs.storageAccountName
  }
}

// ============================================================================
// DEPLOY CONTAINER APPS MODULE
// ============================================================================

module containerAppsModule './modules/container-apps.bicep' = {
  name: 'containers-${uniqueString(resourceGroup().id)}'
  params: {
    location: location
    tags: tags
    containerAppsSubnetResourceId: networkModule.outputs.containerAppsSubnetResourceId
    logAnalyticsWorkspaceId: observabilityModule.outputs.logAnalyticsWorkspaceId
    appInsightsInstrumentationKey: observabilityModule.outputs.appInsightsInstrumentationKey
    environmentName: environmentName
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('Resource Group ID')
output resourceGroupId string = resourceGroup().id

@description('Resource Group name')
output resourceGroupName string = resourceGroup().name

@description('VNet resource ID')
output vnetResourceId string = networkModule.outputs.vnetResourceId

@description('Cosmos DB endpoint')
output cosmosDbEndpoint string = cosmosDbModule.outputs.cosmosDbEndpoint

@description('Key Vault URI')
output keyVaultUri string = keyVaultModule.outputs.keyVaultUri

@description('Storage Account ID')
output storageAccountId string = storageModule.outputs.storageAccountId

@description('Log Analytics Workspace ID')
output logAnalyticsWorkspaceId string = observabilityModule.outputs.logAnalyticsWorkspaceId

@description('Application Insights ID')
output appInsightsId string = observabilityModule.outputs.appInsightsId

@description('Frontend Container App FQDN')
output frontendFqdn string = containerAppsModule.outputs.frontendFqdn

@description('Backend Container App FQDN')
output backendFqdn string = containerAppsModule.outputs.backendFqdn

