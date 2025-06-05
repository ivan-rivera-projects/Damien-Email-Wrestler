#!/bin/bash

# Test script for all 8 AI Intelligence tools in the Damien platform
# Tests each tool with real functionality to ensure 100% operational status

API_KEY="7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
BASE_URL="http://localhost:8892"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Damien AI Intelligence Tools Test Suite${NC}"
echo "============================================================"

# Track results
TOTAL=0
PASSED=0

test_tool() {
    local tool_name=$1
    local params=$2
    local description=$3
    
    TOTAL=$((TOTAL + 1))
    
    echo -e "\n${YELLOW}============================================================${NC}"
    echo -e "${YELLOW}Testing: ${tool_name}${NC}"
    echo -e "${YELLOW}Description: ${description}${NC}"
    echo -e "${YELLOW}============================================================${NC}"
    
    echo "Parameters:"
    echo "$params" | jq .
    
    # Construct MCP request with proper structure
    session_id="test-session-$(date +%s)"
    mcp_request=$(jq -n --arg tool "$tool_name" --argjson params "$params" --arg session "$session_id" '{
        tool_name: $tool,
        input: $params,
        session_id: $session,
        user_id: "test_user"
    }')
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d "$mcp_request" \
        "$BASE_URL/mcp/execute_tool")
    
    # Extract status code and body
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ SUCCESS - Status Code: $http_code${NC}"
        echo "Response preview:"
        echo "$body" | jq . | head -20
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED - Status Code: $http_code${NC}"
        echo "Error:"
        echo "$body" | head -20
        return 1
    fi
}

# Test 1: Quick test for health check
echo -e "\n${BLUE}1️⃣ Testing Quick Test (Health Check)${NC}"
test_tool "damien_ai_quick_test" '{
    "sample_size": 10,
    "days": 7,
    "include_performance": true,
    "validate_components": true
}' "Quick validation of AI integration and performance"

# Test 2: Email analysis
echo -e "\n${BLUE}2️⃣ Testing Email Analysis${NC}"
test_tool "damien_ai_analyze_emails" '{
    "days": 7,
    "max_emails": 50,
    "min_confidence": 0.7,
    "output_format": "summary"
}' "Comprehensive AI analysis of Gmail emails"

# Test 3: Rule suggestions
echo -e "\n${BLUE}3️⃣ Testing Rule Suggestions${NC}"
test_tool "damien_ai_suggest_rules" '{
    "limit": 3,
    "min_confidence": 0.8,
    "include_business_impact": true,
    "auto_validate": true
}' "Generate intelligent email management rules"

# Test 4: Natural language rule creation
echo -e "\n${BLUE}4️⃣ Testing Natural Language Rule Creation${NC}"
test_tool "damien_ai_create_rule" '{
    "rule_description": "Archive all newsletters and marketing emails older than 7 days",
    "validate_before_create": true,
    "dry_run": true,
    "confidence_threshold": 0.8
}' "Create email rules using natural language"

# Test 5: Email insights
echo -e "\n${BLUE}5️⃣ Testing Email Insights${NC}"
test_tool "damien_ai_get_insights" '{
    "insight_type": "summary",
    "time_range": 30,
    "include_predictions": false,
    "format": "text"
}' "Get comprehensive email intelligence and insights"

# Test 6: Inbox optimization
echo -e "\n${BLUE}6️⃣ Testing Inbox Optimization${NC}"
test_tool "damien_ai_optimize_inbox" '{
    "optimization_type": "all",
    "aggressiveness": "moderate",
    "dry_run": true,
    "max_actions": 50
}' "AI-powered inbox optimization"

# Test 7: Large scale analysis
echo -e "\n${BLUE}7️⃣ Testing Large Scale Analysis${NC}"
test_tool "damien_ai_analyze_emails_large_scale" '{
    "target_count": 100,
    "days": 14,
    "min_confidence": 0.75,
    "use_statistical_validation": true
}' "Large-scale email analysis for 100+ emails"

# Test 8: Async analysis
echo -e "\n${BLUE}8️⃣ Testing Async Email Analysis${NC}"
test_tool "damien_ai_analyze_emails_async" '{
    "days": 7,
    "max_emails": 50
}' "Async email analysis job"

# Summary
echo -e "\n${YELLOW}============================================================${NC}"
echo -e "${YELLOW}📊 TEST SUMMARY${NC}"
echo -e "${YELLOW}============================================================${NC}"

echo -e "Total tests: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$((TOTAL - PASSED))${NC}"
echo -e "Success Rate: $((PASSED * 100 / TOTAL))%"

if [ $PASSED -eq $TOTAL ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! AI Intelligence at 100% 🎉${NC}"
    exit 0
else
    echo -e "\n${RED}❌ $((TOTAL - PASSED)) tests failed. Target: 100% operational status${NC}"
    exit 1
fi