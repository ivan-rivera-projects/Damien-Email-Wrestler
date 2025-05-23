#!/bin/bash

# Damien Email Wrestler - Start All Services
# This script starts both the Damien MCP Server and the Smithery Adapter

echo "🚀 Starting Damien Email Wrestler Services"
echo "========================================"

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
    echo -e "${GREEN}🎉 All services are running! You can now run ./scripts/test.sh${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some services failed to start. Check the logs for details.${NC}"
    exit 1
fi
