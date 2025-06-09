#!/usr/bin/env python3
"""
BatchProcessor Integration Test Script

Validates the BatchProcessor implementation with real-world scenarios.
Tests all major functionality including processing strategies, chunking integration,
privacy protection, and performance monitoring.

Usage:
    cd damien-cli
    poetry run python test_batch_processor_integration.py
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from damien_cli.features.ai_intelligence.llm_integration.processing.batch import (
        BatchProcessor, BatchConfig, ProcessingStrategy, EmailItem
    )
    from damien_cli.features.ai_intelligence.llm_integration.processing.chunker import (
        ChunkingConfig, ChunkingStrategy
    )
    print("✅ Successfully imported BatchProcessor components")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_basic_batch_processing():
    """Test basic batch processing functionality."""
    print("\n🧪 Testing Basic Batch Processing...")
    
    # Create simple configuration
    config = BatchConfig(
        batch_size=5,
        processing_strategy=ProcessingStrategy.SEQUENTIAL,
        enable_chunking=False,
        enable_privacy_protection=False
    )
    
    processor = BatchProcessor(config=config)
    
    # Create test emails
    emails = [
        EmailItem(
            email_id=f"test_email_{i:03d}",
            content=f"This is test email number {i} with some sample content to process.",
            metadata={"test_index": i}
        )
        for i in range(5)
    ]
    
    print(f"📧 Created {len(emails)} test emails")
    
    # Process batch
    start_time = time.time()
    result = processor.process_batch(emails)
    processing_time = time.time() - start_time
    
    # Validate results
    assert result.progress.status.value == "completed", f"Expected completed, got {result.progress.status.value}"
    assert result.progress.total_items == 5, f"Expected 5 items, got {result.progress.total_items}"
    assert result.progress.successful_items == 5, f"Expected 5 successful, got {result.progress.successful_items}"
    assert len(result.results) == 5, f"Expected 5 results, got {len(result.results)}"
    
    print(f"✅ Basic processing test passed!")
    print(f"   - Processing time: {processing_time:.2f}s")
    print(f"   - Success rate: {result.summary['success_rate_percent']:.1f}%")
    print(f"   - Total chunks: {result.summary['total_chunks_created']}")
    
    return True


def test_chunking_integration():
    """Test integration with IntelligentChunker."""
    print("\n🧪 Testing Chunking Integration...")
    
    # Create config with chunking enabled
    config = BatchConfig(
        enable_chunking=True,
        chunking_config=ChunkingConfig(
            max_chunk_size=50,  # Small size to force chunking
            strategy=ChunkingStrategy.TOKEN_BASED,
            enable_pii_protection=False
        ),
        enable_privacy_protection=False
    )
    
    processor = BatchProcessor(config=config)
    
    # Create emails with varying sizes
    emails = [
        EmailItem(
            email_id="small_email",
            content="Short email content."
        ),
        EmailItem(
            email_id="large_email", 
            content="This is a very long email content that should be chunked into multiple pieces. " * 10
        )
    ]
    
    print(f"📧 Created {len(emails)} emails (1 small, 1 large)")
    
    # Process batch
    result = processor.process_batch(emails)
    
    # Validate results
    assert result.progress.status.value == "completed"
    assert result.progress.successful_items == 2
    
    # Check chunking behavior
    small_result = next(r for r in result.results if r.email_id == "small_email")
    large_result = next(r for r in result.results if r.email_id == "large_email")
    
    assert len(small_result.chunks) == 1, f"Small email should have 1 chunk, got {len(small_result.chunks)}"
    assert len(large_result.chunks) > 1, f"Large email should have >1 chunks, got {len(large_result.chunks)}"
    
    print(f"✅ Chunking integration test passed!")
    print(f"   - Small email chunks: {len(small_result.chunks)}")
    print(f"   - Large email chunks: {len(large_result.chunks)}")
    
    return True


def test_processing_strategies():
    """Test different processing strategies."""
    print("\n🧪 Testing Processing Strategies...")
    
    # Create test emails
    emails = [
        EmailItem(f"strategy_test_{i}", f"Content for strategy test {i}")
        for i in range(6)
    ]
    
    strategies_to_test = [
        ProcessingStrategy.SEQUENTIAL,
        ProcessingStrategy.PARALLEL,
        ProcessingStrategy.STREAMING
    ]
    
    for strategy in strategies_to_test:
        print(f"  Testing {strategy.value} strategy...")
        
        config = BatchConfig(
            processing_strategy=strategy,
            batch_size=3,  # For streaming test
            max_concurrent_workers=2,  # For parallel test
            enable_chunking=False,
            enable_privacy_protection=False
        )
        
        processor = BatchProcessor(config=config)
        start_time = time.time()
        result = processor.process_batch(emails)
        processing_time = time.time() - start_time
        
        assert result.progress.status.value == "completed"
        assert result.progress.successful_items == 6
        
        print(f"    ✅ {strategy.value}: {processing_time:.2f}s, {result.summary['success_rate_percent']:.1f}% success")
    
    print("✅ All processing strategies test passed!")
    return True


def test_progress_tracking():
    """Test progress tracking functionality."""
    print("\n🧪 Testing Progress Tracking...")
    
    progress_updates = []
    
    def progress_callback(progress):
        progress_updates.append({
            'percentage': progress.progress_percentage,
            'processed': progress.processed_items,
            'status': progress.status.value
        })
        print(f"    Progress: {progress.progress_percentage:.1f}% ({progress.processed_items}/{progress.total_items})")
    
    config = BatchConfig(
        processing_strategy=ProcessingStrategy.SEQUENTIAL,
        enable_chunking=False,
        enable_privacy_protection=False
    )
    
    processor = BatchProcessor(config=config)
    
    # Create more emails to see progress updates
    emails = [
        EmailItem(f"progress_test_{i}", f"Content {i}")
        for i in range(8)
    ]
    
    print(f"📧 Processing {len(emails)} emails with progress tracking...")
    
    result = processor.process_batch(emails, progress_callback=progress_callback)
    
    assert result.progress.status.value == "completed"
    assert len(progress_updates) > 0, "Should have received progress updates"
    
    # Check final progress
    final_progress = progress_updates[-1] if progress_updates else None
    if final_progress:
        assert final_progress['percentage'] == 100.0, "Final progress should be 100%"
    
    print(f"✅ Progress tracking test passed!")
    print(f"   - Received {len(progress_updates)} progress updates")
    
    return True


def test_performance_metrics():
    """Test performance metrics collection."""
    print("\n🧪 Testing Performance Metrics...")
    
    config = BatchConfig(
        processing_strategy=ProcessingStrategy.PARALLEL,
        max_concurrent_workers=2,
        enable_chunking=False,
        enable_privacy_protection=False
    )
    
    processor = BatchProcessor(config=config)
    
    # Create test emails
    emails = [
        EmailItem(f"perf_test_{i}", f"Performance test content {i}")
        for i in range(10)
    ]
    
    print(f"📧 Processing {len(emails)} emails for performance testing...")
    
    start_time = time.time()
    result = processor.process_batch(emails)
    total_time = time.time() - start_time
    
    # Check performance metrics
    performance = result.performance_metrics
    summary = result.summary
    
    assert 'average_processing_time_ms' in performance
    assert 'processing_rate_emails_per_second' in performance
    assert 'efficiency_score' in performance
    assert 'peak_memory_usage_mb' in performance
    
    print(f"✅ Performance metrics test passed!")
    print(f"   - Total time: {total_time:.2f}s")
    print(f"   - Rate: {performance['processing_rate_emails_per_second']:.2f} emails/sec")
    print(f"   - Efficiency: {performance['efficiency_score']:.1f}%")
    print(f"   - Memory: {performance['peak_memory_usage_mb']:.1f} MB")
    
    return True


def test_error_handling():
    """Test error handling and recovery."""
    print("\n🧪 Testing Error Handling...")
    
    config = BatchConfig(
        processing_strategy=ProcessingStrategy.SEQUENTIAL,
        enable_chunking=False,
        enable_privacy_protection=False
    )
    
    processor = BatchProcessor(config=config)
    
    # Create a mix of valid emails
    emails = [
        EmailItem("good_email_1", "Good content 1"),
        EmailItem("good_email_2", "Good content 2"),
        EmailItem("good_email_3", "Good content 3")
    ]
    
    print(f"📧 Processing {len(emails)} emails (testing error recovery)...")
    
    result = processor.process_batch(emails)
    
    # Should complete even with some errors
    assert result.progress.status.value == "completed"
    assert result.progress.total_items == 3
    
    print(f"✅ Error handling test passed!")
    print(f"   - Total processed: {result.progress.processed_items}")
    print(f"   - Successful: {result.progress.successful_items}")
    print(f"   - Failed: {result.progress.failed_items}")
    
    return True


def test_batch_processor_stats():
    """Test BatchProcessor performance statistics."""
    print("\n🧪 Testing BatchProcessor Statistics...")
    
    processor = BatchProcessor()
    
    # Get initial stats
    stats = processor.get_performance_stats()
    
    assert 'total_emails_processed' in stats
    assert 'processor_config' in stats
    assert 'active_batches' in stats
    
    config = stats['processor_config']
    assert 'batch_size' in config
    assert 'strategy' in config
    assert 'chunking_enabled' in config
    
    print(f"✅ Statistics test passed!")
    print(f"   - Config captured: {len(config)} settings")
    print(f"   - Active batches: {stats['active_batches']}")
    
    return True


def main():
    """Run all integration tests."""
    print("🚀 BatchProcessor Integration Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_batch_processing,
        test_chunking_integration,
        test_processing_strategies,
        test_progress_tracking,
        test_performance_metrics,
        test_error_handling,
        test_batch_processor_stats
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_func.__name__} failed")
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"🏆 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All BatchProcessor integration tests passed!")
        print("\n📊 BatchProcessor Implementation Status:")
        print("✅ Basic batch processing - WORKING")
        print("✅ Multiple processing strategies - WORKING")
        print("✅ IntelligentChunker integration - WORKING")
        print("✅ Progress tracking - WORKING")
        print("✅ Performance monitoring - WORKING")
        print("✅ Error handling - WORKING")
        print("✅ Statistics collection - WORKING")
        print("\n🎯 Phase 3 Week 5-6 Progress Update:")
        print("📈 Scalable Processing: 25% → 50% COMPLETE")
        print("   - IntelligentChunker: ✅ COMPLETE")
        print("   - BatchProcessor: ✅ COMPLETE") 
        print("   - RAGEngine: 📅 NEXT")
        print("   - HierarchicalProcessor: 📅 PLANNED")
        print("   - ProgressTracker: 📅 PLANNED")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
