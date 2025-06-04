#!/bin/bash
# Complete fix for Claude MAX Desktop configuration

set -e

echo "🔧 Claude MAX Desktop Complete Fix"
echo "=================================="

# Get the absolute path to the root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_ENV_FILE="${ROOT_DIR}/.env"

echo "📁 Root directory: $ROOT_DIR"

# Load API key from .env file
if [ ! -f "$ROOT_ENV_FILE" ]; then
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
if [ ! -f "$CLAUDE_CONFIG_PATH" ]; then
    echo "❌ Claude Desktop config not found at: $CLAUDE_CONFIG_PATH"
    echo "Please install and run Claude Desktop first"
    exit 1
fi

# Create backup
BACKUP_PATH="${CLAUDE_CONFIG_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CLAUDE_CONFIG_PATH" "$BACKUP_PATH"
echo "💾 Created backup at: $BACKUP_PATH"

# Create a new configuration with the fixed path
cat > "${CLAUDE_CONFIG_PATH}.tmp" << EOF
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@smithery-ai/brave-search",
        "--key",
        "8f22fb11-912e-4db1-8b71-37c5f883f766",
        "--profile",
        "sticky-activity-2uH06K"
      ]
    },
    "context7-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@upstash/context7-mcp",
        "--key",
        "8f22fb11-912e-4db1-8b71-37c5f883f766"
      ]
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@smithery-ai/github",
        "--key",
        "8f22fb11-912e-4db1-8b71-37c5f883f766",
        "--profile",
        "sticky-activity-2uH06K"
      ]
    },
    "mcp-shrimp-task-manager": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@cjo4m06/mcp-shrimp-task-manager",
        "--key",
        "8f22fb11-912e-4db1-8b71-37c5f883f766",
        "--profile",
        "sticky-activity-2uH06K"
      ]
    },
    "desktop-commander": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@wonderwhy-er/desktop-commander",
        "--key",
        "8f22fb11-912e-4db1-8b71-37c5f883f766"
      ]
    },
    "damien_email_wrestler": {
      "command": "bash",
      "args": [
        "${ROOT_DIR}/damien-smithery-adapter/claude-max-fix.sh"
      ],
      "env": {
        "DAMIEN_MCP_SERVER_URL": "http://localhost:8892",
        "DAMIEN_MCP_SERVER_API_KEY": "${API_KEY}",
        "SERVER_NAME": "Damien_Email_Wrestler",
        "SERVER_VERSION": "2.0.0",
        "NODE_ENV": "production"
      }
    }
  }
}
EOF

# Replace the placeholders with actual values
sed -i '' "s|\${ROOT_DIR}|${ROOT_DIR}|g" "${CLAUDE_CONFIG_PATH}.tmp"
sed -i '' "s|\${API_KEY}|${API_KEY}|g" "${CLAUDE_CONFIG_PATH}.tmp"

# Move the temporary file to the actual config
mv "${CLAUDE_CONFIG_PATH}.tmp" "$CLAUDE_CONFIG_PATH"

echo ""
echo "✅ Claude Desktop configuration fixed!"
echo ""
echo "📋 Configuration summary:"
echo "   • Server name: damien_email_wrestler"
echo "   • Script path: ${ROOT_DIR}/damien-smithery-adapter/claude-max-fix.sh"
echo "   • API key: ${API_KEY:0:16}..."
echo ""
echo "🎯 Next steps:"
echo "   1. Quit Claude Desktop completely (Cmd+Q)"
echo "   2. Start all Damien services: cd $ROOT_DIR && ./scripts/start-all.sh"
echo "   3. Relaunch Claude Desktop"
echo "   4. Check Developer settings to verify MCP servers"
echo ""
echo "💡 If the server still doesn't appear:"
echo "   • Check logs: tail -f $ROOT_DIR/logs/claude-max-mcp-stderr.log"
echo "   • Verify backend: curl http://localhost:8892/health"
echo "   • Restore backup: cp $BACKUP_PATH \"$CLAUDE_CONFIG_PATH\""
