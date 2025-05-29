"""
Pipeline selector for choosing optimal processing paths.

This module implements the PipelineSelector component that manages available
processing pipelines and provides selection logic for the routing system.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ProcessingPipeline(Enum):
    """
    Available processing pipelines for email analysis.
    
    Each pipeline represents a different approach to processing email content
    with different cost, performance, and quality characteristics.
    """
    EMBEDDING_ONLY = "embedding_only"     # Fast, cheap, good for simple tasks
    LLM_ONLY = "llm_only"                # Slow, expensive, high quality
    HYBRID = "hybrid"                     # Balanced approach using both

class PipelineCapability(Enum):
    """Capabilities that pipelines can provide."""
    CATEGORIZATION = "categorization"
    SUMMARIZATION = "summarization"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    INFORMATION_EXTRACTION = "information_extraction"
    QUESTION_ANSWERING = "question_answering"
    PATTERN_DETECTION = "pattern_detection"

class PipelineSelector:
    """
    Manages available processing pipelines and provides selection logic.
    
    This component maintains information about available pipelines,
    their capabilities, current status, and provides methods for
    selecting appropriate pipelines based on requirements.
    
    Features:
    - Pipeline availability management
    - Capability-based filtering
    - Load balancing considerations
    - Fallback pipeline selection
    - Pipeline health monitoring
    """
    
    def __init__(self):
        """Initialize the PipelineSelector."""
        self._initialize_pipeline_config()
        self._pipeline_status = {}
        self._initialize_pipeline_status()
        logger.info("PipelineSelector initialized successfully")
    
    def _initialize_pipeline_config(self):
        """Initialize pipeline configuration and capabilities."""
        self._pipeline_capabilities = {
            ProcessingPipeline.EMBEDDING_ONLY: {
                PipelineCapability.CATEGORIZATION,
                PipelineCapability.SENTIMENT_ANALYSIS,
                PipelineCapability.PATTERN_DETECTION
            },
            ProcessingPipeline.LLM_ONLY: {
                PipelineCapability.CATEGORIZATION,
                PipelineCapability.SUMMARIZATION,
                PipelineCapability.SENTIMENT_ANALYSIS,
                PipelineCapability.INFORMATION_EXTRACTION,
                PipelineCapability.QUESTION_ANSWERING,
                PipelineCapability.PATTERN_DETECTION
            },
            ProcessingPipeline.HYBRID: {
                PipelineCapability.CATEGORIZATION,
                PipelineCapability.SUMMARIZATION,
                PipelineCapability.SENTIMENT_ANALYSIS,
                PipelineCapability.INFORMATION_EXTRACTION,
                PipelineCapability.PATTERN_DETECTION
            }
        }
        
        # Pipeline characteristics
        self._pipeline_characteristics = {
            ProcessingPipeline.EMBEDDING_ONLY: {
                'speed_tier': 'fast',
                'cost_tier': 'low',
                'quality_tier': 'good',
                'complexity_handling': 'basic'
            },
            ProcessingPipeline.LLM_ONLY: {
                'speed_tier': 'slow',
                'cost_tier': 'high',
                'quality_tier': 'excellent',
                'complexity_handling': 'advanced'
            },
            ProcessingPipeline.HYBRID: {
                'speed_tier': 'medium',
                'cost_tier': 'medium',
                'quality_tier': 'very_good',
                'complexity_handling': 'good'
            }
        }
    
    def _initialize_pipeline_status(self):
        """Initialize pipeline status tracking."""
        for pipeline in ProcessingPipeline:
            self._pipeline_status[pipeline] = {
                'available': True,
                'load': 0.0,  # Current load (0.0-1.0)
                'error_rate': 0.0,  # Recent error rate
                'avg_latency': self._get_baseline_latency(pipeline),
                'last_health_check': None
            }
    
    def get_available_pipelines(self) -> List[ProcessingPipeline]:
        """
        Get list of currently available pipelines.
        
        Returns:
            List of available ProcessingPipeline enums
        """
        available = []
        
        for pipeline in ProcessingPipeline:
            status = self._pipeline_status[pipeline]
            if status['available'] and status['load'] < 0.9:  # Not overloaded
                available.append(pipeline)
        
        # Always ensure at least one pipeline is available
        if not available:
            logger.warning("No pipelines available, adding fallback")
            available = [ProcessingPipeline.EMBEDDING_ONLY]
        
        return available
    
    def filter_by_capability(
        self,
        pipelines: List[ProcessingPipeline],
        required_capability: PipelineCapability
    ) -> List[ProcessingPipeline]:
        """
        Filter pipelines by required capability.
        
        Args:
            pipelines: List of pipelines to filter
            required_capability: Required capability
            
        Returns:
            Filtered list of pipelines that support the capability
        """
        filtered = []
        
        for pipeline in pipelines:
            capabilities = self._pipeline_capabilities.get(pipeline, set())
            if required_capability in capabilities:
                filtered.append(pipeline)
        
        return filtered
    
    def get_pipeline_characteristics(
        self,
        pipeline: ProcessingPipeline
    ) -> Dict[str, str]:
        """
        Get characteristics of a specific pipeline.
        
        Args:
            pipeline: Pipeline to get characteristics for
            
        Returns:
            Dictionary of pipeline characteristics
        """
        return self._pipeline_characteristics.get(pipeline, {})
    
    def get_pipeline_status(
        self,
        pipeline: ProcessingPipeline
    ) -> Dict[str, Any]:
        """
        Get current status of a specific pipeline.
        
        Args:
            pipeline: Pipeline to get status for
            
        Returns:
            Dictionary of pipeline status information
        """
        return self._pipeline_status.get(pipeline, {})
    
    def update_pipeline_load(
        self,
        pipeline: ProcessingPipeline,
        load: float
    ):
        """
        Update the current load for a pipeline.
        
        Args:
            pipeline: Pipeline to update
            load: Current load (0.0-1.0)
        """
        if pipeline in self._pipeline_status:
            self._pipeline_status[pipeline]['load'] = max(0.0, min(1.0, load))
    
    def record_pipeline_error(self, pipeline: ProcessingPipeline):
        """
        Record an error for a pipeline to track error rates.
        
        Args:
            pipeline: Pipeline that experienced an error
        """
        if pipeline in self._pipeline_status:
            current_error_rate = self._pipeline_status[pipeline]['error_rate']
            # Simple exponential moving average
            self._pipeline_status[pipeline]['error_rate'] = (
                current_error_rate * 0.9 + 0.1
            )
            
            # Disable pipeline if error rate too high
            if self._pipeline_status[pipeline]['error_rate'] > 0.5:
                logger.warning(f"Disabling {pipeline.value} due to high error rate")
                self._pipeline_status[pipeline]['available'] = False
    
    def record_pipeline_success(self, pipeline: ProcessingPipeline, latency: float):
        """
        Record a successful operation for a pipeline.
        
        Args:
            pipeline: Pipeline that succeeded
            latency: Operation latency in seconds
        """
        if pipeline in self._pipeline_status:
            # Update error rate (decrease)
            current_error_rate = self._pipeline_status[pipeline]['error_rate']
            self._pipeline_status[pipeline]['error_rate'] = max(
                0.0, current_error_rate * 0.95
            )
            
            # Update average latency
            current_latency = self._pipeline_status[pipeline]['avg_latency']
            self._pipeline_status[pipeline]['avg_latency'] = (
                current_latency * 0.9 + latency * 0.1
            )
    
    def _get_baseline_latency(self, pipeline: ProcessingPipeline) -> float:
        """Get baseline latency for a pipeline."""
        baselines = {
            ProcessingPipeline.EMBEDDING_ONLY: 0.05,   # 50ms
            ProcessingPipeline.LLM_ONLY: 1.5,          # 1.5s
            ProcessingPipeline.HYBRID: 0.8             # 800ms
        }
        return baselines.get(pipeline, 0.5)
    
    def get_recommended_pipeline_for_task(
        self,
        task_type: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> ProcessingPipeline:
        """
        Get recommended pipeline for a specific task type.
        
        Args:
            task_type: Type of task to perform
            constraints: Optional constraints (cost, time, quality)
            
        Returns:
            Recommended ProcessingPipeline
        """
        # Map task types to capabilities
        task_capability_map = {
            'categorization': PipelineCapability.CATEGORIZATION,
            'summarization': PipelineCapability.SUMMARIZATION,
            'sentiment_analysis': PipelineCapability.SENTIMENT_ANALYSIS,
            'information_extraction': PipelineCapability.INFORMATION_EXTRACTION,
            'question_answering': PipelineCapability.QUESTION_ANSWERING,
            'pattern_detection': PipelineCapability.PATTERN_DETECTION,
            'analysis': PipelineCapability.CATEGORIZATION  # Default
        }
        
        required_capability = task_capability_map.get(
            task_type, PipelineCapability.CATEGORIZATION
        )
        
        # Get available pipelines with required capability
        available = self.get_available_pipelines()
        capable = self.filter_by_capability(available, required_capability)
        
        if not capable:
            logger.warning(f"No pipelines available for {task_type}, using fallback")
            return ProcessingPipeline.EMBEDDING_ONLY
        
        # Apply constraints if provided
        if constraints:
            capable = self._apply_constraints(capable, constraints)
        
        # Default selection logic: prefer balanced approach
        if ProcessingPipeline.HYBRID in capable:
            return ProcessingPipeline.HYBRID
        elif ProcessingPipeline.EMBEDDING_ONLY in capable:
            return ProcessingPipeline.EMBEDDING_ONLY
        else:
            return capable[0]
    
    def _apply_constraints(
        self,
        pipelines: List[ProcessingPipeline],
        constraints: Dict[str, Any]
    ) -> List[ProcessingPipeline]:
        """Apply constraints to filter pipeline options."""
        filtered = pipelines.copy()
        
        # Cost constraints
        if constraints.get('max_cost'):
            max_cost = constraints['max_cost']
            if max_cost < 0.001:  # Very low cost
                filtered = [p for p in filtered if p == ProcessingPipeline.EMBEDDING_ONLY]
            elif max_cost < 0.01:  # Medium cost
                filtered = [p for p in filtered if p != ProcessingPipeline.LLM_ONLY]
        
        # Time constraints
        if constraints.get('max_time'):
            max_time = constraints['max_time']
            if max_time < 0.2:  # Very fast
                filtered = [p for p in filtered if p == ProcessingPipeline.EMBEDDING_ONLY]
            elif max_time < 1.0:  # Medium speed
                filtered = [p for p in filtered if p != ProcessingPipeline.LLM_ONLY]
        
        # Quality constraints
        if constraints.get('min_quality'):
            min_quality = constraints['min_quality']
            if min_quality > 0.9:  # High quality
                filtered = [p for p in filtered if p != ProcessingPipeline.EMBEDDING_ONLY]
        
        return filtered if filtered else pipelines
    
    def get_selector_stats(self) -> Dict[str, Any]:
        """Get selector statistics for monitoring."""
        return {
            'pipeline_status': {
                pipeline.value: status
                for pipeline, status in self._pipeline_status.items()
            },
            'available_count': len(self.get_available_pipelines()),
            'total_pipelines': len(ProcessingPipeline)
        }
