import fetch from 'node-fetch';

async function testAdapter() {
  console.log('Testing Damien Smithery Adapter...');
  
  // Test server health
  console.log('\n1. Testing server health...');
  try {
    const healthResponse = await fetch('http://localhost:8081/health');
    const healthData = await healthResponse.json();
    console.log('Health check response:', healthData);
  } catch (error) {
    console.error('Health check failed:', error instanceof Error ? error.message : String(error));
  }
  
  // Test tool listing
  console.log('\n2. Testing tool listing...');
  try {
    const toolsResponse = await fetch('http://localhost:8081/tools');
    const toolsData = await toolsResponse.json();
    console.log('Tools available:', toolsData);
  } catch (error) {
    console.error('Tool listing failed:', error instanceof Error ? error.message : String(error));
  }
  
  // Test executing a simple tool (list emails)
  console.log('\n3. Testing email listing tool...');
  try {
    const executeResponse = await fetch('http://localhost:8081/execute', {
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
    
    const executeData = await executeResponse.json();
    console.log('Email listing result:', JSON.stringify(executeData, null, 2));
  } catch (error) {
    console.error('Tool execution failed:', error instanceof Error ? error.message : String(error));
  }
}

// Run the test function - this is the ES module way to handle "main" execution
testAdapter().catch(error => {
  console.error('Unhandled error in test:', error instanceof Error ? error.message : String(error));
});
