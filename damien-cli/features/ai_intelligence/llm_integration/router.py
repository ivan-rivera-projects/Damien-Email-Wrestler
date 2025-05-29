from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from .cost_management import CostEstimator # Added import
# from .base import LLMRequest # For type hinting if LLMRequest is passed to CostEstimator

# Placeholder for PerformancePredictor
class PerformancePredictor:
    """
    Predicts the performance characteristics (e.g., accuracy, latency)
    of different processing pipelines for a given task.
    This is a basic placeholder.
    """
    def predict_performance(self, email_data: Dict[str, Any], task_type: str, pipeline: 'ProcessingPipeline') -> Dict[str, float]:
        """
        Predicts performance metrics for a given pipeline.

        Args:
            email_data: The email data being processed.
            task_type: The type of task (e.g., "categorization", "summarization").
            pipeline: The ProcessingPipeline enum member.

        Returns:
            A dictionary with performance metrics, e.g.,
            {'accuracy': 0.9, 'latency_ms': 100.0}
        """
        if pipeline == ProcessingPipeline.EMBEDDING_ONLY:
            return {'accuracy': 0.95, 'latency_ms': 50.0, 'quality_score': 0.7} # Added quality_score
        elif pipeline == ProcessingPipeline.LLM_ONLY:
            return {'accuracy': 0.85, 'latency_ms': 1500.0, 'quality_score': 0.9}
        elif pipeline == ProcessingPipeline.HYBRID:
            return {'accuracy': 0.90, 'latency_ms': 800.0, 'quality_score': 0.85}
        return {'accuracy': 0.7, 'latency_ms': 1000.0, 'quality_score': 0.6} # Default

class ProcessingPipeline(Enum):
    EMBEDDING_ONLY = "embedding_only"
    LLM_ONLY = "llm_only"
    HYBRID = "hybrid"

