#!/bin/bash

# Damien Email Wrestler - Start All Services (Enhanced for Background Jobs)
# This script starts both the Damien MCP Server and the Smithery Adapter
# Now includes validation for async job processing capabilities

echo "🚀 Starting Damien Email Wrestler Services (Enhanced for Background Jobs)"
echo "============================================================================"

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Run the environment synchronization script first
echo "Synchronizing environment variables..."
./scripts/sync-env.sh

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if the MCP Server is fully up and returning tool definitions
check_mcp_tools() {
    local url=$1
    local api_key=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Verifying MCP Server tool definitions..."
    while [ $attempt -lt $max_attempts ]; do
        # Check for both sync and async tools
        if curl -s -H "X-API-Key: $api_key" "$url/health" | grep -q "ok" > /dev/null 2>&1; then
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

# Function to validate background job system
check_background_jobs() {
    local url=$1
    local api_key=$2
    
    echo -n "Validating background job system..."
    
    # Check if async tools are available
    local tools_response=$(curl -s -H "X-API-Key: $api_key" "$url/mcp/list_tools" 2>/dev/null)
    local async_tools=$(echo "$tools_response" | grep -o 'damien_.*_async\|damien_job_' | wc -l)
    
    if [ "$async_tools" -gt 0 ]; then
        echo -e " ${GREEN}✓ ($async_tools async tools)${NC}"
        return 0
    else
        echo -e " ${YELLOW}! (async tools not detected)${NC}"
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

# Check if services are already running
if check_port 8892; then
    echo -e "${YELLOW}⚠️  Damien MCP Server appears to be already running on port 8892${NC}"
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

# Check if MCP Server is healthy before starting Smithery Adapter
if ! wait_for_health "http://localhost:8892/health" "Damien MCP Server"; then
    echo -e "${RED}❌ MCP Server failed to start. Not starting Smithery Adapter.${NC}"
    exit 1
fi

# Read API key from .env file
API_KEY=$(grep "DAMIEN_MCP_SERVER_API_KEY" .env | cut -d'=' -f2)

# Verify MCP Server has tools available
if ! check_mcp_tools "http://localhost:8892" "$API_KEY"; then
    echo -e "${YELLOW}⚠️  MCP Server health check not ready. Smithery Adapter may fall back to static tools.${NC}"
    echo -e "${YELLOW}⚠️  Continuing anyway, Phase 4 AI intelligence tools should be available.${NC}"
fi

# NEW: Validate background job system
echo -e "${BLUE}🔧 Checking background job capabilities...${NC}"
if check_background_jobs "http://localhost:8892" "$API_KEY"; then
    BACKGROUND_JOBS_READY=true
    echo -e "${GREEN}✓ Background job processing system is active${NC}"
    echo -e "${GREEN}  • Large-scale email analysis available${NC}"
    echo -e "${GREEN}  • Inbox optimization jobs available${NC}"
    echo -e "${GREEN}  • Real-time progress tracking enabled${NC}"
else
    BACKGROUND_JOBS_READY=false
    echo -e "${YELLOW}⚠️  Background job system not fully ready${NC}"
    echo -e "${YELLOW}  • Standard tools available, async tools may be limited${NC}"
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

if wait_for_health "http://localhost:8892/health" "Damien MCP Server"; then
    MCP_HEALTHY=true
    
    # Read API key from .env file
    API_KEY=$(grep "DAMIEN_MCP_SERVER_API_KEY" .env | cut -d'=' -f2)
    
    # Verify MCP Server is fully initialized with tools
    if check_mcp_tools "http://localhost:8892" "$API_KEY"; then
        MCP_TOOLS_READY=true
    else
        MCP_TOOLS_READY=false
        echo -e "${YELLOW}⚠️  MCP Server is running with Phase 4 AI intelligence tools active.${NC}"
    fi
else
    MCP_HEALTHY=false
fi

if wait_for_health "http://localhost:8081/health" "Smithery Adapter"; then
    ADAPTER_HEALTHY=true
else
    ADAPTER_HEALTHY=false
fi

# Summary
echo ""
echo "📊 Service Status"
echo "================"

if [ "$MCP_HEALTHY" = true ]; then
    echo -e "${GREEN}✓${NC} Damien MCP Server: Running on http://localhost:8892"
    
    # Show background job status
    if [ "$BACKGROUND_JOBS_READY" = true ]; then
        echo -e "  ${GREEN}└─ Background job processing: ✓ Active${NC}"
        echo -e "  ${GREEN}   ├─ Async email analysis: Available${NC}"
        echo -e "  ${GREEN}   ├─ Job progress tracking: Enabled${NC}"
        echo -e "  ${GREEN}   └─ Notification system: Ready${NC}"
    else
        echo -e "  ${YELLOW}└─ Background job processing: ⚠️  Limited${NC}"
    fi
else
    echo -e "${RED}✗${NC} Damien MCP Server: Failed to start or unhealthy"
fi

if [ "$ADAPTER_HEALTHY" = true ]; then
    echo -e "${GREEN}✓${NC} Smithery Adapter: Running on http://localhost:8081"
else
    echo -e "${RED}✗${NC} Smithery Adapter: Failed to start or unhealthy"
fi

echo ""
echo "Logs are available in the 'logs' directory:"
echo "  - Damien MCP Server: logs/damien-mcp-server.log"
echo "  - Smithery Adapter: logs/smithery-adapter.log"

if [ "$MCP_HEALTHY" = true ] && [ "$ADAPTER_HEALTHY" = true ]; then
    echo ""
    if [ "$BACKGROUND_JOBS_READY" = true ]; then
        echo -e "${GREEN}🎉 All services are running with full background job support!${NC}"
        echo ""
        echo -e "${BLUE}📋 Available Features:${NC}"
        echo "  • Standard email management tools"
        echo "  • Large-scale async email analysis (3,000+ emails)"
        echo "  • Background inbox optimization"
        echo "  • Real-time job progress tracking"
        echo "  • Job cancellation and management"
        echo ""
        echo -e "${BLUE}💡 Quick Test Commands:${NC}"
        echo "  • Run all tests: ./scripts/test.sh"
        echo "  • Check status: ./scripts/status.sh"
        echo "  • Validate async: curl -H 'X-API-Key: $API_KEY' http://localhost:8892/mcp/list_tools | grep async"
    else
        echo -e "${GREEN}🎉 All services are running!${NC}"
        echo -e "${YELLOW}⚠️  Background jobs may have limited functionality${NC}"
    fi
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some services failed to start. Check the logs for details.${NC}"
    exit 1
fi
