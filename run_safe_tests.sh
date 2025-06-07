#!/bin/bash

# Safe Test Runner for Damien Email Wrestler
# Runs read-only tests first, then optionally creates minimal test data

echo "🚀 Damien Email Wrestler - Safe Testing Suite"
echo "============================================"

# Check if we're in the right directory
if [ ! -f "damien-cli/pyproject.toml" ]; then
    echo "❌ Error: Must run from damien-email-wrestler root directory"
    exit 1
fi

# Ensure services are running
echo "🔍 Checking service status..."
./scripts/status.sh

# Ask user if they want to continue
echo ""
echo "This will run safe read-only tests on your Gmail account."
echo "No emails will be modified in Phase 1."
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Testing cancelled"
    exit 1
fi

# Run the safe test runner
cd test_harness
python safe_test_runner.py

# Return to root
cd ..

echo ""
echo "✅ Testing session complete"
echo "Results saved in: test_harness/results/"