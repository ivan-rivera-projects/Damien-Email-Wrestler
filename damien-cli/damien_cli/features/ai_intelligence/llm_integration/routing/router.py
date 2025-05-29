"""
IntelligenceRouter - ML-powered routing system for optimal processing decisions.

This module implements the central routing component that orchestrates complexity
analysis, cost prediction, and pipeline selection for email processing tasks.
"""
from typing import Dict, Any, Optional, List, Tuple, NamedTuple
from enum import Enum
from dataclasses import dataclass
import asyncio
import time
import logging
from datetime import datetime

# Imports from other modules in this package  
from .analyzer import MLComplexityAnalyzer, ComplexityScore
from .predictor import CostPredictor, PerformancePredictor
from .selector import PipelineSelector, ProcessingPipeline
from .learning import AdaptiveLearningEngine

logger = logging.getLogger(__name__)

class RoutingStrategy(Enum):
    """Routing strategies for different optimization goals."""
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized" 
    BALANCED = "balanced"
    QUALITY_OPTIMIZED = "quality_optimized"

@dataclass
class Constraints:
    """Constraints for routing decisions."""
    max_cost: Optional[float] = None
    max_time: Optional[float] = None
    min_quality: Optional[float] = 0.7
    strategy: RoutingStrategy = RoutingStrategy.BALANCED

@dataclass
class ProcessingTask:
    """Processing task for routing decisions."""
    email_data: Dict[str, Any]
    task_type: str = "analysis"
    priority: str = "normal"
    metadata: Optional[Dict[str, Any]] = None

class RoutingDecision(NamedTuple):
    """Routing decision result."""
    pipeline: ProcessingPipeline
    estimated_cost: float
    estimated_time: float
    confidence: float
    reasoning: str
    fallback_pipeline: Optional[ProcessingPipeline] = None

