#!/usr/bin/env node
/**
 * Basic test for the Minimal Damien MCP Server
 * This test verifies that the server can be imported and initialized without errors
 */

import MinimalDamienMCP from '../server.js';

async function runBasicTest() {
  console.log('🧪 Running basic test for Minimal Damien MCP Server...');
  
  try {
    // Test 1: Import and instantiate the server
    console.log('✅ Test 1: Server import successful');
    
    const server = new MinimalDamienMCP();
    console.log('✅ Test 2: Server instantiation successful');
    
    // Test 3: Verify server has required properties
    if (!server.server) {
      throw new Error('Server does not have MCP server instance');
    }
    console.log('✅ Test 3: MCP server instance created');
    
    if (!server.transport) {
      console.log('✅ Test 4: Transport not yet connected (expected)');
    }
    
    console.log('🎉 All basic tests passed!');
    console.log('📋 Server foundation is ready for tool implementation');
    
    // Clean exit
    process.exit(0);
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

runBasicTest();
