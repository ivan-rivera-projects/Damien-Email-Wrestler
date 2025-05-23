# Damien Email Wrestler: Comprehensive Testing Plan

This document outlines the testing strategy and specific test cases for validating the enhancements made to the Damien Email Wrestler application as detailed in the "Damien Email Wrestler: Optimization and Enhancement Plan" and the "Damien Enhancement Checklist".

## Legend
- [ ] To Do
- [ ] In Progress
- [ ] Passed
- [ ] Failed
- [ ] Skipped

## I. General Testing Prerequisites

1.  **Environment Setup:**
    *   [ ] All three services (`damien-cli` configured, `damien-mcp-server`, `damien-smithery-adapter`) can be started successfully.
    *   [ ] `.env` files for `damien-mcp-server` and `damien-smithery-adapter` are correctly configured with necessary API keys, URLs, and log paths (if file logging is enabled for them).
    *   [ ] `damien-cli` has valid `credentials.json` and has been authenticated (resulting in `token.json`).
    *   [ ] (For E2E Gmail tests) A dedicated test Gmail account is prepared with a variety of emails (unread, read, with/without attachments, specific labels, varying dates, specific senders/subjects).
2.  **Tools:**
    *   [ ] `curl` or a similar HTTP client (like Postman or Insomnia) for API endpoint testing.
    *   [ ] `pytest` for running Python unit tests in `damien-cli` and `damien-mcp-server`.
    *   [ ] `npm test` (or equivalent Jest/Mocha runner) for unit/integration tests in `damien-smithery-adapter` (if such tests are written in JS/TS).
    *   [ ] Access to view console logs and log files for all three components.
3.  **API Keys & Tokens:**
    *   `DAMIEN_MCP_SERVER_API_KEY`: Known and used for testing protected MCP server endpoints.
    *   `SMITHERY_BEARER_AUTH`: Known (if testing Smithery registration, though not a focus of these functional tests).

## II. Phase 1 Testing: Core Data Retrieval Optimization

**Objective:** Verify granular header fetching for `damien_list_emails` and `damien_get_email_details`, and optimized Gmail API calls.

### A. `damien-cli` (`core_api/gmail_api_service.py`) - Unit Tests (Conceptual)

*   **`_batch_get_messages_metadata` function:**
    *   [ ] Test correct batch request construction for various message IDs and `headers_to_include`.
        *   *Verification:* Mock `service.new_batch_http_request()` and `batch_request.add()`. Assert arguments passed.
    *   [ ] Test parsing of successful batch responses (mock `batch_request.execute()` and callback behavior).
        *   *Verification:* Ensure returned list of dicts contains correct IDs, threadIds, and extracted header values.
    *   [ ] Test handling of errors for individual items within a batch (mock callback `exception` parameter).
        *   *Verification:* Ensure errored items in the result list have an `error` field.
    *   [ ] Test handling of overall batch execution failure (mock `batch_request.execute()` to raise `HttpError`).
        *   *Verification:* Ensure all items in that batch attempt are marked with an error.
    *   [ ] Test edge cases: empty `message_ids`, empty `headers_to_include` (though the latter should be prevented by caller).
*   **`list_messages` function:**
    *   [ ] Test with `include_headers=None`: Verify it calls Gmail's `list()` and returns basic stubs (ID, threadId).
    *   [ ] Test with `include_headers=["From", "Subject"]`:
        *   *Verification:* Mock `service.users().messages().list().execute()` to return IDs. Mock `_batch_get_messages_metadata` to verify it's called with correct IDs and headers, and its (mocked) rich output is returned.
    *   [ ] Test pagination (`page_token`) in conjunction with `include_headers`.
*   **`get_message_details` function:**
    *   [ ] Test with `include_headers=["From", "Date"]`:
        *   *Verification:* Mock `service.users().messages().get().execute()`. Assert it was called with `format="METADATA"` and `metadataHeaders="From,Date"`.
    *   [ ] Test with `include_headers=None` and various `email_format` options: Verify correct `format` passed to Gmail API.

### B. `damien-mcp-server` - Integration Tests

Assume `damien-mcp-server` is running. Use `curl` with the `DAMIEN_MCP_SERVER_API_KEY`.
Replace `YOUR_MCP_API_KEY` and `http://localhost:8892` as needed.

