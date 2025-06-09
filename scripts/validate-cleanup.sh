#!/bin/bash
# 🔍 Damien Email Wrestler - Post-Cleanup Validation Script
# This script validates that cleanup didn't break core functionality
# Run after cleanup: ./scripts/validate-cleanup.sh

set -e  # Exit on any error

PROJECT_ROOT="/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Damien Email Wrestler Post-Cleanup Validation${NC}"
echo -e "${BLUE}================================================${NC}"

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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

VALIDATION_ERRORS=0

# Function to check if a file exists
check_file() {
    local file="$1"
    local description="$2"
    
    if [[ -f "$file" ]]; then
        print_status "$description: $file"
        return 0
    else
        print_error "$description missing: $file"
        ((VALIDATION_ERRORS++))
        return 1
    fi
}

# Function to check if a directory exists
check_directory() {
    local dir="$1"
    local description="$2"
    
    if [[ -d "$dir" ]]; then
        print_status "$description: $dir"
        return 0
    else
        print_error "$description missing: $dir"
        ((VALIDATION_ERRORS++))
        return 1
    fi
}

# Validate we're in the right directory
if [[ ! -f "CLAUDE.md" || ! -d "damien-cli" ]]; then
    print_error "This script must be run from the Damien Email Wrestler project root"
    exit 1
fi

echo -e "\n${BLUE}Phase 1: Core Application Files${NC}"

# Check essential core files
check_file "README.md" "Main README"
check_file "CLAUDE.md" "Claude integration guide"
check_file "ENVIRONMENT_SETUP.md" "Environment setup guide"
check_file "DAMIEN_TOOL_USAGE_GUIDE.md" "Tool usage guide"

# Check core directories
check_directory "damien-cli" "CLI application directory"
check_directory "damien-mcp-server" "MCP server directory"
check_directory "damien-mcp-minimal" "Minimal MCP directory"
check_directory "aws-infrastructure" "AWS infrastructure directory"
check_directory "scripts" "Scripts directory"

echo -e "\n${BLUE}Phase 2: Damien CLI Core Files${NC}"

# Check CLI essential files
check_file "damien-cli/pyproject.toml" "CLI project configuration"
check_file "damien-cli/cli_entry.py" "CLI entry point"
check_directory "damien-cli/damien_cli" "CLI source code"
check_directory "damien-cli/tests" "CLI tests directory"

# Check CLI core modules
check_directory "damien-cli/damien_cli/core" "CLI core modules"
check_directory "damien-cli/damien_cli/features" "CLI features"
check_directory "damien-cli/damien_cli/core_api" "CLI core API"

echo -e "\n${BLUE}Phase 3: MCP Server Core Files${NC}"

# Check MCP server files
check_file "damien-mcp-server/pyproject.toml" "MCP server project config"
check_file "damien-mcp-server/app/main.py" "MCP server main app"
check_directory "damien-mcp-server/app/tools" "MCP server tools"
check_directory "damien-mcp-server/app/services" "MCP server services"
check_directory "damien-mcp-server/tests" "MCP server tests"

echo -e "\n${BLUE}Phase 4: MCP Minimal Core Files${NC}"

# Check minimal MCP files
check_file "damien-mcp-minimal/package.json" "Minimal MCP package config"
check_file "damien-mcp-minimal/server.js" "Minimal MCP server"
check_directory "damien-mcp-minimal/core" "Minimal MCP core"
check_directory "damien-mcp-minimal/tests" "Minimal MCP tests"

echo -e "\n${BLUE}Phase 5: Documentation Structure${NC}"

# Check documentation organization
check_directory "docs" "Documentation directory"
check_file "docs/README.md" "Documentation index"

# Check documentation subdirectories (created by cleanup)
check_directory "docs/deployment" "Deployment documentation"
check_directory "docs/testing" "Testing documentation"
check_directory "docs/troubleshooting" "Troubleshooting documentation"
check_directory "docs/operations" "Operations documentation"

# Check moved documentation files
check_file "docs/deployment/AWS_LAMBDA_SETUP_GUIDE.md" "AWS setup guide"
check_file "docs/testing/COMPREHENSIVE_100_EMAIL_TEST_REPORT.md" "Test report"
check_file "docs/operations/SECURITY_CHECKLIST.md" "Security checklist"

echo -e "\n${BLUE}Phase 6: Archive Directory Preservation${NC}"

# Ensure archive directory was preserved
check_directory "archive" "Archive directory (historical docs)"
check_directory "archive/implementation-logs" "Implementation logs"
check_directory "archive/planning-docs" "Planning documents"
check_directory "archive/status-tracking" "Status tracking"

