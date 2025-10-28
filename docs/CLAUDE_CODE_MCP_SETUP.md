# Claude Code MCP Setup Guide
## Email Management Automation with Damien

This guide explains how to enable/disable the Damien MCP server in Claude Code for managing thousands of emails through AI-powered automation.

---

## Quick Start

### Automatic MCP Management (Recommended)
MCP configuration is now **automatically managed** by service scripts:

```bash
# Start services → Auto-enables MCP in Claude Code
./scripts/start-all.sh

# Stop services → Auto-disables MCP in Claude Code
./scripts/stop-all.sh
```

**Why automatic?** With 48 tools, Damien consumes significant context window space. Auto-management ensures tools are only enabled when backend services are running and ready to serve them.

### Manual MCP Management (Advanced)
If you need to manually control MCP without affecting services:

```bash
# Enable MCP only
./scripts/claude-code-enable-mcp.sh

# Disable MCP only
./scripts/claude-code-disable-mcp.sh
```

---

## Configuration Comparison

### Claude Desktop Configuration
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "damien-email-wrestler": {
      "command": "node",
      "args": [
        "/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-mcp-minimal/server.js"
      ]
    }
  }
}
```

**Characteristics:**
- File-based configuration
- Automatically starts server when Claude Desktop launches
- Persistent across all sessions
- Requires Claude Desktop restart to apply changes

### Claude Code Configuration
Managed via CLI commands (stored internally by Claude Code)

```bash
claude mcp add damien-email-wrestler \
  "node" \
  "/path/to/damien-mcp-minimal/server.js" \
  -e DAMIEN_MCP_SERVER_URL=http://localhost:8892 \
  -e DAMIEN_MCP_SERVER_API_KEY=<api-key> \
  -e DAMIEN_MCP_MINIMAL_PORT=8893 \
  -e LOG_LEVEL=INFO
```

**Characteristics:**
- CLI-based configuration
- Easy to enable/disable programmatically
- Requires Claude Code restart to apply changes
- Better for project-specific tools

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Claude Code                           │
│                    (MCP Client Interface)                    │
└───────────────────┬─────────────────────────────────────────┘
                    │ MCP Protocol (stdio)
                    │
┌───────────────────▼─────────────────────────────────────────┐
│              Minimal MCP Server (port 8893)                  │
│            • Parameter marshaling (fixed!)                   │
│            • Tool discovery and caching                      │
│            • Request routing                                 │
└───────────────────┬─────────────────────────────────────────┘
                    │ HTTP + API Key
                    │
┌───────────────────▼─────────────────────────────────────────┐
│              Backend MCP Server (port 8892)                  │
│            • Tool registry (48 tools)                        │
│            • Gmail API integration                           │
│            • AI intelligence layer                           │
│            • AWS Lambda enhancement (optional)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Available Tools (48 Total)

When enabled, Claude Code has access to:

### Core Email Operations (13 tools)
- `damien_list_emails` - List with advanced filtering
- `damien_get_email_details` - Full email content
- `damien_trash_emails` - Move to trash
- `damien_label_emails` - Add/remove labels
- `damien_mark_emails` - Mark read/unread
- `damien_delete_emails_permanently` - Permanent deletion
- `damien_count_emails_by_label` - Count by label
- `damien_get_all_emails_by_label` - Bulk retrieval
- And more...

### AI Intelligence (12 tools)
- `damien_ai_analyze_emails` - Pattern detection
- `damien_ai_analyze_emails_async` - Large-scale analysis
- `damien_ai_suggest_rules` - Rule recommendations
- `damien_ai_create_rule` - Natural language rules
- `damien_ai_get_insights` - Email insights
- `damien_ai_optimize_inbox` - Inbox optimization
- `damien_ai_quick_test` - System validation
- And more...

### Bulk Operations (6 tools)
- `damien_ai_bulk_operations` - AI-driven bulk ops
- `damien_trash_emails_by_query` - Query-based trash
- `damien_smart_trash_marketing` - AI marketing cleanup
- `damien_smart_cleanup` - One-click cleanup preview
- `damien_execute_cleanup` - Execute cleanup plan
- And more...

### Organization (5 tools)
- `damien_create_label` - Create new labels
- `damien_delete_label` - Remove labels
- `damien_list_labels` - List all labels
- `damien_smart_rule` - Natural language rules
- `damien_organize_emails` - Auto-organization

### Thread & Draft Management (11 tools)
- Thread operations (list, get, modify, trash, delete)
- Draft operations (create, update, send, list, get, delete)

### Job Management (4 tools)
- `damien_job_get_status` - Check job progress
- `damien_job_get_result` - Get job results
- `damien_job_cancel` - Cancel running job
- `damien_job_list` - List all jobs

---

## Use Cases for Enabling/Disabling

### When to Enable
✅ **Managing email inbox** - Processing thousands of emails
✅ **Email automation setup** - Creating rules and workflows
✅ **Bulk email operations** - Large-scale cleanup or organization
✅ **AI-powered analysis** - Understanding email patterns
✅ **Email productivity** - Focused inbox management sessions

### When to Disable
🔒 **Security-sensitive work** - No email access needed
🔧 **Non-email projects** - Working on other codebases
⚡ **Performance** - Reduce overhead when not using email tools
🎯 **Focus mode** - Limit available tools to reduce distraction

---

## Usage Examples

### Example 1: Analyze Recent Emails
```
You: Analyze my last 100 emails and identify patterns

