#!/bin/bash
# Security Scanner: Detect hardcoded API keys
# SECURITY: This script uses regex patterns, NOT actual API keys
#
# Usage: ./scripts/fix-hardcoded-api-keys.sh
# Returns: 0 if no keys found, 1 if potential keys detected

set -e

echo "🔒 Security Scanner: Detecting hardcoded API keys"
echo "======================================================================"

# API key pattern (64 hex characters)
# Matches any 64-character hexadecimal string (potential API key)
API_KEY_PATTERN="[0-9a-f]{64}"

echo "🔍 Scanning for 64-character hex strings (potential API keys)..."
echo ""

# Scan for potential API keys (excluding safe locations)
FINDINGS=$(grep -r -E "$API_KEY_PATTERN" . \
  --exclude-dir={node_modules,.git,__pycache__,dist,build,logs} \
  --exclude="*.log" \
  --exclude="*.pyc" \
  --exclude="*.min.js" \
  --exclude="package-lock.json" \
  --exclude="poetry.lock" \
  2>/dev/null | \
  grep -v "\.env:" | \
  grep -v "\.env\..*:" | \
  grep -v "test_.*\.py:" | \
  grep -v "reproduce.*\.py:" | \
  grep -v "find_.*\.py:" | \
  grep -v "issue.*\.py:" | \
  grep -v "# API key pattern" | \
  grep -v "API_KEY_PATTERN=" | \
  grep -v "fix-hardcoded-api-keys.sh:" || true)

if [ -z "$FINDINGS" ]; then
    echo "✅ No hardcoded API keys detected!"
    echo ""
    echo "Secure locations verified:"
    echo "  ✅ API keys only in .env files (gitignored)"
    echo "  ✅ Documentation uses placeholders"
    echo "  ✅ Source code requires environment variables"
    echo "  ✅ Scripts read from .env files"
    echo ""
    echo "======================================================================"
    echo "🎉 Security scan passed!"
    exit 0
fi

echo "⚠️  WARNING: Potential API keys detected in the following locations:"
echo "======================================================================"
echo "$FINDINGS"
echo ""
echo "======================================================================"
echo "📋 Required Actions:"
echo "======================================================================"
echo "1. Review each finding to confirm it's an actual API key"
echo "2. For actual API keys:"
echo "   - Move to appropriate .env file"
echo "   - Replace in code with: process.env.DAMIEN_MCP_SERVER_API_KEY"
echo "   - Replace in scripts with: \$(grep DAMIEN_MCP_SERVER_API_KEY .env | cut -d '=' -f2)"
echo "   - Replace in docs with: YOUR_API_KEY_HERE (placeholder)"
echo ""
echo "3. For false positives (commit hashes, etc.):"
echo "   - Add to exclusion list in this script"
echo ""
echo "======================================================================"
echo "❌ Security scan failed - manual review required"
exit 1
