# Damien Platform Environment Setup Guide
**Version**: 2.0.0 - CONSOLIDATED  
**Created**: 2025-01-12  
**Purpose**: Complete environment setup for all Damien Platform components  

---

## 📋 **Quick Start Checklist**

Before you begin, verify:
- [ ] **Python 3.11 or 3.12** installed (NOT 3.13+ due to dependency conflicts)
- [ ] **Poetry** installed (latest version)
- [ ] **Node.js 18+** installed (for Smithery adapter)
- [ ] **Git repository** cloned
- [ ] **Project access** to all components

---

## 🎯 **Overview: Damien Platform Components**

The Damien Platform consists of multiple interconnected components:
- **Damien CLI** (`/damien-cli/`) - Core Gmail management with AI intelligence
- **Damien MCP Server** (`/damien-mcp-server/`) - AI assistant integration
- **Damien Smithery Adapter** (`/damien-smithery-adapter/`) - Discovery service
- **Platform Scripts** (`/scripts/`) - Orchestration and utilities

---

## 🔧 **Step 1: System Prerequisites**

### **Python Version Requirements**
```bash
# Check your Python version
python --version
# Required: Python 3.11.x or 3.12.x (NOT 3.13+)

# Install Python 3.11 if needed:
# macOS with Homebrew:
brew install python@3.11

# Ubuntu/Debian:
sudo apt update && sudo apt install python3.11 python3.11-venv

# Verify installation
python3.11 --version
```

### **Poetry Installation**
```bash
# Install Poetry (official method)
curl -sSL https://install.python-poetry.org | python3 -

# Alternative: via pip
pip install poetry

# Verify Poetry installation
poetry --version

# Configure Poetry globally
poetry config virtualenvs.in-project true
```

### **Node.js Requirements** (for Smithery Adapter)
```bash
# Check Node.js version
node --version
# Required: Node.js 18+ 

# Install Node.js 18+ if needed:
# macOS: brew install node
# Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs
```

---

## 🔧 **Step 2: Platform Environment Configuration**

### **Initial Environment Setup**
```bash
# Navigate to platform root
cd damien-email-wrestler

# Copy example environment file
cp .env.example .env

# Generate secure API key
openssl rand -hex 32
```

### **Configure Environment Variables**
Edit the `.env` file with your values:
```bash
# Core API Configuration
DAMIEN_MCP_SERVER_API_KEY=your_generated_api_key_here
DAMIEN_MCP_SERVER_PORT=3001
DAMIEN_MCP_SERVER_HOST=localhost

# AWS Configuration (for DynamoDB)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Gmail API Configuration  
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./data/token.json

# Environment
NODE_ENV=development
PYTHONPATH=${PYTHONPATH}:./damien-cli
```

### **Sync Environment Across Components**
```bash
# Automatically sync environment variables to all components
./scripts/sync-env.sh

# Verify sync worked correctly
grep DAMIEN_MCP_SERVER_API_KEY .env damien-mcp-server/.env damien-smithery-adapter/.env
```

---

## 🔧 **Step 3: Damien CLI Setup**

### **CLI-Specific Setup**
```bash
# Navigate to CLI directory
cd damien-cli

# Configure Poetry for this project
poetry env use python3.11

# Clean install (removes any conflicts)
poetry env remove --all
poetry install

# Verify installation
poetry env info
# Should show Python 3.11.x/3.12.x and 100+ packages
```

### **Gmail API Setup**
```bash
# Follow the detailed Gmail API setup guide
cat docs/GMAIL_API_SETUP.md

# Place your credentials.json in the CLI root directory
# First run will prompt for OAuth authentication
poetry run damien login
```

### **Validate CLI Setup**
```bash
# Run environment validation script
poetry run python validate_environment.py

# Run privacy tests (should show 37/37 passing)
poetry run pytest tests/test_pii_detection.py -v

# Test basic CLI functionality
poetry run damien --help
```

---

## 🔧 **Step 4: MCP Server Setup**

### **MCP Server Dependencies**
```bash
# Navigate to MCP server directory
cd ../damien-mcp-server

# Install dependencies
poetry install

# Verify installation
poetry env info
```

### **DynamoDB Configuration**
```bash
# For local development, install DynamoDB Local
# Or configure AWS DynamoDB access in .env file

# Test MCP server
poetry run python -m damien_mcp_server.main --help
```

---

## 🔧 **Step 5: Smithery Adapter Setup**

### **Node.js Dependencies**
```bash
# Navigate to Smithery adapter directory
cd ../damien-smithery-adapter

# Install Node.js dependencies
npm install

# Verify installation
npm list --depth=0
```

---

## 🔧 **Step 6: Complete Platform Validation**

### **Start All Services**
```bash
# Return to platform root
cd ../

# Start all services using orchestration script
./scripts/start-all.sh

# Verify all services are running
./scripts/status-check.sh
```

### **Run Integration Tests**
```bash
# Test CLI functionality
cd damien-cli
poetry run python test_router_integration.py

# Test MCP server integration
cd ../damien-mcp-server
poetry run pytest tests/ -v

# Test end-to-end integration
cd ../
./scripts/test-integration.sh
```

---

## 🚨 **Common Issues & Troubleshooting**