*   **`/mcp/list_tools` Endpoint:**
    *   [ ] **Test:** `curl -H "X-API-Key: YOUR_MCP_API_KEY" http://localhost:8892/mcp/list_tools`
    *   **Verification:**
        *   Inspect the JSON output.
        *   For `damien_list_emails` tool:
            *   Ensure `input_schema.properties` contains `include_headers`.
            *   Verify `include_headers.type` is `array` and `items.type` is `string`.
            *   Verify `include_headers.description` is rich and informative (mentions efficiency, common headers).
        *   For `damien_get_email_details` tool:
            *   Ensure `input_schema.properties` contains `include_headers`.
            *   Verify its type and rich description.
            *   Verify `format.default` is `"metadata"`.
*   **`/mcp/execute_tool` for `damien_list_emails`:**
    *   [ ] **Test (Specific Headers):**
        ```bash
        curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_MCP_API_KEY" \
        -d '{
          "tool_name": "damien_list_emails",
          "input": {
            "query": "is:unread",
            "max_results": 2,
            "include_headers": ["From", "Subject"]
          },
          "session_id": "test_session_list_emails_headers"
        }' http://localhost:8892/mcp/execute_tool
        ```
    *   **Verification:** Response `output.email_summaries` should contain items with `id`, `threadId`, `From`, `Subject` (and `additional_headers` if other headers were returned by CLI). Other headers should be absent. (Requires actual emails or sophisticated CLI mock).
    *   [ ] **Test (No Headers):**
        ```bash
        curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_MCP_API_KEY" \
        -d '{
          "tool_name": "damien_list_emails",
          "input": {
            "query": "is:inbox",
            "max_results": 1
          },
          "session_id": "test_session_list_emails_no_headers"
        }' http://localhost:8892/mcp/execute_tool
        ```
    *   **Verification:** Response `output.email_summaries` items should primarily have `id`, `thread_id`, and `snippet` (or whatever minimal set the CLI returns by default now).
*   **`/mcp/execute_tool` for `damien_get_email_details`:**
    *   [ ] **Test (Specific Headers):** (Requires a valid `MESSAGE_ID_TO_TEST`)
        ```bash
        curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_MCP_API_KEY" \
        -d '{
          "tool_name": "damien_get_email_details",
          "input": {
            "message_id": "MESSAGE_ID_TO_TEST",
            "include_headers": ["Message-ID", "Date"]
          },
          "session_id": "test_session_get_details_headers"
        }' http://localhost:8892/mcp/execute_tool
        ```
    *   **Verification:** Response `output` should contain the message details, but the `payload.headers` (or equivalent structure from CLI) should ideally only contain "Message-ID" and "Date".
    *   [ ] **Test (Default Format - Metadata):**
        ```bash
        curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_MCP_API_KEY" \
        -d '{
          "tool_name": "damien_get_email_details",
          "input": {
            "message_id": "MESSAGE_ID_TO_TEST"
          },
          "session_id": "test_session_get_details_default"
        }' http://localhost:8892/mcp/execute_tool
        ```
    *   **Verification:** Response `output` should contain metadata (all headers, snippet).

### C. `damien-smithery-adapter` - Integration Tests

Assume `damien-smithery-adapter` is running and configured to point to the `damien-mcp-server`.
Replace `http://localhost:8081` as needed.

*   **`/tools` Endpoint:**
    *   [ ] **Test:** `curl http://localhost:8081/tools`
    *   **Verification:** Similar to MCP server's `/mcp/list_tools`, check for `damien_list_emails` and `damien_get_email_details` and ensure their `inputSchema` correctly reflects `include_headers` with rich descriptions. (This tests if the adapter correctly fetches and proxies/transforms the schema).
*   **`/execute` Endpoint (forwarding `damien_list_emails`):**
    *   [ ] **Test (Specific Headers):**
        ```bash
        curl -X POST -H "Content-Type: application/json" \
        -d '{
          "tool": "damien_list_emails",
          "input": {
            "query": "is:unread",
            "max_results": 2,
            "include_headers": ["From", "Subject"]
          },
          "session_id": "test_smithery_list_emails_headers"
        }' http://localhost:8081/execute
        ```
    *   **Verification:** The response should match the expected output from the MCP server for this call (i.e., summaries with only "From" and "Subject").

### D. End-to-End (E2E) Tests (Conceptual)

