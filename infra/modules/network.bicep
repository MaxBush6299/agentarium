// Network module: VNet, Subnets, NSGs, and Private DNS Zones
// Deploys network infrastructure with security best practices

@description('Azure region for deployment')
param location string

@description('Tags to apply to all resources')
param tags object

// VNet Parameters
@description('VNet address space')
param vnetAddressSpace string = '10.0.0.0/16'

@description('Container Apps subnet address space')
param containerAppsSubnetAddressSpace string = '10.0.1.0/24'

@description('Private endpoints subnet address space')
param privateEndpointsSubnetAddressSpace string = '10.0.2.0/24'

@description('Integration subnet address space (reserved for future use)')
param integrationSubnetAddressSpace string = '10.0.3.0/24'

// Variables for naming convention
var resourceNamePrefix = 'agents-demo'
var vnetName = 'vnet-${resourceNamePrefix}'
var nsgContainerAppsName = 'nsg-container-apps'
var nsgPrivateEndpointsName = 'nsg-private-endpoints'
var nsgIntegrationName = 'nsg-integration'
var containerAppsSubnetName = 'snet-container-apps'
var privateEndpointsSubnetName = 'snet-private-endpoints'
var integrationSubnetName = 'snet-integration'

// Container Apps NSG
resource containerAppsNsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: nsgContainerAppsName
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowHttpsFromInternet'
        properties: {
          protocol: 'TCP'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: 'Internet'
          destinationAddressPrefix: containerAppsSubnetAddressSpace
          access: 'Allow'
          priority: 100
          direction: 'Inbound'
        }
      }
      {
        name: 'AllowVNetInbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: containerAppsSubnetAddressSpace
          access: 'Allow'
          priority: 200
          direction: 'Inbound'
        }
      }
      {
        name: 'AllowAzureLoadBalancer'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'AzureLoadBalancer'
          destinationAddressPrefix: containerAppsSubnetAddressSpace
          access: 'Allow'
          priority: 300
          direction: 'Inbound'
        }
      }
      {
        name: 'DenyAllInbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          access: 'Deny'
          priority: 4096
          direction: 'Inbound'
        }
      }
      {
        name: 'AllowHttpsToInternet'
        properties: {
          protocol: 'TCP'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: containerAppsSubnetAddressSpace
          destinationAddressPrefix: 'Internet'
          access: 'Allow'
          priority: 100
          direction: 'Outbound'
        }
      }
      {
        name: 'AllowVNetOutbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: containerAppsSubnetAddressSpace
          destinationAddressPrefix: 'VirtualNetwork'
          access: 'Allow'
          priority: 200
          direction: 'Outbound'
        }
      }
      {
        name: 'AllowAzureMonitor'
        properties: {
          protocol: 'TCP'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: containerAppsSubnetAddressSpace
          destinationAddressPrefix: 'AzureMonitor'
          access: 'Allow'
          priority: 300
          direction: 'Outbound'
        }
      }
      {
        name: 'DenyAllOutbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          access: 'Deny'
          priority: 4096
          direction: 'Outbound'
        }
      }
    ]
  }
}

// Private Endpoints NSG
resource privateEndpointsNsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: nsgPrivateEndpointsName
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowContainerApps'
        properties: {
          protocol: 'TCP'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: containerAppsSubnetAddressSpace
          destinationAddressPrefix: privateEndpointsSubnetAddressSpace
          access: 'Allow'
          priority: 100
          direction: 'Inbound'
        }
      }
      {
        name: 'DenyAllInbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          access: 'Deny'
          priority: 4096
          direction: 'Inbound'
        }
      }
      {
        name: 'AllowResponseTraffic'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: privateEndpointsSubnetAddressSpace
          destinationAddressPrefix: '*'
          access: 'Allow'
          priority: 100
          direction: 'Outbound'
        }
      }
    ]
  }
}

// Integration NSG (reserved for future services)
resource integrationNsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: nsgIntegrationName
  location: location
  tags: tags
  properties: {
    securityRules: []
  }
}

// Virtual Network with subnets
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressSpace
      ]
    }
    subnets: [
      {
        name: containerAppsSubnetName
        properties: {
          addressPrefix: containerAppsSubnetAddressSpace
          networkSecurityGroup: {
            id: containerAppsNsg.id
          }
          delegations: [
            {
              name: 'Microsoft.App/environments'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        name: privateEndpointsSubnetName
        properties: {
          addressPrefix: privateEndpointsSubnetAddressSpace
          networkSecurityGroup: {
            id: privateEndpointsNsg.id
          }
        }
      }
      {
        name: integrationSubnetName
        properties: {
          addressPrefix: integrationSubnetAddressSpace
          networkSecurityGroup: {
            id: integrationNsg.id
          }
        }
      }
    ]
  }
}

// Outputs
@description('Virtual Network resource ID')
output vnetResourceId string = virtualNetwork.id

@description('Virtual Network name')
output vnetName string = virtualNetwork.name

@description('Container Apps subnet resource ID')
output containerAppsSubnetResourceId string = '${virtualNetwork.id}/subnets/${containerAppsSubnetName}'

@description('Container Apps subnet name')
output containerAppsSubnetName string = containerAppsSubnetName

@description('Private Endpoints subnet resource ID')
output privateEndpointsSubnetResourceId string = '${virtualNetwork.id}/subnets/${privateEndpointsSubnetName}'

@description('Private Endpoints subnet name')
output privateEndpointsSubnetName string = privateEndpointsSubnetName

@description('Integration subnet resource ID')
output integrationSubnetResourceId string = '${virtualNetwork.id}/subnets/${integrationSubnetName}'

@description('VNet address space for reference')
output vnetAddressSpace string = vnetAddressSpace

@description('Container Apps subnet address space')
output containerAppsSubnetAddressSpace string = containerAppsSubnetAddressSpace

@description('Private Endpoints subnet address space')
output privateEndpointsSubnetAddressSpace string = privateEndpointsSubnetAddressSpace

