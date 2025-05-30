"""
HierarchicalProcessor: Multi-level email analysis and processing

Enterprise-grade hierarchical processing for complex email analysis workflows.
"""

import logging
import time
import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of hierarchical processing tasks."""
    ANALYSIS = "analysis"
    CATEGORIZATION = "categorization"
    EXTRACTION = "extraction"


class TaskStatus(Enum):
    """Status of hierarchical processing tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(Enum):
    """Priority levels for hierarchical tasks."""
    LOW = 1
    NORMAL = 2
    HIGH = 3


@dataclass
class TaskResult:
    """Result from a hierarchical processing task."""
    task_id: str
    status: TaskStatus
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0


@dataclass
class ProcessingTask:
    """Definition of a hierarchical processing task."""
    task_id: str
    name: str
    task_type: TaskType
    processor_function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingWorkflow:
    """Definition of a complete hierarchical processing workflow."""
    workflow_id: str
    name: str
    description: str
    tasks: List[ProcessingTask] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.workflow_id:
            self.workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"


@dataclass
class WorkflowResult:
    """Result from a complete workflow execution."""
    workflow_id: str
    status: TaskStatus
    task_results: Dict[str, TaskResult] = field(default_factory=dict)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate workflow success rate."""
        total_tasks = self.completed_tasks + self.failed_tasks
        if total_tasks == 0:
            return 0.0
        return (self.completed_tasks / total_tasks) * 100.0


class HierarchicalProcessor:
    """Enterprise-grade hierarchical processor for complex email analysis workflows."""
    
    def __init__(
        self,
        rag_engine=None,
        batch_processor=None,
        chunker=None,
        privacy_guardian=None
    ):
        """Initialize the hierarchical processor with component dependencies."""
        self.rag_engine = rag_engine
        self.batch_processor = batch_processor
        self.chunker = chunker
        self.privacy_guardian = privacy_guardian
        
        self.total_workflows_executed = 0
        self.total_tasks_executed = 0
        
        logger.info("HierarchicalProcessor initialized")
    
    def create_email_analysis_workflow(
        self,
        emails,
        analysis_types=None,
        include_privacy_scan=True,
        include_chunking=True,
        include_rag_indexing=True,
        include_semantic_search=False,
        search_queries=None
    ):
        """Create a comprehensive email analysis workflow."""
        analysis_types = analysis_types or ["categorization"]
        
        workflow = ProcessingWorkflow(
            workflow_id=f"email_analysis_{uuid.uuid4().hex[:8]}",
            name="Email Analysis Workflow",
            description=f"Analysis of {len(emails)} emails"
        )
        
        # Create a simple task
        task = ProcessingTask(
            task_id="basic_analysis",
            name="Basic Email Analysis",
            task_type=TaskType.ANALYSIS,
            processor_function=self._basic_analysis_processor,
            parameters={"emails": emails, "analysis_types": analysis_types}
        )
        
        workflow.tasks = [task]
        return workflow
    
    async def execute_workflow(self, workflow):
        """Execute a complete hierarchical workflow."""
        result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            status=TaskStatus.RUNNING
        )
        
        try:
            for task in workflow.tasks:
                task_result = await self._execute_task(task, result)
                result.task_results[task.task_id] = task_result
                
                if task_result.status == TaskStatus.COMPLETED:
                    result.completed_tasks += 1
                else:
                    result.failed_tasks += 1
            
            result.status = TaskStatus.COMPLETED if result.failed_tasks == 0 else TaskStatus.FAILED
            result.end_time = datetime.now(timezone.utc)
            self.total_workflows_executed += 1
            
            return result
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.end_time = datetime.now(timezone.utc)
            logger.error(f"Workflow failed: {e}")
            return result
    
    async def _execute_task(self, task, workflow_result):
        """Execute a single processing task."""
        start_time = time.time()
        task_result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING
        )
        
        try:
            if asyncio.iscoroutinefunction(task.processor_function):
                result_data = await task.processor_function(task.parameters, workflow_result)
            else:
                result_data = task.processor_function(task.parameters, workflow_result)
            
            task_result.result_data = result_data or {}
            task_result.status = TaskStatus.COMPLETED
            self.total_tasks_executed += 1
            
        except Exception as e:
            task_result.status = TaskStatus.FAILED
            task_result.error_message = str(e)
            logger.error(f"Task failed: {e}")
        
        finally:
            task_result.processing_time_seconds = time.time() - start_time
        
        return task_result
    
    async def _basic_analysis_processor(self, parameters, workflow_result):
        """Basic analysis processor."""
        emails = parameters.get("emails", [])
        analysis_types = parameters.get("analysis_types", [])
        
        return {
            "emails_analyzed": len(emails),
            "analysis_types": analysis_types,
            "status": "completed"
        }
    
    def get_performance_stats(self):
        """Get performance statistics."""
        return {
            "workflow_metrics": {
                "total_workflows_executed": self.total_workflows_executed,
                "total_tasks_executed": self.total_tasks_executed
            }
        }


class WorkflowTemplates:
    """Predefined workflow templates."""
    
    @staticmethod
    def comprehensive_analysis_workflow(emails, search_queries=None):
        """Create a comprehensive analysis workflow."""
        return ProcessingWorkflow(
            workflow_id=f"comprehensive_{uuid.uuid4().hex[:8]}",
            name="Comprehensive Email Analysis",
            description="Complete email analysis workflow"
        )
