"""
Smart Cleanup Tools for One-Click Email Workflow

This module implements the smart cleanup workflow that reduces email cleanup
from 4 manual steps to 2 steps with user-friendly previews and confirmations.
"""

import asyncio
import logging
import uuid
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from ..services.tool_registry import tool_registry, ToolDefinition
from ..services.cli_bridge import CLIBridge
from ..services.async_processor import AsyncTaskProcessor

logger = logging.getLogger("damien_mcp_server_app")

# Reuse the global async processor
from .async_tools import async_processor

# Global action token storage (in production, use Redis or database)
action_tokens: Dict[str, Dict[str, Any]] = {}


def _parse_timeframe(timeframe: str) -> Dict[str, Any]:
    """Parse natural language timeframe into Gmail query parameters."""
    timeframe_lower = timeframe.lower()
    
    # Calculate dates
    now = datetime.now()
    
    if "today" in timeframe_lower:
        query_date = now.strftime("%Y/%m/%d")
        return {"query": f"after:{query_date}", "description": "today"}
    elif "yesterday" in timeframe_lower:
        yesterday = now - timedelta(days=1)
        query_date = yesterday.strftime("%Y/%m/%d")
        return {"query": f"after:{query_date} before:{now.strftime('%Y/%m/%d')}", "description": "yesterday"}
    elif "this week" in timeframe_lower or "week" in timeframe_lower:
        week_ago = now - timedelta(days=7)
        query_date = week_ago.strftime("%Y/%m/%d")
        return {"query": f"after:{query_date}", "description": "this week"}
    elif "last week" in timeframe_lower:
        two_weeks_ago = now - timedelta(days=14)
        week_ago = now - timedelta(days=7)
        start_date = two_weeks_ago.strftime("%Y/%m/%d")
        end_date = week_ago.strftime("%Y/%m/%d")
        return {"query": f"after:{start_date} before:{end_date}", "description": "last week"}
    elif "this month" in timeframe_lower or "month" in timeframe_lower:
        month_ago = now - timedelta(days=30)
        query_date = month_ago.strftime("%Y/%m/%d")
        return {"query": f"after:{query_date}", "description": "this month"}
    elif "last month" in timeframe_lower:
        two_months_ago = now - timedelta(days=60)
        month_ago = now - timedelta(days=30)
        start_date = two_months_ago.strftime("%Y/%m/%d")
        end_date = month_ago.strftime("%Y/%m/%d")
        return {"query": f"after:{start_date} before:{end_date}", "description": "last month"}
    elif "last 30 days" in timeframe_lower or "30 days" in timeframe_lower:
        thirty_days_ago = now - timedelta(days=30)
        query_date = thirty_days_ago.strftime("%Y/%m/%d")
        return {"query": f"after:{query_date}", "description": "the last 30 days"}
    elif "last 7 days" in timeframe_lower or "7 days" in timeframe_lower:
        week_ago = now - timedelta(days=7)
        query_date = week_ago.strftime("%Y/%m/%d")
        return {"query": f"after:{query_date}", "description": "the last 7 days"}
    else:
        # Default to last 7 days
        week_ago = now - timedelta(days=7)
        query_date = week_ago.strftime("%Y/%m/%d")
        return {"query": f"after:{query_date}", "description": "the last 7 days"}


def _calculate_time_savings(email_count: int) -> str:
    """Calculate estimated time savings from cleanup."""
    # Estimate: 30 seconds per email for manual processing
    total_seconds = email_count * 30
    
    if total_seconds < 60:
        return f"{total_seconds} seconds"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} minutes"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if minutes > 0:
            return f"{hours} hours {minutes} minutes"
        else:
            return f"{hours} hours"


