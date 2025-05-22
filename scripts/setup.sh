#!/bin/bash

# Damien Email Wrestler - Simple Setup Script
set -e

echo "🤼‍♂️ Damien Email Wrestler Setup"
echo "================================="

# Create directories
mkdir -p data rules logs backups
mkdir -p damien-cli/data damien-mcp-server/data

echo "✓ Created directories"

# Setup environment
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
else
    echo "⚠ .env file already exists"
fi

# Generate API key if needed
if command -v openssl >/dev/null 2>&1; then
    if grep -q "your-secure-32-character-api-key-here" .env; then
        api_key=$(openssl rand -hex 32)
        sed -i.bak "s/your-secure-32-character-api-key-here/$api_key/" .env
        echo "✓ Generated secure API key"
    fi
fi

# Check for credentials
if [ ! -f credentials.json ]; then
    echo "❌ credentials.json not found"
    echo "Please place your Gmail API credentials file as 'credentials.json' in the project root"
    echo "See README.md for detailed setup instructions"
    exit 1
fi

echo "✓ Gmail credentials found"

# Install dependencies
echo "Installing dependencies..."

if [ -d "damien-cli" ] && [ -f "damien-cli/pyproject.toml" ]; then
    cd damien-cli && poetry install && cd ..
    echo "✓ Damien CLI dependencies installed"
fi

if [ -d "damien-mcp-server" ] && [ -f "damien-mcp-server/pyproject.toml" ]; then
    cd damien-mcp-server && poetry install && cd ..
    echo "✓ Damien MCP Server dependencies installed"
fi

if [ -d "damien-smithery-adapter" ] && [ -f "damien-smithery-adapter/package.json" ]; then
    cd damien-smithery-adapter && npm install && cd ..
    echo "✓ Smithery Adapter dependencies installed"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Authenticate with Gmail: cd damien-cli && poetry run damien login"
echo "2. Start services: docker-compose up -d"
echo "3. Test: curl http://localhost:8081/health"
echo "4. Register with Smithery: cd damien-smithery-adapter && npx @smithery/cli register --manual"