echo -e "\n${BLUE}Phase 7: Test Organization${NC}"

# Check test structure
check_directory "damien-cli/tests/integration" "CLI integration tests"
check_directory "damien-cli/tests/components" "CLI component tests"
check_directory "damien-cli/tests/utilities" "CLI utility tests"
check_directory "tests" "Project tests directory"
check_file "damien-cli/tests/README.md" "CLI test documentation"

echo -e "\n${BLUE}Phase 8: Essential Token/Config Files${NC}"

# Check essential authentication files
if [[ -f "damien-cli/data/token.json" ]]; then
    print_status "Gmail token preserved: damien-cli/data/token.json"
else
    print_warning "Gmail token not found (may need re-authentication)"
fi

# Check environment template
if [[ -f "scripts/env-template.sh.example" ]]; then
    print_status "Environment template preserved"
fi

echo -e "\n${BLUE}Phase 9: Service Management Scripts${NC}"

# Check essential scripts
check_file "scripts/start-all.sh" "Start all services script"
check_file "scripts/stop-all.sh" "Stop all services script"
check_file "scripts/status.sh" "Status check script"

echo -e "\n${BLUE}Phase 10: Files That Should Be Gone${NC}"

# Check that scattered test files were removed
REMOVED_FILES=(
    "test_mcp_parity.py"
    "test_ai_tools.py"
    "ai_workflow_demo.py"
    "test_output.json"
    "comprehensive_test_results.json"
    "SESSION_SUMMARY_ENTERPRISE_PIPELINE.md"
)

for file in "${REMOVED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        print_warning "File should have been removed: $file"
    else
        print_status "Confirmed removed: $file"
    fi
done

echo -e "\n${BLUE}Phase 11: Functional Validation${NC}"

# Test basic CLI imports
if cd damien-cli && python -c "import damien_cli; print('CLI imports successful')" 2>/dev/null; then
    print_status "CLI imports working"
    cd ..
else
    print_error "CLI imports failing"
    ((VALIDATION_ERRORS++))
    cd ..
fi

# Check if MCP server can start (dry run)
if python -c "
import sys
sys.path.append('damien-mcp-server')
try:
    from app.main import app
    print('MCP server imports successful')
except Exception as e:
    print(f'MCP server import error: {e}')
    sys.exit(1)
" 2>/dev/null; then
    print_status "MCP server imports working"
else
    print_error "MCP server imports failing"
    ((VALIDATION_ERRORS++))
fi

# Check Node.js dependencies for minimal MCP
if cd damien-mcp-minimal && npm list --depth=0 > /dev/null 2>&1; then
    print_status "Minimal MCP dependencies intact"
    cd ..
else
    print_warning "Minimal MCP may need npm install"
    cd ..
fi

echo -e "\n${BLUE}Phase 12: Git Status Check${NC}"

# Check git status
if git status > /dev/null 2>&1; then
    CHANGED_FILES=$(git status --porcelain | wc -l | tr -d ' ')
    print_info "Git tracking $CHANGED_FILES changed files"
    
    # Show summary of changes
    if [[ $CHANGED_FILES -gt 0 ]]; then
        echo -e "${YELLOW}Changes detected:${NC}"
        git status --porcelain | head -10
        if [[ $CHANGED_FILES -gt 10 ]]; then
            echo "... and $((CHANGED_FILES - 10)) more files"
        fi
    fi
else
    print_warning "Git status check failed"
fi

# Final validation summary
echo -e "\n${GREEN}🎉 Validation Complete!${NC}"
echo -e "${BLUE}===============================================${NC}"

if [[ $VALIDATION_ERRORS -eq 0 ]]; then
    print_status "All core functionality validated successfully"
    print_status "Codebase structure is clean and intact"
    print_status "Ready for development and testing"
    
    echo -e "\n${GREEN}✅ VALIDATION PASSED${NC}"
    echo -e "\n${YELLOW}Recommended Next Steps:${NC}"
    echo "1. Start services: ./scripts/start-all.sh"
    echo "2. Run basic tests: cd damien-cli && pytest tests/"
    echo "3. Commit changes: git add . && git commit -m 'feat: Clean up codebase'"
    
    exit 0
else
    print_error "Found $VALIDATION_ERRORS validation errors"
    print_error "Please review the errors above before proceeding"
    
    echo -e "\n${RED}❌ VALIDATION FAILED${NC}"
    echo -e "\n${YELLOW}Troubleshooting:${NC}"
    echo "1. Check that cleanup scripts ran successfully"
    echo "2. Verify all required files are present"
    echo "3. Run: ./scripts/start-all.sh to test services"
    
    exit 1
fi