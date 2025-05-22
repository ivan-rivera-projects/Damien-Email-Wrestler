# Claude Integration Guide for Damien MCP Server

This guide outlines the steps to integrate Claude with the Damien MCP Server to create an AI-powered email management system.

## What We've Accomplished

1. **Fixed Configuration Issues**:
   - Properly configured nested Pydantic settings models
   - Fixed environment variable handling in tests
   - Ensured all 57 tests are passing

2. **Documentation Updates**:
   - Updated README.md with current project status
   - Updated ROADMAP.md with revised next steps
   - Created MCP_SERVER_ARCHITECTURE.md describing the server design
   - Created CLAUDE_INTEGRATION_CHECKLIST.md for tracking integration tasks

3. **Schema Generation**:
   - Created a script to generate formal JSON schemas for all ten Damien tools
   - Generated individual and combined schema files
   - Added documentation for using the schemas with Claude

4. **Deployment Preparation**:
   - Created guide for using ngrok to expose the MCP server
   - Outlined testing processes for verifying the Claude integration

## Next Steps

Following our integration checklist, the next steps are:

1. **Server Deployment**:
   - Configure the server's environment variables
   - Run the server with `poetry run uvicorn damien_mcp_server.main:app --host 0.0.0.0 --port 8892 --reload`
   - Expose it with ngrok using `ngrok http 8892`
   - Verify server endpoints are accessible and secured

2. **Claude Configuration**:
   - Configure Claude (via Anthropic Console or API) with:
     - MCP endpoint URL (ngrok URL + `/mcp/execute_tool`)
     - Authentication (API key in appropriate header)
     - Tool schemas from `tools/schemas/damien_all_tools.json`

3. **Progressive Testing**:
   - Test basic read operations
   - Test write operations with confirmation
   - Test rule management
   - Test rule application
   - Test multi-turn interactions

## Testing Plan

For the initial Claude integration test, prepare the following interactions:

1. **Simple Email Listing**:
   - "Damien, list my 5 most recent emails."
   - Expected: Claude calls `damien_list_emails` with `max_results: 5`

2. **Filtered Email Query**:
   - "Show me emails with subject containing 'Report'."
   - Expected: Claude calls `damien_list_emails` with `query: "subject:Report"`

3. **Email Details Retrieval**:
   - "What's in the email with ID XXXX?" (Use an actual ID from a previous listing)
   - Expected: Claude calls `damien_get_email_details` with that ID

4. **Safe Write Operation**:
   - "Mark emails from example@domain.com as read."
   - Expected: Claude first lists the emails, then asks for confirmation, then calls `damien_mark_emails`

5. **Rule Management**:
   - "Create a rule named 'Archive Newsletters' that moves emails from newsletter@example.com to the Archive label."
   - Expected: Claude constructs a proper rule definition and calls `damien_add_rule`

For each test, monitor:
- Claude's choice of tool
- Parameter construction
- Response handling
- Error recovery (if applicable)

## Debugging Tips

1. **Server Logs**: Set `DAMIEN_LOG_LEVEL=DEBUG` in `.env` for detailed logging
2. **ngrok Interface**: Monitor requests at http://127.0.0.1:4040
3. **Claude Chain of Thought**: Analyze how Claude decides which tools to use
4. **DynamoDB Console**: Check session context for multi-turn interactions
5. **Iterative Refinement**: Improve tool schemas based on observed Claude behavior
