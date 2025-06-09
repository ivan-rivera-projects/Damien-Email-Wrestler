#!/usr/bin/env python3
"""
Gmail Integration Test Script
Tests the new Gmail analyzer components step by step
"""

import sys
import os
import traceback
from datetime import datetime

# Add damien_cli to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_basic_imports():
    """Test if all components can be imported"""
    print("🧪 Testing Basic Imports...")
    
    try:
        from damien_cli.features.ai_intelligence.categorization.gmail_analyzer import GmailEmailAnalyzer
        print("   ✅ GmailEmailAnalyzer imported")
        
        from damien_cli.features.ai_intelligence.categorization.embeddings import EmailEmbeddingGenerator
        print("   ✅ EmailEmbeddingGenerator imported")
        
        from damien_cli.features.ai_intelligence.categorization.patterns import EmailPatternDetector
        print("   ✅ EmailPatternDetector imported")
        
        from damien_cli.features.ai_intelligence.utils.batch_processor import BatchEmailProcessor
        print("   ✅ BatchEmailProcessor imported")
        
        from damien_cli.features.ai_intelligence.utils.confidence_scorer import ConfidenceScorer
        print("   ✅ ConfidenceScorer imported")
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def test_component_initialization():
    """Test if components can be initialized"""
    print("\n🔧 Testing Component Initialization...")
    
    try:
        from damien_cli.features.ai_intelligence.categorization.gmail_analyzer import GmailEmailAnalyzer
        from damien_cli.features.ai_intelligence.categorization.embeddings import EmailEmbeddingGenerator
        from damien_cli.features.ai_intelligence.categorization.patterns import EmailPatternDetector
        
        # Test initialization
        analyzer = GmailEmailAnalyzer()
        print("   ✅ GmailEmailAnalyzer initialized")
        
        embedding_gen = EmailEmbeddingGenerator()
        print("   ✅ EmailEmbeddingGenerator initialized")
        
        pattern_detector = EmailPatternDetector()
        print("   ✅ EmailPatternDetector initialized")
        
        return True, (analyzer, embedding_gen, pattern_detector)
        
    except Exception as e:
        return False, str(e)

def test_embeddings_basic():
    """Test basic embedding functionality"""
    print("\n🧠 Testing Embedding Generation...")
    
    try:
        from damien_cli.features.ai_intelligence.categorization.embeddings import EmailEmbeddingGenerator
        
        embedding_gen = EmailEmbeddingGenerator()
        
        # Test with sample email data
        sample_email = {
            'id': 'test_123',
            'from_sender': 'newsletter@example.com',
            'subject': 'Weekly Newsletter - Tech Updates',
            'snippet': 'Here are the latest tech updates for this week...',
            'label_names': ['INBOX', 'UNREAD']
        }
        
        # Generate embedding
        embedding = embedding_gen.generate_embedding(sample_email)
        print(f"   ✅ Generated embedding with shape: {embedding.shape}")
        print(f"   ✅ Embedding dimension: {embedding_gen.embedding_dim}")
        
        # Test cache stats
        cache_stats = embedding_gen.get_cache_stats()
        print(f"   ✅ Cache stats: {cache_stats['cached_embeddings']} cached embeddings")
        
        return True, embedding
        
    except Exception as e:
        return False, str(e)

