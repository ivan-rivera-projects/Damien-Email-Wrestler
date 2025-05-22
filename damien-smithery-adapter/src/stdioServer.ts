#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  ListPromptsRequestSchema,
  ListResourcesRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { CONFIG } from './config.js';
import { DamienApiClient } from './damienApiClient.js';
import { getDamienToolDefinitions, staticToolDefinitions } from './toolSchemas.js';

class DamienMcpServer {
  private server: Server;
  private damienClient: DamienApiClient;
  private toolDefinitions: any[] = [];

  constructor() {
    // Initialize Damien API client
    this.damienClient = new DamienApiClient();
    
    // Create MCP server
    this.server = new Server({
      name: CONFIG.SERVER_NAME,
      version: CONFIG.SERVER_VERSION,
    }, {
      capabilities: {
        tools: {},
        prompts: {},
        resources: {},
      },
    });

    this.setupErrorHandling();
    this.setupHandlers();
  }

  private setupErrorHandling(): void {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupHandlers(): void {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      try {
        // Try to get tools from Damien MCP Server, fallback to static definitions
        if (this.toolDefinitions.length === 0) {
          try {
            this.toolDefinitions = await getDamienToolDefinitions();
            console.error(`Loaded ${this.toolDefinitions.length} tools from Damien MCP Server`);
          } catch (error) {
            console.error('Failed to load tools from Damien MCP Server, using static definitions:', error);
            this.toolDefinitions = staticToolDefinitions;
          }
        }

        return {
          tools: this.toolDefinitions.map(tool => ({
            name: tool.name,
            description: tool.description,
            inputSchema: tool.inputSchema,
          })),
        };
      } catch (error) {
        console.error('Error in list tools handler:', error);
        throw new McpError(ErrorCode.InternalError, 'Failed to list tools');
      }
    });

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        console.error(`Executing tool: ${name}`);
        console.error(`Arguments:`, JSON.stringify(args, null, 2));

        // Execute the tool on Damien MCP Server
        const result = await this.damienClient.executeTool(name, args, 'claude_session') as any;
        
        if (result.is_error) {
          throw new McpError(
            ErrorCode.InternalError, 
            result.error_message || `Tool execution failed: ${name}`
          );
        }

        // Format the result for MCP
        let content: string;
        if (result.output !== undefined && result.output !== null) {
          if (typeof result.output === 'string') {
            content = result.output;
          } else {
            content = JSON.stringify(result.output, null, 2);
          }
        } else {
          content = 'Tool executed successfully with no output';
        }

        return {
          content: [
            {
              type: "text",
              text: content,
            },
          ],
        };
      } catch (error) {
        console.error(`Error executing tool ${name}:`, error);
        
        if (error instanceof McpError) {
          throw error;
        }
        
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to execute tool ${name}: ${error instanceof Error ? error.message : 'Unknown error'}`
        );
      }
    });

    // List prompts handler
    this.server.setRequestHandler(ListPromptsRequestSchema, async () => {
      return {
        prompts: [],
      };
    });

    // List resources handler  
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      return {
        resources: [],
      };
    });
  }

  async run(): Promise<void> {
    // Test Damien MCP Server connection
    try {
      await this.damienClient.checkHealth();
      console.error('✅ Connected to Damien MCP Server');
    } catch (error) {
      console.error('⚠️  Warning: Could not connect to Damien MCP Server:', error);
      console.error('Make sure the Damien MCP Server is running at:', CONFIG.DAMIEN_MCP_SERVER_URL);
    }

    // Create stdio transport
    const transport = new StdioServerTransport();
    
    console.error(`🚀 Damien MCP Server starting...`);
    console.error(`📧 Server: ${CONFIG.SERVER_NAME} v${CONFIG.SERVER_VERSION}`);
    console.error(`🔗 Damien MCP Server: ${CONFIG.DAMIEN_MCP_SERVER_URL}`);
    
    await this.server.connect(transport);
    console.error('✅ MCP Server connected and ready');
  }
}

// Start the server
const server = new DamienMcpServer();
server.run().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
