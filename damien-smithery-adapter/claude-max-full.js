#!/usr/bin/env node
/**
 * Claude MAX Compatible MCP Server - Full Version with All 40 Tools
 * Includes all Damien Email Wrestler functionality
 */

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
    this.tools = [];
    this.server = new Server(
      {
        name: 'damien-email-wrestler',
        version: '4.0.0',
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
        timeout: 5000,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const tools = await response.json();
      
      // Convert all 40 tools with proper formatting for Claude MAX
      this.tools = tools.map(tool => ({
        name: tool.name || 'unnamed_tool',
        description: tool.description || 'No description available',
        inputSchema: tool.input_schema || tool.inputSchema || {
          type: 'object',
          properties: {},
          additionalProperties: false,
        },
      }));
      
      // Ensure all tools have valid schemas
      this.tools.forEach(tool => {
        if (!tool.inputSchema.type) {
          tool.inputSchema.type = 'object';
        }
        if (!tool.inputSchema.properties) {
          tool.inputSchema.properties = {};
        }
      });
      
      console.error(`✅ Loaded all ${this.tools.length} tools from Damien MCP Server`);
    } catch (error) {
      console.error('⚠️  Error loading tools:', error.message);
      throw error; // Re-throw to handle in the handler
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
        console.error('Error listing tools:', error);
        // Return empty array rather than throwing
        return {
          tools: [],
        };
      }
    });

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        // Special handling for list_emails to include headers by default
        if (name === 'damien_list_emails' && !args.include_headers) {
          args.include_headers = ['From', 'Subject', 'Date'];
        }
        
        // Add timeout protection
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
            input: args || {},
            session_id: 'claude_max_session',
          }),
          signal: controller.signal,
        });
        
        clearTimeout(timeout);
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => 'Unknown error');
          throw new Error(`Server ${response.status}: ${errorText}`);
        }

        const result = await response.json();
        
        // Handle server errors
        if (result.is_error) {
          return {
            content: [
              {
                type: 'text',
                text: `Error: ${result.error_message || 'Tool execution failed'}`,
              },
            ],
          };
        }

        // Format output based on tool type for better readability
        let outputText;
        
        if (name === 'damien_list_emails' && result.output?.email_summaries) {
          // Special formatting for email lists
          const emails = result.output.email_summaries;
          outputText = `Found ${emails.length} emails:\n\n`;
          
          emails.forEach((email, index) => {
            outputText += `${index + 1}. ${email.Subject || email.snippet || 'No subject'}\n`;
            outputText += `   From: ${email.From || 'Unknown sender'}\n`;
            outputText += `   Date: ${email.Date || 'No date'}\n`;
            outputText += `   ID: ${email.id}\n`;
            if (email.snippet) {
              outputText += `   Preview: ${email.snippet.substring(0, 100)}...\n`;
            }
            outputText += '\n';
          });
          
          if (result.output.next_page_token) {
            outputText += `\nMore emails available (next_page_token: ${result.output.next_page_token})`;
          }
        } else if (typeof result.output === 'string') {
          outputText = result.output;
        } else if (result.output) {
          // Pretty print other outputs
          outputText = JSON.stringify(result.output, null, 2);
        } else {
          outputText = 'Operation completed successfully';
        }
        
        return {
          content: [
            {
              type: 'text',
              text: outputText,
            },
          ],
        };
      } catch (error) {
        let errorMessage;
        if (error.name === 'AbortError') {
          errorMessage = `Tool execution timeout for ${name}`;
        } else {
          errorMessage = `Failed to execute ${name}: ${error.message}`;
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
      // Pre-load tools to reduce startup time
      await this.loadTools();
      
      // Connect to stdio transport
      const transport = new StdioServerTransport();
      await this.server.connect(transport);
      
      console.error('✅ Claude MAX compatible server ready with all tools');
    } catch (error) {
      console.error('Fatal error:', error.message);
      process.exit(1);
    }
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  process.exit(0);
});

process.on('SIGTERM', () => {
  process.exit(0);
});

// Start the server
const server = new DamienMCPServer();
server.run();