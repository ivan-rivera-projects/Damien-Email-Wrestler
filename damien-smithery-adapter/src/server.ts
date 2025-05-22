import { createStatelessServer } from '@smithery/sdk/server/stateless.js';
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { CONFIG } from './config.js';
import { DamienApiClient } from './damienApiClient.js';
import { getDamienToolDefinitions, staticToolDefinitions } from './toolSchemas.js';

/**
 * Creates an MCP server instance with all Damien tools
 */
function createMcpServer(args: { config: any }): any {
  const sessionId = 'default_session'; // We don't have sessionId in this context
  
  // Create MCP server
  const mcpServer = new McpServer({
    name: CONFIG.SERVER_NAME,
    version: CONFIG.SERVER_VERSION
  });
  
  // Initialize Damien API client
  const damienClient = new DamienApiClient();
  
  // Set up tools asynchronously - we'll initialize them when the server starts
  setupDamienTools(mcpServer, damienClient, sessionId);
  
  return mcpServer.server; // Return the underlying server
}

/**
 * Sets up Damien tools on the MCP server
 */
async function setupDamienTools(mcpServer: McpServer, damienClient: DamienApiClient, sessionId: string) {
  try {
    // Check if the Damien MCP Server is up
    try {
      await damienClient.checkHealth();
      console.error('Damien MCP Server health check successful');
    } catch (error) {
      console.error('Damien MCP Server health check failed:', error);
      throw new Error('Damien MCP Server is not available');
    }
    
    // Option 1: Fetch tool definitions dynamically
    const toolDefinitions = await getDamienToolDefinitions();
    
    console.error(`Found ${toolDefinitions.length} tool definitions from Damien MCP Server`);
    
    // Register all tools
    for (const toolDef of toolDefinitions) {
      mcpServer.tool(toolDef.name, async (extra: any) => {
        // The 'extra' object itself should be the ServerRequest, which has 'params'
        const toolParams = (extra as any).params as Record<string, unknown> ?? {};
        console.error("Tool call extra:", JSON.stringify(extra, null, 2)); // Log the extra object
        console.error("Tool call params:", JSON.stringify(toolParams, null, 2)); // Log the extracted params
        // const context = extra.context; // Or however context is structured if needed
        try {
          // Execute the tool on Damien MCP Server
          const damienResult: any = await damienClient.executeTool(toolDef.name, toolParams, sessionId);
          
          if (damienResult.is_error) {
            // Return error if the tool execution failed
            return {
              content: [{type: "text", text: damienResult.error_message || `Unknown error executing tool ${toolDef.name}`}],
              isError: true
            };
          }
          
          // Return successful result
          // Ensure the output is serializable and fits the expected content structure
          let outputContent = "No output";
          if (damienResult.output !== undefined && damienResult.output !== null) {
            try {
              outputContent = JSON.stringify(damienResult.output);
            } catch (e) {
              outputContent = String(damienResult.output);
            }
          }
          return {
            content: [{type: "text", text: outputContent}],
            // structuredContent: damienResult.output, // Use this if the output is already a valid structured content object
          };
        } catch (error: any) {
          console.error(`Error executing tool ${toolDef.name}:`, error);
          return {
            content: [{type: "text", text: `Error executing ${toolDef.name}: ${error.message || 'Unknown error'}`}],
            isError: true
          };
        }
      });
    }
    
    console.error(`Registered ${toolDefinitions.length} Damien tools with MCP server`);
  } catch (error) {
    console.error('Error setting up MCP server tools:', error);
    // Register basic error reporting tool if tool setup fails
    mcpServer.tool("damien_server_status", async (extra: any) => { // Added extra parameter
      const errorMessage = `Failed to initialize Damien tools: ${error instanceof Error ? error.message : 'Unknown error'}`;
      return {
        content: [{type: "text", text: errorMessage}],
        isError: true
      };
    });
  }
  
  return mcpServer.server; // Return the underlying server
}

// Create the stateless server using the MCP server factory
const { app } = createStatelessServer(createMcpServer);

// Start the server
const PORT = CONFIG.SERVER_PORT;
app.listen(PORT, () => {
  console.error(`Damien Smithery MCP server running on port ${PORT}`);
  console.error(`Connecting to Damien MCP Server at ${CONFIG.DAMIEN_MCP_SERVER_URL}`);
});