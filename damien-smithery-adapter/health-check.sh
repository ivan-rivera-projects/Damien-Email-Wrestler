#!/bin/bash

echo "🔍 Damien MCP Health Check"
echo "========================="

# Check if Damien MCP Server is running
echo -n "Damien MCP Server (localhost:8892): "
if curl -s http://localhost:8892/health > /dev/null; then
    echo "✅ Running"
else
    echo "❌ Not responding"
    exit 1
fi

# Check if API key is correct
echo -n "API Key validation: "
API_KEY="7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
if curl -s -H "X-API-Key: $API_KEY" http://localhost:8892/mcp/tool-usage-policy > /dev/null; then
    echo "✅ Valid"
else
    echo "❌ Invalid"
    exit 1
fi

# Check if TypeScript is compiled
echo -n "TypeScript compilation: "
if [ -f "/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter/dist/stdioServer.js" ]; then
    echo "✅ Compiled"
else
    echo "❌ Missing dist files"
    exit 1
fi

echo "✅ All checks passed! Ready for Claude Desktop integration."