*   [ ] **Scenario 1 (List with Specific Headers):**
    *   **Action:** Simulate AI request: "List the last 2 unread emails and show me their sender and subject."
    *   **Expected Tool Calls (verified via logs/mocks if not using real Gmail):**
        1.  Smithery Adapter receives call for `damien_list_emails` with `input: {"query": "is:unread", "max_results": 2, "include_headers": ["From", "Subject"]}`.
        2.  MCP Server receives this and calls `DamienAdapter.list_emails_tool`.
        3.  `damien-cli`'s `gmail_api_service.list_messages` is called.
            *   Makes one `users.messages.list` call to Gmail.
            *   Makes one batched `users.messages.get` call with `format=METADATA` and `metadataHeaders=From,Subject`.
    *   **Verification:** Final output to AI contains only From and Subject (plus ID, threadId).
*   [ ] **Scenario 2 (Get Details with Specific Headers):**
    *   **Action:** AI request: "Get the Message-ID and Date for email X."
    *   **Expected Tool Calls:** `damien_get_email_details` with `input: {"message_id": "X", "include_headers": ["Message-ID", "Date"]}`.
    *   **Verification:** Gmail API called with `format=METADATA` and `metadataHeaders=Message-ID,Date`. Output contains only these.
*   [ ] **Scenario 3 (Edge Cases for `include_headers`):**
    *   Empty `include_headers` list.
    *   Invalid header names in `include_headers`.
    *   Requesting a header that doesn't exist on some emails.
    *   *Verification:* Graceful handling, appropriate (minimal) data returned or clear error messages.

## III. Phase 2 Testing: Rule Engine & Broader Tool Optimization

**Objective:** Verify enhanced rule translation, `apply_rules` summary options, and `list_rules`/`get_rule_details` functionality.

### A. `damien-cli` - Unit Tests (Conceptual)

*   **`translate_rule_to_gmail_query` function:**
    *   [ ] Test conditions with `field: "date_age"`, `operator: "older_than"`, `value: "7d"`. Expected: `"older_than:7d"`.
    *   [ ] Test `field: "date_age"`, `operator: "newer_than"`, `value: "2m"`. Expected: `"newer_than:2m"`.
    *   [ ] Test invalid `date_age` values (e.g., "7days", "foo"). Expected: `None` or warning, no query part.
    *   [ ] Test `field: "has_attachment"`, `operator: "is"`, `value: "true"`. Expected: `"has:attachment"`.
    *   [ ] Test `field: "has_attachment"`, `operator: "is"`, `value: "false"`. Expected: `"-has:attachment"`.
    *   [ ] Test `field: "attachment_filename"`, `operator: "contains"`, `value: "report.pdf"`. Expected: `"filename:report.pdf"`.
    *   [ ] Test `field: "attachment_filename"`, `operator: "equals"`, `value: "exact name.docx"`. Expected: `'filename:("exact name.docx")'`.
    *   [ ] Test `field: "message_size"`, `operator: "greater_than"`, `value: "5M"`. Expected: `"larger:5M"`.
    *   [ ] Test `field: "message_size"`, `operator: "less_than"`, `value: "500K"`. Expected: `"smaller:500K"`.
    *   [ ] Test invalid `message_size` values. Expected: `None` or warning.
*   **`apply_rules_to_mailbox` function:**
    *   [ ] Test with `include_detailed_ids=True`: Mock actions. Verify `summary["actions_planned_or_taken"]` contains lists of (mocked) email IDs.
    *   [ ] Test with `include_detailed_ids=False`: Mock actions. Verify `summary["actions_planned_or_taken"]` contains counts.
    *   [ ] Test `dry_run=True` with both `include_detailed_ids` options, verify output structure.
*   **`_email_field_matches_condition` (if new field/operator logic was added there):**
    *   [ ] Test new `ConditionModel` fields/operators if their matching logic is client-side. (Note: most new ones are for server-side translation).

### B. `damien-mcp-server` - Integration Tests

