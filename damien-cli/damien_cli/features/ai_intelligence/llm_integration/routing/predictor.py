"""
Predictors for cost and performance estimation in the routing system.

This module implements prediction models for cost and performance estimation
to support intelligent routing decisions in the Damien AI Email Intelligence Layer.
"""
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass
from .analyzer import ComplexityScore
from .selector import ProcessingPipeline

logger = logging.getLogger(__name__)

@dataclass
class CostModel:
    """Cost model parameters for different providers and pipelines."""
    embedding_cost_per_token: float = 0.0001
    llm_cost_per_token: float = 0.002
    hybrid_base_cost: float = 0.001
    
class CostPredictor:
    """
    Predicts processing costs for different pipelines and email content.
    
    Features:
    - Token-based cost estimation
    - Provider-specific pricing models
    - Complexity-adjusted predictions
    - Batch processing optimization
    """
    
    def __init__(self):
        """Initialize the CostPredictor."""
        self.cost_model = CostModel()
        self._token_estimation_cache = {}
        logger.info("CostPredictor initialized successfully")
    
    def predict_cost(
        self,
        email_data: Dict[str, Any],
        pipeline: ProcessingPipeline,
        complexity_score: ComplexityScore
    ) -> float:
        """
        Predict the cost of processing email data through a specific pipeline.
        
        Args:
            email_data: Email content and metadata
            pipeline: Processing pipeline to use
            complexity_score: Complexity analysis result
            
        Returns:
            Estimated cost in USD
        """
        try:
            # Estimate token count
            estimated_tokens = self._estimate_tokens(email_data)
            
            # Apply complexity multiplier
            complexity_multiplier = 1.0 + (complexity_score.overall_score * 0.5)
            adjusted_tokens = estimated_tokens * complexity_multiplier
            
            # Calculate cost based on pipeline
            if pipeline == ProcessingPipeline.EMBEDDING_ONLY:
                cost = adjusted_tokens * self.cost_model.embedding_cost_per_token
            elif pipeline == ProcessingPipeline.LLM_ONLY:
                cost = adjusted_tokens * self.cost_model.llm_cost_per_token
            elif pipeline == ProcessingPipeline.HYBRID:
                embedding_cost = adjusted_tokens * self.cost_model.embedding_cost_per_token
                llm_cost = (adjusted_tokens * 0.3) * self.cost_model.llm_cost_per_token
                cost = embedding_cost + llm_cost + self.cost_model.hybrid_base_cost
            else:
                cost = 0.001  # Fallback
            
            return max(cost, 0.0001)  # Minimum cost threshold
            
        except Exception as e:
            logger.error(f"Error predicting cost: {e}")
            return 0.001  # Safe fallback cost
    
    def _estimate_tokens(self, email_data: Dict[str, Any]) -> int:
        """Estimate token count for email content."""
        text_content = self._extract_text_for_tokens(email_data)
        
        # Use cache for identical content
        content_hash = hash(text_content)
        if content_hash in self._token_estimation_cache:
            return self._token_estimation_cache[content_hash]
        
        # Simple token estimation (words * 1.3 for subword tokens)
        word_count = len(text_content.split())
        estimated_tokens = max(int(word_count * 1.3), 10)
        
        # Cache result
        self._token_estimation_cache[content_hash] = estimated_tokens
        
        # Limit cache size
        if len(self._token_estimation_cache) > 1000:
            keys = list(self._token_estimation_cache.keys())
            for key in keys[:500]:
                del self._token_estimation_cache[key]
        
        return estimated_tokens
    
    def _extract_text_for_tokens(self, email_data: Dict[str, Any]) -> str:
        """Extract text content for token estimation."""
        text_parts = []
        
        if 'subject' in email_data and email_data['subject']:
            text_parts.append(str(email_data['subject']))
        
        if 'body' in email_data and email_data['body']:
            text_parts.append(str(email_data['body']))
        
        return ' '.join(text_parts)


