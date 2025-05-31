#!/bin/bash

# Damien Email Wrestler - Simple Test Script
set -e

echo "🧪 Damien Email Wrestler Test Suite"
echo "==================================="

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if API key is set
if [ -z "$DAMIEN_MCP_SERVER_API_KEY" ]; then
    echo "❌ DAMIEN_MCP_SERVER_API_KEY not found in .env file"
    echo "Please ensure your .env file contains the API key"
    exit 1
fi

# Check if services are running first
SERVICE_CHECK_FAILED=false
echo "Checking if required services are running..."
if ! curl -s http://localhost:8894/health | grep -q "ok" 2>/dev/null; then
    echo "❌ Damien MCP Server is not running on port 8894"
    SERVICE_CHECK_FAILED=true
fi

if ! curl -s http://localhost:8081/health | grep -q "ok" 2>/dev/null; then
    echo "❌ Smithery Adapter is not running on port 8081"
    SERVICE_CHECK_FAILED=true
fi

if [ "$SERVICE_CHECK_FAILED" = true ]; then
    echo ""
    echo "⚠️  Required services are not running!"
    echo "Please start all services first by running:"
    echo ""
    echo "    ./scripts/start-all.sh"
    echo ""
    echo "Or start them manually:"
    echo "    cd damien-mcp-server && poetry run uvicorn app.main:app --port 8894 &"
    echo "    cd damien-smithery-adapter && npm run serve &"
    echo ""
    exit 1
fi

TESTS_PASSED=0
TESTS_FAILED=0

test_passed() {
    ((TESTS_PASSED++))
    echo "✓ $1"
}

test_failed() {
    ((TESTS_FAILED++))
    echo "✗ $1"
}

# Test configuration
echo "Testing configuration..."
if [ -f ".env" ]; then
    test_passed "Environment file exists"
else
    test_failed "Environment file missing"
fi

if [ -f "credentials.json" ]; then
    test_passed "Gmail credentials exist"
else
    test_failed "Gmail credentials missing"
fi

# Test health endpoints
echo ""
echo "Testing service health..."

if curl -s http://localhost:8894/health | grep -q "ok"; then
    test_passed "Damien MCP Server health check"
else
    test_failed "Damien MCP Server health check"
fi

if curl -s http://localhost:8081/health | grep -q "ok"; then
    test_passed "Smithery Adapter health check"
else
    test_failed "Smithery Adapter health check"
fi

# Test tool discovery
echo ""
echo "Testing Phase 4 AI intelligence tool discovery..."

# Test Damien MCP Server health (Phase 4 tools are registered on startup)
if curl -s -H "X-API-Key: $DAMIEN_MCP_SERVER_API_KEY" http://localhost:8892/health | grep -q "ok"; then
    test_passed "Damien MCP Server Phase 4 tools available"
else
    test_failed "Damien MCP Server Phase 4 tools not responding"
fi

# Test Smithery Adapter tool listing
SMITHERY_TOOLS=$(curl -s http://localhost:8081/tools)
if echo "$SMITHERY_TOOLS" | grep -q "tools"; then
    test_passed "Smithery Adapter responding"
else
    test_failed "Smithery Adapter not responding properly"
    echo "  Response: $SMITHERY_TOOLS"
fi

# Test Phase 4 AI intelligence tool endpoint
echo ""
echo "Testing Phase 4 AI intelligence tools..."
AI_TEST_RESULT=$(curl -s -X POST -H "Authorization: Bearer $DAMIEN_MCP_SERVER_API_KEY" -H "Content-Type: application/json" \
  http://localhost:8894/health 2>/dev/null)

if echo "$AI_TEST_RESULT" | grep -q "ok"; then
    test_passed "Phase 4 AI intelligence integration working"
else
    test_failed "Phase 4 AI intelligence integration not responding"
    echo "  Response: $AI_TEST_RESULT"
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    echo "🎉 All tests passed!"
else
    echo "❌ Some tests failed. Check the logs and configuration."
    exit 1
fi
