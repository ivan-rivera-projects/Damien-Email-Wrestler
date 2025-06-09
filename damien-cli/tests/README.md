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
