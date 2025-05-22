# Damien MCP Server - Claude Integration Checklist

This checklist outlines all the steps needed to integrate the Damien MCP Server with Claude or other MCP-compliant AI assistants.

## 1. Schema Preparation

- [ ] Generate formal JSON schemas for all ten Damien tools from Pydantic models
  - [ ] damien_list_emails
  - [ ] damien_get_email_details
  - [ ] damien_trash_emails
  - [ ] damien_label_emails 
  - [ ] damien_mark_emails
  - [ ] damien_delete_emails_permanently
  - [ ] damien_apply_rules
  - [ ] damien_list_rules
  - [ ] damien_add_rule
  - [ ] damien_delete_rule
- [ ] Ensure each schema has:
  - [ ] Clear `name` field
  - [ ] Comprehensive `description` that helps Claude understand when to use the tool
  - [ ] Detailed `input_schema` with proper types and descriptions
  - [ ] Optional `output_schema` to help Claude understand the return format
- [ ] Review schemas for security considerations (especially for destructive operations)
- [ ] Create a combined JSON file with all tool schemas for easy Claude configuration

## 2. Server Deployment

- [ ] Configure server for local testing
  - [ ] Ensure all environment variables are properly set in `.env`
  - [ ] Run server with: `poetry run uvicorn damien_mcp_server.app.main:app --host 0.0.0.0 --port 8892 --reload`
- [ ] Expose server for Claude access
  - [ ] Install ngrok if not already available
  - [ ] Run: `ngrok http 8892`
  - [ ] Note the assigned HTTPS URL for Claude configuration
- [ ] Verify server endpoints are accessible and secured
  - [ ] Test `/health` endpoint 
  - [ ] Test `/mcp/protected-test` endpoint with API key
  - [ ] Test `/mcp/gmail-test` endpoint to verify Gmail connection

## 3. Claude Configuration

- [ ] Create tool configuration in Claude
  - [ ] Set up MCP endpoint URL (ngrok URL + `/mcp/execute_tool`)
  - [ ] Configure authentication (API key in appropriate header)
  - [ ] Add all ten tool schemas to Claude
- [ ] Configure appropriate session handling
  - [ ] Ensure proper session_id passing for context management
  - [ ] Set appropriate permissions for Claude's tool use

## 4. Progressive Testing

- [ ] Test basic read operations
  - [ ] Simple email listing
  - [ ] Filtered email queries
  - [ ] Email detail retrieval
- [ ] Test write operations with confirmation
  - [ ] Mark emails as read/unread
  - [ ] Add/remove labels
  - [ ] Trash emails
- [ ] Test rule management
  - [ ] List existing rules
  - [ ] Create new rules
  - [ ] Delete rules
- [ ] Test rule application
  - [ ] Dry run execution
  - [ ] Full execution with confirmation
- [ ] Test multi-turn interactions
  - [ ] Operations that reference previous results
  - [ ] Complex multi-step workflows
  - [ ] Verify context persistence across requests

## 5. Error Handling & Edge Cases

- [ ] Test error conditions
  - [ ] Invalid email IDs
  - [ ] Non-existent rules
  - [ ] Permission issues with Gmail
  - [ ] Resource limits (scan limits, API quotas)
- [ ] Observe Claude's handling of errors
  - [ ] Clear error communication to users
  - [ ] Recovery suggestions

## 6. Documentation & Refinement

- [ ] Update user documentation with Claude integration examples
- [ ] Document any discovered limitations or best practices
- [ ] Refine schemas based on testing observations
  - [ ] Improve descriptions where Claude misunderstands
  - [ ] Add examples for complex parameters
  - [ ] Adjust parameter constraints if needed

## 7. Production Considerations (Future)

- [ ] Plan for more persistent deployment
  - [ ] Proper cloud hosting (AWS/GCP/Azure)
  - [ ] HTTPS with proper SSL certificates
  - [ ] Authentication hardening
- [ ] Performance optimizations
  - [ ] Caching strategies
  - [ ] Connection pooling
  - [ ] Rate limiting
- [ ] Monitoring & alerting
  - [ ] Usage metrics
  - [ ] Error rates
  - [ ] Resource utilization

## 8. Advanced Features (Optional)

- [ ] Implement fine-grained permissions system
- [ ] Add additional tools based on user feedback
- [ ] Support for multiple users/accounts
- [ ] Custom deployment options or configurations
