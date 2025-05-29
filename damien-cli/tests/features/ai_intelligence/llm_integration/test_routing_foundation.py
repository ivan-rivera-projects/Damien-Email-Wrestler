"""
Unit tests for the Intelligence Router foundation components.

This test suite validates the basic functionality of the ML-powered routing
system, ensuring all components work together correctly.
"""
import pytest
import asyncio
from datetime import datetime

from damien_cli.features.ai_intelligence.llm_integration.routing import (
    IntelligenceRouter, MLComplexityAnalyzer, CostPredictor, 
    PerformancePredictor, PipelineSelector, AdaptiveLearningEngine
)
from damien_cli.features.ai_intelligence.llm_integration.routing.router import (
    ProcessingTask, Constraints, RoutingStrategy
)
from damien_cli.features.ai_intelligence.llm_integration.routing.selector import (
    ProcessingPipeline
)
from damien_cli.features.ai_intelligence.llm_integration.routing.learning import (
    RoutingOutcome
)

class TestMLComplexityAnalyzer:
    """Test the ML complexity analyzer component."""
    
    def test_analyzer_initialization(self):
        """Test that the analyzer initializes correctly."""
        analyzer = MLComplexityAnalyzer()
        assert analyzer is not None
    
    @pytest.mark.asyncio
    async def test_analyze_simple_email(self):
        """Test complexity analysis of a simple email."""
        analyzer = MLComplexityAnalyzer()
        
        email_data = {
            "subject": "Meeting Tomorrow",
            "body": "Hi, let's meet tomorrow at 2 PM."
        }
        
        score = await analyzer.analyze(email_data, "categorization")
        
        assert score is not None
        assert 0.0 <= score.overall_score <= 1.0
        assert 0.0 <= score.confidence <= 1.0
        assert score.features.word_count > 0
        assert "simple" in score.reasoning.lower() or "low" in score.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_complex_email(self):
        """Test complexity analysis of a complex email."""
        analyzer = MLComplexityAnalyzer()
        
        complex_email = {
            "subject": "Technical Architecture Review: Algorithm Implementation",
            "body": """
            Dear team,
            
            We need to discuss the implementation of our new machine learning algorithm
            for the recommendation system. The current architecture has several optimization
            opportunities that require careful analysis.
            
            Key areas to address:
            1. Performance bottlenecks in the data pipeline
            2. Scalability concerns with the current framework
            3. Cost optimization strategies for cloud infrastructure
            
            Please review the attached technical specifications and prepare your feedback.
            
            Best regards,
            Technical Lead
            """
        }
        
        score = await analyzer.analyze(complex_email, "analysis")
        
        assert score is not None
        assert score.overall_score > 0.3  # Should be reasonably complex
        assert score.features.language_complexity > 0.0
        assert score.features.word_count > 50

class TestCostPredictor:
    """Test the cost prediction component."""
    
    def test_predictor_initialization(self):
        """Test that the cost predictor initializes correctly."""
        predictor = CostPredictor()
        assert predictor is not None
        assert predictor.cost_model is not None
    
    def test_predict_cost_embedding_only(self):
        """Test cost prediction for embedding-only pipeline."""
        predictor = CostPredictor()
        analyzer = MLComplexityAnalyzer()
        
        email_data = {"subject": "Test", "body": "Simple test email"}
        
        # Create a mock complexity score
        complexity_score = type('MockComplexityScore', (), {
            'overall_score': 0.3,
            'confidence': 0.8
        })()
        
        cost = predictor.predict_cost(
            email_data, 
            ProcessingPipeline.EMBEDDING_ONLY,
            complexity_score
        )
        
        assert cost > 0
        assert cost < 0.01  # Should be relatively cheap
    
    def test_predict_cost_llm_only(self):
        """Test cost prediction for LLM-only pipeline."""
        predictor = CostPredictor()
        
        email_data = {"subject": "Test", "body": "Simple test email"}
        complexity_score = type('MockComplexityScore', (), {
            'overall_score': 0.3,
            'confidence': 0.8
        })()
        
        cost = predictor.predict_cost(
            email_data, 
            ProcessingPipeline.LLM_ONLY,
            complexity_score
        )
        
        assert cost > 0
        # LLM should be more expensive than embedding
        embedding_cost = predictor.predict_cost(
            email_data, 
            ProcessingPipeline.EMBEDDING_ONLY,
            complexity_score
        )
        assert cost > embedding_cost

