# Damien MCP Server Tool Usage Configuration

This document explains how the MCP Server Configuration enforces direct tool usage for AI clients.

## Overview

The Damien MCP Server provides two methods for executing tools:

1. **Direct MCP Tools** (Preferred): Using the direct MCP tool interface with the tool name and parameters
2. **API Endpoints** (Fallback): Using the `/mcp/execute_tool` HTTP endpoint

The server is configured to prioritize direct MCP tool usage to encourage optimal performance and proper integration.

## Configuration Options

The server supports two enforcement policies:

- `direct_mcp_preferred`: Allows both methods but adds usage guidance to API responses
- `direct_mcp_only`: Strictly enforces direct MCP tool usage and rejects API endpoint calls

## Implementation Details

The implementation consists of:

1. **Tool Usage Configuration** (`app/core/tool_usage_config.py`):
   - Defines policy options and default settings
   - Provides methods to get and update configuration

2. **API Enforcement** (`app/routers/tools.py`):
   - Adds warning logs for API endpoint usage
   - Rejects API calls if `direct_mcp_only` policy is active
   - Adds usage guidance to API responses
   
3. **Policy Control** (`app/main.py`):
   - Provides HTTP endpoints to view and update policies
   - Includes policy info in health checks

## API Endpoints

- `GET /health`: Shows server status and current tool usage policy
- `GET /mcp/tool-usage-policy`: Returns detailed policy configuration
- `POST /mcp/tool-usage-policy`: Updates policy configuration

## Example Usage

### Set Policy to Direct MCP Only:

```bash
curl -H "X-API-Key: YOUR_API_KEY" -H "Content-Type: application/json" \
     -X POST -d '{"policy":"direct_mcp_only"}' \
     http://localhost:8892/mcp/tool-usage-policy
```

### Set Policy to Direct MCP Preferred:

```bash
curl -H "X-API-Key: YOUR_API_KEY" -H "Content-Type: application/json" \
     -X POST -d '{"policy":"direct_mcp_preferred"}' \
     http://localhost:8892/mcp/tool-usage-policy
```

## Benefits

- **Automatic Enforcement**: No need to modify prompts or instructions
- **Server-side Control**: Enforced at the infrastructure level
- **Universal Application**: Works for any AI engine connecting to the server
- **No Client Dependencies**: Doesn't rely on AI engines following instructions

## Recommendations

For most deployments, use `direct_mcp_preferred` to encourage best practices while maintaining compatibility with API-based clients.

For strict environments or to enforce proper integration, use `direct_mcp_only` policy.
