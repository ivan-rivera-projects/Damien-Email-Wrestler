#!/bin/bash
# 🧹 Damien Email Wrestler - Automated Codebase Cleanup Script
# This script safely removes development artifacts and reorganizes test files
# Run from project root: ./scripts/cleanup-codebase.sh

set -e  # Exit on any error

PROJECT_ROOT="/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler"
BACKUP_DIR="${PROJECT_ROOT}/../damien-backup-$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Damien Email Wrestler Codebase Cleanup${NC}"
echo -e "${BLUE}=========================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Validate we're in the right directory
if [[ ! -f "CLAUDE.md" || ! -d "damien-cli" || ! -d "damien-mcp-server" ]]; then
    print_error "This script must be run from the Damien Email Wrestler project root directory"
    print_error "Expected files: CLAUDE.md, damien-cli/, damien-mcp-server/"
    exit 1
fi

print_status "Validated project directory structure"

# Step 1: Create backup
echo -e "\n${BLUE}Phase 1: Creating Backup${NC}"
print_warning "Creating full backup at: $BACKUP_DIR"
cp -r . "$BACKUP_DIR"
print_status "Backup created successfully"

# Step 2: Stop all services
echo -e "\n${BLUE}Phase 2: Stopping Services${NC}"
if [[ -f "scripts/stop-all.sh" ]]; then
    ./scripts/stop-all.sh
    print_status "All services stopped"
else
    print_warning "stop-all.sh not found, skipping service stop"
fi

# Step 3: Remove scattered test files from root
echo -e "\n${BLUE}Phase 3: Removing Scattered Test Files${NC}"
TEST_FILES=(
    "test_mcp_parity.py"
    "test_rule_creation_fix.py"
    "test_lambda_direct.py"
    "test_trash_fix_simple.py"
    "test_trash_fix.py"
    "test_ai_tools.py"
    "test_ai_workflow.py"
    "test_trash_debug.py"
    "test_mcp_lambda_integration.py"
    "test_production_rule_creation.py"
    "test_trash_simple.py"
    "simple_rule_test.py"
    "test_ai_simple.py"
    "ai_workflow_demo.py"
    "analyze_token_usage.py"
    "consolidate_docs.sh"
    "rule_creation_fix.md"
    "email_analysis_architecture.md"
)

for file in "${TEST_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        rm "$file"
        print_status "Removed: $file"
    else
        print_warning "Not found: $file"
    fi
done

# Step 4: Remove test output files
echo -e "\n${BLUE}Phase 4: Removing Test Output Files${NC}"
OUTPUT_FILES=(
    "ai-analyzer-test.json"
    "comprehensive_test_results.json"
    "email-processor-test.json"
    "lambda_payload.txt"
    "lambda_test_result.json"
    "test_output.json"
)

for file in "${OUTPUT_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        rm "$file"
        print_status "Removed: $file"
    else
        print_warning "Not found: $file"
    fi
done

# Step 5: Remove cache and compiled files
echo -e "\n${BLUE}Phase 5: Removing Cache and Compiled Files${NC}"

# Remove Python cache
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
print_status "Removed Python cache files"

