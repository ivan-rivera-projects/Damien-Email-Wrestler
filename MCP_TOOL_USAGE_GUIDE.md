# MCP Tool Usage Guide for Claude Code
## Damien Email Wrestler - 49 Tools Documentation

**Version**: Claude Code Compatible  
**Last Updated**: 2025-07-16  
**Purpose**: Comprehensive guide for using Damien MCP tools specifically in Claude Code environment

---

## ⚠️ CRITICAL: Claude Code vs Claude Desktop Differences

**Issue Identified**: Claude Code uses minimal MCP server while Claude Desktop uses enhanced Smithery adapter
**Impact**: Parameter handling differs between environments
**Solution**: This guide provides Claude Code-specific workarounds and verified patterns

---

## 🎯 Quick Reference: Working Patterns

### Email Discovery Pattern (VERIFIED)
```
1. damien_list_emails(query="is:unread", max_results=10) → Get email IDs
2. damien_get_email_details(message_id="id") → Get headers for each email
3. Compile results for analysis
```

### AI Analysis Pattern (VERIFIED)
```
Option 1 (Recommended - Auto-polling):
1. damien_ai_analyze_emails_async(days=30, target_count=100, min_confidence=0.85)
2. damien_job_wait_for_completion(job_id) → Automatically polls until complete

Option 2 (Manual polling):
1. damien_ai_analyze_emails_async(days=30, target_count=100, min_confidence=0.85)
2. damien_job_get_status(job_id) → Monitor progress manually
3. damien_job_get_result(job_id) → Get insights
```

---

## 📧 Core Email Management Tools

### `damien_list_emails` - Email Discovery
**Claude Code Limitation**: `include_headers` parameter not processed correctly
**Workaround Pattern**:
```json
// Step 1: Get email IDs
{
  "query": "is:unread",
  "max_results": 10
}
// Result: List of email IDs only

// Step 2: Get details for each email individually
// Use damien_get_email_details for each ID
```

**Verified Working Parameters**:
- ✅ `query`: Gmail search syntax works perfectly
- ✅ `max_results`: Number limits work
- ❌ `include_headers`: Not processed (use workaround)

**Real Example**:
```
Query: "is:unread" → Returns 10 email IDs
Then: Get details for each ID individually
```

### `damien_get_email_details` - Individual Email Details
**Claude Code Status**: NEEDS TESTING
**Expected Parameters**:
```json
{
  "message_id": "email_id_from_list",
  "format": "metadata"
}
```

**Troubleshooting Note**: Parameter validation issues detected - needs verification

### `damien_trash_emails` - Bulk Trash Operations
**Claude Code Status**: VERIFIED WORKING
**Working Parameters**:
```json
{
  "message_ids": ["id1", "id2", "id3"]
}
```

### `damien_label_emails` - Email Labeling
**Claude Code Status**: VERIFIED WORKING
**Working Parameters**:
```json
{
  "message_ids": ["id1", "id2", "id3"],
  "add_label_names": ["Label1", "Label2"]
}
```

---

## 🤖 AI Analysis Tools

### `damien_ai_analyze_emails_async` - PRIMARY TOOL
**Claude Code Status**: VERIFIED WORKING
**Optimal Parameters**:
```json
{
  "days": 30,
  "target_count": 100,
  "min_confidence": 0.85,
  "use_statistical_validation": true
}
```

**Usage Pattern**:
1. Start async job
2. Monitor with `damien_job_get_status`
3. Retrieve results with `damien_job_get_result`

### `damien_ai_analyze_emails` - Synchronous Analysis
**Claude Code Status**: VERIFIED WORKING
**Optimal Parameters**:
```json
{
  "days": 7,
  "max_emails": 50,
  "min_confidence": 0.8,
  "output_format": "summary"
}
```

### `damien_smart_trash_marketing` - AI-Powered Marketing Detection
**Claude Code Status**: VERIFIED WORKING
**Optimal Parameters**:
```json
{
  "days": 30,
  "max_emails": 500,
  "min_confidence": 0.85,
  "dry_run": false
}
```

---

## 🎛️ Job Management Tools

### `damien_job_get_status` - Monitor Background Jobs
**Claude Code Status**: VERIFIED WORKING
**Parameters**:
```json
{
  "job_id": "job_id_from_async_operation"
}
```

