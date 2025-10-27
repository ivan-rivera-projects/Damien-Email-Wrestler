#!/bin/bash
##############################################################################
# Enable Damien MCP Server in Claude Code
#
# This script configures Claude Code to use the Damien MCP server for email
# management. Once enabled, you'll have access to all 48 email management tools.
##############################################################################

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_PATH="$PROJECT_ROOT/damien-mcp-minimal/server.js"

echo "🔧 Enabling Damien MCP Server for Claude Code"
echo "=============================================="
echo ""

# Check if server file exists
if [ ! -f "$SERVER_PATH" ]; then
    echo "❌ Error: Server file not found at $SERVER_PATH"
    exit 1
fi

# Check if services are running
echo "📊 Checking if Damien services are running..."
if ! curl -s http://localhost:8892/health > /dev/null 2>&1; then
    echo "⚠️  Damien services are not running. Starting them..."
    "$SCRIPT_DIR/start-all.sh"
    echo ""
fi

# Add/Update MCP server configuration
echo "📝 Configuring Claude Code MCP server..."
claude mcp add damien-email-wrestler \
  "node" \
  "$SERVER_PATH" \
  -e DAMIEN_MCP_SERVER_URL=http://localhost:8892 \
  -e DAMIEN_MCP_SERVER_API_KEY=7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f \
  -e DAMIEN_MCP_MINIMAL_PORT=8893 \
  -e LOG_LEVEL=INFO

echo ""
echo "✅ Damien MCP Server enabled in Claude Code!"
echo ""
echo "📋 Available Tools: 48 email management tools"
echo "   • Email operations (list, read, label, trash)"
echo "   • AI-powered analysis and insights"
echo "   • Thread management"
echo "   • Draft management"
echo "   • Rule automation"
echo "   • Bulk operations"
echo ""
echo "💡 Next Steps:"
echo "   1. Restart Claude Code (Cmd+Q, then reopen)"
echo "   2. In a new chat, you'll have access to all Damien tools"
echo "   3. Try: 'Show me my 10 most recent unread emails'"
echo ""
echo "🔍 Verify with: claude mcp list"