### **"No such command" Errors**
**Problem**: Commands like `damien` not found  
**Solution**: Always use `poetry run` prefix
```bash
# Wrong: damien --help
# Correct: poetry run damien --help

# Or activate environment first:
poetry shell
damien --help
```

### **Dependency Conflicts**
**Problem**: Import errors, version conflicts  
**Solution**: Recreate environment
```bash
cd damien-cli
poetry env remove --all
poetry env use python3.11
poetry install
```

### **Authentication Issues Between Services**
**Problem**: API key mismatches  
**Solution**: Re-sync environment
```bash
# From platform root
./scripts/sync-env.sh

# Verify sync
grep DAMIEN_MCP_SERVER_API_KEY .env */**.env

# Restart services
./scripts/stop-all.sh && ./scripts/start-all.sh
```

### **Privacy Tests Not Passing 37/37**
**Problem**: Tests failing  
**Solution**: Debug step by step
```bash
cd damien-cli

# Run with verbose output
poetry run pytest tests/test_pii_detection.py -v --tb=short

# Check specific test
poetry run pytest tests/test_pii_detection.py::test_email_detection -v

# Verify ML dependencies
poetry run python -c "import torch, sentence_transformers; print('ML deps OK')"
```

### **PyTorch/ML Dependencies Issues**
**Problem**: ML imports failing  
**Solution**: Reinstall ML stack
```bash
cd damien-cli
poetry remove torch sentence-transformers
poetry add torch==2.1.0 --source pytorch-cpu
poetry add sentence-transformers==2.6.0
```

---

## ✅ **Environment Validation Checklist**

### **Platform Level**
- [ ] All components have synced environment variables
- [ ] API keys are consistent across services
- [ ] All services start without errors
- [ ] Integration tests pass

### **CLI Level**  
- [ ] Python 3.11.x/3.12.x confirmed
- [ ] Poetry environment created successfully
- [ ] **37/37 privacy tests passing** (critical milestone)
- [ ] Gmail API authentication working
- [ ] All imports working (no dependency conflicts)
- [ ] CLI commands working (with poetry run prefix)

### **MCP Server Level**
- [ ] DynamoDB connection working
- [ ] FastAPI server starts correctly  
- [ ] Authentication working
- [ ] MCP tools responding

### **Smithery Adapter Level**
- [ ] Node.js dependencies installed
- [ ] Smithery SDK integration working
- [ ] Service discovery functional

---

## 🎯 **Success Criteria**

### **Complete Setup Achieved When:**
✅ **All services start successfully** with `./scripts/start-all.sh`  
✅ **37/37 CLI privacy tests passing** (99.9% PII detection accuracy)  
✅ **No "No such command" errors** (proper Poetry usage)  
✅ **Environment variables synced** across all components  
✅ **Authentication working** between all services  
✅ **Integration tests passing** end-to-end  

### **Daily Development Commands**
```bash
# Platform orchestration
./scripts/start-all.sh          # Start all services
./scripts/stop-all.sh           # Stop all services  
./scripts/status-check.sh       # Check service status
./scripts/sync-env.sh           # Sync environment variables

# CLI development (from damien-cli/)
poetry run pytest tests/test_pii_detection.py    # Validate privacy (37/37)
poetry run python validate_environment.py       # Environment check
poetry run damien --help                        # Test CLI
poetry run python test_router_integration.py    # Test intelligence router

# Code quality (from any component)
poetry run black .             # Format code
poetry run flake8 .            # Lint code
poetry run pytest --cov .      # Test with coverage
```

---

## 📚 **Additional Resources**

### **Component-Specific Guides**
- **CLI Development**: `damien-cli/docs/development/DEVELOPMENT_SETUP.md`
- **Gmail API Setup**: `damien-cli/docs/GMAIL_API_SETUP.md`
- **MCP Server Deployment**: `damien-mcp-server/docs/DEPLOYMENT_GUIDE.md`
- **Smithery Integration**: `damien-smithery-adapter/docs/SETUP.md`

### **Architecture Documentation**
- **Platform Architecture**: `docs/ARCHITECTURE.md`
- **CLI Architecture**: `damien-cli/docs/CLI_ARCHITECTURE.md`
- **Phase 3 Status**: `docs/specifications/PHASE_3_MASTER.md`

### **Troubleshooting Resources**
- **Platform Troubleshooting**: `docs/guides/TROUBLESHOOTING.md`
- **Known Issues**: `CHANGELOG.md`
- **Development FAQ**: `docs/guides/DEVELOPER_FAQ.md`

---

## 🏆 **Environment Setup Success**

**Target Achievement**: When this guide is followed correctly, you should achieve:
- ✅ **Consistent environment** across all platform components
- ✅ **37/37 privacy tests passing** with 99.9% PII detection accuracy  
- ✅ **No dependency conflicts** or import errors
- ✅ **All services operational** and communicating correctly
- ✅ **Developer productivity** with clear development workflows
- ✅ **Production readiness** with proper configuration management

**Remember**: The foundation is solid with enterprise-grade privacy protection and intelligent routing systems. This environment setup enables building on that success with confidence! 🎯

---

*Last Updated: 2025-01-12 | Next Review: Before Phase 3 Week 5-6 implementation*
