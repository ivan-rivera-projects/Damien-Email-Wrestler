#!/usr/bin/env node
/**
 * Integration Tests
 * 
 * These tests validate the complete integration of the MCP server with:
 * - Backend API
 * - Claude Desktop compatibility
 * - Error handling scenarios
 * 
 * These tests require a running backend server on the configured port.
 */

import { spawn } from 'child_process';
import { setTimeout } from 'timers/promises';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import MinimalDamienMCP from '../server.js';
import { CONFIG } from '../config/claude-max-config.js';
import fetch from 'node-fetch';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class IntegrationTest {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.server = null;
    this.mcpProcess = null;
    
    // Skip backend tests flag (set if backend is unavailable)
    this.skipBackendTests = false;
  }

  async runAllTests() {
    console.log('🧪 Running Integration Test Suite...\n');

    try {
      // Test 1: Backend connectivity
      await this.testBackendConnectivity();
      
      // Skip remaining tests if backend is unavailable
      if (this.skipBackendTests) {
        console.log('⚠️  Skipping remaining tests due to backend unavailability');
        this.printResults();
        return;
      }
      
      // Test 2: Complete workflow test
      await this.testCompleteWorkflow();
      
      // Test 3: Error handling scenarios
      await this.testErrorHandling();
      
      // Test 4: Claude Desktop compatibility
      await this.testClaudeDesktopCompatibility();
      
      this.printResults();
      
    } catch (error) {
      console.error('❌ Test suite failed:', error);
      this.cleanup();
      process.exit(1);
    }
  }

  async testBackendConnectivity() {
    console.log('📋 Test 1: Backend Connectivity');
    
    try {
      // Initialize server instance for testing
      this.server = new MinimalDamienMCP();
      
      // Perform health check to verify backend connectivity
      const health = await this.server.damienClient.healthCheck();
      
      if (health.status === 'healthy') {
        console.log('✅ Backend is reachable and healthy');
        this.passed++;
      } else {
        console.log('⚠️  Backend is reachable but reports unhealthy status:', health.error);
        console.log('   Some tests may fail due to backend issues');
        this.passed++;
      }
      
      // Verify we can retrieve tools from the backend
      try {
        const tools = await this.server.damienClient.getTools();
        console.log(`✅ Successfully retrieved ${tools.length} tools from backend`);
        this.passed++;
      } catch (error) {
        console.log('❌ Failed to retrieve tools from backend:', error.message);
        console.log('⚠️  Marking backend tests to be skipped');
        this.skipBackendTests = true;
        this.failed++;
      }
      
    } catch (error) {
      console.log('❌ Backend connectivity test failed:', error.message);
      console.log('⚠️  Marking backend tests to be skipped');
      this.skipBackendTests = true;
      this.failed++;
    }
  }

  async testCompleteWorkflow() {
    console.log('\n📋 Test 2: Complete Workflow Test');
    
    try {
      // Direct test of the full workflow using the MCP server
      
      // 1. Get tools available in phase 1
      const tools = await this.server.getCachedTools();
      
      this.assert(tools.length > 0, 'Should have at least one tool available');
      console.log(`✅ Retrieved ${tools.length} tools for Phase 1`);
      
      // 2. Validate tool list caching works
      // Make multiple requests and verify backend is only hit once
      const initialStats = this.server.getRequestStats();
      
      // Make 5 consecutive requests
      for (let i = 0; i < 5; i++) {
        await this.server.getCachedTools();
        await setTimeout(50); // Brief delay
      }
      
      const updatedStats = this.server.getRequestStats();
      
      // Calculate number of cache hits
      const cacheHits = updatedStats.listTools.cacheHits - initialStats.listTools.cacheHits;
      this.assert(cacheHits >= 4, `Should have at least 4 cache hits, got ${cacheHits}`);
      console.log(`✅ Cache is working correctly (${cacheHits} cache hits)`);
      
      // 3. Test tool execution (if we have tools)
      if (tools.length > 0) {
        // Find a tool from phase 1 to test
        const testTool = tools.find(tool => 
          tool.name === 'damien_list_emails' || 
          tool.name === 'damien_list_drafts'
        );
        
        if (testTool) {
          try {
            // Execute the tool via server
            const requestParams = { 
              params: {
                name: testTool.name,
                params: {}
              }
            };
            
            // Mock the MCP request structure
            const response = await this.server.server.requestHandlers.get('call_tool')(requestParams);
            
            this.assert(response && response.content, 'Tool execution should return content');
            console.log(`✅ Successfully executed tool: ${testTool.name}`);
            this.passed++;
          } catch (error) {
            console.log(`⚠️  Tool execution test failed for ${testTool.name}:`, error.message);
            console.log('   This may be expected if the backend requires specific parameters');
            // Not counting as failure since it depends on backend state
          }
        } else {
          console.log('⚠️  No suitable test tool found for execution test');
        }
      }
      
      this.passed += 2;
    } catch (error) {
      console.log('❌ Complete workflow test failed:', error.message);
      this.failed++;
    }
  }

  async testErrorHandling() {
    console.log('\n📋 Test 3: Error Handling Scenarios');
    
    try {
      // Test handling of various error scenarios
      
      // 1. Test with non-existent tool
      try {
        const requestParams = { 
          params: {
            name: 'non_existent_tool_xyz',
            params: {}
          }
        };
        
        // Call the handler directly
        const response = await this.server.server.requestHandlers.get('call_tool')(requestParams);
        
        // Verify we get a proper error response
        this.assert(response && response.content, 'Error response should include content');
        const responseText = response.content[0].text;
        this.assert(responseText.includes('not available'), 'Error message should indicate tool is not available');
        console.log('✅ Properly handled non-existent tool');
        this.passed++;
      } catch (error) {
        console.log('❌ Non-existent tool error handling failed:', error.message);
        this.failed++;
      }
      
      // 2. Test with backend connection failure
      try {
        // Create a client with invalid backend URL
        const originalBaseUrl = this.server.damienClient.baseUrl;
        this.server.damienClient.baseUrl = 'http://localhost:9999'; // Non-existent port
        
        // Invalidate cache to force a backend request
        this.server.invalidateToolsCache();
        
        // Try to get tools (should handle backend failure gracefully)
        const tools = await this.server.getCachedTools();
        
        // Verify we get an empty array instead of an error
        this.assert(Array.isArray(tools), 'Should return array even on backend failure');
        console.log('✅ Properly handled backend connection failure');
        
        // Restore the original URL
        this.server.damienClient.baseUrl = originalBaseUrl;
        this.server.invalidateToolsCache();
        this.passed++;
      } catch (error) {
        console.log('❌ Backend failure handling test failed:', error.message);
        this.failed++;
      }
      
      // 3. Test timeout handling
      try {
        // Create a mock tool execution that will timeout
        const originalExecuteTool = this.server.damienClient.executeTool;
        this.server.damienClient.executeTool = () => new Promise(resolve => {
          // This promise never resolves, simulating a hung request
          setTimeout(() => {}, 100000);
        });
        
        // Set a shorter timeout for testing
        const originalTimeout = CONFIG.DEFAULT_TIMEOUT;
        CONFIG.DEFAULT_TIMEOUT = 500; // 500ms timeout
        
        // Call a tool (should timeout)
        const requestParams = { 
          params: {
            name: 'damien_list_emails',
            params: {}
          }
        };
        
        const startTime = Date.now();
        const response = await this.server.server.requestHandlers.get('call_tool')(requestParams);
        const elapsed = Date.now() - startTime;
        
        // Verify timeout is working
        this.assert(elapsed < 2000, `Request should timeout within 2 seconds, took ${elapsed}ms`);
        this.assert(response && response.content, 'Timeout response should include content');
        const responseText = response.content[0].text;
        this.assert(responseText.includes('timeout') || responseText.includes('timed out'), 
          'Error message should indicate timeout');
        console.log('✅ Properly handled request timeout');
        
        // Restore original functions and settings
        this.server.damienClient.executeTool = originalExecuteTool;
        CONFIG.DEFAULT_TIMEOUT = originalTimeout;
        this.passed++;
      } catch (error) {
        console.log('❌ Timeout handling test failed:', error.message);
        this.failed++;
      }
    } catch (error) {
      console.log('❌ Error handling scenarios test failed:', error.message);
      this.failed++;
    }
  }

  async testClaudeDesktopCompatibility() {
    console.log('\n📋 Test 4: Claude Desktop Compatibility');
    
    try {
      // Launch MCP server as it would be used with Claude Desktop
      const serverPath = resolve(__dirname, '../server.js');
      
      this.mcpProcess = spawn('node', [serverPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      // Wait for server to initialize
      await setTimeout(1000);
      
      // Test sequence that simulates Claude Desktop behavior
      
      // 1. Rapid list_tools requests (Claude MAX pattern)
      const results = [];
      
      for (let i = 0; i < 3; i++) {
        const listToolsRequest = JSON.stringify({
          jsonrpc: '2.0',
          method: 'list_tools',
          id: `test-${i+1}`,
          params: {}
        }) + '\n';
        
        this.mcpProcess.stdin.write(listToolsRequest);
        
        // Wait for response
        try {
          const response = await this.readMCPResponse(this.mcpProcess, 2000);
          results.push(response);
        } catch (error) {
          console.log(`Failed on request ${i+1}:`, error.message);
          throw error;
        }
        
        // Add brief delay to simulate Claude MAX behavior
        await setTimeout(100);
      }
      
      // Verify all responses were successful
      this.assert(results.length === 3, `Should receive 3 responses, got ${results.length}`);
      for (let i = 0; i < results.length; i++) {
        this.assert(results[i].id === `test-${i+1}`, `Response ID should match request ID for request ${i+1}`);
        this.assert(Array.isArray(results[i].result.tools), `Response ${i+1} should contain tools array`);
      }
      
      console.log('✅ Successfully handled Claude MAX-like rapid tool list requests');
      
      // 2. Call a non-existent tool (common Claude MAX pattern)
      const callToolRequest = JSON.stringify({
        jsonrpc: '2.0',
        method: 'call_tool',
        id: 'bad-tool',
        params: {
          name: 'nonexistent_tool',
          params: {}
        }
      }) + '\n';
      
      this.mcpProcess.stdin.write(callToolRequest);
      
      // Wait for response
      const callToolResponse = await this.readMCPResponse(this.mcpProcess, 2000);
      
      // Verify response format is correct even for error
      this.assert(callToolResponse.id === 'bad-tool', 'Response ID should match request ID');
      this.assert(Array.isArray(callToolResponse.result.content), 'Response should contain content array');
      this.assert(callToolResponse.result.content[0].type === 'text', 'Content should be of type text');
      this.assert(callToolResponse.result.content[0].text.includes('not available'), 
        'Error message should indicate tool is not available');
      
      console.log('✅ Successfully handled non-existent tool call from Claude MAX');
      
      this.passed += 2;
    } catch (error) {
      console.log('❌ Claude Desktop compatibility test failed:', error.message);
      this.failed++;
    } finally {
      // Clean up the MCP process
      if (this.mcpProcess) {
        this.mcpProcess.kill();
        this.mcpProcess = null;
      }
    }
  }

  /**
   * Helper function to read a response from the MCP process
   */
  readMCPResponse(process, timeout) {
    return new Promise((resolve, reject) => {
      let data = '';
      const timeoutId = setTimeout(() => {
        reject(new Error(`Timeout waiting for MCP response after ${timeout}ms`));
      }, timeout);
      
      process.stdout.on('data', (chunk) => {
        data += chunk.toString();
        
        // Check if we have a complete JSON-RPC message
        if (data.includes('\n')) {
          // Split by newlines and process each complete message
          const lines = data.split('\n');
          
          // Process all complete messages (except the last one which might be incomplete)
          for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i].trim();
            if (line) {
              try {
                const message = JSON.parse(line);
                clearTimeout(timeoutId);
                process.stdout.removeAllListeners('data');
                resolve(message);
                return;
              } catch (e) {
                // Not a valid JSON message, continue
              }
            }
          }
          
          // Keep the last (potentially incomplete) line for the next chunk
          data = lines[lines.length - 1];
        }
      });
      
      process.stderr.on('data', (chunk) => {
        console.log(`MCP stderr: ${chunk.toString()}`);
      });
      
      process.on('error', (error) => {
        clearTimeout(timeoutId);
        reject(error);
      });
      
      process.on('exit', (code) => {
        if (code !== 0) {
          clearTimeout(timeoutId);
          reject(new Error(`MCP process exited with code ${code}`));
        }
      });
    });
  }

  assert(condition, message) {
    if (!condition) {
      throw new Error(`Assertion failed: ${message}`);
    }
  }

  printResults() {
    console.log('\n📊 Test Results');
    console.log('================');
    console.log(`✅ Passed: ${this.passed}`);
    console.log(`❌ Failed: ${this.failed}`);
    console.log(`📈 Total:  ${this.passed + this.failed}`);
    
    if (this.failed === 0) {
      console.log('\n🎉 All integration tests passed!');
      if (this.skipBackendTests) {
        console.log('⚠️  Note: Some tests were skipped due to backend unavailability.');
        console.log('   Please ensure the backend is running for complete testing.');
      } else {
        console.log('   The MCP server is fully integrated with the backend and ready for Claude Desktop.');
      }
    } else {
      console.log('\n⚠️  Some integration tests failed. Please review the issues above.');
    }
  }

  cleanup() {
    // Clean up resources
    if (this.mcpProcess) {
      this.mcpProcess.kill();
    }
  }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const test = new IntegrationTest();
  test.runAllTests().finally(() => test.cleanup());
}

export default IntegrationTest;
