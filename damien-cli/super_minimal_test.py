#!/usr/bin/env python3
"""
Super minimal test - no ML dependencies
"""
import sys
import os
print("Starting minimal test...")

try:
    # Test just the basic pattern types
    print("Testing PatternType enum...")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    
    # Import just the enum from models
    from damien_cli.features.ai_intelligence.models import PatternType
    print("✅ PatternType imported successfully")
    
    print(f"Available pattern types: {[p.value for p in PatternType]}")
    
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
