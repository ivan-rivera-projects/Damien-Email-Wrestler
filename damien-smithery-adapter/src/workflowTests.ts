import fetch from 'node-fetch';
import { CONFIG } from './config.js';
import chalk from 'chalk'; // For colorful console output

const SESSION_ID = `test_session_${Date.now()}`;
const SERVER_URL = `http://localhost:${CONFIG.SERVER_PORT}`;
const SAVE_EMAIL_IDS = true;

// Storage for email IDs found during testing to use in subsequent tests
let emailIds: string[] = [];
let ruleIds: string[] = [];

interface EmailSummary {
  id: string;
  thread_id: string;
  [key: string]: any;
}

interface ToolExecutionResult {
  success: boolean;
  data: any;
  result?: any;
  error?: any;
}

interface Rule {
  id: string;
  name: string;
  [key: string]: any;
}

/**
 * Makes a request to the adapter's execute endpoint
 */
async function executeToolRequest(toolName: string, input: any): Promise<ToolExecutionResult> {
  console.log(chalk.blue(`\n=== Executing Tool: ${toolName} ===`));
  console.log(chalk.dim('Input:'), JSON.stringify(input, null, 2));
  
  try {
    const response = await fetch(`${SERVER_URL}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tool: toolName,
        input,
        session_id: SESSION_ID
      })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP error ${response.status}: ${errorText}`);
    }
    
    const result = await response.json() as any;
    
    if (result.is_error) {
      console.log(chalk.red('Tool execution failed:'), result.error_message || 'Unknown error');
      return { success: false, data: null, result };
    }
    
    console.log(chalk.green('Tool execution succeeded!'));
    return { success: true, data: result.output, result };
  } catch (error: any) {
    console.error(chalk.red('Request error:'), error.message);
    return { success: false, data: null, error };
  }
}

/**
 * Run all test workflows
 */
