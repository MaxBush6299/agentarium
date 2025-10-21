#!/usr/bin/env node

/**
 * Azure MCP Server
 * Provides Azure resource access via Model Context Protocol
 * Supports managed identity, service principal, and Azure CLI credential authentication
 */

import express from 'express';
import pino from 'pino';
import { DefaultAzureCredential, AzureCliCredential, ClientSecretCredential } from '@azure/identity';
import { ResourcesClient } from '@azure/arm-resources';
import { WebSiteManagementClient } from '@azure/arm-appservice';
import { ComputeManagementClient } from '@azure/arm-compute';
import { ContainerInstanceManagementClient } from '@azure/arm-containerinstance';
import { CosmosDBManagementClient } from '@azure/arm-cosmosdb';
import { StorageManagementClient } from '@azure/arm-storage';
import { KeyVaultManagementClient } from '@azure/arm-keyvault';
import { LogsQueryClient } from '@azure/monitor-query';
import fs from 'fs';
import path from 'path';

// Load configuration
const configLoader = await import('./config-loader.js');
const config = configLoader.loadAndValidateConfig(process.env.NODE_ENV || 'development');

// Initialize logger
const logger = pino({
  level: config.logging.level || 'info',
  transport: config.logging.format === 'text' ? {
    target: 'pino-pretty',
    options: {
      colorize: true,
      ignore: 'pid,hostname',
    }
  } : undefined,
});

// Initialize Express app
const app = express();
app.use(express.json());

// Request logging middleware
app.use((req, res, next) => {
  logger.info({ method: req.method, path: req.path, query: req.query }, 'Incoming request');
  next();
});

// Initialize Azure credential based on configuration
let credential;

try {
  if (config.authentication.type === 'managedIdentity') {
    logger.info('Using Managed Identity authentication');
    const clientId = config.authentication.managedIdentity?.clientId;
    if (clientId) {
      credential = new DefaultAzureCredential({ managedIdentityClientId: clientId });
    } else {
      credential = new DefaultAzureCredential();
    }
  } else if (config.authentication.type === 'servicePrincipal') {
    logger.info('Using Service Principal authentication');
    const sp = config.authentication.servicePrincipal;
    credential = new ClientSecretCredential(sp.tenantId, sp.clientId, sp.clientSecret);
  } else if (config.authentication.type === 'azureCliCredential') {
    logger.info('Using Azure CLI credential authentication (development mode)');
    credential = new AzureCliCredential();
  } else {
    throw new Error(`Unsupported authentication type: ${config.authentication.type}`);
  }
} catch (error) {
  logger.error({ error: error.message }, 'Failed to initialize Azure credential');
  process.exit(1);
}

// Initialize Azure clients
const subscriptionId = config.azure.subscriptionId;
const resourcesClient = new ResourcesClient(credential, { subscriptionId });
const appServiceClient = new WebSiteManagementClient(credential, { subscriptionId });
const computeClient = new ComputeManagementClient(credential, { subscriptionId });
const containerClient = new ContainerInstanceManagementClient(credential, { subscriptionId });
const cosmosClient = new CosmosDBManagementClient(credential, { subscriptionId });
const storageClient = new StorageManagementClient(credential, { subscriptionId });
const keyVaultClient = new KeyVaultManagementClient(credential, { subscriptionId });
const logsQueryClient = new LogsQueryClient(credential);

logger.info({ subscriptionId }, 'Azure clients initialized');

// Response caching
const cache = new Map();

function getCacheKey(key) {
  return cache.get(key);
}

function setCacheKey(key, value, ttl) {
  cache.set(key, value);
  if (config.caching.enabled && ttl) {
    setTimeout(() => cache.delete(key), ttl * 1000);
  }
}

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      config: {
        authentication: config.authentication.type,
        subscriptionId: subscriptionId,
        resourceScope: config.azure.resourceScope,
      },
    });
  } catch (error) {
    logger.error({ error: error.message }, 'Health check failed');
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
    });
  }
});

