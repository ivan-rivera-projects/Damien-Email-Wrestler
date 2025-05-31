#!/bin/bash

# Damien Email Wrestler - Stop All Services
# This script stops both the Damien MCP Server and the Smithery Adapter

echo "🛑 Stopping Damien Email Wrestler Services"
echo "========================================"

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to stop service on a port
stop_service_on_port() {
    local port=$1
    local service_name=$2
    
    # Find PIDs using the port
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -z "$pids" ]; then
        echo -e "${YELLOW}⚠️  No process found on port $port ($service_name)${NC}"
        return 1
    fi
    
    echo "Stopping $service_name on port $port..."
    for pid in $pids; do
        echo "  Killing process $pid"
        kill -TERM $pid 2>/dev/null || kill -KILL $pid 2>/dev/null
    done
    
    # Wait a moment and verify
    sleep 2
    if lsof -ti :$port > /dev/null 2>&1; then
        echo -e "${RED}✗ Failed to stop $service_name${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $service_name stopped${NC}"
        return 0
    fi
}

# Stop services
echo ""
#stop_service_on_port 8894 "Damien MCP Server"
stop_service_on_port 8892 "Damien MCP Server"
stop_service_on_port 8081 "Smithery Adapter"

# Also look for any npm processes related to our services
echo ""
echo "Checking for any remaining Damien processes..."
remaining=$(ps aux | grep -E "(damien-mcp-server|damien-smithery-adapter)" | grep -v grep | grep -v stop-all.sh)

if [ -n "$remaining" ]; then
    echo -e "${YELLOW}Found remaining processes:${NC}"
    echo "$remaining"
    echo ""
    read -p "Kill these processes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$remaining" | awk '{print $2}' | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✓ Processes killed${NC}"
    fi
else
    echo -e "${GREEN}✓ No remaining Damien processes found${NC}"
fi

echo ""
echo "📊 Service Status"
echo "================"

# Check if services are still running
if lsof -ti :8894 > /dev/null 2>&1; then
    echo -e "${RED}✗ Damien MCP Server: Still running on port 8894${NC}"
elif lsof -ti :8892 > /dev/null 2>&1; then
    echo -e "${RED}✗ Damien MCP Server: Still running on port 8892${NC}"
else
    echo -e "${GREEN}✓ Damien MCP Server: Stopped${NC}"
fi

if lsof -ti :8081 > /dev/null 2>&1; then
    echo -e "${RED}✗ Smithery Adapter: Still running on port 8081${NC}"
else
    echo -e "${GREEN}✓ Smithery Adapter: Stopped${NC}"
fi

echo ""
echo "🛑 All services have been stopped."