async function runEmailWorkflowTests() {
  console.log(chalk.yellow('\n=========================================='));
  console.log(chalk.yellow('DAMIEN EMAIL MANAGEMENT WORKFLOW TESTING'));
  console.log(chalk.yellow('==========================================\n'));
  console.log(chalk.dim(`Session ID: ${SESSION_ID}`));
  console.log(chalk.dim(`Server URL: ${SERVER_URL}`));
  
  // Test 1: List emails (unread)
  console.log(chalk.cyan('\n📨 TEST 1: List Unread Emails'));
  const unreadEmailsResult = await executeToolRequest('damien_list_emails', {
    query: 'is:unread',
    max_results: 5
  });
  
  if (unreadEmailsResult.success && unreadEmailsResult.data?.email_summaries?.length > 0) {
    console.log(chalk.green(`Found ${unreadEmailsResult.data.email_summaries.length} unread emails`));
    emailIds = unreadEmailsResult.data.email_summaries.map((email: EmailSummary) => email.id);
    console.log(chalk.dim('Email IDs:'), emailIds);
  } else {
    console.log(chalk.yellow('No unread emails found or tool failed. Trying without query...'));
    
    // Fall back to just listing any emails if no unread are found
    const anyEmailsResult = await executeToolRequest('damien_list_emails', {
      max_results: 5
    });
    
    if (anyEmailsResult.success && anyEmailsResult.data?.email_summaries?.length > 0) {
      console.log(chalk.green(`Found ${anyEmailsResult.data.email_summaries.length} emails`));
      emailIds = anyEmailsResult.data.email_summaries.map((email: EmailSummary) => email.id);
      console.log(chalk.dim('Email IDs:'), emailIds);
    } else {
      console.log(chalk.red('No emails found for testing. Some tests will be skipped.'));
    }
  }
  
  // Test 2: Get email details
  if (emailIds.length > 0) {
    console.log(chalk.cyan('\n📩 TEST 2: Get Email Details'));
    const emailDetailsResult = await executeToolRequest('damien_get_email_details', {
      message_id: emailIds[0],
      format: 'full'
    });
    
    if (emailDetailsResult.success) {
      console.log(chalk.green('Successfully retrieved email details'));
      
      if (emailDetailsResult.data?.subject) {
        console.log(chalk.dim('Subject:'), emailDetailsResult.data.subject);
      }
      
      if (emailDetailsResult.data?.snippet) {
        console.log(chalk.dim('Snippet:'), emailDetailsResult.data.snippet);
      }
    }
  }
  
  // Test 3: Mark emails as read (if we have email IDs and at least one was likely unread)
  if (emailIds.length > 0) {
    console.log(chalk.cyan('\n✓ TEST 3: Mark Email as Read'));
    const markReadResult = await executeToolRequest('damien_mark_emails', {
      message_ids: [emailIds[0]],
      mark_as: 'read'
    });
    
    if (markReadResult.success) {
      console.log(chalk.green(`Successfully marked email as read: ${emailIds[0]}`));
    }
  }
  
  // Test 4: Add a label to an email
  if (emailIds.length > 0) {
    console.log(chalk.cyan('\n🏷️ TEST 4: Add Label to Email'));
    const testLabelName = `DAMIEN_TEST_${Date.now()}`;
    const addLabelResult = await executeToolRequest('damien_label_emails', {
      message_ids: [emailIds[0]],
      add_label_names: [testLabelName]
    });
    
    if (addLabelResult.success) {
      console.log(chalk.green(`Successfully added label "${testLabelName}" to email ${emailIds[0]}`));
      
      // Now remove the test label
      console.log(chalk.dim('\nRemoving test label...'));
      const removeLabelResult = await executeToolRequest('damien_label_emails', {
        message_ids: [emailIds[0]],
        remove_label_names: [testLabelName]
      });
      
      if (removeLabelResult.success) {
        console.log(chalk.green(`Successfully removed test label "${testLabelName}"`));
      }
    }
  }
  
  // Test 5: List rules
  console.log(chalk.cyan('\n📋 TEST 5: List Rules'));
  const listRulesResult = await executeToolRequest('damien_list_rules', {});
  
  if (listRulesResult.success) {
    const rulesCount = Array.isArray(listRulesResult.data) ? listRulesResult.data.length : 0;
    console.log(chalk.green(`Successfully retrieved ${rulesCount} rules`));
    
    if (rulesCount > 0) {
      ruleIds = listRulesResult.data.map((rule: Rule) => rule.id);
      console.log(chalk.dim('Rule IDs:'), ruleIds);
    }
  }
  
  // Test 6: Add a new rule
  console.log(chalk.cyan('\n➕ TEST 6: Add New Rule'));
  const testRuleName = `Test Rule ${Date.now()}`;
  const addRuleResult = await executeToolRequest('damien_add_rule', {
    rule_definition: {
      name: testRuleName,
      description: "Test rule created by Damien Smithery adapter test script",
      is_enabled: true,
      conditions: [
        {
          field: "subject",
          operator: "contains",
          value: "TEST_RULE_SUBJECT_NEVER_MATCH"
        }
      ],
      condition_conjunction: "AND",
      actions: [
        {
          type: "add_label",
          parameters: {
            label_name: "TEST_LABEL"
          }
        }
      ]
    }
  });
  
  let testRuleId = null;
  if (addRuleResult.success) {
    testRuleId = addRuleResult.data?.id;
    console.log(chalk.green(`Successfully added test rule "${testRuleName}" with ID: ${testRuleId}`));
  }
  
  // Test 7: Apply rules
  console.log(chalk.cyan('\n▶️ TEST 7: Apply Rules'));
  const applyRulesResult = await executeToolRequest('damien_apply_rules', {
    dry_run: true,
    scan_limit: 10
  });
  
  if (applyRulesResult.success) {
    console.log(chalk.green('Successfully ran rules in dry-run mode'));
    console.log(chalk.dim('Total messages scanned:'), applyRulesResult.data?.total_messages_scanned || 0);
    console.log(chalk.dim('Total rules evaluated:'), applyRulesResult.data?.total_rules_evaluated || 0);
  }
  
  // Test 8: Delete the test rule we created
  if (testRuleId) {
    console.log(chalk.cyan('\n❌ TEST 8: Delete Test Rule'));
    const deleteRuleResult = await executeToolRequest('damien_delete_rule', {
      rule_identifier: testRuleId
    });
    
    if (deleteRuleResult.success) {
      console.log(chalk.green(`Successfully deleted test rule "${testRuleName}"`));
    }
  }
  
  // Test 9: Move an email to trash (don't use the first email ID as we've already tested with it)
  if (emailIds.length > 1) {
    const emailToTrash = emailIds[1];
    console.log(chalk.cyan(`\n🗑️ TEST 9: Move Email to Trash (ID: ${emailToTrash})`));
    const trashEmailResult = await executeToolRequest('damien_trash_emails', {
      message_ids: [emailToTrash]
    });
    
    if (trashEmailResult.success) {
      console.log(chalk.green(`Successfully moved email ${emailToTrash} to trash`));
    }
  }
  
  console.log(chalk.yellow('\n=========================================='));
  console.log(chalk.green('✨ All tests completed!'));
  console.log(chalk.yellow('==========================================\n'));
}

// Only run if executed directly (not imported)
if (require.main === module) {
  runEmailWorkflowTests()
    .catch(error => console.error(chalk.red('Test error:'), error))
    .finally(() => console.log(chalk.blue('\nWorkflow testing complete.')));
}

export { runEmailWorkflowTests };
