#!/bin/bash
# Enhanced Claude MCP Integration Script for Damien Email Wrestler
# Compatible with Claude Max account requirements

# Enhanced logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $@" >&2
}

# Create logs directory if it doesn't exist
LOGS_DIR="/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/logs"
mkdir -p "$LOGS_DIR"

# Set strict environment variables  
export DAMIEN_MCP_SERVER_URL="http://localhost:8892"
export DAMIEN_MCP_SERVER_API_KEY="7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
export SERVER_NAME="Damien Email Wrestler"
export SERVER_VERSION="1.0.0"
export NODE_ENV="production"

# Change to the correct directory
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter

# Verify health before starting
log "🔍 Performing health check..."
if ! ./health-check.sh >/dev/null 2>&1; then
    log "❌ Health check failed. Attempting to start Damien MCP Server..."
    # Try to start the backend if it's not running
    # You may need to adjust this command based on your setup
    log "⚠️  Backend server health check failed - please ensure Damien MCP Server is running"
fi

# Pre-flight checks
if [ ! -f "dist/stdioServer.js" ]; then
    log "❌ Missing dist/stdioServer.js - running build..."
    npm run build || {
        log "❌ Build failed!"
        exit 1
    }
fi

log "🚀 Starting Damien MCP Server (stdio mode)..."
log "📧 Server: $SERVER_NAME v$SERVER_VERSION"  
log "🔗 Backend: $DAMIEN_MCP_SERVER_URL"
log "🔑 API Key: ${DAMIEN_MCP_SERVER_API_KEY:0:16}..."

# Start the stdio server with proper error handling
# Route stderr to log file while keeping stdout clean for MCP communication
exec node dist/stdioServer.js "$@" 2>"$LOGS_DIR/claude-mcp-stderr.log"