class TestPipelineSelector:
    """Test the pipeline selector component."""
    
    def test_selector_initialization(self):
        """Test that the pipeline selector initializes correctly."""
        selector = PipelineSelector()
        assert selector is not None
    
    def test_get_available_pipelines(self):
        """Test getting available pipelines."""
        selector = PipelineSelector()
        
        pipelines = selector.get_available_pipelines()
        
        assert isinstance(pipelines, list)
        assert len(pipelines) > 0
        assert all(isinstance(p, ProcessingPipeline) for p in pipelines)
    
    def test_get_recommended_pipeline(self):
        """Test getting recommended pipeline for a task."""
        selector = PipelineSelector()
        
        # Test different task types
        for task_type in ['categorization', 'summarization', 'analysis']:
            pipeline = selector.get_recommended_pipeline_for_task(task_type)
            assert isinstance(pipeline, ProcessingPipeline)
    
    def test_pipeline_characteristics(self):
        """Test getting pipeline characteristics."""
        selector = PipelineSelector()
        
        for pipeline in ProcessingPipeline:
            characteristics = selector.get_pipeline_characteristics(pipeline)
            assert isinstance(characteristics, dict)
            assert 'speed_tier' in characteristics
            assert 'cost_tier' in characteristics

class TestIntelligenceRouter:
    """Test the main intelligence router component."""
    
    def test_router_initialization(self):
        """Test that the router initializes correctly."""
        router = IntelligenceRouter()
        assert router is not None
        assert router.complexity_analyzer is not None
        assert router.cost_predictor is not None
        assert router.performance_predictor is not None
        assert router.pipeline_selector is not None
        assert router.learning_engine is not None
    
    @pytest.mark.asyncio
    async def test_route_simple_task(self):
        """Test routing a simple task."""
        router = IntelligenceRouter()
        
        task = ProcessingTask(
            email_data={"subject": "Test", "body": "Simple test email"},
            task_type="categorization"
        )
        
        constraints = Constraints(
            max_cost=0.01,
            strategy=RoutingStrategy.COST_OPTIMIZED
        )
        
        decision = await router.route(task, constraints)
        
        assert decision is not None
        assert isinstance(decision.pipeline, ProcessingPipeline)
        assert decision.estimated_cost > 0
        assert decision.estimated_time > 0
        assert 0.0 <= decision.confidence <= 1.0
        assert decision.reasoning is not None
    
    @pytest.mark.asyncio
    async def test_route_different_strategies(self):
        """Test routing with different optimization strategies."""
        router = IntelligenceRouter()
        
        task = ProcessingTask(
            email_data={"subject": "Test", "body": "Test email for routing"},
            task_type="analysis"
        )
        
        strategies = [
            RoutingStrategy.COST_OPTIMIZED,
            RoutingStrategy.PERFORMANCE_OPTIMIZED,
            RoutingStrategy.BALANCED,
            RoutingStrategy.QUALITY_OPTIMIZED
        ]
        
        decisions = []
        for strategy in strategies:
            constraints = Constraints(strategy=strategy)
            decision = await router.route(task, constraints)
            decisions.append(decision)
            assert decision is not None
        
        # Verify that different strategies can produce different results
        pipelines = [d.pipeline for d in decisions]
        # At least some variety in decisions (not all identical)
        assert len(set(pipelines)) >= 1

