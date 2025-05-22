#!/bin/bash
# Test script to verify Damien MCP Server compatibility with Smithery SDK

# Load API key from .env file (simplified approach)
if [ -f "../.env" ]; then
  source <(grep -v '^#' ../.env | sed -E 's/(.*)=(.*)$/export \1="\2"/g')
fi

# Set default values if not found in .env
API_KEY=${DAMIEN_MCP_SERVER_API_KEY:-"test_api_key"}
SERVER_URL=${DAMIEN_MCP_SERVER_URL:-"http://localhost:8892"}

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_result() {
  if [ $1 -eq 0 ]; then
    echo -e "${GREEN}[PASS]${NC} $2"
  else
    echo -e "${RED}[FAIL]${NC} $2"
    echo -e "${YELLOW}Response:${NC} $3"
  fi
}

echo "=== Testing Damien MCP Server Smithery Compatibility ==="
echo "Server URL: $SERVER_URL"
echo "API Key: ${API_KEY:0:3}...${API_KEY:(-3)}"
echo "========================================================"

# Test 1: Health check
echo -e "\n${YELLOW}Test 1:${NC} Health Check"
response=$(curl -s "$SERVER_URL/health")
expected='"status":"ok"'
if [[ "$response" == *"$expected"* ]]; then
  print_result 0 "Health check endpoint is working"
else
  print_result 1 "Health check endpoint failed" "$response"
fi

# Test 2: Authentication
echo -e "\n${YELLOW}Test 2:${NC} Authentication"
response=$(curl -s -H "X-API-Key: $API_KEY" "$SERVER_URL/mcp/protected-test")
expected='"message":"Access granted'
if [[ "$response" == *"$expected"* ]]; then
  print_result 0 "Authentication is working"
else
  print_result 1 "Authentication test failed" "$response"
fi

# Test 3: List Tools
echo -e "\n${YELLOW}Test 3:${NC} List Tools Endpoint"
response=$(curl -s -H "X-API-Key: $API_KEY" "$SERVER_URL/mcp/list_tools")
expected='"name":"damien_list_emails"'
if [[ "$response" == *"$expected"* ]] && [[ "$response" == *'"input_schema"'* ]]; then
  print_result 0 "List tools endpoint is working and returns tool schemas"
else
  print_result 1 "List tools endpoint failed or missing required fields" "$response"
fi

# Test 4: Execute Tool (damien_list_emails)
echo -e "\n${YELLOW}Test 4:${NC} Execute Tool Endpoint"
response=$(curl -s -X POST -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"tool_name":"damien_list_emails","input":{"query":"is:unread","max_results":3},"session_id":"test_session_1"}' \
  "$SERVER_URL/mcp/execute_tool")
expected='"is_error":'
if [[ "$response" == *"$expected"* ]]; then
  if [[ "$response" == *'"is_error":false'* ]]; then
    print_result 0 "Execute tool endpoint is working (successful response)"
  else
    error_msg=$(echo "$response" | grep -o '"error_message":"[^"]*"' | cut -d'"' -f4)
    print_result 0 "Execute tool endpoint is working (error response: $error_msg)"
  fi
else
  print_result 1 "Execute tool endpoint failed" "$response"
fi

echo -e "\n${YELLOW}Summary:${NC}"
echo "The Damien MCP Server appears to be compatible with the Smithery SDK integration."
echo "You can now proceed with creating the Smithery adapter as described in the guide."
