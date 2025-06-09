#!/usr/bin/env python3
"""
Environment validation script for Damien CLI development.
Run with: poetry run python validate_environment.py

This script validates that all dependencies are properly installed
and the development environment is ready for Phase 3 LLM Integration.
"""

def validate_environment():
    """Validate the complete development environment."""
    print("🔍 Validating Damien CLI Development Environment...")
    
    # Check Python version
    import sys
    print(f"✅ Python version: {sys.version}")
    
    if not ((3, 11) <= sys.version_info < (3, 13)):
        print(f"❌ Python version {sys.version_info} not supported")
        print("   Required: Python 3.11.x or 3.12.x")
        return False
    
    # Check core dependencies
    try:
        import torch
        import sentence_transformers
        import sklearn
        import pandas
        import numpy as np
        import openai
        import tiktoken
        print("✅ All core ML dependencies available")
    except ImportError as e:
        print(f"❌ Missing core dependency: {e}")
        print("   Run: poetry install")
        return False
    
    # Check Damien core modules
    try:
        from damien_cli.features.ai_intelligence.llm_integration.privacy import PrivacyGuardian
        from damien_cli.features.email_management import EmailManager
        print("✅ Damien core modules importable")
    except ImportError as e:
        print(f"❌ Damien module import error: {e}")
        print("   Check project structure and dependencies")
        return False
    
    # Test privacy functionality instantiation
    try:
        guardian = PrivacyGuardian()
        print("✅ Privacy module instantiable")
    except Exception as e:
        print(f"❌ Privacy module instantiation error: {e}")
        return False
    
    # Check development tools
    try:
        import pytest
        import black
        print("✅ Development tools available")
    except ImportError as e:
        print(f"❌ Missing dev dependency: {e}")
        return False
    
    print("\n🎉 Environment validation successful!")
    print("\n📋 Next steps:")
    print("   1. Run: poetry run pytest tests/test_pii_detection.py")
    print("   2. Target: 37/37 tests passing")
    print("   3. Verify: 99.9% PII detection accuracy achieved")
    print("   4. Start development with confidence!")
    
    return True

if __name__ == "__main__":
    success = validate_environment()
    exit(0 if success else 1)
