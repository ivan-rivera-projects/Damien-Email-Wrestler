#!/bin/bash
# 🧪 Damien Email Wrestler - Test File Reorganization Script
# This script reorganizes scattered test files into proper test directories
# Run after cleanup-codebase.sh: ./scripts/reorganize-tests.sh

set -e  # Exit on any error

PROJECT_ROOT="/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Damien Email Wrestler Test Reorganization${NC}"
echo -e "${BLUE}==========================================${NC}"

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
if [[ ! -f "CLAUDE.md" || ! -d "damien-cli" ]]; then
    print_error "This script must be run from the Damien Email Wrestler project root"
    exit 1
fi

# Step 1: Create proper test directory structure in damien-cli
echo -e "\n${BLUE}Phase 1: Creating Test Directory Structure${NC}"
mkdir -p damien-cli/tests/{integration,components,utilities,performance}
mkdir -p tests/{integration,performance,fixtures}
print_status "Created test directory structure"

# Step 2: Reorganize damien-cli test files
echo -e "\n${BLUE}Phase 2: Reorganizing damien-cli Test Files${NC}"

cd damien-cli

# Integration tests - comprehensive end-to-end tests
INTEGRATION_TESTS=(
    "test_phase3_complete_integration.py"
    "test_end_to_end_pipeline.py"
    "test_batch_processor_integration.py"
    "test_embeddings_integration.py"
    "test_router_integration.py"
    "test_rag_engine_integration.py"
    "test_gmail_integration.py"
    "test_phase3_validation.py"
)

for file in "${INTEGRATION_TESTS[@]}"; do
    if [[ -f "$file" ]]; then
        mv "$file" "tests/integration/"
        print_status "Moved to integration: $file"
    fi
done

# Component tests - specific feature/component tests
COMPONENT_TESTS=(
    "test_sentence_transformers.py"
    "test_pattern_detection.py"
    "test_embeddings.py"
    "test_pattern_creation.py"
    "test_model_validation.py"
)

for file in "${COMPONENT_TESTS[@]}"; do
    if [[ -f "$file" ]]; then
        mv "$file" "tests/components/"
        print_status "Moved to components: $file"
    fi
done

# Utility tests - helper and utility function tests
UTILITY_TESTS=(
    "test_error_handling.py"
    "test_imports.py"
    "test_component_imports.py"
    "test_fixes.py"
)

for file in "${UTILITY_TESTS[@]}"; do
    if [[ -f "$file" ]]; then
        mv "$file" "tests/utilities/"
        print_status "Moved to utilities: $file"
    fi
done

# Performance tests - benchmark and load tests
PERFORMANCE_TESTS=(
    "test_results_phase1.json"
    "test_results_write_operations.json"
    "ragengine_readiness_check.py"
    "validate_environment.py"
    "validate_fixes.py"
)

for file in "${PERFORMANCE_TESTS[@]}"; do
    if [[ -f "$file" ]]; then
        mv "$file" "tests/performance/"
        print_status "Moved to performance: $file"
    fi
done

# Remove minimal/obsolete test files
OBSOLETE_TESTS=(
    "minimal_import_test.py"
    "minimal_test.py"
    "super_minimal_test.py"
    "test_env.py"
)

for file in "${OBSOLETE_TESTS[@]}"; do
    if [[ -f "$file" ]]; then
        rm "$file"
        print_status "Removed obsolete: $file"
    fi
done

cd ..

# Step 3: Reorganize MCP server test files
echo -e "\n${BLUE}Phase 3: Reorganizing MCP Server Test Files${NC}"

MCP_TEST_FILES=(
    "test_fetch_emails_implementation.py"
    "test_dynamodb.py"
    "test_large_scale_analysis.py"
    "test_thread_direct.py"
    "validate_job_management.py"
)

for file in "${MCP_TEST_FILES[@]}"; do
    if [[ -f "damien-mcp-server/$file" ]]; then
        mv "damien-mcp-server/$file" "damien-mcp-server/tests/"
        print_status "Moved MCP test: $file"
    fi
done

# Step 4: Create test configuration files
echo -e "\n${BLUE}Phase 4: Creating Test Configuration${NC}"

