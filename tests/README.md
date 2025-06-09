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
