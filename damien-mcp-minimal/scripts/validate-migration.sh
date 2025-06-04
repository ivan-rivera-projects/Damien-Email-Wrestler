#!/bin/bash
#
# Migration Validation Script for Damien MCP Minimal Server
#
# This script validates that the migration to the minimal MCP server
# was successful by testing connectivity and functionality.
#
# Usage:
#   ./validate-migration.sh [options]
#
# Options:
#   --verbose        Show detailed output
#   --help           Show this help message
#

# Set script to exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
VERBOSE=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --verbose)
      VERBOSE=true
      ;;
    --help)
      echo "Usage: ./validate-migration.sh [options]"
      echo ""
      echo "Options:"
      echo "  --verbose        Show detailed output"
      echo "  --help           Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown parameter: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
  shift
done

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# Go to the project root directory
cd "$SCRIPT_DIR/../.."
PROJECT_ROOT=$(pwd)
MINIMAL_DIR="$PROJECT_ROOT/damien-mcp-minimal"

# Import .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Set configuration values
MINIMAL_PORT="${DAMIEN_MCP_MINIMAL_PORT:-8893}"

# Claude Desktop config path based on OS
if [ -z "$CLAUDE_DESKTOP_CONFIG_PATH" ]; then
  if [ "$(uname)" == "Darwin" ]; then
    # macOS
    CLAUDE_DESKTOP_CONFIG_PATH="$HOME/Library/Application Support/Claude Desktop/config.json"
  elif [ "$(uname)" == "Linux" ]; then
    # Linux
    CLAUDE_DESKTOP_CONFIG_PATH="$HOME/.config/Claude Desktop/config.json"
  elif [ "$(expr substr $(uname -s) 1 5)" == "MINGW" ] || [ "$(expr substr $(uname -s) 1 6)" == "CYGWIN" ]; then
    # Windows
    CLAUDE_DESKTOP_CONFIG_PATH="$APPDATA\\Claude Desktop\\config.json"
  else
    echo -e "${RED}Unsupported operating system${NC}"
    exit 1
  fi
fi

# Function to check if a process is running on a port
check_port_in_use() {
  local port=$1
  if command -v lsof &> /dev/null; then
    if lsof -i:"$port" &> /dev/null; then
      return 0
    else
      return 1
    fi
  elif command -v netstat &> /dev/null; then
    if netstat -tulpn 2>/dev/null | grep ":$port " &> /dev/null; then
      return 0
    else
      return 1
    fi
  else
    echo -e "${YELLOW}Warning: Neither lsof nor netstat available. Cannot check port usage.${NC}"
    return 1
  fi
}

# Function to run a test with proper formatting
run_test() {
  local test_name=$1
  local test_cmd=$2
  
  echo -e "${BLUE}TEST: $test_name${NC}"
  
  if $VERBOSE; then
    echo -e "${CYAN}Running: $test_cmd${NC}"
  fi
  
  if eval "$test_cmd"; then
    echo -e "${GREEN}✓ PASS: $test_name${NC}"
    return 0
  else
    echo -e "${RED}✗ FAIL: $test_name${NC}"
    return 1
  fi
}

# Print header
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    Damien MCP Migration Validation    ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Track validation success
VALIDATION_SUCCESS=true

# Test 1: Check if minimal server is running
if ! run_test "Minimal server running" "check_port_in_use $MINIMAL_PORT"; then
  echo -e "${RED}ERROR: Minimal MCP server is not running on port $MINIMAL_PORT${NC}"
  echo -e "${YELLOW}Please start the server before running validation.${NC}"
  exit 1
fi

# Test 2: Check Claude Desktop configuration
if [ -f "$CLAUDE_DESKTOP_CONFIG_PATH" ] && command -v jq &> /dev/null; then
  CURRENT_MCP_URL=$(jq -r '.mcpConfig.mcpUrl // "not-set"' "$CLAUDE_DESKTOP_CONFIG_PATH")
  EXPECTED_URL="http://localhost:$MINIMAL_PORT"
  
  if ! run_test "Claude Desktop configuration" "[ \"$CURRENT_MCP_URL\" = \"$EXPECTED_URL\" ]"; then
    echo -e "${RED}ERROR: Claude Desktop is not configured to use minimal server${NC}"
    echo -e "${YELLOW}Current URL: $CURRENT_MCP_URL${NC}"
    echo -e "${YELLOW}Expected URL: $EXPECTED_URL${NC}"
    VALIDATION_SUCCESS=false
  fi
