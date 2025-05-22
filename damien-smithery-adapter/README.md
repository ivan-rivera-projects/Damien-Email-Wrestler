# Damien Smithery Adapter

This is a Smithery SDK adapter for the Damien MCP Server. It enables AI assistants like Claude to interact with Damien's Gmail management capabilities through the Smithery SDK's implementation of the Model Context Protocol (MCP).

## Overview

The Damien Smithery Adapter acts as a bridge between the Smithery SDK and the Damien MCP Server. It exposes Damien's Gmail management tools in a way that conforms to the Smithery SDK's expectations.

## Prerequisites

- Node.js 18+
- A running Damien MCP Server instance (on port 8892 by default)
- (Optional) A Smithery Registry account for tool registration

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd damien_smithery_adapter
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables by creating a `.env` file:
   ```bash
   cp .env.example .env
   # Edit the .env file with appropriate values
   ```

   Required environment variables include:
   ```
   DAMIEN_MCP_SERVER_URL=http://localhost:8892
   DAMIEN_MCP_SERVER_API_KEY=your_damien_mcp_server_api_key
   SERVER_PORT=8081
   SERVER_NAME="Damien Email Manager (Smithery Adapter)"
   SERVER_VERSION="1.0.0"
   SMITHERY_BEARER_AUTH=your_smithery_registry_token_here
   ```

## Usage

### Building the Adapter

```bash
npm run build
```

This will compile the TypeScript code to JavaScript in the `dist` directory.

### Starting the Adapter

```bash
npm run serve
```

This will start the Smithery adapter server on the port specified in your `.env` file (default: 8081). The server will connect to the Damien MCP Server and expose its tools via the Model Context Protocol.

### Development Mode

```bash
npm run start
```

This will compile and start the server in one step, useful during development.

### Registering with Smithery Registry

If you have a Smithery Registry account, you can register your adapter:

```bash
npm run register
```

Note: Due to current limitations in the Smithery Registry SDK (version 0.3.7), automatic registration might not be available. The script will provide instructions for manual registration.

Manual registration options:
1. Use the Smithery CLI tool: `npx @smithery/cli register --manual`
2. Visit the Smithery Registry website: https://smithery.ai/
3. Consider updating to a newer version of the Smithery SDK that supports direct registration

## How It Works

1. The adapter fetches tool definitions from your Damien MCP Server.
2. It registers these tools with the Smithery SDK's MCP implementation.
3. When an AI assistant calls a tool, the adapter:
   - Receives the request
   - Forwards it to your Damien MCP Server
   - Returns the result to the AI assistant

## Architecture

```
┌───────────────┐          ┌───────────────────┐          ┌──────────────────┐
│               │          │                   │          │                  │
│   AI Agent    │◄────────►│  Smithery SDK     │◄────────►│  Damien MCP      │
│   (Claude)    │  MCP     │  Server Adapter   │  HTTP    │  Server          │
│               │          │                   │          │                  │
└───────────────┘          └───────────────────┘          └──────────────────┘
```

## Troubleshooting

If you encounter issues, check the following:

1. Ensure the Damien MCP Server is running and accessible
   ```bash
   curl http://localhost:8892/health
   ```

2. Verify the API key is correct
   ```bash
   curl -H "X-API-Key: your_api_key" http://localhost:8892/mcp/protected-test
   ```

3. Check that the tool definitions are being properly fetched from the Damien MCP Server
   ```bash
   curl -H "X-API-Key: your_api_key" http://localhost:8892/mcp/list_tools
   ```

4. Look for any errors in the adapter logs

### Common Issues

#### Module Resolution Errors

If you encounter module resolution errors, ensure that:
- You are using the appropriate import statements with `.js` extensions
- The tsconfig.json has `"moduleResolution": "NodeNext"` and `"module": "NodeNext"`
- The package.json has `"type": "module"`
- You are using the appropriate Node.js flags when running the server

## Status

See [INTEGRATION_STATUS.md](./INTEGRATION_STATUS.md) for the current status of the integration and checklist of completed items.

## References

- [Damien MCP Server](https://github.com/your-username/damien-mcp-server)
- [Smithery SDK](https://github.com/smithery-ai/sdk)
- [Model Context Protocol](https://github.com/modelcontextprotocol/typescript-sdk)