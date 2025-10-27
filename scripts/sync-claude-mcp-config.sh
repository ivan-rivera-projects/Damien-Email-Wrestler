#!/bin/bash

# ========================================
# Damien Email Wrestler - Claude Desktop MCP Config Sync
# ========================================
# Automatically syncs Claude Desktop MCP configuration with .env file
# Updates ONLY Claude Desktop config (not Claude Code)

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Claude Desktop config location
CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

echo "🔄 Syncing Claude Desktop MCP configuration with .env file..."

# Verify .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    echo "Please ensure .env file exists with DAMIEN_MCP_SERVER_API_KEY set"
    exit 1
fi

# Load environment variables
source "$ENV_FILE"

# Verify required variables are set
if [ -z "${DAMIEN_MCP_SERVER_API_KEY:-}" ]; then
    echo "❌ Error: DAMIEN_MCP_SERVER_API_KEY not found in .env file"
    exit 1
fi

# Get minimal server path
MINIMAL_SERVER_PATH="$PROJECT_ROOT/damien-mcp-minimal/server.js"
if [ ! -f "$MINIMAL_SERVER_PATH" ]; then
    echo "❌ Error: Minimal MCP server not found at $MINIMAL_SERVER_PATH"
    exit 1
fi

# Verify Claude Desktop config exists
if [ ! -f "$CLAUDE_DESKTOP_CONFIG" ]; then
    echo "❌ Error: Claude Desktop config not found at $CLAUDE_DESKTOP_CONFIG"
    echo "Please ensure Claude Desktop is installed and has been run at least once"
    exit 1
fi

echo "📋 Configuration to sync:"
echo "   Server: damien-email-wrestler"
echo "   Command: node $MINIMAL_SERVER_PATH"
echo "   Target: Claude Desktop"

# Update Claude Desktop config using Python for safe JSON manipulation
python3 << PYTHON_SCRIPT
import json
import os
from pathlib import Path

config_path = Path("$CLAUDE_DESKTOP_CONFIG")

# Read existing config
with open(config_path, 'r') as f:
    config = json.load(f)

# Ensure mcpServers key exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Add or update damien-email-wrestler configuration
config['mcpServers']['damien-email-wrestler'] = {
    "command": "node",
    "args": ["$MINIMAL_SERVER_PATH"]
}

# Write updated config back
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"✅ Added damien-email-wrestler to Claude Desktop config")
print(f"📝 Config location: {config_path}")
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to update Claude Desktop configuration"
    exit 1
fi

echo ""
echo "✅ Claude Desktop MCP configuration synced successfully!"
echo ""
echo "🔍 Next steps:"
echo "   1. Restart Claude Desktop completely (quit and reopen)"
echo "   2. The damien-email-wrestler server will be available"
echo ""
echo "💡 Tip: Restart Claude Desktop to load the updated configuration"
