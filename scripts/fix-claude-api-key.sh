#\!/bin/bash
# Fix API key issue in Claude Desktop config

set -e

echo "🔧 Fixing API key in Claude Desktop config"
echo "========================================"

# Get API key from .env file
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_KEY=$(grep "^DAMIEN_MCP_SERVER_API_KEY=" "$ROOT_DIR/.env" | cut -d '=' -f 2-)

if [ -z "$API_KEY" ]; then
    echo "❌ Error: API key not found in .env file"
    # Use hardcoded key as fallback
    API_KEY="7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
    echo "Using fallback API key"
fi

CLAUDE_CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [ \! -f "$CLAUDE_CONFIG_PATH" ]; then
    echo "❌ Error: Claude Desktop config not found"
    exit 1
fi

# Create backup
BACKUP_PATH="${CLAUDE_CONFIG_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CLAUDE_CONFIG_PATH" "$BACKUP_PATH"
echo "💾 Created backup at: $BACKUP_PATH"

# Fix API key using Python to ensure proper JSON handling
python3 -c "
import json, os

# Read config
with open('$CLAUDE_CONFIG_PATH', 'r') as f:
    config = json.load(f)

# Ensure API key is properly set
if 'mcpServers' in config and 'damien_email_wrestler' in config['mcpServers']:
    config['mcpServers']['damien_email_wrestler']['env']['DAMIEN_MCP_SERVER_API_KEY'] = '$API_KEY'
    print('✅ Fixed API key in damien_email_wrestler config')
else:
    print('⚠️ damien_email_wrestler config not found')

# Write updated config
with open('$CLAUDE_CONFIG_PATH', 'w') as f:
    json.dump(config, f, indent=2)
"

echo ""
echo "✅ Claude Desktop configuration fixed"
echo "Please restart Claude Desktop completely (quit and relaunch)"
