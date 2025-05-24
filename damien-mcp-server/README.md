# Damien MCP Server

MCP Server for Damien-CLI functionalities. This server enables AI assistants like Claude to interact with Damien's Gmail management capabilities through the MCP protocol.

## Overview

The Damien MCP Server acts as a bridge between AI assistants and the Damien-CLI core functionalities. It exposes Damien's Gmail management capabilities as MCP tools that can be used by AI assistants through a standardized API.

### Key Features

- **MCP Protocol Support**: Implements the Model Context Protocol for seamless integration with AI assistants
- **Gmail Management**: Provides tools for listing, trashing, labeling, and managing emails
- **Optimized Email Fetching**: Supports granular header fetching with `include_headers` parameter for efficient API usage
- **Rule Management**: Allows creating, listing, and applying Gmail filtering rules
- **Session Context**: Maintains conversation context using DynamoDB for multi-turn interactions
- **Secure Authentication**: Uses existing Damien-CLI token-based authentication with Gmail
- **Smithery SDK Integration**: Can be integrated with Smithery SDK for enhanced discovery and standardized MCP compliance

### Performance Optimizations

The server includes several performance optimizations:

- **Granular Header Fetching**: Use `include_headers` parameter to fetch only specific email headers (e.g., `["From", "Subject"]`)
- **Reduced API Calls**: Single API call instead of multiple detail fetches (up to 16x improvement)
- **Minimal Data Transfer**: Only requested headers are transferred, reducing bandwidth usage
- **Efficient Validation**: Robust parameter validation handles both array and JSON string formats

### Architecture

The server follows a clean, layered architecture:

1. **API Layer** (FastAPI endpoints): Handles HTTP requests, validation, and response formatting
2. **Adapter Layer** (DamienAdapter): Bridges between MCP requests and Damien core_api calls
3. **Core Layer** (Damien core_api): Provides the underlying Gmail/Rules functionality
4. **Storage Layer** (DynamoDB): Stores session context for multi-turn conversations

## Prerequisites

- Python 3.13+
- Poetry for dependency management
- AWS account (for DynamoDB session storage)
- Damien-CLI with valid Gmail authentication (token.json)

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd damien_mcp_server
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

## Configuration

The server requires several configuration parameters to run correctly. These can be set via environment variables or in a `.env` file in the project root.

Copy the example configuration file and adjust as needed:
```bash
cp .env.example .env
# Edit the .env file with appropriate values
```

Required environment variables include:

```
DAMIEN_MCP_SERVER_API_KEY=YOUR_SECURE_API_KEY_HERE
DAMIEN_GMAIL_TOKEN_JSON_PATH=/path/to/your/damien_cli_project/data/token.json
DAMIEN_GMAIL_CREDENTIALS_JSON_PATH=/path/to/your/damien_cli_project/credentials.json
DAMIEN_DYNAMODB_SESSION_TABLE_NAME=DamienMCPSessions
DAMIEN_DYNAMODB_REGION=us-east-1
DAMIEN_DYNAMODB_SESSION_TTL_SECONDS=86400
AWS_REGION=us-east-1
DAMIEN_LOG_LEVEL=INFO
DAMIEN_DEFAULT_USER_ID=damien_user_default
```

### DynamoDB Setup

You need to create a DynamoDB table with the following configuration:

- **Table Name**: `DamienMCPSessions` (or your custom name from env var)
- **Primary Key**: 
  - Partition key: `user_id` (String)
  - Sort key: `session_id` (String)
- **TTL**: Enable with attribute name `ttl`
- **Billing Mode**: Pay-per-request (on-demand) is recommended for development

You can create the table using AWS CLI:

```bash
aws dynamodb create-table \
  --table-name DamienMCPSessions \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=session_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=session_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Enable TTL
aws dynamodb update-time-to-live \
  --table-name DamienMCPSessions \
  --time-to-live-specification "Enabled=true, AttributeName=ttl" \
  --region us-east-1
```

#### IAM Permissions

