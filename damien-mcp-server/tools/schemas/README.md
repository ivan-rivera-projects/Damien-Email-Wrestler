# Damien Tool Schemas for Claude Integration

This directory contains JSON schemas for Damien's tools, which can be used to configure Claude or other MCP-compliant AI assistants to use the Damien MCP Server.

## Schema Files

- `damien_all_tools.json` - Combined schema file containing all tools
- Individual schema files for each tool:
  - `damien_list_emails.json`
  - `damien_get_email_details.json` 
  - `damien_trash_emails.json`
  - `damien_label_emails.json`
  - `damien_mark_emails.json`
  - `damien_delete_emails_permanently.json`
  - `damien_apply_rules.json`
  - `damien_list_rules.json`
  - `damien_add_rule.json`
  - `damien_delete_rule.json`

## How to Use with Claude

To configure Claude to use these tools, you'll need to:

1. Deploy the Damien MCP Server and make it accessible via a public URL (e.g., using ngrok)
2. Configure Claude (via the Anthropic Console or API) with:
   - The URL of your MCP server's `/mcp/execute_tool` endpoint
   - Your MCP server's API key for authentication
   - The tool schemas from `damien_all_tools.json`

### Configuration Example

When configuring Claude via the Anthropic API, your request would include:

```json
{
  "model": "claude-3-5-sonnet-20240520",
  "max_tokens": 4096,
  "messages": [...],
  "tools": {
    "function_calling": "auto",
    "function_definitions": [
      // Copy the contents of damien_all_tools.json here
    ]
  },
  "tool_choice": "auto",
  "tool_resources": [
    {
      "type": "mcp",
      "configuration": {
        "endpoint": "https://your-ngrok-url.ngrok.io/mcp/execute_tool",
        "authentication": {
          "type": "header",
          "header": "X-Api-Key",
          "value": "your-mcp-server-api-key"
        }
      }
    }
  ]
}
```

## Prompt Tips for Claude

Once configured, you can instruct Claude to use Damien with prompts like:

- "List my 5 most recent unread emails"
- "Show me emails from newsletter@example.com"
- "Trash the emails with subject 'Old News'"
- "Apply my email rules but just do a dry run"
- "Add a rule to trash emails from spam@example.com"

For best results, follow a progressive testing strategy:
1. Start with simple read operations (list emails, get details)
2. Progress to safe write operations (labeling, marking as read)
3. Test destructive operations (trashing, deleting) with confirmations
4. Test complex operations (rule application, rule management)
5. Test multi-turn conversations that reference previous results

## Schema Management

These schemas were generated using the `generate_schemas.py` script in the parent directory. If you make changes to the Damien MCP Server's API, you should update this script and regenerate the schemas.
