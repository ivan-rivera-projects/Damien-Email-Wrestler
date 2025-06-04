const assert = require('assert');
const PhaseTestBase = require('./phase-test-base');

class Phase4Tester extends PhaseTestBase {
  constructor() {
    super(4);
    // Combined list of all tools from previous phases
    this.previousPhaseTools = [
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
      'damien_delete_thread_permanently'
    ];
    
    this.phase4Tools = [
      'damien_list_rules',
      'damien_get_rule_details',
      'damien_add_rule',
      'damien_delete_rule',
      'damien_apply_rules'
    ];
  }
  
  async runTests() {
    // Test tool availability
    await this.runTest('All previous phase tools available', async () => {
      await this.verifyToolAvailability(this.previousPhaseTools);
    });
    
    await this.runTest('All Phase 4 tools available', async () => {
      await this.verifyToolAvailability(this.phase4Tools);
    });
    
    // Tool-specific tests for Phase 4
    await this.runTest('damien_list_rules works', async () => {
      this.server.mockToolResponse('damien_list_rules', {
        rules: [
          { id: 'rule1', name: 'Archive Newsletters' },
          { id: 'rule2', name: 'Mark Important' }
        ]
      });
      
      const response = await this.server.invokeToolWithMock('damien_list_rules', {});
      assert(response.rules.length === 2, 'Should return rules');
    });
    
    await this.runTest('damien_get_rule_details works', async () => {
      this.server.mockToolResponse('damien_get_rule_details', {
        id: 'rule1',
        name: 'Archive Newsletters',
        conditions: [
          { field: 'from', operator: 'contains', value: 'newsletter' }
        ],
        actions: [
          { type: 'archive' }
        ]
      });
      
      const response = await this.server.invokeToolWithMock('damien_get_rule_details', {
        rule_id: 'rule1'
      });
      
      assert(response.id === 'rule1', 'Should return rule details');
      assert(response.conditions.length === 1, 'Should return rule conditions');
      assert(response.actions.length === 1, 'Should return rule actions');
    });
    
    await this.runTest('damien_add_rule works', async () => {
      this.server.mockToolResponse('damien_add_rule', {
        success: true,
        rule_id: 'rule3'
      });
      
      const response = await this.server.invokeToolWithMock('damien_add_rule', {
        name: 'New Rule',
        conditions: [
          { field: 'subject', operator: 'contains', value: 'important' }
        ],
        actions: [
          { type: 'label', label: 'Important' }
        ]
      });
      
      assert(response.success === true, 'Should return success');
      assert(response.rule_id === 'rule3', 'Should return new rule ID');
    });
    
    await this.runTest('damien_delete_rule works', async () => {
      this.server.mockToolResponse('damien_delete_rule', {
        success: true,
        rule_id: 'rule1'
      });
      
      const response = await this.server.invokeToolWithMock('damien_delete_rule', {
        rule_id: 'rule1'
      });
      
      assert(response.success === true, 'Should return success');
    });
    
    await this.runTest('damien_apply_rules works', async () => {
      this.server.mockToolResponse('damien_apply_rules', {
        success: true,
        applied_count: 5,
        rule_results: [
          { rule_id: 'rule1', matched_emails: 3 },
          { rule_id: 'rule2', matched_emails: 2 }
        ]
      });
      
      const response = await this.server.invokeToolWithMock('damien_apply_rules', {
        email_ids: ['email1', 'email2', 'email3', 'email4', 'email5']
      });
      
      assert(response.success === true, 'Should return success');
      assert(response.applied_count === 5, 'Should apply to 5 emails');
    });
    
    // Performance testing
    await this.runTest('Performance meets criteria', async () => {
      await this.runPerformanceTest();
    });
  }
}

module.exports = Phase4Tester;