Ensure your AWS user or role has appropriate permissions for DynamoDB operations:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/DamienMCPSessions",
        "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/DamienMCPSessions/index/*"
      ]
    }
  ]
}
```

### Gmail Authentication

Make sure Damien CLI is properly authenticated with Gmail:

```bash
cd ../damien_cli_project
poetry run damien login
```

This will create a token.json file that the MCP server will use.

## Running the Server

Start the development server:

```bash
poetry run uvicorn app.main:app --reload --port 8892
```

For production:

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8892
```

## Available MCP Tools

The following MCP tools are currently implemented:

1. **damien_list_emails**
   - Lists emails from your Gmail account based on query parameters
   - Parameters:
     - `query`: Optional Gmail query string (e.g., "is:unread", "from:example.com")
     - `max_results`: Maximum number of emails to retrieve (default: 10)
     - `page_token`: Optional token for pagination
   - Example request:
     ```json
     {
       "tool_name": "damien_list_emails",
       "input": {
         "query": "is:unread",
         "max_results": 5
       },
       "session_id": "conversation_123456789"
     }
     ```

2. **damien_get_email_details**
   - Retrieves detailed information about a specific email
   - Parameters:
     - `message_id`: ID of the email to retrieve (required)
     - `format`: Format of the details to retrieve (default: "full")
   - Example request:
     ```json
     {
       "tool_name": "damien_get_email_details",
       "input": {
         "message_id": "1234abcd5678",
         "format": "full"
       },
       "session_id": "conversation_123456789"
     }
     ```

3. **damien_trash_emails**
   - Moves specified emails to the trash folder
   - Parameters:
     - `message_ids`: List of email IDs to trash (required)
   - Example request:
     ```json
     {
       "tool_name": "damien_trash_emails",
       "input": {
         "message_ids": ["1234abcd5678", "8765dcba4321"]
       },
       "session_id": "conversation_123456789"
     }
     ```

4. **damien_label_emails**
   - Adds or removes labels from specified emails
   - Parameters:
     - `message_ids`: List of email IDs to modify (required)
     - `add_label_names`: List of label names to add
     - `remove_label_names`: List of label names to remove
   - Example request:
     ```json
     {
       "tool_name": "damien_label_emails",
       "input": {
         "message_ids": ["1234abcd5678"],
         "add_label_names": ["Important", "Follow-up"],
         "remove_label_names": ["Pending"]
       },
       "session_id": "conversation_123456789"
     }
     ```

5. **damien_mark_emails**
   - Marks emails as read or unread
   - Parameters:
     - `message_ids`: List of email IDs to mark (required)
     - `mark_as`: Either "read" or "unread" (required)
   - Example request:
     ```json
     {
       "tool_name": "damien_mark_emails",
       "input": {
         "message_ids": ["1234abcd5678", "8765dcba4321"],
         "mark_as": "read"
       },
       "session_id": "conversation_123456789"
     }
     ```

6. **damien_apply_rules**
   - Applies email filtering rules to your Gmail account
   - Parameters:
     - `rule_ids_to_apply`: Optional list of specific rule IDs to apply
     - `gmail_query_filter`: Optional Gmail query to pre-filter emails
     - `scan_limit`: Maximum number of emails to scan
     - `date_after`: Only process emails after this date (YYYY/MM/DD)
     - `date_before`: Only process emails before this date (YYYY/MM/DD)
     - `dry_run`: If true, simulate without making changes
   - Example request:
     ```json
     {
       "tool_name": "damien_apply_rules",
       "input": {
         "gmail_query_filter": "in:inbox",
         "scan_limit": 100,
         "dry_run": true
       },
       "session_id": "conversation_123456789"
     }
     ```

7. **damien_list_rules**
   - Lists all email filtering rules
   - No parameters required
   - Example request:
     ```json
     {
       "tool_name": "damien_list_rules",
       "input": {},
       "session_id": "conversation_123456789"
     }
     ```

