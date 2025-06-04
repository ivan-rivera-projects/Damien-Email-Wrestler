#!/bin/bash
# Simple test wrapper for Damien MCP Server

# Create logs directory if it doesn't exist
LOGS_DIR="/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/logs"
mkdir -p "$LOGS_DIR"

# Set environment variables
export DAMIEN_MCP_SERVER_URL="http://localhost:8892"
export DAMIEN_MCP_SERVER_API_KEY="7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
export SERVER_NAME="Damien_Email_Wrestler"
export SERVER_VERSION="2.0.0"
export NODE_ENV="production"
export NODE_OPTIONS="--max-old-space-size=2048"

# Change to the correct directory
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter

# Log to stderr for Claude to see
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Damien MCP Server" >&2

# Start the Node.js script directly
exec node claude-max-minimal.js
