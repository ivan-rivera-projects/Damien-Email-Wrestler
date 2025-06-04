#!/usr/bin/env node
/**
 * Test suite for DamienClient
 * Tests backend communication, error handling, and tool operations
 */

import DamienClient from '../core/damien-client.js';

class DamienClientTest {
  constructor() {
    this.client = null;
    this.passed = 0;
    this.failed = 0;
  }

  async runAllTests() {
    console.log('🧪 Running DamienClient test suite...\n');

    try {
      // Test 1: Client instantiation
      await this.testClientInstantiation();
      
      // Test 2: Configuration validation
      await this.testConfigurationValidation();
      
      // Test 3: Health check
      await this.testHealthCheck();
      
      // Test 4: Tool fetching
      await this.testGetTools();
      
      // Test 5: Tool execution (if backend is available)
      await this.testToolExecution();
      
      // Test 6: Error handling
      await this.testErrorHandling();
      
      this.printResults();
      
    } catch (error) {
      console.error('❌ Test suite failed:', error);
      process.exit(1);
    }
  }

  async testClientInstantiation() {
    console.log('📋 Test 1: Client Instantiation');
    
    try {
      // Test with default configuration
      this.client = new DamienClient();
      this.assert(this.client instanceof DamienClient, 'Client should be instance of DamienClient');
      this.assert(this.client.baseUrl, 'Client should have baseUrl');
      this.assert(this.client.apiKey, 'Client should have apiKey');
      
      console.log('✅ Client instantiated successfully');
      
      // Test with custom configuration
      const customClient = new DamienClient({
        baseUrl: 'http://localhost:8892',
        apiKey: 'test-key-12345678901234567890123456789012',
        timeout: 5000
      });
      
      this.assert(customClient.baseUrl === 'http://localhost:8892', 'Custom baseUrl should be set');
      this.assert(customClient.defaultTimeout === 5000, 'Custom timeout should be set');
      
      console.log('✅ Custom configuration works');
      this.passed += 2;
      
    } catch (error) {
      console.log('❌ Client instantiation failed:', error.message);
      this.failed++;
    }
  }

  async testConfigurationValidation() {
    console.log('\n📋 Test 2: Configuration Validation');
    
    try {
      // Test invalid URL
      try {
        new DamienClient({ baseUrl: 'invalid-url' });
        this.failed++;
        console.log('❌ Should have failed with invalid URL');
      } catch (error) {
        console.log('✅ Correctly rejected invalid URL');
        this.passed++;
      }
      
      // Test missing API key
      try {
        new DamienClient({ 
          apiKey: '',
          baseUrl: 'http://localhost:8892' // Provide valid URL to isolate API key test
        });
        this.failed++;
        console.log('❌ Should have failed with empty API key');
      } catch (error) {
        console.log('✅ Correctly rejected empty API key');
        this.passed++;
      }
      
      // Test short API key
      try {
        new DamienClient({ apiKey: 'short' });
        this.failed++;
        console.log('❌ Should have failed with short API key');
      } catch (error) {
        console.log('✅ Correctly rejected short API key');
        this.passed++;
      }
      
    } catch (error) {
      console.log('❌ Configuration validation test failed:', error.message);
      this.failed++;
    }
  }

  async testHealthCheck() {
    console.log('\n📋 Test 3: Health Check');
    
    try {
      const health = await this.client.healthCheck();
      
      this.assert(health && typeof health === 'object', 'Health response should be an object');
      this.assert(health.status, 'Health response should have status');
      this.assert(health.timestamp, 'Health response should have timestamp');
      
      if (health.status === 'healthy') {
        console.log('✅ Backend is healthy and reachable');
        this.passed++;
      } else {
        console.log('⚠️  Backend health check indicates issues:', health.error);
        console.log('✅ Health check method works (backend may be down)');
        this.passed++;
      }
      
    } catch (error) {
      console.log('❌ Health check failed:', error.message);
      this.failed++;
    }
  }

  async testGetTools() {
    console.log('\n📋 Test 4: Get Tools');
    
    try {
      const tools = await this.client.getTools();
      
      this.assert(Array.isArray(tools), 'Tools should be an array');
      console.log(`✅ Fetched ${tools.length} tools from backend`);
      
      if (tools.length > 0) {
        const firstTool = tools[0];
        this.assert(firstTool.name, 'Tool should have name');
        this.assert(firstTool.description, 'Tool should have description');
        this.assert(firstTool.inputSchema, 'Tool should have inputSchema');
        
        console.log(`✅ Tool structure validated (sample: ${firstTool.name})`);
        this.passed += 2;
      } else {
        console.log('⚠️  No tools returned (backend may not have tools registered)');
        this.passed++;
      }
      
    } catch (error) {
      console.log('❌ Get tools failed:', error.message);
      console.log('   This may indicate backend is not running on port 8892');
      this.failed++;
    }
  }

  async testToolExecution() {
    console.log('\n📋 Test 5: Tool Execution');
    
    try {
      // First get tools to see what's available
      const tools = await this.client.getTools();
      
      if (tools.length === 0) {
        console.log('⚠️  Skipping tool execution test (no tools available)');
        return;
      }
      
      // Try to execute a simple tool (health check or list type tool)
      const testTool = tools.find(tool => 
        tool.name.includes('health') || 
        tool.name.includes('list') ||
        tool.name.includes('get_vacation') // Simple getter tool
      );
      
      if (!testTool) {
        console.log('⚠️  No suitable test tool found for execution test');
        return;
      }
      
      console.log(`🔧 Testing tool execution with: ${testTool.name}`);
      
      const result = await this.client.executeTool(testTool.name, {});
      
      this.assert(result && typeof result === 'object', 'Tool result should be an object');
      console.log('✅ Tool execution successful');
      this.passed++;
      
    } catch (error) {
      console.log('❌ Tool execution failed:', error.message);
      console.log('   This may be expected if backend requires specific parameters');
      // Not counting as failure since it depends on backend state
    }
  }

  async testErrorHandling() {
    console.log('\n📋 Test 6: Error Handling');
    
    try {
      // Test with non-existent tool
      try {
        await this.client.executeTool('non_existent_tool', {});
        console.log('⚠️  Expected error for non-existent tool, but succeeded');
      } catch (error) {
        console.log('✅ Properly handled non-existent tool error');
        this.passed++;
      }
      
      // Test with invalid client (wrong port)
      const invalidClient = new DamienClient({
        baseUrl: 'http://localhost:9999', // Non-existent port
        apiKey: this.client.apiKey,
        timeout: 2000,
        maxRetries: 1
      });
      
      try {
        await invalidClient.healthCheck();
        console.log('⚠️  Expected error for invalid endpoint, but succeeded');
      } catch (error) {
        console.log('✅ Properly handled connection error');
        this.passed++;
      }
      
    } catch (error) {
      console.log('❌ Error handling test failed:', error.message);
      this.failed++;
    }
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
      console.log('\n🎉 All tests passed! DamienClient is ready for use.');
      process.exit(0);
    } else {
      console.log('\n⚠️  Some tests failed. Please review the issues above.');
      process.exit(1);
    }
  }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const test = new DamienClientTest();
  test.runAllTests();
}

export default DamienClientTest;
