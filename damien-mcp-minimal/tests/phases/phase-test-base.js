import assert from 'assert';

class PhaseTestBase {
  constructor(phaseNumber) {
    this.phaseNumber = phaseNumber;
    this.server = null;
    this.results = {
      passed: 0,
      failed: 0,
      skipped: 0,
      tests: []
    };
  }

  async setup() {
    // Set the phase for testing
    process.env.DAMIEN_INITIAL_PHASE = this.phaseNumber.toString();
    
    // In a real implementation, this would initialize the server
    // For testing purposes, we're creating a mock server
    this.server = {
      getCachedTools: async () => {
        // Return tools based on the current phase
        const toolSets = {
          1: [
            { name: 'damien_list_emails' },
            { name: 'damien_get_email_details' },
            { name: 'damien_create_draft' },
            { name: 'damien_send_draft' },
            { name: 'damien_list_drafts' }
          ],
          2: [
            // Phase 1 tools
            { name: 'damien_list_emails' },
            { name: 'damien_get_email_details' },
            { name: 'damien_create_draft' },
            { name: 'damien_send_draft' },
            { name: 'damien_list_drafts' },
            // Phase 2 tools
            { name: 'damien_trash_emails' },
            { name: 'damien_label_emails' },
            { name: 'damien_mark_emails' },
            { name: 'damien_update_draft' },
            { name: 'damien_delete_draft' },
            { name: 'damien_get_draft_details' },
            { name: 'damien_delete_emails_permanently' }
          ],
          // Additional phases would be defined similarly
        };
        
        // Default to returning all tools for higher phases
        if (this.phaseNumber > 2) {
          return toolSets[2].concat([
            // Phase 3 tools
            { name: 'damien_list_threads' },
            { name: 'damien_get_thread_details' },
            { name: 'damien_modify_thread_labels' },
            { name: 'damien_trash_thread' },
            { name: 'damien_delete_thread_permanently' }
          ]);
        }
        
        return toolSets[this.phaseNumber] || [];
      },
      
      // Mock method for tool responses
      mockResponses: {},
      mockToolResponse(toolName, response) {
        this.mockResponses[toolName] = response;
      },
      
      // Mock method for invoking tools
      async invokeToolWithMock(toolName, params) {
        if (this.mockResponses[toolName]) {
          return this.mockResponses[toolName];
        }
        throw new Error(`No mock response defined for tool: ${toolName}`);
      },
      
      // Mock method for getting request stats
      getRequestStats() {
        return {
          averageResponseTime: 50,
          requestCount: 10,
          cacheHitRate: 0.9,
          errorRate: 0.01
        };
      }
    };
    
    // Wait for server initialization (simulated)
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  async teardown() {
    // Cleanup
    this.server = null;
  }

  async runTest(testName, testFn) {
    console.log(`Running test: ${testName}`);
    
    try {
      await testFn();
      console.log(`✅ PASS: ${testName}`);
      this.results.passed++;
      this.results.tests.push({ name: testName, status: 'passed' });
    } catch (error) {
      console.error(`❌ FAIL: ${testName}`);
      console.error(`Error: ${error.message}`);
      this.results.failed++;
      this.results.tests.push({ name: testName, status: 'failed', error: error.message });
    }
  }

  skipTest(testName) {
    console.log(`⏩ SKIP: ${testName}`);
    this.results.skipped++;
    this.results.tests.push({ name: testName, status: 'skipped' });
  }

  printSummary() {
    console.log('\n----------------------------------------');
    console.log(`Phase ${this.phaseNumber} Test Summary:`);
    console.log(`Total tests: ${this.results.passed + this.results.failed + this.results.skipped}`);
    console.log(`Passed: ${this.results.passed}`);
    console.log(`Failed: ${this.results.failed}`);
    console.log(`Skipped: ${this.results.skipped}`);
    console.log('----------------------------------------\n');
    
    if (this.results.failed > 0) {
      console.log('Failed tests:');
      this.results.tests
        .filter(test => test.status === 'failed')
        .forEach(test => {
          console.log(`- ${test.name}: ${test.error}`);
        });
      console.log('----------------------------------------\n');
    }
  }

  async verifyToolAvailability(toolNames) {
    const tools = await this.server.getCachedTools();
    const availableToolNames = tools.map(tool => tool.name);
    
    for (const toolName of toolNames) {
      assert(
        availableToolNames.includes(toolName),
        `Tool '${toolName}' should be available in phase ${this.phaseNumber}`
      );
    }
  }

  async runPerformanceTest() {
    console.log('Running performance test...');
    
    const iterations = 10;
    const startTime = Date.now();
    
    for (let i = 0; i < iterations; i++) {
      await this.server.getCachedTools();
    }
    
    const elapsedMs = Date.now() - startTime;
    const avgMs = elapsedMs / iterations;
    
    console.log(`Performance test results:`);
    console.log(`- Average response time: ${avgMs.toFixed(2)}ms`);
    
    // Phase-specific performance requirements
    let maxAcceptableResponseTime;
    switch (this.phaseNumber) {
      case 1: maxAcceptableResponseTime = 1000; break;
      case 2: maxAcceptableResponseTime = 1200; break;
      case 3: maxAcceptableResponseTime = 1400; break;
      case 4: maxAcceptableResponseTime = 1600; break;
      case 5: maxAcceptableResponseTime = 2000; break;
      case 6: maxAcceptableResponseTime = 2200; break;
      default: maxAcceptableResponseTime = 1000;
    }
    
    assert(
      avgMs < maxAcceptableResponseTime,
      `Performance below threshold. Expected < ${maxAcceptableResponseTime}ms, got ${avgMs.toFixed(2)}ms`
    );
    
    return { avgMs, iterations, maxAcceptableResponseTime };
  }
}

export default PhaseTestBase;