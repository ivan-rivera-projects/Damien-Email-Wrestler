import pino from 'pino';
import fs from 'fs'; // For directory creation
import path from 'path'; // For path manipulation
import { CONFIG } from './config.js'; // To get log level from config

const serviceName = 'damien-smithery-adapter';
const logLevel = CONFIG.LOG_LEVEL.toLowerCase() || 'info';

const pinoOptions: pino.LoggerOptions = {
  level: logLevel,
  base: {
    service: serviceName,
    pid: process.pid,
  },
  timestamp: () => `,"timestamp":"${new Date(Date.now()).toISOString()}"`,
  formatters: {
    level: (label: string) => {
      return { level: label.toUpperCase() };
    },
  },
  messageKey: 'message',
};

// Define transport targets
const targets: pino.TransportTargetOptions[] = [
  {
    target: 'pino/file', // Default console output (stdout)
    level: logLevel,
    options: { destination: 1 } // 1 = stdout
  }
];

if (CONFIG.LOG_FILE_PATH) {
  try {
    const logDir = path.dirname(CONFIG.LOG_FILE_PATH);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    targets.push({
      target: 'pino/file', // For file output
      level: logLevel,
      options: { destination: CONFIG.LOG_FILE_PATH, mkdir: true } // mkdir might be redundant if dir created above
    });
    // Initial log to console indicating file logging is set up, as logger isn't fully up yet.
    console.log(`[${serviceName}] File logging configured at ${CONFIG.LOG_FILE_PATH}`);
  } catch (err) {
    console.error(`[${serviceName}] CRITICAL: Failed to setup file logging at ${CONFIG.LOG_FILE_PATH}:`, err);
  }
}

const transport = pino.transport({ targets });
const logger = pino(pinoOptions, transport);

// Log initial setup (after logger is fully initialized)
logger.info(`Smithery Adapter logging initialized. Level: ${logLevel.toUpperCase()}. File logging: ${CONFIG.LOG_FILE_PATH ? 'Enabled to ' + CONFIG.LOG_FILE_PATH : 'Disabled'}`);


export default logger;