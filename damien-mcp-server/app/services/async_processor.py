"""
Async Task Processor

Handles asynchronous processing of long-running AI intelligence tasks
with progress tracking and non-blocking operations.
"""

import asyncio
import time
import uuid
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of async tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AsyncTask:
    """Represents an async processing task."""
    
    def __init__(self, task_id: str, name: str, processor_func: Callable, parameters: Dict[str, Any]):
        self.task_id = task_id
        self.name = name
        self.processor_func = processor_func
        self.parameters = parameters
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.progress = 0.0
        self.message = ""


class AsyncTaskProcessor:
    """Processes tasks asynchronously with progress tracking."""
    
    def __init__(self):
        self.active_tasks: Dict[str, AsyncTask] = {}
        self.completed_tasks: Dict[str, AsyncTask] = {}
        self.max_completed_tasks = 100  # Keep last 100 completed tasks
        logger.info("Async task processor initialized")
    
    async def submit_task(
        self,
        name: str,
        processor_func: Callable,
        parameters: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> str:
        """Submit a task for async processing."""
        if not task_id:
            task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = AsyncTask(task_id, name, processor_func, parameters)
        self.active_tasks[task_id] = task
        
        # Start processing in background
        asyncio.create_task(self._process_task(task))
        
        logger.info(f"Submitted async task: {name} ({task_id})")
        return task_id
    
    async def _process_task(self, task: AsyncTask):
        """Process a single task."""
        try:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
            
            # Execute the processor function
            if asyncio.iscoroutinefunction(task.processor_func):
                task.result = await task.processor_func(task.parameters)
            else:
                task.result = task.processor_func(task.parameters)
            
            task.status = TaskStatus.COMPLETED
            task.progress = 100.0
            task.message = "Task completed successfully"
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.message = f"Task failed: {e}"
            logger.error(f"Task {task.task_id} failed: {e}")
        
        finally:
            task.end_time = datetime.now()
            
            # Move to completed tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            self.completed_tasks[task.task_id] = task
            
            # Cleanup old completed tasks
            if len(self.completed_tasks) > self.max_completed_tasks:
                oldest_task_id = min(self.completed_tasks.keys(), 
                                   key=lambda tid: self.completed_tasks[tid].end_time)
                del self.completed_tasks[oldest_task_id]
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task."""
        task = self.active_tasks.get(task_id) or self.completed_tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status.value,
            "progress": task.progress,
            "message": task.message,
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "end_time": task.end_time.isoformat() if task.end_time else None,
            "result": task.result if task.status == TaskStatus.COMPLETED else None,
            "error": task.error if task.status == TaskStatus.FAILED else None
        }
    
    def list_active_tasks(self) -> List[Dict[str, Any]]:
        """List all active tasks."""
        return [self.get_task_status(task_id) for task_id in self.active_tasks.keys()]
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.end_time = datetime.now()
            task.message = "Task cancelled by user"
            
            # Move to completed
            del self.active_tasks[task_id]
            self.completed_tasks[task_id] = task
            
            logger.info(f"Cancelled task: {task_id}")
            return True
        
        return False
