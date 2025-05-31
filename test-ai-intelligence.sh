#!/bin/bash

# Test Script for All 6 AI Email Intelligence Tools
# ==================================================
# Tests the complete Phase 4 AI intelligence capabilities of Damien Email Wrestler

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
API_KEY=""
MCP_URL="http://localhost:8892"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$SCRIPT_DIR/logs/ai-intelligence-test-$TIMESTAMP.log"

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}" | tee -a "$LOG_FILE"
}

print_header() {
    echo "" | tee -a "$LOG_FILE"
    print_status "$CYAN" "=================================================================="
    print_status "$CYAN" "$1"
    print_status "$CYAN" "=================================================================="
}

print_subheader() {
    echo "" | tee -a "$LOG_FILE"
    print_status "$BLUE" "🔹 $1"
    print_status "$BLUE" "$(printf '%.0s-' {1..50})"
}

print_success() {
    print_status "$GREEN" "✅ $1"
}

print_error() {
    print_status "$RED" "❌ $1"
}

print_warning() {
    print_status "$YELLOW" "⚠️  $1"
}

print_info() {
    print_status "$BLUE" "ℹ️  $1"
}

# Function to load API key
load_api_key() {
    if [[ -f "$ENV_FILE" ]]; then
        API_KEY=$(grep "DAMIEN_MCP_SERVER_API_KEY" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ -z "$API_KEY" ]]; then
            print_error "API key not found in $ENV_FILE"
            exit 1
        fi
        print_success "API key loaded from $ENV_FILE"
    else
        print_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
}

# Function to check server health
check_server_health() {
    print_subheader "Checking MCP Server Health"
    
    local health_response
    health_response=$(curl -s --max-time 10 "$MCP_URL/health" || echo "CURL_FAILED")
    
    if [[ "$health_response" == "CURL_FAILED" ]]; then
        print_error "MCP Server is not responding at $MCP_URL"
        print_info "Please run: ./scripts/start-all.sh"
        exit 1
    fi
    
    local status
    status=$(echo "$health_response" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
    
    if [[ "$status" == "ok" ]]; then
        print_success "MCP Server is healthy"
        echo "$health_response" | jq '.' >> "$LOG_FILE" 2>/dev/null || echo "$health_response" >> "$LOG_FILE"
    else
        print_error "MCP Server health check failed"
        echo "$health_response" >> "$LOG_FILE"
        exit 1
    fi
}

# Function to make API call with error handling
make_api_call() {
    local tool_name=$1
    local params=$2
    local description=$3
    
    print_info "Testing: $description"
    print_info "Tool: $tool_name"
    print_info "Parameters: $params"
    
    # Generate a unique session ID for this test
    local session_id="test_session_$(date +%s)_$$"
    
    # Use the correct MCP request format
    local request_body="{
        \"tool_name\": \"$tool_name\",
        \"input\": $params,
        \"session_id\": \"$session_id\"
    }"
    
    local response
    response=$(curl -s --max-time 30 \
        -X POST "$MCP_URL/mcp/execute_tool" \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d "$request_body" \
        2>/dev/null || echo "CURL_FAILED")
    
    if [[ "$response" == "CURL_FAILED" ]]; then
        print_error "API call failed for $tool_name"
        return 1
    fi
    
    echo "Request for $tool_name:" >> "$LOG_FILE"
    echo "$request_body" | jq '.' >> "$LOG_FILE" 2>/dev/null || echo "$request_body" >> "$LOG_FILE"
    echo "Response for $tool_name:" >> "$LOG_FILE"
    echo "$response" | jq '.' >> "$LOG_FILE" 2>/dev/null || echo "$response" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    # Check if response indicates success
    local success
    success=$(echo "$response" | jq -r '.success // false' 2>/dev/null || echo "false")
    
    if [[ "$success" == "true" ]]; then
        print_success "$description - SUCCESS"
        
        # Extract and display key information
        local key_info
        key_info=$(echo "$response" | jq -r '.data // {}' 2>/dev/null)
        if [[ "$key_info" != "{}" ]] && [[ "$key_info" != "null" ]]; then
            echo "$key_info" | jq '.' 2>/dev/null | head -10 || echo "$key_info" | head -10
        fi
        return 0
    else
        local error_msg
        error_msg=$(echo "$response" | jq -r '.error_message // .detail // "Unknown error"' 2>/dev/null || echo "Unknown error")
        print_error "$description - FAILED: $error_msg"
        return 1
    fi
}

# Test functions for each AI tool

test_ai_quick_test() {
    print_subheader "1. AI Quick Test - System Health Validation"
    
    local params='{
        "sample_size": 25,
        "days": 7,
        "include_performance": true,
        "validate_components": true
    }'
    
    make_api_call "damien_ai_quick_test" "$params" "AI system health and performance validation"
}

