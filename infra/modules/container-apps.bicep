// Container Apps module: Managed container hosting environment
// Deploys Container Apps environment integrated with VNet and monitoring

@description('Azure region for deployment')
param location string

@description('Tags to apply to all resources')
param tags object

@description('Resource ID of the Container Apps subnet')
param containerAppsSubnetResourceId string

@description('Log Analytics workspace ID')
param logAnalyticsWorkspaceId string

@description('Application Insights instrumentation key (secure)')
@secure()
param appInsightsInstrumentationKey string

@description('Environment name for the Container Apps (dev/prod)')
param environmentName string = 'demo'

@description('Cosmos DB endpoint URL')
param cosmosDbEndpoint string

@description('Cosmos DB database name')
param cosmosDbDatabaseName string = 'agents-db'

@description('Frontend URL for CORS configuration')
param frontendUrl string = ''

@description('Azure OpenAI endpoint URL')
param azureOpenAIEndpoint string = ''

@description('Azure OpenAI API key (secure)')
@secure()
param azureOpenAIApiKey string = ''

@description('Azure OpenAI API version')
param azureOpenAIApiVersion string = '2025-03-01-preview'

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: 'cae-${environmentName}'
  location: location
  tags: tags
  properties: {
    vnetConfiguration: {
      internal: false
      infrastructureSubnetId: containerAppsSubnetResourceId
    }
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2021-06-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2021-06-01').primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// Frontend Container App
resource frontendContainerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: 'ca-frontend-${environmentName}'
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    environmentId: containerAppsEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      maxInactiveRevisions: 2
      registries: []
      secrets: [
        {
          name: 'appinsights-key'
          value: appInsightsInstrumentationKey
        }
      ]
      ingress: {
        external: true
        allowInsecure: false
        targetPort: 3000
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
    }
    template: {
      revisionSuffix: 'v1'
      containers: [
        {
          name: 'frontend'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'APPLICATIONINSIGHTS_INSTRUMENTATION_KEY'
              secretRef: 'appinsights-key'
            }
            {
              name: 'ASPNETCORE_ENVIRONMENT'
              value: 'Production'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-requests'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Backend Container App
resource backendContainerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: 'ca-backend-${environmentName}'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    environmentId: containerAppsEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      maxInactiveRevisions: 2
      registries: []
      secrets: [
        {
          name: 'appinsights-key'
          value: appInsightsInstrumentationKey
        }
        {
          name: 'azure-openai-api-key'
          value: azureOpenAIApiKey
        }
      ]
      ingress: {
        external: false
        allowInsecure: false
        targetPort: 8080
      }
    }
    template: {
      revisionSuffix: 'v1'
      containers: [
        {
          name: 'backend'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'APPLICATIONINSIGHTS_INSTRUMENTATION_KEY'
              secretRef: 'appinsights-key'
            }
            {
              name: 'ASPNETCORE_ENVIRONMENT'
              value: 'Production'
            }
            {
              name: 'COSMOS_ENDPOINT'
              value: cosmosDbEndpoint
            }
            {
              name: 'COSMOS_DATABASE_NAME'
              value: cosmosDbDatabaseName
            }
            {
              name: 'FRONTEND_URL'
              value: !empty(frontendUrl) ? frontendUrl : 'https://ca-frontend-${environmentName}.${containerAppsEnvironment.properties.defaultDomain}'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAIEndpoint
            }
            {
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'azure-openai-api-key'
            }
            {
              name: 'AZURE_OPENAI_API_VERSION'
              value: azureOpenAIApiVersion
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-requests'
            http: {
              metadata: {
                concurrentRequests: '30'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
@description('Container Apps Environment resource ID')
output containerAppsEnvironmentId string = containerAppsEnvironment.id

@description('Container Apps Environment name')
output containerAppsEnvironmentName string = containerAppsEnvironment.name

@description('Frontend Container App resource ID')
output frontendContainerAppId string = frontendContainerApp.id

@description('Frontend Container App name')
output frontendContainerAppName string = frontendContainerApp.name

@description('Frontend Container App FQDN')
output frontendFqdn string = frontendContainerApp.properties.configuration.ingress.fqdn

@description('Backend Container App resource ID')
output backendContainerAppId string = backendContainerApp.id

@description('Backend Container App name')
output backendContainerAppName string = backendContainerApp.name

@description('Backend Container App FQDN')
output backendFqdn string = backendContainerApp.properties.configuration.ingress.fqdn

@description('Backend Container App managed identity principal ID')
output backendPrincipalId string = backendContainerApp.identity.principalId
