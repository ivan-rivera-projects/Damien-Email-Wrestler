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
      console.error('Received SIGINT, shutting down gracefully...');
      await this.server.close();
      process.exit(0);
    });

    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error);
      // Don't exit immediately for Claude MAX compatibility
      setTimeout(() => process.exit(1), 1000);
    });

    process.on('unhandledRejection', (reason) => {
      console.error('Unhandled Rejection:', reason);
      // Don't exit immediately for Claude MAX compatibility
      setTimeout(() => process.exit(1), 1000);
    });
  }

  private setupHandlers(): void {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      try {
        // Try to get tools from Damien MCP Server with a timeout for Claude MAX
        if (this.toolDefinitions.length === 0) {
          try {
            // Add timeout to prevent hanging
            const toolsPromise = getDamienToolDefinitions();
            const timeoutPromise = new Promise((_, reject) => 
              setTimeout(() => reject(new Error('Tool loading timeout')), 5000)
            );
            
            this.toolDefinitions = await Promise.race([toolsPromise, timeoutPromise]) as any[];
            console.error(`Loaded ${this.toolDefinitions.length} tools from Damien MCP Server`);
          } catch (error) {
            console.error('Failed to load tools from Damien MCP Server, using static definitions:', error);
            this.toolDefinitions = staticToolDefinitions;
          }
        }

        // Ensure we always return valid tool definitions
        const tools = this.toolDefinitions.map(tool => ({
          name: tool.name,
          description: tool.description || 'No description available',
          inputSchema: tool.inputSchema || { type: 'object', properties: {} },
        }));

        return { tools };
      } catch (error) {
        console.error('Error in list tools handler:', error);
        // Return static tools as fallback to prevent Claude MAX from erroring
        return {
          tools: staticToolDefinitions.map(tool => ({
            name: tool.name,
            description: tool.description || 'No description available',
            inputSchema: tool.inputSchema || { type: 'object', properties: {} },
          })),
        };
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
          // Return error in MCP format that Claude MAX expects
          return {
            content: [
              {
                type: "text",
                text: `Error: ${result.error_message || `Tool execution failed: ${name}`}`,
              },
            ],
            isError: true,
          };
        }

        // Format the result for MCP - handle Claude MAX's stricter format requirements
        let content: string;
        if (result.output !== undefined && result.output !== null) {
          if (typeof result.output === 'string') {
            content = result.output;
          } else {
            // Claude MAX may have issues with deeply nested objects, so we stringify with formatting
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
          isError: false,
        };
      } catch (error) {
        console.error(`Error executing tool ${name}:`, error);
        
        // Return error in a format Claude MAX can handle
        return {
          content: [
            {
              type: "text", 
              text: `Failed to execute tool ${name}: ${error instanceof Error ? error.message : 'Unknown error'}`,
            },
          ],
          isError: true,
        };
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
