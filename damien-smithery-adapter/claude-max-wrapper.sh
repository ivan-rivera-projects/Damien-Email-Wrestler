#!/bin/bash
# Claude MAX compatibility wrapper for Damien Email Wrestler
# This wrapper ensures proper handling of Claude MAX's enhanced tool processing

# Enhanced logging for debugging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $@" >&2
}

# Set environment with Claude MAX compatibility flags
export DAMIEN_MCP_SERVER_URL="http://localhost:8892"
export DAMIEN_MCP_SERVER_API_KEY="7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
export SERVER_NAME="Damien Email Wrestler"
export SERVER_VERSION="1.0.0"
export NODE_ENV="production"
export NODE_OPTIONS="--max-old-space-size=2048"  # Increase memory for Claude MAX

# Change to the correct directory
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter

# Create logs directory if it doesn't exist
LOGS_DIR="../logs"
mkdir -p "$LOGS_DIR"

# Check if the MCP server is running
check_backend() {
    curl -s -f -m 2 "$DAMIEN_MCP_SERVER_URL/health" > /dev/null 2>&1
    return $?
}

# Start backend if not running
if ! check_backend; then
    log "⚠️  Backend server not running. Starting Damien MCP Server..."
    cd ../damien-mcp-server
    poetry run uvicorn app.main:app --port 8892 > "$LOGS_DIR/damien-mcp-server.log" 2>&1 &
    BACKEND_PID=$!
    log "Started backend with PID: $BACKEND_PID"
    cd ../damien-smithery-adapter
    
    # Wait for backend to be ready
    for i in {1..30}; do
        if check_backend; then
            log "✅ Backend server is ready"
            break
        fi
        sleep 1
    done
fi

# Ensure TypeScript is built
if [ ! -f "dist/stdioServer.js" ] || [ "src/stdioServer.ts" -nt "dist/stdioServer.js" ]; then
    log "📦 Building TypeScript..."
    npm run build 2>&1 || {
        log "❌ Build failed!"
        exit 1
    }
fi

log "🚀 Starting Damien MCP Server for Claude MAX"
log "📧 Server: $SERVER_NAME v$SERVER_VERSION"
log "🔗 Backend: $DAMIEN_MCP_SERVER_URL"

# Start with error handling optimized for Claude MAX
exec node dist/stdioServer.js "$@" 2>"$LOGS_DIR/claude-max-mcp-stderr.log"
