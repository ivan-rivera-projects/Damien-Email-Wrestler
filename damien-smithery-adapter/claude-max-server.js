#!/usr/bin/env node
/**
 * Claude MAX Compatible MCP Server for Damien Email Wrestler
 * This is a complete rewrite optimized for Claude MAX's stricter requirements
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';

const DAMIEN_URL = process.env.DAMIEN_MCP_SERVER_URL || 'http://localhost:8892';
const API_KEY = process.env.DAMIEN_MCP_SERVER_API_KEY || '7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f';

class ClaudeMaxDamienServer {
  constructor() {
    this.tools = [];
    this.server = new Server(
      {
        name: 'damien-email-wrestler',
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
      const response = await fetch(`${DAMIEN_URL}/mcp/list_tools`, {
        headers: { 'X-API-Key': API_KEY },
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const tools = await response.json();
      this.tools = tools.map(tool => ({
        name: tool.name,
        description: tool.description || 'No description',
        inputSchema: tool.input_schema || tool.inputSchema || { type: 'object', properties: {} },
      }));
      
      console.error(`Loaded ${this.tools.length} tools from Damien MCP Server`);
    } catch (error) {
      console.error('Error loading tools:', error.message);
      // Use minimal fallback tools for Claude MAX
      this.tools = [
        {
          name: 'damien_list_emails',
          description: 'List emails from Gmail',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'Gmail search query' },
              max_results: { type: 'integer', default: 10 },
            },
          },
        },
      ];
    }
  }

  setupHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      if (this.tools.length === 0) {
        await this.loadTools();
      }
      
      return { tools: this.tools };
    });

    // Call tool handler  
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        // Call Damien MCP Server
        const response = await fetch(`${DAMIEN_URL}/mcp/execute_tool`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
          },
          body: JSON.stringify({
            tool_name: name,
            input: args || {},
            session_id: 'claude_max_session',
          }),
        });

        if (!response.ok) {
          const error = await response.text();
          throw new Error(`Server error: ${response.status} - ${error}`);
        }

        const result = await response.json();
        
        // Handle errors from Damien server
        if (result.is_error) {
          return {
            content: [
              {
                type: 'text',
                text: `Error: ${result.error_message || 'Unknown error'}`,
              },
            ],
          };
        }

        // Format successful response
        const output = typeof result.output === 'string' 
          ? result.output 
          : JSON.stringify(result.output, null, 2);
          
        return {
          content: [
            {
              type: 'text', 
              text: output,
            },
          ],
        };
      } catch (error) {
        console.error(`Tool execution error:`, error);
        return {
          content: [
            {
              type: 'text',
              text: `Failed to execute ${name}: ${error.message}`,
            },
          ],
        };
      }
    });
  }

  async run() {
    // Test connection
    try {
      const health = await fetch(`${DAMIEN_URL}/health`);
      if (health.ok) {
        console.error('✅ Connected to Damien MCP Server');
      } else {
        console.error('⚠️  Damien MCP Server health check failed');
      }
    } catch (error) {
      console.error('⚠️  Cannot connect to Damien MCP Server:', error.message);
    }

    // Load tools before starting
    await this.loadTools();

    // Start server
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('✅ Claude MAX compatible server ready');
  }
}

// Start server
const server = new ClaudeMaxDamienServer();
server.run().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
