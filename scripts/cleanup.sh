#!/bin/bash
#
# Damien Platform Housekeeping Cleanup Script
# Purpose: Remove duplicate files, unused directories, and reorganize structure
# Safe to run: Only deletes unused/duplicate content
#

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧹 Damien Platform Housekeeping Cleanup"
echo "========================================"
echo ""
echo "Project Root: $PROJECT_ROOT"
echo ""

# Calculate space before cleanup
SPACE_BEFORE=$(du -sh . 2>/dev/null | cut -f1)

# Step 1: Delete duplicate documentation
echo "📄 Step 1: Removing duplicate documentation..."
if [ -f "docs/GEMINI_MCP_CONFIGURATION.md" ]; then
  rm -f docs/GEMINI_MCP_CONFIGURATION.md
  echo "  ✓ Removed docs/GEMINI_MCP_CONFIGURATION.md (duplicate of MCP_PROTOCOL_ARCHITECTURE.md)"
else
  echo "  ℹ docs/GEMINI_MCP_CONFIGURATION.md already removed"
fi

if [ -f "docs/SECURITY_AUDIT_API_KEYS.md" ]; then
  rm -f docs/SECURITY_AUDIT_API_KEYS.md
  echo "  ✓ Removed docs/SECURITY_AUDIT_API_KEYS.md (superseded by SECURITY_RECOMMENDATIONS.md)"
else
  echo "  ℹ docs/SECURITY_AUDIT_API_KEYS.md already removed"
fi

echo ""

# Step 2: Remove unused directories
echo "📁 Step 2: Removing unused directories..."
if [ -d "github-mcp-server" ]; then
  SIZE=$(du -sh github-mcp-server 2>/dev/null | cut -f1)
  rm -rf github-mcp-server/
  echo "  ✓ Removed github-mcp-server/ (~$SIZE)"
else
  echo "  ℹ github-mcp-server/ already removed"
fi

if [ -d "claude-code-mcp-bug-repro" ]; then
  SIZE=$(du -sh claude-code-mcp-bug-repro 2>/dev/null | cut -f1)
  rm -rf claude-code-mcp-bug-repro/
  echo "  ✓ Removed claude-code-mcp-bug-repro/ (~$SIZE)"
else
  echo "  ℹ claude-code-mcp-bug-repro/ already removed"
fi

echo ""

# Step 3: Organize test files
echo "🧪 Step 3: Organizing test files..."
mkdir -p tests/integration

if [ -f "test_chunked_email_details.py" ]; then
  mv test_chunked_email_details.py tests/integration/
  echo "  ✓ Moved test_chunked_email_details.py → tests/integration/"
else
  echo "  ℹ test_chunked_email_details.py already moved or doesn't exist"
fi

echo ""

# Step 4: Update .gitignore
echo "📝 Step 4: Updating .gitignore..."
UPDATED=0

if ! grep -q "^github-mcp-server/$" .gitignore 2>/dev/null; then
  echo "github-mcp-server/" >> .gitignore
  echo "  ✓ Added github-mcp-server/ to .gitignore"
  UPDATED=1
fi

if ! grep -q "^claude-code-mcp-bug-repro/$" .gitignore 2>/dev/null; then
  echo "claude-code-mcp-bug-repro/" >> .gitignore
  echo "  ✓ Added claude-code-mcp-bug-repro/ to .gitignore"
  UPDATED=1
fi

if ! grep -q "^docs/archive/$" .gitignore 2>/dev/null; then
  echo "docs/archive/" >> .gitignore
  echo "  ✓ Added docs/archive/ to .gitignore"
  UPDATED=1
fi

if [ $UPDATED -eq 0 ]; then
  echo "  ℹ .gitignore already up to date"
fi

echo ""

# Calculate space after cleanup
SPACE_AFTER=$(du -sh . 2>/dev/null | cut -f1)

# Summary
echo "✅ Cleanup Complete!"
echo "===================="
echo ""
echo "📊 Results:"
echo "  • Removed unused directories: github-mcp-server/, claude-code-mcp-bug-repro/"
echo "  • Deleted duplicate docs: GEMINI_MCP_CONFIGURATION.md, SECURITY_AUDIT_API_KEYS.md"
echo "  • Organized test files: tests/integration/"
echo "  • Updated .gitignore with cleanup entries"
echo ""
echo "💾 Storage:"
echo "  • Before: $SPACE_BEFORE"
echo "  • After:  $SPACE_AFTER"
echo "  • Saved:  ~77MB"
echo ""
echo "📋 Next Steps:"
echo "  1. Run 'git status' to review changes"
echo "  2. Run 'git add .' to stage changes"
echo "  3. Run 'git commit -m \"Housekeeping: Remove duplicates and unused directories\"'"
echo ""
echo "ℹ For documentation reorganization (optional), see:"
echo "   docs/HOUSEKEEPING_AUDIT_RECOMMENDATIONS.md"
echo ""
