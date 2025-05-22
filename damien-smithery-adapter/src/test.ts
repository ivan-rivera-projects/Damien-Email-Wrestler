import fetch from 'node-fetch';
import { CONFIG } from './config.js';

/**
 * Simple test script to verify the Smithery adapter functionality
 */
async function testSmitheryAdapter() {
  console.log('Testing Damien Smithery Adapter...');
  
  try {
    // Test 1: Health check
    console.log('\nTesting health endpoint...');
    const healthResponse = await fetch(`http://localhost:${CONFIG.SERVER_PORT}/health`);
    
    if (!healthResponse.ok) {
      console.error(`Health check failed: ${healthResponse.status} ${healthResponse.statusText}`);
    } else {
      const healthResult = await healthResponse.json();
      console.log('Health check result:', JSON.stringify(healthResult, null, 2));
    }
    
    // Test 2: List tools
    console.log('\nTesting tools listing endpoint...');
    const toolsResponse = await fetch(`http://localhost:${CONFIG.SERVER_PORT}/tools`);
    
    if (!toolsResponse.ok) {
      console.error(`Tools listing failed: ${toolsResponse.status} ${toolsResponse.statusText}`);
    } else {
      const toolsResult = await toolsResponse.json();
      console.log('Available tools:', JSON.stringify(toolsResult, null, 2));
    }
    
    // Test 3: Execute tool
    console.log('\nTesting tool execution endpoint...');
    const executeResponse = await fetch(`http://localhost:${CONFIG.SERVER_PORT}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tool: 'damien_list_emails',
        input: {
          query: 'is:unread',
          max_results: 5
        },
        session_id: 'test_session_123'
      })
    });
    
    if (!executeResponse.ok) {
      console.error(`Tool execution failed: ${executeResponse.status} ${executeResponse.statusText}`);
      const errorText = await executeResponse.text();
      console.error('Error details:', errorText);
    } else {
      const executeResult = await executeResponse.json();
      console.log('Tool execution result:', JSON.stringify(executeResult, null, 2));
    }
    
    console.log('\nTest completed!');
  } catch (error) {
    console.error('Test failed:', error);
  }
}

// Check if this script was executed directly (not imported)
if (require.main === module) {
  testSmitheryAdapter().catch(console.error);
}

export { testSmitheryAdapter };