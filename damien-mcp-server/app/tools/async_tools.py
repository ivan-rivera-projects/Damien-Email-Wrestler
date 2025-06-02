"""
Async Tools for Background Job Processing

This module implements the async email processing tools that enable
large-scale operations without timeout issues.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from ..services.async_processor import AsyncTaskProcessor, TaskStatus
from ..services.tool_registry import tool_registry, ToolDefinition

logger = logging.getLogger("damien_mcp_server_app")

# Global async processor instance
async_processor = AsyncTaskProcessor()


async def damien_ai_analyze_emails_async_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for async large-scale email analysis."""
    try:
        # Extract parameters with defaults
        days = params.get("days", 30)
        target_count = params.get("target_count", 1000)
        min_confidence = params.get("min_confidence", 0.85)
        query = params.get("query", "")
        use_statistical_validation = params.get("use_statistical_validation", True)
        
        # Define the async email analysis function
        async def analyze_emails_task(task_params):
            # Import here to avoid circular imports
            from ..services.cli_bridge import CLIBridge
            
            # Get CLI bridge instance for large-scale operations
            cli_bridge = CLIBridge()
            await cli_bridge.ensure_initialized()
            
            # Fetch emails using the working email fetching mechanism
            emails_result = await cli_bridge.fetch_emails(
                days=task_params["days"],
                max_emails=task_params["target_count"],
                query=task_params["query"]
            )
            
            # Analyze patterns using the fixed analysis method
            analysis_result = await cli_bridge.analyze_email_patterns(
                emails=emails_result.get("emails", []),
                min_confidence=task_params["min_confidence"]
            )
            
            # Generate business insights
            insights_result = await cli_bridge.generate_business_insights(
                analysis_data=analysis_result,
                output_format="detailed"
            )
            
            # Return comprehensive results
            return {
                "status": "success",
                "emails_analyzed": len(emails_result.get("emails", [])),
                "patterns_detected": len(analysis_result.get("patterns", [])),
                "insights": insights_result,
                "processing_metadata": {
                    "emails_fetched": emails_result.get("total_fetched", 0),
                    "pattern_coverage_percentage": analysis_result.get("pattern_coverage_percentage", 0),
                    "confidence_threshold": task_params["min_confidence"],
                    "use_statistical_validation": task_params["use_statistical_validation"]
                }
            }
        
        # Submit task for background processing
        task_id = await async_processor.submit_task(
            name=f"Large-scale email analysis ({target_count} emails)",
            processor_func=analyze_emails_task,
            parameters={
                "days": days,
                "target_count": target_count,
                "min_confidence": min_confidence,
                "query": query,
                "use_statistical_validation": use_statistical_validation
            }
        )
        
        # Estimate duration (rough calculation)
        estimated_duration_minutes = max(1, target_count // 100)  # ~1 minute per 100 emails
        
        logger.info(f"Started async email analysis task {task_id} for {target_count} emails")
        
        return {
            "success": True,
            "job_id": task_id,
            "status": "started",
            "message": f"Background analysis started for {target_count} emails",
            "estimated_duration_minutes": estimated_duration_minutes,
            "tracking": {
                "use_damien_job_get_status": f"Check progress with damien_job_get_status(job_id='{task_id}')",
                "use_damien_job_get_result": f"Get results with damien_job_get_result(job_id='{task_id}') when complete"
            }
        }
        
    except Exception as e:
        logger.error(f"Error starting async email analysis: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to start async analysis: {str(e)}"
        }


async def damien_job_get_status_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getting job status."""
    try:
        job_id = params.get("job_id")
        if not job_id:
            return {
                "success": False,
                "error": "job_id parameter is required"
            }
        
        status = async_processor.get_task_status(job_id)
        if not status:
            return {
                "success": False,
                "error": f"Job {job_id} not found"
            }
        
        return {
            "success": True,
            "job_id": job_id,
            "status": status["status"],
            "progress": {
                "percentage": status["progress"],
                "message": status["message"],
                "start_time": status["start_time"],
                "end_time": status["end_time"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get job status: {str(e)}"
        }


async def damien_job_get_result_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getting job results."""
    try:
        job_id = params.get("job_id")
        if not job_id:
            return {
                "success": False,
                "error": "job_id parameter is required"
            }
        
        status = async_processor.get_task_status(job_id)
        if not status:
            return {
                "success": False,
                "error": f"Job {job_id} not found"
            }
        
        if status["status"] != TaskStatus.COMPLETED.value:
            return {
                "success": False,
                "error": f"Job {job_id} is not completed yet. Current status: {status['status']}"
            }
        
        return {
            "success": True,
            "job_id": job_id,
            "status": "completed",
            "result": status["result"]
        }
        
    except Exception as e:
        logger.error(f"Error getting job result: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get job result: {str(e)}"
        }


async def damien_job_cancel_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for canceling a job."""
    try:
        job_id = params.get("job_id")
        if not job_id:
            return {
                "success": False,
                "error": "job_id parameter is required"
            }
        
        cancelled = async_processor.cancel_task(job_id)
        if not cancelled:
            return {
                "success": False,
                "error": f"Job {job_id} not found or already completed"
            }
        
        logger.info(f"Cancelled job {job_id}")
        
        return {
            "success": True,
            "job_id": job_id,
            "status": "cancelled",
            "message": f"Job {job_id} has been cancelled"
        }
        
    except Exception as e:
        logger.error(f"Error cancelling job: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to cancel job: {str(e)}"
        }


async def damien_job_list_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for listing active jobs."""
    try:
        active_tasks = async_processor.list_active_tasks()
        
        return {
            "success": True,
            "active_jobs": active_tasks,
            "count": len(active_tasks)
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to list jobs: {str(e)}"
        }


def register_async_tools():
    """Register all async job processing tools."""
    logger.info("🚀 Starting registration of async job processing tools...")
    
    # Async email analysis tool
    tool_def1 = ToolDefinition(
        name="damien_ai_analyze_emails_async",
        description="🚀 LARGE-SCALE BACKGROUND EMAIL ANALYSIS - No more timeouts! Processes 3,000+ emails in background with progress tracking.",
        input_schema={
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 30,
                    "description": "Number of days to analyze (default: 30)"
                },
                "target_count": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10000,
                    "default": 1000,
                    "description": "Target number of emails to analyze (default: 1000)"
                },
                "min_confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.85,
                    "description": "Minimum confidence threshold for patterns (default: 0.85)"
                },
                "query": {
                    "type": "string",
                    "default": "",
                    "description": "Optional Gmail search query (e.g., 'is:unread')"
                },
                "use_statistical_validation": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable statistical validation (default: true)"
                }
            }
        },
        handler="damien_ai_analyze_emails_async"
    )
    tool_registry.register_tool(tool_def1, damien_ai_analyze_emails_async_handler)
    
    # Job status tool
    tool_def2 = ToolDefinition(
        name="damien_job_get_status",
        description="📊 Track background job progress with real-time updates",
        input_schema={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID to check status for"
                }
            },
            "required": ["job_id"]
        },
        handler="damien_job_get_status"
    )
    tool_registry.register_tool(tool_def2, damien_job_get_status_handler)
    
    # Job result tool
    tool_def3 = ToolDefinition(
        name="damien_job_get_result",
        description="🎯 Get comprehensive analysis results when job completes",
        input_schema={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID to get results for"
                }
            },
            "required": ["job_id"]
        },
        handler="damien_job_get_result"
    )
    tool_registry.register_tool(tool_def3, damien_job_get_result_handler)
    
    # Job cancel tool
    tool_def4 = ToolDefinition(
        name="damien_job_cancel",
        description="❌ Cancel a running background job",
        input_schema={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID to cancel"
                }
            },
            "required": ["job_id"]
        },
        handler="damien_job_cancel"
    )
    tool_registry.register_tool(tool_def4, damien_job_cancel_handler)
    
    # Job list tool
    tool_def5 = ToolDefinition(
        name="damien_job_list",
        description="📋 List all active background jobs",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler="damien_job_list"
    )
    tool_registry.register_tool(tool_def5, damien_job_list_handler)
    
    logger.info("✅ Successfully registered 5 async job processing tools")


# Export registration function
__all__ = ["register_async_tools"]
