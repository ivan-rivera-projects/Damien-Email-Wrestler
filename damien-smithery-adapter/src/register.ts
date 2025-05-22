import { SmitheryRegistry } from "@smithery/registry";
// Remove the problematic import
// import * as smitherySDK from "@smithery/sdk";
import { CONFIG } from './config.js';
import { staticToolDefinitions } from './toolSchemas.js';

async function registerServer() {
  if (!CONFIG.SMITHERY_BEARER_AUTH) {
    console.error('Error: SMITHERY_BEARER_AUTH environment variable is required for registration');
    process.exit(1);
  }

  try {
    // Initialize Smithery Registry client
    const smitheryRegistry = new SmitheryRegistry({
      bearerAuth: CONFIG.SMITHERY_BEARER_AUTH
    });
    
    // Server connection information - use your actual server URL in production
    const serverUrl = `http://localhost:${CONFIG.SERVER_PORT}`;
    
    // Create tools array from tool definitions
    const tools = staticToolDefinitions.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputSchema
    }));
    
    // Prepare server definition - check the current version of Smithery Registry for exact parameter names
    const serverDefinition = {
      name: "damien-email-manager", // Unique server name
      displayName: CONFIG.SERVER_NAME,
      description: "Gmail email management via Damien CLI",
      connections: [
        {
          type: "http",
          url: serverUrl
        }
      ],
      tools: tools
    };
    
    console.log('Server definition prepared:', serverDefinition);
    console.log('');
    console.log('❌ Server registration cannot be completed automatically with the current version');
    console.log('   of the Smithery Registry SDK (0.3.7).');
    console.log('');
    console.log('Please register your server manually using one of these methods:');
    console.log('');
    console.log('1. Use the Smithery CLI tool:');
    console.log('   npx @smithery/cli register --manual');
    console.log('');
    console.log('2. Visit the Smithery Registry website:');
    console.log('   https://smithery.ai/');
    console.log('');
    console.log('3. Update to a newer version of @smithery/registry or @smithery/sdk');
    console.log('   that supports server registration');
    console.log('');
    console.log('Your server will still run locally at:');
    console.log(`http://localhost:${CONFIG.SERVER_PORT}`);
    
  } catch (error) {
    console.error('Error preparing server for registration:', error);
  }
}

// Run the registration
registerServer().catch(console.error);