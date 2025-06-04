/**
 * Configuration for Minimal Damien MCP Server
 * Manages environment variables and server settings
 */

// Import dotenv for environment variable loading
import dotenv from 'dotenv';
import { existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Resolve paths relative to project root
const projectRoot = resolve(__dirname, '..');
const projectParent = resolve(projectRoot, '..');

// Try to load environment variables from different locations
// First try project-specific .env, then fall back to parent project .env
const envPaths = [
  resolve(projectRoot, '.env'),
  resolve(projectParent, '.env')
];

let envLoaded = false;
for (const envPath of envPaths) {
  if (existsSync(envPath)) {
    dotenv.config({ path: envPath });
    console.error(`Environment variables loaded from: ${envPath}`);
    envLoaded = true;
    break;
  }
}

if (!envLoaded) {
  console.error('Warning: No .env file found, using default values');
  // Load from .env.example if available
  const exampleEnvPath = resolve(projectRoot, '.env.example');
  if (existsSync(exampleEnvPath)) {
    dotenv.config({ path: exampleEnvPath });
    console.error(`Environment variables loaded from example: ${exampleEnvPath}`);
  }
}

export const CONFIG = {
  // Backend connection settings
  BACKEND_URL: process.env.DAMIEN_BACKEND_URL || process.env.DAMIEN_MCP_SERVER_URL || 'http://localhost:8892',
  API_KEY: process.env.DAMIEN_MCP_SERVER_API_KEY || '7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f',
  
  // Server configuration
  SERVER_NAME: 'damien_email_wrestler_minimal',
  SERVER_VERSION: '1.0.0',
  SERVER_PORT: parseInt(process.env.DAMIEN_MCP_MINIMAL_PORT || '8893', 10),
  
  // Request timeouts and retries
  DEFAULT_TIMEOUT: parseInt(process.env.DAMIEN_DEFAULT_TIMEOUT || '30000', 10), // 30 seconds
  HEALTH_CHECK_TIMEOUT: parseInt(process.env.DAMIEN_HEALTH_CHECK_TIMEOUT || '5000', 10), // 5 seconds
  MAX_RETRIES: parseInt(process.env.DAMIEN_MAX_RETRIES || '3', 10),
  RETRY_DELAY: parseInt(process.env.DAMIEN_RETRY_DELAY || '1000', 10), // 1 second
  
  // Tool caching settings
  TOOL_CACHE_DURATION: parseInt(process.env.DAMIEN_TOOL_CACHE_DURATION || '3600000', 10), // 1 hour
  
  // Phase management
  INITIAL_PHASE: parseInt(process.env.DAMIEN_INITIAL_PHASE || '1', 10),
  PHASE_AUTO_PROGRESS: process.env.DAMIEN_PHASE_AUTO_PROGRESS === 'true',
  
  // Logging configuration
  LOG_LEVEL: process.env.LOG_LEVEL || 'INFO',
  VERBOSE_LOGGING: process.env.VERBOSE_LOGGING === 'true',
  LOG_TO_FILE: process.env.DAMIEN_LOG_TO_FILE === 'true',
  LOG_FILE_PATH: process.env.DAMIEN_LOG_FILE_PATH || resolve(projectRoot, 'logs/mcp-minimal.log'),
  
  // Development settings
  NODE_ENV: process.env.NODE_ENV || 'production',
  
  // AWS configuration for optional features
  AWS_REGION: process.env.AWS_REGION || 'us-east-1',
  DYNAMODB_TABLE_NAME: process.env.DYNAMODB_TABLE_NAME || 'DamienMCPSessions',
  
  // Paths for deployment and backups
  CLAUDE_DESKTOP_CONFIG_PATH: process.env.CLAUDE_DESKTOP_CONFIG_PATH || 
    (process.platform === 'darwin' 
      ? '~/Library/Application Support/Claude Desktop/config.json'
      : process.platform === 'win32'
        ? '%APPDATA%\\Claude Desktop\\config.json'
        : '~/.config/Claude Desktop/config.json'),
  BACKUP_DIR: process.env.DAMIEN_BACKUP_DIR || resolve(projectRoot, 'backups'),
};

/**
 * Validate configuration
 */
export function validateConfig() {
  const errors = [];
  
  // Validate backend URL
  if (!CONFIG.BACKEND_URL) {
    errors.push('DAMIEN_MCP_SERVER_URL is required');
  } else {
    try {
      new URL(CONFIG.BACKEND_URL);
    } catch (error) {
      errors.push(`Invalid DAMIEN_MCP_SERVER_URL format: ${CONFIG.BACKEND_URL}`);
    }
  }
  
  // Validate API key
  if (!CONFIG.API_KEY || CONFIG.API_KEY.length < 32) {
    errors.push('DAMIEN_MCP_SERVER_API_KEY must be at least 32 characters');
  }
  
  // Validate server port
  if (isNaN(CONFIG.SERVER_PORT) || CONFIG.SERVER_PORT < 1024 || CONFIG.SERVER_PORT > 65535) {
    errors.push(`Invalid server port: ${CONFIG.SERVER_PORT}. Must be between 1024 and 65535.`);
  }
  
  // Validate initial phase
  if (isNaN(CONFIG.INITIAL_PHASE) || CONFIG.INITIAL_PHASE < 1 || CONFIG.INITIAL_PHASE > 6) {
    errors.push(`Invalid initial phase: ${CONFIG.INITIAL_PHASE}. Must be between 1 and 6.`);
  }
  
  // Validate timeout values
  if (isNaN(CONFIG.DEFAULT_TIMEOUT) || CONFIG.DEFAULT_TIMEOUT < 1000) {
    errors.push(`Invalid default timeout: ${CONFIG.DEFAULT_TIMEOUT}. Must be at least 1000ms.`);
  }
  
  // Validate log level
  const validLogLevels = ['DEBUG', 'INFO', 'WARNING', 'ERROR'];
  if (!validLogLevels.includes(CONFIG.LOG_LEVEL.toUpperCase())) {
    errors.push(`Invalid log level: ${CONFIG.LOG_LEVEL}. Must be one of: ${validLogLevels.join(', ')}.`);
  }
  
  if (errors.length > 0) {
    throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
  }
}

/**
 * Log configuration (for debugging)
 */
export function logConfig() {
  if (CONFIG.VERBOSE_LOGGING || process.env.NODE_ENV === 'development') {
    console.error('📋 Minimal MCP Server Configuration:');
    console.error(`   Backend URL: ${CONFIG.BACKEND_URL}`);
    console.error(`   API Key: ${CONFIG.API_KEY.substring(0, 16)}...`);
    console.error(`   Server Name: ${CONFIG.SERVER_NAME}`);
    console.error(`   Server Port: ${CONFIG.SERVER_PORT}`);
    console.error(`   Initial Phase: ${CONFIG.INITIAL_PHASE}`);
    console.error(`   Environment: ${CONFIG.NODE_ENV}`);
    console.error(`   Log Level: ${CONFIG.LOG_LEVEL}`);
    console.error(`   Tool Cache Duration: ${CONFIG.TOOL_CACHE_DURATION}ms (${CONFIG.TOOL_CACHE_DURATION / 1000 / 60} minutes)`);
  }
}

export default CONFIG;
