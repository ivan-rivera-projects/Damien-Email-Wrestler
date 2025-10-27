#!/bin/bash
##############################################################################
# Disable Damien MCP Server in Claude Code
#
# This script removes the Damien MCP server from Claude Code configuration.
# Use this when you want to work on other tasks without email management tools.
##############################################################################

set -e  # Exit on error

echo "🔧 Disabling Damien MCP Server for Claude Code"
echo "=============================================="
echo ""

# Remove MCP server configuration
echo "📝 Removing Damien MCP server from Claude Code..."
if claude mcp remove damien-email-wrestler 2>/dev/null; then
    echo "✅ Damien MCP Server disabled in Claude Code"
    echo ""
    echo "💡 Notes:"
    echo "   • Damien tools will no longer be available in new Claude Code chats"
    echo "   • Backend services are still running (use ./scripts/stop-all.sh to stop them)"
    echo "   • Re-enable anytime with: ./scripts/claude-code-enable-mcp.sh"
    echo ""
    echo "🔄 To apply changes: Restart Claude Code (Cmd+Q, then reopen)"
else
    echo "⚠️  Damien MCP server was not configured in Claude Code"
    echo "   (This is fine - it means it was already disabled)"
fi

echo ""
echo "🔍 Verify with: claude mcp list"