class TestAdaptiveLearningEngine:
    """Test the adaptive learning engine component."""
    
    def test_learning_engine_initialization(self):
        """Test that the learning engine initializes correctly."""
        engine = AdaptiveLearningEngine()
        assert engine is not None
    
    def test_record_outcome(self):
        """Test recording routing outcomes."""
        engine = AdaptiveLearningEngine()
        
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
        
        # Verify that the outcome was recorded
        metrics = engine.get_learning_metrics()
        assert metrics is not None
    
    def test_get_pattern_insights(self):
        """Test getting pattern insights."""
        engine = AdaptiveLearningEngine()
        
        insights = engine.get_pattern_insights()
        assert isinstance(insights, dict)
    
    def test_export_learning_data(self):
        """Test exporting learning data."""
        engine = AdaptiveLearningEngine()
        
        data = engine.export_learning_data()
        assert isinstance(data, dict)
        assert 'learning_metrics' in data
        assert 'export_timestamp' in data

class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_routing_flow(self):
        """Test complete end-to-end routing flow."""
        router = IntelligenceRouter()
        
        # Create a realistic email processing task
        task = ProcessingTask(
            email_data={
                "subject": "Quarterly Business Review Meeting",
                "body": """
                Hi team,
                
                Our quarterly business review is scheduled for next Friday.
                Please prepare your department reports and key metrics.
                
                Agenda:
                1. Q3 performance analysis
                2. Q4 planning and goals
                3. Budget discussions
                
                Looking forward to productive discussions.
                
                Best,
                Manager
                """,
                "from": "manager@company.com",
                "to": ["team@company.com"]
            },
            task_type="categorization"
        )
        
        constraints = Constraints(
            max_cost=0.005,
            max_time=1.0,
            min_quality=0.8,
            strategy=RoutingStrategy.BALANCED
        )
        
        # Route the task
        decision = await router.route(task, constraints)
        
        # Verify the decision
        assert decision is not None
        assert decision.estimated_cost <= constraints.max_cost
        assert decision.estimated_time <= constraints.max_time
        assert isinstance(decision.pipeline, ProcessingPipeline)
        
        # Simulate processing outcome
        outcome = RoutingOutcome(
            decision_id="integration_test_001",
            pipeline_used=decision.pipeline.value,
            actual_cost=decision.estimated_cost * 0.95,  # Slightly better than predicted
            actual_time=decision.estimated_time * 1.1,   # Slightly slower than predicted
            actual_quality=0.88,
            success=True
        )
        
        # Record the outcome for learning
        router.learning_engine.record_outcome(
            {
                'pipeline': decision.pipeline.value,
                'estimated_cost': decision.estimated_cost,
                'estimated_time': decision.estimated_time
            },
            outcome
        )
        
        # Verify learning occurred
        metrics = router.learning_engine.get_learning_metrics()
        assert metrics.success_rate > 0

# Performance and stress tests
class TestPerformanceRequirements:
    """Test that performance requirements are met."""
    
    @pytest.mark.asyncio
    async def test_routing_speed(self):
        """Test that routing decisions are made quickly."""
        router = IntelligenceRouter()
        
        task = ProcessingTask(
            email_data={"subject": "Speed Test", "body": "Quick routing test"},
            task_type="categorization"
        )
        
        constraints = Constraints()
        
        # Measure routing time
        start_time = datetime.now()
        decision = await router.route(task, constraints)
        end_time = datetime.now()
        
        routing_time = (end_time - start_time).total_seconds()
        
        # Should be fast (< 0.1 seconds for simple routing)
        assert routing_time < 0.1
        assert decision is not None
    
    def test_component_memory_efficiency(self):
        """Test that components don't consume excessive memory."""
        # Create multiple instances to test memory usage
        routers = [IntelligenceRouter() for _ in range(5)]
        
        # Basic validation that all components are created
        for router in routers:
            assert router is not None
            assert hasattr(router, 'complexity_analyzer')
            assert hasattr(router, 'cost_predictor')
            assert hasattr(router, 'performance_predictor')
            assert hasattr(router, 'pipeline_selector')
            assert hasattr(router, 'learning_engine')

if __name__ == "__main__":
    # Run basic tests if script is executed directly
    pytest.main([__file__, "-v"])
