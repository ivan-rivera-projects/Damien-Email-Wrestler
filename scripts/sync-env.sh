#!/bin/bash
# sync-env.sh - Synchronizes environment variables across components

set -e  # Exit on error

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_ENV_FILE="${ROOT_DIR}/.env"
MCP_ENV_FILE="${ROOT_DIR}/damien-mcp-server/.env"
ADAPTER_ENV_FILE="${ROOT_DIR}/damien-smithery-adapter/.env"

echo "🔄 Synchronizing environment variables across components..."

# Function to extract value from .env file
get_env_var() {
  local file=$1
  local var_name=$2
  grep "^${var_name}=" "$file" | cut -d '=' -f 2-
}

# Get API key from root .env file
API_KEY=$(get_env_var "$ROOT_ENV_FILE" "DAMIEN_MCP_SERVER_API_KEY")

if [ -z "$API_KEY" ]; then
  echo "❌ Error: DAMIEN_MCP_SERVER_API_KEY not found in $ROOT_ENV_FILE"
  exit 1
fi

echo "🔑 Using API key from root .env file: ${API_KEY:0:10}..."

# Update MCP Server .env file
if [ -f "$MCP_ENV_FILE" ]; then
  if grep -q "^DAMIEN_MCP_SERVER_API_KEY=" "$MCP_ENV_FILE"; then
    sed -i.bak "s|^DAMIEN_MCP_SERVER_API_KEY=.*|DAMIEN_MCP_SERVER_API_KEY=${API_KEY}|" "$MCP_ENV_FILE"
    rm "${MCP_ENV_FILE}.bak" 2>/dev/null || true
    echo "✅ Updated API key in MCP Server .env file"
  else
    echo "⚠️ DAMIEN_MCP_SERVER_API_KEY not found in $MCP_ENV_FILE"
  fi
else
  echo "⚠️ MCP Server .env file not found: $MCP_ENV_FILE"
fi

# Update Smithery Adapter .env file
if [ -f "$ADAPTER_ENV_FILE" ]; then
  if grep -q "^DAMIEN_MCP_SERVER_API_KEY=" "$ADAPTER_ENV_FILE"; then
    sed -i.bak "s|^DAMIEN_MCP_SERVER_API_KEY=.*|DAMIEN_MCP_SERVER_API_KEY=${API_KEY}|" "$ADAPTER_ENV_FILE"
    rm "${ADAPTER_ENV_FILE}.bak" 2>/dev/null || true
    echo "✅ Updated API key in Smithery Adapter .env file"
  else
    echo "⚠️ DAMIEN_MCP_SERVER_API_KEY not found in $ADAPTER_ENV_FILE"
  fi
else
  echo "⚠️ Smithery Adapter .env file not found: $ADAPTER_ENV_FILE"
fi

echo "🎉 Environment variable synchronization complete!"

# Update Claude Desktop configuration with correct API key and naming
CLAUDE_CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

echo ""
echo "🖥️  Checking Claude Desktop configuration..."

if [ -f "$CLAUDE_CONFIG_PATH" ]; then
    # Check if Damien server is configured
    if grep -q "damien.*email.*wrestler" "$CLAUDE_CONFIG_PATH"; then
        echo "✅ Damien MCP server found in Claude Desktop config"
        
        # Check if using correct naming pattern (underscores vs hyphens)
        if grep -q '"damien-email-wrestler"' "$CLAUDE_CONFIG_PATH"; then
            echo "⚠️  Found hyphenated server name (damien-email-wrestler)"
            echo "🔧 Claude Max requires underscore naming (damien_email_wrestler)"
            echo ""
            echo "To fix this manually, update your Claude Desktop config:"
            echo "   1. Open Claude Desktop"
            echo "   2. Go to Settings > Developer"
            echo "   3. Edit Config"
            echo "   4. Change 'damien-email-wrestler' to 'damien_email_wrestler'"
            echo ""
        elif grep -q '"damien_email_wrestler"' "$CLAUDE_CONFIG_PATH"; then
            echo "✅ Using correct naming pattern for Claude Max"
        fi
        
        # Check API key sync
        CONFIG_API_KEY=$(grep -A 10 "damien.*email.*wrestler" "$CLAUDE_CONFIG_PATH" | grep "DAMIEN_MCP_SERVER_API_KEY" | cut -d'"' -f4)
        if [ "$CONFIG_API_KEY" = "$API_KEY" ]; then
            echo "✅ Claude Desktop API key is synchronized"
        else
            echo "⚠️  API key mismatch detected:"
            echo "   Config: ${CONFIG_API_KEY:0:10}..."
            echo "   .env:   ${API_KEY:0:10}..."
            echo "   Please update Claude Desktop config manually"
        fi
    else
        echo "⚠️  Damien MCP server not found in Claude Desktop config"
        echo "Please add it manually through Claude Desktop settings"
    fi
else
    echo "⚠️  Claude Desktop config file not found"
    echo "Expected location: $CLAUDE_CONFIG_PATH"
fi

echo ""
echo "🎯 Next steps:"
echo "   1. Restart Claude Desktop to reload configuration"
echo "   2. Run ./scripts/test.sh to validate setup"
echo "   3. Check Claude Desktop for MCP tool availability"
