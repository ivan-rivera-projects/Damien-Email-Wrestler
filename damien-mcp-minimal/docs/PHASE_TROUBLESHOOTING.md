# Phase Troubleshooting Guide

This document provides detailed troubleshooting information for issues that may arise during phase expansion of the Damien MCP Minimal Server.

## Common Issues Across All Phases

Before diving into phase-specific issues, check these common problems:

1. **Server Not Starting**:
   - Check for port conflicts
   - Verify environment variables in `.env`
   - Check logs for startup errors
   - Ensure Node.js version is 18+

2. **Tool Not Available**:
   - Verify tool is included in the current phase
   - Check backend server is running
   - Verify API key is correct
   - Check for network connectivity issues

3. **Claude Desktop Connectivity**:
   - Verify Claude Desktop configuration has correct MCP URL
   - Check that minimal server is running
   - Restart Claude Desktop after configuration changes

4. **Performance Issues**:
   - Check for high CPU or memory usage
   - Verify cache is working correctly
   - Look for slow network connections
   - Check backend response times

## Phase 1 Troubleshooting

### `damien_list_emails` Issues

**Symptom**: No emails are returned or request times out.

**Possible Causes and Solutions**:
- **Backend Connectivity**: Verify backend is reachable with `curl http://localhost:8892/health`
- **Authentication**: Check API key in configuration
- **Pagination**: Try limiting request size with `limit` parameter
- **Caching**: Clear cache by restarting server

**Common Error Messages**:
- `Error fetching emails: Request timeout after 30000ms`
  - Increase timeout in configuration or optimize backend query
- `Error fetching emails: Invalid authentication`
  - Check API key in configuration

### `damien_get_email_details` Issues

**Symptom**: Cannot retrieve email details or incomplete information.

**Possible Causes and Solutions**:
- **Invalid Email ID**: Verify email ID is correct
- **Permission Issues**: Check if email is accessible
- **Attachment Handling**: Large attachments may cause timeouts

**Common Error Messages**:
- `Error fetching email details: Email not found`
  - Verify email ID and that email exists
- `Error fetching email details: Request timeout`
  - Consider using minimal format parameter

### `damien_create_draft` Issues

**Symptom**: Draft creation fails or drafts not saved.

**Possible Causes and Solutions**:
- **Validation Errors**: Check email format, recipient addresses
- **Attachment Size**: Large attachments may cause issues
- **Authentication**: Verify correct API key

**Common Error Messages**:
- `Error creating draft: Invalid recipient format`
  - Check email address format
- `Error creating draft: Attachment too large`
  - Reduce attachment size or split into multiple emails

### `damien_send_draft` Issues

**Symptom**: Cannot send draft or draft not found.

**Possible Causes and Solutions**:
- **Draft ID Invalid**: Verify draft exists and ID is correct
- **Backend Connectivity**: Check connection to backend server
- **Quota Issues**: Email sending quotas may be exceeded

**Common Error Messages**:
- `Error sending draft: Draft not found`
  - Verify draft ID and existence
- `Error sending draft: Quota exceeded`
  - Wait and try again later

### `damien_list_drafts` Issues

**Symptom**: No drafts listed or incorrect drafts shown.

**Possible Causes and Solutions**:
- **Caching**: Restart server to clear cache
- **Query Parameters**: Check filtering parameters
- **Authentication**: Verify correct API key

**Common Error Messages**:
- `Error listing drafts: Invalid query parameters`
  - Check query parameters format

## Phase 2 Troubleshooting

### `damien_trash_emails` Issues

**Symptom**: Emails not moved to trash or operation fails.

**Possible Causes and Solutions**:
- **Permission Issues**: Check if operation is allowed
- **Invalid Email IDs**: Verify all email IDs exist
- **Batch Size**: Try with smaller batch of emails

**Common Error Messages**:
- `Error trashing emails: Operation not permitted`
  - Check permissions and API scopes
- `Error trashing emails: Some emails not found`
  - Verify all email IDs exist

### `damien_label_emails` Issues

**Symptom**: Labels not applied or removed correctly.

