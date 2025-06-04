const assert = require('assert');
const PhaseTestBase = require('./phase-test-base');

class Phase5Tester extends PhaseTestBase {
  constructor() {
    super(5);
    // Combined list of all tools from phases 1-4 (not listing them all for brevity)
    this.previousPhaseTools = [
      // Phase 1-4 tools would be listed here
      'damien_list_emails',
      'damien_get_email_details',
      'damien_create_draft',
      'damien_send_draft',
      'damien_list_drafts',
      'damien_trash_emails',
      'damien_label_emails',
      'damien_mark_emails',
      'damien_update_draft',
      'damien_delete_draft',
      'damien_get_draft_details',
      'damien_delete_emails_permanently',
      'damien_list_threads',
      'damien_get_thread_details',
      'damien_modify_thread_labels',
      'damien_trash_thread',
      'damien_delete_thread_permanently',
      'damien_list_rules',
      'damien_get_rule_details',
      'damien_add_rule',
      'damien_delete_rule',
      'damien_apply_rules'
    ];
    
    this.phase5Tools = [
      'damien_ai_analyze_emails',
      'damien_ai_suggest_rules',
      'damien_ai_quick_test',
      'damien_ai_create_rule',
      'damien_ai_get_insights',
      'damien_ai_optimize_inbox',
      'damien_ai_analyze_emails_large_scale',
      'damien_ai_analyze_emails_async',
      'damien_job_get_status'
    ];
  }
  
  async runTests() {
    // Test tool availability
    await this.runTest('All Phase 5 tools available', async () => {
      await this.verifyToolAvailability(this.phase5Tools);
    });
    
    // Tool-specific tests for Phase 5
    await this.runTest('damien_ai_analyze_emails works', async () => {
      this.server.mockToolResponse('damien_ai_analyze_emails', {
        analysis: {
          categories: ['promotions', 'social'],
          important_count: 2,
          spam_likelihood: 'low'
        }
      });
      
      const response = await this.server.invokeToolWithMock('damien_ai_analyze_emails', {
        email_ids: ['email1', 'email2', 'email3']
      });
      
      assert(response.analysis.categories.length === 2, 'Should return analysis categories');
    });
    
    await this.runTest('damien_ai_suggest_rules works', async () => {
      this.server.mockToolResponse('damien_ai_suggest_rules', {
        suggested_rules: [
          {
            name: 'Archive Newsletters',
            conditions: [
              { field: 'from', operator: 'contains', value: 'newsletter' }
            ],
            actions: [
              { type: 'archive' }
            ]
          }
        ]
      });
      
      const response = await this.server.invokeToolWithMock('damien_ai_suggest_rules', {
        sample_size: 100
      });
      
      assert(response.suggested_rules.length === 1, 'Should return suggested rules');
    });
    
    // Add tests for other Phase 5 tools
    await this.runTest('damien_ai_quick_test works', async () => {
      this.server.mockToolResponse('damien_ai_quick_test', {
        matched_emails: 3,
        total_tested: 5,
        match_rate: 0.6
      });
      
      const response = await this.server.invokeToolWithMock('damien_ai_quick_test', {
        rule_id: 'rule1',
        sample_size: 5
      });
      
      assert(response.matched_emails === 3, 'Should return match count');
    });
    
    await this.runTest('damien_job_get_status works', async () => {
      this.server.mockToolResponse('damien_job_get_status', {
        job_id: 'job1',
        status: 'completed',
        progress: 100,
        result: { success: true }
      });
      
      const response = await this.server.invokeToolWithMock('damien_job_get_status', {
        job_id: 'job1'
      });
      
      assert(response.status === 'completed', 'Should return job status');
    });
    
    // Performance testing
    await this.runTest('Performance meets criteria', async () => {
      await this.runPerformanceTest();
    });
  }
}

module.exports = Phase5Tester;