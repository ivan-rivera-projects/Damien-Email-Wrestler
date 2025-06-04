#\!/bin/bash
# Script to update Claude Desktop configuration for Claude MAX compatibility

set -e

echo "🔧 Claude MAX Desktop Compatibility Fix"
echo "======================================"

# Load API key from root .env file
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_ENV_FILE="${ROOT_DIR}/.env"

if [ \! -f "$ROOT_ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ROOT_ENV_FILE"
    exit 1
fi

API_KEY=$(grep "^DAMIEN_MCP_SERVER_API_KEY=" "$ROOT_ENV_FILE" | cut -d '=' -f 2-)

if [ -z "$API_KEY" ]; then
    echo "❌ Error: DAMIEN_MCP_SERVER_API_KEY not found in .env file"
    exit 1
fi

echo "🔑 Using API key: ${API_KEY:0:16}..."

CLAUDE_CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Check if Claude Desktop config exists
if [ \! -f "$CLAUDE_CONFIG_PATH" ]; then
    echo "❌ Claude Desktop config not found at: $CLAUDE_CONFIG_PATH"
    echo "Please install and run Claude Desktop first"
    exit 1
fi

echo "📁 Found Claude Desktop config at: $CLAUDE_CONFIG_PATH"

# Create backup
BACKUP_PATH="${CLAUDE_CONFIG_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CLAUDE_CONFIG_PATH" "$BACKUP_PATH"
echo "💾 Created backup at: $BACKUP_PATH"

# Check if any Damien server exists in config and remove it first
if grep -q "\"damien_email_wrestler\"\\|\"damien-email-wrestler\"" "$CLAUDE_CONFIG_PATH"; then
    echo "🔄 Removing existing Damien MCP server configuration"
    
    # Create a temporary file without the Damien configuration
    cat "$CLAUDE_CONFIG_PATH" | python3 -c '
import json, sys
config = json.load(sys.stdin)
if "mcpServers" in config:
    for key in list(config["mcpServers"].keys()):
        if "damien" in key.lower():
            del config["mcpServers"][key]
    if not config["mcpServers"]:
        del config["mcpServers"]
json.dump(config, sys.stdout, indent=2)
' > "${CLAUDE_CONFIG_PATH}.tmp"
    
    mv "${CLAUDE_CONFIG_PATH}.tmp" "$CLAUDE_CONFIG_PATH"
fi

# Add new configuration using Python for JSON manipulation
echo "➕ Adding new Damien MCP server configuration for Claude MAX..."

cat "$CLAUDE_CONFIG_PATH" | python3 -c '
import json, sys, os

config = json.load(sys.stdin)
root_dir = os.environ.get("ROOT_DIR")
api_key = os.environ.get("API_KEY")

if "mcpServers" not in config:
    config["mcpServers"] = {}

# Use a fully compatible name with no hyphens for Claude MAX
config["mcpServers"]["damien_email_wrestler"] = {
    "command": "bash",
    "args": [
        f"{root_dir}/damien-smithery-adapter/claude-max-fix.sh"
    ],
    "env": {
        "DAMIEN_MCP_SERVER_URL": "http://localhost:8892",
        "DAMIEN_MCP_SERVER_API_KEY": api_key,
        "SERVER_NAME": "Damien_Email_Wrestler",
        "SERVER_VERSION": "2.0.0",
        "NODE_ENV": "production"
    }
}

json.dump(config, sys.stdout, indent=2)
' > "${CLAUDE_CONFIG_PATH}.tmp"

export ROOT_DIR API_KEY
mv "${CLAUDE_CONFIG_PATH}.tmp" "$CLAUDE_CONFIG_PATH"

echo ""
echo "✅ Claude Desktop configuration updated for Claude MAX compatibility\!"
echo ""
echo "📋 Configuration summary:"
echo "   • Server name: damien_email_wrestler (Claude MAX compatible)"
echo "   • Using new script: claude-max-fix.sh with fixed implementation"
echo "   • API key: ${API_KEY:0:16}... (synchronized)"
echo ""
echo "🎯 Next steps:"
echo "   1. Stop all running Damien services: ./scripts/stop-all.sh"
echo "   2. Start services with: ./scripts/start-all.sh"
echo "   3. Restart Claude Desktop completely (Quit and relaunch)"
echo "   4. Open settings in Claude Desktop and check Developer settings"
echo "   5. Verify MCP server 'damien_email_wrestler' shows as 'Running'"
echo ""
echo "💡 Troubleshooting:"
echo "   • Check logs in: $ROOT_DIR/logs/claude-max-mcp-stderr.log"
echo "   • Restore backup if needed: cp $BACKUP_PATH $CLAUDE_CONFIG_PATH"
echo "   • Run ./damien-smithery-adapter/health-check.sh to verify server status"
