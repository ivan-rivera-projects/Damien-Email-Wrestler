// src/config.ts
import dotenv from 'dotenv';
dotenv.config(); // Loads .env file into process.env

export const CONFIG = {
  DAMIEN_MCP_SERVER_URL: process.env.DAMIEN_MCP_SERVER_URL || 'http://localhost:8892',
  DAMIEN_MCP_SERVER_API_KEY: '7a508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f', // Hardcoded for debugging
  
  SERVER_PORT: parseInt(process.env.SERVER_PORT || '8081', 10), // Port for THIS Smithery adapter server
  SERVER_NAME: process.env.SERVER_NAME || 'Damien Email Manager via Smithery',
  SERVER_VERSION: process.env.SERVER_VERSION || '1.0.0',
  
  SMITHERY_REGISTRY_URL: process.env.SMITHERY_REGISTRY_URL || 'https://registry.smithery.ai', // If different
  SMITHERY_BEARER_AUTH: process.env.SMITHERY_BEARER_AUTH || '', // Your token for Smithery Registry
  LOG_LEVEL: process.env.LOG_LEVEL || 'info',
  LOG_FILE_PATH: process.env.ADAPTER_LOG_FILE_PATH || '../../logs/smithery-adapter.log', // Default to project logs dir
};

if (!CONFIG.DAMIEN_MCP_SERVER_API_KEY) {
  console.error('CRITICAL ERROR: DAMIEN_MCP_SERVER_API_KEY environment variable is required for the Smithery adapter to call the Damien MCP Server.');
  process.exit(1);
}
if (!CONFIG.SMITHERY_BEARER_AUTH && process.env.NODE_ENV !== 'development_no_registry') { // Allow no registry auth for local dev without registration
    console.warn('WARNING: SMITHERY_BEARER_AUTH is not set. Server registration with Smithery Registry will fail.');
}