def test_pattern_detection_basic():
    """Test basic pattern detection"""
    print("\n🔍 Testing Pattern Detection...")
    
    try:
        from damien_cli.features.ai_intelligence.categorization.patterns import EmailPatternDetector
        import numpy as np
        
        pattern_detector = EmailPatternDetector()
        
        # Create sample email data
        sample_emails = [
            {
                'id': 'email_1',
                'from_sender': 'newsletter@techcorp.com',
                'subject': 'Weekly Tech Newsletter #1',
                'snippet': 'This week in tech news...',
                'label_names': ['INBOX'],
                'has_attachments': False,
                'size_estimate': 5000,
                'received_timestamp': 1704067200  # Jan 1, 2024
            },
            {
                'id': 'email_2', 
                'from_sender': 'newsletter@techcorp.com',
                'subject': 'Weekly Tech Newsletter #2',
                'snippet': 'Another week of tech updates...',
                'label_names': ['INBOX'],
                'has_attachments': False,
                'size_estimate': 5200,
                'received_timestamp': 1704672000  # Jan 8, 2024
            },
            {
                'id': 'email_3',
                'from_sender': 'orders@shop.com',
                'subject': 'Order Receipt #12345',
                'snippet': 'Thank you for your purchase...',
                'label_names': ['INBOX'],
                'has_attachments': True,
                'size_estimate': 15000,
                'received_timestamp': 1704758400  # Jan 9, 2024
            },
            {
                'id': 'email_4',
                'from_sender': 'orders@shop.com', 
                'subject': 'Order Receipt #12346',
                'snippet': 'Your order has been processed...',
                'label_names': ['INBOX'],
                'has_attachments': True,
                'size_estimate': 14500,
                'received_timestamp': 1704844800  # Jan 10, 2024
            }
        ]
        
        # Create mock embeddings
        embeddings = np.random.random((len(sample_emails), 384))
        
        # Detect patterns
        patterns = pattern_detector.detect_patterns(sample_emails, embeddings)
        
        print(f"   ✅ Detected {len(patterns)} patterns")
        for i, pattern in enumerate(patterns):
            print(f"   📊 Pattern {i+1}: {pattern.pattern_name}")
            print(f"      Type: {pattern.pattern_type.value}")
            print(f"      Emails: {pattern.email_count}")
            print(f"      Confidence: {pattern.confidence:.0%}")
        
        return True, patterns
        
    except Exception as e:
        return False, str(e)

def test_gmail_analyzer_mock():
    """Test Gmail analyzer with mock data"""
    print("\n📧 Testing Gmail Analyzer (Mock Mode)...")
    
    try:
        from damien_cli.features.ai_intelligence.categorization.gmail_analyzer import GmailEmailAnalyzer
        
        # Note: This will test without actual Gmail API calls
        analyzer = GmailEmailAnalyzer()
        
        print("   ✅ Gmail analyzer ready")
        print("   ⚠️  Note: Full testing requires Gmail API authentication")
        print("   💡 Use 'damien ai quick-test' with authenticated Gmail API")
        
        return True, analyzer
        
    except Exception as e:
        return False, str(e)

def main():
    """Run all tests"""
    print("🚀 Gmail Integration Test Suite")
    print("=" * 50)
    
    start_time = datetime.now()
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Basic imports
    success, result = test_basic_imports()
    if success:
        tests_passed += 1
        print("   🎉 All imports successful!")
    else:
        print(f"   ❌ Import failed: {result}")
        traceback.print_exc()
    
    # Test 2: Component initialization
    success, result = test_component_initialization()
    if success:
        tests_passed += 1
        print("   🎉 All components initialized!")
    else:
        print(f"   ❌ Initialization failed: {result}")
        traceback.print_exc()
    
    # Test 3: Embeddings
    success, result = test_embeddings_basic()
    if success:
        tests_passed += 1
        print("   🎉 Embeddings working!")
    else:
        print(f"   ❌ Embeddings failed: {result}")
        traceback.print_exc()
    
    # Test 4: Pattern detection
    success, result = test_pattern_detection_basic()
    if success:
        tests_passed += 1
        print("   🎉 Pattern detection working!")
    else:
        print(f"   ❌ Pattern detection failed: {result}")
        traceback.print_exc()
    
    # Test 5: Gmail analyzer
    success, result = test_gmail_analyzer_mock()
    if success:
        tests_passed += 1
        print("   🎉 Gmail analyzer ready!")
    else:
        print(f"   ❌ Gmail analyzer failed: {result}")
        traceback.print_exc()
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   ✅ Tests passed: {tests_passed}/{total_tests}")
    print(f"   ⏱️  Duration: {duration:.1f}s")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Gmail integration is ready!")
        print("\n🚀 Next steps:")
        print("   1. Authenticate Gmail API: damien auth")
        print("   2. Test with real data: damien ai quick-test")
        print("   3. Run full analysis: damien ai analyze")
        return 0
    else:
        print(f"❌ {total_tests - tests_passed} tests failed")
        print("💡 Check the error messages above for troubleshooting")
        return 1

if __name__ == "__main__":
    sys.exit(main())
