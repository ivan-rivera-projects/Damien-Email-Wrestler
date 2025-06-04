const assert = require('assert');
const PhaseTestBase = require('./phase-test-base');

class Phase6Tester extends PhaseTestBase {
  constructor() {
    super(6);
    // Combined list of all tools from phases 1-5 (not listing them all for brevity)
    this.previousPhaseTools = [
      // Phase 1-5 tools would be listed here
      // Just include a few critical ones for example
      'damien_list_emails',
      'damien_trash_emails',
      'damien_list_threads',
      'damien_list_rules',
      'damien_ai_analyze_emails'
    ];
    
    this.phase6Tools = [
      'damien_get_vacation_settings',
      'damien_update_vacation_settings',
      'damien_get_imap_settings',
      'damien_update_imap_settings',
      'damien_get_pop_settings',
      'damien_update_pop_settings'
    ];
  }
  
  async runTests() {
    // Test tool availability
    await this.runTest('All Phase 6 tools available', async () => {
      await this.verifyToolAvailability(this.phase6Tools);
    });
    
    // Tool-specific tests for Phase 6
    await this.runTest('damien_get_vacation_settings works', async () => {
      this.server.mockToolResponse('damien_get_vacation_settings', {
        enabled: false,
        message: '',
        start_date: null,
        end_date: null
      });
      
      const response = await this.server.invokeToolWithMock('damien_get_vacation_settings', {});
      assert(response.hasOwnProperty('enabled'), 'Should return vacation settings');
    });
    
    await this.runTest('damien_update_vacation_settings works', async () => {
      this.server.mockToolResponse('damien_update_vacation_settings', {
        success: true,
        enabled: true
      });
      
      const response = await this.server.invokeToolWithMock('damien_update_vacation_settings', {
        enabled: true,
        message: 'I am on vacation',
        start_date: '2025-06-10',
        end_date: '2025-06-20'
      });
      
      assert(response.success === true, 'Should return success');
    });
    
    await this.runTest('damien_get_imap_settings works', async () => {
      this.server.mockToolResponse('damien_get_imap_settings', {
        enabled: true,
        auto_expunge: true,
        expunge_behavior: 'archive'
      });
      
      const response = await this.server.invokeToolWithMock('damien_get_imap_settings', {});
      assert(response.hasOwnProperty('enabled'), 'Should return IMAP settings');
    });
    
    await this.runTest('damien_update_imap_settings works', async () => {
      this.server.mockToolResponse('damien_update_imap_settings', {
        success: true,
        enabled: false
      });
      
      const response = await this.server.invokeToolWithMock('damien_update_imap_settings', {
        enabled: false
      });
      
      assert(response.success === true, 'Should return success');
    });
    
    await this.runTest('damien_get_pop_settings works', async () => {
      this.server.mockToolResponse('damien_get_pop_settings', {
        enabled: false,
        enable_for: 'all_mail'
      });
      
      const response = await this.server.invokeToolWithMock('damien_get_pop_settings', {});
      assert(response.hasOwnProperty('enabled'), 'Should return POP settings');
    });
    
    await this.runTest('damien_update_pop_settings works', async () => {
      this.server.mockToolResponse('damien_update_pop_settings', {
        success: true,
        enabled: true
      });
      
      const response = await this.server.invokeToolWithMock('damien_update_pop_settings', {
        enabled: true,
        enable_for: 'all_mail'
      });
      
      assert(response.success === true, 'Should return success');
    });
    
    // Performance testing
    await this.runTest('Performance meets criteria', async () => {
      await this.runPerformanceTest();
    });
    
    // Final validation - all tools from all phases
    await this.runTest('All 37 tools available in Phase 6', async () => {
      const allTools = [
        // Phase 1
        'damien_list_emails',
        'damien_get_email_details',
        'damien_create_draft',
        'damien_send_draft',
        'damien_list_drafts',
        // Phase 2
        'damien_trash_emails',
        'damien_label_emails',
        'damien_mark_emails',
        'damien_update_draft',
        'damien_delete_draft',
        'damien_get_draft_details',
        'damien_delete_emails_permanently',
        // Phase 3
        'damien_list_threads',
        'damien_get_thread_details',
        'damien_modify_thread_labels',
        'damien_trash_thread',
        'damien_delete_thread_permanently',
        // Phase 4
        'damien_list_rules',
        'damien_get_rule_details',
        'damien_add_rule',
        'damien_delete_rule',
        'damien_apply_rules',
        // Phase 5
        'damien_ai_analyze_emails',
        'damien_ai_suggest_rules',
        'damien_ai_quick_test',
        'damien_ai_create_rule',
        'damien_ai_get_insights',
        'damien_ai_optimize_inbox',
        'damien_ai_analyze_emails_large_scale',
        'damien_ai_analyze_emails_async',
        'damien_job_get_status',
        // Phase 6
        'damien_get_vacation_settings',
        'damien_update_vacation_settings',
        'damien_get_imap_settings',
        'damien_update_imap_settings',
        'damien_get_pop_settings',
        'damien_update_pop_settings'
      ];
      
      await this.verifyToolAvailability(allTools);
      
      const tools = await this.server.getCachedTools();
      assert(tools.length === 37, 'Should have all 37 tools available');
    });
  }
}

module.exports = Phase6Tester;