class IntelligenceRouter:
    """
    ML-powered routing system for optimal processing decisions.
    
    Features:
    - Real-time complexity analysis using ML models
    - Cost prediction and optimization across providers
    - Performance estimation based on historical data
    - Adaptive learning from processing outcomes
    """
    
    def __init__(self):
        """Initialize the IntelligenceRouter with all components."""
        self.complexity_analyzer = MLComplexityAnalyzer()
        self.cost_predictor = CostPredictor()
        self.performance_predictor = PerformancePredictor()
        self.pipeline_selector = PipelineSelector()
        self.learning_engine = AdaptiveLearningEngine()
        
        self._decision_count = 0
        self._decision_history: List[Tuple[ProcessingTask, RoutingDecision, datetime]] = []
        
        logger.info("IntelligenceRouter initialized successfully")
    
    async def route(
        self,
        task: ProcessingTask,
        constraints: Constraints
    ) -> RoutingDecision:
        """
        Make intelligent routing decision for a processing task.
        
        Args:
            task: The processing task to route
            constraints: Constraints and preferences for routing
            
        Returns:
            RoutingDecision with selected pipeline and predictions
        """
        start_time = time.time()
        
        try:
            # Analyze task complexity
            complexity_score = await self.complexity_analyzer.analyze(
                task.email_data, task.task_type
            )
            
            # Get and evaluate available pipelines
            available_pipelines = self.pipeline_selector.get_available_pipelines()
            best_pipeline = self._select_best_pipeline(
                available_pipelines, task, complexity_score, constraints
            )
            
            # Create routing decision
            decision = await self._create_routing_decision(
                best_pipeline, task, complexity_score, constraints
            )
            
            # Record for learning
            self._record_decision(task, decision)
            
            routing_time = time.time() - start_time
            logger.info(f"Routing decision made in {routing_time:.3f}s: {decision.pipeline}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in routing decision: {e}")
            return self._create_fallback_decision(str(e))
    
    def _select_best_pipeline(
        self,
        available_pipelines: List[ProcessingPipeline],
        task: ProcessingTask,
        complexity_score: ComplexityScore,
        constraints: Constraints
    ) -> ProcessingPipeline:
        """Select the best pipeline based on evaluation criteria."""
        pipeline_evaluations = []
        
        for pipeline in available_pipelines:
            # Predict cost and performance
            estimated_cost = self.cost_predictor.predict_cost(
                task.email_data, pipeline, complexity_score
            )
            performance_metrics = self.performance_predictor.predict_performance(
                task.email_data, task.task_type, pipeline
            )
            
            # Check if meets constraints
            if self._meets_constraints(estimated_cost, performance_metrics, constraints):
                score = self._calculate_pipeline_score(
                    estimated_cost, performance_metrics, constraints
                )
                pipeline_evaluations.append((pipeline, score))
        
        # Return best pipeline or fallback
        if pipeline_evaluations:
            pipeline_evaluations.sort(key=lambda x: x[1], reverse=True)
            return pipeline_evaluations[0][0]
        else:
            logger.warning("No pipelines meet constraints, using fallback")
            return ProcessingPipeline.EMBEDDING_ONLY
    
    def _meets_constraints(
        self,
        cost: float,
        performance: Dict[str, float],
        constraints: Constraints
    ) -> bool:
        """Check if pipeline option meets the given constraints."""
        if constraints.max_cost and cost > constraints.max_cost:
            return False
        if constraints.max_time and performance['latency_ms'] / 1000.0 > constraints.max_time:
            return False
        if constraints.min_quality and performance['quality_score'] < constraints.min_quality:
            return False
        return True
    
    def _calculate_pipeline_score(
        self,
        cost: float,
        performance: Dict[str, float],
        constraints: Constraints
    ) -> float:
        """Calculate a score for pipeline selection based on strategy."""
        if constraints.strategy == RoutingStrategy.COST_OPTIMIZED:
            return 1.0 / (cost + 0.001)  # Lower cost = higher score
        elif constraints.strategy == RoutingStrategy.PERFORMANCE_OPTIMIZED:
            return 1.0 / (performance['latency_ms'] + 1.0)  # Lower latency = higher score
        elif constraints.strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            return performance['quality_score']
        else:  # BALANCED
            # Balanced score considering cost, performance, and quality
            cost_score = 1.0 / (cost + 0.001)
            perf_score = 1.0 / (performance['latency_ms'] / 1000.0 + 0.1)
            quality_score = performance['quality_score']
            return (cost_score + perf_score + quality_score) / 3.0
    
    async def _create_routing_decision(
        self,
        pipeline: ProcessingPipeline,
        task: ProcessingTask,
        complexity_score: ComplexityScore,
        constraints: Constraints
    ) -> RoutingDecision:
        """Create a routing decision with predictions and reasoning."""
        # Get final predictions for selected pipeline
        estimated_cost = self.cost_predictor.predict_cost(
            task.email_data, pipeline, complexity_score
        )
        performance_metrics = self.performance_predictor.predict_performance(
            task.email_data, task.task_type, pipeline
        )
        
        # Calculate confidence based on complexity and historical performance
        confidence = self._calculate_confidence(complexity_score, pipeline)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            pipeline, estimated_cost, performance_metrics, constraints
        )
        
        # Select fallback pipeline
        fallback_pipeline = self._select_fallback_pipeline(pipeline)
        
        return RoutingDecision(
            pipeline=pipeline,
            estimated_cost=estimated_cost,
            estimated_time=performance_metrics['latency_ms'] / 1000.0,
            confidence=confidence,
            reasoning=reasoning,
            fallback_pipeline=fallback_pipeline
        )
    
    def _calculate_confidence(
        self,
        complexity_score: ComplexityScore,
        pipeline: ProcessingPipeline
    ) -> float:
        """Calculate confidence in the routing decision."""
        # Base confidence on complexity score certainty
        base_confidence = complexity_score.confidence
        
        # Adjust based on pipeline reliability (could be learned over time)
        pipeline_reliability = {
            ProcessingPipeline.EMBEDDING_ONLY: 0.95,
            ProcessingPipeline.LLM_ONLY: 0.85,
            ProcessingPipeline.HYBRID: 0.90
        }
        
        return min(base_confidence * pipeline_reliability.get(pipeline, 0.8), 1.0)
    
    def _generate_reasoning(
        self,
        pipeline: ProcessingPipeline,
        cost: float,
        performance: Dict[str, float],
        constraints: Constraints
    ) -> str:
        """Generate human-readable reasoning for the routing decision."""
        reasons = []
        
        reasons.append(f"Selected {pipeline.value} pipeline")
        reasons.append(f"Estimated cost: ${cost:.4f}")
        reasons.append(f"Expected time: {performance['latency_ms']:.0f}ms")
        reasons.append(f"Quality score: {performance['quality_score']:.2f}")
        
        if constraints.strategy != RoutingStrategy.BALANCED:
            reasons.append(f"Optimized for {constraints.strategy.value}")
        
        return " | ".join(reasons)
    
    def _select_fallback_pipeline(self, primary: ProcessingPipeline) -> ProcessingPipeline:
        """Select an appropriate fallback pipeline."""
        if primary == ProcessingPipeline.LLM_ONLY:
            return ProcessingPipeline.HYBRID
        elif primary == ProcessingPipeline.HYBRID:
            return ProcessingPipeline.EMBEDDING_ONLY
        else:
            return ProcessingPipeline.EMBEDDING_ONLY
    
    def _record_decision(self, task: ProcessingTask, decision: RoutingDecision):
        """Record routing decision for learning and analytics."""
        self._decision_count += 1
        self._decision_history.append((task, decision, datetime.now()))
        
        # Limit history size for memory management
        if len(self._decision_history) > 1000:
            self._decision_history = self._decision_history[-500:]
    
    def _create_fallback_decision(self, error_msg: str) -> RoutingDecision:
        """Create a safe fallback decision when routing fails."""
        return RoutingDecision(
            pipeline=ProcessingPipeline.EMBEDDING_ONLY,
            estimated_cost=0.001,
            estimated_time=0.1,
            confidence=0.5,
            reasoning=f"Fallback due to routing error: {error_msg}"
        )
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics for monitoring and debugging."""
        if not self._decision_history:
            return {"total_decisions": 0}
        
        recent_decisions = [d[1] for d in self._decision_history[-100:]]
        pipeline_counts = {}
        total_cost = 0.0
        total_time = 0.0
        
        for decision in recent_decisions:
            pipeline = decision.pipeline.value
            pipeline_counts[pipeline] = pipeline_counts.get(pipeline, 0) + 1
            total_cost += decision.estimated_cost
            total_time += decision.estimated_time
        
        return {
            "total_decisions": self._decision_count,
            "recent_pipeline_distribution": pipeline_counts,
            "average_cost": total_cost / len(recent_decisions),
            "average_time": total_time / len(recent_decisions)
        }
