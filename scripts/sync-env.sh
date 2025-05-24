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
