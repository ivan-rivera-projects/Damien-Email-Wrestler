#!/bin/bash

# Damien Email Wrestler - Simple Test Script
set -e

echo "🧪 Damien Email Wrestler Test Suite"
echo "==================================="

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

if curl -s http://localhost:8892/health | grep -q "ok"; then
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
echo "Testing tool discovery..."

if curl -s http://localhost:8081/tools | grep -q "damien_list_emails"; then
    test_passed "Tool discovery works"
else
    test_failed "Tool discovery failed"
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
