#!/usr/bin/env node

/**
 * GitHub Issue Creator for Damien Platform
 * 
 * This script reads bugs from known_bugs_to_correct.md and creates
 * GitHub issues using the GitHub CLI (gh).
 * 
 * Usage: node create-github-issues.js
 * 
 * Prerequisites:
 * - GitHub CLI (gh) installed and authenticated
 * - Node.js 14+
 * - Read access to known_bugs_to_correct.md
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const REPO = 'ivan-rivera-projects/Damien-Email-Wrestler';
const BUGS_FILE = path.join(__dirname, '../known_bugs_to_correct.md');

// Define all issues to create
const ISSUES = [
  {
    title: 'Script Misidentification: damien-work-start.sh Restarts Claude Desktop, Not Claude Code',
    body: `## Problem
The \`damien-work-start.sh\` script contains misleading comments claiming it restarts "Claude Code," but the actual implementation restarts **Claude Desktop** instead.

## Current Behavior
- Lines 73-74 execute: \`osascript -e 'quit app "Claude"'\` and \`open -a "Claude" "$PROJECT_ROOT"\`
- The macOS app identifier \`"Claude"\` resolves to **Claude Desktop** (native macOS application)
- Script comments (Line 59) state: "Step 3: Restarting Claude Code"
- User expectations misaligned with actual behavior

## Root Cause
Two different Claude applications exist:
- **Claude Desktop** - Native macOS app with MCP server support (what's actually being restarted)
- **Claude Code** - Terminal-based command-line tool (\`claude\` command)

## Impact
- Developer confusion about which Claude application is being used
- Misleading setup/onboarding experience
- Potential workflow disruptions

## Files Affected
- \`/scripts/damien-work-start.sh\` - Lines 59, 73-74, 85

## Proposed Solution (Immediate)
Update comments to reference "Claude Desktop" with clear explanation of why it's preferred (MCP server support).

## Proposed Solution (Long-term)
Add configuration option to choose between Claude Desktop or Claude Code, with separate documentation for each use case.`,
    labels: ['bug', 'critical', 'type:documentation', 'type:logic']
  },
  {
    title: 'damien_ai_bulk_operations: Tool Fails with Silent Error on Dry-Run',
    body: `## Problem
The \`damien_ai_bulk_operations\` tool fails silently when attempting a dry-run preview with generic error message.

## Error Details
\`\`\`
Error: "No result received from client-side tool execution"
\`\`\`

## Test Case
\`\`\`javascript
Tool: damien_ai_bulk_operations
Parameters:
  - dry_run: true
  - job_id: task_1815f1b4
  - max_emails: 500
  - min_confidence: 0.75
  - operation: trash
  - pattern_filter: ["newsletter_subscriptions"]

Result: Error (no data returned)
\`\`\`

## Expected Behavior
- Should return preview of emails that would be affected
- Should show dry-run results with counts and confidence scores
- Should allow user to review before executing

## Actual Behavior
- Tool execution fails silently
- No result data returned to client
- Error message is generic with no debugging information

## Root Causes (Potential)
1. Job ID format or state mismatch
2. Pattern filter parameter not properly serialized
3. Client-side MCP handler timeout or crash
4. Incompatibility between async job results and bulk operations tool

## Impact
- Cannot preview bulk operations before execution
- Reduces user confidence in destructive operations
- Forces use of workaround tools (not optimal)

## Recommended Resolution
1. Add comprehensive error logging
2. Validate job_id format and state before processing
3. Add parameter validation for pattern_filter array
4. Return detailed error messages instead of generic failures
5. Add timeout configuration for long-running operations
6. Test integration between async analysis and bulk operations`,
    labels: ['bug', 'high', 'type:tool-failure', 'needs-investigation']
  },
  {
    title: 'damien_smart_trash_marketing: Silent Failure with Historical Emails',
    body: `## Problem
The \`damien_smart_trash_marketing\` tool exhibits inconsistent behavior - works for recent emails but fails silently for older emails (6+ years old).

## Evidence

### Working Cases ✅
- September 2025: 269 emails trashed successfully (90.2% confidence)
- October 2025: 129 emails trashed successfully (90.4% confidence)

### Failing Case ❌
- October 2019: Analysis found 621 emails, trash operation returned 0 emails processed
- No error message provided
- Job status shows "completed" despite no action taken

## Test Case (Reproducer)
\`\`\`javascript
Tool: damien_smart_trash_marketing
Parameters:
  - days: 31
  - dry_run: false
  - max_emails: 1000
  - min_confidence: 0.75
  - query: "after:2019-10-01 before:2019-11-01"

Result:
  - total_analyzed: 0
  - emails_trashed: 0
  - patterns_detected: []
\`\`\`

## Expected Behavior
- Should trash 621 emails detected as marketing
- Should return accurate count of emails processed
- Should work consistently regardless of email age

## Actual Behavior
- Returns success status with 0 emails processed
- Analysis phase works correctly
- Trash execution phase fails silently
- Silent failure = data integrity risk

## Root Causes (Potential)
1. Gmail API pagination issue with older emails
2. Email ID format incompatibility with messages older than 1-2 years
3. API rate limiting or timeout on large historical operations
4. Date-range filtering not working for older emails
5. Trash operation doesn't validate email existence before processing

## Impact
- Cannot reliably clean up marketing emails from historical periods
- Users may believe cleanup succeeded when it actually failed
- Reduces trust in automation for large-scale operations
- Data integrity concerns

## Recommended Resolution
1. Add explicit error handling for zero-result cases
2. Validate email IDs before trash operation
3. Implement pagination for large result sets
4. Add retry logic with exponential backoff
5. Log detailed information about failed attempts
6. Return actionable error messages instead of silent failures

## Testing Required
- Test with emails from 2015-2020 range
- Test with various batch sizes (100, 500, 1000+)
- Test different date ranges
- Monitor Gmail API rate limits
- Verify email ID format consistency`,
    labels: ['bug', 'high', 'type:tool-failure', 'data-integrity', 'needs-investigation']
  },
  {
    title: 'Email Body Content Not Retrieved: damien_get_email_details Returns Empty Text and HTML',
    body: `## Problem
When retrieving full email details, the email body content (both text and HTML) is returned as empty strings despite emails having actual content.

## Evidence
\`\`\`json
"body": {
  "text": "",
  "html": ""
}
\`\`\`

## Test Case
- Email ID: \`19a29995846254b4\` (Meta Blueprint marketing email)
- Email ID: \`19a296fa1e8ab295\` (BoF Daily Digest newsletter)
- Both returned empty body content despite having subject lines and headers

## Expected Behavior
- Should return parsed email body content (both text and HTML versions)
- Should enable content-based email analysis
- Should support advanced content filtering

## Actual Behavior
- Body fields always empty
- Forces reliance on headers/subject for analysis only
- Limits advanced filtering capabilities

## Root Causes (Potential)
1. MIME multipart parsing not extracting message parts
2. Content encoding issue (charset, gzip, etc.)
3. Permission restrictions on reading full message content
4. API format specification mismatch

## Impact
- Content-based email analysis is less effective
- Spam/marketing detection relies only on headers and sender
- Cannot perform advanced content filtering
- Reduces accuracy of AI pattern detection

## Recommended Resolution
1. Implement proper MIME multipart parsing
2. Handle content encoding/decoding
3. Support both text and HTML body extraction
4. Add fallback to plaintext conversion for HTML-only emails
5. Test with various email formats

## Testing Required
- Test with various email types (HTML-only, multipart, text-only)
- Test with different character encodings
- Verify MIME boundary parsing
- Compare against Gmail API raw message retrieval`,
    labels: ['bug', 'medium', 'type:data-retrieval', 'needs-investigation']
  },
  {
    title: 'Pattern Coverage Metric Exceeds 100%: Metric Labeling and Calculation Issue',
    body: `## Problem
Analysis results report a "pattern_coverage_percentage" of 128.1%, which is mathematically impossible for a coverage metric (should max at 100%).

## Evidence
\`\`\`json
{
  "emails_analyzed": 392,
  "emails_with_patterns": 502,
  "pattern_coverage_percentage": 128.1
}
\`\`\`

## Analysis
- Emails analyzed: 392
- Emails with patterns: 502
- Reported coverage: 502 / 392 = 128.06% ✗

## Root Cause
The metric calculation treats each pattern match independently. An email matching multiple patterns is counted multiple times, but the metric is labeled as "coverage_percentage" which implies a single-valued metric.

## Expected Behavior
- Metric should be clearly labeled as "pattern_match_rate" or "average_patterns_per_email"
- Should clarify that emails can match multiple patterns
- Should show individual pattern coverage separately

## Actual Behavior
- Metric labeled as "coverage_percentage" (misleading)
- Value exceeds 100% (violates convention)
- Could confuse stakeholders about analysis comprehensiveness

## Impact
- Confusing metric reporting
- Could mislead stakeholders about analysis comprehensiveness
- Violates standard metric conventions (percentages max at 100%)
- Reduces trust in analysis results

## Recommended Resolution
1. Rename metric to "pattern_match_rate_percentage" or "average_patterns_per_email"
2. Add documentation explaining the calculation
3. Add separate metrics for:
   - Emails with at least one pattern (coverage_percentage)
   - Average patterns per email
   - Individual pattern distribution
4. Add data validation to catch metrics exceeding 100%`,
    labels: ['bug', 'medium', 'type:metric', 'type:documentation']
  },
  {
    title: 'Redundant API Usage Guidance Messages in Every Tool Response',
    body: `## Problem
Every Damien tool response includes a repetitive \`_api_usage_guidance\` section containing identical guidance.

## Evidence
\`\`\`json
"_api_usage_guidance": {
  "message": "For optimal performance, use direct MCP tools instead of API endpoints",
  "recommendation": "Use 'damien_get_email_details' tool directly for optimal performance",
  "policy": "direct_mcp_preferred"
}
\`\`\`

## Issues
- Appears in every response (dozens of times in a session)
- Same message repeated verbatim
- Clutters response output
- Violates DRY (Don't Repeat Yourself) principle
- No additional value after first mention

## Expected Behavior
- Guidance shown once during session initialization
- Removed from individual tool responses
- Could be available in verbose/debug mode only

## Impact
- Increases response size and complexity
- Makes logs harder to read
- No useful information after initial display
- Reduces signal-to-noise ratio

## Recommended Resolution
1. Show guidance only on first tool call of session
2. Add \`--verbose\` flag to include in all responses when needed
3. Move to session initialization message
4. Cache and suppress duplicate messages`,
    labels: ['enhancement', 'low', 'type:output-quality']
  },
  {
    title: 'Improve MCP Integration Documentation and Troubleshooting Guide',
    body: `## Problem
Lack of comprehensive documentation for MCP integration, debugging, and troubleshooting creates friction for developers.

## Current Issues
- MCP integration points not clearly documented
- No troubleshooting guide for common errors
- Session logging insufficient for debugging
- No tool capability matrix/reference

## Proposed Documentation
1. **MCP Integration Points**
   - Document which tools use MCP
   - Explain MCP authentication flow
   - Document tool availability and requirements

2. **Troubleshooting Guide**
   - Common error messages and solutions
   - Debug mode instructions
   - How to enable verbose logging

3. **Session Logging**
   - Add comprehensive session logging
   - Include timestamps and error details
   - Make logs accessible for debugging

4. **Tool Capability Matrix**
   - Document what each tool can do
   - List parameters and options
   - Show real examples of tool usage

## Files to Create
- \`docs/MCP_INTEGRATION.md\`
- \`docs/TROUBLESHOOTING.md\`
- \`docs/TOOL_REFERENCE.md\`

## Impact
- Reduces onboarding time
- Faster debugging and issue resolution
- Better developer experience`,
    labels: ['documentation', 'low', 'type:docs', 'enhancement']
  }
];

/**
 * Helper function to run shell commands
 */
