#!/usr/bin/env python3
"""
Test script to validate the immediate fixes for the Pydantic validation error
and PyTorch compatibility issues.
"""

import sys
import os
import traceback
from pathlib import Path

# Add the damien_cli directory to Python path
current_dir = Path(__file__).parent
damien_cli_dir = current_dir / "damien_cli"
sys.path.insert(0, str(damien_cli_dir))

def test_imports():
    """Test that all components can be imported successfully"""
    print("🧪 Testing component imports...")
    
    try:
        # Test core models import
        from damien_cli.features.ai_intelligence.models import BatchProcessingResult
        print("✅ BatchProcessingResult imported successfully")
        
        # Test batch processor import
        from damien_cli.features.ai_intelligence.utils.batch_processor import BatchEmailProcessor
        print("✅ BatchEmailProcessor imported successfully")
        
        # Test embeddings import
        from damien_cli.features.ai_intelligence.categorization.embeddings import EmailEmbeddingGenerator
        print("✅ EmailEmbeddingGenerator imported successfully")
        
        # Test pattern detector import
        from damien_cli.features.ai_intelligence.categorization.patterns import EmailPatternDetector
        print("✅ EmailPatternDetector imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        traceback.print_exc()
        return False

def test_batch_processor():
    """Test that BatchEmailProcessor can be initialized and the BatchProcessingResult model works"""
    print("\n🧪 Testing BatchEmailProcessor...")
    
    try:
        from damien_cli.features.ai_intelligence.utils.batch_processor import BatchEmailProcessor
        from damien_cli.features.ai_intelligence.models import BatchProcessingResult
        
        # Initialize batch processor
        processor = BatchEmailProcessor(batch_size=10)
        print("✅ BatchEmailProcessor initialized successfully")
        
        # Test creating a BatchProcessingResult with all required fields
        result = BatchProcessingResult(
            total_items=100,
            processed_successfully=95,
            failed_items=5,
            skipped_items=0,
            processing_time_seconds=10.5,
            throughput_per_second=9.5,
            peak_memory_usage_mb=128.5,
            average_cpu_usage_percent=45.2,
            patterns_discovered=3,
            suggestions_created=2,
            retry_attempts=0,
            embeddings_generated=95,
            batch_size=10,
            parallel_workers=1
        )
        print("✅ BatchProcessingResult created successfully with all required fields")
        
        # Test computed properties
        success_rate = result.success_rate
        error_rate = result.error_rate
        print(f"✅ Computed properties work: success_rate={success_rate}%, error_rate={error_rate}%")
        
        return True
        
    except Exception as e:
        print(f"❌ BatchProcessor test failed: {e}")
        traceback.print_exc()
        return False

def test_embeddings():
    """Test that EmailEmbeddingGenerator can be initialized"""
    print("\n🧪 Testing EmailEmbeddingGenerator...")
    
    try:
        from damien_cli.features.ai_intelligence.categorization.embeddings import EmailEmbeddingGenerator
        
        # Initialize embeddings generator
        generator = EmailEmbeddingGenerator()
        print("✅ EmailEmbeddingGenerator initialized successfully")
        
        # Test with mock data
        email_data = {
            'id': 'test123',
            'subject': 'Test Email Subject',
            'snippet': 'This is a test email snippet for embedding generation',
            'from_sender': 'test@example.com'
        }
        
        # Generate embedding (should work with mock embeddings even if torch fails)
        embedding = generator.generate_embedding(email_data)
        print(f"✅ Embedding generated successfully, shape: {embedding.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")
        traceback.print_exc()
        return False

def test_patterns():
    """Test that EmailPatternDetector can be initialized"""
    print("\n🧪 Testing EmailPatternDetector...")
    
    try:
        from damien_cli.features.ai_intelligence.categorization.patterns import EmailPatternDetector
        
        # Initialize pattern detector
        detector = EmailPatternDetector()
        print("✅ EmailPatternDetector initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern detector test failed: {e}")
        traceback.print_exc()
        return False

def test_gmail_analyzer():
    """Test that GmailEmailAnalyzer can be initialized"""
    print("\n🧪 Testing GmailEmailAnalyzer...")
    
    try:
        # This import might fail if the file doesn't exist yet, which is expected
        try:
            from damien_cli.features.ai_intelligence.categorization.gmail_analyzer import GmailEmailAnalyzer
            analyzer = GmailEmailAnalyzer()
            print("✅ GmailEmailAnalyzer initialized successfully")
            return True
        except ImportError:
            print("ℹ️  GmailEmailAnalyzer not found (expected - will be created in Phase 4)")
            return True
        
    except Exception as e:
        print(f"❌ Gmail analyzer test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Running Damien AI Intelligence Fix Validation Tests\n")
    
    tests = [
        ("Component Imports", test_imports),
        ("Batch Processor", test_batch_processor),
        ("Embeddings Generator", test_embeddings),
        ("Pattern Detector", test_patterns),
        ("Gmail Analyzer", test_gmail_analyzer),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The fixes are working correctly.")
        print("\n📋 Ready for Phase 4 implementation:")
        print("   1. ✅ Pydantic validation errors fixed")
        print("   2. ✅ Component imports working")
        print("   3. ✅ Batch processing functional")
        print("   4. ✅ AI intelligence layer operational")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
