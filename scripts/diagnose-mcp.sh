#!/bin/bash

echo "🔍 Damien MCP Server Diagnostics"
echo "================================="

# Check if Node.js is available
echo -n "✓ Node.js: "
node --version || echo "❌ Not found"

# Check if backend is running
echo -n "✓ Backend health: "
if curl -s -f http://localhost:8892/health > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

# Check if the scripts exist
echo -n "✓ claude-max-fix.js: "
if [ -f "/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter/claude-max-fix.js" ]; then
    echo "✅ Exists"
else
    echo "❌ Missing"
fi

# Test loading the Node modules
echo -n "✓ Node modules: "
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter
if node -e "require('@modelcontextprotocol/sdk/server/index.js')" 2>/dev/null; then
    echo "✅ Loaded"
else
    echo "❌ Failed to load"
fi

# Check npm modules
echo ""
echo "📦 Checking npm dependencies..."
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter
npm list @modelcontextprotocol/sdk node-fetch 2>/dev/null | grep -E "(@modelcontextprotocol/sdk|node-fetch)"

echo ""
echo "📋 Claude Desktop Config:"
cat "/Users/ivanrivera/Library/Application Support/Claude/claude_desktop_config.json" | python3 -c "import json, sys; config=json.load(sys.stdin); print(json.dumps(config.get('mcpServers', {}).get('damien_email_wrestler', {}), indent=2))"

echo ""
echo "💡 Test the MCP connection:"
echo "   node /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter/claude-max-fix.js"
