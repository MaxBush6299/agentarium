/**
 * Frontend Application Configuration
 * Environment variables and API configuration
 */

export const config = {
  // API Configuration
  apiBaseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  
  // Entra ID (Azure AD) Configuration
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID || '',
    authority: import.meta.env.VITE_ENTRA_AUTHORITY || '',
    redirectUri: import.meta.env.VITE_ENTRA_REDIRECT_URI || window.location.origin,
    scopes: [
      (import.meta.env.VITE_API_SCOPE || 'https://localhost/api/.default')
    ],
  },
  
  // Application Configuration
  app: {
    name: 'Agentarium',
    version: '0.1.0',
    environment: import.meta.env.MODE || 'development',
  },
  
  // Feature Flags
  features: {
    enableTracing: import.meta.env.VITE_ENABLE_TRACING !== 'false',
    enableChatExport: import.meta.env.VITE_ENABLE_CHAT_EXPORT !== 'false',
    enableA2AVisualization: import.meta.env.VITE_ENABLE_A2A_VIZ !== 'false',
  },
}

// Development mode detection
export const isDevelopment = config.app.environment === 'development'
export const isProduction = config.app.environment === 'production'
