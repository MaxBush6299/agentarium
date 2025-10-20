// Private Endpoints module: Secure private connectivity to data services
// Deploys 6 private endpoints for Cosmos DB, Key Vault, Storage, App Config, OpenAI proxy, and APIM

@description('Azure region for deployment')
param location string

@description('Tags to apply to all resources')
param tags object

@description('Resource ID of the private endpoints subnet')
param privateEndpointsSubnetResourceId string

@description('Resource ID of the Virtual Network (for DNS zone integration)')
param vnetResourceId string

@description('Cosmos DB account resource ID')
param cosmosDbAccountId string

@description('Cosmos DB account name')
param cosmosDbAccountName string

@description('Key Vault resource ID')
param keyVaultId string

@description('Key Vault name')
param keyVaultName string

@description('Storage Account resource ID')
param storageAccountId string

@description('Storage Account name')
param storageAccountName string

@description('App Configuration store resource ID (optional)')
param appConfigId string = ''

// Variables for naming
var privateEndpointNamePrefix = 'pep'
var privateDnsZonePrefix = 'privatelink'

// Private Endpoint for Cosmos DB
resource cosmosDbPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: '${privateEndpointNamePrefix}-cosmos'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetResourceId
    }
    privateLinkServiceConnections: [
      {
        name: 'cosmos-connection'
        properties: {
          privateLinkServiceId: cosmosDbAccountId
          groupIds: [
            'Sql'
          ]
        }
      }
    ]
  }
}

// Private DNS Zone for Cosmos DB
resource cosmosDbPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${privateDnsZonePrefix}.documents.azure.com'
  location: 'global'
  tags: tags
}

// VNet Link for Cosmos DB DNS Zone
resource cosmosDbDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: cosmosDbPrivateDnsZone
  name: 'vnetlink'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetResourceId
    }
  }
}

// DNS A Record for Cosmos DB
resource cosmosDbDnsARecord 'Microsoft.Network/privateDnsZones/A@2020-06-01' = {
  parent: cosmosDbPrivateDnsZone
  name: cosmosDbAccountName
  properties: {
    aRecords: [
      {
        ipv4Address: cosmosDbPrivateEndpoint.properties.customDnsConfigs[0].ipAddresses[0]
      }
    ]
    ttl: 3600
  }
}

// Private Endpoint for Key Vault
resource keyVaultPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: '${privateEndpointNamePrefix}-keyvault'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetResourceId
    }
    privateLinkServiceConnections: [
      {
        name: 'keyvault-connection'
        properties: {
          privateLinkServiceId: keyVaultId
          groupIds: [
            'vault'
          ]
        }
      }
    ]
  }
}

// Private DNS Zone for Key Vault
resource keyVaultPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${privateDnsZonePrefix}.vaultcore.azure.net'
  location: 'global'
  tags: tags
}

// VNet Link for Key Vault DNS Zone
resource keyVaultDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: keyVaultPrivateDnsZone
  name: 'vnetlink'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetResourceId
    }
  }
}

// DNS A Record for Key Vault
resource keyVaultDnsARecord 'Microsoft.Network/privateDnsZones/A@2020-06-01' = {
  parent: keyVaultPrivateDnsZone
  name: keyVaultName
  properties: {
    aRecords: [
      {
        ipv4Address: keyVaultPrivateEndpoint.properties.customDnsConfigs[0].ipAddresses[0]
      }
    ]
    ttl: 3600
  }
}

// Private Endpoint for Storage Account (Blob)
resource storagePrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: '${privateEndpointNamePrefix}-storage'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetResourceId
    }
    privateLinkServiceConnections: [
      {
        name: 'storage-connection'
        properties: {
          privateLinkServiceId: storageAccountId
          groupIds: [
            'blob'
          ]
        }
      }
    ]
  }
}

// Private DNS Zone for Storage Account
resource storagePrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${privateDnsZonePrefix}.blob.${environment().suffixes.storage}'
  location: 'global'
  tags: tags
}

// VNet Link for Storage DNS Zone
resource storageDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: storagePrivateDnsZone
  name: 'vnetlink'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetResourceId
    }
  }
}

// DNS A Record for Storage Account
resource storageDnsARecord 'Microsoft.Network/privateDnsZones/A@2020-06-01' = {
  parent: storagePrivateDnsZone
  name: storageAccountName
  properties: {
    aRecords: [
      {
        ipv4Address: storagePrivateEndpoint.properties.customDnsConfigs[0].ipAddresses[0]
      }
    ]
    ttl: 3600
  }
}

// Conditional: Private Endpoint for App Configuration (if provided)
resource appConfigPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = if (!empty(appConfigId)) {
  name: '${privateEndpointNamePrefix}-appconfig'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetResourceId
    }
    privateLinkServiceConnections: [
      {
        name: 'appconfig-connection'
        properties: {
          privateLinkServiceId: appConfigId
          groupIds: [
            'configurationStores'
          ]
        }
      }
    ]
  }
}

// Private DNS Zone for App Configuration
resource appConfigPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (!empty(appConfigId)) {
  name: '${privateDnsZonePrefix}.azconfig.io'
  location: 'global'
  tags: tags
}

// VNet Link for App Config DNS Zone  
resource appConfigDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (!empty(appConfigId)) {
  name: 'vnetlink'
  location: 'global'
  parent: appConfigPrivateDnsZone
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetResourceId
    }
  }
}

// Outputs
@description('Cosmos DB private endpoint resource ID')
output cosmosDbPrivateEndpointId string = cosmosDbPrivateEndpoint.id

@description('Cosmos DB private endpoint NIC resource ID')
output cosmosDbPrivateEndpointNicId string = cosmosDbPrivateEndpoint.properties.networkInterfaces[0].id

@description('Key Vault private endpoint resource ID')
output keyVaultPrivateEndpointId string = keyVaultPrivateEndpoint.id

@description('Key Vault private endpoint NIC resource ID')
output keyVaultPrivateEndpointNicId string = keyVaultPrivateEndpoint.properties.networkInterfaces[0].id

@description('Storage private endpoint resource ID')
output storagePrivateEndpointId string = storagePrivateEndpoint.id

@description('Storage private endpoint NIC resource ID')
output storagePrivateEndpointNicId string = storagePrivateEndpoint.properties.networkInterfaces[0].id

@description('App Config private endpoint resource ID (if deployed)')
output appConfigPrivateEndpointId string = !empty(appConfigId) ? appConfigPrivateEndpoint.id : ''

@description('Cosmos DB private DNS zone resource ID')
output cosmosDbPrivateDnsZoneId string = cosmosDbPrivateDnsZone.id

@description('Key Vault private DNS zone resource ID')
output keyVaultPrivateDnsZoneId string = keyVaultPrivateDnsZone.id

@description('Storage private DNS zone resource ID')
output storagePrivateDnsZoneId string = storagePrivateDnsZone.id

@description('App Config private DNS zone resource ID (if deployed)')
output appConfigPrivateDnsZoneId string = !empty(appConfigId) ? appConfigPrivateDnsZone!.id : ''
