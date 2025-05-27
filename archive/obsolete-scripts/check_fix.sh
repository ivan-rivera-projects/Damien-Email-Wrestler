#!/bin/bash
# Script to test the API routing fix

echo "===== TESTING THREAD TOOLS API ROUTING FIX ====="
echo ""

# Test listing all available tools
echo "1. Checking available tools..."
curl -s -X GET -H "X-API-Key: 7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f" \
     http://localhost:8895/mcp/list_tools | grep -c "damien_list_threads"

if [ $? -eq 0 ]; then
    echo "✅ Thread tools are listed in available tools"
else
    echo "❌ Thread tools not found in available tools list"
fi

echo ""
echo "2. Testing damien_list_threads execution..."
curl -s -X POST -H "Content-Type: application/json" \
     -H "X-API-Key: 7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f" \
     -d '{"tool_name": "damien_list_threads", "input": {"max_results": 3}, "session_id": "test"}' \
     http://localhost:8895/mcp/execute_tool | jq .

echo ""
echo "3. Testing damien_get_thread_details execution..."
# First get a thread ID from list_threads
THREAD_ID=$(curl -s -X POST -H "Content-Type: application/json" \
            -H "X-API-Key: 7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f" \
            -d '{"tool_name": "damien_list_threads", "input": {"max_results": 1}, "session_id": "test"}' \
            http://localhost:8895/mcp/execute_tool | jq -r '.output.threads[0].id')

if [ -z "$THREAD_ID" ] || [ "$THREAD_ID" == "null" ]; then
    echo "❌ Could not retrieve a thread ID for testing"
else
    echo "Using thread ID: $THREAD_ID"
    curl -s -X POST -H "Content-Type: application/json" \
         -H "X-API-Key: 7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f" \
         -d "{\"tool_name\": \"damien_get_thread_details\", \"input\": {\"thread_id\": \"$THREAD_ID\"}, \"session_id\": \"test\"}" \
         http://localhost:8895/mcp/execute_tool | jq .
fi

echo ""
echo "===== TEST COMPLETE ====="