test_ai_analyze_emails() {
    print_subheader "2. AI Analyze Emails - Pattern Detection & Insights"
    
    local params='{
        "days": 14,
        "max_emails": 100,
        "min_confidence": 0.7,
        "output_format": "summary"
    }'
    
    make_api_call "damien_ai_analyze_emails" "$params" "Email pattern analysis and business insights"
}

test_ai_get_insights() {
    print_subheader "3. AI Get Insights - Email Intelligence & Trends"
    
    local params='{
        "time_range": 30,
        "insight_type": "summary",
        "format": "text",
        "include_predictions": false
    }'
    
    make_api_call "damien_ai_get_insights" "$params" "Comprehensive email intelligence and trends"
}

test_ai_suggest_rules() {
    print_subheader "4. AI Suggest Rules - Intelligent Rule Generation"
    
    local params='{
        "limit": 5,
        "min_confidence": 0.8,
        "include_business_impact": true,
        "auto_validate": true
    }'
    
    make_api_call "damien_ai_suggest_rules" "$params" "ML-powered email rule suggestions"
}

test_ai_create_rule() {
    print_subheader "5. AI Create Rule - Natural Language Rule Creation"
    
    local params='{
        "rule_description": "Automatically archive marketing emails from retail companies that I have not opened in the last 30 days",
        "dry_run": true,
        "confidence_threshold": 0.8,
        "validate_before_create": true
    }'
    
    make_api_call "damien_ai_create_rule" "$params" "Natural language email rule creation"
}

test_ai_optimize_inbox() {
    print_subheader "6. AI Optimize Inbox - Intelligent Inbox Management"
    
    local params='{
        "optimization_type": "all",
        "aggressiveness": "moderate",
        "dry_run": true,
        "max_actions": 50
    }'
    
    make_api_call "damien_ai_optimize_inbox" "$params" "AI-powered inbox optimization"
}

# Main execution
main() {
    print_header "🚀 DAMIEN AI EMAIL INTELLIGENCE TEST SUITE"
    print_info "Timestamp: $(date)"
    print_info "Log file: $LOG_FILE"
    
    # Setup
    load_api_key
    check_server_health
    
    # Test counters
    local total_tests=6
    local passed_tests=0
    local failed_tests=0
    
    print_header "🧪 TESTING ALL 6 AI INTELLIGENCE TOOLS"
    
    # Execute all tests
    if test_ai_quick_test; then ((passed_tests++)); else ((failed_tests++)); fi
    if test_ai_analyze_emails; then ((passed_tests++)); else ((failed_tests++)); fi
    if test_ai_get_insights; then ((passed_tests++)); else ((failed_tests++)); fi
    if test_ai_suggest_rules; then ((passed_tests++)); else ((failed_tests++)); fi
    if test_ai_create_rule; then ((passed_tests++)); else ((failed_tests++)); fi
    if test_ai_optimize_inbox; then ((passed_tests++)); else ((failed_tests++)); fi
    
    # Results summary
    print_header "📊 TEST RESULTS SUMMARY"
    
    print_info "Total Tests: $total_tests"
    print_success "Passed: $passed_tests"
    
    if [[ $failed_tests -gt 0 ]]; then
        print_error "Failed: $failed_tests"
    else
        print_success "Failed: $failed_tests"
    fi
    
    local success_rate=$((passed_tests * 100 / total_tests))
    print_info "Success Rate: $success_rate%"
    
    echo "" | tee -a "$LOG_FILE"
    if [[ $failed_tests -eq 0 ]]; then
        print_success "🎉 ALL AI INTELLIGENCE TOOLS ARE WORKING PERFECTLY!"
        print_info "Your Phase 4 AI capabilities are fully operational."
    elif [[ $passed_tests -gt 0 ]]; then
        print_warning "⚠️  PARTIAL SUCCESS - Some AI tools are working"
        print_info "Check the log file for details: $LOG_FILE"
    else
        print_error "❌ ALL TESTS FAILED - AI Intelligence system needs attention"
        print_info "Check MCP server logs and configuration"
    fi
    
    print_header "🔍 ADDITIONAL DIAGNOSTICS"
    
    # Tool availability check
    print_info "Checking AI tool availability..."
    local tools_response
    tools_response=$(curl -s -H "X-API-Key: $API_KEY" "$MCP_URL/mcp/list_tools" 2>/dev/null || echo "[]")
    local ai_tool_count
    ai_tool_count=$(echo "$tools_response" | jq '[.[] | select(.name | startswith("damien_ai_"))] | length' 2>/dev/null || echo "0")
    
    if [[ "$ai_tool_count" == "6" ]]; then
        print_success "All 6 AI tools are registered and available"
    else
        print_warning "Expected 6 AI tools, found: $ai_tool_count"
    fi
    
    print_info "Detailed logs saved to: $LOG_FILE"
    print_info "Test completed at: $(date)"
    
    # Exit with appropriate code
    if [[ $failed_tests -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Handle script interruption
trap 'print_error "Test interrupted by user"; exit 130' INT TERM

# Run main function
main "$@"
