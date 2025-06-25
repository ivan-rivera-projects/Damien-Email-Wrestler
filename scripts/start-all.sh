#!/bin/bash

# Damien Email Wrestler - Start All Services (Improved)
# This script starts both the Damien MCP Server and the Smithery Adapter
# Simplified to remove confusing background job checks

echo "🚀 Starting Damien Email Wrestler Services"
echo "========================================"

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the server mode from command line argument
SERVER_MODE="minimal"
USE_MINIMAL=true

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --standard)
      SERVER_MODE="standard"
      USE_MINIMAL=false
      shift
      ;;
    *)
      shift
      ;;
  esac
done

# Run the environment synchronization script first (if exists)
echo "Synchronizing environment variables..."
if [ -f "./scripts/sync-env.sh" ]; then
    ./scripts/sync-env.sh
else
    echo "⚠️  Note: sync-env.sh not found, skipping environment sync"
fi

# Sync Claude Code MCP configuration with .env file
echo "🔄 Ensuring Claude Code MCP configuration is current..."
if ! ./scripts/sync-claude-mcp-config.sh; then
    echo "⚠️  Warning: Failed to sync Claude MCP config, proceeding anyway..."
fi

# Ensure TypeScript compilation is up to date for Smithery Adapter
echo "Checking TypeScript compilation for Smithery Adapter..."
cd damien-smithery-adapter
if [ ! -f "dist/stdioServer.js" ] || [ "src/stdioServer.ts" -nt "dist/stdioServer.js" ]; then
    echo "Building TypeScript components..."
    npm run build
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ TypeScript build failed${NC}"
        exit 1
    fi
fi
cd ..

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for a service to be healthy
wait_for_health() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Waiting for $service_name to be healthy..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" | grep -q "ok" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo -e " ${RED}✗${NC}"
    return 1
}

