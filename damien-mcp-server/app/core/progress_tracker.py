"""
Progress Tracker for MCP Server

Provides real-time progress tracking for long-running operations
with callback support and detailed metrics.
"""

import time
import uuid
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OperationStatus(Enum):
    """Status of tracked operations."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressStep:
    """Individual step in a tracked operation."""
    step_id: str
    name: str
    description: str
    completed: bool = False
    progress_percent: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class TrackedOperation:
    """Represents a tracked operation with progress."""
    
    def __init__(self, operation_id: str, name: str, total_items: int = 0, steps: List[tuple] = None):
        self.operation_id = operation_id
        self.name = name
        self.total_items = total_items
        self.items_processed = 0
        self.status = OperationStatus.RUNNING
        self.start_time = datetime.now()
        self.end_time = None
        self.current_message = ""
        self.error_message = None
        
        # Initialize steps
        self.steps = []
        self.current_step_index = 0
        
        if steps:
            for i, (step_id, name, description) in enumerate(steps):
                step = ProgressStep(step_id, name, description)
                if i == 0:  # Start first step
                    step.start_time = self.start_time
                self.steps.append(step)
    
    @property
    def overall_progress(self) -> float:
        """Calculate overall progress percentage."""
        if self.steps:
            # Step-based progress
            completed_steps = sum(1 for step in self.steps if step.completed)
            current_step_progress = 0.0
            
            if self.current_step_index < len(self.steps):
                current_step_progress = self.steps[self.current_step_index].progress_percent / 100.0
            
            return ((completed_steps + current_step_progress) / len(self.steps)) * 100.0
        elif self.total_items > 0:
            # Item-based progress
            return (self.items_processed / self.total_items) * 100.0
        else:
            return 0.0
    
    @property
    def elapsed_time_seconds(self) -> float:
        """Calculate elapsed time."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def current_step(self) -> Optional[ProgressStep]:
        """Get current step."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None


class ProgressTracker:
    """Tracks progress of operations with real-time updates."""
    
    def __init__(self):
        self.operations: Dict[str, TrackedOperation] = {}
        self.callbacks: List[Callable] = []
        logger.info("Progress tracker initialized")
    
    def create_operation(
        self,
        name: str,
        total_items: int = 0,
        steps: List[tuple] = None,
        operation_id: Optional[str] = None
    ) -> TrackedOperation:
        """Create a new tracked operation."""
        if not operation_id:
            operation_id = f"op_{uuid.uuid4().hex[:8]}"
        
        operation = TrackedOperation(operation_id, name, total_items, steps)
        self.operations[operation_id] = operation
        
        logger.info(f"Created tracked operation: {name} ({operation_id})")
        return operation
    
    def update_progress(
        self,
        operation_id: str,
        items_processed: Optional[int] = None,
        step_progress: Optional[float] = None,
        message: Optional[str] = None
    ):
        """Update progress for an operation."""
        operation = self.operations.get(operation_id)
        if not operation:
            return
        
        if items_processed is not None:
            operation.items_processed = items_processed
        
        if step_progress is not None and operation.current_step:
            operation.current_step.progress_percent = min(100.0, step_progress)
        
        if message:
            operation.current_message = message
        
        # Notify callbacks
        self._notify_callbacks(operation)
    
    def advance_step(self, operation_id: str, message: Optional[str] = None) -> bool:
        """Advance to next step in operation."""
        operation = self.operations.get(operation_id)
        if not operation or not operation.steps:
            return False
        
        # Complete current step
        if operation.current_step:
            operation.current_step.completed = True
            operation.current_step.progress_percent = 100.0
            operation.current_step.end_time = datetime.now()
        
        # Move to next step
        operation.current_step_index += 1
        
        if operation.current_step_index < len(operation.steps):
            # Start next step
            next_step = operation.steps[operation.current_step_index]
            next_step.start_time = datetime.now()
            
            if message:
                operation.current_message = message
            
            self._notify_callbacks(operation)
            return True
        
        return False
    
    def complete_operation(self, operation_id: str, message: Optional[str] = None):
        """Mark operation as completed."""
        operation = self.operations.get(operation_id)
        if not operation:
            return
        
        operation.status = OperationStatus.COMPLETED
        operation.end_time = datetime.now()
        
        # Complete any remaining steps
        for step in operation.steps:
            if not step.completed:
                step.completed = True
                step.progress_percent = 100.0
                step.end_time = operation.end_time
        
        if message:
            operation.current_message = message
        
        self._notify_callbacks(operation)
        logger.info(f"Completed operation: {operation.name} ({operation_id})")
    
    def fail_operation(self, operation_id: str, error_message: str):
        """Mark operation as failed."""
        operation = self.operations.get(operation_id)
        if not operation:
            return
        
        operation.status = OperationStatus.FAILED
        operation.end_time = datetime.now()
        operation.error_message = error_message
        
        self._notify_callbacks(operation)
        logger.error(f"Failed operation: {operation.name} ({operation_id}) - {error_message}")
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of an operation."""
        operation = self.operations.get(operation_id)
        if not operation:
            return None
        
        return {
            "operation_id": operation.operation_id,
            "name": operation.name,
            "status": operation.status.value,
            "overall_progress": operation.overall_progress,
            "current_message": operation.current_message,
            "error_message": operation.error_message,
            "elapsed_time_seconds": operation.elapsed_time_seconds,
            "start_time": operation.start_time.isoformat(),
            "end_time": operation.end_time.isoformat() if operation.end_time else None,
            "total_items": operation.total_items,
            "items_processed": operation.items_processed,
            "current_step": {
                "name": operation.current_step.name,
                "description": operation.current_step.description,
                "progress": operation.current_step.progress_percent
            } if operation.current_step else None,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "description": step.description,
                    "completed": step.completed,
                    "progress": step.progress_percent
                }
                for step in operation.steps
            ]
        }
    
    def list_operations(self) -> List[Dict[str, Any]]:
        """List all tracked operations."""
        return [self.get_operation_status(op_id) for op_id in self.operations.keys()]
    
    def add_callback(self, callback: Callable[[TrackedOperation], None]):
        """Add progress callback."""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self, operation: TrackedOperation):
        """Notify all callbacks of progress update."""
        for callback in self.callbacks:
            try:
                callback(operation)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
    
    def cleanup_completed(self, max_age_hours: int = 24):
        """Cleanup old completed operations."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for op_id, operation in self.operations.items():
            if (operation.status in [OperationStatus.COMPLETED, OperationStatus.FAILED] and
                operation.end_time and operation.end_time < cutoff_time):
                to_remove.append(op_id)
        
        for op_id in to_remove:
            del self.operations[op_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old operations")
