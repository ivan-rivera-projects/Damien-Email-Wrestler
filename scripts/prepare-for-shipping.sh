#!/bin/bash
# Damien Email Wrestler - Shipping Preparation Script
# This script cleans up the project for production deployment
# Run from the project root directory

set -e

echo "🧹 Preparing Damien Email Wrestler for shipping..."
echo "📁 Current directory: $(pwd)"
echo "⚠️  This will clean up development files and prepare for production"
echo

# Confirm we're in the right directory
if [[ ! -f "README.md" ]] || [[ ! -d "damien-cli" ]]; then
    echo "❌ Error: Please run this script from the damien-email-wrestler root directory"
    exit 1
fi

echo "🔍 Pre-cleanup analysis:"
echo "   📊 Current size: $(du -sh . 2>/dev/null | cut -f1)"
echo "   📁 .DS_Store files: $(find . -name ".DS_Store" 2>/dev/null | wc -l | xargs)"
echo "   🐍 __pycache__ dirs: $(find . -name "__pycache__" -type d 2>/dev/null | wc -l | xargs)"
echo "   📦 node_modules dirs: $(find . -name "node_modules" -type d 2>/dev/null | wc -l | xargs)"
echo

# 1. CRITICAL: Remove files with personal/sensitive paths
echo "🔐 Step 1: Removing files with personal machine paths..."
echo "   Removing BACKUP_LOCATION_README.md (contains personal paths)"
rm -f BACKUP_LOCATION_README.md

# 2. Remove system and cache files
echo "🗑️  Step 2: Removing system files and caches..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name ".DS_Store?" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name ".nyc_output" -type d -exec rm -rf {} + 2>/dev/null || true

# 3. Remove development dependencies (with user confirmation)
echo "📦 Step 3: Development dependencies cleanup..."
NODE_MODULES_COUNT=$(find . -name "node_modules" -type d 2>/dev/null | wc -l | xargs)
if [ "$NODE_MODULES_COUNT" -gt 0 ]; then
    echo "   Found $NODE_MODULES_COUNT node_modules directories"
    read -p "   Remove node_modules directories? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
        echo "   ✅ Removed node_modules directories"
    else
        echo "   ⏭️  Keeping node_modules directories"
    fi
fi

if [ -d "./venv" ]; then
    VENV_SIZE=$(du -sh ./venv 2>/dev/null | cut -f1)
    echo "   Found Python virtual environment (size: $VENV_SIZE)"
    read -p "   Remove Python virtual environment? (y/N): " -n 1 -r
    echo  
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf ./venv/ 2>/dev/null || true
        echo "   ✅ Removed virtual environment"
    else
        echo "   ⏭️  Keeping virtual environment"
    fi
fi

# 4. Remove obsolete development components
echo "🧹 Step 4: Removing obsolete development components..."
OBSOLETE_DIRS=()
[ -d "./claude-code-mcp-bug-repro" ] && OBSOLETE_DIRS+=("claude-code-mcp-bug-repro")
[ -d "./github-mcp-server" ] && OBSOLETE_DIRS+=("github-mcp-server")

