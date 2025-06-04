#!/usr/bin/env node
/**
 * Enhanced Claude MAX Compatible MCP Server for Damien Email Wrestler
 * Addresses tool loading issues and provides robust error handling
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';

// Configuration with validation
const CONFIG = {
  DAMIEN_URL: process.env.DAMIEN_MCP_SERVER_URL || 'http://localhost:8892',
  API_KEY: process.env.DAMIEN_MCP_SERVER_API_KEY,
  SERVER_NAME: process.env.SERVER_NAME || 'damien_email_wrestler',
  SERVER_VERSION: process.env.SERVER_VERSION || '2.0.0',
  TIMEOUT_MS: 30000,
  HEALTH_CHECK_TIMEOUT_MS: 5000,
  MAX_RETRIES: 3,
};

// Validate required configuration
if (!CONFIG.API_KEY || CONFIG.API_KEY.length < 32) {
  console.error('❌ Invalid or missing DAMIEN_MCP_SERVER_API_KEY');
  process.exit(1);
}

// Enhanced logging with proper stderr handling
const log = (message, level = 'INFO') => {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${level}: ${message}`;
  process.stderr.write(logMessage + '\n');
};

class EnhancedClaudeMaxServer {
  constructor() {
    this.tools = [];
    this.toolsLastLoaded = null;
    this.toolsCache = null;
    this.server = new Server(
      {
        name: CONFIG.SERVER_NAME,
        version: CONFIG.SERVER_VERSION,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
    this.setupErrorHandlers();
  }

  setupErrorHandlers() {
    // Global error handlers
    process.on('uncaughtException', (error) => {
      log(`Uncaught exception: ${error.message}`, 'ERROR');
      log(error.stack, 'ERROR');
      process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
      log(`Unhandled rejection at: ${promise}, reason: ${reason}`, 'ERROR');
    });
  }

  async makeRequest(url, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), options.timeout || CONFIG.TIMEOUT_MS);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'X-API-Key': CONFIG.API_KEY,
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeout);

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      return response;
    } catch (error) {
      clearTimeout(timeout);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timed out');
      }
      
      throw error;
    }
  }

  async healthCheck() {
    try {
      await this.makeRequest(`${CONFIG.DAMIEN_URL}/health`, {
        timeout: CONFIG.HEALTH_CHECK_TIMEOUT_MS,
      });
      return true;
    } catch (error) {
      log(`Health check failed: ${error.message}`, 'WARN');
      return false;
    }
  }

  validateTool(tool) {
    // Comprehensive tool validation for Claude MAX compatibility
    if (!tool || typeof tool !== 'object') {
      return null;
    }

    const name = tool.name || tool.tool_name;
    if (!name || typeof name !== 'string') {
      log(`Skipping tool with invalid name: ${JSON.stringify(tool)}`, 'WARN');
      return null;
    }

    // Clean and validate description
    const description = tool.description || `Tool for ${name}`;
    
    // Process and validate input schema
    let inputSchema = tool.input_schema || tool.inputSchema || tool.schema;
    
    if (!inputSchema || typeof inputSchema !== 'object') {
      inputSchema = {
        type: 'object',
        properties: {},
        required: [],
      };
    }

    // Fix common schema issues for Claude MAX
    if (inputSchema.properties) {
      const fixedProperties = {};
      
      for (const [propName, prop] of Object.entries(inputSchema.properties)) {
        if (!prop || typeof prop !== 'object') {
          continue;
        }

        const fixedProp = { ...prop };

        // Fix array schema issues
        if (fixedProp.type === 'array' && fixedProp.items) {
          if (typeof fixedProp.items === 'string') {
            fixedProp.items = { type: fixedProp.items };
          }
        }

        // Ensure required fields have proper types
        if (!fixedProp.type) {
          fixedProp.type = 'string'; // Default to string
        }

        // Clean up description
        if (fixedProp.description) {
          fixedProp.description = String(fixedProp.description).trim();
        }

        fixedProperties[propName] = fixedProp;
      }

      inputSchema.properties = fixedProperties;
    }

    // Ensure required array exists and is valid
    if (!Array.isArray(inputSchema.required)) {
      inputSchema.required = [];
    }

    return {
      name: name.trim(),
      description: description.trim(),
      inputSchema,
    };
  }

  async loadTools() {
    try {
      // Check if we need to reload tools (cache for 5 minutes)
      const now = Date.now();
      if (this.toolsCache && this.toolsLastLoaded && (now - this.toolsLastLoaded) < 300000) {
        log('Using cached tools');
        this.tools = this.toolsCache;
        return;
      }

      log('Loading tools from Damien MCP Server...');

      // Verify backend is healthy first
      if (!(await this.healthCheck())) {
        throw new Error('Backend server is not healthy');
      }

      const response = await this.makeRequest(`${CONFIG.DAMIEN_URL}/mcp/list_tools`);
      const responseData = await response.json();
      
      // Handle both formats: direct array or { tools: [] }
      const rawTools = Array.isArray(responseData) ? responseData : 
                       (responseData && responseData.tools && Array.isArray(responseData.tools)) ? 
                       responseData.tools : [];

      if (rawTools.length === 0) {
        throw new Error('No tools found in response');
      }

      log(`Received ${rawTools.length} raw tools from backend`);

      // Validate and process tools
      const validatedTools = [];
      const invalidTools = [];

      for (const rawTool of rawTools) {
        const validatedTool = this.validateTool(rawTool);
        if (validatedTool) {
          validatedTools.push(validatedTool);
        } else {
          invalidTools.push(rawTool);
        }
      }

      if (invalidTools.length > 0) {
        log(`Filtered out ${invalidTools.length} invalid tools`, 'WARN');
      }

      this.tools = validatedTools;
      this.toolsCache = validatedTools;
      this.toolsLastLoaded = now;

      log(`Successfully loaded and validated ${this.tools.length} tools`);

      // Log sample of tool names for debugging
      const sampleTools = this.tools.slice(0, 5).map(t => t.name);
      log(`Sample tools: ${sampleTools.join(', ')}`);

    } catch (error) {
      log(`Error loading tools: ${error.message}`, 'ERROR');
      
      // Provide essential fallback tools to ensure Claude MAX can work
      this.tools = this.getFallbackTools();
      log(`Using ${this.tools.length} fallback tools`);
    }
  }

  getFallbackTools() {
    return [
      {
        name: 'damien_list_emails',
        description: 'List emails from your Gmail account with optional search filters',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Gmail search query (optional)',
            },
            max_results: {
              type: 'integer',
              description: 'Maximum number of emails to return (default: 10)',
              default: 10,
            },
          },
          required: [],
        },
      },
      {
        name: 'damien_send_email',
        description: 'Send an email through Gmail',
        inputSchema: {
          type: 'object',
          properties: {
            to: {
              type: 'string',
              description: 'Recipient email address',
            },
            subject: {
              type: 'string',
              description: 'Email subject',
            },
            body: {
              type: 'string',
              description: 'Email body content',
            },
          },
          required: ['to', 'subject', 'body'],
        },
      },
      {
        name: 'damien_get_email_details',
        description: 'Get detailed information about a specific email',
        inputSchema: {
          type: 'object',
          properties: {
            email_id: {
              type: 'string',
              description: 'The ID of the email to retrieve',
            },
          },
          required: ['email_id'],
        },
      },
    ];
  }

  setupHandlers() {
    // List tools handler with caching
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      try {
        if (this.tools.length === 0) {
          await this.loadTools();
        }

        log(`Returning ${this.tools.length} tools to Claude MAX`);
        
        return {
          tools: this.tools,
        };
      } catch (error) {
        log(`Error in list tools handler: ${error.message}`, 'ERROR');
        
        // Always return a valid response for Claude MAX
        return {
          tools: this.getFallbackTools(),
        };
      }
    });

    // Call tool handler with enhanced argument processing
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        log(`Executing tool: ${name}`);

        // Enhanced argument processing for Claude MAX compatibility
        const processedArgs = this.processArguments(args);

        const requestBody = {
          tool_name: name,
          input: processedArgs || {},
          session_id: 'claude_max_session',
          metadata: {
            client: 'claude_max',
            timestamp: new Date().toISOString(),
          },
        };

        log(`Tool request: ${JSON.stringify(requestBody, null, 2)}`);

        const response = await this.makeRequest(`${CONFIG.DAMIEN_URL}/mcp/execute_tool`, {
          method: 'POST',
          body: JSON.stringify(requestBody),
        });

        const result = await response.json();
        log(`Tool response received for ${name}`);

        return this.formatResponse(result, name);

      } catch (error) {
        log(`Tool execution error for ${name}: ${error.message}`, 'ERROR');
        return this.formatErrorResponse(error, name);
      }
    });
  }

  processArguments(args) {
    if (!args || typeof args !== 'object') {
      return {};
    }

    const processed = {};

    for (const [key, value] of Object.entries(args)) {
      // Handle JSON string arrays (common Claude MAX issue)
      if (typeof value === 'string' && value.startsWith('[') && value.endsWith(']')) {
        try {
          processed[key] = JSON.parse(value);
        } catch (e) {
          log(`Failed to parse array string for ${key}: ${value}`, 'WARN');
          processed[key] = value;
        }
      } else if (typeof value === 'string' && value.startsWith('{') && value.endsWith('}')) {
        // Handle JSON string objects
        try {
          processed[key] = JSON.parse(value);
        } catch (e) {
          log(`Failed to parse object string for ${key}: ${value}`, 'WARN');
          processed[key] = value;
        }
      } else {
        processed[key] = value;
      }
    }

    return processed;
  }

  formatResponse(result, toolName) {
    let content;

    if (result.is_error) {
      content = `Error executing ${toolName}: ${result.error_message || 'Unknown error occurred'}`;
    } else if (result.output === null || result.output === undefined) {
      content = `Tool ${toolName} executed successfully with no output`;
    } else if (typeof result.output === 'string') {
      content = result.output;
    } else {
      // Pretty print objects for better readability in Claude MAX
      try {
        content = JSON.stringify(result.output, null, 2);
      } catch (e) {
        content = String(result.output);
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: content,
        },
      ],
    };
  }

  formatErrorResponse(error, toolName) {
    let errorMessage = `Failed to execute ${toolName}: `;
    
    if (error.name === 'AbortError') {
      errorMessage += 'Request timed out';
    } else if (error.message.includes('ECONNREFUSED')) {
      errorMessage += 'Backend server is not running';
    } else if (error.message.includes('401') || error.message.includes('403')) {
      errorMessage += 'Authentication failed';
    } else {
      errorMessage += error.message;
    }

    return {
      content: [
        {
          type: 'text',
          text: errorMessage,
        },
      ],
    };
  }

  async run() {
    try {
      log('Starting Enhanced Claude MAX MCP Server');
      log(`Server: ${CONFIG.SERVER_NAME} v${CONFIG.SERVER_VERSION}`);
      log(`Backend: ${CONFIG.DAMIEN_URL}`);

      // Pre-load tools to reduce startup time
      await this.loadTools();

      // Connect to stdio transport
      const transport = new StdioServerTransport();
      await this.server.connect(transport);

      log('✅ Enhanced MCP Server started successfully and ready for Claude MAX');

    } catch (error) {
      log(`Fatal error: ${error.message}`, 'ERROR');
      log(error.stack, 'ERROR');
      process.exit(1);
    }
  }
}

// Graceful shutdown handling
const shutdown = (signal) => {
  log(`Received ${signal}, shutting down gracefully`);
  process.exit(0);
};

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGQUIT', () => shutdown('SIGQUIT'));

// Start the enhanced server
const server = new EnhancedClaudeMaxServer();
server.run();
