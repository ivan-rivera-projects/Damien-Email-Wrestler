#\!/bin/bash
# Enhanced Claude MAX compatibility wrapper for Damien Email Wrestler
# This wrapper ensures proper handling of Claude MAX's enhanced tool processing

# Enhanced logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $@" >&2
}

# Create logs directory if it doesn't exist
LOGS_DIR="/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/logs"
mkdir -p "$LOGS_DIR"

# Set strict environment variables with fixed naming for Claude MAX  
export DAMIEN_MCP_SERVER_URL="http://localhost:8892"
export DAMIEN_MCP_SERVER_API_KEY="7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
export SERVER_NAME="Damien_Email_Wrestler" # Underscores instead of spaces
export SERVER_VERSION="2.0.0"
export NODE_ENV="production"
export NODE_OPTIONS="--max-old-space-size=2048"  # Increase memory for Claude MAX

# Change to the correct directory
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter

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
    BACKEND_PID=$\!
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

# Make sure the new enhanced script exists and is executable
if [ ! -f "claude-max-fix-enhanced.js" ]; then
    log "❌ Missing claude-max-fix-enhanced.js script!"
    exit 1
fi

chmod +x claude-max-fix-enhanced.js

log "🚀 Starting Damien MCP Server for Claude MAX (Fixed version)"
log "📧 Server: $SERVER_NAME v$SERVER_VERSION"
log "🔗 Backend: $DAMIEN_MCP_SERVER_URL"

# Start with error handling optimized for Claude MAX
exec node claude-max-fix-enhanced.js "$@" 2>"$LOGS_DIR/claude-max-mcp-stderr.log"
