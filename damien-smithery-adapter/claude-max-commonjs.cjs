#!/usr/bin/env node
/**
 * CommonJS version of Claude MAX Compatible MCP Server for Damien Email Wrestler
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

// Use dynamic import for node-fetch
let fetch;
(async () => {
  const module = await import('node-fetch');
  fetch = module.default;
  
  // Start the server after fetch is loaded
  const server = new ClaudeMaxCompatibleServer();
  server.run();
})();

const DAMIEN_URL = process.env.DAMIEN_MCP_SERVER_URL || 'http://localhost:8892';
const API_KEY = process.env.DAMIEN_MCP_SERVER_API_KEY || '7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f';

// Simple logging that doesn't interfere with stdio
const log = (msg) => {
  process.stderr.write(`[${new Date().toISOString()}] ${msg}\n`);
};

class ClaudeMaxCompatibleServer {
  constructor() {
    this.tools = [];
    this.server = new Server(
      {
        name: 'damien_email_wrestler',
        version: '2.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  async loadTools() {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${DAMIEN_URL}/mcp/list_tools`, {
        headers: { 'X-API-Key': API_KEY },
        signal: controller.signal,
      });
      
      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const tools = await response.json();
      
      // Convert and validate tools for Claude MAX
      this.tools = tools.map(tool => {
        const name = tool.name || 'unnamed_tool';
        
        let processedSchema = tool.input_schema || tool.inputSchema || {
          type: 'object',
          properties: {},
        };
        
        // Convert array properties that might be strings to proper arrays
        if (processedSchema.properties) {
          for (const propName in processedSchema.properties) {
            const prop = processedSchema.properties[propName];
            if (prop.type === 'array' && prop.items && typeof prop.items === 'string') {
              prop.items = { type: prop.items };
            }
          }
        }
        
        return {
          name: name,
          description: tool.description || `No description available for ${name}`,
          inputSchema: processedSchema,
        };
      });
      
      log(`Loaded ${this.tools.length} tools`);
    } catch (error) {
      log(`Error loading tools: ${error.message}`);
      // Provide essential fallback tools
      this.tools = [
        {
          name: 'damien_list_emails',
          description: 'List emails from your Gmail account',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Gmail search query (optional)',
              },
              max_results: {
                type: 'integer',
                description: 'Maximum number of emails to return',
                default: 10,
              },
            },
          },
        },
      ];
    }
  }

  setupHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      try {
        if (this.tools.length === 0) {
          await this.loadTools();
        }
        
        return {
          tools: this.tools,
        };
      } catch (error) {
        log(`Error in list tools: ${error.message}`);
        return {
          tools: [],
        };
      }
    });

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        log(`Executing tool: ${name}`);
        
        const fixedArgs = {};
        
        if (args) {
          for (const key in args) {
            if (typeof args[key] === 'string' && 
                (args[key].startsWith('[') && args[key].endsWith(']'))) {
              try {
                fixedArgs[key] = JSON.parse(args[key]);
              } catch (e) {
                fixedArgs[key] = args[key];
              }
            } else {
              fixedArgs[key] = args[key];
            }
          }
        }
        
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);
        
        const response = await fetch(`${DAMIEN_URL}/mcp/execute_tool`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
          },
          body: JSON.stringify({
            tool_name: name,
            input: fixedArgs || {},
            session_id: 'claude_max_session',
          }),
          signal: controller.signal,
        });
        
        clearTimeout(timeout);
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => 'Unknown error');
          throw new Error(`Server returned ${response.status}: ${errorText}`);
        }

        const result = await response.json();
        
        let content;
        if (result.is_error) {
          content = `Error: ${result.error_message || 'Tool execution failed'}`;
        } else if (result.output === null || result.output === undefined) {
          content = 'Tool executed successfully with no output';
        } else if (typeof result.output === 'string') {
          content = result.output;
        } else {
          content = JSON.stringify(result.output, null, 2);
        }
        
        return {
          content: [
            {
              type: 'text',
              text: content,
            },
          ],
        };
      } catch (error) {
        log(`Tool execution error: ${error.message}`);
        
        let errorMessage = `Failed to execute ${name}: `;
        if (error.name === 'AbortError') {
          errorMessage += 'Request timed out';
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
    });
  }

  async run() {
    try {
      await this.loadTools();
      
      const transport = new StdioServerTransport();
      await this.server.connect(transport);
      
      log('Server started successfully');
    } catch (error) {
      log(`Fatal error: ${error.message}`);
      process.exit(1);
    }
  }
}

// Handle process signals gracefully
process.on('SIGINT', () => {
  log('Received SIGINT, shutting down');
  process.exit(0);
});

process.on('SIGTERM', () => {
  log('Received SIGTERM, shutting down');
  process.exit(0);
});
