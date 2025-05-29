"""
Adaptive learning engine for routing optimization.

This module implements the AdaptiveLearningEngine that learns from routing
decisions and outcomes to improve future routing performance.
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class RoutingOutcome:
    """
    Represents the outcome of a routing decision.
    
    Attributes:
        decision_id: Unique identifier for the routing decision
        pipeline_used: Pipeline that was selected
        actual_cost: Actual cost incurred
        actual_time: Actual processing time
        actual_quality: Actual quality achieved
        success: Whether the processing was successful
        error_message: Error message if processing failed
    """
    decision_id: str
    pipeline_used: str
    actual_cost: float
    actual_time: float
    actual_quality: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class LearningMetrics:
    """
    Metrics for evaluating learning performance.
    
    Attributes:
        prediction_accuracy: How accurate predictions were
        cost_optimization: How well costs were optimized
        time_optimization: How well processing times were optimized
        quality_achievement: How well quality targets were met
        success_rate: Overall success rate of routing decisions
    """
    prediction_accuracy: float
    cost_optimization: float
    time_optimization: float
    quality_achievement: float
    success_rate: float

class AdaptiveLearningEngine:
    """
    Adaptive learning engine for routing optimization.
    
    This component learns from routing decisions and their outcomes to
    improve future routing performance. It tracks prediction accuracy,
    identifies patterns in successful decisions, and adjusts routing
    strategies based on observed results.
    
    Features:
    - Outcome tracking and analysis
    - Prediction accuracy measurement
    - Pattern recognition in successful routing
    - Adaptive strategy adjustment
    - Performance trend analysis
    """
    
    def __init__(self):
        """Initialize the AdaptiveLearningEngine."""
        self._outcomes_history: List[Tuple[Dict[str, Any], RoutingOutcome, datetime]] = []
        self._learning_metrics = LearningMetrics(
            prediction_accuracy=0.0,
            cost_optimization=0.0,
            time_optimization=0.0,
            quality_achievement=0.0,
            success_rate=0.0
        )
        self._pattern_insights = {}
        logger.info("AdaptiveLearningEngine initialized successfully")
    
    def record_outcome(
        self,
        routing_decision: Dict[str, Any],
        outcome: RoutingOutcome
    ):
        """
        Record the outcome of a routing decision for learning.
        
        Args:
            routing_decision: The original routing decision data
            outcome: The actual outcome of the processing
        """
        try:
            # Store the outcome with timestamp
            self._outcomes_history.append((
                routing_decision,
                outcome,
                datetime.now()
            ))
            
            # Limit history size for memory management
            if len(self._outcomes_history) > 1000:
                self._outcomes_history = self._outcomes_history[-500:]
            
            # Update learning metrics
            self._update_learning_metrics()
            
            # Identify new patterns
            self._analyze_patterns()
            
            logger.info(f"Recorded outcome for decision {outcome.decision_id}")
            
        except Exception as e:
            logger.error(f"Error recording outcome: {e}")
    
    def _update_learning_metrics(self):
        """Update learning metrics based on recent outcomes."""
        if not self._outcomes_history:
            return
        
        # Analyze recent outcomes (last 100)
        recent_outcomes = self._outcomes_history[-100:]
        
        # Calculate prediction accuracy
        prediction_errors = []
        cost_optimizations = []
        time_optimizations = []
        quality_achievements = []
        success_count = 0
        
        for decision, outcome, timestamp in recent_outcomes:
            # Prediction accuracy (based on cost and time predictions)
            predicted_cost = decision.get('estimated_cost', 0)
            predicted_time = decision.get('estimated_time', 0)
            
            if predicted_cost > 0:
                cost_error = abs(predicted_cost - outcome.actual_cost) / predicted_cost
                prediction_errors.append(cost_error)
                
                # Cost optimization (actual vs predicted)
                cost_optimizations.append(
                    max(0, (predicted_cost - outcome.actual_cost) / predicted_cost)
                )
            
            if predicted_time > 0:
                time_error = abs(predicted_time - outcome.actual_time) / predicted_time
                prediction_errors.append(time_error)
                
                # Time optimization
                time_optimizations.append(
                    max(0, (predicted_time - outcome.actual_time) / predicted_time)
                )
            
            # Quality achievement
            quality_achievements.append(outcome.actual_quality)
            
            # Success rate
            if outcome.success:
                success_count += 1
        
        # Update metrics
        if prediction_errors:
            self._learning_metrics.prediction_accuracy = 1.0 - (
                sum(prediction_errors) / len(prediction_errors)
            )
        
        if cost_optimizations:
            self._learning_metrics.cost_optimization = (
                sum(cost_optimizations) / len(cost_optimizations)
            )
        
        if time_optimizations:
            self._learning_metrics.time_optimization = (
                sum(time_optimizations) / len(time_optimizations)
            )
        
        if quality_achievements:
            self._learning_metrics.quality_achievement = (
                sum(quality_achievements) / len(quality_achievements)
            )
        
        self._learning_metrics.success_rate = success_count / len(recent_outcomes)
    
    def _analyze_patterns(self):
        """Analyze patterns in routing decisions and outcomes."""
        if len(self._outcomes_history) < 20:
            return  # Need enough data for pattern recognition
        
        # Analyze success patterns by pipeline
        pipeline_success = {}
        pipeline_performance = {}
        
        for decision, outcome, timestamp in self._outcomes_history[-50:]:
            pipeline = outcome.pipeline_used
            
            # Track success rates
            if pipeline not in pipeline_success:
                pipeline_success[pipeline] = {'success': 0, 'total': 0}
            
            pipeline_success[pipeline]['total'] += 1
            if outcome.success:
                pipeline_success[pipeline]['success'] += 1
            
            # Track performance metrics
            if pipeline not in pipeline_performance:
                pipeline_performance[pipeline] = {
                    'costs': [], 'times': [], 'qualities': []
                }
            
            pipeline_performance[pipeline]['costs'].append(outcome.actual_cost)
            pipeline_performance[pipeline]['times'].append(outcome.actual_time)
            pipeline_performance[pipeline]['qualities'].append(outcome.actual_quality)
        
        # Store insights
        self._pattern_insights = {
            'pipeline_success_rates': {
                pipeline: data['success'] / data['total']
                for pipeline, data in pipeline_success.items()
                if data['total'] > 0
            },
            'pipeline_avg_performance': {
                pipeline: {
                    'avg_cost': sum(data['costs']) / len(data['costs']) if data['costs'] else 0,
                    'avg_time': sum(data['times']) / len(data['times']) if data['times'] else 0,
                    'avg_quality': sum(data['qualities']) / len(data['qualities']) if data['qualities'] else 0
                }
                for pipeline, data in pipeline_performance.items()
            }
        }
    
    def get_learning_metrics(self) -> LearningMetrics:
        """
        Get current learning metrics.
        
        Returns:
            LearningMetrics with current performance data
        """
        return self._learning_metrics
    
    def get_pattern_insights(self) -> Dict[str, Any]:
        """
        Get insights discovered through pattern analysis.
        
        Returns:
            Dictionary containing pattern insights
        """
        return self._pattern_insights
    
    def get_routing_recommendations(
        self,
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get routing recommendations based on learned patterns.
        
        Args:
            task_context: Context about the current task
            
        Returns:
            Dictionary with routing recommendations
        """
        recommendations = {
            'preferred_pipelines': [],
            'avoid_pipelines': [],
            'confidence_adjustments': {},
            'reasoning': []
        }
        
        # Use pattern insights to make recommendations
        if self._pattern_insights:
            success_rates = self._pattern_insights.get('pipeline_success_rates', {})
            
            # Recommend pipelines with high success rates
            for pipeline, success_rate in success_rates.items():
                if success_rate > 0.8:
                    recommendations['preferred_pipelines'].append(pipeline)
                    recommendations['reasoning'].append(
                        f"{pipeline} has high success rate ({success_rate:.2f})"
                    )
                elif success_rate < 0.5:
                    recommendations['avoid_pipelines'].append(pipeline)
                    recommendations['reasoning'].append(
                        f"{pipeline} has low success rate ({success_rate:.2f})"
                    )
            
            # Adjust confidence based on prediction accuracy
            accuracy = self._learning_metrics.prediction_accuracy
            if accuracy < 0.7:
                recommendations['confidence_adjustments']['reduce_confidence'] = True
                recommendations['reasoning'].append(
                    f"Reducing confidence due to low prediction accuracy ({accuracy:.2f})"
                )
        
        return recommendations
    
    def export_learning_data(self) -> Dict[str, Any]:
        """
        Export learning data for analysis or backup.
        
        Returns:
            Dictionary with exportable learning data
        """
        return {
            'learning_metrics': {
                'prediction_accuracy': self._learning_metrics.prediction_accuracy,
                'cost_optimization': self._learning_metrics.cost_optimization,
                'time_optimization': self._learning_metrics.time_optimization,
                'quality_achievement': self._learning_metrics.quality_achievement,
                'success_rate': self._learning_metrics.success_rate
            },
            'pattern_insights': self._pattern_insights,
            'outcomes_count': len(self._outcomes_history),
            'export_timestamp': datetime.now().isoformat()
        }
    
    def get_learning_summary(self) -> str:
        """
        Get a human-readable summary of learning progress.
        
        Returns:
            String summary of learning status
        """
        metrics = self._learning_metrics
        
        summary_parts = [
            f"Learning Summary:",
            f"- Prediction Accuracy: {metrics.prediction_accuracy:.2f}",
            f"- Cost Optimization: {metrics.cost_optimization:.2f}",
            f"- Time Optimization: {metrics.time_optimization:.2f}",
            f"- Quality Achievement: {metrics.quality_achievement:.2f}",
            f"- Success Rate: {metrics.success_rate:.2f}",
            f"- Total Outcomes Analyzed: {len(self._outcomes_history)}"
        ]
        
        if self._pattern_insights:
            summary_parts.append("- Pattern Insights Available")
        
        return "\n".join(summary_parts)
