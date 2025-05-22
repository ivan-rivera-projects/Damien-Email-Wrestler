import express from 'express';
import { CONFIG } from './config.js';
import { DamienApiClient } from './damienApiClient.js';
import { getDamienToolDefinitions } from './toolSchemas.js';

// Define our own ToolDefinition interface
interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: any;
}

interface ToolExecutionRequest {
  tool: string;
  input: Record<string, any>;
  session_id?: string;
}

async function startServer(): Promise<void> {
  const app = express();
  app.use(express.json());

  // Initialize Damien API client
  const damienClient = new DamienApiClient();

  // Check if the Damien MCP Server is up
  try {
    await damienClient.checkHealth();
    console.log('Damien MCP Server health check successful');
  } catch (error) {
    console.error('Damien MCP Server health check failed:', error);
    console.error('Make sure the Damien MCP Server is running at ' + CONFIG.DAMIEN_MCP_SERVER_URL);
  }

  // Get tool definitions from Damien MCP Server
  let tools: ToolDefinition[] = [];
  try {
    tools = await getDamienToolDefinitions();
    console.log(`Found ${tools.length} tools from Damien MCP Server`);
  } catch (error) {
    console.error('Failed to fetch tool definitions:', error);
  }

  // Health check endpoint
  app.get('/health', (req, res) => {
    res.json({
      status: 'ok',
      message: 'Damien Smithery Adapter is running',
      damienMcpServerUrl: CONFIG.DAMIEN_MCP_SERVER_URL
    });
  });

  // List available tools endpoint
  app.get('/tools', (req, res) => {
    res.json({
      tools: tools.map(tool => ({
        name: tool.name,
        description: tool.description
      }))
    });
  });

  // Execute tool endpoint
  app.post('/execute', async (req, res) => {
    try {
      const { tool, input, session_id = 'default_session' } = req.body as ToolExecutionRequest;
      
      if (!tool) {
        return res.status(400).json({
          error: 'Missing required field: tool'
        });
      }
      
      console.log(`Executing tool: ${tool}`);
      console.log(`Input:`, input);
      console.log(`Session ID: ${session_id}`);

      const result = await damienClient.executeTool(tool, input, session_id);
      
      res.json(result);
    } catch (error: any) {
      console.error('Error executing tool:', error);
      res.status(500).json({
        error: 'Error executing tool: ' + (error.message || 'Unknown error')
      });
    }
  });

  // Start server
  const PORT = CONFIG.SERVER_PORT;
  app.listen(PORT, () => {
    console.log(`Damien Smithery Adapter running at http://localhost:${PORT}`);
    console.log(`Connected to Damien MCP Server at ${CONFIG.DAMIEN_MCP_SERVER_URL}`);
  });
}

export { startServer };