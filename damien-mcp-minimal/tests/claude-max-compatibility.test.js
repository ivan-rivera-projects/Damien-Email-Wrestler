#!/usr/bin/env node
/**
 * Claude MAX Compatibility Tests
 * 
 * These tests specifically target compatibility with Claude MAX to ensure
 * the MCP server doesn't trigger crashes or memory issues in Claude Desktop.
 * 
 * Key focus areas:
 * - Tool list request frequency (caching)
 * - MCP protocol compliance
 * - Tool schema validation for Claude MAX compatibility
 * - Memory usage and performance monitoring
 */

import { spawn } from 'child_process';
import { setTimeout } from 'timers/promises';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import MinimalDamienMCP from '../server.js';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class ClaudeMaxCompatibilityTest {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.server = null;
    this.mcpProcess = null;
    this.testToolRequests = [];
  }

  async runAllTests() {
    console.log('🧪 Running Claude MAX Compatibility Test Suite...\n');

    try {
      // Test 1: Tool list caching and request frequency
      await this.testToolListCaching();
      
      // Test 2: MCP protocol compliance
      await this.testMCPProtocolCompliance();
      
      // Test 3: Tool schema validation
      await this.testToolSchemaValidation();
      
      // Test 4: Memory usage and performance
      await this.testMemoryAndPerformance();
      
      this.printResults();
      
    } catch (error) {
      console.error('❌ Test suite failed:', error);
      this.cleanup();
      process.exit(1);
    }
  }

  async testToolListCaching() {
    console.log('📋 Test 1: Tool List Caching and Request Frequency');
    
    try {
      // Initialize server instance for direct testing
      this.server = new MinimalDamienMCP();
      
      // Reset the cache to ensure we're testing from scratch
      this.server.invalidateToolsCache();
      
      // Record timestamps of list_tools requests
      const timestamps = [];
      
      // Make multiple requests in quick succession
      for (let i = 0; i < 5; i++) {
        const startTime = Date.now();
        timestamps.push(startTime);
        
        await this.server.getCachedTools();
        
        // Add a small delay to simulate Claude MAX's request pattern
        await setTimeout(100);
      }
      
      // Get the request stats to analyze caching behavior
      const stats = this.server.getRequestStats();
      
      // Verify cache hits are working
      const cacheHits = stats.listTools.cacheHits;
      this.assert(cacheHits >= 4, `Cache hits should be at least 4, got ${cacheHits}`);
      console.log(`✅ Cache hits working correctly (${cacheHits} out of 5 requests)`);
      
      // Check backend requests frequency (should be only 1)
      const backendRequests = 5 - cacheHits;
      this.assert(backendRequests <= 1, `Backend requests should be at most 1, got ${backendRequests}`);
      console.log(`✅ Backend request frequency limited correctly (${backendRequests} actual requests)`);
      
      // Verify cache data is preserved
      this.assert(this.server.toolsCache.data !== null, 'Cache data should be preserved');
      console.log('✅ Cache data correctly preserved between requests');
      
      this.passed += 3;
    } catch (error) {
      console.log('❌ Tool list caching test failed:', error.message);
      this.failed++;
    }
  }

  async testMCPProtocolCompliance() {
    console.log('\n📋 Test 2: MCP Protocol Compliance');
    
    try {
      // We'll launch the MCP server as a child process and communicate with it
      // using the MCP protocol to verify compliance
      
      // Create a temporary test file to send MCP protocol messages
      const serverPath = resolve(__dirname, '../server.js');
      
      // Initialize the MCP child process
      this.mcpProcess = spawn('node', [serverPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      // Wait for server to initialize
      await setTimeout(1000);
      
      // Test list_tools request (standard MCP protocol format)
      const listToolsRequest = JSON.stringify({
        jsonrpc: '2.0',
        method: 'list_tools',
        id: 'test-1',
        params: {}
      }) + '\n';
      
      // Send request to MCP server
      this.mcpProcess.stdin.write(listToolsRequest);
      
      // Collect response with timeout
      const listToolsResponse = await this.readMCPResponse(this.mcpProcess, 3000);
      
      // Validate response format
      this.assert(listToolsResponse, 'Should receive a response to list_tools request');
      this.assert(listToolsResponse.jsonrpc === '2.0', 'Response should follow JSON-RPC 2.0');
      this.assert(listToolsResponse.id === 'test-1', 'Response ID should match request ID');
      this.assert(Array.isArray(listToolsResponse.result.tools), 'Response should contain tools array');
      
      console.log('✅ list_tools request/response follows MCP protocol');
      
      // Test call_tool request (with a tool that should be available in phase 1)
      const callToolRequest = JSON.stringify({
        jsonrpc: '2.0',
        method: 'call_tool',
        id: 'test-2',
        params: {
          name: 'damien_list_emails',
          params: {}
        }
      }) + '\n';
      
      // Send request to MCP server
      this.mcpProcess.stdin.write(callToolRequest);
      
      // Collect response with timeout
      const callToolResponse = await this.readMCPResponse(this.mcpProcess, 3000);
      
      // Validate response format (even if the tool execution fails, the format should be correct)
      this.assert(callToolResponse, 'Should receive a response to call_tool request');
      this.assert(callToolResponse.jsonrpc === '2.0', 'Response should follow JSON-RPC 2.0');
      this.assert(callToolResponse.id === 'test-2', 'Response ID should match request ID');
      this.assert(Array.isArray(callToolResponse.result.content), 'Response should contain content array');
      
      console.log('✅ call_tool request/response follows MCP protocol');
      
      this.passed += 2;
    } catch (error) {
      console.log('❌ MCP protocol compliance test failed:', error.message);
      this.failed++;
    } finally {
      // Clean up the MCP process
      if (this.mcpProcess) {
        this.mcpProcess.kill();
        this.mcpProcess = null;
      }
    }
  }

  async testToolSchemaValidation() {
    console.log('\n📋 Test 3: Tool Schema Validation for Claude MAX Compatibility');
    
    try {
      // If server isn't initialized yet, do it now
      if (!this.server) {
        this.server = new MinimalDamienMCP();
      }
      
      // Get tools with validation in place
      const tools = await this.server.getCachedTools();
      
      if (tools.length === 0) {
        console.log('⚠️  No tools available for schema validation test');
        return;
      }
      
      // Check each tool for Claude MAX compatibility issues
      let allToolsValid = true;
      const schemaIssues = [];
      
      for (const tool of tools) {
        // Tool name checks
        if (!tool.name || typeof tool.name !== 'string') {
          allToolsValid = false;
          schemaIssues.push(`Tool missing valid name: ${JSON.stringify(tool.name)}`);
        }
        
        // Tool description checks
        if (!tool.description || typeof tool.description !== 'string') {
          allToolsValid = false;
          schemaIssues.push(`Tool missing valid description: ${tool.name}`);
        }
        
        // Input schema checks
        if (!tool.inputSchema || typeof tool.inputSchema !== 'object') {
          allToolsValid = false;
          schemaIssues.push(`Tool missing valid inputSchema: ${tool.name}`);
        } else {
          // Check input schema properties
          if (tool.inputSchema.properties) {
            // Check each property for type specification
            for (const [propName, prop] of Object.entries(tool.inputSchema.properties)) {
              if (!prop.type) {
                allToolsValid = false;
                schemaIssues.push(`Property "${propName}" in tool "${tool.name}" missing type`);
              }
              
              // Check array schema issues
              if (prop.type === 'array' && !prop.items) {
                allToolsValid = false;
                schemaIssues.push(`Array property "${propName}" in tool "${tool.name}" missing items definition`);
              }
            }
          }
          
          // Check that required is an array
          if (tool.inputSchema.required && !Array.isArray(tool.inputSchema.required)) {
            allToolsValid = false;
            schemaIssues.push(`Tool "${tool.name}" has invalid required property (not an array)`);
          }
        }
      }
      
      // Verify all tools have valid schemas
      if (allToolsValid) {
        console.log('✅ All tool schemas are valid for Claude MAX compatibility');
        this.passed++;
      } else {
        console.log('❌ Some tool schemas have issues for Claude MAX compatibility:');
        schemaIssues.forEach(issue => console.log(`   - ${issue}`));
        this.failed++;
      }
      
    } catch (error) {
      console.log('❌ Tool schema validation test failed:', error.message);
      this.failed++;
    }
  }

  async testMemoryAndPerformance() {
    console.log('\n📋 Test 4: Memory Usage and Performance Monitoring');
    
    try {
      // If server isn't initialized yet, do it now
      if (!this.server) {
        this.server = new MinimalDamienMCP();
      }
      
      // Get initial memory usage
      const initialMemory = process.memoryUsage();
      
      // Make a series of requests to simulate Claude MAX activity
      const iterations = 10;
      const startTime = Date.now();
      
      for (let i = 0; i < iterations; i++) {
        // Get tools (should use cache after first request)
        await this.server.getCachedTools();
        
        // Add a small delay to simulate Claude MAX's request pattern
        await setTimeout(100);
      }
      
      // Measure elapsed time
      const elapsedTime = Date.now() - startTime;
      const averageResponseTime = elapsedTime / iterations;
      
      // Get final memory usage
      const finalMemory = process.memoryUsage();
      
      // Calculate memory growth
      const heapGrowth = finalMemory.heapUsed - initialMemory.heapUsed;
      const rssGrowth = finalMemory.rss - initialMemory.rss;
      
      // Verify performance is within expected bounds
      this.assert(averageResponseTime < 200, `Average response time should be under 200ms, got ${averageResponseTime.toFixed(2)}ms`);
      console.log(`✅ Performance meets target (avg response: ${averageResponseTime.toFixed(2)}ms)`);
      
      // Check memory leak indicators (allow for some growth, but not excessive)
      // Less than 10MB growth for 10 iterations is reasonable
      const maxAcceptableGrowthMB = 10;
      const heapGrowthMB = heapGrowth / (1024 * 1024);
      const rssGrowthMB = rssGrowth / (1024 * 1024);
      
      this.assert(heapGrowthMB < maxAcceptableGrowthMB, 
        `Heap growth should be under ${maxAcceptableGrowthMB}MB, got ${heapGrowthMB.toFixed(2)}MB`);
        
      console.log(`✅ Memory usage stable (heap growth: ${heapGrowthMB.toFixed(2)}MB, RSS growth: ${rssGrowthMB.toFixed(2)}MB)`);
      
      this.passed += 2;
    } catch (error) {
      console.log('❌ Memory and performance test failed:', error.message);
      this.failed++;
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
      console.log('\n🎉 All Claude MAX compatibility tests passed!');
      console.log('   The MCP server is compatible with Claude MAX and should not cause crashes.');
    } else {
      console.log('\n⚠️  Some Claude MAX compatibility tests failed. Please review the issues above.');
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
  const test = new ClaudeMaxCompatibilityTest();
  test.runAllTests().finally(() => test.cleanup());
}

export default ClaudeMaxCompatibilityTest;
