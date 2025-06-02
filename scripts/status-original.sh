#!/bin/bash

# Damien Email Wrestler - Service Status Check
# This script checks the status of all Damien services

echo "📊 Damien Email Wrestler Service Status"
echo "====================================="

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if API key is set
if [ -z "$DAMIEN_MCP_SERVER_API_KEY" ]; then
    echo "⚠️  Warning: DAMIEN_MCP_SERVER_API_KEY not found in .env file"
    echo "Some status checks may be limited"
fi

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_service() {
    local port=$1
    local name=$2
    local url=$3
    
    echo -n "Checking $name (port $port)... "
    
    # Check if port is in use
    if ! lsof -i :$port > /dev/null 2>&1; then
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
    
    # Check health endpoint
    if curl -s "$url" | grep -q "ok" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        
        # Get additional info if available
        if [ "$port" = "8892" ]; then
            # For MCP server, check tool count
            if [ -n "$DAMIEN_MCP_SERVER_API_KEY" ]; then
                TOOLS=$(curl -s -H "X-API-Key: $DAMIEN_MCP_SERVER_API_KEY" http://localhost:8892/mcp/list_tools 2>/dev/null | grep -o '"name"' | wc -l)
                echo "  └─ Available tools: $TOOLS"
            else
                echo "  └─ Tool count unavailable (API key not set)"
            fi
        elif [ "$port" = "8081" ]; then
            # For Smithery adapter, check if connected to MCP
            if curl -s http://localhost:8081/tools | grep -q "damien_" > /dev/null 2>&1; then
                echo "  └─ Connected to Damien MCP Server ✓"
            else
                echo -e "  └─ ${YELLOW}Warning: Not connected to Damien MCP Server${NC}"
            fi
        fi
        return 0
    else
        echo -e "${YELLOW}✗ Running but unhealthy${NC}"
        return 1
    fi
}

# Check services
echo ""
check_service 8892 "Damien MCP Server" "http://localhost:8892/health"
MCP_STATUS=$?

check_service 8081 "Smithery Adapter" "http://localhost:8081/health"
ADAPTER_STATUS=$?

# Check logs directory
echo ""
echo "Log files:"
if [ -d "logs" ]; then
    echo "  └─ logs/ directory exists"
    if [ -f "logs/damien-mcp-server.log" ]; then
        echo "      ├─ damien-mcp-server.log ($(wc -l < logs/damien-mcp-server.log) lines)"
    fi
    if [ -f "logs/smithery-adapter.log" ]; then
        echo "      └─ smithery-adapter.log ($(wc -l < logs/smithery-adapter.log) lines)"
    fi
else
    echo -e "  └─ ${YELLOW}logs/ directory not found${NC}"
fi

# Summary and recommendations
echo ""
echo "Summary:"
echo "--------"

if [ $MCP_STATUS -eq 0 ] && [ $ADAPTER_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ All services are running and healthy!${NC}"
    echo ""
    echo "You can now:"
    echo "  • Run tests: ./scripts/test.sh"
    echo "  • Use the API: curl http://localhost:8081/tools"
    echo "  • Connect Claude Desktop to the Smithery Adapter"
else
    echo -e "${RED}✗ Some services are not running properly${NC}"
    echo ""
    echo "To start all services, run:"
    echo -e "  ${GREEN}./scripts/start-all.sh${NC}"
    echo ""
    echo "To stop all services, run:"
    echo -e "  ${GREEN}./scripts/stop-all.sh${NC}"
fi