# Create pytest.ini for damien-cli tests
cat > damien-cli/pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
markers =
    integration: Integration tests that require external services
    performance: Performance and benchmark tests
    slow: Tests that take more than 10 seconds
    requires_auth: Tests that require Gmail authentication
    requires_aws: Tests that require AWS credentials
EOF

print_status "Created damien-cli/pytest.ini"

# Create test README
cat > damien-cli/tests/README.md << 'EOF'
# Damien CLI Test Suite

## Test Organization

### `integration/`
End-to-end tests that validate complete workflows:
- Phase 3 complete integration tests
- Pipeline validation tests
- External service integration tests

### `components/`
Feature-specific component tests:
- AI/ML component tests (embeddings, pattern detection)
- Model validation tests
- Sentence transformer tests

### `utilities/`
Helper function and utility tests:
- Error handling tests
- Import validation tests
- Fix verification tests

### `performance/`
Performance and benchmark tests:
- Environment validation
- Readiness checks
- Load testing results

## Running Tests

```bash
# All tests
pytest

# Specific category
pytest tests/integration/
pytest tests/components/
pytest tests/utilities/
pytest tests/performance/

# With markers
pytest -m "not slow"
pytest -m "integration"
pytest -m "requires_auth"
```

## Test Requirements

- Some tests require Gmail authentication (`-m requires_auth`)
- Some tests require AWS credentials (`-m requires_aws`)
- Performance tests may take longer (`-m slow`)
EOF

print_status "Created damien-cli/tests/README.md"

# Step 5: Update main project tests directory
echo -e "\n${BLUE}Phase 5: Organizing Project-Level Tests${NC}"

# Move any remaining project-level test files
if [[ -d "test_harness" ]]; then
    mv test_harness/* tests/integration/ 2>/dev/null || true
    rmdir test_harness 2>/dev/null || true
    print_status "Moved test harness files to integration tests"
fi

# Create project-level test README
cat > tests/README.md << 'EOF'
# Damien Email Wrestler - Project Test Suite

## Test Organization

This directory contains project-level tests that span multiple components:

### `integration/`
Cross-component integration tests:
- Multi-service workflow tests
- End-to-end pipeline validation
- Service communication tests

### `performance/`
System-wide performance tests:
- Throughput benchmarks
- Memory usage tests
- Scalability validation

### `fixtures/`
Shared test data and fixtures:
- Sample email data
- Mock API responses
- Test configurations

## Component-Specific Tests

Component-specific tests are located in each component's directory:
- `damien-cli/tests/` - CLI application tests
- `damien-mcp-server/tests/` - MCP server tests
- `damien-mcp-minimal/tests/` - Minimal adapter tests

## Running Tests

```bash
# All project tests
pytest tests/

# Specific test categories
pytest tests/integration/
pytest tests/performance/

# All tests across entire project
pytest -x  # Stop on first failure
```
EOF

print_status "Created tests/README.md"

# Final summary
echo -e "\n${GREEN}🎉 Test Reorganization Complete!${NC}"
echo -e "${BLUE}===============================================${NC}"

echo -e "\n${GREEN}📁 New Test Structure:${NC}"
echo "damien-cli/tests/"
echo "├── integration/     # End-to-end workflow tests"
echo "├── components/      # Feature-specific tests"
echo "├── utilities/       # Helper function tests"
echo "├── performance/     # Benchmark tests"
echo "├── pytest.ini      # Test configuration"
echo "└── README.md        # Test documentation"
echo ""
echo "damien-mcp-server/tests/"
echo "├── (existing structure preserved)"
echo "└── (moved loose test files here)"
echo ""
echo "tests/"
echo "├── integration/     # Cross-component tests"
echo "├── performance/     # System-wide benchmarks"
echo "├── fixtures/        # Shared test data"
echo "└── README.md        # Project test guide"

echo -e "\n${YELLOW}Test Commands:${NC}"
echo "# Run all CLI tests:"
echo "cd damien-cli && pytest"
echo ""
echo "# Run integration tests only:"
echo "cd damien-cli && pytest tests/integration/"
echo ""
echo "# Run project-wide tests:"
echo "pytest tests/"

print_status "All test files organized into proper directories"
print_status "Test configuration files created"
print_status "Documentation updated with test organization"

echo -e "\n${GREEN}Test structure is now clean and organized! 🧪${NC}"