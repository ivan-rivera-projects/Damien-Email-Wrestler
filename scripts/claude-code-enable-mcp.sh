#!/bin/bash
# Enable MCP integration for Claude Code
# Security: Reads API key from .env file

set -e

# Get API key from .env file
if [ -f "damien-mcp-server/.env" ]; then
    API_KEY=$(grep DAMIEN_MCP_SERVER_API_KEY damien-mcp-server/.env | cut -d '=' -f2)
else
    echo "❌ Error: damien-mcp-server/.env not found"
    exit 1
fi

claude mcp add damien-email-wrestler \
  "node" \
  "$(pwd)/damien-mcp-minimal/server.js" \
  -e DAMIEN_MCP_SERVER_URL=http://localhost:8892 \
  -e DAMIEN_MCP_SERVER_API_KEY=$API_KEY \
  -e DAMIEN_MCP_MINIMAL_PORT=8893 \
  -e LOG_LEVEL=INFO

echo "✅ MCP integration enabled"
