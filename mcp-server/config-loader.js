#!/usr/bin/env node

/**
 * Azure MCP Server Configuration Loader
 * Loads and validates configuration from JSON files with environment variable substitution
 */

const fs = require('fs');
const path = require('path');

/**
 * Load configuration file with environment variable substitution
 */
function loadConfig(configPath) {
  if (!fs.existsSync(configPath)) {
    throw new Error(`Configuration file not found: ${configPath}`);
  }

  let configContent = fs.readFileSync(configPath, 'utf-8');

  // Replace environment variables: ${VAR_NAME} -> process.env.VAR_NAME
  configContent = configContent.replace(/\$\{([A-Z_]+)\}/g, (match, envVar) => {
    const value = process.env[envVar];
    if (value === undefined) {
      throw new Error(`Environment variable not found: ${envVar}`);
    }
    return value;
  });

  try {
    return JSON.parse(configContent);
  } catch (error) {
    throw new Error(`Failed to parse configuration: ${error.message}`);
  }
}

/**
 * Validate configuration against schema
 */
function validateConfig(config, schema) {
  // Basic validation - check required fields
  if (!config.server) {
    throw new Error('Configuration missing required field: server');
  }
  if (!config.authentication) {
    throw new Error('Configuration missing required field: authentication');
  }
  if (!config.azure) {
    throw new Error('Configuration missing required field: azure');
  }

  // Validate authentication type
  const validAuthTypes = ['managedIdentity', 'servicePrincipal', 'azureCliCredential'];
  if (!validAuthTypes.includes(config.authentication.type)) {
    throw new Error(`Invalid authentication type: ${config.authentication.type}`);
  }

  // Validate resource scope
  if (config.azure.resourceScope) {
    const validScopes = ['subscription', 'resourceGroup', 'resource'];
    if (!validScopes.includes(config.azure.resourceScope)) {
      throw new Error(`Invalid resource scope: ${config.azure.resourceScope}`);
    }
  }

  return true;
}

/**
 * Get default configuration based on environment
 */
function getDefaultConfigPath(environment) {
  const configDir = path.join(__dirname, 'config');

  switch (environment) {
    case 'production':
    case 'prod':
      return path.join(configDir, 'prod.json');
    case 'development':
    case 'dev':
    default:
      return path.join(configDir, 'dev.json');
  }
}

/**
 * Load and validate configuration
 */
function loadAndValidateConfig(configPathOrEnv) {
  const schemaPath = path.join(__dirname, 'config', 'schema.json');
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf-8'));

  let configPath = configPathOrEnv;

  // If argument looks like an environment name, get the default path
  if (!configPathOrEnv || ['dev', 'prod', 'development', 'production'].includes(configPathOrEnv)) {
    const env = configPathOrEnv || process.env.NODE_ENV || 'development';
    configPath = getDefaultConfigPath(env);
    console.log(`Using ${env} configuration: ${configPath}`);
  }

  const config = loadConfig(configPath);
  validateConfig(config, schema);

  return config;
}

module.exports = {
  loadConfig,
  validateConfig,
  getDefaultConfigPath,
  loadAndValidateConfig,
};

// If run directly, print loaded configuration
if (require.main === module) {
  try {
    const configArg = process.argv[2] || process.env.NODE_ENV || 'development';
    const config = loadAndValidateConfig(configArg);
    console.log(JSON.stringify(config, null, 2));
  } catch (error) {
    console.error(`Configuration error: ${error.message}`);
    process.exit(1);
  }
}