Claude: [Uses damien_ai_analyze_emails_async to process 100 emails]
Found patterns:
- 45 marketing emails (newsletters, promotions)
- 23 work-related communications
- 18 notifications (social media, updates)
- 14 personal emails

Would you like me to create rules to auto-organize these?
```

### Example 2: Bulk Cleanup
```
You: Find and trash all marketing emails from the past week

Claude: [Uses damien_smart_trash_marketing]
Found 67 marketing emails matching criteria:
- 23 newsletter subscriptions
- 31 promotional offers
- 13 product announcements

Preview shows emails from: Amazon, Walmart, various retailers
Proceed with trashing? (This is reversible - they go to trash)
```

### Example 3: Smart Organization
```
You: Organize all my Shopify emails with a label

Claude: [Uses damien_organize_emails]
Created label "Shopify Support"
Applied to 142 emails matching Shopify patterns
Created rule to auto-label future Shopify emails

Your Shopify emails are now organized!
```

---

## Troubleshooting

### Tools Not Available in Claude Code
**Symptoms:** Damien tools don't appear in new chats

**Solutions:**
1. Check if MCP server is configured:
   ```bash
   claude mcp list
   ```

2. Verify services are running:
   ```bash
   ./scripts/status.sh
   ```

3. Re-enable MCP server:
   ```bash
   ./scripts/claude-code-enable-mcp.sh
   ```

4. Restart Claude Code completely (Cmd+Q, then reopen)

### Parameter Marshaling Issues
**Symptoms:** Array parameters not working (e.g., `include_headers`)

**Solutions:**
- ✅ **FIXED** as of commit c307e96
- The minimal MCP server now includes parameter preprocessing
- Arrays sent as JSON strings are automatically parsed

### Services Not Running
**Symptoms:** Connection errors, timeouts

**Solutions:**
```bash
# Stop all services
./scripts/stop-all.sh

# Start all services
./scripts/start-all.sh

