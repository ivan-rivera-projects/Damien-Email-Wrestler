#!/usr/bin/env python3
"""Test that Pydantic models work correctly with all required fields"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "damien_cli"))

def test_batch_processing_result():
    """Test BatchProcessingResult with all required fields"""
    
    try:
        from damien_cli.features.ai_intelligence.models import BatchProcessingResult
        
        # Test with all required fields (this previously failed)
        result = BatchProcessingResult(
            total_items=100,
            processed_successfully=95,
            failed_items=5,
            skipped_items=0,
            processing_time_seconds=10.5,
            throughput_per_second=9.0,
            peak_memory_usage_mb=128.5,        # Previously missing
            average_cpu_usage_percent=45.2,   # Previously missing
            patterns_discovered=3,             # Previously missing
            suggestions_created=2,             # Previously missing
            retry_attempts=0,                  # Previously missing
            embeddings_generated=95,
            batch_size=10,
            parallel_workers=1
        )
        
        # Test computed properties
        success_rate = result.success_rate
        error_rate = result.error_rate
        
        print(f"✅ BatchProcessingResult: Created successfully")
        print(f"   📊 Success rate: {success_rate}%")
        print(f"   📊 Error rate: {error_rate}%")
        
        # Test error adding
        result.add_error("test_error", "Test error message", "item_123")
        print(f"   📋 Error tracking: {len(result.errors)} errors recorded")
        
        return True
        
    except Exception as e:
        print(f"❌ BatchProcessingResult test failed: {e}")
        return False

def test_email_analysis_result():
    """Test EmailAnalysisResult model"""
    
    try:
        from damien_cli.features.ai_intelligence.models import (
            EmailAnalysisResult, PerformanceMetrics
        )
        
        # Create start and end time
        start_time = datetime.now()
        end_time = datetime.now()
        
        # Create performance metrics
        perf_metrics = PerformanceMetrics(
            operation_name="test_analysis",
            start_time=start_time,
            end_time=end_time,
            items_processed=100
        )
        
        # Create analysis result
        analysis = EmailAnalysisResult(
            total_emails_analyzed=100,
            processing_performance=perf_metrics,
            estimated_total_time_savings=10.0
        )
        
        print(f"✅ EmailAnalysisResult: Created successfully")
        print(f"   📧 Emails analyzed: {analysis.total_emails_analyzed}")
        
        return True
        
    except Exception as e:
        print(f"❌ EmailAnalysisResult test failed: {e}")
        return False

def main():
    """Run all model validation tests"""
    
    print("🧪 Testing Model Validation")
    print("=" * 40)
    
    tests = [
        ("BatchProcessingResult", test_batch_processing_result),
        ("EmailAnalysisResult", test_email_analysis_result),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Testing {test_name}:")
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n📊 Model Validation Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All models validated successfully!")
        return True
    else:
        print("⚠️ Some model tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