8. **damien_add_rule**
   - Adds a new email filtering rule
   - Parameters:
     - `rule_definition`: Rule definition object (required)
   - Example request:
     ```json
     {
       "tool_name": "damien_add_rule",
       "input": {
         "rule_definition": {
           "name": "Archive Newsletters",
           "description": "Move newsletter emails to archive",
           "is_enabled": true,
           "conditions": [
             {"field": "subject", "operator": "contains", "value": "Newsletter"}
           ],
           "condition_conjunction": "AND",
           "actions": [
             {"type": "add_label", "label_name": "Newsletter"}
           ]
         }
       },
       "session_id": "conversation_123456789"
     }
     ```

9. **damien_delete_rule**
   - Deletes an existing rule by ID or name
   - Parameters:
     - `rule_identifier`: ID or name of the rule to delete (required)
   - Example request:
     ```json
     {
       "tool_name": "damien_delete_rule",
       "input": {
         "rule_identifier": "Archive Newsletters"
       },
       "session_id": "conversation_123456789"
     }
     ```

10. **damien_delete_emails_permanently**
    - Permanently deletes emails (cannot be recovered)
    - Parameters:
      - `message_ids`: List of email IDs to delete permanently (required)
    - Example request:
      ```json
      {
        "tool_name": "damien_delete_emails_permanently",
        "input": {
          "message_ids": ["1234abcd5678"]
        },
        "session_id": "conversation_123456789"
      }
      ```

## API Endpoints

### Authentication

All protected endpoints require the `X-API-Key` header with your API key.

### Health Check

- `GET /health`: Check if the server is running (public)

### Test Endpoints

- `GET /mcp/protected-test`: Test authentication (protected)
- `GET /mcp/gmail-test`: Test Gmail connection (protected)

### MCP Tool Endpoints

- `GET /mcp/list_tools`: Discover available tools and their schemas (protected)
- `POST /mcp/execute_tool`: Execute an MCP tool (protected)
  - Request body must conform to the `MCPExecuteToolServerRequest` schema
  - Returns an `MCPExecuteToolServerResponse` with the results or error

## API Documentation

Once running, access the interactive API documentation:

- Swagger UI: http://127.0.0.1:8892/docs
- ReDoc: http://127.0.0.1:8892/redoc

### Usage Examples

#### Optimized Email Listing with Header Fetching

The `include_headers` parameter allows you to fetch only specific email headers in a single API call, dramatically improving performance:

```bash
# Fetch only From headers for 5 unread emails (1 API call instead of 6)
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8892/mcp/execute_tool \
     -d '{
       "tool_name": "damien_list_emails",
       "input": {
         "query": "is:unread",
         "max_results": 5,
         "include_headers": ["From"]
       },
       "session_id": "example-session"
     }'
```

```bash
# Fetch multiple headers for efficient email preview
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8892/mcp/execute_tool \
     -d '{
       "tool_name": "damien_list_emails",
       "input": {
         "query": "in:inbox",
         "max_results": 10,
         "include_headers": ["From", "Subject", "Date"]
       },
       "session_id": "example-session"
     }'
```

#### Optimized Email Details

```bash
# Get specific headers for a single email
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8892/mcp/execute_tool \
     -d '{
       "tool_name": "damien_get_email_details",
       "input": {
         "message_id": "your-message-id",
         "include_headers": ["From", "To", "Subject", "Date", "Reply-To"]
       },
       "session_id": "example-session"
     }'
```

#### Performance Comparison

**Before optimization (old approach):**
- List 15 emails: 16 API calls (1 list + 15 detail calls)
- Large data transfer (full email metadata for each)
- Slower response times

**After optimization (with include_headers):**
- List 15 emails with From headers: 1 API call
- Minimal data transfer (only requested headers)
- 16x performance improvement

#### Common Header Options

- `["From"]` - Sender information only
- `["From", "Subject"]` - Sender and subject for email previews  
- `["From", "To", "Subject", "Date"]` - Complete email summary
- `["Message-ID", "Reply-To"]` - For email threading and responses

## Configuring Claude to Use This Server

To configure Claude to use the MCP server, you'll need to provide the following information:

