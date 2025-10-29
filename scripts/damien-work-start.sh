#!/bin/bash
##############################################################################
# Damien Work Session - Start
#
# This script:
# 1. Starts all Damien services
# 2. Enables MCP in Claude Code
# 3. Automatically restarts Claude Desktop to load MCP tools
# 4. Provides a resume prompt for the new session
#
# Note: This script restarts Claude Desktop (the native macOS app) rather than
# Claude Code (the CLI tool) because Claude Desktop has built-in MCP server
# support, making it ideal for testing the 48 Damien MCP tools.
#
# Usage: ./scripts/damien-work-start.sh
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting Damien Work Session"
echo "================================"
echo ""

# Step 1: Start services and enable MCP
echo "📊 Step 1: Starting services and enabling MCP..."
"$SCRIPT_DIR/start-all.sh"
echo ""

# Step 2: Generate resume prompt
echo "📝 Step 2: Generating resume prompt..."
RESUME_PROMPT="Test Damien MCP Integration - Session Start

I'm ready to test all 48 Damien Email Wrestler tools with my real Gmail data.

**Services Status**: All running and healthy
**MCP Tools**: Freshly loaded and ready
**Project**: /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler

**First Test - Email Discovery:**
Show me my 2 most recent unread emails with full content.

Use:
- damien_list_emails (query: 'is:unread', max_results: 2)
- damien_get_email_details for each email ID

This validates: Basic connectivity, parameter handling, Gmail API access."

# Save to clipboard (macOS only)
if command -v pbcopy &> /dev/null; then
    echo "$RESUME_PROMPT" | pbcopy
    echo "✅ Resume prompt copied to clipboard!"
    echo ""
fi

echo "📋 Resume Prompt (also in clipboard):"
echo "─────────────────────────────────────"
echo "$RESUME_PROMPT"
echo "─────────────────────────────────────"
echo ""

# Step 3: Restart Claude Desktop
echo "🔄 Step 3: Restarting Claude Desktop..."
echo ""
echo "⚠️  Claude Desktop will now:"
echo "   1. Quit (saving your current session)"
echo "   2. Wait 3 seconds"
echo "   3. Reopen with this project"
echo ""
echo "💡 After restart, paste the resume prompt to continue"
echo ""
read -p "Press ENTER to restart Claude Desktop now, or Ctrl+C to cancel..."

# Quit Claude Desktop
osascript -e 'quit app "Claude"' 2>/dev/null || true

# Wait for clean shutdown
echo "⏳ Waiting for clean shutdown..."
sleep 3

# Reopen Claude Desktop with this project
echo "🎯 Reopening Claude Desktop..."
open -a "Claude" "$PROJECT_ROOT"

echo ""
echo "✅ Damien Work Session Started!"
echo ""
echo "📋 Next Steps:"
echo "   1. Wait for Claude Desktop to fully load"
echo "   2. Start a new chat"
echo "   3. Paste the resume prompt (already in clipboard)"
echo "   4. Begin testing the 48 tools!"
echo ""