class IntelligenceRouter:
    """Routes requests to appropriate processing pipeline"""
    
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.cost_estimator = CostEstimator()
        self.performance_predictor = PerformancePredictor()
    
    def route_request(
        self,
        email: Dict[str, Any],
        task_type: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[ProcessingPipeline, Dict[str, Any]]:
        """
        Determine optimal processing pipeline
        
        Returns:
            - Selected pipeline
            - Routing metadata and reasoning
        """
        
        # Analyze email complexity
        complexity_score = self.complexity_analyzer.analyze(email)
        
        # Estimate costs for each pipeline
        costs = {
            ProcessingPipeline.EMBEDDING_ONLY: self.cost_estimator.estimate_embedding_cost(len(email.get('content',''))),
            # TODO: To get a proper LLM cost, an LLMRequest object needs to be constructed here
            # based on the 'email' and 'task_type' to pass to estimate_llm_cost.
            # For now, using a placeholder or assuming 'email' dict can be adapted by CostEstimator.
            # This will likely require creating a dummy/template LLMRequest for estimation.
            ProcessingPipeline.LLM_ONLY: self.cost_estimator.estimate_llm_cost(email), # Placeholder: email is Dict, not LLMRequest
            ProcessingPipeline.HYBRID: self.cost_estimator.estimate_hybrid_cost(email, email) # Placeholder: email is Dict
        }
        
        # Predict performance
        performance_predictions = {}
        for p_pipeline in ProcessingPipeline:
            performance_predictions[p_pipeline] = self.performance_predictor.predict_performance(email, task_type, p_pipeline)
        
        # Extract relevant metrics for decision making, e.g. accuracy
        # The _select_pipeline method expects a dict like: {ProcessingPipeline.EMBEDDING_ONLY: 0.95 (accuracy)}
        # We'll use 'quality_score' from the predictor as the primary performance metric for selection.
        performance = {
            p: metrics['quality_score'] for p, metrics in performance_predictions.items()
        }
        
        # Apply constraints
        if constraints:
            max_cost = constraints.get('max_cost', float('inf'))
            min_accuracy = constraints.get('min_accuracy', 0.0)
            max_latency_ms = constraints.get('max_latency_ms', 5000)
        else:
            max_cost = 0.01  # Default 1 cent per email
            min_accuracy = 0.8
            max_latency_ms = 3000
        
        # Decision logic
        selected_pipeline = self._select_pipeline(
            task_type=task_type,
            complexity_score=complexity_score,
            costs=costs,
            performance=performance,
            max_cost=max_cost,
            min_accuracy=min_accuracy
        )
        
        # Build routing metadata
        metadata = {
            'complexity_score': complexity_score,
            'estimated_costs': costs,
            'full_performance_predictions': performance_predictions, # Store all predicted metrics
            'selection_performance_metric': performance, # Metric used for selection
            'selected_pipeline': selected_pipeline.value,
            'reasoning': self._explain_routing_decision(
                selected_pipeline, complexity_score, costs
            )
        }
        
        return selected_pipeline, metadata
    
    def _select_pipeline(
        self,
        task_type: str,
        complexity_score: float,
        costs: Dict[ProcessingPipeline, float],
        performance: Dict[ProcessingPipeline, float],
        max_cost: float,
        min_accuracy: float
    ) -> ProcessingPipeline:
        """Select optimal pipeline based on multiple factors"""
        
        # Task-specific routing rules
        if task_type == "simple_categorization":
            if complexity_score < 0.3:
                return ProcessingPipeline.EMBEDDING_ONLY
        
        elif task_type == "natural_language_rule":
            # Always need LLM for natural language understanding
            return ProcessingPipeline.LLM_ONLY
        
        elif task_type == "pattern_detection":
            if complexity_score < 0.5:
                return ProcessingPipeline.EMBEDDING_ONLY
            elif complexity_score < 0.8:
                return ProcessingPipeline.HYBRID
            else:
                return ProcessingPipeline.LLM_ONLY
        
        elif task_type == "importance_ranking":
            # Hybrid approach works best for nuanced ranking
            return ProcessingPipeline.HYBRID
        
        # Default logic based on constraints
        valid_pipelines = []
        
        for pipeline, cost in costs.items():
            if cost <= max_cost and performance[pipeline] >= min_accuracy:
                valid_pipelines.append(pipeline)
        
        if not valid_pipelines:
            # Fallback to cheapest option
            return ProcessingPipeline.EMBEDDING_ONLY
        
        # Select best performance within constraints
        return max(valid_pipelines, key=lambda p: performance[p])
    
    def _explain_routing_decision(
        self,
        pipeline: ProcessingPipeline,
        complexity: float,
        costs: Dict[ProcessingPipeline, float]
    ) -> str:
        """Generate human-readable explanation"""
        
        if pipeline == ProcessingPipeline.EMBEDDING_ONLY:
            return (
                f"Using embedding-only pipeline due to low complexity "
                f"({complexity:.2f}) and cost efficiency (${costs[pipeline]:.4f})"
            )
        elif pipeline == ProcessingPipeline.LLM_ONLY:
            return (
                f"Using LLM-only pipeline for high complexity task "
                f"({complexity:.2f}) requiring advanced reasoning"
            )
        else:
            return (
                f"Using hybrid pipeline to balance accuracy and cost "
                f"(complexity: {complexity:.2f}, cost: ${costs[pipeline]:.4f})"
            )

class ComplexityAnalyzer:
    """Analyzes email complexity for routing decisions"""
    
    def analyze(self, email: Dict[str, Any]) -> float:
        """
        Calculate complexity score (0-1)
        
        Factors:
        - Content length and structure
        - Language complexity
        - Number of topics
        - Ambiguity indicators
        - Attachment complexity
        """
        
        scores = []
        
        # Length complexity
        content_length = len(email.get('content', ''))
        length_score = min(content_length / 5000, 1.0)
        scores.append(length_score * 0.2)
        
        # Structural complexity
        line_count = email.get('content', '').count('\n')
        structure_score = min(line_count / 50, 1.0)
        scores.append(structure_score * 0.15)
        
        # Language complexity (simplified)
        complex_words = ['however', 'therefore', 'nevertheless', 'furthermore']
        word_count = sum(1 for word in complex_words if word in email.get('content', '').lower())
        language_score = min(word_count / 5, 1.0)
        scores.append(language_score * 0.25)
        
        # Topic diversity
        # In production, use more sophisticated topic modeling
        sentences = email.get('content', '').split('.')
        topic_score = min(len(sentences) / 20, 1.0)
        scores.append(topic_score * 0.2)
        
        # Ambiguity indicators
        ambiguous_phrases = ['maybe', 'possibly', 'might', 'could be', 'not sure']
        ambiguity_count = sum(1 for phrase in ambiguous_phrases if phrase in email.get('content', '').lower())
        ambiguity_score = min(ambiguity_count / 3, 1.0)
        scores.append(ambiguity_score * 0.2)
        
        return sum(scores)