async def damien_smart_cleanup_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Smart cleanup preview - analyzes emails and shows user-friendly preview.
    
    This is step 1 of the 2-step workflow that replaces the 4-step manual process.
    """
    try:
        # Extract parameters
        timeframe = params.get("timeframe", "this week")
        confidence_threshold = params.get("confidence_threshold", 0.90)
        pattern_types = params.get("pattern_types", ["newsletter_subscriptions", "marketing", "promotional"])
        max_emails = params.get("max_emails", 500)
        
        logger.info(f"Starting smart cleanup preview for timeframe: {timeframe}")
        
        # Parse timeframe into Gmail query
        timeframe_config = _parse_timeframe(timeframe)
        base_query = timeframe_config["query"]
        description = timeframe_config["description"]
        
        # Use only the timeframe query - let AI analyze and categorize all emails
        full_query = base_query
        
        # Submit analysis task
        cli_bridge = CLIBridge()
        await cli_bridge.ensure_initialized()
        
        # Run AI analysis using the same async workflow as smart trash marketing
        # This avoids the parameter conflicts that cause the "unsupported type for timedelta" error
        from .async_tools import damien_ai_analyze_emails_async_handler
        
        # Extract days from the timeframe for the async analysis
        # For "last 30 days", we'll use days=30 (without the query parameter)
        if "30 days" in timeframe.lower():
            days_param = 30
        elif "7 days" in timeframe.lower() or "week" in timeframe.lower():
            days_param = 7
        elif "today" in timeframe.lower():
            days_param = 1
        else:
            days_param = 30  # Default
        
        # Use async analysis with proper parameters (same as working smart trash marketing)
        async_params = {
            "days": days_param,
            "target_count": max_emails,
            "min_confidence": confidence_threshold,
            "use_statistical_validation": True
        }
        
        analysis_result = await damien_ai_analyze_emails_async_handler(
            async_params,
            context
        )
        
        if not analysis_result.get("success"):
            return {
                "success": False,
                "error": f"Analysis failed: {analysis_result.get('error', 'Unknown error')}"
            }
        
        # For async analysis, we need to get the job and wait for results
        job_id = analysis_result.get("job_id")
        if not job_id:
            return {
                "success": False,
                "error": "Async analysis did not return a job ID"
            }
        
        # Wait for the job to complete and get results
        # Use the same global async processor that the async tools use
        from .async_tools import async_processor
        
        # Wait for job completion (with timeout)
        max_wait_time = 120  # 2 minutes max
        wait_start = time.time()
        
        while time.time() - wait_start < max_wait_time:
            job_status = async_processor.get_task_status(job_id)
            if job_status and job_status.get("status") == "completed":
                job_result = async_processor.get_task_result(job_id)
                ai_result = job_result.get("result", {})
                break
            elif job_status and job_status.get("status") == "failed":
                return {
                    "success": False,
                    "error": f"Analysis job failed: {job_status.get('error', 'Unknown error')}"
                }
            else:
                # Job still running, wait a bit
                await asyncio.sleep(2)
        else:
            return {
                "success": False,
                "error": "Analysis job timed out"
            }
        
        # Extract patterns from the completed job result
        detailed_patterns = ai_result.get("patterns", [])
        
        # Filter patterns by confidence and type
        actionable_patterns = []
        total_actionable_emails = 0
        
        for pattern in detailed_patterns:
            pattern_type = pattern.get("pattern_type", "")
            pattern_confidence = pattern.get("confidence", 0)
            email_ids = pattern.get("email_ids", [])
            
            # Check confidence threshold
            if pattern_confidence < confidence_threshold:
                continue
            if not email_ids:
                continue
            
            # Check if this pattern matches our criteria using flexible matching
            # (similar to the successful smart trash marketing tool)
            pattern_lower = pattern_type.lower()
            description = pattern.get("description", "").lower()
            
            # Check if this is a marketing/promotional pattern - be MORE inclusive
            is_target_pattern = (
                "newsletter" in pattern_lower or
                "marketing" in pattern_lower or
                "promotion" in pattern_lower or
                "job" in pattern_lower or
                "alert" in pattern_lower or
                "notification" in pattern_lower or
                "subscription" in pattern_lower or
                "digest" in pattern_lower or
                "update" in pattern_lower or
                "announcement" in pattern_lower or
                "commercial" in pattern_lower or
                "advertisement" in pattern_lower or
                "deal" in pattern_lower or
                "offer" in pattern_lower or
                "sale" in pattern_lower
            )
            
            # Also check pattern description if available
            if not is_target_pattern and description:
                is_target_pattern = any(word in description for word in [
                    "marketing", "newsletter", "promotion", "subscription",
                    "unsubscribe", "commercial", "advertisement"
                ])
            
            # Only include patterns that match our target types
            if is_target_pattern:
                actionable_patterns.append(pattern)
                total_actionable_emails += len(email_ids)
        
        # Calculate average confidence
        if actionable_patterns:
            avg_confidence = sum(p.get("confidence", 0) for p in actionable_patterns) / len(actionable_patterns)
        else:
            avg_confidence = 0
        
        # Generate action token for execution
        action_token = f"cleanup_{uuid.uuid4().hex[:8]}"
        
        # Store cleanup plan with action token
        action_tokens[action_token] = {
            "patterns": actionable_patterns,
            "analysis_result": analysis_result,
            "timeframe": timeframe,
            "description": description,
            "confidence_threshold": confidence_threshold,
            "pattern_types": pattern_types,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()  # 1 hour expiry
        }
        
        # Calculate time savings
        time_savings = _calculate_time_savings(total_actionable_emails)
        
        # Generate preview message
        if total_actionable_emails > 0:
            preview_message = f"Found {total_actionable_emails} emails from {description} ready for cleanup ({avg_confidence:.1f}% confidence)"
            status_emoji = "🎯"
        else:
            preview_message = f"No emails found matching cleanup criteria from {description}"
            status_emoji = "✅"
        
        logger.info(f"Smart cleanup preview complete: {total_actionable_emails} emails found")
        
        return {
            "success": True,
            "preview_mode": True,
            "emails_found": total_actionable_emails,
            "confidence": round(avg_confidence, 1),
            "estimated_time_savings": time_savings,
            "preview_message": f"{status_emoji} {preview_message}",
            "action_token": action_token,
            "ready_to_execute": total_actionable_emails > 0,
            "timeframe_description": description,
            "patterns_summary": [
                {
                    "type": p.get("pattern_type"),
                    "count": len(p.get("email_ids", [])),
                    "confidence": p.get("confidence")
                }
                for p in actionable_patterns
            ],
            "execution_instructions": {
                "next_step": f"Use damien_execute_cleanup with action_token '{action_token}' to proceed",
                "expires_in": "1 hour"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in smart cleanup preview: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to generate cleanup preview: {str(e)}"
        }


async def damien_execute_cleanup_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute cleanup using action token from preview.
    
    This is step 2 of the 2-step workflow that completes the email cleanup.
    """
    try:
        # Extract action token
        action_token = params.get("action_token")
        if not action_token:
            return {
                "success": False,
                "error": "action_token parameter is required"
            }
        
        # Retrieve cleanup plan
        cleanup_plan = action_tokens.get(action_token)
        if not cleanup_plan:
            return {
                "success": False,
                "error": "Invalid or expired action token"
            }
        
        # Check expiry
        expires_at = datetime.fromisoformat(cleanup_plan["expires_at"].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_at:
            # Clean up expired token
            del action_tokens[action_token]
            return {
                "success": False,
                "error": "Action token has expired. Please run smart cleanup preview again."
            }
        
        logger.info(f"Executing cleanup with action token: {action_token}")
        
        # Extract patterns and prepare for bulk operations
        patterns = cleanup_plan["patterns"]
        
        if not patterns:
            return {
                "success": True,
                "emails_processed": 0,
                "message": "No emails found to cleanup",
                "timeframe": cleanup_plan["description"]
            }
        
        # Collect all email IDs from patterns
        all_email_ids = []
        pattern_summary = []
        
        for pattern in patterns:
            email_ids = pattern.get("email_ids", [])
            if email_ids:
                all_email_ids.extend(email_ids)
                pattern_summary.append({
                    "pattern_type": pattern.get("pattern_type"),
                    "emails_processed": len(email_ids),
                    "confidence": pattern.get("confidence"),
                    "description": pattern.get("description")
                })
        
        # Remove duplicates while preserving order
        unique_email_ids = list(dict.fromkeys(all_email_ids))
        
        # Execute bulk trash operation
        cli_bridge = CLIBridge()
        await cli_bridge.ensure_initialized()
        
        # Use existing bulk trash functionality
        trash_result = await cli_bridge.execute_tool_command(
            "damien_trash_emails",
            {"message_ids": unique_email_ids}
        )
        
        # Calculate time savings
        time_savings = _calculate_time_savings(len(unique_email_ids))
        
        # Clean up the action token
        del action_tokens[action_token]
        
        logger.info(f"Smart cleanup execution complete: {len(unique_email_ids)} emails processed")
        
        return {
            "success": True,
            "emails_processed": len(unique_email_ids),
            "patterns_processed": len(patterns),
            "time_saved": time_savings,
            "timeframe": cleanup_plan["description"],
            "completion_message": f"✅ Successfully cleaned up {len(unique_email_ids)} emails from {cleanup_plan['description']}",
            "pattern_summary": pattern_summary,
            "trash_operation_result": trash_result
        }
        
    except Exception as e:
        logger.error(f"Error executing cleanup: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to execute cleanup: {str(e)}"
        }


def register_smart_cleanup_tools():
    """Register smart cleanup tools."""
    logger.info("🧹 Registering smart cleanup tools...")
    
    # Smart cleanup preview tool
    tool_def1 = ToolDefinition(
        name="damien_smart_cleanup",
        description="🧹 SMART CLEANUP: One-click email cleanup workflow - Step 1: Analyze and preview emails for cleanup with user-friendly summary and action token",
        input_schema={
            "type": "object",
            "properties": {
                "timeframe": {
                    "type": "string",
                    "default": "this week",
                    "description": "Natural language timeframe (e.g., 'this week', 'last month', 'today', 'last 7 days')"
                },
                "confidence_threshold": {
                    "type": "number",
                    "minimum": 0.5,
                    "maximum": 1.0,
                    "default": 0.90,
                    "description": "Minimum confidence threshold for email classification (default: 0.90)"
                },
                "pattern_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["newsletter_subscriptions", "marketing", "promotional"],
                    "description": "Types of email patterns to target for cleanup"
                },
                "max_emails": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 1000,
                    "default": 500,
                    "description": "Maximum number of emails to analyze (default: 500)"
                }
            }
        },
        handler="damien_smart_cleanup"
    )
    tool_registry.register_tool(tool_def1, damien_smart_cleanup_handler)
    
    # Smart cleanup execution tool
    tool_def2 = ToolDefinition(
        name="damien_execute_cleanup",
        description="✅ EXECUTE CLEANUP: One-click email cleanup workflow - Step 2: Execute the cleanup plan using action token from smart cleanup preview",
        input_schema={
            "type": "object",
            "properties": {
                "action_token": {
                    "type": "string",
                    "description": "Action token from damien_smart_cleanup preview (required)"
                }
            },
            "required": ["action_token"]
        },
        handler="damien_execute_cleanup"
    )
    tool_registry.register_tool(tool_def2, damien_execute_cleanup_handler)
    
    logger.info("✅ Successfully registered 2 smart cleanup tools")


# Export registration function
__all__ = ["register_smart_cleanup_tools"]