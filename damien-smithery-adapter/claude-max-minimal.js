#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';

const DAMIEN_URL = process.env.DAMIEN_MCP_SERVER_URL || 'http://localhost:8892';
const API_KEY = process.env.DAMIEN_MCP_SERVER_API_KEY || '7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f';

class DamienMCPServer {
  constructor() {
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

  setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      try {
        const response = await fetch(`${DAMIEN_URL}/mcp/list_tools`, {
          headers: { 'X-API-Key': API_KEY },
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        
        const tools = await response.json();
        
        return {
          tools: tools.map(tool => ({
            name: tool.name,
            description: tool.description || 'No description',
            inputSchema: tool.input_schema || tool.inputSchema || {
              type: 'object',
              properties: {},
            },
          })),
        };
      } catch (error) {
        console.error('Error listing tools:', error);
        return { tools: [] };
      }
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
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
          const errorText = await response.text();
          throw new Error(`Server error: ${errorText}`);
        }

        const result = await response.json();
        
        return {
          content: [
            {
              type: 'text',
              text: result.is_error 
                ? `Error: ${result.error_message || 'Unknown error'}`
                : (typeof result.output === 'string' ? result.output : JSON.stringify(result.output, null, 2)),
            },
          ],
        };
      } catch (error) {
        console.error('Error executing tool:', error);
        return {
          content: [
            {
              type: 'text',
              text: `Error executing ${name}: ${error.message}`,
            },
          ],
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Damien MCP Server connected successfully');
  }
}

const server = new DamienMCPServer();
server.run().catch(console.error);
