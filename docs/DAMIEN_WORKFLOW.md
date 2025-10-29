# Damien Work Session Workflow
**Context Window Management for Claude Code**

## Overview

This workflow enables/disables Damien MCP tools on-demand to save context window space when not actively managing emails.

## Why This Approach?

**Problem**: MCP tools consume context window even when not in use
**Solution**: Enable MCP only during email management work
**Benefit**: Frees ~1000-2000 tokens for other work when Damien tools aren't needed

## Technical Constraint

**MCP servers are loaded at Claude Code startup only.**
There is no "hot reload" mechanism - this is a limitation of the MCP protocol specification, not Claude Code.

Therefore, **restart is required** after enabling/disabling MCP configuration.

## The Workflow

### Starting a Damien Work Session

```bash
./scripts/damien-work-start.sh
```

**What it does:**
1. Starts all Damien services (MCP server, adapters)
2. Enables MCP configuration in Claude Code
3. Generates resume prompt and copies to clipboard
4. Prompts for confirmation
5. Automatically quits Claude Code
6. Waits 3 seconds for clean shutdown
7. Reopens Claude Code with project loaded

**After restart:**
1. Wait for Claude Code to fully load
2. Start a new chat
3. Paste the resume prompt (already in clipboard)
4. Begin using all 48 Damien tools

### Ending a Damien Work Session

```bash
./scripts/damien-work-stop.sh
```

**What it does:**
1. Stops all Damien services
2. Disables MCP configuration in Claude Code

**After stopping:**
- **Current session**: Tools still visible but will error if called
- **Next session**: Tools won't load (context window freed)
- **Optional restart**: Restart Claude Code to fully free context window immediately

## Workflow Comparison

### Option 1: Always-On (Not Recommended)
```
✓ Tools always available
✗ Always consuming context window (~1500 tokens)
✗ Services running even when not needed
```

### Option 2: Manual Management (Previous Approach)
```
✓ Context window saved when not in use
✗ Manual MCP enable/disable commands
✗ Manual Claude Code restart
✗ Need to remember resume context
```

### Option 3: Automated Workflow (Current - Recommended)
```
✓ Context window saved when not in use
✓ Single command to start work session
✓ Automatic restart with resume prompt
✓ Seamless continuation of work
✗ Still requires restart (unavoidable)
```

## Typical Usage Patterns

### Daily Email Management
```bash
# Morning: Start work
./scripts/damien-work-start.sh
# [Paste resume prompt after restart]
# Work with emails using MCP tools

# Done for the day
./scripts/damien-work-stop.sh
```

### Ad-Hoc Email Tasks
```bash
# Need to quickly check/manage emails
./scripts/damien-work-start.sh
# [Quick email management]
./scripts/damien-work-stop.sh
```

### Extended Sessions
```bash
# Start once
./scripts/damien-work-start.sh

# Work across multiple chats in Claude Code
# All tools remain available

# Stop when completely done
./scripts/damien-work-stop.sh
```

## Context Window Savings

**Estimated savings when Damien tools not loaded:**
- Tool definitions: ~800 tokens
- MCP protocol overhead: ~300 tokens
- System prompts: ~400 tokens
- **Total saved**: ~1500 tokens per session

**For a 200k context window:**
- Savings: 0.75% per session
- Meaningful for long conversations or large codebases

## Troubleshooting

### "Tools not available after restart"
**Check:**
```bash
# Verify services running
./scripts/status.sh

# Verify MCP configuration
claude mcp list | grep damien

# Re-run start script if needed
./scripts/damien-work-start.sh
```

### "Services won't start"
**Fix:**
```bash
# Clean shutdown
./scripts/stop-all.sh

# Wait 5 seconds
sleep 5

# Restart
./scripts/start-all.sh
```

### "Resume prompt not in clipboard"
The prompt is also printed to terminal. Copy manually:
```
Test Damien MCP Integration - Session Start

I'm ready to test all 48 Damien Email Wrestler tools with my real Gmail data.

**Services Status**: All running and healthy
**MCP Tools**: Freshly loaded and ready
**Project**: /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler

**First Test - Email Discovery:**
Show me my 2 most recent unread emails with full content.
```

## Alternative: Keep Services Running, Toggle MCP Only

If you want to avoid restart but keep services warm:

```bash
# Enable MCP without restarting services
./scripts/claude-code-enable-mcp.sh

# Restart Claude Code manually (Cmd+Q → Reopen)

# Later: Disable MCP only
./scripts/claude-code-disable-mcp.sh

# Restart Claude Code manually

# Services stay running in background
```

This approach saves startup time but keeps services consuming resources.

## Future Enhancement Ideas

1. **macOS Shortcut Integration**
   - Create macOS Shortcut that runs start script
   - Bind to keyboard shortcut
   - One-key email management activation

2. **Session Recovery**
   - Save conversation context before restart
   - Auto-restore after restart
   - Seamless continuation

3. **Health Monitoring**
   - Pre-flight checks before restart
   - Validate all services healthy
   - Alert if issues detected

4. **Usage Analytics**
   - Track time in Damien sessions
   - Measure context window savings
   - Optimize workflow based on patterns

---

**Remember**: The restart requirement is a technical limitation of the MCP protocol, not a design choice. The automated workflow minimizes friction while maintaining the context window benefits.