class PerformancePredictor:
    """
    Predicts performance characteristics for different processing pipelines.
    
    This component estimates performance metrics like latency, accuracy,
    and quality scores based on email content characteristics and
    historical performance data.
    """
    
    def __init__(self):
        """Initialize the PerformancePredictor."""
        self._performance_history = {}
        logger.info("PerformancePredictor initialized successfully")
    
    def predict_performance(
        self,
        email_data: Dict[str, Any],
        task_type: str,
        pipeline: ProcessingPipeline
    ) -> Dict[str, float]:
        """
        Predict performance metrics for a processing pipeline.
        
        Args:
            email_data: Email content and metadata
            task_type: Type of processing task
            pipeline: Processing pipeline
            
        Returns:
            Dictionary with performance metrics including:
            - latency_ms: Expected latency in milliseconds
            - accuracy: Expected accuracy (0.0-1.0)
            - quality_score: Expected quality (0.0-1.0)
        """
        try:
            # Get base performance characteristics
            base_metrics = self._get_base_performance(pipeline)
            
            # Adjust based on content characteristics
            content_length = len(str(email_data.get('body', '')))
            length_multiplier = 1.0 + (content_length / 2000.0)
            
            # Adjust latency based on content length
            adjusted_latency = base_metrics['latency_ms'] * length_multiplier
            
            # Task-specific adjustments
            task_adjustments = self._get_task_adjustments(task_type)
            
            return {
                'latency_ms': adjusted_latency * task_adjustments['latency_multiplier'],
                'accuracy': base_metrics['accuracy'] * task_adjustments['accuracy_multiplier'],
                'quality_score': base_metrics['quality_score'] * task_adjustments['quality_multiplier']
            }
            
        except Exception as e:
            logger.error(f"Error predicting performance: {e}")
            return self._get_fallback_performance()
    
    def _get_base_performance(self, pipeline: ProcessingPipeline) -> Dict[str, float]:
        """Get base performance characteristics for a pipeline."""
        performance_profiles = {
            ProcessingPipeline.EMBEDDING_ONLY: {
                'latency_ms': 50.0,
                'accuracy': 0.85,
                'quality_score': 0.7
            },
            ProcessingPipeline.LLM_ONLY: {
                'latency_ms': 1500.0,
                'accuracy': 0.95,
                'quality_score': 0.9
            },
            ProcessingPipeline.HYBRID: {
                'latency_ms': 800.0,
                'accuracy': 0.92,
                'quality_score': 0.85
            }
        }
        
        return performance_profiles.get(pipeline, {
            'latency_ms': 500.0,
            'accuracy': 0.8,
            'quality_score': 0.75
        })
    
    def _get_task_adjustments(self, task_type: str) -> Dict[str, float]:
        """Get task-specific performance adjustments."""
        adjustments = {
            'categorization': {
                'latency_multiplier': 0.8,
                'accuracy_multiplier': 1.1,
                'quality_multiplier': 1.0
            },
            'summarization': {
                'latency_multiplier': 1.3,
                'accuracy_multiplier': 0.9,
                'quality_multiplier': 1.1
            },
            'sentiment_analysis': {
                'latency_multiplier': 0.9,
                'accuracy_multiplier': 1.0,
                'quality_multiplier': 0.95
            },
            'analysis': {
                'latency_multiplier': 1.0,
                'accuracy_multiplier': 1.0,
                'quality_multiplier': 1.0
            }
        }
        
        return adjustments.get(task_type, {
            'latency_multiplier': 1.0,
            'accuracy_multiplier': 1.0,
            'quality_multiplier': 1.0
        })
    
    def _get_fallback_performance(self) -> Dict[str, float]:
        """Return fallback performance metrics."""
        return {
            'latency_ms': 500.0,
            'accuracy': 0.8,
            'quality_score': 0.75
        }
    
    def record_actual_performance(
        self,
        pipeline: ProcessingPipeline,
        predicted_metrics: Dict[str, float],
        actual_metrics: Dict[str, float]
    ):
        """Record actual performance for learning and calibration."""
        record = {
            'predicted': predicted_metrics,
            'actual': actual_metrics,
            'error': {
                key: abs(actual_metrics.get(key, 0) - predicted_metrics.get(key, 0))
                for key in predicted_metrics.keys()
            }
        }
        
        pipeline_key = pipeline.value
        if pipeline_key not in self._performance_history:
            self._performance_history[pipeline_key] = []
        
        self._performance_history[pipeline_key].append(record)
        
        # Limit history size
        if len(self._performance_history[pipeline_key]) > 100:
            self._performance_history[pipeline_key] = self._performance_history[pipeline_key][-50:]
        
        logger.info(f"Recorded performance for {pipeline_key}")
