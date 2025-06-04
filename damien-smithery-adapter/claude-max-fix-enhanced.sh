#!/bin/bash
# Enhanced Claude MAX compatibility wrapper for Damien Email Wrestler
# Addresses all identified issues and provides robust error handling

# Strict error handling
set -euo pipefail

# Enhanced logging function with proper stderr redirection
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

# Get absolute paths to prevent path resolution issues
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Enhanced environment variable setup with validation
validate_env() {
    local required_vars=("DAMIEN_MCP_SERVER_URL" "DAMIEN_MCP_SERVER_API_KEY")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log "❌ Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi
    
    return 0
}

# Set environment variables with proper defaults
export DAMIEN_MCP_SERVER_URL="${DAMIEN_MCP_SERVER_URL:-http://localhost:8892}"
export DAMIEN_MCP_SERVER_API_KEY="${DAMIEN_MCP_SERVER_API_KEY:-}"
export SERVER_NAME="${SERVER_NAME:-Damien_Email_Wrestler}"
export SERVER_VERSION="${SERVER_VERSION:-2.0.0}"
export NODE_ENV="${NODE_ENV:-production}"
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=2048 --no-warnings}"

# Validate environment
if ! validate_env; then
    log "❌ Environment validation failed"
    exit 1
fi

log "🚀 Starting Damien MCP Server for Claude MAX"
log "📧 Server: $SERVER_NAME v$SERVER_VERSION"
log "🔗 Backend: $DAMIEN_MCP_SERVER_URL"
log "📁 Project Root: $PROJECT_ROOT"

# Change to the adapter directory
cd "$SCRIPT_DIR"

# Function to check backend health with retries
check_backend_health() {
    local max_attempts=5
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f -m 3 "$DAMIEN_MCP_SERVER_URL/health" > /dev/null 2>&1; then
            return 0
        fi
        log "⏳ Backend health check attempt $attempt/$max_attempts failed"
        ((attempt++))
        sleep 1
    done
    
    return 1
}

# Start backend if not running
if ! check_backend_health; then
    log "⚠️  Backend server not responding. Starting Damien MCP Server..."
    
    # Change to MCP server directory and start backend
    cd "$PROJECT_ROOT/damien-mcp-server"
    
    if [[ ! -f "pyproject.toml" ]]; then
        log "❌ pyproject.toml not found in damien-mcp-server directory"
        exit 1
    fi
    
    # Start backend in background with proper error handling
    {
        poetry run uvicorn app.main:app --port 8892 --host 127.0.0.1 \
            --access-log --log-level info \
            > "$LOGS_DIR/damien-mcp-server.log" 2>&1
    } &
    
    BACKEND_PID=$!
    log "📦 Started backend server with PID: $BACKEND_PID"
    
    # Return to adapter directory
    cd "$SCRIPT_DIR"
    
    # Wait for backend to be ready with timeout
    log "⏳ Waiting for backend server to become ready..."
    local wait_count=0
    while [[ $wait_count -lt 30 ]]; do
        if check_backend_health; then
            log "✅ Backend server is ready and healthy"
            break
        fi
        
        if [[ $wait_count -eq 29 ]]; then
            log "❌ Backend server failed to start within 30 seconds"
            log "📄 Check logs: $LOGS_DIR/damien-mcp-server.log"
            exit 1
        fi
        
        ((wait_count++))
        sleep 1
    done
else
    log "✅ Backend server is already running and healthy"
fi

# Verify Node.js dependencies
if [[ ! -f "package.json" ]]; then
    log "❌ package.json not found in adapter directory"
    exit 1
fi

if [[ ! -d "node_modules" ]] || [[ ! -f "node_modules/.package-lock.json" ]]; then
    log "📦 Installing/updating Node.js dependencies..."
    npm install --production --silent
fi

# Verify the main MCP script exists
if [[ ! -f "claude-max-fix.js" ]]; then
    log "❌ claude-max-fix.js not found in adapter directory"
    exit 1
fi

# Make sure script is executable (though not needed for node)
chmod +x "claude-max-fix.js"

# Set up proper signal handling for graceful shutdown
cleanup() {
    log "🛑 Received shutdown signal, cleaning up..."
    
    # Kill any child processes
    if [[ -n "${BACKEND_PID:-}" ]]; then
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            log "🔄 Stopping backend server (PID: $BACKEND_PID)"
            kill -TERM "$BACKEND_PID" 2>/dev/null || true
            wait "$BACKEND_PID" 2>/dev/null || true
        fi
    fi
    
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM SIGQUIT

# Final validation before starting MCP server
log "🔍 Performing final validation..."

# Test API key
if ! curl -s -f -m 3 -H "X-API-Key: $DAMIEN_MCP_SERVER_API_KEY" \
    "$DAMIEN_MCP_SERVER_URL/mcp/list_tools" > /dev/null 2>&1; then
    log "❌ API key validation failed"
    exit 1
fi

log "✅ All validations passed"
log "🎯 Starting Claude MAX compatible MCP server..."

# Start the MCP server with enhanced error handling and logging
exec node claude-max-fix.js "$@" 2>>"$LOGS_DIR/claude-max-mcp-stderr.log"
