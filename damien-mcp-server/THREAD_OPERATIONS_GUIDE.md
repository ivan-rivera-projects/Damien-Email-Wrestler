# Thread Operations Documentation

## Overview

The Damien MCP Server now provides comprehensive email thread management capabilities through 5 dedicated tools. Thread operations enable managing entire email conversations as units, which is essential for professional email workflow automation.

## What are Email Threads?

Email threads (also called conversations) are groups of related emails that share the same conversation context. When you reply to an email or forward it, Gmail groups these messages together as a thread. Thread operations allow you to:

- View entire conversations at once
- Apply actions to all messages in a conversation
- Manage conversation-level metadata and labels
- Organize related emails as cohesive units

## Available Thread Tools

### 1. `damien_list_threads`
**Purpose**: List email threads with optional filtering and pagination

**Parameters**:
- `query` (optional): Gmail query string to filter threads
- `max_results` (default: 100): Maximum number of threads to return (1-500)
- `page_token` (optional): Token for pagination

**Example**:
```json
{
  "tool_name": "damien_list_threads",
  "input": {
    "query": "subject:project OR from:client@company.com",
    "max_results": 20
  },
  "session_id": "list_threads_session"
}
```

**Use Cases**:
- Find all threads about a specific project
- List conversations with specific people
- Get recent thread activity with pagination

### 2. `damien_get_thread_details`
**Purpose**: Get complete information about a specific thread including all messages

**Parameters**:
- `thread_id` (required): Thread ID to retrieve
- `format` (default: "full"): Detail level - "full", "metadata", or "minimal"

**Example**:
```json
{
  "tool_name": "damien_get_thread_details", 
  "input": {
    "thread_id": "194bd65e470d1f51",
    "format": "full"
  },
  "session_id": "thread_details_session"
}
```

**Use Cases**:
- Review complete conversation history
- Analyze thread participants and timeline
- Extract information from multi-message discussions

### 3. `damien_modify_thread_labels`
**Purpose**: Add or remove labels from an entire thread

**Parameters**:
- `thread_id` (required): Thread ID to modify
- `add_labels` (optional): Array of label names to add
- `remove_labels` (optional): Array of label names to remove

**Example**:
```json
{
  "tool_name": "damien_modify_thread_labels",
  "input": {
    "thread_id": "194bd65e470d1f51", 
    "add_labels": ["Project Alpha", "Priority"],
    "remove_labels": ["INBOX"]
  },
  "session_id": "label_thread_session"
}
```

**Use Cases**:
- Organize conversations by project or priority
- Archive entire conversations (remove INBOX label)
- Apply workflow labels to complete discussions

### 4. `damien_trash_thread`
**Purpose**: Move an entire thread to trash (reversible action)

**Parameters**:
- `thread_id` (required): Thread ID to move to trash

**Example**:
```json
{
  "tool_name": "damien_trash_thread",
  "input": {
    "thread_id": "194bd65e470d1f51"
  },
  "session_id": "trash_thread_session"
}
```

**Use Cases**:
- Remove unwanted conversations from inbox
- Clean up completed project discussions
- Temporarily hide conversations (reversible)

### 5. `damien_delete_thread_permanently`
**Purpose**: Permanently delete an entire thread (irreversible action)

**Parameters**:
- `thread_id` (required): Thread ID to permanently delete

**Example**:
```json
{
  "tool_name": "damien_delete_thread_permanently",
  "input": {
    "thread_id": "194bd65e470d1f51"
  },
  "session_id": "delete_thread_session"
}
```

**Use Cases**:
- Permanently remove sensitive conversations
- Delete spam or unwanted thread conversations
- Clean up storage space (use with extreme caution)

## Advanced Usage Examples

### Workflow: Project Thread Management
```bash
# 1. Find all threads about "Project Alpha"
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_API_KEY" \\
-d '{
  "tool_name": "damien_list_threads",
  "input": {
    "query": "subject:(Project Alpha) OR body:(Project Alpha)",
    "max_results": 50
  },
  "session_id": "project_alpha_threads"
}' http://localhost:8892/mcp/execute_tool

# 2. Get details for a specific project thread
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_API_KEY" \\
-d '{
  "tool_name": "damien_get_thread_details",
  "input": {
    "thread_id": "THREAD_ID_FROM_STEP_1",
    "format": "metadata"
  },
  "session_id": "project_thread_details"
}' http://localhost:8892/mcp/execute_tool

# 3. Label all project threads for organization
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_API_KEY" \\
-d '{
  "tool_name": "damien_modify_thread_labels",
  "input": {
    "thread_id": "THREAD_ID_FROM_STEP_1",
    "add_labels": ["Project Alpha", "Completed"],
    "remove_labels": ["INBOX"]
  },
  "session_id": "label_project_thread"
}' http://localhost:8892/mcp/execute_tool
```

