#!/usr/bin/env node

// Simple CommonJS-based stdio server for Claude integration
const { createStdioServer } = require('@smithery/sdk/server/stdio');
const fetch = require('node-fetch');

// Configuration
const DAMIEN_MCP_SERVER_URL = process.env.DAMIEN_MCP_SERVER_URL || 'http://localhost:8892';
const DAMIEN_MCP_SERVER_API_KEY = process.env.DAMIEN_MCP_SERVER_API_KEY || '';
const SERVER_NAME = process.env.SERVER_NAME || 'Damien Email Wrestler';
const SERVER_VERSION = process.env.SERVER_VERSION || '1.0.0';

// Simple Damien API Client
class DamienApiClient {
  constructor() {
    this.baseUrl = DAMIEN_MCP_SERVER_URL;
    this.apiKey = DAMIEN_MCP_SERVER_API_KEY;
  }
  
  async executeTool(toolName, params, sessionId) {
    const url = `${this.baseUrl}/mcp/execute_tool`;
    console.error(`Executing tool: ${toolName}`);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      },
      body: JSON.stringify({
        tool_name: toolName,
        input: params,
        session_id: sessionId || 'claude_session'
      })
    });
    
    if (!response.ok) {
      throw new Error(`Damien MCP Server error: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  async listTools() {
    const url = `${this.baseUrl}/mcp/list_tools`;
    console.error(`Listing tools from: ${this.baseUrl}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'X-API-Key': this.apiKey
      }
    });
    
    if (!response.ok) {
      throw new Error(`Damien MCP Server error: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  }
}

// Static definitions in case server is unavailable
const staticTools = [
  {
    name: "damien_list_emails",
    description: "Lists email messages based on a query, with support for pagination.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Optional Gmail search query string to filter emails."
        },
        max_results: {
          type: "integer",
          default: 10,
          description: "Maximum number of email summaries to return."
        }
      }
    }
  }
];

// Create the stdio server
createStdioServer(async ({ sessionId }) => {
  console.error(`Starting Damien MCP STDIO Server - session: ${sessionId}`);
  console.error(`Server URL: ${DAMIEN_MCP_SERVER_URL}`);
  
  const damienClient = new DamienApiClient();
  let toolDefinitions = [];
  
  try {
    console.error('Attempting to fetch tools from Damien MCP Server...');
    const damienTools = await damienClient.listTools();
    
    toolDefinitions = damienTools.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.input_schema || {}
    }));
    
    console.error(`Successfully loaded ${toolDefinitions.length} tools from Damien MCP Server`);
  } catch (error) {
    console.error('Failed to load tools from Damien MCP Server, using static definitions:', error);
    toolDefinitions = staticTools;
  }
  
  return {
    name: SERVER_NAME,
    version: SERVER_VERSION,
    tools: toolDefinitions.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputSchema,
      async handler(params) {
        try {
          console.error(`Executing tool ${tool.name} with params:`, params);
          const result = await damienClient.executeTool(tool.name, params, sessionId);
          
          if (result.is_error) {
            console.error(`Error from Damien: ${result.error_message}`);
            return {
              error: result.error_message || `Tool execution failed: ${tool.name}`
            };
          }
          
          console.error(`Tool execution successful`);
          return {
            result: result.output
          };
        } catch (error) {
          console.error(`Error executing tool ${tool.name}:`, error);
          return {
            error: error.message || 'Unknown error'
          };
        }
      }
    }))
  };
}).catch(error => {
  console.error('Fatal error in Damien stdio server:', error);
  process.exit(1);
});