function runCommand(command) {
  try {
    const output = execSync(command, { encoding: 'utf8' });
    return { success: true, output };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Create a single GitHub issue using gh CLI
 */
function createIssue(issue) {
  console.log(`\n📝 Creating: "${issue.title}"`);
  
  // Build the gh command
  const labelFlags = issue.labels.map(l => `--label "${l}"`).join(' ');
  
  // Escape the body for shell - using temp file approach is safer
  const tempFile = `/tmp/issue-body-${Date.now()}.txt`;
  fs.writeFileSync(tempFile, issue.body);
  
  const command = `gh issue create --title "${issue.title.replace(/"/g, '\\"')}" --body "$(cat ${tempFile})" ${labelFlags} --repo ${REPO}`;
  
  const result = runCommand(command);
  
  // Clean up temp file
  try {
    fs.unlinkSync(tempFile);
  } catch (e) {
    // Ignore cleanup errors
  }
  
  if (result.success) {
    // Extract issue number from output
    // gh returns: https://github.com/owner/repo/issues/123
    const urlMatch = result.output.match(/\/issues\/(\d+)/);
    const hashMatch = result.output.match(/#(\d+)/);
    const issueNumber = urlMatch ? urlMatch[1] : (hashMatch ? hashMatch[1] : 'unknown');
    console.log(`   ✅ Created successfully: #${issueNumber}`);
    return { success: true, issueNumber };
  } else {
    console.error(`   ❌ Failed: ${result.error}`);
    return { success: false, error: result.error };
  }
}

/**
 * Main function
 */
async function main() {
  console.log('╔═══════════════════════════════════════════════════════════╗');
  console.log('║  GitHub Issue Creator - Damien Platform                  ║');
  console.log('║  Creating issues from known_bugs_to_correct.md            ║');
  console.log('╚═══════════════════════════════════════════════════════════╝');
  
  // Verify file exists
  if (!fs.existsSync(BUGS_FILE)) {
    console.error(`\n❌ Error: ${BUGS_FILE} not found`);
    process.exit(1);
  }
  console.log(`\n📖 Reading bugs from: ${BUGS_FILE}`);
  
  // Verify gh CLI is available
  const ghCheck = runCommand('gh auth status');
  if (!ghCheck.success) {
    console.error('\n❌ Error: GitHub CLI (gh) not found or not authenticated');
    console.error('Install gh: https://cli.github.com/');
    console.error('Authenticate: gh auth login');
    process.exit(1);
  }
  console.log('✅ GitHub CLI authenticated and ready');
  
  console.log(`\n🎯 Target Repository: ${REPO}`);
  console.log(`📊 Issues to Create: ${ISSUES.length}`);
  
  // Create each issue
  const results = [];
  for (const issue of ISSUES) {
    const result = createIssue(issue);
    results.push(result);
  }
  
  // Summary
  console.log('\n╔═══════════════════════════════════════════════════════════╗');
  console.log('║  CREATION SUMMARY                                         ║');
  console.log('╚═══════════════════════════════════════════════════════════╝');
  
  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log(`\n✅ Successful: ${successful}/${ISSUES.length}`);
  console.log(`❌ Failed: ${failed}/${ISSUES.length}`);
  
  if (failed === 0) {
    console.log('\n🎉 All issues created successfully!');
    console.log(`\nView them at: https://github.com/${REPO}/issues`);
  } else {
    console.log('\n⚠️  Some issues failed to create. Check the output above.');
    process.exit(1);
  }
}

// Run the script
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
