"""
ProgressTracker: Real-time processing updates for large operations

Enterprise-grade progress tracking for email processing operations with real-time updates,
performance monitoring, and user feedback capabilities.
"""

import logging
import time
import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class ProgressType(Enum):
    """Types of progress tracking operations."""
    INDEXING = "indexing"
    PROCESSING = "processing"
    SEARCHING = "searching"
    ANALYSIS = "analysis"
    WORKFLOW = "workflow"
    BATCH = "batch"


class ProgressStatus(Enum):
    """Status of progress tracking operations."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressStep:
    """Individual step in a progress tracking operation."""
    step_id: str
    name: str
    description: str
    weight: float = 1.0  # Relative weight for progress calculation
    status: ProgressStatus = ProgressStatus.INITIALIZING
    progress_percent: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate step duration in seconds."""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now(timezone.utc)
        return (end - self.start_time).total_seconds()
    
    @property
    def is_completed(self) -> bool:
        """Check if step is completed."""
        return self.status in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELLED]


@dataclass
class ProgressSnapshot:
    """Snapshot of progress at a specific time."""
    operation_id: str
    timestamp: datetime
    overall_progress_percent: float
    current_step: Optional[str]
    steps_completed: int
    total_steps: int
    estimated_time_remaining_seconds: Optional[float]
    throughput_items_per_second: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressCallbackData:
    """Data passed to progress callbacks."""
    operation_id: str
    progress_type: ProgressType
    overall_progress_percent: float
    current_step_name: str
    current_step_progress: float
    message: str
    items_processed: int
    total_items: int
    elapsed_time_seconds: float
    estimated_time_remaining_seconds: Optional[float]
    throughput_items_per_second: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProgressTracker:
    """Enterprise-grade progress tracker for email processing operations."""
    
    def __init__(
        self,
        enable_callbacks: bool = True,
        enable_snapshots: bool = True,
        snapshot_interval_seconds: float = 1.0,
        max_snapshots_per_operation: int = 1000
    ):
        """Initialize the progress tracker."""
        self.enable_callbacks = enable_callbacks
        self.enable_snapshots = enable_snapshots
        self.snapshot_interval_seconds = snapshot_interval_seconds
        self.max_snapshots_per_operation = max_snapshots_per_operation
        
        # Active operations tracking
        self.active_operations: Dict[str, 'ProgressOperation'] = {}
        self.operation_snapshots: Dict[str, List[ProgressSnapshot]] = {}
        
        # Callbacks
        self.global_callbacks: List[Callable[[ProgressCallbackData], None]] = []
        self.operation_callbacks: Dict[str, List[Callable[[ProgressCallbackData], None]]] = {}
        
        # Performance tracking
        self.total_operations_tracked = 0
        self.completed_operations = 0
        self.failed_operations = 0
        
        logger.info("ProgressTracker initialized")
    
    def create_operation(
        self,
        operation_id: str = None,
        name: str = "Processing Operation",
        progress_type: ProgressType = ProgressType.PROCESSING,
        total_items: int = 0,
        steps: List[ProgressStep] = None
    ) -> 'ProgressOperation':
        """Create a new progress tracking operation."""
        if not operation_id:
            operation_id = f"{progress_type.value}_{uuid.uuid4().hex[:8]}"
        
        operation = ProgressOperation(
            operation_id=operation_id,
            name=name,
            progress_type=progress_type,
            total_items=total_items,
            steps=steps or [],
            tracker=self
        )
        
        self.active_operations[operation_id] = operation
        self.operation_snapshots[operation_id] = []
        self.total_operations_tracked += 1
        
        logger.info(f"Created progress operation: {name} ({operation_id})")
        return operation
    
    def add_global_callback(self, callback: Callable[[ProgressCallbackData], None]) -> None:
        """Add a global progress callback that receives updates from all operations."""
        self.global_callbacks.append(callback)
    
    def add_operation_callback(
        self,
        operation_id: str,
        callback: Callable[[ProgressCallbackData], None]
    ) -> None:
        """Add a callback for a specific operation."""
        if operation_id not in self.operation_callbacks:
            self.operation_callbacks[operation_id] = []
        self.operation_callbacks[operation_id].append(callback)
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a progress operation."""
        operation = self.active_operations.get(operation_id)
        if not operation:
            return None
        
        return {
            "operation_id": operation.operation_id,
            "name": operation.name,
            "progress_type": operation.progress_type.value,
            "status": operation.status.value,
            "overall_progress_percent": operation.overall_progress_percent,
            "current_step": operation.current_step.name if operation.current_step else None,
            "items_processed": operation.items_processed,
            "total_items": operation.total_items,
            "elapsed_time_seconds": operation.elapsed_time_seconds,
            "estimated_time_remaining": operation.estimated_time_remaining_seconds,
            "throughput_items_per_second": operation.throughput_items_per_second,
            "steps_completed": len([s for s in operation.steps if s.is_completed]),
            "total_steps": len(operation.steps)
        }
    
    def get_operation_snapshots(self, operation_id: str) -> List[ProgressSnapshot]:
        """Get historical snapshots for an operation."""
        return self.operation_snapshots.get(operation_id, [])
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the progress tracker."""
        active_count = len(self.active_operations)
        success_rate = (
            self.completed_operations / max(1, self.completed_operations + self.failed_operations) * 100
        )
        
        return {
            "tracking_metrics": {
                "total_operations_tracked": self.total_operations_tracked,
                "active_operations": active_count,
                "completed_operations": self.completed_operations,
                "failed_operations": self.failed_operations,
                "success_rate_percent": success_rate
            },
            "callback_metrics": {
                "global_callbacks": len(self.global_callbacks),
                "operation_callbacks": sum(len(callbacks) for callbacks in self.operation_callbacks.values())
            },
            "snapshot_metrics": {
                "total_snapshots": sum(len(snapshots) for snapshots in self.operation_snapshots.values()),
                "snapshot_interval_seconds": self.snapshot_interval_seconds,
                "max_snapshots_per_operation": self.max_snapshots_per_operation
            }
        }
    
    def _fire_callbacks(self, callback_data: ProgressCallbackData) -> None:
        """Fire progress callbacks for an operation."""
        if not self.enable_callbacks:
            return
        
        try:
            # Fire global callbacks
            for callback in self.global_callbacks:
                try:
                    callback(callback_data)
                except Exception as e:
                    logger.error(f"Global callback failed: {e}")
            
            # Fire operation-specific callbacks
            operation_callbacks = self.operation_callbacks.get(callback_data.operation_id, [])
            for callback in operation_callbacks:
                try:
                    callback(callback_data)
                except Exception as e:
                    logger.error(f"Operation callback failed: {e}")
        
        except Exception as e:
            logger.error(f"Failed to fire callbacks: {e}")
    
    def _create_snapshot(self, operation: 'ProgressOperation') -> None:
        """Create a progress snapshot for an operation."""
        if not self.enable_snapshots:
            return
        
        try:
            snapshot = ProgressSnapshot(
                operation_id=operation.operation_id,
                timestamp=datetime.now(timezone.utc),
                overall_progress_percent=operation.overall_progress_percent,
                current_step=operation.current_step.name if operation.current_step else None,
                steps_completed=len([s for s in operation.steps if s.is_completed]),
                total_steps=len(operation.steps),
                estimated_time_remaining_seconds=operation.estimated_time_remaining_seconds,
                throughput_items_per_second=operation.throughput_items_per_second,
                metadata={
                    "items_processed": operation.items_processed,
                    "total_items": operation.total_items,
                    "status": operation.status.value
                }
            )
            
            # Add snapshot and maintain size limit
            snapshots = self.operation_snapshots[operation.operation_id]
            snapshots.append(snapshot)
            
            if len(snapshots) > self.max_snapshots_per_operation:
                # Remove oldest snapshots, keeping the most recent ones
                snapshots[:] = snapshots[-self.max_snapshots_per_operation:]
        
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
    
    def _cleanup_operation(self, operation_id: str) -> None:
        """Clean up completed operation."""
        try:
            if operation_id in self.active_operations:
                operation = self.active_operations[operation_id]
                
                # Update completion stats
                if operation.status == ProgressStatus.COMPLETED:
                    self.completed_operations += 1
                elif operation.status == ProgressStatus.FAILED:
                    self.failed_operations += 1
                
                # Remove from active operations
                del self.active_operations[operation_id]
                
                # Clean up operation callbacks
                if operation_id in self.operation_callbacks:
                    del self.operation_callbacks[operation_id]
                
                logger.debug(f"Cleaned up operation: {operation_id}")
        
        except Exception as e:
            logger.error(f"Failed to cleanup operation {operation_id}: {e}")


