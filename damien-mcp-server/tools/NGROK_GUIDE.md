# Exposing Damien MCP Server with ngrok

This guide explains how to use ngrok to expose your locally running Damien MCP Server to the internet for integration with Claude.

## Prerequisites

1. Install ngrok: https://ngrok.com/download
2. Create a free ngrok account and get your authtoken
3. Have the Damien MCP Server running locally

## Steps

### 1. Configure ngrok

First-time setup only:
```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
```

### 2. Start the Damien MCP Server

In one terminal, start the Damien MCP Server:
```bash
cd /path/to/damien_mcp_server
poetry run uvicorn damien_mcp_server.main:app --host 0.0.0.0 --port 8892 --reload
```

Confirm it's running by visiting http://localhost:8892/health in your browser.

### 3. Start ngrok

In another terminal, start ngrok to expose port 8892:
```bash
ngrok http 8892
```

You should see output like:
```
Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.3.5
Region                        United States (us)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://a1b2-203-0-113-42.ngrok-free.app -> http://localhost:8892
```

### 4. Use the ngrok URL with Claude

The forwarding URL (e.g., `https://a1b2-203-0-113-42.ngrok-free.app`) is your public URL for the MCP server.

When configuring Claude, use:
- Endpoint URL: `https://a1b2-203-0-113-42.ngrok-free.app/mcp/execute_tool`
- API Key: Your Damien MCP Server API key (from the `.env` file)
- Tool schemas: The JSON from `tools/schemas/damien_all_tools.json`

### 5. Test the Connection

Before configuring Claude, you can test the connection by making a request to the health endpoint of your ngrok URL:
```bash
curl https://a1b2-203-0-113-42.ngrok-free.app/health
```

You should get a response like:
```json
{"status":"ok","message":"Damien MCP Server is healthy!"}
```

You can also test the protected endpoint (which requires authentication):
```bash
curl -H "X-API-Key: YOUR_API_KEY" https://a1b2-203-0-113-42.ngrok-free.app/mcp/protected-test
```

### 6. Monitor Requests

While ngrok is running, you can monitor HTTP traffic to your server at http://127.0.0.1:4040

This is extremely useful for debugging Claude's interactions with your MCP server.

## Notes

- Free ngrok sessions expire after a few hours and each session creates a new random URL
- For more persistent testing, consider a paid ngrok plan or deploying the server to a cloud provider
- Always protect your API key and be cautious about exposing your Gmail to the internet through this server
