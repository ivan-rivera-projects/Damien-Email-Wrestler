/**
 * DamienClient - Backend Communication Client for Minimal MCP Server
 * 
 * This client handles all communication with the existing Python FastAPI backend
 * while providing proper error handling, retry logic, and Claude MAX compatibility.
 * 
 * Based on existing DamienApiClient patterns but optimized for the minimal server.
 */

import fetch from 'node-fetch';

export class DamienClient {
  constructor(config = {}) {
    // Configuration with environment variable support and fallbacks
    this.baseUrl = config.baseUrl !== undefined ? config.baseUrl :
                   process.env.DAMIEN_MCP_SERVER_URL || 
                   'http://localhost:8892';
    
    this.apiKey = config.apiKey !== undefined ? config.apiKey :
                  process.env.DAMIEN_MCP_SERVER_API_KEY || 
                  '7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f';
    
    // Request configuration
    this.defaultTimeout = config.timeout || 30000; // 30 seconds
    this.maxRetries = config.maxRetries || 3;
    this.retryDelay = config.retryDelay || 1000; // 1 second
    
    // Validate configuration
    this.validateConfig();
    
    this.log('DamienClient initialized', { baseUrl: this.baseUrl });
  }

  /**
   * Validate client configuration
   */
  validateConfig() {
    if (!this.baseUrl) {
      throw new Error('Backend URL is required');
    }
    
    if (!this.apiKey) {
      throw new Error('API key is required');
    }
    
    if (this.apiKey.length < 32) {
      throw new Error('Valid API key is required (minimum 32 characters)');
    }
    
    // Validate URL format
    try {
      new URL(this.baseUrl);
    } catch (error) {
      throw new Error(`Invalid backend URL format: ${this.baseUrl}`);
    }
  }

  /**
   * Get list of available tools from the backend
   * @returns {Promise<Array>} Array of tool definitions
   */
  async getTools() {
    const endpoint = '/mcp/list_tools';
    
    try {
      this.log('Fetching tools from backend');
      
      const response = await this.makeRequest(endpoint, {
        method: 'GET'
      });
      
      const tools = await response.json();
      
      // Validate response format
      if (!Array.isArray(tools)) {
        throw new Error('Backend returned invalid tools format (expected array)');
      }
      
      this.log(`Successfully fetched ${tools.length} tools`);
      
      // Validate and normalize each tool
      return tools.map(tool => this.validateAndNormalizeTool(tool));
      
    } catch (error) {
      this.logError('Failed to fetch tools', error);
      throw new Error(`Failed to fetch tools: ${error.message}`);
    }
  }

  /**
   * Execute a tool on the backend
   * @param {string} toolName - Name of the tool to execute
   * @param {Object} args - Tool arguments
   * @param {string} sessionId - Session identifier
   * @returns {Promise<Object>} Tool execution result
   */
  async executeTool(toolName, args = {}, sessionId = 'minimal_mcp_session') {
    const endpoint = '/mcp/execute_tool';
    
    try {
      this.log(`Executing tool: ${toolName}`);
      
      const requestBody = {
        tool_name: toolName,
        input: args,
        session_id: sessionId,
        metadata: {
          client: 'minimal_mcp_server',
          timestamp: new Date().toISOString()
        }
      };
      
      const response = await this.makeRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(requestBody)
      });
      
      const result = await response.json();
      
      this.log(`Tool ${toolName} executed successfully`);
      
      return result;
      
    } catch (error) {
      this.logError(`Tool execution failed: ${toolName}`, error);
      throw new Error(`Tool execution failed: ${error.message}`);
    }
  }

  /**
   * Check backend health and connectivity
   * @returns {Promise<Object>} Health status
   */
  async healthCheck() {
    const endpoint = '/health';
    
    try {
      this.log('Performing health check');
      
      const response = await this.makeRequest(endpoint, {
        method: 'GET',
        timeout: 5000 // Shorter timeout for health checks
      });
      
      const health = await response.json();
      
      this.log('Health check successful');
      
      return {
        status: 'healthy',
        backend: health,
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      this.logError('Health check failed', error);
      
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Make HTTP request with retry logic and proper error handling
   * @private
   */
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const timeout = options.timeout || this.defaultTimeout;
    
    const requestOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
        'User-Agent': 'DamienMinimalMCP/1.0.0',
        ...options.headers
      },
      ...options
    };

    // Remove timeout from options to avoid conflicts
    delete requestOptions.timeout;

    let lastError;
    
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        const response = await fetch(url, {
          ...requestOptions,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => 'No error details available');
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        return response;
        
      } catch (error) {
        lastError = error;
        
        if (error.name === 'AbortError') {
          lastError = new Error(`Request timeout after ${timeout}ms`);
        }
        
        this.logError(`Request attempt ${attempt}/${this.maxRetries} failed`, lastError);
        
        // Don't retry on authentication errors or client errors (4xx)
        if (error.message.includes('401') || error.message.includes('403') || 
            error.message.includes('400') || error.message.includes('404')) {
          break;
        }
        
        // Wait before retrying (except on last attempt)
        if (attempt < this.maxRetries) {
          await this.sleep(this.retryDelay * attempt);
        }
      }
    }
    
    throw lastError;
  }

  /**
   * Validate and normalize tool definition
   * @private
   */
  validateAndNormalizeTool(tool) {
    if (!tool || typeof tool !== 'object') {
      throw new Error('Tool must be an object');
    }
    
    const name = tool.name || tool.tool_name;
    if (!name || typeof name !== 'string') {
      throw new Error('Tool must have a valid name');
    }
    
    const description = tool.description || `Tool: ${name}`;
    
    // Ensure input schema is properly formatted for Claude MAX
    let inputSchema = tool.input_schema || tool.inputSchema || tool.schema;
    
    if (!inputSchema || typeof inputSchema !== 'object') {
      inputSchema = {
        type: 'object',
        properties: {},
        required: []
      };
    }
    
    // Fix common schema issues that cause Claude MAX problems
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
        
        // Ensure type is specified
        if (!fixedProp.type) {
          fixedProp.type = 'string';
        }
        
        fixedProperties[propName] = fixedProp;
      }
      
      inputSchema.properties = fixedProperties;
    }
    
    // Ensure required is an array
    if (!Array.isArray(inputSchema.required)) {
      inputSchema.required = [];
    }
    
    return {
      name: name.trim(),
      description: description.trim(),
      inputSchema
    };
  }

  /**
   * Sleep utility for retry delays
   * @private
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Log messages (to stderr to avoid interfering with MCP communication)
   * @private
   */
  log(message, data = null) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] DamienClient: ${message}`;
    
    if (data) {
      process.stderr.write(`${logMessage} ${JSON.stringify(data)}\n`);
    } else {
      process.stderr.write(`${logMessage}\n`);
    }
  }

  /**
   * Log error messages
   * @private
   */
  logError(message, error = null) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] DamienClient ERROR: ${message}`;
    
    process.stderr.write(`${logMessage}\n`);
    
    if (error) {
      process.stderr.write(`[${timestamp}] DamienClient ERROR: ${error.stack || error}\n`);
    }
  }
}

export default DamienClient;
