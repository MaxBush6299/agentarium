// Cosmos DB module: SQL API with AI agent data collections
// Implements agent persistence layer with 6 collections for different data types

@description('Azure region for deployment')
param location string

@description('Tags to apply to all resources')
param tags object

@description('Cosmos DB account name')
param accountName string

@description('Cosmos DB throughput mode (manual or autoscale)')
param throughputMode string = 'autoscale'

@description('Cosmos DB provisioned throughput (manual mode)')
param manualProvisionedThroughput int = 400

@description('Cosmos DB autoscale max throughput (autoscale mode)')
param autoscaleMaxThroughput int = 4000

@description('Database name')
param databaseName string = 'agents-db'

@description('Enable backup redundancy')
param enableBackupRedundancy bool = true

// Calculate throughput settings based on mode
var throughputSettings = throughputMode == 'autoscale' ? {
  autoscaleSettings: {
    maxThroughput: autoscaleMaxThroughput
  }
} : {
  throughput: manualProvisionedThroughput
}

// Cosmos DB Account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: accountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'ConsistentPrefix'
      maxIntervalInSeconds: 5
      maxStalenessPrefix: 100
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: true
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
      {
        name: 'EnableTable'
      }
      {
        name: 'EnableCassandra'
      }
    ]
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 8
        backupStorageRedundancy: enableBackupRedundancy ? 'Geo' : 'Local'
      }
    }
    networkAclBypass: 'AzureServices'
    publicNetworkAccess: 'Disabled'
    disableKeyBasedMetadataWriteAccess: true
  }
}

// Cosmos DB SQL Database
resource sqlDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosDbAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

// Threads Collection - stores conversation threads
resource threadsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: sqlDatabase
  name: 'threads'
  properties: {
    resource: {
      id: 'threads'
      partitionKey: {
        paths: ['/agentId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      defaultTtl: 7776000 // 90 days
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: ['/threadId']
          }
        ]
      }
    }
    options: throughputSettings
  }
}

// Runs Collection - stores agent run executions
resource runsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: sqlDatabase
  name: 'runs'
  properties: {
    resource: {
      id: 'runs'
      partitionKey: {
        paths: ['/threadId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      defaultTtl: 7776000 // 90 days
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: ['/runId']
          }
        ]
      }
    }
    options: throughputSettings
  }
}

// Steps Collection - stores individual steps in agent execution
resource stepsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: sqlDatabase
  name: 'steps'
  properties: {
    resource: {
      id: 'steps'
      partitionKey: {
        paths: ['/runId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      defaultTtl: 7776000 // 90 days
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: ['/stepId']
          }
        ]
      }
    }
    options: throughputSettings
  }
}

// Tool Calls Collection - stores tool invocations and results
resource toolCallsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: sqlDatabase
  name: 'toolCalls'
  properties: {
    resource: {
      id: 'toolCalls'
      partitionKey: {
        paths: ['/stepId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      defaultTtl: 7776000 // 90 days
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: ['/toolCallId']
          }
        ]
      }
    }
    options: throughputSettings
  }
}

// Agents Collection - stores agent configurations and metadata
resource agentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: sqlDatabase
  name: 'agents'
  properties: {
    resource: {
      id: 'agents'
      partitionKey: {
        paths: ['/agentType']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: ['/agentId']
          }
        ]
      }
    }
    options: throughputSettings
  }
}

// Metrics Collection - stores performance and operational metrics
resource metricsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: sqlDatabase
  name: 'metrics'
  properties: {
    resource: {
      id: 'metrics'
      partitionKey: {
        paths: ['/timestamp']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      defaultTtl: 5184000 // 60 days for metrics retention
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: ['/metricId']
          }
        ]
      }
    }
    options: throughputSettings
  }
}

// Outputs
@description('Cosmos DB Account resource ID')
output cosmosDbAccountId string = cosmosDbAccount.id

@description('Cosmos DB Account name')
output cosmosDbAccountName string = cosmosDbAccount.name

@description('Cosmos DB Endpoint URL')
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint

@description('Database name')
output databaseName string = databaseName

@description('Threads collection name')
output threadsCollectionName string = 'threads'

@description('Runs collection name')
output runsCollectionName string = 'runs'

@description('Steps collection name')
output stepsCollectionName string = 'steps'

@description('Tool Calls collection name')
output toolCallsCollectionName string = 'toolCalls'

@description('Agents collection name')
output agentsCollectionName string = 'agents'

@description('Metrics collection name')
output metricsCollectionName string = 'metrics'
