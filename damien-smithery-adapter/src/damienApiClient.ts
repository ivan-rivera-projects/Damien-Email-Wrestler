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
    
    try {
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
        }),
        // Add timeout for Claude MAX compatibility
        signal: AbortSignal.timeout(30000) // 30 second timeout
      });
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'No error details');
        throw new Error(`Damien MCP Server error: ${response.status} ${response.statusText} - ${errorText}`);
      }
      
      return await response.json();
    } catch (error: any) {
      // Handle timeout and other network errors gracefully
      if (error?.name === 'AbortError') {
        throw new Error(`Tool execution timeout for ${toolName}`);
      }
      throw error;
    }
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