**Possible Causes and Solutions**:
- **Label Format**: Ensure label name is valid
- **Label Existence**: Verify label exists for removal
- **Batch Operation**: Try with smaller batch of emails

**Common Error Messages**:
- `Error applying label: Invalid label format`
  - Check label name format
- `Error applying label: Label not found`
  - Create label first if it doesn't exist

### `damien_mark_emails` Issues

**Symptom**: Read/unread status not updated.

**Possible Causes and Solutions**:
- **Permission Issues**: Check if operation is allowed
- **Invalid Email IDs**: Verify all email IDs exist
- **Status Conflict**: Check current status before updating

**Common Error Messages**:
- `Error marking emails: Operation not permitted`
  - Check permissions and API scopes

### `damien_update_draft` Issues

**Symptom**: Draft not updated or update incomplete.

**Possible Causes and Solutions**:
- **Draft ID Invalid**: Verify draft exists and ID is correct
- **Field Validation**: Check format of updated fields
- **Concurrency**: Check if draft was modified elsewhere

**Common Error Messages**:
- `Error updating draft: Draft not found`
  - Verify draft ID and existence
- `Error updating draft: Invalid field format`
  - Check format of fields being updated

### `damien_delete_draft` Issues

**Symptom**: Draft not deleted or operation fails.

**Possible Causes and Solutions**:
- **Draft ID Invalid**: Verify draft exists and ID is correct
- **Permission Issues**: Check if operation is allowed
- **Backend Connectivity**: Verify connection to backend

**Common Error Messages**:
- `Error deleting draft: Draft not found`
  - Verify draft ID and existence
- `Error deleting draft: Operation not permitted`
  - Check permissions and API scopes

### `damien_get_draft_details` Issues

**Symptom**: Cannot retrieve draft details or incomplete information.

**Possible Causes and Solutions**:
- **Draft ID Invalid**: Verify draft exists and ID is correct
- **Permission Issues**: Check if draft is accessible
- **Attachment Handling**: Large attachments may cause timeouts

**Common Error Messages**:
- `Error fetching draft details: Draft not found`
  - Verify draft ID and that draft exists

### `damien_delete_emails_permanently` Issues

**Symptom**: Emails not deleted or operation fails.

**Possible Causes and Solutions**:
- **Permission Issues**: Check if operation is allowed
- **Invalid Email IDs**: Verify all email IDs exist
- **Email State**: Emails might need to be in trash first

**Common Error Messages**:
- `Error deleting emails: Operation not permitted`
  - Check permissions and API scopes
- `Error deleting emails: Some emails not found`
  - Verify all email IDs exist

## Phase 3 Troubleshooting

### Thread Management Issues

**Symptom**: Thread operations fail or return unexpected results.

**Possible Causes and Solutions**:
- **Thread ID Invalid**: Verify thread exists and ID is correct
- **Thread Size**: Large threads may cause performance issues
- **Thread State**: Some operations require specific thread states

**Common Error Messages**:
- `Error processing thread: Thread not found`
  - Verify thread ID and existence
- `Error processing thread: Thread too large`
  - Try with individual messages instead of whole thread

## Phase 4 Troubleshooting

### Rule Management Issues

**Symptom**: Rules not applied correctly or rule operations fail.

**Possible Causes and Solutions**:
- **Rule Syntax**: Check rule format and syntax
- **Rule Complexity**: Simplify complex rules
- **Rule Conflicts**: Check for conflicting rules
- **Backend Support**: Verify backend supports all rule features

**Common Error Messages**:
- `Error creating rule: Invalid rule syntax`
  - Check rule format and syntax
- `Error applying rules: Rule conflict detected`
  - Resolve conflicts between rules

## Phase 5 Troubleshooting

### AI Features Issues

**Symptom**: AI operations fail or produce unexpected results.

**Possible Causes and Solutions**:
- **Input Size**: Check size of email set for analysis
- **Backend Capability**: Verify backend supports AI features
- **Resource Constraints**: AI operations require more resources
- **Async Operation**: Some operations need to be tracked asynchronously