class ProgressOperation:
    """Individual progress tracking operation."""
    
    def __init__(
        self,
        operation_id: str,
        name: str,
        progress_type: ProgressType,
        total_items: int,
        steps: List[ProgressStep],
        tracker: ProgressTracker
    ):
        """Initialize a progress operation."""
        self.operation_id = operation_id
        self.name = name
        self.progress_type = progress_type
        self.total_items = total_items
        self.steps = steps
        self.tracker = tracker
        
        # State tracking
        self.status = ProgressStatus.INITIALIZING
        self.items_processed = 0
        self.current_step: Optional[ProgressStep] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Performance tracking
        self.last_snapshot_time = time.time()
        self.items_processed_at_last_snapshot = 0
        
        # Initialize first step if available
        if self.steps:
            self.current_step = self.steps[0]
    
    @property
    def elapsed_time_seconds(self) -> float:
        """Calculate elapsed time since operation start."""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now(timezone.utc)
        return (end - self.start_time).total_seconds()
    
    @property
    def overall_progress_percent(self) -> float:
        """Calculate overall progress percentage."""
        if not self.steps:
            # Item-based progress
            if self.total_items == 0:
                return 0.0
            return min(100.0, (self.items_processed / self.total_items) * 100.0)
        
        # Step-based progress with weights
        total_weight = sum(step.weight for step in self.steps)
        if total_weight == 0:
            return 0.0
        
        completed_weight = 0.0
        for step in self.steps:
            if step.status == ProgressStatus.COMPLETED:
                completed_weight += step.weight
            elif step.status == ProgressStatus.RUNNING and step == self.current_step:
                completed_weight += step.weight * (step.progress_percent / 100.0)
        
        return min(100.0, (completed_weight / total_weight) * 100.0)
    
    @property
    def throughput_items_per_second(self) -> float:
        """Calculate current throughput in items per second."""
        elapsed = self.elapsed_time_seconds
        if elapsed == 0:
            return 0.0
        return self.items_processed / elapsed
    
    @property
    def estimated_time_remaining_seconds(self) -> Optional[float]:
        """Estimate remaining time based on current throughput."""
        if self.total_items == 0 or self.items_processed == 0:
            return None
        
        throughput = self.throughput_items_per_second
        if throughput == 0:
            return None
        
        remaining_items = self.total_items - self.items_processed
        return remaining_items / throughput
    
    def start(self) -> None:
        """Start the progress operation."""
        self.status = ProgressStatus.RUNNING
        self.start_time = datetime.now(timezone.utc)
        
        if self.current_step:
            self.current_step.status = ProgressStatus.RUNNING
            self.current_step.start_time = self.start_time
        
        self._update_progress("Operation started")
        logger.info(f"Started progress operation: {self.name} ({self.operation_id})")
    
    def update_progress(
        self,
        items_processed: int = None,
        step_progress_percent: float = None,
        message: str = "",
        metadata: Dict[str, Any] = None
    ) -> None:
        """Update progress information."""
        if items_processed is not None:
            self.items_processed = items_processed
        
        if step_progress_percent is not None and self.current_step:
            self.current_step.progress_percent = min(100.0, step_progress_percent)
        
        self._update_progress(message, metadata)
    
    def advance_step(self, message: str = "", metadata: Dict[str, Any] = None) -> bool:
        """Advance to the next step in the operation."""
        if not self.steps:
            return False
        
        # Complete current step
        if self.current_step:
            self.current_step.status = ProgressStatus.COMPLETED
            self.current_step.end_time = datetime.now(timezone.utc)
            self.current_step.progress_percent = 100.0
        
        # Find next step
        current_index = -1
        if self.current_step:
            for i, step in enumerate(self.steps):
                if step.step_id == self.current_step.step_id:
                    current_index = i
                    break
        
        next_index = current_index + 1
        if next_index < len(self.steps):
            self.current_step = self.steps[next_index]
            self.current_step.status = ProgressStatus.RUNNING
            self.current_step.start_time = datetime.now(timezone.utc)
            
            self._update_progress(message or f"Advanced to step: {self.current_step.name}", metadata)
            return True
        
        return False
    
    def complete(self, message: str = "Operation completed", metadata: Dict[str, Any] = None) -> None:
        """Complete the progress operation."""
        self.status = ProgressStatus.COMPLETED
        self.end_time = datetime.now(timezone.utc)
        
        # Complete current step if running
        if self.current_step and self.current_step.status == ProgressStatus.RUNNING:
            self.current_step.status = ProgressStatus.COMPLETED
            self.current_step.end_time = self.end_time
            self.current_step.progress_percent = 100.0
        
        self._update_progress(message, metadata)
        self.tracker._cleanup_operation(self.operation_id)
        
        logger.info(f"Completed progress operation: {self.name} ({self.operation_id}) "
                   f"in {self.elapsed_time_seconds:.2f}s")
    
    def fail(self, error_message: str, metadata: Dict[str, Any] = None) -> None:
        """Mark the operation as failed."""
        self.status = ProgressStatus.FAILED
        self.end_time = datetime.now(timezone.utc)
        
        # Fail current step if running
        if self.current_step and self.current_step.status == ProgressStatus.RUNNING:
            self.current_step.status = ProgressStatus.FAILED
            self.current_step.end_time = self.end_time
        
        self._update_progress(f"Operation failed: {error_message}", metadata)
        self.tracker._cleanup_operation(self.operation_id)
        
        logger.error(f"Failed progress operation: {self.name} ({self.operation_id}) - {error_message}")
    
    def cancel(self, message: str = "Operation cancelled", metadata: Dict[str, Any] = None) -> None:
        """Cancel the progress operation."""
        self.status = ProgressStatus.CANCELLED
        self.end_time = datetime.now(timezone.utc)
        
        # Cancel current step if running
        if self.current_step and self.current_step.status == ProgressStatus.RUNNING:
            self.current_step.status = ProgressStatus.CANCELLED
            self.current_step.end_time = self.end_time
        
        self._update_progress(message, metadata)
        self.tracker._cleanup_operation(self.operation_id)
        
        logger.info(f"Cancelled progress operation: {self.name} ({self.operation_id})")
    
    def _update_progress(self, message: str = "", metadata: Dict[str, Any] = None) -> None:
        """Internal method to update progress and fire callbacks."""
        current_time = time.time()
        
        # Create callback data
        callback_data = ProgressCallbackData(
            operation_id=self.operation_id,
            progress_type=self.progress_type,
            overall_progress_percent=self.overall_progress_percent,
            current_step_name=self.current_step.name if self.current_step else "",
            current_step_progress=self.current_step.progress_percent if self.current_step else 0.0,
            message=message,
            items_processed=self.items_processed,
            total_items=self.total_items,
            elapsed_time_seconds=self.elapsed_time_seconds,
            estimated_time_remaining_seconds=self.estimated_time_remaining_seconds,
            throughput_items_per_second=self.throughput_items_per_second,
            metadata=metadata or {}
        )
        
        # Fire callbacks
        self.tracker._fire_callbacks(callback_data)
        
        # Create snapshot if enough time has passed
        if current_time - self.last_snapshot_time >= self.tracker.snapshot_interval_seconds:
            self.tracker._create_snapshot(self)
            self.last_snapshot_time = current_time
    
    def add_step(
        self,
        step_id: str,
        name: str,
        description: str,
        weight: float = 1.0
    ) -> ProgressStep:
        """Add a new step to the operation."""
        step = ProgressStep(
            step_id=step_id,
            name=name,
            description=description,
            weight=weight
        )
        self.steps.append(step)
        
        # If no current step, make this the current step
        if not self.current_step and self.status == ProgressStatus.RUNNING:
            self.current_step = step
            step.status = ProgressStatus.RUNNING
            step.start_time = datetime.now(timezone.utc)
        
        return step


