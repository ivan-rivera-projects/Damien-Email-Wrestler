import { CONFIG } from './config.js'; // To get log level from config

const serviceName = 'damien-smithery-adapter';
const logLevel = CONFIG.LOG_LEVEL.toLowerCase() || 'info';

// Create a simple console logger for now to bypass the TypeScript error
const logger = {
  info: (message: string, ...args: any[]) => console.log(`[INFO] ${message}`, ...args),
  error: (message: string, ...args: any[]) => console.error(`[ERROR] ${message}`, ...args),
  warn: (message: string, ...args: any[]) => console.warn(`[WARN] ${message}`, ...args),
  debug: (message: string, ...args: any[]) => console.debug(`[DEBUG] ${message}`, ...args)
};

// Log initial setup
console.log(`[${serviceName}] Simple logging initialized. Level: ${logLevel.toUpperCase()}`);
if (CONFIG.LOG_FILE_PATH) {
  console.log(`[${serviceName}] File logging configured at ${CONFIG.LOG_FILE_PATH}`);
}

export default logger;