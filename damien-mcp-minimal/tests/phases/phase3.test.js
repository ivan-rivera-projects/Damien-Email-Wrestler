const assert = require('assert');
const PhaseTestBase = require('./phase-test-base');

class Phase3Tester extends PhaseTestBase {
  constructor() {
    super(3);
    this.previousPhaseTools = [
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
      'damien_delete_emails_permanently'
    ];
    this.phase3Tools = [
      'damien_list_threads',
      'damien_get_thread_details',
      'damien_modify_thread_labels',
      'damien_trash_thread',
      'damien_delete_thread_permanently'
    ];
  }
  
  async runTests() {
    // Test tool availability
    await this.runTest('All previous phase tools available', async () => {
      await this.verifyToolAvailability(this.previousPhaseTools);
    });
    
    await this.runTest('All Phase 3 tools available', async () => {
      await this.verifyToolAvailability(this.phase3Tools);
    });
    
    // Tool-specific tests for Phase 3
    await this.runTest('damien_list_threads works', async () => {
      this.server.mockToolResponse('damien_list_threads', {
        threads: [
          { id: 'thread1', subject: 'Thread 1', message_count: 3 },
          { id: 'thread2', subject: 'Thread 2', message_count: 2 }
        ]
      });
      
      const response = await this.server.invokeToolWithMock('damien_list_threads', {});
      assert(response.threads.length === 2, 'Should return threads');
    });
    
    await this.runTest('damien_get_thread_details works', async () => {
      this.server.mockToolResponse('damien_get_thread_details', {
        id: 'thread1',
        subject: 'Thread 1',
        messages: [
          { id: 'msg1', subject: 'Message 1' },
          { id: 'msg2', subject: 'Message 2' },
          { id: 'msg3', subject: 'Message 3' }
        ]
      });
      
      const response = await this.server.invokeToolWithMock('damien_get_thread_details', {
        thread_id: 'thread1'
      });
      
      assert(response.id === 'thread1', 'Should return thread details');
      assert(response.messages.length === 3, 'Should return thread messages');
    });
    
    await this.runTest('damien_modify_thread_labels works', async () => {
      this.server.mockToolResponse('damien_modify_thread_labels', {
        success: true,
        thread_id: 'thread1',
        added_labels: ['Important'],
        removed_labels: ['Pending']
      });
      
      const response = await this.server.invokeToolWithMock('damien_modify_thread_labels', {
        thread_id: 'thread1',
        add_labels: ['Important'],
        remove_labels: ['Pending']
      });
      
      assert(response.success === true, 'Should return success');
    });
    
    await this.runTest('damien_trash_thread works', async () => {
      this.server.mockToolResponse('damien_trash_thread', {
        success: true,
        thread_id: 'thread1'
      });
      
      const response = await this.server.invokeToolWithMock('damien_trash_thread', {
        thread_id: 'thread1'
      });
      
      assert(response.success === true, 'Should return success');
    });
    
    await this.runTest('damien_delete_thread_permanently works', async () => {
      this.server.mockToolResponse('damien_delete_thread_permanently', {
        success: true,
        thread_id: 'thread1'
      });
      
      const response = await this.server.invokeToolWithMock('damien_delete_thread_permanently', {
        thread_id: 'thread1'
      });
      
      assert(response.success === true, 'Should return success');
    });
    
    // Performance testing
    await this.runTest('Performance meets criteria', async () => {
      await this.runPerformanceTest();
    });
  }
}

module.exports = Phase3Tester;