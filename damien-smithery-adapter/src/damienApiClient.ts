import fetch from 'node-fetch';
import { CONFIG } from './config.js';

/**
 * Client for interacting with the Damien MCP Server API
 */
export class DamienApiClient {
  private baseUrl: string;
  private apiKey: string;
  
  constructor(baseUrl = CONFIG.DAMIEN_MCP_SERVER_URL, apiKey = CONFIG.DAMIEN_MCP_SERVER_API_KEY) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }
  
  /**
   * Executes a tool on the Damien MCP Server
   */
  async executeTool(toolName: string, params: any, sessionId: string) {
    const url = `${this.baseUrl}/mcp/execute_tool`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      },
      body: JSON.stringify({
        tool_name: toolName,
        input: params,
        session_id: sessionId
      })
    });
    
    if (!response.ok) {
      throw new Error(`Damien MCP Server error: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  /**
   * Get the list of available tools from the Damien MCP Server
   */
  async listTools() {
    const url = `${this.baseUrl}/mcp/list_tools`;
    
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
  
  /**
   * Check server health
   */
  async checkHealth() {
    const url = `${this.baseUrl}/health`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Damien MCP Server health check failed: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  }
}