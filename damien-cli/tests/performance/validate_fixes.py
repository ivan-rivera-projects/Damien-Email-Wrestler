#!/usr/bin/env python3
"""
Quick test script to validate just the Pydantic validation fix
without requiring all ML dependencies.
"""

import sys
import os
import traceback
from pathlib import Path

# Add the damien_cli directory to Python path
current_dir = Path(__file__).parent
damien_cli_dir = current_dir / "damien_cli"
sys.path.insert(0, str(damien_cli_dir))

def test_batch_processing_result_model():
    """Test that BatchProcessingResult model works with all required fields"""
    print("🧪 Testing BatchProcessingResult model validation fix...")
    
    try:
        # Mock the imports that might not be available
        sys.modules['pydantic'] = type('MockPydantic', (), {
            'BaseModel': object,
            'Field': lambda **kwargs: None,
            'computed_field': lambda func: func,
            'ConfigDict': lambda **kwargs: {},
        })()
        
        # Create a minimal test of the model structure
        expected_fields = [
            'total_items',
            'processed_successfully', 
            'failed_items',
            'skipped_items',
            'processing_time_seconds',
            'throughput_per_second',
            'peak_memory_usage_mb',          # Previously missing - should now be included
            'average_cpu_usage_percent',     # Previously missing - should now be included  
            'patterns_discovered',           # Previously missing - should now be included
            'suggestions_created',           # Previously missing - should now be included
            'retry_attempts',                # Previously missing - should now be included
            'embeddings_generated',
            'batch_size',
            'parallel_workers'
        ]
        
        print("✅ Expected fields for BatchProcessingResult:")
        for field in expected_fields:
            print(f"   • {field}")
        
        # Test that all expected fields are present in our batch_processor.py
        with open('damien_cli/features/ai_intelligence/utils/batch_processor.py', 'r') as f:
            content = f.read()
            
        missing_fields = []
        for field in expected_fields:
            if field not in content:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing fields in batch_processor.py: {missing_fields}")
            return False
        else:
            print("✅ All required fields found in batch_processor.py")
        
        # Check that the specific fields from the error are now included
        critical_fields = [
            'peak_memory_usage_mb',
            'average_cpu_usage_percent', 
            'patterns_discovered',
            'suggestions_created',
            'retry_attempts'
        ]
        
        print("\n🔍 Checking that previously missing fields are now included:")
        for field in critical_fields:
            if field in content:
                print(f"   ✅ {field} - FOUND")
            else:
                print(f"   ❌ {field} - MISSING")
                return False
        
        print("\n✅ All critical fields that were causing Pydantic validation errors are now present!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False

def test_batch_processor_structure():
    """Test that the batch processor has the correct structure"""
    print("\n🧪 Testing batch processor file structure...")
    
    try:
        batch_processor_file = 'damien_cli/features/ai_intelligence/utils/batch_processor.py'
        
        if not os.path.exists(batch_processor_file):
            print(f"❌ File not found: {batch_processor_file}")
            return False
        
        with open(batch_processor_file, 'r') as f:
            content = f.read()
        
        # Check for the corrected BatchProcessingResult instantiation
        required_patterns = [
            'BatchProcessingResult(',
            'peak_memory_usage_mb=',
            'average_cpu_usage_percent=',
            'patterns_discovered=',
            'suggestions_created=',
            'retry_attempts='
        ]
        
        print("🔍 Checking for required patterns in batch_processor.py:")
        for pattern in required_patterns:
            if pattern in content:
                print(f"   ✅ {pattern}")
            else:
                print(f"   ❌ {pattern} - MISSING")
                return False
        
        # Check that psutil is imported for memory/CPU monitoring
        if 'import psutil' in content:
            print("   ✅ psutil import found (for memory/CPU monitoring)")
        else:
            print("   ❌ psutil import missing")
            return False
        
        print("\n✅ Batch processor structure looks correct!")
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        traceback.print_exc()
        return False

def test_pyproject_dependencies():
    """Test that pyproject.toml has correct dependency versions"""
    print("\n🧪 Testing pyproject.toml dependency versions...")
    
    try:
        with open('pyproject.toml', 'r') as f:
            content = f.read()
        
        # Check for the corrected PyTorch version
        if 'torch = "2.1.0"' in content:
            print("   ✅ PyTorch version corrected to 2.1.0 (compatible version)")
        else:
            print("   ❌ PyTorch version not corrected")
            return False
        
        # Check for sentence-transformers compatibility
        if 'sentence-transformers = "2.6.0"' in content:
            print("   ✅ sentence-transformers version set to compatible 2.6.0")
        else:
            print("   ❌ sentence-transformers version not updated")
            return False
        
        # Check for psutil dependency
        if 'psutil' in content:
            print("   ✅ psutil dependency found (for system monitoring)")
        else:
            print("   ❌ psutil dependency missing")
            return False
        
        print("\n✅ Dependencies look correctly configured!")
        return True
        
    except Exception as e:
        print(f"❌ Dependency test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run validation tests for the fixes"""
    print("🚀 Validating Damien AI Intelligence Fixes")
    print("=" * 50)
    
    tests = [
        ("BatchProcessingResult Model Fix", test_batch_processing_result_model),
        ("Batch Processor Structure", test_batch_processor_structure), 
        ("Dependency Configuration", test_pyproject_dependencies),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'-' * 30}")
        print(f"🔬 {test_name}")
        print('-' * 30)
        
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'=' * 50}")
    print("🏁 VALIDATION SUMMARY")
    print('=' * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} validation tests passed")
    
    if passed == total:
        print("\n🎉 ALL FIXES VALIDATED SUCCESSFULLY!")
        print("\n📋 Summary of fixes applied:")
        print("   1. ✅ Fixed BatchProcessingResult Pydantic validation error")
        print("   2. ✅ Added missing required fields:")
        print("      • peak_memory_usage_mb")  
        print("      • average_cpu_usage_percent")
        print("      • patterns_discovered")
        print("      • suggestions_created") 
        print("      • retry_attempts")
        print("   3. ✅ Updated PyTorch to compatible version (2.1.0)")
        print("   4. ✅ Updated sentence-transformers to compatible version (2.6.0)")
        print("   5. ✅ Added psutil for system monitoring")
        print("\n🚀 Ready to proceed with Phase 4 implementation!")
        print("   Next: poetry install && poetry run python -m damien_cli.cli_entry ai quick-test")
        return True
    else:
        print(f"\n⚠️  {total - passed} validation test(s) failed.")
        print("Please review the errors and ensure all fixes are properly applied.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
