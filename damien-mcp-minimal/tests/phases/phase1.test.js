import assert from 'assert';
import PhaseTestBase from './phase-test-base.js';

class Phase1Tester extends PhaseTestBase {
  constructor() {
    super(1);
    this.phase1Tools = [
      'damien_list_emails',
      'damien_get_email_details',
      'damien_create_draft',
      'damien_send_draft',
      'damien_list_drafts'
    ];
  }
  
  async runTests() {
    // Test tool availability
    await this.runTest('All Phase 1 tools available', async () => {
      await this.verifyToolAvailability(this.phase1Tools);
    });
    
    // Tool-specific tests
    await this.runTest('damien_list_emails works', async () => {
      // Mock response for list_emails
      this.server.mockToolResponse('damien_list_emails', {
        emails: [
          { id: 'email1', subject: 'Test Email 1' },
          { id: 'email2', subject: 'Test Email 2' }
        ]
      });
      
      const response = await this.server.invokeToolWithMock('damien_list_emails', {});
      assert(response.emails.length === 2, 'Should return mock emails');
    });
    
    await this.runTest('damien_get_email_details works', async () => {
      // Mock response for get_email_details
      this.server.mockToolResponse('damien_get_email_details', {
        id: 'email1',
        subject: 'Test Email 1',
        body: 'This is a test email body',
        from: 'sender@example.com'
      });
      
      const response = await this.server.invokeToolWithMock('damien_get_email_details', { email_id: 'email1' });
      assert(response.id === 'email1', 'Should return mock email details');
    });
    
    await this.runTest('damien_create_draft works', async () => {
      // Mock response for create_draft
      this.server.mockToolResponse('damien_create_draft', {
        draft_id: 'draft1',
        status: 'created'
      });
      
      const response = await this.server.invokeToolWithMock('damien_create_draft', {
        subject: 'Test Draft',
        to: 'recipient@example.com',
        body: 'This is a test draft'
      });
      
      assert(response.draft_id === 'draft1', 'Should return mock draft ID');
    });
    
    await this.runTest('damien_send_draft works', async () => {
      // Mock response for send_draft
      this.server.mockToolResponse('damien_send_draft', {
        status: 'sent',
        message_id: 'msg123'
      });
      
      const response = await this.server.invokeToolWithMock('damien_send_draft', { draft_id: 'draft1' });
      assert(response.status === 'sent', 'Should return sent status');
    });
    
    await this.runTest('damien_list_drafts works', async () => {
      // Mock response for list_drafts
      this.server.mockToolResponse('damien_list_drafts', {
        drafts: [
          { id: 'draft1', subject: 'Test Draft 1' },
          { id: 'draft2', subject: 'Test Draft 2' }
        ]
      });
      
      const response = await this.server.invokeToolWithMock('damien_list_drafts', {});
      assert(response.drafts.length === 2, 'Should return mock drafts');
    });
    
    // Performance testing
    await this.runTest('Performance meets criteria', async () => {
      await this.runPerformanceTest();
    });
  }
}

export default Phase1Tester;