const assert = require('assert');
const PhaseTestBase = require('./phase-test-base');

class Phase2Tester extends PhaseTestBase {
  constructor() {
    super(2);
    this.phase1Tools = [
      'damien_list_emails',
      'damien_get_email_details',
      'damien_create_draft',
      'damien_send_draft',
      'damien_list_drafts'
    ];
    this.phase2Tools = [
      'damien_trash_emails',
      'damien_label_emails',
      'damien_mark_emails',
      'damien_update_draft',
      'damien_delete_draft',
      'damien_get_draft_details',
      'damien_delete_emails_permanently'
    ];
  }
  
  async runTests() {
    // Test tool availability
    await this.runTest('All Phase 1 tools available', async () => {
      await this.verifyToolAvailability(this.phase1Tools);
    });
    
    await this.runTest('All Phase 2 tools available', async () => {
      await this.verifyToolAvailability(this.phase2Tools);
    });
    
    // Tool-specific tests for Phase 2
    await this.runTest('damien_trash_emails works', async () => {
      this.server.mockToolResponse('damien_trash_emails', {
        success: true,
        trashed_count: 2
      });
      
      const response = await this.server.invokeToolWithMock('damien_trash_emails', {
        email_ids: ['email1', 'email2']
      });
      
      assert(response.success === true, 'Should return success');
      assert(response.trashed_count === 2, 'Should trash 2 emails');
    });
    
    await this.runTest('damien_label_emails works', async () => {
      this.server.mockToolResponse('damien_label_emails', {
        success: true,
        labeled_count: 2
      });
      
      const response = await this.server.invokeToolWithMock('damien_label_emails', {
        email_ids: ['email1', 'email2'],
        label: 'Important'
      });
      
      assert(response.success === true, 'Should return success');
      assert(response.labeled_count === 2, 'Should label 2 emails');
    });
    
    await this.runTest('damien_mark_emails works', async () => {
      this.server.mockToolResponse('damien_mark_emails', {
        success: true,
        marked_count: 2
      });
      
      const response = await this.server.invokeToolWithMock('damien_mark_emails', {
        email_ids: ['email1', 'email2'],
        read: true
      });
      
      assert(response.success === true, 'Should return success');
      assert(response.marked_count === 2, 'Should mark 2 emails');
    });
    
    await this.runTest('damien_update_draft works', async () => {
      this.server.mockToolResponse('damien_update_draft', {
        success: true,
        draft_id: 'draft1'
      });
      
      const response = await this.server.invokeToolWithMock('damien_update_draft', {
        draft_id: 'draft1',
        subject: 'Updated Subject'
      });
      
      assert(response.success === true, 'Should return success');
    });
    
    await this.runTest('damien_delete_draft works', async () => {
      this.server.mockToolResponse('damien_delete_draft', {
        success: true,
        draft_id: 'draft1'
      });
      
      const response = await this.server.invokeToolWithMock('damien_delete_draft', {
        draft_id: 'draft1'
      });
      
      assert(response.success === true, 'Should return success');
    });
    
    await this.runTest('damien_get_draft_details works', async () => {
      this.server.mockToolResponse('damien_get_draft_details', {
        id: 'draft1',
        subject: 'Test Draft',
        to: 'recipient@example.com',
        body: 'This is a test draft'
      });
      
      const response = await this.server.invokeToolWithMock('damien_get_draft_details', {
        draft_id: 'draft1'
      });
      
      assert(response.id === 'draft1', 'Should return draft details');
    });
    
    await this.runTest('damien_delete_emails_permanently works', async () => {
      this.server.mockToolResponse('damien_delete_emails_permanently', {
        success: true,
        deleted_count: 2
      });
      
      const response = await this.server.invokeToolWithMock('damien_delete_emails_permanently', {
        email_ids: ['email1', 'email2']
      });
      
      assert(response.success === true, 'Should return success');
      assert(response.deleted_count === 2, 'Should delete 2 emails');
    });
    
    // Performance testing
    await this.runTest('Performance meets criteria', async () => {
      await this.runPerformanceTest();
    });
  }
}

module.exports = Phase2Tester;