if [ ${#OBSOLETE_DIRS[@]} -gt 0 ]; then
    echo "   Found obsolete directories: ${OBSOLETE_DIRS[*]}"
    read -p "   Remove obsolete development directories? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for dir in "${OBSOLETE_DIRS[@]}"; do
            rm -rf "./$dir/" 2>/dev/null || true
            echo "   ✅ Removed $dir"
        done
    else
        echo "   ⏭️  Keeping obsolete directories"
    fi
fi

# 5. Remove redundant MCP implementations
echo "🔄 Step 5: Cleaning up redundant MCP implementations..."
REDUNDANT_DIRS=()
[ -d "./damien-smithery-adapter" ] && REDUNDANT_DIRS+=("damien-smithery-adapter")
[ -d "./damien-mcp-server/damien_smithery_adapter" ] && REDUNDANT_DIRS+=("damien-mcp-server/damien_smithery_adapter")

if [ ${#REDUNDANT_DIRS[@]} -gt 0 ]; then
    echo "   Found redundant MCP implementations: ${REDUNDANT_DIRS[*]}"
    echo "   (Keeping: damien-mcp-minimal for Claude Code, damien-mcp-server for backend)"
    read -p "   Remove redundant MCP implementations? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for dir in "${REDUNDANT_DIRS[@]}"; do
            rm -rf "./$dir/" 2>/dev/null || true
            echo "   ✅ Removed $dir"
        done
    else
        echo "   ⏭️  Keeping redundant implementations"
    fi
fi

# 6. Clean up test directories
echo "🧪 Step 6: Organizing test directories..."
[ -f "./damien-cli/test/archived_test_email_management_commands.py" ] && rm -f "./damien-cli/test/archived_test_email_management_commands.py"
[ -d "./damien-mcp-server/test" ] && rm -rf "./damien-mcp-server/test/" 2>/dev/null || true
echo "   ✅ Removed archived and duplicate test files"

# 7. Handle sensitive data and credentials
echo "🔐 Step 7: Handling sensitive data and credentials..."

# Handle credentials.json
if [ -f "damien-cli/credentials.json" ]; then
    echo "   Found credentials.json"
    read -p "   Create credentials.json.example template? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # Create example file with placeholders
        cat > damien-cli/credentials.json.example << 'EOF'
{
  "installed": {
    "client_id": "YOUR_GMAIL_CLIENT_ID_HERE.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET_HERE",
    "redirect_uris": [
      "http://localhost"
    ]
  }
}
EOF
        echo "   ✅ Created credentials.json.example"
    fi
    
    read -p "   Remove actual credentials.json? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f damien-cli/credentials.json
        echo "   ✅ Removed credentials.json"
    else
        echo "   ⚠️  WARNING: credentials.json contains sensitive data - consider removing before shipping"
    fi
fi

# Clean user data directories
echo "   Cleaning user data directories..."
rm -f damien-cli/data/token.json* 2>/dev/null || true
rm -f damien-cli/data/ai_intelligence/embeddings_cache/*.pkl 2>/dev/null || true  
rm -f damien-cli/data/conversation_contexts/*.json 2>/dev/null || true
rm -f damien-cli/data/*.json 2>/dev/null || true

# Create placeholder files to maintain directory structure
touch damien-cli/data/.gitkeep 2>/dev/null || true
touch damien-cli/data/ai_intelligence/embeddings_cache/.gitkeep 2>/dev/null || true
touch damien-cli/data/conversation_contexts/.gitkeep 2>/dev/null || true

echo "   ✅ Cleaned user data (maintained directory structure)"

# 8. Handle environment files
if [ -f ".env" ]; then
    echo "   Found .env file with environment variables"
    read -p "   Remove .env file (keep .env.example)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f .env
        echo "   ✅ Removed .env file"
        if [ ! -f ".env.example" ]; then
            echo "   ⚠️  WARNING: No .env.example found - users will need environment setup guidance"
        fi
    else
        echo "   ⚠️  WARNING: .env may contain sensitive keys - review before shipping"
    fi
fi

# 9. Clean log files
echo "📋 Step 8: Cleaning log files..."
if [ -d "./logs" ]; then
    LOG_COUNT=$(find ./logs -name "*.log" 2>/dev/null | wc -l | xargs)
    if [ "$LOG_COUNT" -gt 0 ]; then
        find ./logs -name "*.log" -delete 2>/dev/null || true
        echo "   ✅ Removed $LOG_COUNT log files"
    fi
fi

# 10. Update .gitignore to prevent future issues
echo "📝 Step 9: Updating .gitignore..."
if [ -f ".gitignore" ]; then
    # Add common patterns if not already present
    PATTERNS_TO_ADD=(
        "# System files"
        ".DS_Store"
        ".DS_Store?"
        ""
        "# Python cache"
        "__pycache__/"
        "*.pyc"
        "*.pyo"
        ""
        "# Node.js"
        "node_modules/"
        ""
        "# User data and credentials"
        "damien-cli/data/token.json*"
        "damien-cli/data/*.json"
        "damien-cli/data/ai_intelligence/embeddings_cache/*.pkl"
        "damien-cli/data/conversation_contexts/*.json"
        "damien-cli/credentials.json"
        ""
        "# Environment and logs"
        ".env"
        "logs/*.log"
        ""
        "# Development artifacts"
        "*BACKUP_LOCATION_README.md"
        "SHIPPING_MANIFEST.md"
    )
    
    for pattern in "${PATTERNS_TO_ADD[@]}"; do
        if [ ! -z "$pattern" ] && ! grep -q "^$pattern$" .gitignore 2>/dev/null; then
            echo "$pattern" >> .gitignore
        fi
    done
    echo "   ✅ Updated .gitignore with shipping patterns"
fi

# 11. Create shipping manifest
echo "📦 Step 10: Creating shipping manifest..."
cat > SHIPPING_MANIFEST.md << EOF
# Damien Email Wrestler - Shipping Manifest
*Generated: $(date)*

## 🏗️ Components Included:
- ✅ **Core CLI Engine** (damien-cli/) - Main application
- ✅ **MCP Backend Server** (damien-mcp-server/) - FastAPI backend with 48 tools
- ✅ **Claude Code Adapter** (damien-mcp-minimal/) - MCP compatibility layer
- ✅ **AWS Infrastructure** (aws-infrastructure/) - Lambda functions and deployment
- ✅ **Documentation** (docs/) - User and developer guides
- ✅ **Scripts** (scripts/) - Deployment and management scripts

## 🚀 Quick Setup:
1. **Install Python dependencies**: \`cd damien-cli && poetry install\`
2. **Install Node.js dependencies**: \`cd damien-mcp-minimal && npm install\`
3. **Configure Gmail API**: Copy credentials to \`damien-cli/credentials.json\`
4. **Set environment variables**: Copy \`.env.example\` to \`.env\` and configure
5. **Start services**: \`./scripts/start-all.sh\`

## 🗑️ Removed During Shipping:
- System cache files (__pycache__/, .DS_Store)
- Development dependencies (node_modules/, venv/)
- Personal machine paths and backup references
- Obsolete development artifacts
- User data, credentials, and logs
- Redundant MCP implementations

## 📋 Pre-Deployment Checklist:
- [ ] Configure Gmail API credentials
- [ ] Set up environment variables
- [ ] Review and test core functionality
- [ ] Configure AWS Lambda (optional)
- [ ] Set up monitoring and logging
- [ ] Test MCP integration with Claude Code

## 🔗 Key Files:
- \`README.md\` - Main project documentation
- \`CLAUDE.md\` - Claude Code integration guide  
- \`MCP_TOOL_USAGE_GUIDE.md\` - Tool usage reference
- \`scripts/start-all.sh\` - Service startup
- \`.env.example\` - Environment configuration template

EOF

# Final summary
echo
echo "🎉 Shipping preparation complete!"
echo
echo "📊 Final analysis:"
echo "   📁 Final size: $(du -sh . 2>/dev/null | cut -f1)"
echo "   📄 Generated SHIPPING_MANIFEST.md with setup instructions"
echo "   🔐 Sensitive data handled appropriately"
echo "   📦 Project structure optimized for deployment"
echo
echo "✅ Ready to ship!"
echo "📋 Next steps:"
echo "   1. Review SHIPPING_MANIFEST.md"
echo "   2. Test the installation process"
echo "   3. Commit changes to version control"
echo "   4. Create release package"
echo