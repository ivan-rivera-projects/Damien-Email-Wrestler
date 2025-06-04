#!/usr/bin/env node

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { spawn } from 'child_process';

async function testMCPServer() {
  console.log('🧪 Testing Damien MCP Server...\n');
  
  const serverPath = '/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter/claude-simple-wrapper.sh';
  
  const transport = new StdioClientTransport({
    command: 'bash',
    args: [serverPath],
  });
  
  const client = new Client({
    name: 'test-client',
    version: '1.0.0',
  }, {
    capabilities: {}
  });
  
  try {
    await client.connect(transport);
    console.log('✅ Connected to MCP server\n');
    
    // List available tools
    console.log('📋 Listing available tools...');
    const toolsResponse = await client.listTools();
    console.log(`Found ${toolsResponse.tools.length} tools:\n`);
    
    toolsResponse.tools.slice(0, 5).forEach(tool => {
      console.log(`  • ${tool.name}: ${tool.description}`);
    });
    
    if (toolsResponse.tools.length > 5) {
      console.log(`  ... and ${toolsResponse.tools.length - 5} more tools\n`);
    }
    
    console.log('✅ MCP server is working correctly!');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await transport.close();
  }
}

testMCPServer().catch(console.error);
