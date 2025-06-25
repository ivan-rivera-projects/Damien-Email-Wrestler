#!/bin/bash

# ========================================
# Damien Email Wrestler - Claude MCP Config Sync
# ========================================
# Automatically syncs Claude Code MCP configuration with .env file
# Ensures single source of truth for API keys and configuration

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

echo "🔄 Syncing Claude Code MCP configuration with .env file..."

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

if [ -z "${DAMIEN_MCP_SERVER_URL:-}" ]; then
    echo "❌ Error: DAMIEN_MCP_SERVER_URL not found in .env file"  
    exit 1
fi

# Get minimal server path
MINIMAL_SERVER_PATH="$PROJECT_ROOT/damien-mcp-minimal/server.js"
if [ ! -f "$MINIMAL_SERVER_PATH" ]; then
    echo "❌ Error: Minimal MCP server not found at $MINIMAL_SERVER_PATH"
    exit 1
fi

echo "📋 Configuration to sync:"
echo "   API Key: ${DAMIEN_MCP_SERVER_API_KEY:0:16}..."
echo "   Server URL: $DAMIEN_MCP_SERVER_URL"
echo "   Server Path: $MINIMAL_SERVER_PATH"

# Remove existing damien-email-wrestler MCP configuration
echo "🗑️  Removing existing Claude Code MCP configuration..."
claude mcp remove damien-email-wrestler 2>/dev/null || echo "   (No existing configuration found)"

# Add new configuration with values from .env
echo "➕ Adding new Claude Code MCP configuration..."
claude mcp add damien-email-wrestler \
  "node" \
  "$MINIMAL_SERVER_PATH" \
  -e DAMIEN_MCP_SERVER_URL="$DAMIEN_MCP_SERVER_URL" \
  -e DAMIEN_MCP_SERVER_API_KEY="$DAMIEN_MCP_SERVER_API_KEY" \
  -e DAMIEN_MCP_MINIMAL_PORT="${DAMIEN_MCP_MINIMAL_PORT:-8893}" \
  -e LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo "✅ Claude Code MCP configuration synced successfully!"
echo ""
echo "🔍 Verify configuration:"
echo "   claude mcp list"
echo ""
echo "💡 To automatically sync after .env changes, run this script again"
echo "   or add it to your startup scripts"