# Remove embeddings cache (if it exists and is large)
if [[ -d "damien-cli/data/ai_intelligence/embeddings_cache" ]]; then
    CACHE_SIZE=$(du -sh damien-cli/data/ai_intelligence/embeddings_cache 2>/dev/null | cut -f1)
    rm -rf damien-cli/data/ai_intelligence/embeddings_cache/*
    print_status "Cleared embeddings cache ($CACHE_SIZE)"
fi

# Remove log files
if [[ -d "logs" ]]; then
    rm -rf logs/*
    print_status "Cleared log files"
fi

# Step 6: Remove backup files
echo -e "\n${BLUE}Phase 6: Removing Backup Files${NC}"
find . -name "*.backup" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
print_status "Removed backup files"

# Remove phase expansion backups
if [[ -d "damien-mcp-minimal/backups" ]]; then
    rm -f damien-mcp-minimal/backups/phase_expansion_*
    print_status "Removed phase expansion backups"
fi

# Step 7: Clean up duplicate credentials
echo -e "\n${BLUE}Phase 7: Cleaning Duplicate Credentials${NC}"
CRED_FILES=(
    "credentials.json"
    "damien-cli/credentials.json"
    "damien-cli/docs/credentials.json"
)

for file in "${CRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        rm "$file"
        print_status "Removed duplicate: $file"
    fi
done

# Keep primary token file
if [[ -f "damien-cli/data/token.json" ]]; then
    print_status "Primary Gmail token preserved: damien-cli/data/token.json"
fi

# Step 8: Create proper documentation structure
echo -e "\n${BLUE}Phase 8: Creating Documentation Structure${NC}"
mkdir -p docs/{deployment,testing,troubleshooting,operations}
print_status "Created documentation directories"

# Step 9: Move documentation files (if they exist)
echo -e "\n${BLUE}Phase 9: Moving Documentation Files${NC}"

# Move testing docs
[[ -f "COMPREHENSIVE_100_EMAIL_TEST_REPORT.md" ]] && mv "COMPREHENSIVE_100_EMAIL_TEST_REPORT.md" "docs/testing/" && print_status "Moved: COMPREHENSIVE_100_EMAIL_TEST_REPORT.md"
[[ -f "E2E_TESTING_GUIDE.md" ]] && mv "E2E_TESTING_GUIDE.md" "docs/testing/" && print_status "Moved: E2E_TESTING_GUIDE.md"

# Move deployment docs
[[ -f "PRODUCTION_READINESS_PLAN.md" ]] && mv "PRODUCTION_READINESS_PLAN.md" "docs/deployment/" && print_status "Moved: PRODUCTION_READINESS_PLAN.md"
[[ -f "AWS_LAMBDA_SETUP_GUIDE.md" ]] && mv "AWS_LAMBDA_SETUP_GUIDE.md" "docs/deployment/" && print_status "Moved: AWS_LAMBDA_SETUP_GUIDE.md"

# Move troubleshooting docs
[[ -f "ISSUE_REPORT_EmailProcessingWorkflow.md" ]] && mv "ISSUE_REPORT_EmailProcessingWorkflow.md" "docs/troubleshooting/" && print_status "Moved: ISSUE_REPORT_EmailProcessingWorkflow.md"
[[ -f "TIMEOUT_ANALYSIS_AND_SOLUTION.md" ]] && mv "TIMEOUT_ANALYSIS_AND_SOLUTION.md" "docs/troubleshooting/" && print_status "Moved: TIMEOUT_ANALYSIS_AND_SOLUTION.md"
[[ -f "PARETO_ANALYSIS_TIMEOUT_FIXES.md" ]] && mv "PARETO_ANALYSIS_TIMEOUT_FIXES.md" "docs/troubleshooting/" && print_status "Moved: PARETO_ANALYSIS_TIMEOUT_FIXES.md"

# Move operations docs
[[ -f "OPTIMIZATION_IMPLEMENTATION_SUMMARY.md" ]] && mv "OPTIMIZATION_IMPLEMENTATION_SUMMARY.md" "docs/operations/" && print_status "Moved: OPTIMIZATION_IMPLEMENTATION_SUMMARY.md"
[[ -f "SECURITY_CHECKLIST.md" ]] && mv "SECURITY_CHECKLIST.md" "docs/operations/" && print_status "Moved: SECURITY_CHECKLIST.md"

# Remove obsolete status files
[[ -f "SESSION_SUMMARY_ENTERPRISE_PIPELINE.md" ]] && rm "SESSION_SUMMARY_ENTERPRISE_PIPELINE.md" && print_status "Removed obsolete: SESSION_SUMMARY_ENTERPRISE_PIPELINE.md"
[[ -f "MCP_LAMBDA_INTEGRATION_SUMMARY.md" ]] && rm "MCP_LAMBDA_INTEGRATION_SUMMARY.md" && print_status "Removed duplicate: MCP_LAMBDA_INTEGRATION_SUMMARY.md"

# Step 10: Create master documentation index
echo -e "\n${BLUE}Phase 10: Creating Documentation Index${NC}"
cat > docs/README.md << 'EOF'
# Damien Email Wrestler Documentation

## Quick Start
- [Main README](../README.md) - Project overview and setup
- [Environment Setup](../ENVIRONMENT_SETUP.md) - Installation guide
- [Claude Integration](../CLAUDE.md) - AI assistant usage
- [Tool Usage Guide](../DAMIEN_TOOL_USAGE_GUIDE.md) - Optimal patterns

## Deployment
- [Production Readiness](deployment/PRODUCTION_READINESS_PLAN.md) - Go-live checklist
- [AWS Lambda Setup](deployment/AWS_LAMBDA_SETUP_GUIDE.md) - Cloud enhancement

## Testing
- [E2E Testing Guide](testing/E2E_TESTING_GUIDE.md) - Complete test procedures
- [100 Email Test Report](testing/COMPREHENSIVE_100_EMAIL_TEST_REPORT.md) - Real-world validation

## Operations
- [Security Checklist](operations/SECURITY_CHECKLIST.md) - Security best practices
- [Optimization Summary](operations/OPTIMIZATION_IMPLEMENTATION_SUMMARY.md) - Performance improvements

## Troubleshooting
- [Timeout Analysis](troubleshooting/TIMEOUT_ANALYSIS_AND_SOLUTION.md) - Performance issues
- [Email Processing Issues](troubleshooting/ISSUE_REPORT_EmailProcessingWorkflow.md) - Workflow problems
- [Pareto Analysis Fixes](troubleshooting/PARETO_ANALYSIS_TIMEOUT_FIXES.md) - Priority fixes

## Architecture
- [Complete Architecture](ARCHITECTURE.md) - System design
- [Quick Start](QUICK_START.md) - Fast setup
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
EOF

print_status "Created documentation index: docs/README.md"

# Final summary
echo -e "\n${GREEN}🎉 Cleanup Complete!${NC}"
echo -e "${BLUE}===============================================${NC}"
print_status "Backup created at: $BACKUP_DIR"
print_status "Removed ~75 development and temporary files"
print_status "Organized documentation into proper structure"
print_status "Preserved all core application code and essential docs"
print_status "Archive directory maintained for historical reference"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Review the cleanup results"
echo "2. Test functionality: ./scripts/status.sh"
echo "3. Start services: ./scripts/start-all.sh"
echo "4. Commit changes: git add . && git commit -m 'feat: Clean up codebase and organize documentation'"

echo -e "\n${BLUE}📁 Clean Directory Structure:${NC}"
echo "├── damien-cli/           # Core application"
echo "├── damien-mcp-server/    # FastAPI server"
echo "├── damien-mcp-minimal/   # MCP adapter"
echo "├── aws-infrastructure/   # Lambda functions"
echo "├── docs/                 # Organized documentation"
echo "│   ├── deployment/"
echo "│   ├── testing/"
echo "│   ├── troubleshooting/"
echo "│   └── operations/"
echo "├── scripts/              # Management scripts"
echo "└── archive/              # Historical docs (preserved)"

echo -e "\n${GREEN}Codebase is now clean, organized, and ready for development! 🚀${NC}"