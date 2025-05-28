#!/usr/bin/env python3
"""
Minimal import test to identify the issue
"""
import sys
import os

# Add damien_cli to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

print("Testing imports step by step...")

try:
    print("1. Testing core models...")
    from damien_cli.features.ai_intelligence.models import PatternType
    print("   ✅ PatternType imported")
    
    from damien_cli.features.ai_intelligence.models import EmailPattern
    print("   ✅ EmailPattern imported")
    
except Exception as e:
    print(f"   ❌ Models import failed: {e}")
    exit(1)

try:
    print("2. Testing embeddings...")
    from damien_cli.features.ai_intelligence.categorization.embeddings import EmailEmbeddingGenerator
    print("   ✅ EmailEmbeddingGenerator imported")
    
except Exception as e:
    print(f"   ❌ Embeddings import failed: {e}")
    exit(1)

try:
    print("3. Testing patterns...")
    from damien_cli.features.ai_intelligence.categorization.patterns import EmailPatternDetector
    print("   ✅ EmailPatternDetector imported")
    
except Exception as e:
    print(f"   ❌ Patterns import failed: {e}")
    exit(1)

try:
    print("4. Testing Gmail analyzer...")
    from damien_cli.features.ai_intelligence.categorization.gmail_analyzer import GmailEmailAnalyzer
    print("   ✅ GmailEmailAnalyzer imported")
    
except Exception as e:
    print(f"   ❌ Gmail analyzer import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("🎉 All imports successful!")
