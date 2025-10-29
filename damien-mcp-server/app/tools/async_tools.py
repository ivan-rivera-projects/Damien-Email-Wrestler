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


async def damien_ai_bulk_operations_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for AI-powered bulk operations based on analysis results."""
    try:
        # Extract parameters
        job_id = params.get("job_id")
        operation = params.get("operation", "trash")  # trash, label, archive, mark_read
        pattern_filter = params.get("pattern_filter", [])  # Filter by pattern types
        min_confidence = params.get("min_confidence", 0.85)
        max_emails = params.get("max_emails", 100)
        dry_run = params.get("dry_run", True)
        additional_params = params.get("additional_params", {})  # For label names, etc.
        
        if not job_id:
            return {
                "success": False,
                "error": "job_id parameter is required"
            }
        
        # Define the bulk operations task
        async def bulk_operations_task(task_params):
            from ..services.cli_bridge import CLIBridge
            
            cli_bridge = CLIBridge()
            await cli_bridge.ensure_initialized()
            
            # Get the analysis results
            analysis_status = async_processor.get_task_status(task_params["source_job_id"])
            if not analysis_status or analysis_status["status"] != "completed":
                raise Exception(f"Source analysis job {task_params['source_job_id']} not completed")
            
            analysis_result = analysis_status["result"]
            detailed_patterns = analysis_result.get("insights", {}).get("detailed_patterns", [])
            
            # Filter patterns by type and confidence
            target_patterns = []
            for pattern in detailed_patterns:
                pattern_type = pattern.get("pattern_type", "")
                pattern_confidence = pattern.get("confidence", 0)
                
                # Apply filters
                if pattern_filter and pattern_type not in pattern_filter:
                    continue
                if pattern_confidence < task_params["min_confidence"]:
                    continue
                
                target_patterns.append(pattern)
            
            # Collect email IDs from filtered patterns
            target_email_ids = []
            pattern_summary = []
            
            for pattern in target_patterns:
                email_ids = pattern.get("email_ids", [])
                if email_ids:
                    # Limit emails per pattern to prevent overwhelming operations
                    limited_ids = email_ids[:task_params["max_emails"]]
                    target_email_ids.extend(limited_ids)
                    
                    pattern_summary.append({
                        "pattern_type": pattern.get("pattern_type"),
                        "emails_targeted": len(limited_ids),
                        "confidence": pattern.get("confidence"),
                        "description": pattern.get("description")
                    })
            
            # Remove duplicates while preserving order
            unique_email_ids = list(dict.fromkeys(target_email_ids))
            
            # Limit total emails
            if len(unique_email_ids) > task_params["max_emails"]:
                unique_email_ids = unique_email_ids[:task_params["max_emails"]]
            
            if not unique_email_ids:
                return {
                    "status": "success",
                    "operation": task_params["operation"],
                    "emails_processed": 0,
                    "message": "No emails found matching the criteria",
                    "pattern_summary": pattern_summary,
                    "dry_run": task_params["dry_run"]
                }
            
            # Execute operation if not dry run
            operation_result = {}
            if not task_params["dry_run"]:
                operation_type = task_params["operation"]
                
                if operation_type == "trash":
                    operation_result = await cli_bridge.execute_tool_command(
                        "damien_trash_emails",
                        {"message_ids": unique_email_ids}
                    )
                elif operation_type == "label":
                    label_names = task_params["additional_params"].get("label_names", ["AI_PROCESSED"])
                    operation_result = await cli_bridge.execute_tool_command(
                        "damien_label_emails",
                        {
                            "message_ids": unique_email_ids,
                            "add_label_names": label_names
                        }
                    )
                elif operation_type == "archive":
                    # Archive by removing INBOX label
                    operation_result = await cli_bridge.execute_tool_command(
                        "damien_label_emails",
                        {
                            "message_ids": unique_email_ids,
                            "remove_label_names": ["INBOX"]
                        }
                    )
                elif operation_type == "mark_read":
                    operation_result = await cli_bridge.execute_tool_command(
                        "damien_mark_emails",
                        {
                            "message_ids": unique_email_ids,
                            "mark_as_read": True
                        }
                    )
                else:
                    raise Exception(f"Unsupported operation: {operation_type}")
            
            return {
                "status": "success",
                "operation": task_params["operation"],
                "emails_processed": len(unique_email_ids),
                "email_ids_processed": unique_email_ids,
                "pattern_summary": pattern_summary,
                "operation_result": operation_result,
                "dry_run": task_params["dry_run"],
                "confidence_threshold": task_params["min_confidence"]
            }
        
        # Submit bulk operations task
        task_id = await async_processor.submit_task(
            name=f"AI bulk {operation} ({len(pattern_filter) if pattern_filter else 'all'} patterns)",
            processor_func=bulk_operations_task,
            parameters={
                "source_job_id": job_id,
                "operation": operation,
                "pattern_filter": pattern_filter,
                "min_confidence": min_confidence,
                "max_emails": max_emails,
                "dry_run": dry_run,
                "additional_params": additional_params
            }
        )
        
        logger.info(f"Started AI bulk operations task {task_id} for {operation}")
        
        return {
            "success": True,
            "job_id": task_id,
            "status": "started",
            "operation": operation,
            "source_analysis_job": job_id,
            "message": f"Background bulk {operation} operation started",
            "dry_run": dry_run,
            "tracking": {
                "use_damien_job_get_status": f"Check progress with damien_job_get_status(job_id='{task_id}')",
                "use_damien_job_get_result": f"Get results with damien_job_get_result(job_id='{task_id}') when complete"
            }
        }
        
    except Exception as e:
        logger.error(f"Error starting AI bulk operations: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to start AI bulk operations: {str(e)}"
        }


async def damien_job_wait_for_completion_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for auto-polling job status until completion (Issue #34 Enhancement).

    This tool eliminates the need for manual polling by automatically checking
    job status at configured intervals and returning results when complete.

    Features:
    - Configurable polling intervals with optional exponential backoff
    - Smart timeout handling with partial results
    - Polling limits to prevent runaway loops
    - Optional progress updates for user visibility
    - Graceful degradation on timeout
    """
    try:
        # Extract parameters with smart defaults
        job_id = params.get("job_id")
        poll_interval = params.get("poll_interval", 10)  # 10 seconds default
        timeout = params.get("timeout", 600)  # 10 minutes default
        max_polls = params.get("max_polls", 60)  # 60 polls max
        show_progress = params.get("show_progress", True)
        exponential_backoff = params.get("exponential_backoff", True)

        # Validation
        if not job_id:
            return {
                "success": False,
                "error_message": "job_id parameter is required"
            }

        # Exponential backoff intervals: 5s → 10s → 15s → 30s
        backoff_intervals = [5, 10, 15, 30]

        # Tracking variables
        poll_count = 0
        start_time = datetime.now(timezone.utc)
        last_status = None
        progress_updates = []

        logger.info(f"Starting auto-poll for job {job_id} (interval: {poll_interval}s, timeout: {timeout}s, max_polls: {max_polls})")

        while poll_count < max_polls:
            # Check elapsed time
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed >= timeout:
                # Smart timeout handling - return partial results
                logger.warning(f"Timeout reached ({timeout}s) for job {job_id} at poll {poll_count}")
                return {
                    "success": False,
                    "status": "timeout",
                    "job_id": job_id,
                    "elapsed_time_seconds": elapsed,
                    "polls_completed": poll_count,
                    "last_known_status": last_status,
                    "message": f"Job did not complete within {timeout} seconds",
                    "suggestion": f"Job may still be running. Use damien_job_get_status(job_id='{job_id}') to check current status.",
                    "progress_history": progress_updates if show_progress else None
                }

            poll_count += 1

            # Get current status
            status = async_processor.get_task_status(job_id)
            if not status:
                return {
                    "success": False,
                    "error_message": f"Job {job_id} not found",
                    "job_id": job_id,
                    "polls_completed": poll_count
                }

            last_status = status
            current_progress = status.get("progress", 0)
            current_message = status.get("message", "")
            job_status = status.get("status")

            # Build progress update
            if show_progress:
                progress_updates.append({
                    "poll_number": poll_count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "progress_percentage": current_progress,
                    "message": current_message,
                    "status": job_status,
                    "elapsed_seconds": elapsed
                })
                logger.info(f"[Poll {poll_count}/{max_polls}] {current_progress:.0f}% - {current_message}")

            # Check if job completed
            if job_status == TaskStatus.COMPLETED.value:
                logger.info(f"Job {job_id} completed successfully after {poll_count} polls and {elapsed:.1f}s")

                return {
                    "success": True,
                    "status": "completed",
                    "job_id": job_id,
                    "result": status.get("result"),
                    "completion_details": {
                        "polls_required": poll_count,
                        "elapsed_time_seconds": elapsed,
                        "start_time": status.get("start_time"),
                        "end_time": status.get("end_time")
                    },
                    "progress_history": progress_updates if show_progress else None
                }

            # Check if job failed
            if job_status == TaskStatus.FAILED.value:
                error_msg = status.get("error", "Unknown error")
                logger.error(f"Job {job_id} failed after {poll_count} polls: {error_msg}")

                return {
                    "success": False,
                    "status": "failed",
                    "job_id": job_id,
                    "error_message": error_msg,
                    "failure_details": {
                        "polls_before_failure": poll_count,
                        "elapsed_time_seconds": elapsed,
                        "last_progress": current_progress,
                        "last_message": current_message
                    },
                    "progress_history": progress_updates if show_progress else None
                }

            # Job still running - calculate next wait interval
            if exponential_backoff:
                # Progressive backoff: 5s → 10s → 15s → 30s
                interval_index = min(poll_count // 3, len(backoff_intervals) - 1)
                current_interval = backoff_intervals[interval_index]
            else:
                current_interval = poll_interval

            # Wait before next poll
            await asyncio.sleep(current_interval)

        # Max polls reached
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.warning(f"Max polls ({max_polls}) reached for job {job_id}")

        return {
            "success": False,
            "status": "max_polls_reached",
            "job_id": job_id,
            "elapsed_time_seconds": elapsed,
            "polls_completed": poll_count,
            "last_known_status": last_status,
            "message": f"Job did not complete within {max_polls} polling attempts",
            "suggestion": f"Job may still be running. Use damien_job_get_status(job_id='{job_id}') to check current status.",
            "progress_history": progress_updates if show_progress else None
        }

    except Exception as e:
        logger.error(f"Error waiting for job completion: {e}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Failed to wait for job completion: {str(e)}",
            "job_id": params.get("job_id")
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
    
    # AI Bulk Operations tool
    tool_def6 = ToolDefinition(
        name="damien_ai_bulk_operations",
        description="🎯 INTELLIGENT BULK OPERATIONS - Apply operations (trash, label, archive) to emails based on AI analysis patterns with confidence filtering",
        input_schema={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID from a completed damien_ai_analyze_emails_async analysis"
                },
                "operation": {
                    "type": "string",
                    "enum": ["trash", "label", "archive", "mark_read"],
                    "default": "trash",
                    "description": "Operation to perform on matched emails"
                },
                "pattern_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by pattern types (e.g., ['newsletter_subscriptions', 'job_alerts']). Empty array = all patterns"
                },
                "min_confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.85,
                    "description": "Minimum confidence threshold for patterns (default: 0.85)"
                },
                "max_emails": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 100,
                    "description": "Maximum number of emails to process (default: 100)"
                },
                "dry_run": {
                    "type": "boolean",
                    "default": True,
                    "description": "Dry run mode - show what would be done without executing (default: true)"
                },
                "additional_params": {
                    "type": "object",
                    "description": "Additional parameters for operations (e.g., label_names for labeling)",
                    "properties": {
                        "label_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Label names to apply (for label operation)"
                        }
                    }
                }
            },
            "required": ["job_id"]
        },
        handler="damien_ai_bulk_operations"
    )
    tool_registry.register_tool(tool_def6, damien_ai_bulk_operations_handler)

    # Wait for completion tool (Issue #34 Enhancement)
    tool_def7 = ToolDefinition(
        name="damien_job_wait_for_completion",
        description="🎯 AUTO-POLL JOB UNTIL COMPLETE - No more manual status checks! Automatically waits for job completion with real-time progress updates and smart timeout handling.",
        input_schema={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID to wait for (returned from async operations)"
                },
                "poll_interval": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 60,
                    "default": 10,
                    "description": "Base polling interval in seconds (default: 10). Ignored if exponential_backoff is true."
                },
                "timeout": {
                    "type": "integer",
                    "minimum": 30,
                    "maximum": 3600,
                    "default": 600,
                    "description": "Maximum wait time in seconds (default: 600 = 10 minutes)"
                },
                "max_polls": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 200,
                    "default": 60,
                    "description": "Maximum number of status checks (default: 60)"
                },
                "show_progress": {
                    "type": "boolean",
                    "default": True,
                    "description": "Display progress updates during polling (default: true)"
                },
                "exponential_backoff": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use progressive polling intervals: 5s → 10s → 15s → 30s (default: true)"
                }
            },
            "required": ["job_id"]
        },
        handler="damien_job_wait_for_completion"
    )
    tool_registry.register_tool(tool_def7, damien_job_wait_for_completion_handler)

    logger.info("✅ Successfully registered 7 async job processing tools (including auto-poll enhancement)")


# Export registration function
__all__ = ["register_async_tools"]