*   **`/mcp/list_tools` Endpoint:**
    *   [ ] **Test:** `curl -H "X-API-Key: YOUR_MCP_API_KEY" http://localhost:8892/mcp/list_tools`
    *   **Verification:**
        *   For `damien_apply_rules`: Check `input_schema` for `include_detailed_ids` (boolean, default false, description). Check `output_schema` for `include_detailed_ids_in_summary` and updated `actions_planned_or_taken` description.
        *   For `damien_list_rules`: Check `input_schema` for `summary_view` (boolean, default true, description). Check `output_schema` for `rules` (List[Any] with description) and `summary_view_active`.
        *   For `damien_get_rule_details`: Check `input_schema` for `rule_id_or_name` (string, required). Check `output_schema` matches `RuleModelOutput`.
*   **`/mcp/execute_tool` for `damien_apply_rules`:**
    *   [ ] Test with `include_detailed_ids: true` and `false`. Verify structure of `output.actions_planned_or_taken`.
*   **`/mcp/execute_tool` for `damien_list_rules`:**
    *   [ ] Test with `summary_view: true`. Verify `output.rules` contains summaries and `output.summary_view_active` is true.
    *   [ ] Test with `summary_view: false`. Verify `output.rules` contains full definitions and `output.summary_view_active` is false.
*   **`/mcp/execute_tool` for `damien_get_rule_details`:**
    *   [ ] Test with a valid rule ID/name. Verify full rule definition is returned.
    *   [ ] Test with an invalid/non-existent rule ID/name. Verify `is_error: true` and appropriate error message.

### C. End-to-End (E2E) Tests (Conceptual)

*   [ ] **Scenario (Rule with new conditions):** Create a rule in `rules.json` using `date_age` (e.g., `older_than:1d`). Apply rules. Verify (via logs/mocks) that `translate_rule_to_gmail_query` generated the correct Gmail query part.
*   [ ] **Scenario (`apply_rules` output):** Call `damien_apply_rules` (via Smithery adapter) with `include_detailed_ids=true` and then `false`. Verify the structure of the `actions_planned_or_taken` field in the output.
*   [ ] **Scenario (`list_rules` output):** Call `damien_list_rules` with `summary_view=true` and then `false`. Verify output structure.
*   [ ] **Scenario (`get_rule_details`):** Call `damien_get_rule_details` for an existing rule and a non-existent one. Verify outputs.

## IV. Phase 3 Testing: Logging Standardization

**Objective:** Verify consistent, structured JSON logging across all components and correct file path handling.

### A. `damien-cli`

*   [ ] **Unit Test `CustomJsonFormatter`:** Verify JSON structure, presence of all custom fields (`timestamp`, `level`, `name`, `service_name`, `module`, `function`, `line_number`, `message`).
*   [ ] **Manual Check:**
    *   Run CLI commands (e.g., `damien login`, apply a simple rule).
    *   Inspect console output: Is it JSON? Does it contain the structured fields?
    *   Inspect `data/damien_session.log`: Is it JSON? Correct fields?
    *   Verify `DATA_DIR` in `core/config.py` is correctly defined and created.
    *   Verify log levels are respected.

### B. `damien-mcp-server`

*   [ ] **Unit Test `CustomJsonFormatter`:** Verify JSON structure, `service_name` is "damien-mcp-server".
*   [ ] **Manual Check:**
    *   Start server. Make API calls (e.g., `/health`, `/mcp/execute_tool`).
    *   Inspect console output: Are logs from `damien_mcp_server_app` logger in JSON format with correct fields?
    *   If `log_file_path` is configured in `settings`:
        *   Verify directory for log file is created if it doesn't exist.
        *   Verify log file is written to with JSON logs.
        *   Test with invalid/unwritable `log_file_path` (expect console error, graceful failure of file logging).
    *   Verify log levels from `settings.log_level` are respected.

### C. `damien-smithery-adapter`

*   [ ] **Unit Test (Conceptual for `logger.ts`):** Verify `pino` options (level, base fields, timestamp, messageKey).
*   [ ] **Manual Check:**
    *   Start server. Make API calls (e.g., `/health`, `/tools`, `/execute`).
    *   Inspect console output: Is it JSON (or pino-pretty if piped)? Correct fields?
    *   If `ADAPTER_LOG_FILE_PATH` is configured in `.env`/`config.ts`:
        *   Verify directory for log file is created.
        *   Verify log file is written to with JSON logs.
    *   Verify log levels from `CONFIG.LOG_LEVEL` are respected.

---

This testing plan provides a comprehensive checklist. Actual test scripts and detailed assertions would be developed based on these outlines.