// List available tools
app.get('/tools', (req, res) => {
  const tools = [];

  if (config.tools.resources) {
    tools.push({
      name: 'list_resources',
      description: 'List all Azure resources in the subscription',
      inputSchema: {
        type: 'object',
        properties: {
          filter: {
            type: 'string',
            description: 'Optional filter expression',
          },
          limit: {
            type: 'integer',
            description: 'Maximum number of resources to return',
            default: 100,
          },
        },
      },
    });
  }

  if (config.tools.resourceGroups) {
    tools.push({
      name: 'list_resource_groups',
      description: 'List all resource groups',
      inputSchema: {
        type: 'object',
        properties: {
          limit: {
            type: 'integer',
            description: 'Maximum number of groups to return',
            default: 50,
          },
        },
      },
    });
  }

  if (config.tools.appServices) {
    tools.push({
      name: 'list_app_services',
      description: 'List all App Services',
      inputSchema: {
        type: 'object',
        properties: {
          resourceGroup: {
            type: 'string',
            description: 'Filter by resource group',
          },
        },
      },
    });
  }

  if (config.tools.virtualMachines) {
    tools.push({
      name: 'list_virtual_machines',
      description: 'List all Virtual Machines',
      inputSchema: {
        type: 'object',
        properties: {
          resourceGroup: {
            type: 'string',
            description: 'Filter by resource group',
          },
        },
      },
    });
  }

  if (config.tools.cosmos) {
    tools.push({
      name: 'list_cosmos_accounts',
      description: 'List all Cosmos DB accounts',
      inputSchema: {
        type: 'object',
        properties: {
          resourceGroup: {
            type: 'string',
            description: 'Filter by resource group',
          },
        },
      },
    });
  }

  if (config.tools.storage) {
    tools.push({
      name: 'list_storage_accounts',
      description: 'List all Storage Accounts',
      inputSchema: {
        type: 'object',
        properties: {
          resourceGroup: {
            type: 'string',
            description: 'Filter by resource group',
          },
        },
      },
    });
  }

  if (config.tools.keyVault) {
    tools.push({
      name: 'list_key_vaults',
      description: 'List all Key Vaults',
      inputSchema: {
        type: 'object',
        properties: {
          resourceGroup: {
            type: 'string',
            description: 'Filter by resource group',
          },
        },
      },
    });
  }

  if (config.tools.monitoring) {
    tools.push({
      name: 'query_logs',
      description: 'Query Log Analytics logs',
      inputSchema: {
        type: 'object',
        properties: {
          workspaceId: {
            type: 'string',
            description: 'Log Analytics workspace ID',
          },
          query: {
            type: 'string',
            description: 'KQL query',
          },
          timespan: {
            type: 'string',
            description: 'Time span (e.g., PT1H for 1 hour)',
            default: 'PT1H',
          },
        },
        required: ['workspaceId', 'query'],
      },
    });
  }

  res.json({
    tools,
    count: tools.length,
  });
});

// List resources endpoint
app.post('/tools/list_resources', async (req, res) => {
  try {
    const { filter, limit = 100 } = req.body;
    logger.info({ filter, limit }, 'Listing resources');

    const resources = [];
    for await (const resource of resourcesClient.list()) {
      if (resources.length >= limit) break;
      resources.push({
        id: resource.id,
        name: resource.name,
        type: resource.type,
        location: resource.location,
      });
    }

    res.json({ resources, count: resources.length });
  } catch (error) {
    logger.error({ error: error.message }, 'Failed to list resources');
    res.status(500).json({ error: error.message });
  }
});

// List resource groups endpoint
app.post('/tools/list_resource_groups', async (req, res) => {
  try {
    const { limit = 50 } = req.body;
    logger.info({ limit }, 'Listing resource groups');

    const groups = [];
    for await (const group of resourcesClient.resourceGroups.list()) {
      if (groups.length >= limit) break;
      groups.push({
        id: group.id,
        name: group.name,
        location: group.location,
      });
    }

    res.json({ groups, count: groups.length });
  } catch (error) {
    logger.error({ error: error.message }, 'Failed to list resource groups');
    res.status(500).json({ error: error.message });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error({ error: err.message, stack: err.stack }, 'Unhandled error');
  res.status(500).json({
    error: 'Internal server error',
    message: err.message,
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Start server
const PORT = config.server.port || 3000;
const HOST = config.server.host || '0.0.0.0';

app.listen(PORT, HOST, () => {
  logger.info({ host: HOST, port: PORT }, 'Azure MCP Server started');
  logger.info({ authentication: config.authentication.type }, 'Authentication configured');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});
