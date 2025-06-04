#!/bin/bash
# fix-claude-config.sh - Fixes Claude Desktop configuration for Claude Max compatibility

set -e

echo "🔧 Claude Desktop Configuration Fix for Claude Max"
echo "================================================="

# Load API key from root .env file
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_ENV_FILE="${ROOT_DIR}/.env"

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

echo "📁 Found Claude Desktop config at: $CLAUDE_CONFIG_PATH"

# Create backup
BACKUP_PATH="${CLAUDE_CONFIG_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CLAUDE_CONFIG_PATH" "$BACKUP_PATH"
echo "💾 Created backup at: $BACKUP_PATH"

# Check if Damien server exists in config
if grep -q "damien.*email.*wrestler" "$CLAUDE_CONFIG_PATH"; then
    echo "✅ Found existing Damien MCP server configuration"
    
    # Fix naming pattern (hyphens to underscores)
    if grep -q "damien-email-wrestler" "$CLAUDE_CONFIG_PATH"; then
        echo "🔧 Fixing server name: damien-email-wrestler → damien_email_wrestler"
        sed -i.tmp 's/"damien-email-wrestler"/"damien_email_wrestler"/g' "$CLAUDE_CONFIG_PATH"
        rm "${CLAUDE_CONFIG_PATH}.tmp"
    fi
    
    # Update API key
    echo "🔧 Updating API key in configuration..."
    # Use a more robust sed command to update the API key within the damien_email_wrestler section
    sed -i.tmp '/damien_email_wrestler/,/}/ s|"DAMIEN_MCP_SERVER_API_KEY": "[^"]*"|"DAMIEN_MCP_SERVER_API_KEY": "'$API_KEY'"|' "$CLAUDE_CONFIG_PATH"
    rm "${CLAUDE_CONFIG_PATH}.tmp"
    
else
    echo "➕ Adding new Damien MCP server configuration..."
    
    # Check if config has mcpServers section
    if grep -q '"mcpServers"' "$CLAUDE_CONFIG_PATH"; then
        # Add to existing mcpServers section
        sed -i.tmp '/"mcpServers": {/a\
    "damien_email_wrestler": {\
      "command": "bash",\
      "args": [\
        "'"$ROOT_DIR"'/damien-smithery-adapter/claude-integration-v2.sh"\
      ],\
      "env": {\
        "DAMIEN_MCP_SERVER_URL": "http://localhost:8892",\
        "DAMIEN_MCP_SERVER_API_KEY": "'"$API_KEY"'",\
        "SERVER_NAME": "Damien Email Wrestler",\
        "SERVER_VERSION": "1.0.0"\
      }\
    },' "$CLAUDE_CONFIG_PATH"
    else
        # Create new mcpServers section
        sed -i.tmp 's/{/{\
  "mcpServers": {\
    "damien_email_wrestler": {\
      "command": "bash",\
      "args": [\
        "'"$ROOT_DIR"'/damien-smithery-adapter/claude-integration-v2.sh"\
      ],\
      "env": {\
        "DAMIEN_MCP_SERVER_URL": "http://localhost:8892",\
        "DAMIEN_MCP_SERVER_API_KEY": "'"$API_KEY"'",\
        "SERVER_NAME": "Damien Email Wrestler",\
        "SERVER_VERSION": "1.0.0"\
      }\
    }\
  },/' "$CLAUDE_CONFIG_PATH"
    fi
    rm "${CLAUDE_CONFIG_PATH}.tmp"
fi

echo ""
echo "✅ Claude Desktop configuration updated!"
echo ""
echo "📋 Configuration summary:"
echo "   • Server name: damien_email_wrestler (Claude Max compatible)"
echo "   • API key: ${API_KEY:0:16}... (synchronized)"
echo "   • Script path: $ROOT_DIR/damien-smithery-adapter/claude-integration-v2.sh"
echo ""
echo "🎯 Next steps:"
echo "   1. Restart Claude Desktop completely"
echo "   2. Check Settings > Developer to verify MCP server shows as 'Running'"
echo "   3. Look for the MCP tools icon in Claude chat interface"
echo "   4. Run ./scripts/test.sh to validate everything"
echo ""
echo "💡 If you encounter issues:"
echo "   • Check logs in: $ROOT_DIR/logs/"
echo "   • Restore backup from: $BACKUP_PATH"
echo "   • Run ./scripts/start-all.sh to ensure services are running"
