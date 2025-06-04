#\!/bin/bash
# Completely rebuild the Claude Desktop configuration

set -e

echo "🔄 Rebuilding Claude Desktop configuration"
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

# Create a fresh Claude Desktop config file
python3 -c "
import json, os

# Basic config template
config = {
    'telemetry': {
        'enabled': False
    },
    'mcpServers': {
        'damien_email_wrestler': {
            'command': 'bash',
            'args': [
                '${ROOT_DIR}/damien-smithery-adapter/claude-max-fix.sh'
            ],
            'env': {
                'DAMIEN_MCP_SERVER_URL': 'http://localhost:8892',
                'DAMIEN_MCP_SERVER_API_KEY': '${API_KEY}',
                'SERVER_NAME': 'Damien_Email_Wrestler',
                'SERVER_VERSION': '2.0.0',
                'NODE_ENV': 'production'
            }
        }
    }
}

# Preserve existing settings from current config
try:
    with open('${CLAUDE_CONFIG_PATH}', 'r') as f:
        old_config = json.load(f)
        
    # Preserve these sections if they exist
    for section in ['appearance', 'chat', 'models', 'window', 'organization']:
        if section in old_config:
            config[section] = old_config[section]
            
    # Preserve other MCP servers if they exist
    if 'mcpServers' in old_config:
        for server_name, server_config in old_config['mcpServers'].items():
            if server_name \!= 'damien_email_wrestler' and server_name \!= 'damien-email-wrestler':
                config['mcpServers'][server_name] = server_config
except Exception as e:
    print(f'⚠️ Could not read existing config: {e}, creating fresh config')

# Write the updated config
with open('${CLAUDE_CONFIG_PATH}', 'w') as f:
    json.dump(config, f, indent=2)
    print('✅ Wrote new Claude Desktop configuration')
"

echo ""
echo "✅ Claude Desktop configuration completely rebuilt"
echo "Please restart Claude Desktop completely (quit and relaunch)"
echo "Check Developer settings to verify 'damien_email_wrestler' shows as 'Running'"
