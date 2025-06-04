#!/bin/bash
#
# Test Runner for Damien MCP Minimal Server
#
# This script runs all test suites and reports results.
# It can be used to verify system functionality before deployment.
#
# Usage:
#   ./run-tests.sh [options]
#
# Options:
#   --basic-only     Run only basic tests
#   --backend-only   Run only backend connectivity tests
#   --integration    Run integration tests (requires backend)
#   --all            Run all tests (default)
#   --benchmark      Include performance benchmarks
#   --verbose        Show detailed output
#

# Set script to exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_BASIC=true
RUN_COMPAT=true
RUN_PHASE=true
RUN_INTEGRATION=false
RUN_BENCHMARK=false
VERBOSE=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --basic-only) 
      RUN_BASIC=true
      RUN_COMPAT=false
      RUN_PHASE=false
      RUN_INTEGRATION=false
      ;;
    --backend-only)
      RUN_BASIC=false
      RUN_COMPAT=false
      RUN_PHASE=false
      RUN_INTEGRATION=true
      ;;
    --integration)
      RUN_INTEGRATION=true
      ;;
    --all)
      RUN_BASIC=true
      RUN_COMPAT=true
      RUN_PHASE=true
      RUN_INTEGRATION=true
      ;;
    --benchmark)
      RUN_BENCHMARK=true
      ;;
    --verbose)
      VERBOSE=true
      ;;
    *)
      echo -e "${RED}Unknown parameter: $1${NC}"
      exit 1
      ;;
  esac
  shift
done

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# Go to the project root directory
cd "$SCRIPT_DIR/.."

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    Damien MCP Minimal Server Tests     ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Track test results
PASSED=0
FAILED=0
SKIPPED=0

# Function to run a test
run_test() {
  local test_name=$1
  local test_script=$2
  local required=$3
  
  if [ "$required" = true ] || eval "$4"; then
    echo -e "\n${BLUE}Running $test_name...${NC}"
    
    if [ "$VERBOSE" = true ]; then
      node "$test_script"
      result=$?
    else
      # Capture output but show errors
      output=$(node "$test_script" 2>&1)
      result=$?
      
      # Show only test results (lines with emojis)
      echo "$output" | grep -E "✅|❌|⚠️|🎉" || true
    fi
    
    if [ $result -eq 0 ]; then
      echo -e "${GREEN}✓ $test_name passed${NC}"
      ((PASSED++))
    else
      echo -e "${RED}✗ $test_name failed${NC}"
      ((FAILED++))
    fi
  else
    echo -e "\n${YELLOW}Skipping $test_name...${NC}"
    ((SKIPPED++))
  fi
}

# Run basic tests
run_test "Basic Tests" "tests/basic-test.js" true "$RUN_BASIC"

# Run Damien Client tests
run_test "Damien Client Tests" "tests/damien-client.test.js" true "$RUN_BASIC"

# Run Claude MAX compatibility tests
run_test "Claude MAX Compatibility Tests" "tests/claude-max-compatibility.test.js" false "$RUN_COMPAT"

# Run Phase Progression tests
run_test "Phase Progression Tests" "tests/phase-progression.test.js" false "$RUN_PHASE"

# Run Integration tests
run_test "Integration Tests" "tests/integration.test.js" false "$RUN_INTEGRATION"

# Run performance benchmarks if requested
if [ "$RUN_BENCHMARK" = true ]; then
  echo -e "\n${BLUE}Running Performance Benchmarks...${NC}"
  
  # Start time
  start_time=$(date +%s.%N)
  
  # Run a simple benchmark
  node -e "
    import('./server.js').then(async module => {
      const server = new module.default();
      console.log('Starting benchmark...');
      
      // Measure tool list performance
      const startTime = Date.now();
      const iterations = 100;
      
      for (let i = 0; i < iterations; i++) {
        await server.getCachedTools();
      }
      
      const elapsedMs = Date.now() - startTime;
      const avgMs = elapsedMs / iterations;
      
      console.log(\`Completed \${iterations} tool list requests in \${elapsedMs}ms\`);
      console.log(\`Average response time: \${avgMs.toFixed(2)}ms per request\`);
      
      // Memory usage
      const memoryUsage = process.memoryUsage();
      console.log('Memory usage:');
      console.log(\`  RSS: \${(memoryUsage.rss / 1024 / 1024).toFixed(2)} MB\`);
      console.log(\`  Heap used: \${(memoryUsage.heapUsed / 1024 / 1024).toFixed(2)} MB\`);
      
      process.exit(0);
    }).catch(err => {
      console.error('Benchmark failed:', err);
      process.exit(1);
    });
  "
  
  # End time
  end_time=$(date +%s.%N)
  execution_time=$(echo "$end_time - $start_time" | bc)
  
  echo -e "${BLUE}Benchmark execution time: ${execution_time} seconds${NC}"
fi

# Print summary
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${BLUE}              Test Summary              ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}Tests passed: $PASSED${NC}"
echo -e "${RED}Tests failed: $FAILED${NC}"
echo -e "${YELLOW}Tests skipped: $SKIPPED${NC}"
echo -e "${BLUE}Total tests: $((PASSED + FAILED + SKIPPED))${NC}"

# Exit with error if any tests failed
if [ $FAILED -gt 0 ]; then
  echo -e "\n${RED}❌ Some tests failed!${NC}"
  exit 1
else
  echo -e "\n${GREEN}🎉 All executed tests passed!${NC}"
  exit 0
fi