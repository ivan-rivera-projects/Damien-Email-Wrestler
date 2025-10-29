#!/bin/bash
##############################################################################
# Damien Work Session - Stop
#
# This script:
# 1. Disables MCP in Claude Code
# 2. Stops all Damien services
# 3. Frees up context window for other work
#
# Note: You can continue using Claude Code for other work immediately.
#       The MCP tools will be unavailable, but context window is freed.
#       If you want to remove tool definitions from current session, restart Claude Code.
#
# Usage: ./scripts/damien-work-stop.sh
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🛑 Stopping Damien Work Session"
echo "================================"
echo ""

# Step 1: Stop services and disable MCP
echo "📊 Step 1: Stopping services and disabling MCP..."
"$SCRIPT_DIR/stop-all.sh"
echo ""

echo "✅ Damien Work Session Stopped!"
echo ""
echo "📋 What's Changed:"
echo "   ✓ All Damien services stopped (freed system resources)"
echo "   ✓ MCP configuration disabled (won't load on next restart)"
echo "   ✓ Context window will be freed on next Claude Code restart"
echo ""
echo "💡 Current Session:"
echo "   • You can continue using Claude Code for other work"
echo "   • Damien tools are still visible but will error if called"
echo "   • To fully free context window: Restart Claude Code (Cmd+Q → Reopen)"
echo ""
echo "🔄 To Resume Damien Work Later:"
echo "   ./scripts/damien-work-start.sh"
echo ""