### `damien_job_get_result` - Retrieve Completed Results
**Claude Code Status**: VERIFIED WORKING
**Parameters**:
```json
{
  "job_id": "completed_job_id"
}
```

### `damien_job_list` - List All Jobs
**Claude Code Status**: VERIFIED WORKING
**Parameters**: None required

### `damien_job_wait_for_completion` - Auto-Poll Job Until Complete
**Claude Code Status**: VERIFIED WORKING
**Purpose**: Automatically monitors background jobs until completion - no more manual status checks!

**Optimal Parameters**:
```json
{
  "job_id": "job_id_from_async_operation",
  "poll_interval": 10,
  "timeout": 600,
  "max_polls": 60,
  "show_progress": true,
  "exponential_backoff": true
}
```

**Parameter Details**:
- `job_id` (required): Job ID from async operation
- `poll_interval` (default: 10): Initial polling interval in seconds
- `timeout` (default: 600): Maximum wait time in seconds (10 minutes)
- `max_polls` (default: 60): Maximum number of polling attempts
- `show_progress` (default: true): Show progress updates during polling
- `exponential_backoff` (default: true): Progressive intervals (5s→10s→15s→30s)

**Usage Examples**:

Basic usage (recommended):
```json
{
  "job_id": "task_7125151d"
}
```

Silent background mode:
```json
{
  "job_id": "task_7125151d",
  "show_progress": false
}
```

Custom timeout for large jobs:
```json
{
  "job_id": "task_7125151d",
  "timeout": 1200,
  "max_polls": 120
}
```

Conservative polling:
```json
{
  "job_id": "task_7125151d",
  "poll_interval": 30,
  "exponential_backoff": false
}
```

**Success Response**:
```json
{
  "success": true,
  "status": "completed",
  "result": {
    "patterns": [...],
    "statistics": {...}
  },
  "completion_details": {
    "total_wait_time": 85.2,
    "polls_used": 9,
    "final_interval": 10
  }
}
```

**Timeout Response** (job still running):
```json
{
  "success": false,
  "status": "timeout",
  "last_known_status": "running",
  "suggestion": "Job may still be running. Use damien_job_get_status(job_id='task_xxx') to check current status, or call again with higher timeout.",
  "progress_history": [...]
}
```

**Best Practices**:
- Use default parameters for most scenarios
- Set `show_progress: false` for silent background operations
- Increase `timeout` and `max_polls` for jobs processing 1000+ emails
- Check `completion_details` to optimize future polling strategies

---

## 🗂️ Organization Tools - Natural Language Interface

### `damien_organize_emails` - One-Command Organization
**Claude Code Status**: NEEDS TESTING
**Expected Parameters**:
```json
{
  "pattern": "from Shopify about customers",
  "action": "archive with label 'Shopify Support'",
  "apply_to_existing": true,
  "dry_run": false
}
```

### `damien_create_label` - Direct Label Management
**Claude Code Status**: NEEDS TESTING
**Expected Parameters**:
```json
{
  "name": "Important Clients",
  "color": {
    "background": "#42d692",
    "text": "#094228"
  }
}
```

### `damien_smart_rule` - Natural Language Rules
**Claude Code Status**: NEEDS TESTING
**Expected Parameters**:
```json
{
  "instruction": "Archive all Amazon receipts with label 'Receipts'",
  "preview": true,
  "apply_to_existing": false
}
```

---

## 🚀 Enhanced Operations

### `damien_trash_emails_by_query` - Large-Scale Query-Based Trash
**Claude Code Status**: VERIFIED WORKING
**Optimal Parameters**:
```json
{
  "query": "is:unread (list:* OR marketing)",
  "max_results": 1000,
  "dry_run": false,
  "use_async": true
}
```

### `damien_smart_cleanup` - Preview Cleanup Operations
**Claude Code Status**: NEEDS TESTING
**Expected Parameters**:
```json
{
  "timeframe": "this week",
  "confidence_threshold": 0.9,
  "max_emails": 500
}
```

### `damien_execute_cleanup` - Execute Cleanup Plans
**Claude Code Status**: NEEDS TESTING
**Expected Parameters**:
```json
{
  "action_token": "token_from_smart_cleanup"
}
```

---

## 🔧 Claude Code Workarounds

### Getting Email Headers (From/Subject/Date)
**Problem**: `include_headers` not working in `damien_list_emails`
**Workaround**:
```
1. Use damien_list_emails to get email IDs
2. Use damien_get_email_details for each email individually
3. Extract headers from individual responses
4. Compile into desired format
```

