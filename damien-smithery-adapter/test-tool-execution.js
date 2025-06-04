#!/usr/bin/env node

// Test tool execution directly
import fetch from 'node-fetch';

const DAMIEN_URL = 'http://localhost:8892';
const API_KEY = '7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f';

async function testToolExecution() {
  console.log('🧪 Testing Damien MCP Tool Execution\n');
  
  try {
    // Test a simple tool - list emails with minimal parameters
    console.log('📧 Testing damien_list_emails tool...');
    
    const response = await fetch(`${DAMIEN_URL}/mcp/execute_tool`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
      },
      body: JSON.stringify({
        tool_name: 'damien_list_emails',
        input: {
          max_results: 5
        },
        session_id: 'test_session',
      }),
    });
    
    console.log(`Response status: ${response.status}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      return;
    }
    
    const result = await response.json();
    console.log('✅ Tool executed successfully!');
    console.log('Result:', JSON.stringify(result, null, 2).substring(0, 500) + '...');
    
  } catch (error) {
    console.error('❌ Error executing tool:', error);
  }
}

testToolExecution();
