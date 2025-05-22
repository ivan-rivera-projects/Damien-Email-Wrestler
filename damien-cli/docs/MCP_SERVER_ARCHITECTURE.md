# Damien MCP Server Architecture

This document outlines the architecture of the Damien MCP Server, which allows Claude and other AI assistants to interact with Damien's core functionality.

## Overview

The Damien MCP Server is a FastAPI-based server that implements the Machine Conversational Protocol (MCP). It acts as a bridge between AI assistants (like Claude) and Damien's core email management functionality.

The server exposes Damien's capabilities as tools that Claude can invoke, with contextual awareness across multiple interactions.

## System Architecture

The MCP Server is built with a layered architecture:

```
┌───────────────────┐
│  AI Assistant     │ Claude or other MCP-compliant AI
└─────────┬─────────┘
          │ HTTP (MCP Protocol)
┌─────────▼─────────────────────────────────────────┐
│ Damien MCP Server (FastAPI)                       │
│ ┌─────────────────┐  ┌───────────────────────┐    │
│ │ Authentication  │  │ MCP Tool Endpoints     │    │
│ │ (API Keys)      │  │ (/mcp/execute_tool)   │    │
│ └─────────────────┘  └───────────┬───────────┘    │
│                                  │                │
│ ┌─────────────────┐  ┌───────────▼───────────┐    │
│ │ DynamoDB        │◄─┤ DamienAdapter         │    │
│ │ Session Context │  │ (Service Layer)       │    │
│ └─────────────────┘  └───────────┬───────────┘    │
└─────────────────────────────────┬─────────────────┘
                                  │
┌─────────────────────────────────▼─────────────────┐
│ Damien Core API                                   │
│ ┌─────────────────┐  ┌───────────────────────┐    │
│ │ gmail_api_      │  │ rules_api_service.py  │    │
│ │ service.py      │  │                       │    │
│ └─────────────────┘  └───────────────────────┘    │
└─────────────────────────────────┬─────────────────┘
                                  │
┌─────────────────────────────────▼─────────────────┐
│ External Services                                 │
│ ┌─────────────────┐  ┌───────────────────────┐    │
│ │ Gmail API       │  │ Local Files           │    │
│ │ (Google)        │  │ (rules.json, etc)     │    │
│ └─────────────────┘  └───────────────────────┘    │
└───────────────────────────────────────────────────┘
```

## Key Components

### 1. Authentication & Security

- **API Key Authentication**: All requests to the MCP Server require a valid API key.
- **Environment-Based Configuration**: Sensitive configuration (API keys, paths) is handled via environment variables.
- **Security Validations**: Input validation using Pydantic models.

### 2. MCP Protocol Implementation

- **Tool Execution Endpoint**: `/mcp/execute_tool` handles requests from Claude.
- **Tool Response Format**: Follows the MCP specification with consistent error handling.
- **Session Context**: Uses DynamoDB to maintain state across multiple interactions.

### 3. DamienAdapter

- **Bridge to Damien Core**: Translates MCP tool calls into Damien core_api operations.
- **Tool-Specific Methods**: One method per tool with appropriate parameter mapping.
- **Error Handling**: Maps Damien errors to MCP-compliant error responses.

### 4. Session Context Management

- **DynamoDB Integration**: Stores and retrieves session context based on user_id and session_id.
- **Context Structure**: Maintains history of tool calls and their results.
- **TTL Management**: Automatically expires old session data.

## Tools Exposed to Claude

The MCP Server exposes the following Damien tools to Claude:

1. **damien_list_emails**: List email summaries with filtering options.
2. **damien_get_email_details**: Get detailed information about a specific email.
3. **damien_trash_emails**: Move emails to the trash folder.
4. **damien_label_emails**: Add or remove labels from emails.
5. **damien_mark_emails**: Mark emails as read or unread.
6. **damien_delete_emails_permanently**: Permanently delete emails (with warnings).
7. **damien_apply_rules**: Apply configured rules to emails with filtering options.
8. **damien_list_rules**: List all configured filtering rules.
9. **damien_add_rule**: Add a new filtering rule.
10. **damien_delete_rule**: Delete an existing rule.

## Configuration 

The MCP Server uses Pydantic's `BaseSettings` for configuration, supporting:

- Environment variables
- `.env` file for local development
- Nested settings models for organization

Key configuration includes:
- API authentication key
- Gmail token and credentials paths
- DynamoDB table name and region
- Logging level

## Data Flow: Example Interaction

1. Claude sends an MCP request to `/mcp/execute_tool` with:
   - `tool_name`: "damien_list_emails"
   - `params`: {"query": "is:unread", "max_results": 5}
   - `session_id`: "conversation_123"

2. The MCP Server:
   - Validates the API key
   - Validates the request parameters using Pydantic
   - Calls `adapter.list_emails_tool(query="is:unread", max_results=5)`

3. The DamienAdapter:
   - Gets an authenticated Gmail service client
   - Calls `damien_cli.core_api.gmail_api_service.list_messages()`
   - Transforms the response into the expected format

4. The MCP Server:
   - Stores the result in DynamoDB with the session_id
   - Returns an MCP-compliant response to Claude with the email list

5. Claude can then reference this data in subsequent requests, such as:
   - "Get details of the first email in that list"
   - "Trash those emails from XYZ"

## Testing

The MCP Server includes a comprehensive test suite:

- **Unit Tests**: For individual components (adapter, services)
- **Integration Tests**: For API endpoints
- **Mocking**: Tests use mocks for external dependencies (DynamoDB, Damien core_api)

## Deployment Options

The server can be deployed in various ways:

1. **Local Development**: Using uvicorn directly
2. **Exposed via ngrok**: For testing with Claude
3. **Cloud Deployment** (future): AWS/GCP/Azure for production use
