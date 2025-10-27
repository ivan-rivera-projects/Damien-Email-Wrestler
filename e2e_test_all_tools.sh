#!/bin/bash
#
# Damien Email Wrestler - End-to-End Tool Smoke Test
#
# This script tests all available MCP tools to ensure they are functioning correctly.
# It requires the damien-mcp-minimal server to be running.
#

# --- Configuration ---
BASE_URL="http://localhost:8893"
API_KEY="2cce28d6432ac936fba9bdb124059c1b034a9858fe22ce4d3e367136b5b251c7"
REPORT_FILE="E2E_TEST_RESULTS.md"
SESSION_ID="e2e-test-$(date +%s)"

# --- Test Harness ---
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to execute a tool and check the result
# Usage: run_test "Test Name" "tool_name" '{"param1": "value1"}'
run_test() {
    local test_name="$1"
    local tool_name="$2"
    local params="$3"
    local expected_success=${4:-true}

    ((TOTAL_TESTS++))
    echo -n "🧪 Running test: $test_name..."

    # Construct the request payload
    local payload
    if [[ -z "$params" ]]; then
        payload=$(jq -n --arg name "$tool_name" '{name: $name, params: {}}')
    else
        payload=$(jq -n --arg name "$tool_name" --argjson p "$params" '{name: $name, params: $p}')
    fi

    # Make the API call
    response=$(curl -s -X POST "$BASE_URL/mcp/execute_tool" \
        -H "Content-Type: application/json" \
        -H "x-api-key: $API_KEY" \
        -d "$payload")

    # Check for curl error
    if [ $? -ne 0 ]; then
        echo "❌ FAILED (curl error)"
        ((FAILED_TESTS++))
        log_failure "$test_name" "$tool_name" "$params" "curl command failed"
        return
    fi

    # Check if the response is valid JSON and contains an is_error field
    is_error=$(echo "$response" | jq -r '.is_error' 2>/dev/null)
    if [ -z "$is_error" ]; then
         is_error=$(echo "$response" | jq -r 'has("error")')
    fi


    if [[ "$is_error" == "true" && "$expected_success" == "true" ]]; then
        echo "❌ FAILED"
        ((FAILED_TESTS++))
        log_failure "$test_name" "$tool_name" "$params" "$response"
    elif [[ "$is_error" == "false" && "$expected_success" == "false" ]]; then
        echo "❌ FAILED (Expected failure, but succeeded)"
        ((FAILED_TESTS++))
        log_failure "$test_name" "$tool_name" "$params" "$response"
    else
        echo "✅ PASSED"
        ((PASSED_TESTS++))
        log_success "$test_name" "$tool_name" "$params" "$response"
    fi
}