# Check status
./scripts/status.sh
```

---

## Configuration Files

### Key Files
- **Enable script:** `scripts/claude-code-enable-mcp.sh`
- **Disable script:** `scripts/claude-code-disable-mcp.sh`
- **Server:** `damien-mcp-minimal/server.js`
- **Backend:** `damien-mcp-server/app/main.py`
- **Logs:** `logs/damien-mcp-minimal.log`

### Environment Variables
Set via MCP configuration:
- `DAMIEN_MCP_SERVER_URL` - Backend server URL (http://localhost:8892)
- `DAMIEN_MCP_SERVER_API_KEY` - API authentication key
- `DAMIEN_MCP_MINIMAL_PORT` - Minimal server port (8893)
- `LOG_LEVEL` - Logging verbosity (INFO/DEBUG)

---

## Best Practices

### 1. Start Services First
Always ensure Damien services are running before enabling MCP:
```bash
./scripts/start-all.sh
./scripts/claude-code-enable-mcp.sh
```

### 2. Restart Claude Code After Changes
MCP configuration changes require a full restart:
- Quit Claude Code (Cmd+Q)
- Wait 2-3 seconds
- Reopen Claude Code

### 3. Test Connection
Verify the MCP connection in a new chat:
```
You: List my 5 most recent unread emails
```

### 4. Monitor Logs
When troubleshooting, watch the logs:
```bash
tail -f logs/damien-mcp-minimal.log
```

### 5. Use Async Tools for Large Operations
For operations on 100+ emails, use async versions:
- `damien_ai_analyze_emails_async` (not `damien_ai_analyze_emails`)
- `damien_trash_emails_by_query` (for query-based operations)

---

## Advanced: Manual MCP Management

### Add Server
```bash
claude mcp add damien-email-wrestler \
  "node" \
  "/path/to/server.js" \
  -e KEY=value
```

### Remove Server
```bash
claude mcp remove damien-email-wrestler
```

### List Servers
```bash
claude mcp list
```

### Check Server Health
```bash
curl http://localhost:8893/health
```

---

## Security Considerations

### API Keys
- API keys are stored in MCP configuration
- Keys authenticate requests between MCP layers
- Keys are NOT exposed to external services

### Gmail Tokens
- Gmail OAuth tokens stored in: `damien-cli/data/token.json`
- Auto-refreshed by Google OAuth flow
- Never transmitted over network

### Network Security
- All communication is localhost-only
- No external network access required
- Optional AWS Lambda uses AWS SDK with IAM authentication

---

## Performance Optimization

### For Large Inboxes (10,000+ emails)
1. Use async tools for analysis
2. Process in batches of 500-1000
3. Enable AWS Lambda for faster AI processing
4. Monitor with job status tools

### For Fast Operations
1. Use `include_headers` parameter to reduce round-trips
2. Cache frequently accessed data
3. Use bulk operations instead of loops

---

## Support & Documentation

- **Tool Usage Guide:** `MCP_TOOL_USAGE_GUIDE.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`
- **Architecture:** `docs/MCP_PROTOCOL_ARCHITECTURE.md`
- **Issue Tracker:** GitHub Issues

---

## Context Window Optimization

### The Problem
With **48 tools**, Damien's MCP server consumes significant context window space in every Claude Code session. Each tool definition includes:
- Tool name and description
- Complete input schema
- Parameter types and validation rules
- Example usage patterns

**Total context impact:** ~15-20% of available context window

### The Solution: Auto-Enable/Disable
Services running = MCP enabled = Context usage justified
Services stopped = MCP disabled = Context window freed

**Benefits:**
- ✅ Zero context waste when not using email tools
- ✅ Automatic management - no manual steps
- ✅ Services and tools always in sync
- ✅ Maximum available context for coding tasks

### Workflow
```bash
# Working on email management
./scripts/start-all.sh          # Services start + MCP enabled
# [Restart Claude Code]
# [Use 48 email tools]

# Done with email, working on code
./scripts/stop-all.sh            # Services stop + MCP disabled
# [Restart Claude Code]
# [Full context available for coding]
```

---

## Changelog

### 2025-10-28 - Auto-Enable/Disable MCP Integration
- Integrated MCP management into service lifecycle
- `start-all.sh` now auto-enables MCP in Claude Code
- `stop-all.sh` now auto-disables MCP in Claude Code
- Context window optimization: tools only enabled when services running
- Updated documentation with automatic workflow

### 2025-10-27 - Parameter Marshaling Fix
- Fixed array parameter handling in Claude Code
- Added `processArguments()` to minimal MCP server
- Claude Code now has parity with Claude Desktop

### 2025-10-27 - Claude Code Setup Scripts
- Added `claude-code-enable-mcp.sh`
- Added `claude-code-disable-mcp.sh`
- Created comprehensive setup documentation

---

**Ready to manage thousands of emails with AI-powered automation!** 🚀