else
  echo -e "${YELLOW}WARNING: Cannot check Claude Desktop configuration${NC}"
  echo -e "${YELLOW}(missing jq or config file: $CLAUDE_DESKTOP_CONFIG_PATH)${NC}"
fi

# Test 3: Basic server functionality using health check
if [ -f "$MINIMAL_DIR/tests/basic-test.js" ]; then
  if ! run_test "Basic server functionality" "(cd $MINIMAL_DIR && node tests/basic-test.js)"; then
    echo -e "${RED}ERROR: Basic server functionality test failed${NC}"
    VALIDATION_SUCCESS=false
  fi
else
  echo -e "${YELLOW}WARNING: Cannot run basic server test (file not found)${NC}"
  echo -e "${YELLOW}File not found: $MINIMAL_DIR/tests/basic-test.js${NC}"
fi

# Test 4: Claude MAX compatibility test
if [ -f "$MINIMAL_DIR/tests/claude-max-compatibility.test.js" ]; then
  if ! run_test "Claude MAX compatibility" "(cd $MINIMAL_DIR && node tests/claude-max-compatibility.test.js)"; then
    echo -e "${RED}ERROR: Claude MAX compatibility test failed${NC}"
    VALIDATION_SUCCESS=false
  fi
else
  echo -e "${YELLOW}WARNING: Cannot run Claude MAX compatibility test (file not found)${NC}"
  echo -e "${YELLOW}File not found: $MINIMAL_DIR/tests/claude-max-compatibility.test.js${NC}"
fi

# Test 5: Tool functionality tests for Phase 1
if [ -f "$MINIMAL_DIR/tests/phase-progression.test.js" ]; then
  if ! run_test "Phase 1 tool functionality" "(cd $MINIMAL_DIR && DAMIEN_INITIAL_PHASE=1 node tests/phase-progression.test.js)"; then
    echo -e "${RED}ERROR: Phase 1 tool functionality test failed${NC}"
    VALIDATION_SUCCESS=false
  fi
else
  echo -e "${YELLOW}WARNING: Cannot run Phase 1 tool test (file not found)${NC}"
  echo -e "${YELLOW}File not found: $MINIMAL_DIR/tests/phase-progression.test.js${NC}"
fi

# Test 6: Performance test
echo -e "${BLUE}TEST: Performance monitoring${NC}"
cd $MINIMAL_DIR

# Create a simple performance test
PERF_TEST=$(mktemp)
cat > $PERF_TEST << 'EOF'
import MinimalDamienMCP from './server.js';

async function runPerformanceTest() {
  try {
    console.log('Starting performance test...');
    
    const server = new MinimalDamienMCP();
    
    // Measure tool list performance
    const startTime = Date.now();
    const iterations = 10;
    
    console.log(`Running ${iterations} consecutive tool list requests...`);
    
    for (let i = 0; i < iterations; i++) {
      await server.getCachedTools();
    }
    
    const elapsedMs = Date.now() - startTime;
    const avgMs = elapsedMs / iterations;
    
    console.log(`Completed ${iterations} tool list requests in ${elapsedMs}ms`);
    console.log(`Average response time: ${avgMs.toFixed(2)}ms per request`);
    
    // Check if performance is acceptable (less than 200ms per request on average)
    if (avgMs < 200) {
      console.log('Performance is within acceptable limits');
      process.exit(0);
    } else {
      console.error('Performance is below acceptable limits');
      process.exit(1);
    }
  } catch (error) {
    console.error('Performance test failed:', error);
    process.exit(1);
  }
}

runPerformanceTest();
EOF

if ! run_test "Performance monitoring" "node $PERF_TEST"; then
  echo -e "${RED}ERROR: Performance test failed${NC}"
  VALIDATION_SUCCESS=false
fi

# Clean up temp file
rm $PERF_TEST

# Return to project root
cd $PROJECT_ROOT

# Print validation summary
echo -e "\n${BLUE}Validation Summary${NC}"
echo -e "${BLUE}=========================================${NC}"

if $VALIDATION_SUCCESS; then
  echo -e "${GREEN}✅ All validation tests passed!${NC}"
  echo -e "${GREEN}Migration to minimal MCP server was successful.${NC}"
  exit 0
else
  echo -e "${RED}❌ Some validation tests failed.${NC}"
  echo -e "${YELLOW}Migration may not be fully successful. Please check the errors above.${NC}"
  exit 1
fi
