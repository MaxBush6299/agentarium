// Observability module: Application Insights and Log Analytics workspace
// Provides monitoring and diagnostics for the AI agents platform

@description('Azure region for deployment')
param location string

@description('Tags to apply to all resources')
param tags object

@description('Log Analytics workspace name')
param logAnalyticsWorkspaceName string

@description('Application Insights name')
param appInsightsName string

@description('Log Analytics workspace retention in days (0-730, 0 = unlimited)')
param logRetentionDays int = 30

@description('Application Insights daily data cap in GB')
param appInsightsDailyCapGb int = 10

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: logRetentionDays
    workspaceCapping: {
      dailyQuotaGb: appInsightsDailyCapGb
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    RetentionInDays: logRetentionDays
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    IngestionMode: 'LogAnalytics'
  }
}

// Log Analytics Solutions for Container Monitoring
resource containerInsightsSolution 'Microsoft.OperationsManagement/solutions@2015-11-01-preview' = {
  name: 'ContainerInsights(${logAnalyticsWorkspace.name})'
  location: location
  tags: tags
  properties: {
    workspaceResourceId: logAnalyticsWorkspace.id
  }
  plan: {
    name: 'ContainerInsights(${logAnalyticsWorkspace.name})'
    publisher: 'Microsoft'
    product: 'OMSGallery/ContainerInsights'
    promotionCode: ''
  }
}

// Outputs
@description('Log Analytics Workspace resource ID')
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id

@description('Log Analytics Workspace name')
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name

@description('Application Insights resource ID')
output appInsightsId string = appInsights.id

@description('Application Insights name')
output appInsightsName string = appInsights.name

@description('Application Insights instrumentation key')
@secure()
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey

@description('Application Insights connection string')
@secure()
output appInsightsConnectionString string = appInsights.properties.ConnectionString

@description('Container Insights solution ID')
output containerInsightsSolutionId string = containerInsightsSolution.id
