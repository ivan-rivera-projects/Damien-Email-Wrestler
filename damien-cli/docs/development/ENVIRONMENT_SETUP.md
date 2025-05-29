# Development Environment Setup Guide
**Version**: 1.0.0  
**Created**: 2025-01-12  
**Purpose**: Complete setup guide to get all 37/37 tests passing  

---

## Quick Start Checklist ✅

Before you begin, verify:
- [ ] Python 3.11 or 3.12 installed (NOT 3.13+)
- [ ] Poetry installed (latest version)
- [ ] Git repository cloned
- [ ] Project directory: `damien-email-wrestler/damien-cli`

---

## Essential Setup Steps

### 1. Python Version Check
```bash
# Check your Python version
python --version
# Should show: Python 3.11.x or 3.12.x (NOT 3.13+)

# If wrong version, install Python 3.11:
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

### 2. Poetry Setup
```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Verify Poetry
poetry --version

# Configure Poetry for this project
poetry env use python3.11
poetry config virtualenvs.in-project true
```

### 3. Project Dependencies
```bash
# Navigate to project directory
cd damien-email-wrestler/damien-cli

# Clean install (removes conflicts)
poetry env remove --all
poetry install

# Verify installation
poetry env info
# Should show Python 3.11.x/3.12.x and 100+ packages
```

### 4. Validate Setup
```bash
# Run the privacy tests (should be 37/37 passing)
poetry run pytest tests/test_pii_detection.py -v

# Test CLI command
poetry run damien --help

# Test core imports
poetry run python -c "
from damien_cli.features.ai_intelligence.llm_integration.privacy import PrivacyGuardian
print('✅ Setup successful!')
"
```

---

## Development Commands

### Daily Commands
```bash
# Run all tests
poetry run pytest

# Run specific test file  
poetry run pytest tests/test_pii_detection.py

# Format code
poetry run black damien_cli/ tests/

# Lint code
poetry run flake8 damien_cli/ tests/

# CLI commands (always use poetry run prefix)
poetry run damien --help
```

### Target Results
- **37/37 tests passing** (privacy module working)
- **All imports successful** (no dependency conflicts)
- **CLI commands working** (using poetry run prefix)
- **Code formatting** (black/flake8 passing)


---

## Common Issues & Solutions

### "No such command" Errors
**Problem**: Commands like `damien` not found  
**Solution**: Always use `poetry run` prefix
```bash
# Wrong: damien --help
# Correct: poetry run damien --help

# Or activate environment first:
poetry shell
damien --help
```

### Dependency Conflicts
**Problem**: Import errors, version conflicts  
**Solution**: Recreate environment
```bash
poetry env remove --all
poetry env use python3.11
poetry install
```

### Test Failures
**Problem**: Tests not passing 37/37  
**Solution**: Debug step by step
```bash
# Run with verbose output
poetry run pytest tests/test_pii_detection.py -v --tb=short

# Check specific test
poetry run pytest tests/test_pii_detection.py::test_email_detection -v

# Verify dependencies
poetry run python -c "import torch, sentence_transformers; print('ML deps OK')"
```

### PyTorch Issues
**Problem**: Torch import failures  
**Solution**: Reinstall CPU version
```bash
poetry remove torch
poetry add torch==2.1.0 --source pytorch-cpu
```

---

## Environment Validation Script

Save this as `validate_environment.py` in project root:

```python
#!/usr/bin/env python3
"""Environment validation for Damien CLI development."""

def validate_environment():
    print("🔍 Validating Damien CLI Environment...")
    
    # Check Python version
    import sys
    print(f"✅ Python: {sys.version}")
    assert (3, 11) <= sys.version_info < (3, 13), "Need Python 3.11-3.12"
    
    # Check core dependencies
    try:
        import torch, sentence_transformers, sklearn, pandas, numpy
        import openai, tiktoken
        print("✅ ML dependencies available")
    except ImportError as e:
        print(f"❌ Missing: {e}")
        return False
    
    # Check Damien modules
    try:
        from damien_cli.features.ai_intelligence.llm_integration.privacy import PrivacyGuardian
        from damien_cli.features.email_management import EmailManager
        print("✅ Damien modules importable")
    except ImportError as e:
        print(f"❌ Module error: {e}")
        return False
    
    print("\n🎉 Environment validation successful!")
    print("Run: poetry run pytest tests/test_pii_detection.py")
    print("Target: 37/37 tests passing")
    return True

if __name__ == "__main__":
    validate_environment()
```

### Run Validation
```bash
poetry run python validate_environment.py
```

---

## Success Criteria

Setup is complete when you achieve:
- [ ] **Python 3.11.x/3.12.x** confirmed
- [ ] **Poetry environment** created successfully  
- [ ] **37/37 privacy tests passing** (PII detection working)
- [ ] **All imports working** (no dependency conflicts)
- [ ] **CLI commands working** (with poetry run prefix)
- [ ] **Validation script** passes all checks

**Next Steps**: Start implementing Intelligence Router with confidence!