### Bulk Operations Efficiency
**Best Practice**: 
- Use query-based operations when possible
- Batch email IDs for bulk operations
- Leverage async tools for large datasets

### Parameter Format Troubleshooting
**Common Issues**:
- Array parameters may need string format
- JSON objects in parameters may need escaping
- Some tools require exact parameter names

---

## 📊 Verified Tool Status Matrix

| Tool Category | Working | Needs Testing | Broken |
|---------------|---------|---------------|---------|
| Email Listing | ✅ (IDs only) | 🟡 (Headers) | ❌ |
| Email Details | 🟡 | | |
| AI Analysis | ✅ | | |
| Job Management | ✅ | | |
| Bulk Operations | ✅ | | |
| Organization | | 🟡 | |
| Label Management | ✅ | 🟡 | |

**Legend**:
- ✅ Verified working in Claude Code
- 🟡 Needs testing/verification
- ❌ Known issues/limitations

---

## 🎯 Recommended Workflows for Claude Code

### Workflow 1: Get Recent Unread Emails with Headers
```
1. damien_list_emails(query="is:unread", max_results=10)
2. For each email ID: damien_get_email_details(message_id=id)
3. Extract From, Subject, Date from each response
4. Compile tabular results
```

### Workflow 2: AI-Powered Email Analysis (Recommended with Auto-Polling)
```
1. damien_ai_analyze_emails_async(days=30, target_count=100, min_confidence=0.85)
2. damien_job_wait_for_completion(job_id) → Automatically polls until complete
3. Process automation recommendations from result

Alternative (Manual Polling):
1. damien_ai_analyze_emails_async(days=30, target_count=100, min_confidence=0.85)
2. damien_job_get_status(job_id) until complete
3. damien_job_get_result(job_id)
4. Process automation recommendations
```

### Workflow 3: Smart Email Cleanup
```
1. damien_smart_trash_marketing(days=30, max_emails=500, min_confidence=0.85)
2. Review results and confidence scores
3. Apply bulk operations based on AI recommendations
```

---

## 🐛 Known Issues & Solutions

### Issue 1: include_headers Parameter Ignored
**Symptom**: Email lists return only IDs, no headers
**Cause**: Claude Code MCP interface limitation
**Solution**: Use individual email detail calls

### Issue 2: Parameter Validation Errors
**Symptom**: "Field required" errors for valid parameters
**Cause**: Parameter serialization differences
**Solution**: Check exact parameter names and formats

### Issue 3: Tool Response Differences
**Symptom**: Different results between Claude Desktop and Claude Code
**Cause**: Different MCP server implementations
**Solution**: Use verified Claude Code patterns from this guide

---

## 🎯 Testing Checklist

Use this checklist to verify tool functionality:

### Core Functions
- [ ] `damien_list_emails` returns email IDs
- [ ] `damien_get_email_details` returns headers
- [ ] `damien_trash_emails` works with ID arrays
- [ ] `damien_label_emails` applies labels correctly

### AI Functions
- [ ] `damien_ai_analyze_emails_async` starts jobs
- [ ] `damien_job_get_status` shows progress
- [ ] `damien_job_get_result` returns analysis
- [ ] `damien_job_wait_for_completion` auto-polls until complete
- [ ] Confidence thresholds work correctly

### Advanced Functions
- [ ] `damien_smart_trash_marketing` identifies patterns
- [ ] `damien_organize_emails` natural language works
- [ ] `damien_trash_emails_by_query` handles large volumes

---

## 🔄 Update Protocol

When testing new tools or finding working patterns:

1. **Test the tool** with various parameter combinations
2. **Document results** in this guide
3. **Update status matrix** with verification status
4. **Add workarounds** for any limitations found
5. **Update workflows** with verified patterns

---

## 📞 Troubleshooting Support

**Service Status Check**: `./scripts/status.sh`
**Log Locations**: `/logs/damien-mcp-server.log`
**Backend Health**: `curl http://localhost:8892/health`

**Common Resolution Steps**:
1. Restart services: `./scripts/stop-all.sh && ./scripts/start-all.sh`
2. Check service logs for errors
3. Verify API keys and configuration
4. Test with minimal parameter sets first

---

*This guide will be continuously updated as more tools are verified for Claude Code compatibility.*