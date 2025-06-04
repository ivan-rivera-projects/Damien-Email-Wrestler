#!/usr/bin/env node
/**
 * Minimal Claude MAX-compatible MCP Server for Damien Email Wrestler
 * 
 * This is a clean, minimal implementation designed to replace the current
 * broken MCP server that crashes Claude Desktop. It starts with no tools
 * and will gradually expand through phases.
 * 
 * Key Features:
 * - Claude MAX protocol compliance
 * - Proper error handling and logging
 * - Graceful shutdown handling
 * - Foundation for phase-based tool expansion
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import DamienClient from './core/damien-client.js';
import { CONFIG, validateConfig, logConfig } from './config/claude-max-config.js';
import phaseManager, { TOOL_PHASES } from './core/tool-phases.js';
import http from 'http';

class MinimalDamienMCP {
  constructor() {
    this.server = null;
    this.transport = null;
    this.damienClient = null;
    this.isShuttingDown = false;
    
    // Cache for tool lists to prevent excessive backend requests
    this.toolsCache = {
      data: null,
      timestamp: 0,
      isRefreshing: false,
      pendingPromise: null
    };
    
    // Request statistics for monitoring
    this.requestStats = {
      listTools: {
        total: 0,
        cacheHits: 0,
        errors: 0,
        lastRequest: 0
      },
      callTool: {
        total: 0,
        byTool: {},
        errors: 0,
        lastRequest: 0
      }
    };
    
    // Validate configuration first
    validateConfig();
    logConfig();
    
    // Initialize backend client
    this.initializeBackendClient();
    
    // Initialize the MCP server
    this.initializeServer();
    
    // Set up signal handlers for graceful shutdown
    this.setupSignalHandlers();
    
    this.log('Minimal Damien MCP Server initialized');
  }

  /**
   * Initialize backend client
   */
  initializeBackendClient() {
    try {
      this.damienClient = new DamienClient({
        baseUrl: CONFIG.BACKEND_URL,
        apiKey: CONFIG.API_KEY,
        timeout: CONFIG.DEFAULT_TIMEOUT,
        maxRetries: CONFIG.MAX_RETRIES,
        retryDelay: CONFIG.RETRY_DELAY
      });
      
      this.log('Backend client initialized successfully');
      
      // Validate that all configured tools exist in the backend
      // This is done asynchronously to avoid blocking startup
      this.validatePhaseTools();
    } catch (error) {
      this.logError('Failed to initialize backend client', error);
      process.exit(1);
    }
  }
  
  /**
   * Validate phase tools against backend
   */
  async validatePhaseTools() {
    try {
      this.log('Validating phase tools against backend...');
      
      const validationResult = await phaseManager.validateToolsExist(this.damienClient);
      
      if (!validationResult.valid) {
        this.log('⚠️ Warning: Some phase tools are not available in the backend');
        
        // Log detailed missing tools information
        for (const [phase, tools] of Object.entries(validationResult.missingTools)) {
          this.log(`Missing tools in Phase ${phase}: ${tools.join(', ')}`);
        }
      }
    } catch (error) {
      this.logError('Error validating phase tools', error);
    }
  }

  /**
   * Initialize the MCP server with proper configuration
   */
  initializeServer() {
    try {
      this.server = new Server(
        {
          name: CONFIG.SERVER_NAME,
          version: CONFIG.SERVER_VERSION,
        },
        {
          capabilities: {
            tools: {}, // Will be populated in later tasks
          },
        }
      );

      // Set up request handlers
      this.setupRequestHandlers();
      
      // Subscribe to phase change events to invalidate cache
      phaseManager.onPhaseChange((previousPhase, newPhase) => {
        this.log(`Phase changed from ${previousPhase} to ${newPhase}, invalidating tools cache`);
        this.invalidateToolsCache();
      });
      
      this.log('MCP Server initialized successfully');
    } catch (error) {
      this.logError('Failed to initialize MCP server', error);
      process.exit(1);
    }
  }

  /**
   * Set up MCP request handlers
   */
  setupRequestHandlers() {
    // List tools handler - returns tools available in the current phase with caching
    this.server.setRequestHandler(ListToolsRequestSchema, async (request) => {
      const requestId = `list_tools_${Date.now()}`;
      const startTime = Date.now();
      
      try {
        this.logRequest(requestId, 'ListTools', 'start');
        this.requestStats.listTools.total++;
        this.requestStats.listTools.lastRequest = startTime;
        
        // Get tools with caching
        const tools = await this.getCachedTools();
        
        // Update cache hit statistics if we used the cache
        if (Date.now() - this.toolsCache.timestamp < CONFIG.TOOL_CACHE_DURATION) {
          this.requestStats.listTools.cacheHits++;
        }
        
        const responseTime = Date.now() - startTime;
        this.logRequest(requestId, 'ListTools', 'success', { 
          toolCount: tools.length, 
          responseTimeMs: responseTime,
          cacheAge: Date.now() - this.toolsCache.timestamp
        });
        
        return {
          tools
        };
      } catch (error) {
        const responseTime = Date.now() - startTime;
        this.requestStats.listTools.errors++;
        
        this.logRequest(requestId, 'ListTools', 'error', { 
          error: error.message,
          responseTimeMs: responseTime
        });
        
        // Even in case of error, return an empty tools array rather than failing
        // This ensures Claude MAX doesn't crash
        return {
          tools: []
        };
      }
    });

    // Call tool handler - executes tools available in the current phase
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, params } = request.params;
      const requestId = `call_tool_${name}_${Date.now()}`;
      const startTime = Date.now();
      let hasError = false;
      
      try {
        this.logRequest(requestId, `CallTool:${name}`, 'start', { params });
        this.requestStats.callTool.total++;
        this.requestStats.callTool.lastRequest = startTime;
        
        // Update per-tool statistics
        if (!this.requestStats.callTool.byTool[name]) {
          this.requestStats.callTool.byTool[name] = { count: 0, errors: 0 };
        }
        this.requestStats.callTool.byTool[name].count++;
        
        // Check if tool is available in current phase
        if (!phaseManager.isToolAvailable(name)) {
          this.logRequest(requestId, `CallTool:${name}`, 'unavailable', { 
            phase: phaseManager.currentPhase,
            phaseName: TOOL_PHASES[phaseManager.currentPhase].name
          });
          
          // Return a helpful message about phase availability
          return {
            content: [
              {
                type: 'text',
                text: `Tool '${name}' is not available in the current implementation phase (${phaseManager.currentPhase}: ${TOOL_PHASES[phaseManager.currentPhase].name}). Please use only the tools provided in the list_tools response.`
              }
            ]
          };
        }
        
        // Validate tool arguments based on schema
        // This will be done by executing the tool and handling any validation errors
        
        // Set up timeout for tool execution
        const timeoutPromise = new Promise((_, reject) => {
          const toolTimeout = setTimeout(() => {
            clearTimeout(toolTimeout);
            reject(new Error(`Tool execution timed out after ${CONFIG.DEFAULT_TIMEOUT}ms`));
          }, CONFIG.DEFAULT_TIMEOUT);
        });
        
        try {
          // Execute the tool with timeout
          const resultPromise = this.damienClient.executeTool(name, params);
          const result = await Promise.race([resultPromise, timeoutPromise]);
          
          // Record performance metrics
          const responseTime = Date.now() - startTime;
          phaseManager.recordToolExecution(name, responseTime, false);
          
          this.logRequest(requestId, `CallTool:${name}`, 'success', { 
            responseTimeMs: responseTime
          });
          
          // Return result as text content with proper formatting for Claude MAX
          // Format based on the result type (object or primitive)
          let formattedResult;
          
          if (typeof result === 'object' && result !== null) {
            // Formatting for object responses
            formattedResult = JSON.stringify(result, null, 2);
          } else {
            // Formatting for primitive responses
            formattedResult = String(result);
          }
          
          return {
            content: [
              {
                type: 'text',
                text: formattedResult
              }
            ]
          };
        } catch (error) {
          hasError = true;
          throw error;
        }
      } catch (error) {
        const responseTime = Date.now() - startTime;
        
        // Update error statistics
        this.requestStats.callTool.errors++;
        if (this.requestStats.callTool.byTool[name]) {
          this.requestStats.callTool.byTool[name].errors++;
        }
        
        // Record performance metrics for the error
        if (hasError) {
          phaseManager.recordToolExecution(name, responseTime, true);
        }
        
        this.logRequest(requestId, `CallTool:${name}`, 'error', { 
          error: error.message,
          responseTimeMs: responseTime
        });
        
        // Return a Claude MAX-compatible error response
        return {
          content: [
            {
              type: 'text',
              text: `Error executing tool: ${error.message}`
            }
          ]
        };
      }
    });
  }

  /**
   * Set up signal handlers for graceful shutdown
   */
  setupSignalHandlers() {
    const signals = ['SIGINT', 'SIGTERM', 'SIGQUIT'];
    
    signals.forEach(signal => {
      process.on(signal, () => {
        this.log(`Received ${signal}, initiating graceful shutdown`);
        this.gracefulShutdown();
      });
    });

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      this.logError('Uncaught exception', error);
      this.gracefulShutdown();
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      this.logError('Unhandled promise rejection', { reason, promise });
      this.gracefulShutdown();
    });
  }

  /**
   * Perform graceful shutdown
   */
  async gracefulShutdown() {
    if (this.isShuttingDown) {
      return;
    }
    
    this.isShuttingDown = true;
    this.log('Starting graceful shutdown...');

    try {
      // Cleanup phase manager
      phaseManager.shutdown();
      
      // Close transport if connected
      if (this.transport) {
        this.log('Closing transport connection');
        await this.transport.close();
      }

      this.log('Graceful shutdown completed');
      process.exit(0);
    } catch (error) {
      this.logError('Error during graceful shutdown', error);
      process.exit(1);
    }
  }

  /**
   * Start the MCP server
   */
  async run() {
    try {
      this.log('Starting Minimal Damien MCP Server...');
      
      // Create and connect stdio transport
      this.transport = new StdioServerTransport();
      await this.server.connect(this.transport);
      
      // Start HTTP server for health checks
      this.startHealthServer();
      
      // Get current phase information
      const currentPhase = phaseManager.currentPhase;
      const phaseInfo = TOOL_PHASES[currentPhase];
      const availableTools = phaseManager.getPhaseTools();
      
      this.log('✅ Minimal Damien MCP Server started successfully');
      this.log(`📊 Current Phase: ${currentPhase} - ${phaseInfo.name}`);
      this.log(`📋 Phase Description: ${phaseInfo.description}`);
      this.log(`🛠️ Available Tools: ${availableTools.length} tools`);
      this.log(`🎯 Performance Targets: ${phaseInfo.performance.latencyTarget}ms latency, max ${phaseInfo.performance.maxResponseTime}ms response time, <${phaseInfo.performance.errorThreshold * 100}% errors`);
      
    } catch (error) {
      this.logError('Failed to start MCP server', error);
      process.exit(1);
    }
  }
  
  /**
   * Start HTTP server for health checks
   */
  startHealthServer() {
    const healthServer = http.createServer(async (req, res) => {
      // Add verbose logging for debugging
      this.log(`HTTP Request: ${req.method} ${req.url}`);
      if (req.headers) {
        this.log(`HTTP Headers: ${JSON.stringify(req.headers)}`);
      }
      
      // Parse the URL
      const url = new URL(req.url, `http://${req.headers.host}`);
      const path = url.pathname;
      
      // Handle health check endpoint
      if (path === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok' }));
        return;
      }
      
      // Handle MCP tool endpoints
      if (path === '/mcp/list_tools') {
        // Verify API key
        const apiKey = req.headers['x-api-key'];
        if (apiKey !== CONFIG.API_KEY) {
          res.writeHead(401, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Invalid API key' }));
          return;
        }
        
        try {
          const tools = await this.getCachedTools();
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ tools }));
        } catch (error) {
          this.logError('Error handling list_tools request', error);
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: error.message }));
        }
        return;
      }
      
      // Handle execute_tool endpoint
      if (path === '/mcp/execute_tool') {
        // Verify API key
        const apiKey = req.headers['x-api-key'];
        if (apiKey !== CONFIG.API_KEY) {
          res.writeHead(401, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Invalid API key' }));
          return;
        }
        
        // Parse request body for tool name and parameters
        let body = '';
        req.on('data', chunk => {
          body += chunk.toString();
        });
        
        req.on('end', async () => {
          try {
            // Parse parameters from body
            const requestData = body ? JSON.parse(body) : {};
            this.log(`Raw request body: ${body}`);
            this.log(`Parsed request data: ${JSON.stringify(requestData)}`);
            
            // Support multiple request formats
            let toolName, toolParams;
            
            // Format 1: { name: "tool_name", params: {...} } (Standard MCP format)
            if (requestData.name) {
              toolName = requestData.name;
              toolParams = requestData.params || {};
            }
            // Format 2: { tool: "tool_name", arguments: {...} } (Alternative format)
            else if (requestData.tool) {
              toolName = requestData.tool;
              toolParams = requestData.arguments || {};
            }
            // Format 3: { tool_name: "tool_name", input: {...} } (Smithery adapter format)
            else if (requestData.tool_name) {
              toolName = requestData.tool_name;
              toolParams = requestData.input || {};
            }
            // Format 4: Direct tool parameters (infer tool name from URL)
            else {
              // Try to get tool name from URL path
              const urlParts = url.pathname.split('/');
              if (urlParts.length >= 3 && urlParts[1] === 'mcp') {
                toolName = urlParts[2];
                toolParams = requestData;
              }
            }
            
            this.log(`Tool execution request: ${toolName} with params: ${JSON.stringify(toolParams)}`);
            
            // Validate tool name
            if (!toolName) {
              res.writeHead(400, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Tool name is required' }));
              return;
            }
            
            // Check if tool is available in current phase
            if (!phaseManager.isToolAvailable(toolName)) {
              res.writeHead(404, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ 
                error: `Tool '${toolName}' not found or not available in phase ${phaseManager.currentPhase}` 
              }));
              return;
            }
            
            // Execute the tool
            const result = await this.damienClient.executeTool(toolName, toolParams || {});
            
            // Return result
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(result));
          } catch (error) {
            this.logError(`Error executing tool`, error);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: error.message }));
          }
        });
        return;
      }
      
      // Handle direct tool execution endpoints (e.g., /mcp/damien_list_emails)
      const toolMatch = path.match(/^\/mcp\/([a-zA-Z0-9_]+)$/);
      if (toolMatch) {
        const toolName = toolMatch[1];
        
        // Verify API key
        const apiKey = req.headers['x-api-key'];
        if (apiKey !== CONFIG.API_KEY) {
          res.writeHead(401, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Invalid API key' }));
          return;
        }
        
        // Check if tool is available in current phase
        if (!phaseManager.isToolAvailable(toolName)) {
          res.writeHead(404, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ 
            error: `Tool '${toolName}' not found or not available in phase ${phaseManager.currentPhase}` 
          }));
          return;
        }
        
        // Parse request body for tool parameters
        let body = '';
        req.on('data', chunk => {
          body += chunk.toString();
        });
        
        req.on('end', async () => {
          try {
            // Parse parameters from body
            const params = body ? JSON.parse(body) : {};
            
            this.log(`Raw request body for ${toolName}: ${body}`);
            this.log(`Direct tool execution: ${toolName} with params: ${JSON.stringify(params)}`);
            
            // Execute the tool
            const result = await this.damienClient.executeTool(toolName, params);
            
            // Return result
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(result));
          } catch (error) {
            this.logError(`Error executing tool ${toolName}`, error);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: error.message }));
          }
        });
        return;
      }
      
      // Default 404 for unknown paths
      res.writeHead(404);
      res.end();
    });
    
    healthServer.listen(CONFIG.SERVER_PORT, () => {
      this.log(`Health check server listening on port ${CONFIG.SERVER_PORT}`);
    });
    
    // Handle errors
    healthServer.on('error', (error) => {
      this.logError('Health server error', error);
    });
  }

  /**
   * Get tools with caching to prevent excessive backend requests
   * Uses a 5-minute cache by default (configurable via CONFIG.TOOL_CACHE_DURATION)
   */
  async getCachedTools() {
    const now = Date.now();
    const cacheAge = now - this.toolsCache.timestamp;
    
    // If cache is valid and not expired, use it
    if (this.toolsCache.data && cacheAge < CONFIG.TOOL_CACHE_DURATION) {
      this.log(`Using cached tools (age: ${cacheAge}ms)`);
      return this.toolsCache.data;
    }
    
    // If a refresh is already in progress, wait for it to complete
    if (this.toolsCache.isRefreshing && this.toolsCache.pendingPromise) {
      this.log('Another refresh in progress, waiting for it to complete');
      return this.toolsCache.pendingPromise;
    }
    
    // Set the flag to indicate a refresh is in progress
    this.toolsCache.isRefreshing = true;
    
    // Create a promise for this refresh operation
    this.toolsCache.pendingPromise = (async () => {
      try {
        this.log('Refreshing tools cache');
        
        // Get all tools from backend
        const allTools = await this.damienClient.getTools();
        
        // Filter tools based on current phase
        const availableToolNames = phaseManager.getPhaseTools();
        const phaseTools = allTools.filter(tool => availableToolNames.includes(tool.name));
        
        // Update cache
        this.toolsCache.data = phaseTools;
        this.toolsCache.timestamp = Date.now();
        
        this.log(`Cache refreshed with ${phaseTools.length} tools for phase ${phaseManager.currentPhase}`);
        
        return phaseTools;
      } catch (error) {
        this.logError('Error refreshing tools cache', error);
        
        // If cache refresh fails but we have existing cached data, use it even if expired
        if (this.toolsCache.data) {
          this.log('Using expired cache due to refresh failure');
          return this.toolsCache.data;
        }
        
        // If no cached data, return empty array to prevent Claude MAX crashes
        return [];
      } finally {
        // Reset the refresh flag
        this.toolsCache.isRefreshing = false;
        this.toolsCache.pendingPromise = null;
      }
    })();
    
    // Return the promise that will resolve with the tools
    return this.toolsCache.pendingPromise;
  }
  
  /**
   * Invalidate the tools cache (called when phase changes)
   */
  invalidateToolsCache() {
    this.log('Invalidating tools cache');
    this.toolsCache.data = null;
    this.toolsCache.timestamp = 0;
  }
  
  /**
   * Get current request statistics for monitoring
   */
  getRequestStats() {
    // Calculate cache hit rate
    const cacheHitRate = this.requestStats.listTools.total > 0
      ? this.requestStats.listTools.cacheHits / this.requestStats.listTools.total
      : 0;
    
    // Calculate error rates
    const listToolsErrorRate = this.requestStats.listTools.total > 0
      ? this.requestStats.listTools.errors / this.requestStats.listTools.total
      : 0;
      
    const callToolErrorRate = this.requestStats.callTool.total > 0
      ? this.requestStats.callTool.errors / this.requestStats.callTool.total
      : 0;
    
    // Calculate tool-specific statistics
    const toolStats = Object.entries(this.requestStats.callTool.byTool).map(([name, stats]) => {
      return {
        name,
        count: stats.count,
        errors: stats.errors,
        errorRate: stats.count > 0 ? stats.errors / stats.count : 0
      };
    });
    
    return {
      timestamp: new Date().toISOString(),
      listTools: {
        total: this.requestStats.listTools.total,
        cacheHits: this.requestStats.listTools.cacheHits,
        cacheHitRate,
        errors: this.requestStats.listTools.errors,
        errorRate: listToolsErrorRate,
        lastRequest: this.requestStats.listTools.lastRequest > 0
          ? new Date(this.requestStats.listTools.lastRequest).toISOString()
          : null
      },
      callTool: {
        total: this.requestStats.callTool.total,
        errors: this.requestStats.callTool.errors,
        errorRate: callToolErrorRate,
        lastRequest: this.requestStats.callTool.lastRequest > 0
          ? new Date(this.requestStats.callTool.lastRequest).toISOString()
          : null,
        tools: toolStats
      },
      cache: {
        age: this.toolsCache.timestamp > 0 ? Date.now() - this.toolsCache.timestamp : null,
        isRefreshing: this.toolsCache.isRefreshing,
        hasData: !!this.toolsCache.data
      },
      phase: {
        current: phaseManager.currentPhase,
        name: TOOL_PHASES[phaseManager.currentPhase].name,
        toolCount: phaseManager.getPhaseTools().length,
        performance: phaseManager.getPerformanceMetrics()
      }
    };
  }

  /**
   * Log messages to stderr (stdout is used for MCP communication)
   */
  log(message) {
    const timestamp = new Date().toISOString();
    process.stderr.write(`[${timestamp}] INFO: ${message}\n`);
  }

  /**
   * Log error messages to stderr
   */
  logError(message, error = null) {
    const timestamp = new Date().toISOString();
    process.stderr.write(`[${timestamp}] ERROR: ${message}\n`);
    if (error) {
      process.stderr.write(`[${timestamp}] ERROR: ${error.stack || error}\n`);
    }
  }
  
  /**
   * Log request details for debugging and monitoring
   */
  logRequest(requestId, requestType, status, details = null) {
    if (CONFIG.LOG_LEVEL === 'DEBUG' || CONFIG.VERBOSE_LOGGING) {
      const timestamp = new Date().toISOString();
      const logMessage = `[${timestamp}] REQUEST ${requestId} ${requestType} ${status}`;
      
      if (details) {
        process.stderr.write(`${logMessage} ${JSON.stringify(details)}\n`);
      } else {
        process.stderr.write(`${logMessage}\n`);
      }
    }
  }
}

// Start the server if this file is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new MinimalDamienMCP();
  server.run().catch((error) => {
    console.error('Fatal error starting server:', error);
    process.exit(1);
  });
}

export default MinimalDamienMCP;