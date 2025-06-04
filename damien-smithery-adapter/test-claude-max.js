#!/usr/bin/env node
/**
 * Diagnostic script to test MCP server compatibility
 */

import { spawn } from 'child_process';
import { resolve } from 'path';

console.log('🔍 Testing Damien MCP Server for Claude MAX compatibility...\n');

// Test 1: Check if backend is running
console.log('1. Checking backend server...');
try {
  const healthResponse = await fetch('http://localhost:8892/health');
  if (healthResponse.ok) {
    console.log('   ✅ Backend server is running');
  } else {
    console.log('   ❌ Backend server returned error:', healthResponse.status);
  }
} catch (error) {
  console.log('   ❌ Cannot connect to backend server:', error.message);
  console.log('   💡 Run ./scripts/start-all.sh first');
  process.exit(1);
}

// Test 2: Check tool listing
console.log('\n2. Checking tool listing...');
try {
  const toolsResponse = await fetch('http://localhost:8892/mcp/list_tools', {
    headers: { 'X-API-Key': '7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f' }
  });
  const tools = await toolsResponse.json();
  console.log(`   ✅ Found ${tools.length} tools`);
  
  // Check tool format
  const firstTool = tools[0];
  if (firstTool.input_schema) {
    console.log('   ⚠️  Tools use "input_schema" (snake_case) - needs conversion for MCP');
  }
} catch (error) {
  console.log('   ❌ Failed to list tools:', error.message);
}

// Test 3: Test MCP server startup
console.log('\n3. Testing MCP server startup...');
const serverPath = resolve('claude-max-server.js');
const mcpServer = spawn('node', [serverPath], {
  stdio: ['pipe', 'pipe', 'pipe'],
  env: {
    ...process.env,
    DAMIEN_MCP_SERVER_URL: 'http://localhost:8892',
    DAMIEN_MCP_SERVER_API_KEY: '7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f'
  }
});

// Send list tools request
mcpServer.stdin.write(JSON.stringify({
  jsonrpc: '2.0',
  method: 'tools/list',
  params: {},
  id: 1
}) + '\n');

// Wait for response
let responseBuffer = '';
mcpServer.stdout.on('data', (data) => {
  responseBuffer += data.toString();
  try {
    const lines = responseBuffer.split('\n');
    for (const line of lines) {
      if (line.trim()) {
        const response = JSON.parse(line);
        if (response.result && response.result.tools) {
          console.log(`   ✅ MCP server responded with ${response.result.tools.length} tools`);
          console.log('   ✅ First tool:', response.result.tools[0].name);
          mcpServer.kill();
          process.exit(0);
        }
      }
    }
  } catch (e) {
    // Buffer incomplete, wait for more data
  }
});

mcpServer.stderr.on('data', (data) => {
  const output = data.toString();
  if (!output.includes('✅')) {
    console.error('   Server error:', output);
  }
});

setTimeout(() => {
  console.log('   ❌ MCP server did not respond in time');
  mcpServer.kill();
  process.exit(1);
}, 5000);
