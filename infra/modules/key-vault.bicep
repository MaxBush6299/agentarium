// Key Vault module: Secure secrets management for AI agents
// Stores API keys, connection strings, and other sensitive data with RBAC

@description('Azure region for deployment')
param location string

@description('Tags to apply to all resources')
param tags object

@description('Key Vault name (must be globally unique)')
param vaultName string

@description('Resource ID of the Managed Identity that will access the vault')
param managedIdentityPrincipalId string

@description('Enable soft delete protection')
param enableSoftDelete bool = true

@description('Private endpoints enabled')
param privateEndpointsEnabled bool = true

// Key Vault Resource
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: vaultName
  location: location
  tags: tags
  properties: {
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: false
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enableRbacAuthorization: true
    enableSoftDelete: enableSoftDelete
    softDeleteRetentionInDays: 90
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: privateEndpointsEnabled ? 'Deny' : 'Allow'
    }
  }
}

// Role Assignment: Managed Identity gets "Key Vault Secrets User" role
resource secretsUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, managedIdentityPrincipalId, '4633458b-17de-408a-b874-0445c86b69e6')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
  scope: keyVault
}

// Role Assignment: Managed Identity gets "Key Vault Crypto Officer" role (for keys if needed)
resource cryptoOfficerRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, managedIdentityPrincipalId, '14b46709-7fe3-46a5-8f3a-8feeeac86025')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '14b46709-7fe3-46a5-8f3a-8feeeac86025')
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
  scope: keyVault
}

// Placeholder secrets (these should be populated via deployment or post-deployment scripts)
// OpenAI API Key
resource openaiApiKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: 'placeholder-replace-with-actual-key'
    attributes: {
      enabled: true
    }
  }
}

// Cosmos DB Connection String
resource cosmosDbConnectionString 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'cosmosdb-connection-string'
  properties: {
    value: 'placeholder-replace-with-actual-connection-string'
    attributes: {
      enabled: true
    }
  }
}

// App Configuration Connection String
resource appConfigConnectionString 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'appconfig-connection-string'
  properties: {
    value: 'placeholder-replace-with-actual-connection-string'
    attributes: {
      enabled: true
    }
  }
}

// Storage Account Connection String
resource storageConnectionString 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'storage-connection-string'
  properties: {
    value: 'placeholder-replace-with-actual-connection-string'
    attributes: {
      enabled: true
    }
  }
}

// API Management Subscription Key
resource apiMSubscriptionKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'apim-subscription-key'
  properties: {
    value: 'placeholder-replace-with-actual-key'
    attributes: {
      enabled: true
    }
  }
}

// Outputs
@description('Key Vault resource ID')
output keyVaultId string = keyVault.id

@description('Key Vault name')
output keyVaultName string = keyVault.name

@description('Key Vault URI for secret references')
output keyVaultUri string = keyVault.properties.vaultUri

@description('OpenAI API Key secret reference')
output openaiApiKeyRef string = '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=${openaiApiKey.name})'

@description('Cosmos DB Connection String secret reference')
output cosmosDbConnectionStringRef string = '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=${cosmosDbConnectionString.name})'

@description('App Config Connection String secret reference')
output appConfigConnectionStringRef string = '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=${appConfigConnectionString.name})'

@description('Storage Connection String secret reference')
output storageConnectionStringRef string = '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=${storageConnectionString.name})'

@description('APIM Subscription Key secret reference')
output apiMSubscriptionKeyRef string = '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=${apiMSubscriptionKey.name})'