# Utility functions for common progress tracking scenarios

def create_batch_progress_tracker(
    operation_name: str,
    total_emails: int,
    include_chunking: bool = False,
    include_rag_indexing: bool = False
) -> ProgressOperation:
    """Create a progress tracker for batch email processing."""
    tracker = ProgressTracker()
    
    steps = [
        ProgressStep("validation", "Input Validation", "Validating email inputs", weight=0.5),
        ProgressStep("processing", "Email Processing", "Processing email content", weight=3.0)
    ]
    
    if include_chunking:
        steps.append(ProgressStep("chunking", "Content Chunking", "Chunking email content", weight=1.0))
    
    if include_rag_indexing:
        steps.append(ProgressStep("indexing", "Vector Indexing", "Creating vector index", weight=1.5))
    
    steps.append(ProgressStep("finalization", "Finalization", "Finalizing results", weight=0.5))
    
    return tracker.create_operation(
        name=operation_name,
        progress_type=ProgressType.BATCH,
        total_items=total_emails,
        steps=steps
    )


def create_rag_progress_tracker(
    operation_name: str,
    total_chunks: int
) -> ProgressOperation:
    """Create a progress tracker for RAG indexing operations."""
    tracker = ProgressTracker()
    
    steps = [
        ProgressStep("preparation", "Preparation", "Preparing for indexing", weight=0.5),
        ProgressStep("embedding", "Embedding Generation", "Generating embeddings", weight=2.0),
        ProgressStep("storage", "Vector Storage", "Storing vectors in database", weight=1.0),
        ProgressStep("verification", "Verification", "Verifying index integrity", weight=0.5)
    ]
    
    return tracker.create_operation(
        name=operation_name,
        progress_type=ProgressType.INDEXING,
        total_items=total_chunks,
        steps=steps
    )


def create_workflow_progress_tracker(
    workflow_name: str,
    total_tasks: int
) -> ProgressOperation:
    """Create a progress tracker for hierarchical workflow execution."""
    tracker = ProgressTracker()
    
    return tracker.create_operation(
        name=workflow_name,
        progress_type=ProgressType.WORKFLOW,
        total_items=total_tasks,
        steps=[]  # Steps will be added dynamically based on workflow tasks
    )
