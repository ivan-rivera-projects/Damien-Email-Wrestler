#!/usr/bin/env python3
"""Test that all AI intelligence components can be imported and initialized"""

import sys
from pathlib import Path

# Add damien_cli to path
sys.path.insert(0, str(Path(__file__).parent / "damien_cli"))

def test_all_imports():
    """Test importing all core AI components"""
    
    tests = [
        # Core models
        ("BatchProcessingResult", "damien_cli.features.ai_intelligence.models", "BatchProcessingResult"),
        ("EmailAnalysisResult", "damien_cli.features.ai_intelligence.models", "EmailAnalysisResult"),
        ("EmailPattern", "damien_cli.features.ai_intelligence.models", "EmailPattern"),
        ("CategorySuggestion", "damien_cli.features.ai_intelligence.models", "CategorySuggestion"),
        
        # Core processors
        ("GmailEmailAnalyzer", "damien_cli.features.ai_intelligence.categorization.gmail_analyzer", "GmailEmailAnalyzer"),
        ("EmailEmbeddingGenerator", "damien_cli.features.ai_intelligence.categorization.embeddings", "EmailEmbeddingGenerator"),
        ("EmailPatternDetector", "damien_cli.features.ai_intelligence.categorization.patterns", "EmailPatternDetector"),
        ("BatchEmailProcessor", "damien_cli.features.ai_intelligence.utils.batch_processor", "BatchEmailProcessor"),
        ("ConfidenceScorer", "damien_cli.features.ai_intelligence.utils.confidence_scorer", "ConfidenceScorer"),
    ]
    
    results = []
    
    for test_name, module_path, class_name in tests:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            
            # Try to instantiate (with minimal args if needed)
            if class_name == "GmailEmailAnalyzer":
                instance = cls(gmail_service=None)  # Allow None for testing
            elif class_name == "BatchProcessingResult":
                instance = cls(
                    total_items=1, 
                    processed_successfully=1, 
                    failed_items=0,
                    skipped_items=0, 
                    processing_time_seconds=1.0, 
                    throughput_per_second=1.0,
                    peak_memory_usage_mb=1.0, 
                    average_cpu_usage_percent=1.0,
                    patterns_discovered=0, 
                    suggestions_created=0, 
                    retry_attempts=0,
                    embeddings_generated=0, 
                    batch_size=1, 
                    parallel_workers=1
                )
            elif class_name == "EmailAnalysisResult":
                from datetime import datetime
                from damien_cli.features.ai_intelligence.models import PerformanceMetrics
                perf_metrics = PerformanceMetrics(
                    operation_name="test_analysis",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    items_processed=100
                )
                instance = cls(
                    total_emails_analyzed=100,
                    processing_performance=perf_metrics,
                    estimated_total_time_savings=10.0
                )
            elif class_name == "EmailPattern":
                from damien_cli.features.ai_intelligence.models import PatternCharacteristics
                chars = PatternCharacteristics(
                    primary_feature="sender",
                    secondary_features=["subject"],
                    statistical_measures={"mean": 5.0, "std_dev": 1.0}
                )
                instance = cls(
                    pattern_type="sender",
                    pattern_name="Test Pattern",
                    description="Test description",
                    email_count=10,
                    total_email_universe=100,
                    prevalence_rate=0.1,
                    confidence=0.8,
                    confidence_level="high",
                    characteristics=chars
                )
            elif class_name == "CategorySuggestion":
                # We need to create proper RuleCondition and RuleAction objects
                from damien_cli.features.ai_intelligence.models import RuleCondition, RuleAction
                
                rule_condition = RuleCondition(
                    field="from_sender",
                    operator="contains",
                    value="newsletter",
                    case_sensitive=False
                )
                
                rule_action = RuleAction(
                    action_type="archive",
                    parameters={"param1": "value1"}
                )
                
                instance = cls(
                    category_name="Test Category",
                    description="Test description",
                    email_count=10,
                    affected_email_percentage=10.0,
                    estimated_time_savings_minutes=5.0,
                    confidence=0.8,
                    confidence_level="high",
                    rule_conditions=[rule_condition],
                    rule_actions=[rule_action],
                    rule_complexity="simple"
                )
            else:
                instance = cls()
            
            print(f"✅ {test_name}: Import and instantiation successful")
            results.append((test_name, True, None))
            
        except Exception as e:
            print(f"❌ {test_name}: Failed - {str(e)}")
            results.append((test_name, False, str(e)))
    
    # Summary
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"\n📊 Component Import Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All components imported successfully!")
        return True
    else:
        print("⚠️ Some components failed to import.")
        for test_name, success, error in results:
            if not success:
                print(f"   ❌ {test_name}: {error}")
        return False

if __name__ == "__main__":
    success = test_all_imports()
    sys.exit(0 if success else 1)
