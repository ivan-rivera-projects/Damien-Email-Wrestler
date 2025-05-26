#!/bin/bash
# Restart the MCP server with our changes

# Stop the running server if it exists
pkill -f "uvicorn app.main:app --host 0.0.0.0 --port 8895"

# Change to the MCP server directory
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-mcp-server

# Start the server with increased logging
export DAMIEN_LOG_LEVEL=DEBUG
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8895 &

# Wait for server to start
sleep 3

echo "MCP Server restarted on port 8895"
echo "To test thread tools, run: python /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/test_thread_tools.py"