### Workflow: Conversation Cleanup
```bash
# 1. Find old threads from specific sender
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_API_KEY" \\
-d '{
  "tool_name": "damien_list_threads",
  "input": {
    "query": "from:newsletter@company.com older_than:30d",
    "max_results": 100
  },
  "session_id": "old_newsletter_threads"
}' http://localhost:8892/mcp/execute_tool

# 2. Trash multiple old threads (reversible)
# Note: This would be done in a loop for each thread_id from step 1
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_API_KEY" \\
-d '{
  "tool_name": "damien_trash_thread",
  "input": {
    "thread_id": "THREAD_ID_FROM_STEP_1"
  },
  "session_id": "cleanup_old_threads"
}' http://localhost:8892/mcp/execute_tool
```

## Integration with Email Rules

Thread operations can be integrated with Damien's rule system for automated workflow management:

```json
{
  "rule_name": "Project Completion Thread Management",
  "conditions": [
    {"field": "subject", "operator": "contains", "value": "Project Complete"},
    {"field": "thread_message_count", "operator": "greater_than", "value": 5}
  ],
  "actions": [
    {
      "type": "modify_thread_labels",
      "parameters": {
        "add_labels": ["Completed Projects"],
        "remove_labels": ["Active", "INBOX"]
      }
    }
  ]
}
```

## Thread vs Individual Email Operations

| Operation | Individual Emails | Thread Operations |
|-----------|------------------|-------------------|
| **Scope** | Single message | Entire conversation |
| **Efficiency** | Good for specific emails | Better for conversations |
| **Use Case** | Targeted actions | Workflow management |
| **Reversibility** | Per-message | Per-conversation |

**When to use Thread Operations**:
- Managing project conversations
- Organizing client communications
- Bulk conversation management
- Workflow-based email processing

**When to use Email Operations**:
- Targeting specific messages
- Fine-grained email management
- Message-level processing
- Individual email actions

## Error Handling

All thread operations include comprehensive error handling:

- **Invalid Thread ID**: Clear error message when thread doesn't exist
- **Permission Issues**: Helpful guidance for access problems
- **Rate Limiting**: Automatic retry logic and user feedback
- **Network Issues**: Graceful degradation and retry mechanisms

## Performance Considerations

- **Thread Listing**: Optimized Gmail API queries for fast results
- **Thread Details**: Efficient retrieval with format options
- **Label Operations**: Batch processing for multiple label changes
- **Rate Limiting**: Integrated with Gmail API limits

## Security Notes

- **Permanent Deletion**: `damien_delete_thread_permanently` is irreversible
- **Label Management**: Ensure proper permissions for label operations
- **Thread Access**: Operations respect Gmail API access permissions
- **Audit Trail**: All thread operations are logged for tracking

## Testing Thread Operations

The thread operations system includes comprehensive testing:

1. **Unit Tests**: All handler functions tested with mocked Gmail API
2. **Integration Tests**: End-to-end testing with real Gmail threads
3. **Direct Testing**: Framework for testing handlers independently
4. **Real-world Validation**: Tested with actual email conversations

Example test thread: "The 'Burbs" thread (ID: `194bd65e470d1f51`) with 9 messages demonstrated successful:
- Thread listing and filtering
- Complete thread details retrieval
- Label management operations
- Thread status management

## Future Enhancements

Thread operations provide the foundation for advanced features:

- **Thread-based Rules**: Automated conversation management
- **Thread Analytics**: Conversation metrics and insights
- **Thread Templates**: Standardized conversation responses
- **Thread Workflows**: Multi-step conversation automation
- **Calendar Integration**: Thread-based meeting and event management

## Support and Troubleshooting

For issues with thread operations:

1. **Check Thread ID**: Ensure the thread ID exists and is accessible
2. **Verify Permissions**: Confirm Gmail API access and scopes
3. **Test with Known Threads**: Use thread IDs from `damien_list_threads`
4. **Review Error Messages**: Thread operations provide detailed error context
5. **Check Rate Limits**: Monitor Gmail API usage and limits

Thread operations are production-ready and provide the foundation for advanced email workflow automation in the Damien platform.
