#!/bin/bash
# 🚀 Damien Email Wrestler - Master Cleanup Script
# This script orchestrates the complete codebase cleanup process
# Run from project root: ./scripts/master-cleanup.sh

set -e  # Exit on any error

PROJECT_ROOT="/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}🚀 Damien Email Wrestler - Master Cleanup${NC}"
echo -e "${BOLD}${BLUE}=========================================${NC}"

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

print_step() {
    echo -e "\n${BOLD}${BLUE}$1${NC}"
}

# Validate we're in the right directory
if [[ ! -f "CLAUDE.md" || ! -d "damien-cli" || ! -d "damien-mcp-server" ]]; then
    print_error "This script must be run from the Damien Email Wrestler project root directory"
    print_error "Expected: CLAUDE.md, damien-cli/, damien-mcp-server/ directories"
    exit 1
fi

print_status "Validated project directory structure"

# Check if required scripts exist
REQUIRED_SCRIPTS=(
    "scripts/cleanup-codebase.sh"
    "scripts/reorganize-tests.sh"
    "scripts/validate-cleanup.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ ! -f "$script" ]]; then
        print_error "Required script missing: $script"
        exit 1
    fi
    
    if [[ ! -x "$script" ]]; then
        chmod +x "$script"
        print_status "Made executable: $script"
    fi
done

# Pre-cleanup information
print_step "📊 Pre-Cleanup Analysis"

# Count current files
TOTAL_FILES=$(find . -type f ! -path "./.git/*" ! -path "./node_modules/*" ! -path "./__pycache__/*" | wc -l | tr -d ' ')
TOTAL_DIRS=$(find . -type d ! -path "./.git/*" ! -path "./node_modules/*" ! -path "./__pycache__/*" | wc -l | tr -d ' ')
MD_FILES=$(find . -name "*.md" ! -path "./.git/*" | wc -l | tr -d ' ')
PY_FILES=$(find . -name "*.py" ! -path "./.git/*" ! -path "./venv/*" ! -path "./__pycache__/*" | wc -l | tr -d ' ')
TEST_FILES=$(find . -name "test_*.py" ! -path "./.git/*" ! -path "./*/tests/*" | wc -l | tr -d ' ')

print_info "Current codebase statistics:"
echo "  📁 Total files: $TOTAL_FILES"
echo "  📁 Total directories: $TOTAL_DIRS"
echo "  📄 Markdown files: $MD_FILES"
echo "  🐍 Python files: $PY_FILES"
echo "  🧪 Scattered test files: $TEST_FILES"

# Get current disk usage
if command -v du &> /dev/null; then
    CURRENT_SIZE=$(du -sh . 2>/dev/null | cut -f1)
    print_info "Current directory size: $CURRENT_SIZE"
fi

# Check git status
GIT_STATUS=$(git status --porcelain | wc -l | tr -d ' ')
if [[ $GIT_STATUS -eq 0 ]]; then
    print_status "Git working directory is clean"
else
    print_warning "Git has $GIT_STATUS uncommitted changes"
    echo -e "${YELLOW}Consider committing current changes before cleanup${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleanup cancelled. Commit your changes and run again."
        exit 0
    fi
fi

# Confirm cleanup
echo -e "\n${BOLD}${YELLOW}⚠️  CLEANUP CONFIRMATION${NC}"
echo "This cleanup will:"
echo "  • Remove ~75 development and temporary files"
echo "  • Reorganize ~25 test files into proper directories"
echo "  • Consolidate ~15 documentation files"
echo "  • Create automatic backup before changes"
echo "  • Preserve all core application code and essential docs"
echo ""
read -p "Proceed with cleanup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Cleanup cancelled by user"
    exit 0
fi

# Step 1: Main codebase cleanup
print_step "🧹 Step 1: Main Codebase Cleanup"
print_info "Running codebase cleanup script..."

if ./scripts/cleanup-codebase.sh; then
    print_status "Codebase cleanup completed successfully"
else
    print_error "Codebase cleanup failed"
    exit 1
fi

# Step 2: Test reorganization
print_step "🧪 Step 2: Test File Reorganization"
print_info "Reorganizing test files into proper structure..."

if ./scripts/reorganize-tests.sh; then
    print_status "Test reorganization completed successfully"
else
    print_error "Test reorganization failed"
    exit 1
fi

# Step 3: Validation
print_step "🔍 Step 3: Post-Cleanup Validation"
print_info "Validating that cleanup didn't break functionality..."

if ./scripts/validate-cleanup.sh; then
    print_status "Validation completed successfully"
else
    print_error "Validation failed - please review errors"
    exit 1
fi

# Post-cleanup statistics
print_step "📊 Post-Cleanup Analysis"

NEW_TOTAL_FILES=$(find . -type f ! -path "./.git/*" ! -path "./node_modules/*" ! -path "./__pycache__/*" | wc -l | tr -d ' ')
NEW_TOTAL_DIRS=$(find . -type d ! -path "./.git/*" ! -path "./node_modules/*" ! -path "./__pycache__/*" | wc -l | tr -d ' ')
NEW_MD_FILES=$(find . -name "*.md" ! -path "./.git/*" | wc -l | tr -d ' ')
NEW_PY_FILES=$(find . -name "*.py" ! -path "./.git/*" ! -path "./venv/*" ! -path "./__pycache__/*" | wc -l | tr -d ' ')
NEW_TEST_FILES=$(find . -name "test_*.py" ! -path "./.git/*" ! -path "./*/tests/*" | wc -l | tr -d ' ')

FILES_REMOVED=$((TOTAL_FILES - NEW_TOTAL_FILES))
DIRS_CHANGED=$((TOTAL_DIRS - NEW_TOTAL_DIRS))
MD_ORGANIZED=$((MD_FILES - NEW_MD_FILES))
SCATTERED_TESTS_REMOVED=$((TEST_FILES - NEW_TEST_FILES))

print_info "Cleanup results:"
echo "  🗑️  Files removed: $FILES_REMOVED"
echo "  📁 Directory changes: $DIRS_CHANGED"
echo "  📄 Documentation organized: $MD_ORGANIZED files"
echo "  🧪 Scattered tests reorganized: $SCATTERED_TESTS_REMOVED files"

# Get new disk usage
if command -v du &> /dev/null; then
    NEW_SIZE=$(du -sh . 2>/dev/null | cut -f1)
    print_info "New directory size: $NEW_SIZE"
fi

# Final git status
NEW_GIT_STATUS=$(git status --porcelain | wc -l | tr -d ' ')
print_info "Git changes: $NEW_GIT_STATUS files modified"

# Success summary
print_step "🎉 Cleanup Complete!"

echo -e "${BOLD}${GREEN}✅ CLEANUP SUCCESSFUL${NC}"
echo ""
echo -e "${BOLD}Summary of Changes:${NC}"
echo "  • Removed $FILES_REMOVED temporary and development files"
echo "  • Organized $SCATTERED_TESTS_REMOVED scattered test files into proper directories"
echo "  • Consolidated $MD_ORGANIZED documentation files"
echo "  • Created clean directory structure with proper separation"
echo "  • Preserved all core functionality and essential documentation"
echo "  • Maintained historical archive for reference"

echo -e "\n${BOLD}${BLUE}📁 New Clean Structure:${NC}"
echo "├── 📁 damien-cli/           # Core CLI application"
echo "│   ├── damien_cli/          # Source code"
echo "│   └── tests/               # Organized test suite"
echo "├── 📁 damien-mcp-server/    # FastAPI MCP server"
echo "├── 📁 damien-mcp-minimal/   # Minimal MCP adapter"
echo "├── 📁 aws-infrastructure/   # Lambda functions"
echo "├── 📁 docs/                 # Organized documentation"
echo "│   ├── deployment/          # Production guides"
echo "│   ├── testing/             # Test documentation"
echo "│   ├── troubleshooting/     # Issue resolution"
echo "│   └── operations/          # Operations guides"
echo "├── 📁 scripts/              # Management scripts"
echo "├── 📁 tests/                # Project-level tests"
echo "└── 📁 archive/              # Historical docs (preserved)"

echo -e "\n${BOLD}${YELLOW}🚀 Next Steps:${NC}"
echo "1. 🔧 Test functionality:"
echo "   ./scripts/start-all.sh"
echo ""
echo "2. 🧪 Run test suites:"
echo "   cd damien-cli && pytest tests/"
echo "   cd ../damien-mcp-server && pytest"
echo ""
echo "3. 💾 Commit the cleaned codebase:"
echo "   git add ."
echo "   git commit -m \"feat: Clean up codebase and organize documentation\""
echo ""
echo "4. 📚 Review new documentation structure:"
echo "   cat docs/README.md"

echo -e "\n${BOLD}${GREEN}🎯 Your codebase is now clean, organized, and ready for development!${NC}"

# Offer to run next steps
echo -e "\n${YELLOW}Would you like to:${NC}"
read -p "1. Start services to test functionality? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Starting services..."
    if ./scripts/start-all.sh; then
        print_status "Services started successfully"
    else
        print_warning "Service start had issues - check logs"
    fi
fi

echo -e "\n${GREEN}Master cleanup process completed successfully! 🎉${NC}"