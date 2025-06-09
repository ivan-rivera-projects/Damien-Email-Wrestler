#!/usr/bin/env python3
"""
Integration validation script for Intelligence Router foundation.

This script tests the Intelligence Router components to ensure they work
correctly and integrate with the existing email management pipeline.

Run with: poetry run python test_router_integration.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all router components can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from damien_cli.features.ai_intelligence.llm_integration.routing import (
            IntelligenceRouter, MLComplexityAnalyzer, CostPredictor,
            PerformancePredictor, PipelineSelector, AdaptiveLearningEngine
        )
        print("✅ All routing components imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_component_initialization():
    """Test that all components initialize correctly."""
    print("🔍 Testing component initialization...")
    
    try:
        from damien_cli.features.ai_intelligence.llm_integration.routing import (
            IntelligenceRouter, MLComplexityAnalyzer, CostPredictor,
            PerformancePredictor, PipelineSelector, AdaptiveLearningEngine
        )
        
        # Initialize each component
        analyzer = MLComplexityAnalyzer()
        cost_predictor = CostPredictor()
        performance_predictor = PerformancePredictor()
        pipeline_selector = PipelineSelector()
        learning_engine = AdaptiveLearningEngine()
        router = IntelligenceRouter()
        
        print("✅ All components initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

async def test_complexity_analysis():
    """Test complexity analysis functionality."""
    print("🔍 Testing complexity analysis...")
    
    try:
        from damien_cli.features.ai_intelligence.llm_integration.routing import MLComplexityAnalyzer
        
        analyzer = MLComplexityAnalyzer()
        
        # Test simple email
        simple_email = {
            "subject": "Hello",
            "body": "Just saying hi!"
        }
        
        score = await analyzer.analyze(simple_email, "categorization")
        
        assert score is not None
        assert 0.0 <= score.overall_score <= 1.0
        assert 0.0 <= score.confidence <= 1.0
        assert score.features.word_count > 0
        
        print(f"✅ Complexity analysis working - Score: {score.overall_score:.2f}, Confidence: {score.confidence:.2f}")
        return True
    except Exception as e:
        print(f"❌ Complexity analysis error: {e}")
        return False

def test_pipeline_selection():
    """Test pipeline selection functionality."""
    print("🔍 Testing pipeline selection...")
    
    try:
        from damien_cli.features.ai_intelligence.llm_integration.routing import PipelineSelector
        from damien_cli.features.ai_intelligence.llm_integration.routing.selector import ProcessingPipeline
        
        selector = PipelineSelector()
        
        # Test getting available pipelines
        pipelines = selector.get_available_pipelines()
        assert len(pipelines) > 0
        assert all(isinstance(p, ProcessingPipeline) for p in pipelines)
        
        # Test pipeline recommendation
        recommended = selector.get_recommended_pipeline_for_task("categorization")
        assert isinstance(recommended, ProcessingPipeline)
        
        print(f"✅ Pipeline selection working - {len(pipelines)} pipelines available")
        print(f"   Recommended for categorization: {recommended.value}")
        return True
    except Exception as e:
        print(f"❌ Pipeline selection error: {e}")
        return False

def test_cost_prediction():
    """Test cost prediction functionality."""
    print("🔍 Testing cost prediction...")
    
    try:
        from damien_cli.features.ai_intelligence.llm_integration.routing import CostPredictor
        from damien_cli.features.ai_intelligence.llm_integration.routing.selector import ProcessingPipeline
        
        predictor = CostPredictor()
        
        email_data = {"subject": "Test", "body": "Test email for cost prediction"}
        
        # Create a mock complexity score
        complexity_score = type('MockComplexityScore', (), {
            'overall_score': 0.5,
            'confidence': 0.8
        })()
        
        # Test cost prediction for different pipelines
        embedding_cost = predictor.predict_cost(
            email_data, ProcessingPipeline.EMBEDDING_ONLY, complexity_score
        )
        llm_cost = predictor.predict_cost(
            email_data, ProcessingPipeline.LLM_ONLY, complexity_score
        )
        
        assert embedding_cost > 0
        assert llm_cost > 0
        assert llm_cost > embedding_cost  # LLM should be more expensive
        
        print(f"✅ Cost prediction working - Embedding: ${embedding_cost:.4f}, LLM: ${llm_cost:.4f}")
        return True
    except Exception as e:
        print(f"❌ Cost prediction error: {e}")
        return False

async def test_end_to_end_routing():
    """Test complete end-to-end routing functionality."""
    print("🔍 Testing end-to-end routing...")
    
    try:
        from damien_cli.features.ai_intelligence.llm_integration.routing import IntelligenceRouter
        from damien_cli.features.ai_intelligence.llm_integration.routing.router import (
            ProcessingTask, Constraints, RoutingStrategy
        )
        
        router = IntelligenceRouter()
        
        # Create a test task
        task = ProcessingTask(
            email_data={
                "subject": "Meeting Tomorrow",
                "body": "Hi team, let's meet tomorrow at 2 PM for the project review.",
                "from": "manager@company.com"
            },
            task_type="categorization"
        )
        
        # Create constraints
        constraints = Constraints(
            max_cost=0.01,
            max_time=1.0,
            strategy=RoutingStrategy.BALANCED
        )
        
        # Make routing decision
        start_time = time.time()
        decision = await router.route(task, constraints)
        routing_time = time.time() - start_time
        
        # Validate decision
        assert decision is not None
        assert decision.estimated_cost > 0
        assert decision.estimated_time > 0
        assert 0.0 <= decision.confidence <= 1.0
        assert decision.reasoning is not None
        
        print(f"✅ End-to-end routing working:")
        print(f"   Pipeline: {decision.pipeline.value}")
        print(f"   Cost: ${decision.estimated_cost:.4f}")
        print(f"   Time: {decision.estimated_time:.3f}s")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Routing time: {routing_time:.3f}s")
        print(f"   Reasoning: {decision.reasoning}")
        
        return True
    except Exception as e:
        print(f"❌ End-to-end routing error: {e}")
        return False

def test_learning_engine():
    """Test adaptive learning engine functionality."""
    print("🔍 Testing learning engine...")
    
    try:
        from damien_cli.features.ai_intelligence.llm_integration.routing import AdaptiveLearningEngine
        from damien_cli.features.ai_intelligence.llm_integration.routing.learning import RoutingOutcome
        from damien_cli.features.ai_intelligence.llm_integration.routing.selector import ProcessingPipeline
        
        engine = AdaptiveLearningEngine()
        
        # Test recording an outcome
        decision = {
            'pipeline': ProcessingPipeline.EMBEDDING_ONLY.value,
            'estimated_cost': 0.001,
            'estimated_time': 0.05
        }
        
        outcome = RoutingOutcome(
            decision_id="test_001",
            pipeline_used=ProcessingPipeline.EMBEDDING_ONLY.value,
            actual_cost=0.0012,
            actual_time=0.048,
            actual_quality=0.85,
            success=True
        )
        
        engine.record_outcome(decision, outcome)
        
        # Test getting metrics
        metrics = engine.get_learning_metrics()
        assert metrics is not None
        
        # Test getting insights
        insights = engine.get_pattern_insights()
        assert isinstance(insights, dict)
        
        print("✅ Learning engine working - outcome recorded and metrics available")
        return True
    except Exception as e:
        print(f"❌ Learning engine error: {e}")
        return False

async def main():
    """Run all integration tests."""
    print("🚀 Intelligence Router Foundation Integration Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Initialization Test", test_component_initialization),
        ("Complexity Analysis", test_complexity_analysis),
        ("Pipeline Selection", test_pipeline_selection),
        ("Cost Prediction", test_cost_prediction),
        ("End-to-End Routing", test_end_to_end_routing),
        ("Learning Engine", test_learning_engine)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nSUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Intelligence Router foundation is ready!")
        print("\n📋 Next steps:")
        print("   1. The routing system foundation is complete")
        print("   2. All components are working and integrated")
        print("   3. Ready for advanced ML model training")
        print("   4. Ready for production infrastructure setup")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
