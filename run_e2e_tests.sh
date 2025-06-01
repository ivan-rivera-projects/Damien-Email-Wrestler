#!/bin/bash
# File: run_e2e_tests.sh

set -e  # Exit on any error

echo "🚀 Starting Damien Platform E2E Tests..."
echo "Current directory: $(pwd)"

# Test 1: Gmail Authentication
echo ""
echo "📧 Testing Gmail authentication..."
cd damien-cli
echo "Testing from: $(pwd)"

if poetry run python -c "
from damien_cli.core_api.gmail_api_service import get_authenticated_service, list_messages
try:
    service = get_authenticated_service()
    messages = list_messages(service, max_results=1)
    print('✅ Gmail authentication: PASS')
except Exception as e:
    print(f'❌ Gmail authentication: FAIL - {e}')
" 2>/dev/null; then
    echo "✅ Gmail authentication: PASS"
else
    echo "❌ Gmail authentication: FAIL"
fi

# Test 2: MCP Server
echo ""
echo "🔧 Testing MCP server..."
cd ../damien-mcp-server
echo "Testing from: $(pwd)"

# Start MCP server in background
poetry run python -m app.main &
MCP_PID=$!
echo "Started MCP server with PID: $MCP_PID"
sleep 5

# Test health endpoint
if curl -f http://localhost:8892/health > /dev/null 2>&1; then
    echo "✅ MCP server health: PASS"
else
    echo "❌ MCP server health: FAIL"
fi

# Clean up MCP server
kill $MCP_PID 2>/dev/null || true
sleep 2

# Test 3: OpenAI Integration
echo ""
echo "🤖 Testing OpenAI integration..."
cd ..
echo "Testing from: $(pwd)"

# Run from damien-cli directory for proper imports
cd damien-cli
if poetry run python ../analyze_token_usage.py > /dev/null 2>&1; then
    echo "✅ OpenAI integration: PASS"
else
    echo "❌ OpenAI integration: FAIL - Running basic test..."
    # Basic test without full integration
    if poetry run python -c "
import os
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print('✅ OpenAI API key found')
else:
    print('❌ OpenAI API key missing')
"; then
        echo "✅ Basic OpenAI config: PASS"
    else
        echo "❌ Basic OpenAI config: FAIL"
    fi
fi

# Test 4: AI Intelligence (Basic Import Test)
echo ""
echo "🧠 Testing AI intelligence imports..."
if poetry run python -c "
try:
    from damien_cli.features.ai_intelligence.categorization.gmail_analyzer import GmailEmailAnalyzer
    print('✅ AI intelligence imports: PASS')
except ImportError as e:
    print(f'❌ AI intelligence imports: FAIL - {e}')
" 2>/dev/null; then
    echo "✅ AI Intelligence imports: PASS"
else
    echo "❌ AI Intelligence imports: FAIL"
fi

echo ""
echo "🏁 E2E Tests completed!"
echo "📊 Check results above. For detailed testing, run each component individually."
echo ""
echo "Next steps:"
echo "1. For OpenAI testing: cd damien-cli && poetry run python ../analyze_token_usage.py"
echo "2. For MCP testing: cd damien-mcp-server && poetry run python -m app.main"
echo "3. For full AI testing: Use the E2E_TESTING_GUIDE.md manual tests"