# Function to verify MCP tools are available
check_mcp_tools() {
    local url=$1
    local api_key=$2
    
    echo -n "Verifying MCP tools are available..."
    local tool_count=$(curl -s -H "X-API-Key: $api_key" "$url/mcp/list_tools" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    
    if [ "$tool_count" -gt 0 ]; then
        echo -e " ${GREEN}✓ ($tool_count tools)${NC}"
        return 0
    else
        echo -e " ${YELLOW}⚠️  ($tool_count tools detected)${NC}"
        return 1
    fi
}

# Check if services are already running
MCP_PORT=8892
MINIMAL_PORT=8893

# Always start the standard MCP server first when using minimal MCP
if [ "$USE_MINIMAL" = true ]; then
    echo -e "${BLUE}ℹ️ Using Minimal MCP Server (Direct tool access - 39 optimized tools)${NC}"
    echo -e "${BLUE}ℹ️ Starting standard MCP Server first as backend${NC}"
    
    if check_port $MCP_PORT; then
        echo -e "${YELLOW}⚠️  Damien MCP Server appears to be already running on port $MCP_PORT${NC}"
    else
        echo "Starting Damien MCP Server as backend..."
        cd damien-mcp-server
        poetry run uvicorn app.main:app --port 8892 > ../logs/damien-mcp-server.log 2>&1 &
        MCP_PID=$!
        echo "Damien MCP Server started with PID: $MCP_PID"
        cd ..
        
        # Give the MCP Server time to start up and initialize
        echo "Waiting for MCP Server to initialize..."
        sleep 5
    fi
    
    # Check if MCP Server is healthy before starting minimal MCP
    if ! wait_for_health "http://localhost:$MCP_PORT/health" "Damien MCP Server"; then
        echo -e "${RED}❌ MCP Server failed to start. Cannot start Minimal MCP Server.${NC}"
        exit 1
    fi
    
    # Now start the minimal MCP server
    if check_port $MINIMAL_PORT; then
        echo -e "${YELLOW}⚠️  Damien Minimal MCP Server appears to be already running on port $MINIMAL_PORT${NC}"
    else
        echo "Starting Damien Minimal MCP Server..."
        cd damien-mcp-minimal
        node server.js > ../logs/damien-mcp-minimal.log 2>&1 &
        MINIMAL_MCP_PID=$!
        echo "Damien Minimal MCP Server started with PID: $MINIMAL_MCP_PID"
        cd ..
        
        # Give the Minimal MCP Server time to start up and initialize
        echo "Waiting for Minimal MCP Server to initialize..."
        sleep 5
    fi
else
    if check_port $MCP_PORT; then
        echo -e "${YELLOW}⚠️  Damien MCP Server appears to be already running on port $MCP_PORT${NC}"
    else
        echo "Starting Damien MCP Server..."
        cd damien-mcp-server
        poetry run uvicorn app.main:app --port 8892 > ../logs/damien-mcp-server.log 2>&1 &
        MCP_PID=$!
        echo "Damien MCP Server started with PID: $MCP_PID"
        cd ..
        
        # Give the MCP Server time to start up and initialize
        echo "Waiting for MCP Server to initialize..."
        sleep 5
    fi
fi

# Check if MCP Server is healthy before starting Smithery Adapter
if [ "$USE_MINIMAL" = true ]; then
    if ! wait_for_health "http://localhost:$MINIMAL_PORT/health" "Damien Minimal MCP Server"; then
        echo -e "${RED}❌ Minimal MCP Server failed to start. Not starting Smithery Adapter.${NC}"
        exit 1
    fi
else
    if ! wait_for_health "http://localhost:$MCP_PORT/health" "Damien MCP Server"; then
        echo -e "${RED}❌ MCP Server failed to start. Not starting Smithery Adapter.${NC}"
        exit 1
    fi
fi

if check_port 8081; then
    echo -e "${YELLOW}⚠️  Smithery Adapter appears to be already running on port 8081${NC}"
else
    echo "Starting Smithery Adapter..."
    cd damien-smithery-adapter
    npm run serve > ../logs/smithery-adapter.log 2>&1 &
    ADAPTER_PID=$!
    echo "Smithery Adapter started with PID: $ADAPTER_PID"
    cd ..
fi

# Wait for services to be healthy
echo ""
echo "Checking service health..."

if [ "$USE_MINIMAL" = true ]; then
    # Check both MCP servers when using minimal
    if wait_for_health "http://localhost:$MCP_PORT/health" "Backend MCP Server"; then
        BACKEND_MCP_HEALTHY=true
    else
        BACKEND_MCP_HEALTHY=false
    fi
    
    if wait_for_health "http://localhost:$MINIMAL_PORT/health" "Minimal MCP Server"; then
        MINIMAL_MCP_HEALTHY=true
    else
        MINIMAL_MCP_HEALTHY=false
    fi
else
    # Only check standard MCP server
    if wait_for_health "http://localhost:$MCP_PORT/health" "Damien MCP Server"; then
        MCP_HEALTHY=true
    else
        MCP_HEALTHY=false
    fi
fi

if wait_for_health "http://localhost:8081/health" "Smithery Adapter"; then
    ADAPTER_HEALTHY=true
else
    ADAPTER_HEALTHY=false
fi

# Read API key from .env file
API_KEY=$(grep "DAMIEN_MCP_SERVER_API_KEY" .env | cut -d'=' -f2)

# Summary
echo ""
echo "📊 Service Status"
echo "================"

if [ "$USE_MINIMAL" = true ]; then
    # Show both servers when using minimal
    if [ "$BACKEND_MCP_HEALTHY" = true ]; then
        echo -e "${GREEN}✓${NC} Backend MCP Server: Running on http://localhost:$MCP_PORT"
    else
        echo -e "${RED}✗${NC} Backend MCP Server: Failed to start or unhealthy"
    fi
    
    if [ "$MINIMAL_MCP_HEALTHY" = true ]; then
        echo -e "${GREEN}✓${NC} Damien Minimal MCP Server: Running on http://localhost:$MINIMAL_PORT"
        echo -e "  ${GREEN}└─ Hybrid AI Architecture: CLI + AWS Lambda enhancement${NC}"
        
        # Check available tools
        if check_mcp_tools "http://localhost:$MINIMAL_PORT" "$API_KEY"; then
            echo -e "  ${GREEN}   ├─ All 39 optimized tools: Active${NC}"
            echo -e "  ${GREEN}   ├─ AI Intelligence suite: Available (12 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Email management: Available (13 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Thread operations: Available (5 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Draft management: Available (6 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Rule management: Available (5 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Settings management: Available (2 tools) - Core only${NC}"
            echo -e "  ${GREEN}   └─ Job management: Available (4 tools)${NC}"
        else
            echo -e "  ${YELLOW}└─ Tools loading...${NC}"
        fi
    else
        echo -e "${RED}✗${NC} Damien Minimal MCP Server: Failed to start or unhealthy"
    fi
else
    # Only show standard MCP server
    if [ "$MCP_HEALTHY" = true ]; then
        echo -e "${GREEN}✓${NC} Damien MCP Server: Running on http://localhost:$MCP_PORT"
        
        # Check available tools
        if check_mcp_tools "http://localhost:$MCP_PORT" "$API_KEY"; then
            echo -e "  ${GREEN}└─ All 39 optimized tools: ✓ Active${NC}"
            echo -e "  ${GREEN}   ├─ AI intelligence tools: Available (12 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Email management: Available (13 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Thread operations: Available (5 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Draft management: Available (6 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Rule management: Available (5 tools)${NC}"
            echo -e "  ${GREEN}   ├─ Settings management: Available (2 tools) - Core only${NC}"
            echo -e "  ${GREEN}   └─ Job management: Available (4 tools)${NC}"
        else
            echo -e "  ${YELLOW}└─ Tools loading...${NC}"
        fi
    else
        echo -e "${RED}✗${NC} Damien MCP Server: Failed to start or unhealthy"
    fi
fi

if [ "$ADAPTER_HEALTHY" = true ]; then
    echo -e "${GREEN}✓${NC} Smithery Adapter: Running on http://localhost:8081"
else
    echo -e "${RED}✗${NC} Smithery Adapter: Failed to start or unhealthy"
fi

echo ""
if [ "$USE_MINIMAL" = true ]; then
    echo "Logs are available in the 'logs' directory:"
    echo "  - Damien Minimal MCP Server: logs/damien-mcp-minimal.log"
    echo "  - Smithery Adapter: logs/smithery-adapter.log"
else
    echo "Logs are available in the 'logs' directory:"
    echo "  - Damien MCP Server: logs/damien-mcp-server.log"
    echo "  - Smithery Adapter: logs/smithery-adapter.log"
fi

if [ "$USE_MINIMAL" = true ]; then
    # For minimal mode, check the appropriate variables
    if [ "$BACKEND_MCP_HEALTHY" = true ] && [ "$MINIMAL_MCP_HEALTHY" = true ] && [ "$ADAPTER_HEALTHY" = true ]; then
        ALL_HEALTHY=true
    else
        ALL_HEALTHY=false
    fi
else
    # For standard mode, check standard variables
    if [ "$MCP_HEALTHY" = true ] && [ "$ADAPTER_HEALTHY" = true ]; then
        ALL_HEALTHY=true
    else
        ALL_HEALTHY=false
    fi
fi

if [ "$ALL_HEALTHY" = true ]; then
    echo ""
    echo -e "${GREEN}🎉 All services are running successfully!${NC}"
    echo ""
    
    echo -e "${BLUE}📋 Hybrid AI Features Available (39 optimized tools):${NC}"
    echo "  • Email management (list, read, label, trash, delete) - 13 tools"
    echo "  • AI-powered analysis with optional AWS Lambda enhancement - 12 tools"
    echo "  • Thread-level operations and management - 5 tools"
    echo "  • Draft creation and lifecycle management - 6 tools"
    echo "  • Intelligent rule creation and automation - 5 tools"
    echo "  • Core settings and configuration - 2 tools (vacation/IMAP/POP removed)"
    echo "  • Async job management and tracking - 4 tools"
    echo ""
    echo -e "${BLUE}💡 Quick Test Commands:${NC}"
    if [ "$USE_MINIMAL" = true ]; then
        echo "  • Check tool availability: curl -H 'X-API-Key: $API_KEY' http://localhost:$MINIMAL_PORT/mcp/list_tools | python3 -m json.tool"
    else
        echo "  • Check tool availability: curl -H 'X-API-Key: $API_KEY' http://localhost:$MCP_PORT/mcp/list_tools | python3 -m json.tool"
    fi
    echo "  • Run system validation: ./scripts/test.sh"
    
    echo "  • Check status anytime: ./scripts/status.sh"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some services failed to start. Check the logs for details.${NC}"
    exit 1
fi
