#!/usr/bin/env node
/**
 * Debug MCP Server for Damien - Logs everything to understand Claude MAX issues
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LOG_FILE = path.join(__dirname, '../logs/claude-max-debug.log');

const DAMIEN_URL = process.env.DAMIEN_MCP_SERVER_URL || 'http://localhost:8892';
const API_KEY = process.env.DAMIEN_MCP_SERVER_API_KEY || '7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f';

// Debug logging to file
const debugLog = (msg, data = null) => {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] ${msg}${data ? '\n' + JSON.stringify(data, null, 2) : ''}\n`;
  fs.appendFileSync(LOG_FILE, logEntry);
};

class DebugMcpServer {
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

    debugLog('Server instance created');
    this.setupHandlers();
  }

  async loadTools() {
    debugLog('Loading tools from Damien server...');
    try {
      const response = await fetch(`${DAMIEN_URL}/mcp/list_tools`, {
        headers: { 'X-API-Key': API_KEY },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const tools = await response.json();
      debugLog(`Received ${tools.length} tools from server`);
      
      // Focus on the email listing tool for debugging
      this.tools = tools
        .filter(tool => ['damien_list_emails', 'damien_get_email_details'].includes(tool.name))
        .map(tool => ({
          name: tool.name,
          description: tool.description || 'No description',
          inputSchema: tool.input_schema || tool.inputSchema || {
            type: 'object',
            properties: {},
          },
        }));
      
      debugLog(`Filtered to ${this.tools.length} essential tools`, this.tools);
    } catch (error) {
      debugLog('Error loading tools', { error: error.message });
      // Minimal fallback
      this.tools = [{
        name: 'damien_list_emails',
        description: 'List recent emails',
        inputSchema: {
          type: 'object',
          properties: {
            max_results: { type: 'integer', default: 5 }
          },
        },
      }];
    }
  }

  setupHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async (request) => {
      debugLog('LIST TOOLS REQUEST', request);
      
      try {
        if (this.tools.length === 0) {
          await this.loadTools();
        }
        
        const response = { tools: this.tools };
        debugLog('LIST TOOLS RESPONSE', response);
        return response;
      } catch (error) {
        debugLog('LIST TOOLS ERROR', { error: error.message, stack: error.stack });
        return { tools: [] };
      }
    });

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      debugLog('CALL TOOL REQUEST', request);
      
      const { name, arguments: args } = request.params;
      
      try {
        debugLog(`Calling Damien server for tool: ${name}`, args);
        
        const response = await fetch(`${DAMIEN_URL}/mcp/execute_tool`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
          },
          body: JSON.stringify({
            tool_name: name,
            input: args || {},
            session_id: 'claude_max_debug',
          }),
        });
        
        const responseText = await response.text();
        debugLog('Raw server response', { status: response.status, body: responseText });
        
        if (!response.ok) {
          throw new Error(`Server error ${response.status}: ${responseText}`);
        }
        
        const result = JSON.parse(responseText);
        debugLog('Parsed server response', result);
        
        // Build response
        let content = 'No output';
        if (result.is_error) {
          content = `Error: ${result.error_message || 'Unknown error'}`;
        } else if (result.output) {
          content = typeof result.output === 'string' ? result.output : JSON.stringify(result.output, null, 2);
        }
        
        const toolResponse = {
          content: [{
            type: 'text',
            text: content,
          }],
        };
        
        debugLog('CALL TOOL RESPONSE', toolResponse);
        return toolResponse;
        
      } catch (error) {
        debugLog('CALL TOOL ERROR', { 
          error: error.message, 
          stack: error.stack,
          name: name,
          args: args 
        });
        
        return {
          content: [{
            type: 'text',
            text: `Error: ${error.message}`,
          }],
        };
      }
    });
  }

  async run() {
    debugLog('Starting server...');
    
    try {
      await this.loadTools();
      const transport = new StdioServerTransport();
      await this.server.connect(transport);
      debugLog('Server connected successfully');
    } catch (error) {
      debugLog('FATAL ERROR', { error: error.message, stack: error.stack });
      process.exit(1);
    }
  }
}

// Clear log file on start
fs.writeFileSync(LOG_FILE, '');
debugLog('=== DEBUG MCP SERVER STARTING ===');

const server = new DebugMcpServer();
server.run();
