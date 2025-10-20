// Storage Account module: Blob storage for logs, exports, and artifacts
// Used for agent execution logs and model outputs with private endpoint support

@description('Azure region for deployment')
param location string

@description('Tags to apply to all resources')
param tags object

@description('Storage Account name (must be globally unique, lowercase alphanumeric)')
param accountName string

@description('SKU for the storage account')
param storageSku string = 'Standard_LRS'

@description('Enable hierarchical namespace for Data Lake support')
param enableHierarchicalNamespace bool = false

@description('Private endpoints enabled')
param privateEndpointsEnabled bool = true

@description('Minimum TLS version required')
param minimumTlsVersion string = 'TLS1_2'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: storageSku
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowCrossTenantReplication: false
    defaultToOAuthAuthentication: true
    dnsEndpointType: 'Standard'
    isHnsEnabled: enableHierarchicalNamespace
    minimumTlsVersion: minimumTlsVersion
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: privateEndpointsEnabled ? 'Deny' : 'Allow'
    }
    publicNetworkAccess: 'Enabled'
    supportsHttpsTrafficOnly: true
  }
}

// Blob Services
resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    automaticSnapshotPolicyEnabled: false
    changeFeed: {
      enabled: false
    }
    cors: {
      corsRules: []
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    isVersioningEnabled: false
  }
}

// Logs Container - stores execution logs and diagnostics
resource logsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'logs'
  properties: {
    publicAccess: 'None'
  }
}

// Exports Container - stores agent outputs and exports
resource exportsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'exports'
  properties: {
    publicAccess: 'None'
  }
}

// Models Container - stores LLM models and weights
resource modelsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'models'
  properties: {
    publicAccess: 'None'
  }
}

// Artifacts Container - stores build artifacts and configurations
resource artifactsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'artifacts'
  properties: {
    publicAccess: 'None'
  }
}

// Outputs
@description('Storage Account resource ID')
output storageAccountId string = storageAccount.id

@description('Storage Account name')
output storageAccountName string = storageAccount.name

@description('Primary blob endpoint')
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob

@description('Logs container name')
output logsContainerName string = 'logs'

@description('Exports container name')
output exportsContainerName string = 'exports'

@description('Models container name')
output modelsContainerName string = 'models'

@description('Artifacts container name')
output artifactsContainerName string = 'artifacts'

@description('Storage Account connection string reference for Key Vault')
output connectionStringKeyVaultRef string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=<from-key-vault>;EndpointSuffix=core.windows.net'
