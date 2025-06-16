#!/bin/bash

# Damien Email Wrestler - Enhanced Status Check
# Provides comprehensive status of all platform components

echo "📊 Damien Platform Status Check"
echo "==============================="

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check service health
check_service() {
    local url=$1
    local name=$2
    local port=$3
    
    if curl -s --connect-timeout 2 --max-time 5 "$url" | grep -q "ok" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name: Running on port $port"
        return 0
    else
        echo -e "${RED}✗${NC} $name: Not responding on port $port"
        return 1
    fi
}

# Function to count tools
get_tool_count() {
    local api_key=$1
    curl -s --connect-timeout 2 --max-time 5 -H "X-API-Key: $api_key" "http://localhost:8892/mcp/list_tools" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0"
}

# Check services
echo ""
echo "🔍 Service Health Checks"
echo "------------------------"

MCP_HEALTHY=false
ADAPTER_HEALTHY=false

if check_service "http://localhost:8892/health" "Damien MCP Server" "8892"; then
    MCP_HEALTHY=true
fi

if check_service "http://localhost:8081/health" "Smithery Adapter" "8081"; then
    ADAPTER_HEALTHY=true
fi

# Check tools if MCP is healthy
if [ "$MCP_HEALTHY" = true ]; then
    API_KEY=$(grep "DAMIEN_MCP_SERVER_API_KEY" .env | cut -d'=' -f2)
    TOOL_COUNT=$(get_tool_count "$API_KEY")
    echo -e "  ${BLUE}└─ Available tools: $TOOL_COUNT${NC}"
fi

# Process information
echo ""
echo "🔧 Process Information"
echo "----------------------"

# Check for running processes
MCP_PROCESS=$(ps aux | grep "uvicorn.*8892" | grep -v grep | awk '{print $2}')
ADAPTER_PROCESS=$(ps aux | grep "node.*damien-smithery-adapter" | grep -v grep | awk '{print $2}')

if [ -n "$MCP_PROCESS" ]; then
    echo -e "${GREEN}✓${NC} MCP Server process: PID $MCP_PROCESS"
else
    echo -e "${RED}✗${NC} MCP Server process: Not found"
fi

if [ -n "$ADAPTER_PROCESS" ]; then
    echo -e "${GREEN}✓${NC} Smithery Adapter process: PID $ADAPTER_PROCESS"
else
    echo -e "${RED}✗${NC} Smithery Adapter process: Not found"
fi

# Log files
echo ""
echo "📝 Recent Log Activity"
echo "----------------------"

if [ -f "logs/damien-mcp-server.log" ]; then
    echo "📄 MCP Server (last 3 lines):"
    tail -3 logs/damien-mcp-server.log | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  MCP Server log not found${NC}"
fi

echo ""
if [ -f "logs/smithery-adapter.log" ]; then
    echo "📄 Smithery Adapter (last 3 lines):"
    tail -3 logs/smithery-adapter.log | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  Smithery Adapter log not found${NC}"
fi

# Overall status
echo ""
echo "🎯 Overall Status"
echo "----------------"

if [ "$MCP_HEALTHY" = true ] && [ "$ADAPTER_HEALTHY" = true ]; then
    echo -e "${GREEN}✅ System Status: HEALTHY${NC}"
    echo -e "${GREEN}   All services operational and ready for use${NC}"
elif [ "$MCP_HEALTHY" = true ]; then
    echo -e "${YELLOW}⚠️  System Status: PARTIAL${NC}"
    echo -e "${YELLOW}   MCP Server running, Smithery Adapter needs attention${NC}"
elif [ "$ADAPTER_HEALTHY" = true ]; then
    echo -e "${YELLOW}⚠️  System Status: PARTIAL${NC}"
    echo -e "${YELLOW}   Smithery Adapter running, MCP Server needs attention${NC}"
else
    echo -e "${RED}❌ System Status: DOWN${NC}"
    echo -e "${RED}   Both services need to be started${NC}"
fi

echo ""
echo "💡 Management Commands:"
echo "  • Start services: ./scripts/start-all.sh"
echo "  • Stop services: ./scripts/stop-all.sh"
echo "  • View logs: tail -f logs/damien-mcp-server.log"
if [ -n "$API_KEY" ]; then
    echo "  • Test tools: curl -H 'X-API-Key: $API_KEY' http://localhost:8892/mcp/list_tools"
else
    echo "  • Test tools: curl -H 'X-API-Key: YOUR_API_KEY' http://localhost:8892/mcp/list_tools"
fi