**Common Error Messages**:
- `Error in AI analysis: Input too large`
  - Reduce number of emails or use large-scale variant
- `Error in AI analysis: Operation timeout`
  - Consider using async variant for large operations

### Async Operations Issues

**Symptom**: Background jobs not completing or status not updating.

**Possible Causes and Solutions**:
- **Job Tracking**: Verify job ID is correct
- **Backend Resources**: Check if backend has sufficient resources
- **Job Timeout**: Long-running jobs may have timeouts
- **Job Status**: Check job status before accessing results

**Common Error Messages**:
- `Error tracking job: Job not found`
  - Verify job ID and existence
- `Error retrieving results: Job still running`
  - Wait for job completion before accessing results

## Phase 6 Troubleshooting

### Account Settings Issues

**Symptom**: Settings not retrieved or updated correctly.

**Possible Causes and Solutions**:
- **Permission Issues**: Check if operation is allowed
- **Setting Validation**: Verify setting format and values
- **Setting Dependencies**: Some settings have dependencies
- **Backend Support**: Verify backend supports all settings

**Common Error Messages**:
- `Error updating settings: Invalid setting value`
  - Check setting format and valid values
- `Error updating settings: Operation not permitted`
  - Check permissions and API scopes

## Advanced Troubleshooting

### Diagnosing Performance Issues

To diagnose performance issues:

1. **Enable Verbose Logging**:
   ```bash
   # In .env file
   VERBOSE_LOGGING=true
   ```

2. **Run Performance Benchmark**:
   ```bash
   npm run benchmark
   ```

3. **Check Memory Usage**:
   ```bash
   # Run with Node.js memory inspection
   node --inspect server.js
   ```

4. **Monitor Network Calls**:
   Use network monitoring tools to check request/response patterns

### Resolving Cache Issues

If caching problems are suspected:

1. **Clear Cache**:
   Restart the server to clear in-memory cache

2. **Adjust Cache Duration**:
   ```bash
   # In .env file
   DAMIEN_TOOL_CACHE_DURATION=60000  # 1 minute for testing
   ```

3. **Disable Cache for Debugging**:
   Modify `getCachedTools()` to bypass cache (for debugging only)

### Handling Tool Compatibility Issues

If tools seem incompatible between phases:

1. **Check Tool Versions**:
   Verify backend supports all tool versions

2. **Inspect Tool Schemas**:
   Compare tool schemas between phases for changes

3. **Test Individual Tools**:
   Test each tool in isolation to identify issues

4. **Review Backend Logs**:
   Check backend logs for error messages

## Getting Help

If you cannot resolve an issue using this guide:

1. **Gather Information**:
   - Server logs
   - Error messages
   - Steps to reproduce
   - Current phase and configuration

2. **Check Documentation**:
   Review all documentation for known issues

3. **Contact Support**:
   Provide all gathered information when seeking help

## Recovery Procedures

### Emergency Rollback

If a phase expansion causes critical issues:

1. **Stop the Server**:
   ```bash
   npm stop
   ```

2. **Restore Previous Phase**:
   ```bash
   # In .env file
   DAMIEN_INITIAL_PHASE=1  # Replace with previous working phase
   ```

3. **Restart in Safe Mode**:
   ```bash
   npm run start:safe
   ```

4. **Validate Recovery**:
   ```bash
   npm run test:basic
   ```

### Data Recovery

If email operations cause data issues:

1. **Stop All Operations**:
   Pause all email operations

2. **Check Gmail Web Interface**:
   Verify email state in Gmail web interface

3. **Use Gmail Recovery Tools**:
   Gmail has built-in recovery tools for some operations

4. **Contact Gmail Support**:
   For serious data issues, contact Gmail support

## Preventative Measures

To avoid issues during phase expansion:

1. **Thorough Testing**:
   Test each phase thoroughly before expanding

2. **Regular Backups**:
   Back up configuration before each phase change

3. **Staged Rollout**:
   Expand to a test account before production

4. **Monitoring**:
   Implement continuous monitoring for early detection

5. **Documentation**:
   Keep documentation updated with any discovered issues
