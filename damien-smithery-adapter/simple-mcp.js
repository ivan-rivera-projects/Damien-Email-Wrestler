#!/usr/bin/env node
/**
 * Simplified MCP Server for Claude MAX - Damien Email Wrestler
 * Minimal implementation focused on reliability
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

class SimpleDamienMCP {
  constructor() {
    this.server = new Server(
      {
        name: 'damien-email-wrestler',
        version: '3.0.0',
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
    // List tools - simplified to just email operations
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'damien_list_emails',
            description: 'List recent emails from your Gmail account',
            inputSchema: {
              type: 'object',
              properties: {
                max_results: {
                  type: 'integer',
                  description: 'Number of emails to return (default: 10)',
                  default: 10,
                },
                query: {
                  type: 'string',
                  description: 'Gmail search query (optional)',
                },
              },
            },
          },
          {
            name: 'damien_get_email_details',
            description: 'Get full details of a specific email',
            inputSchema: {
              type: 'object',
              properties: {
                message_id: {
                  type: 'string',
                  description: 'Gmail message ID',
                },
              },
              required: ['message_id'],
            },
          },
        ],
      };
    });

    // Call tool handler - simplified error handling
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        // Special handling for list_emails to include headers
        if (name === 'damien_list_emails' && !args.include_headers) {
          args.include_headers = ['From', 'Subject', 'Date'];
        }
        
        const response = await fetch(`${DAMIEN_URL}/mcp/execute_tool`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
          },
          body: JSON.stringify({
            tool_name: name,
            input: args || {},
            session_id: 'claude_max',
          }),
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error(`Server error: ${response.status} ${text}`);
        }

        const result = await response.json();
        
        // Handle errors from the server
        if (result.is_error) {
          return {
            content: [
              {
                type: 'text',
                text: `Error: ${result.error_message || 'Unknown error occurred'}`,
              },
            ],
          };
        }

        // Format the output based on the tool
        let outputText = '';
        
        if (name === 'damien_list_emails' && result.output?.email_summaries) {
          const emails = result.output.email_summaries;
          outputText = `Found ${emails.length} emails:\n\n`;
          
          emails.forEach((email, index) => {
            outputText += `${index + 1}. ${email.Subject || 'No subject'}\n`;
            outputText += `   From: ${email.From || 'Unknown'}\n`;
            outputText += `   Date: ${email.Date || 'Unknown'}\n`;
            outputText += `   ID: ${email.id}\n\n`;
          });
        } else if (result.output) {
          // Generic output formatting
          outputText = typeof result.output === 'string' 
            ? result.output 
            : JSON.stringify(result.output, null, 2);
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
        // Simple error response
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
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

// Start the server
const server = new SimpleDamienMCP();
server.run().catch(() => process.exit(1));