1. Server URL: `http://your-server-address:8892` (or your public ngrok URL)
2. API key: The value from your `.env` file (`DAMIEN_MCP_SERVER_API_KEY`)
3. Tool definitions: Use the JSON schemas from the `/mcp/list_tools` endpoint

Example tool definition for `damien_list_emails`:

```json
{
  "name": "damien_list_emails",
  "description": "Lists email messages based on a query, with support for pagination.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Gmail search query (e.g., 'is:unread', 'from:example.com')"
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of emails to retrieve",
        "default": 10
      },
      "page_token": {
        "type": "string",
        "description": "Token for fetching the next page of results"
      }
    }
  }
}
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black app tests
```

### Linting

```bash
poetry run flake8 app tests
```

## Troubleshooting

### Common Issues

#### DynamoDB Connection Issues

If you encounter DynamoDB connection issues:

```bash
# Check the table status
aws dynamodb describe-table --table-name DamienMCPSessions --region us-east-1 --query "Table.TableStatus"

# Verify your IAM permissions
aws iam list-attached-user-policies --user-name $(aws iam get-user --query "User.UserName" --output text)

# Test DynamoDB connection
aws dynamodb list-tables --region us-east-1
```

#### Gmail Authentication Issues

If you encounter Gmail authentication issues:

1. Check that token.json exists and is valid:
   ```bash
   cat /path/to/your/damien_cli_project/data/token.json
   ```

2. Re-authenticate with Damien CLI:
   ```bash
   cd ../damien_cli_project
   poetry run damien login
   ```

3. Check logs for specific error messages:
   ```bash
   tail -f logs/server.log
   ```

#### API Testing

You can test the server's endpoints using curl:

```bash
# Check if the server is running
curl http://localhost:8892/health

# Test authentication
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8892/mcp/protected-test

# Test Gmail connection
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8892/mcp/gmail-test

# Get list of available tools
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8892/mcp/list_tools

# Execute the list_emails tool
curl -X POST \
  http://localhost:8892/mcp/execute_tool \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "tool_name": "damien_list_emails",
    "input": {
      "query": "is:unread",
      "max_results": 5
    },
    "session_id": "test_session_1"
  }'
```

## Smithery SDK Integration

The Damien MCP Server has been designed to be compatible with the Smithery SDK. This enables enhanced discovery and standardized MCP compliance for AI assistants.

### Integration Steps

1. **Ensure the Damien MCP Server is running and accessible**
2. **Install Node.js and npm/yarn for Smithery SDK**
3. **Create a new directory for the Smithery adapter:**

```bash
mkdir damien-smithery-adapter
cd damien-smithery-adapter
npm init -y
```

4. **Install Smithery SDK dependencies:**

```bash
npm install @smithery/sdk @modelcontextprotocol/sdk
npm install typescript ts-node @types/node dotenv --save-dev
```

5. **Configure the Smithery adapter to connect to your Damien MCP Server**

```typescript
// Example configuration
const CONFIG = {
  DAMIEN_MCP_SERVER_URL: process.env.DAMIEN_MCP_SERVER_URL || 'http://localhost:8892',
  DAMIEN_MCP_SERVER_API_KEY: process.env.DAMIEN_MCP_SERVER_API_KEY || '',
  SERVER_PORT: parseInt(process.env.SERVER_PORT || '8081', 10),
  SERVER_NAME: process.env.SERVER_NAME || 'Damien Email Manager',
  SERVER_VERSION: process.env.SERVER_VERSION || '1.0.0',
}
```

6. **Implement a client to connect to the Damien MCP Server**

The Smithery adapter uses HTTP requests to communicate with the Damien MCP Server via these endpoints:

- `GET /mcp/list_tools`: Retrieves available tools and their schemas
- `POST /mcp/execute_tool`: Executes a specific tool with parameters

7. **Create a stateless MCP server with the Smithery SDK**

The Smithery SDK can register all tools from the Damien MCP Server and handle tool execution through a standardized interface.

For a complete guide on implementing the Smithery adapter, refer to the integration document.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