# --- Logging ---
log_header() {
    echo "# Damien E2E Test Report - $(date)" > "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "Running tests against: $BASE_URL" >> "$REPORT_FILE"
    echo "Session ID: $SESSION_ID" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

log_success() {
    local test_name="$1"
    local tool_name="$2"
    local params="$3"
    local response="$4"
    echo "## ✅ PASSED: $test_name" >> "$REPORT_FILE"
    echo "**Tool:** \`$tool_name\`" >> "$REPORT_FILE"
    echo "**Params:**" >> "$REPORT_FILE"
    echo "
```json
" >> "$REPORT_FILE"
    echo "$params" | jq . >> "$REPORT_FILE"
    echo "
```
" >> "$REPORT_FILE"
    echo "**Response (truncated):**" >> "$REPORT_FILE"
    echo "
```json
" >> "$REPORT_FILE"
    echo "$response" | jq . | head -n 20 >> "$REPORT_FILE"
    echo "
```
" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

log_failure() {
    local test_name="$1"
    local tool_name="$2"
    local params="$3"
    local response="$4"
    echo "## ❌ FAILED: $test_name" >> "$REPORT_FILE"
    echo "**Tool:** \`$tool_name\`" >> "$REPORT_FILE"
    echo "**Params:**" >> "$REPORT_FILE"
    echo "
```json
" >> "$REPORT_FILE"
    echo "$params" | jq . >> "$REPORT_FILE"
    echo "
```
" >> "$REPORT_FILE"
    echo "**Full Response:**" >> "$REPORT_FILE"
    echo "
```json
" >> "$REPORT_FILE"
    echo "$response" | jq . >> "$REPORT_FILE"
    echo "
```
" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

log_summary() {
    echo ""
    echo "--- Test Summary ---"
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "--------------------"
    echo ""
    echo "# Test Summary" >> "$REPORT_FILE"
    echo "- **Total Tests:** $TOTAL_TESTS" >> "$REPORT_FILE"
    echo "- **Passed:** $PASSED_TESTS" >> "$REPORT_FILE"
    echo "- **Failed:** $FAILED_TESTS" >> "$REPORT_FILE"
}

# --- Test Execution ---
main() {
    log_header

    echo "--- Starting Read-Only Tests ---"
    run_test "List tools" "tools/list" "{}"
    run_test "List emails (default)" "damien_list_emails" "{}"
    run_test "List emails (with params)" "damien_list_emails" '{"max_results": 3, "query": "is:starred"}'
    run_test "List drafts" "damien_list_drafts" "{}"
    run_test "List threads" "damien_list_threads" '{"max_results": 3}'
    run_test "List rules" "damien_list_rules" "{}"
    run_test "List labels" "damien_list_labels" "{}"
    run_test "Get settings" "damien_get_settings" "{}"
    run_test "AI Quick Test" "damien_ai_quick_test" "{}"
    run_test "Get AI Insights" "damien_ai_get_insights" "{}"

    # --- Tests that require existing data (need to get IDs first) ---
    echo ""
    echo "--- Starting Read-Only Detail Tests (requires data) ---"
    local first_email_id=$(curl -s -X POST "$BASE_URL/mcp/execute_tool" -H "Content-Type: application/json" -H "x-api-key: $API_KEY" -d '{"name": "damien_list_emails", "params": {"max_results": 1}}' | jq -r '.output.email_summaries[0].id')
    if [ -n "$first_email_id" ] && [ "$first_email_id" != "null" ]; then
        run_test "Get email details" "damien_get_email_details" "{\"message_id\": \"$first_email_id\"}"
    else
        echo "⚠️ SKIPPED: Get email details (no emails found)"
    fi

    local first_thread_id=$(curl -s -X POST "$BASE_URL/mcp/execute_tool" -H "Content-Type: application/json" -H "x-api-key: $API_KEY" -d '{"name": "damien_list_threads", "params": {"max_results": 1}}' | jq -r '.output.threads[0].id')
    if [ -n "$first_thread_id" ] && [ "$first_thread_id" != "null" ]; then
        run_test "Get thread details" "damien_get_thread_details" "{\"thread_id\": \"$first_thread_id\"}"
    else
        echo "⚠️ SKIPPED: Get thread details (no threads found)"
    fi

    # --- CRUD Tests (Create -> Read -> Update -> Delete) ---
    echo ""
    echo "--- Starting CRUD Tests ---"
    # Label CRUD
    local test_label_name="test-label-$(date +%s)"
    run_test "Create Label" "damien_create_label" "{\"name\": \"$test_label_name\"}"
    run_test "Delete Label" "damien_delete_label" "{\"name\": \"$test_label_name\"}"

    # Draft CRUD
    local draft_to="test@example.com"
    local draft_subject="E2E Test Draft"
    local draft_body="This is a test draft."
    local create_draft_response=$(curl -s -X POST "$BASE_URL/mcp/execute_tool" -H "Content-Type: application/json" -H "x-api-key: $API_KEY" -d "{\"name\": \"damien_create_draft\", \"params\": {\"to\": [\"$draft_to\"], \"subject\": \"$draft_subject\", \"body\": \"$draft_body\"}}")
    local draft_id=$(echo "$create_draft_response" | jq -r '.output.id')

    if [ -n "$draft_id" ] && [ "$draft_id" != "null" ]; then
        echo "✅ PASSED: Create Draft (manually)"
        ((PASSED_TESTS++)); ((TOTAL_TESTS++))
        log_success "Create Draft" "damien_create_draft" "{\"to\": [\"$draft_to\"], \"subject\": \"$draft_subject\", \"body\": \"$draft_body\"}" "$create_draft_response"
        run_test "Get Draft Details" "damien_get_draft_details" "{\"draft_id\": \"$draft_id\"}"
        run_test "Update Draft" "damien_update_draft" "{\"draft_id\": \"$draft_id\", \"subject\": \"E2E Test Draft [Updated]\"}"
        run_test "Delete Draft" "damien_delete_draft" "{\"draft_id\": \"$draft_id\"}"
    else
        echo "❌ FAILED: Create Draft (manually)"
        ((FAILED_TESTS++)); ((TOTAL_TESTS++))
        log_failure "Create Draft" "damien_create_draft" "{\"to\": [\"$draft_to\"], \"subject\": \"$draft_subject\", \"body\": \"$draft_body\"}" "$create_draft_response"
        echo "⚠️ SKIPPED: Draft Details, Update, Delete tests"
    fi

    # --- AI and Async Tests ---
    echo ""
    echo "--- Starting AI & Async Tests ---"
    run_test "AI Analyze Emails" "damien_ai_analyze_emails" '{"days": 1, "max_emails": 10}'
    
    local async_job_response=$(curl -s -X POST "$BASE_URL/mcp/execute_tool" -H "Content-Type: application/json" -H "x-api-key: $API_KEY" -d '{"name": "damien_ai_analyze_emails_async", "params": {"days": 1, "target_count": 10}}')
    local job_id=$(echo "$async_job_response" | jq -r '.output.job_id')
    if [ -n "$job_id" ] && [ "$job_id" != "null" ]; then
        echo "✅ PASSED: Start Async Analysis Job (manually)"
        ((PASSED_TESTS++)); ((TOTAL_TESTS++))
        log_success "Start Async Analysis Job" "damien_ai_analyze_emails_async" '{"days": 1, "target_count": 10}' "$async_job_response"
        
        # Wait a moment for the job to start
        sleep 5

        run_test "Job Get Status" "damien_job_get_status" "{\"job_id\": \"$job_id\"}"
        run_test "Job List" "damien_job_list" "{}"
        # We don't wait for the result as it can take time, but we can try to cancel it
        run_test "Job Cancel" "damien_job_cancel" "{\"job_id\": \"$job_id\"}"
    else
        echo "❌ FAILED: Start Async Analysis Job (manually)"
        ((FAILED_TESTS++)); ((TOTAL_TESTS++))
        log_failure "Start Async Analysis Job" "damien_ai_analyze_emails_async" '{"days": 1, "target_count": 10}' "$async_job_response"
        echo "⚠️ SKIPPED: Job status, list, and cancel tests"
    fi

    log_summary
}

main
