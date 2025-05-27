# Damien Platform Quick Start Guide

## Prerequisites

- Python 3.13+ with Poetry
- Node.js 18+ with npm
- Docker and Docker Compose
- Gmail account with API access
- Google Cloud Project for Gmail API credentials

## One-Command Setup (Recommended)

```bash
git clone https://github.com/your-org/damien-email-wrestler.git
cd damien-email-wrestler
./scripts/start-all.sh
```

## Manual Setup

### 1. Gmail API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download and rename to `credentials.json`
6. Place in project root

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Install Dependencies
```bash
# Damien CLI
cd damien-cli
poetry install

# MCP Server
cd ../damien-mcp-server
poetry install

# Smithery Adapter
cd ../damien-smithery-adapter
npm install
```

### 4. Start Services
```bash
# Start MCP Server
cd damien-mcp-server
poetry run uvicorn app.main:app --port 8892 &

# Start Smithery Adapter
cd ../damien-smithery-adapter
npm run serve &
```

### 5. Authenticate with Gmail
```bash
cd damien-cli
poetry run damien login
```

### 6. Test Installation
```bash
./scripts/test.sh
```

## Verification

- MCP Server: `curl http://localhost:8892/health`
- Smithery Adapter: `curl http://localhost:8081/health`
- All tools: `curl http://localhost:8081/tools`

## Next Steps

- See [User Guide](../damien-cli/docs/USER_GUIDE.md) for CLI usage
- See [MCP Tools Reference](api/MCP_TOOLS_REFERENCE.md) for AI integration
- See [Troubleshooting](TROUBLESHOOTING.md) for common issues
