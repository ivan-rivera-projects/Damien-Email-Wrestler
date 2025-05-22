# 🚀 Damien Email Wrestler - Startup Scripts

This directory contains scripts to help you quickly start and test Damien Email Wrestler.

## 📜 Available Scripts

### `start.sh` - Quick Start Script
**The fastest way to get Damien running!**

```bash
# Make executable and run
chmod +x scripts/start.sh
./scripts/start.sh
```

**What it does:**
- ✅ Checks for Docker and Docker Compose
- ✅ Verifies Gmail credentials exist
- ✅ Creates `.env` from template if needed
- ✅ Handles Gmail authentication
- ✅ Starts all services with Docker Compose
- ✅ Waits for services to be ready
- ✅ Shows you next steps

### `setup.sh` - Initial Setup
**Prepares your environment for first run**

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**What it does:**
- Creates necessary directories
- Copies environment templates
- Generates secure API keys
- Installs dependencies
- Guides you through initial configuration

### `test.sh` - Health Check & Testing
**Verifies everything is working correctly**

```bash
chmod +x scripts/test.sh
./scripts/test.sh
```

**What it does:**
- Checks configuration files
- Tests service health endpoints
- Verifies tool discovery
- Runs basic functionality tests
- Shows detailed test results

## 🏃‍♂️ Quick Start Workflow

For a brand new setup:

```bash
# 1. Clone the repository
git clone https://github.com/ivan-rivera-projects/Damien-Email-Wrestler.git
cd Damien-Email-Wrestler

# 2. Run initial setup
./scripts/setup.sh

# 3. Place your Gmail credentials
# Follow docs/GMAIL_API_SETUP.md to get credentials.json

# 4. Edit configuration
nano .env  # Add your API keys

# 5. Start everything
./scripts/start.sh

# 6. Test the installation
./scripts/test.sh
```

## 🔧 Manual Development Setup

If you prefer manual control or are developing:

### Terminal 1: Damien MCP Server
```bash
cd damien-mcp-server
poetry install
poetry run uvicorn app.main:app --reload --port 8892
```

### Terminal 2: Smithery Adapter
```bash
cd damien-smithery-adapter
npm install
npm run build
npm start
```

### Terminal 3: Testing
```bash
# Test health
curl http://localhost:8892/health
curl http://localhost:8081/health

# Test tools
curl http://localhost:8081/tools
```

## 🐳 Docker Commands Reference

### Start Services
```bash
# Start in background
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up damien-mcp-server
```

### Monitor Services
```bash
# View logs
docker-compose logs -f

# Check status
docker-compose ps

# View specific service logs
docker-compose logs -f damien-smithery-adapter
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart specific service
docker-compose restart damien-mcp-server
```

## 🔍 Troubleshooting Scripts

### Permission Issues
```bash
# Fix script permissions
chmod +x scripts/*.sh
```

### Port Conflicts
```bash
# Check what's using ports 8892 or 8081
lsof -i :8892
lsof -i :8081

# Kill processes if needed
sudo kill -9 $(lsof -t -i:8892)
```

### Service Not Starting
```bash
# Check Docker status
docker --version
docker-compose --version

# View detailed logs
docker-compose logs --tail=50 damien-mcp-server
docker-compose logs --tail=50 damien-smithery-adapter
```

### Gmail Authentication Issues
```bash
# Reset Gmail authentication
rm damien-cli/data/token.json
cd damien-cli
poetry run damien login
```

## 📊 Environment Variables Reference

The scripts check for these key environment variables:

```env
# Required
DAMIEN_MCP_SERVER_API_KEY=your-64-character-api-key

# Gmail (auto-detected paths)
DAMIEN_GMAIL_TOKEN_JSON_PATH=./damien-cli/data/token.json
DAMIEN_GMAIL_CREDENTIALS_JSON_PATH=./credentials.json

# Optional AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Optional Smithery
SMITHERY_BEARER_AUTH=your-smithery-token
```

## ⚡ Pro Tips

### Speed up development
```bash
# Use nodemon for auto-restart
cd damien-smithery-adapter
npm install -g nodemon
nodemon dist/index.js

# Use uvicorn with reload
cd damien-mcp-server
poetry run uvicorn app.main:app --reload --port 8892
```

### Quick testing commands
```bash
# Test email listing
curl -X POST http://localhost:8081/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "damien_list_emails", "params": {"max_results": 3}, "session_id": "test"}'

# Test health checks in one command
curl -s http://localhost:8892/health && curl -s http://localhost:8081/health
```

### Debugging with logs
```bash
# Follow all logs
docker-compose logs -f

# Filter specific service logs
docker-compose logs -f damien-mcp-server | grep ERROR

# Get last 100 lines
docker-compose logs --tail=100
```

---

**Need help?** Check the main README.md or create an issue on GitHub! 🤼‍♂️
