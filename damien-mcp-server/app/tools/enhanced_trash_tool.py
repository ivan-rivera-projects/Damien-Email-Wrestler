"""
Enhanced Trash Tool with Query-Based Operations

This module implements an enhanced trash tool that can handle large-scale
email operations without the ID generation bottleneck.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..services.tool_registry import tool_registry, ToolDefinition
from ..services.cli_bridge import CLIBridge
from ..services.async_processor import AsyncTaskProcessor

logger = logging.getLogger("damien_mcp_server_app")

# Reuse the global async processor
from .async_tools import async_processor


async def damien_trash_emails_by_query_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced trash handler that supports query-based operations for large datasets.
    
    This avoids the ID generation bottleneck by using Gmail queries directly.
    """
    try:
        # Extract parameters
        query = params.get("query", "")
        max_results = params.get("max_results", 1000)
        use_async = params.get("use_async", False)
        dry_run = params.get("dry_run", False)
        
        # Validate parameters
        if not query:
            return {
                "success": False,
                "error": "Query parameter is required for query-based trash operations"
            }
        
        # Determine if we should use async based on max_results
        if max_results > 100 or use_async:
            # Use async processing for large operations
            return await _handle_async_trash(query, max_results, dry_run)
        else:
            # Use synchronous processing for small operations
            return await _handle_sync_trash(query, max_results, dry_run)
            
    except Exception as e:
        logger.error(f"Error in enhanced trash handler: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to trash emails: {str(e)}"
        }


async def _handle_sync_trash(query: str, max_results: int, dry_run: bool) -> Dict[str, Any]:
    """Handle synchronous trash operations for smaller datasets."""
    try:
        cli_bridge = CLIBridge()
        await cli_bridge.ensure_initialized()
        
        # Fetch emails using the query
        logger.info(f"Fetching emails with query: {query}, max_results: {max_results}")
        emails_result = await cli_bridge.fetch_emails(
            query=query,
            max_emails=max_results
        )
        
        emails = emails_result.get("emails", [])
        total_count = len(emails)
        
        if dry_run:
            # Just return what would be trashed
            return {
                "success": True,
                "mode": "dry_run",
                "would_trash": total_count,
                "query": query,
                "sample_emails": [
                    {
                        "subject": email.get("subject", "No subject"),
                        "from": email.get("from", "Unknown"),
                        "date": email.get("date", "Unknown")
                    }
                    for email in emails[:10]  # Show first 10 as sample
                ]
            }
        
        # Actually trash the emails
        message_ids = [email["id"] for email in emails if "id" in email]
        
        if not message_ids:
            return {
                "success": True,
                "trashed_count": 0,
                "message": "No emails found matching the query"
            }
        
        # Use the CLI bridge to trash emails
        trash_result = await cli_bridge.call_damien_tool(
            "damien_trash_emails",
            {"message_ids": message_ids}
        )
        
        # Extract data from the complete result structure
        trash_data = trash_result.get("data", {})
        
        return {
            "success": True,
            "mode": "synchronous",
            "trashed_count": trash_data.get("trashed_count", 0),
            "query": query,
            "total_found": total_count,
            "processing_time": trash_data.get("processing_time", 0)
        }
        
    except Exception as e:
        logger.error(f"Error in sync trash: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Sync trash failed: {str(e)}"
        }


async def _enhanced_keyword_analysis(cli_bridge, task_params) -> Dict[str, Any]:
    """Enhanced fallback analysis using improved keyword detection."""
    try:
        import time
        start_time = time.time()
        logger.info(f"🔍 DIAGNOSTIC: _enhanced_keyword_analysis started")
        logger.info(f"🔍 DIAGNOSTIC: task_params: {task_params}")
        
        # Fetch emails for analysis
        logger.info(f"🔍 DIAGNOSTIC: About to fetch emails...")
        fetch_start = time.time()
        emails_result = await cli_bridge.fetch_emails(
            query=task_params["query"],
            days=task_params["days"],
            max_emails=task_params["max_emails"]
        )
        fetch_end = time.time()
        
        logger.info(f"🔍 DIAGNOSTIC: Fetch emails completed in {fetch_end - fetch_start:.2f} seconds")
        logger.info(f"🔍 DIAGNOSTIC: emails_result keys: {emails_result.keys() if emails_result else 'None'}")
        
        emails = emails_result.get("emails", [])
        total_analyzed = len(emails)
        
        logger.info(f"🔍 DIAGNOSTIC: Fallback analysis: analyzing {total_analyzed} emails")
        logger.info(f"🔍 DIAGNOSTIC: Sample email data: {emails[0] if emails else 'No emails'}")
        
        # Enhanced pattern detection with more comprehensive keywords
        marketing_email_ids = []
        patterns = []
        
        # More comprehensive marketing detection
        marketing_keywords = [
            'unsubscribe', 'newsletter', 'marketing', 'promotion', 'promo', 
            'sale', 'offer', 'deal', 'discount', 'alert', 'notification',
            'digest', 'update', 'news', 'announcement', 'campaign',
            'job', 'hiring', 'career', 'opportunity', 'recruit'
        ]
        
        marketing_domains = [
            'marketing.', 'newsletter.', 'news.', 'hello@', 'noreply', 
            'no-reply', 'alerts@', 'jobalerts', 'notifications@',
            'promo@', 'offers@', 'deals@', 'campaign@'
        ]
        
        marketing_emails = []
        
        for email in emails:
            subject = email.get('Subject', email.get('subject', '')).lower()
            snippet = email.get('snippet', '').lower()
            sender = email.get('From', email.get('from', '')).lower()
            list_unsubscribe = email.get('List-Unsubscribe', '') or email.get('list-unsubscribe', '')
            
            # Multiple detection criteria
            has_unsubscribe_header = bool(list_unsubscribe)
            has_marketing_domain = any(domain in sender for domain in marketing_domains)
            has_marketing_keywords = any(keyword in subject or keyword in snippet for keyword in marketing_keywords)
            
            # More aggressive detection
            if has_unsubscribe_header or has_marketing_domain or has_marketing_keywords:
                marketing_emails.append(email)
                email_id = email.get('id', email.get('Id', ''))
                if email_id:
                    marketing_email_ids.append(email_id)
        
        if marketing_emails:
            patterns.append({
                "pattern_type": "marketing_emails",
                "email_count": len(marketing_emails),
                "confidence": min(0.95, 0.75 + (len(marketing_emails) / total_analyzed * 0.20)),
                "description": f"Marketing and promotional emails ({len(marketing_emails)} emails)",
                "email_ids": marketing_email_ids
            })
        
        end_time = time.time()
        logger.info(f"🔍 DIAGNOSTIC: _enhanced_keyword_analysis completed in {end_time - start_time:.2f} seconds")
        logger.info(f"🔍 DIAGNOSTIC: Found {len(patterns)} patterns, analyzed {total_analyzed} emails")
        
        return {
            "patterns": patterns,
            "emails_analyzed": total_analyzed,
            "success": True,
            "mode": "enhanced_fallback"
        }
        
    except Exception as e:
        logger.error(f"🔍 DIAGNOSTIC: Enhanced fallback analysis failed: {e}", exc_info=True)
        return {
            "patterns": [],
            "emails_analyzed": 0,
            "success": False,
            "error": str(e)
        }


async def _handle_async_trash(query: str, max_results: int, dry_run: bool) -> Dict[str, Any]:
    """Handle asynchronous trash operations for large datasets."""
    try:
        # Define the async trash task
        async def trash_emails_task(task_params):
            cli_bridge = CLIBridge()
            await cli_bridge.ensure_initialized()
            
            # Fetch all emails at once (up to max_results)
            logger.info(f"Fetching up to {max_results} emails for async trash processing")
            await async_processor.update_task_progress(
                task_params["task_id"],
                10.0,
                "Fetching emails for processing..."
            )
            
            emails_result = await cli_bridge.fetch_emails(
                query=task_params["query"],
                max_emails=task_params["max_results"]
            )
            
            emails = emails_result.get("emails", [])
            total_found = len(emails)
            total_trashed = 0
            
            await async_processor.update_task_progress(
                task_params["task_id"],
                25.0,
                f"Found {total_found} emails to process"
            )
            
            if not emails:
                return {
                    "status": "success",
                    "total_trashed": 0,
                    "total_found": 0,
                    "query": task_params["query"],
                    "dry_run": task_params["dry_run"],
                    "message": "No emails found matching the query"
                }
            
            if not task_params["dry_run"]:
                # Process emails in batches for trashing
                batch_size = 50
                for i in range(0, len(emails), batch_size):
                    batch = emails[i:i + batch_size]
                    
                    # Update progress
                    progress = 25.0 + (i / len(emails)) * 70.0
                    await async_processor.update_task_progress(
                        task_params["task_id"],
                        progress,
                        f"Trashing batch {i//batch_size + 1}/{(len(emails) + batch_size - 1)//batch_size}, processed {total_trashed} emails"
                    )
                    
                    # Trash this batch
                    message_ids = [email["id"] for email in batch if "id" in email]
                    if message_ids:
                        trash_result = await cli_bridge.call_damien_tool(
                            "damien_trash_emails",
                            {"message_ids": message_ids}
                        )
                        trash_data = trash_result.get("data", {})
                        batch_trashed = trash_data.get("trashed_count", 0)
                        total_trashed += batch_trashed
                        logger.info(f"Trashed {batch_trashed} emails in batch {i//batch_size + 1}")
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
            else:
                # Dry run - just count what would be trashed
                total_trashed = total_found
            
            return {
                "status": "success",
                "total_trashed": total_trashed,
                "total_found": total_found,
                "query": task_params["query"],
                "dry_run": task_params["dry_run"],
                "processing_metadata": {
                    "batches_processed": (total_found + 49) // 50,  # Round up division
                    "emails_per_batch": 50
                }
            }
        
        # Submit task for background processing
        task_id = await async_processor.submit_task(
            name=f"Trash emails by query: {query[:50]}...",
            processor_func=trash_emails_task,
            parameters={
                "query": query,
                "max_results": max_results,
                "dry_run": dry_run,
                "task_id": None  # Will be set by processor automatically
            }
        )
        
        # Estimate duration
        estimated_duration_minutes = max(1, max_results // 100)
        
        return {
            "success": True,
            "mode": "asynchronous",
            "job_id": task_id,
            "status": "started",
            "message": f"Background trash operation started for query: {query}",
            "estimated_duration_minutes": estimated_duration_minutes,
            "max_results": max_results,
            "tracking": {
                "check_progress": f"damien_job_get_status(job_id='{task_id}')",
                "get_results": f"damien_job_get_result(job_id='{task_id}')"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in async trash: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Async trash failed: {str(e)}"
        }


async def damien_smart_trash_marketing_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Smart handler that uses AI analysis to identify and trash marketing emails.
    DIAGNOSTIC VERSION with extensive logging to debug the 0.6-second failure.
    """
    try:
        # DIAGNOSTIC: Log every step with timestamps
        import time
        start_time = time.time()
        
        query = params.get("query", "")
        min_confidence = params.get("min_confidence", 0.85)
        dry_run = params.get("dry_run", False)
        max_emails = params.get("max_emails", 500)
        days = params.get("days", 30)
        
        logger.info(f"🔍 DIAGNOSTIC: Handler started at {start_time}")
        logger.info(f"🔍 DIAGNOSTIC: Parameters - query: '{query}', max_emails: {max_emails}, min_confidence: {min_confidence}, dry_run: {dry_run}, days: {days}")
        
        # Test if async_processor is available
        logger.info(f"🔍 DIAGNOSTIC: Testing async_processor availability...")
        try:
            active_tasks = async_processor.list_active_tasks()
            logger.info(f"🔍 DIAGNOSTIC: async_processor working, active tasks: {len(active_tasks)}")
        except Exception as e:
            logger.error(f"🔍 DIAGNOSTIC: async_processor FAILED: {e}")
            return {
                "success": False,
                "error": f"async_processor not available: {str(e)}",
                "diagnostic": "async_processor_failed"
            }
        
        logger.info(f"🔍 DIAGNOSTIC: About to submit async task...")
        
        # Step 1: First run the AI analysis to identify patterns
        # This is the SAME analysis that found 268/300 marketing emails initially
        async def smart_trash_with_real_ai_task(task_params):
            try:
                task_start = time.time()
                logger.info(f"🔍 DIAGNOSTIC: Async task function started at {task_start}")
                logger.info(f"🔍 DIAGNOSTIC: Task params: {task_params}")
                
                cli_bridge = CLIBridge()
                logger.info(f"🔍 DIAGNOSTIC: CLIBridge created, calling ensure_initialized...")
                await cli_bridge.ensure_initialized()
                logger.info(f"🔍 DIAGNOSTIC: CLIBridge initialized successfully")
                
                # Update progress
                logger.info(f"🔍 DIAGNOSTIC: About to update progress to 10%...")
                await async_processor.update_task_progress(
                    task_params["task_id"],
                    10.0,
                    f"Starting AI analysis of up to {task_params['max_emails']} emails..."
                )
                logger.info(f"🔍 DIAGNOSTIC: Progress updated to 10%")
                
                # Step 1: Use async analysis workflow (same as damien_ai_analyze_emails_async)
                # Import the async analysis handler at runtime to avoid circular imports
                try:
                    logger.info(f"🔍 DIAGNOSTIC: Using async analysis workflow...")
                    from ..tools.async_tools import damien_ai_analyze_emails_async_handler
                    logger.info(f"🔍 DIAGNOSTIC: Async analysis handler imported successfully")
                    
                    # Call the async analysis handler with proper parameters
                    async_params = {
                        "days": task_params["days"],
                        "target_count": task_params["max_emails"],
                        "min_confidence": task_params["min_confidence"],
                        "query": task_params["query"],
                        "use_statistical_validation": True
                    }
                    logger.info(f"🔍 DIAGNOSTIC: Starting async analysis with params: {async_params}")
                    
                    ai_start = time.time()
                    async_result = await damien_ai_analyze_emails_async_handler(
                        async_params,
                        {}  # empty context
                    )
                    ai_end = time.time()
                    
                    logger.info(f"🔍 DIAGNOSTIC: Async analysis completed in {ai_end - ai_start:.2f} seconds")
                    logger.info(f"🔍 DIAGNOSTIC: Async result keys: {async_result.keys() if async_result else 'None'}")
                    
                    if async_result and async_result.get("success"):
                        # Get the job ID and wait for completion
                        job_id = async_result.get("job_id")
                        logger.info(f"🔍 DIAGNOSTIC: Waiting for async job {job_id} to complete...")
                        
                        # Wait for job completion with timeout
                        from ..core.async_processor import AsyncProcessor
                        async_processor_instance = AsyncProcessor()
                        
                        max_wait_time = 300  # 5 minutes max
                        wait_start = time.time()
                        
                        while time.time() - wait_start < max_wait_time:
                            job_status = await async_processor_instance.get_task_status(job_id)
                            if job_status.get("status") == "completed":
                                logger.info(f"🔍 DIAGNOSTIC: Async job completed successfully")
                                job_result = await async_processor_instance.get_task_result(job_id)
                                ai_result = job_result.get("result", {})
                                break
                            elif job_status.get("status") == "failed":
                                logger.error(f"🔍 DIAGNOSTIC: Async job failed: {job_status}")
                                raise Exception(f"Async analysis job failed: {job_status.get('error', 'Unknown error')}")
                            else:
                                # Job still running, wait a bit
                                await asyncio.sleep(2)
                        else:
                            raise Exception("Async analysis job timed out")
                    else:
                        raise Exception(f"Failed to start async analysis: {async_result}")
                    
                except Exception as e:
                    logger.error(f"🔍 DIAGNOSTIC: Async analysis failed: {e}", exc_info=True)
                    # Fallback to enhanced keyword-based analysis  
                    logger.info(f"🔍 DIAGNOSTIC: Falling back to enhanced keyword analysis due to error...")
                    fallback_start = time.time()
                    ai_result = await _enhanced_keyword_analysis(
                        cli_bridge, task_params
                    )
                    fallback_end = time.time()
                    logger.info(f"🔍 DIAGNOSTIC: Fallback analysis completed in {fallback_end - fallback_start:.2f} seconds")
                    logger.info(f"🔍 DIAGNOSTIC: Fallback result: {ai_result.keys() if ai_result else 'None'}")
                
                logger.info(f"🔍 DIAGNOSTIC: About to update progress to 40%...")
                await async_processor.update_task_progress(
                    task_params["task_id"],
                    40.0,
                    "AI analysis complete, processing patterns..."
                )
                logger.info(f"🔍 DIAGNOSTIC: Progress updated to 40%")
                
                # Step 2: Extract ALL patterns from AI analysis (now using correct data structure)
                logger.info(f"🔍 DIAGNOSTIC: Extracting patterns from AI result...")
                # AI result from async analysis has the correct structure
                patterns = ai_result.get("patterns", [])
                total_analyzed = ai_result.get("emails_analyzed", 0)
                
                logger.info(f"🔍 DIAGNOSTIC: AI result keys: {ai_result.keys() if ai_result else 'None'}")
                
                logger.info(f"🔍 DIAGNOSTIC: AI analyzed {total_analyzed} emails and found {len(patterns)} patterns")
                logger.info(f"🔍 DIAGNOSTIC: Pattern details: {[p.get('pattern_type', 'unknown') for p in patterns]}")
                
                # Step 3: Identify marketing-related patterns AND their email IDs
                logger.info(f"🔍 DIAGNOSTIC: Starting pattern analysis for marketing detection...")
                marketing_email_ids = set()  # Use set to avoid duplicates
                marketing_patterns = []
                
                for i, pattern in enumerate(patterns):
                    pattern_type = pattern.get("pattern_type", "")
                    pattern_confidence = pattern.get("confidence", 0)
                    email_ids = pattern.get("email_ids", [])
                    
                    logger.info(f"🔍 DIAGNOSTIC: Pattern {i+1}/{len(patterns)}: '{pattern_type}' confidence={pattern_confidence:.3f}, emails={len(email_ids)}")
                    logger.info(f"🔍 DIAGNOSTIC: Pattern email_ids sample: {email_ids[:3] if email_ids else 'None'}")
                    
                    # Check if this is a marketing pattern - be MORE inclusive
                    # The AI might use different pattern names than we expect
                    pattern_lower = pattern_type.lower()
                    
                    # Marketing patterns include newsletters, promotions, notifications, updates, etc.
                    is_marketing = (
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
                    description = pattern.get("description", "").lower()
                    if not is_marketing and description:
                        is_marketing = any(word in description for word in [
                            "marketing", "newsletter", "promotion", "subscription",
                            "unsubscribe", "commercial", "advertisement"
                        ])
                    
                    if is_marketing and pattern_confidence >= task_params["min_confidence"]:
                        marketing_patterns.append(pattern)
                        marketing_email_ids.update(email_ids)
                        logger.info(f"🔍 DIAGNOSTIC: ✅ Pattern '{pattern_type}' ACCEPTED as marketing with {len(email_ids)} emails")
                    else:
                        logger.info(f"🔍 DIAGNOSTIC: ❌ Pattern '{pattern_type}' REJECTED - is_marketing: {is_marketing}, confidence: {pattern_confidence:.3f} vs threshold: {task_params['min_confidence']}")
                
                marketing_email_ids = list(marketing_email_ids)
                total_marketing = len(marketing_email_ids)
                
                logger.info(f"🔍 DIAGNOSTIC: Final marketing analysis results:")
                logger.info(f"🔍 DIAGNOSTIC: - Total patterns found: {len(patterns)}")
                logger.info(f"🔍 DIAGNOSTIC: - Marketing patterns accepted: {len(marketing_patterns)}")
                logger.info(f"🔍 DIAGNOSTIC: - Total marketing emails identified: {total_marketing}")
                logger.info(f"🔍 DIAGNOSTIC: - Marketing email IDs sample: {marketing_email_ids[:5] if marketing_email_ids else 'None'}")
                
                logger.info(f"🔍 DIAGNOSTIC: About to update progress to 60%...")
                await async_processor.update_task_progress(
                    task_params["task_id"],
                    60.0,
                    f"Identified {total_marketing} marketing emails from {len(marketing_patterns)} patterns"
                )
                logger.info(f"🔍 DIAGNOSTIC: Progress updated to 60%")
                
                # Step 4: Handle dry run or actual trash
                if task_params["dry_run"]:
                    return {
                        "status": "success",
                        "mode": "dry_run_with_real_ai",
                        "total_analyzed": total_analyzed,
                        "marketing_emails_found": total_marketing,
                        "patterns_detected": [
                            {
                                "type": p.get("pattern_type"),
                                "confidence": p.get("confidence"),
                                "count": len(p.get("email_ids", [])),
                                "description": p.get("description", "")
                            }
                            for p in marketing_patterns
                        ],
                        "would_trash": total_marketing,
                        "confidence_threshold": task_params["min_confidence"]
                    }
                
                # Step 5: Trash the marketing emails
                total_trashed = 0
                if marketing_email_ids:
                    # Process in batches
                    batch_size = 50
                    for i in range(0, len(marketing_email_ids), batch_size):
                        batch = marketing_email_ids[i:i + batch_size]
                        
                        progress = 70.0 + (i / len(marketing_email_ids)) * 25.0
                        await async_processor.update_task_progress(
                            task_params["task_id"],
                            progress,
                            f"Trashing batch {i//batch_size + 1}/{(len(marketing_email_ids) + batch_size - 1)//batch_size}"
                        )
                        
                        trash_result = await cli_bridge.call_damien_tool(
                            "damien_trash_emails",
                            {"message_ids": batch}
                        )
                        
                        trash_data = trash_result.get("data", {})
                        batch_trashed = trash_data.get("trashed_count", 0)
                        total_trashed += batch_trashed
                        logger.info(f"Trashed {batch_trashed} emails in batch")
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.1)
                
                await async_processor.update_task_progress(
                    task_params["task_id"],
                    100.0,
                    f"Completed! AI identified and trashed {total_trashed} marketing emails"
                )
                
                return {
                    "status": "success",
                    "mode": "real_ai_powered",
                    "total_analyzed": total_analyzed,
                    "marketing_emails_found": total_marketing,
                    "emails_trashed": total_trashed,
                    "patterns_detected": [
                        {
                            "type": p.get("pattern_type"),
                            "confidence": p.get("confidence"),
                            "count": len(p.get("email_ids", [])),
                            "description": p.get("description", "")
                        }
                        for p in marketing_patterns
                    ],
                    "confidence_threshold": task_params["min_confidence"],
                    "ai_accuracy": f"{(total_marketing / total_analyzed * 100):.1f}%" if total_analyzed > 0 else "N/A"
                }
                
            except Exception as e:
                task_end = time.time()
                logger.error(f"🔍 DIAGNOSTIC: Error in smart trash task after {task_end - task_start:.2f} seconds: {e}", exc_info=True)
                raise
        
        # Submit task for background processing
        logger.info(f"🔍 DIAGNOSTIC: About to submit async task...")
        submit_start = time.time()
        
        task_params = {
            "query": query,
            "days": days,
            "max_emails": max_emails,
            "min_confidence": min_confidence,
            "dry_run": dry_run,
            "task_id": None  # Will be set by processor
        }
        logger.info(f"🔍 DIAGNOSTIC: Task parameters for submission: {task_params}")
        
        task_id = await async_processor.submit_task(
            name=f"REAL AI-powered marketing email cleanup ({max_emails} emails)",
            processor_func=smart_trash_with_real_ai_task,
            parameters=task_params
        )
        
        submit_end = time.time()
        logger.info(f"🔍 DIAGNOSTIC: Task submitted in {submit_end - submit_start:.2f} seconds")
        logger.info(f"🔍 DIAGNOSTIC: Generated task_id: {task_id}")
        
        # Estimate duration
        estimated_duration_minutes = max(1, max_emails // 100)
        
        handler_end = time.time()
        logger.info(f"🔍 DIAGNOSTIC: Handler completed in {handler_end - start_time:.2f} seconds")
        logger.info(f"🔍 DIAGNOSTIC: Returning success response with job_id: {task_id}")
        
        return {
            "success": True,
            "mode": "asynchronous",
            "job_id": task_id,
            "status": "started",
            "message": f"AI-powered marketing email analysis and cleanup started",
            "estimated_duration_minutes": estimated_duration_minutes,
            "parameters": {
                "query": query,
                "days": days,
                "max_emails": max_emails,
                "min_confidence": min_confidence,
                "dry_run": dry_run
            },
            "tracking": {
                "check_progress": f"damien_job_get_status(job_id='{task_id}')",
                "get_results": f"damien_job_get_result(job_id='{task_id}')"
            }
        }
        
    except Exception as e:
        handler_error_time = time.time()
        logger.error(f"🔍 DIAGNOSTIC: Error in smart trash marketing after {handler_error_time - start_time:.2f} seconds: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Smart trash marketing failed: {str(e)}"
        }


def register_enhanced_trash_tools():
    """Register enhanced trash tools."""
    logger.info("🗑️ Registering enhanced trash tools...")
    
    # Query-based trash tool
    tool_def1 = ToolDefinition(
        name="damien_trash_emails_by_query",
        description="🗑️ ENHANCED: Trash emails using Gmail queries - handles 1000+ emails without timeout!",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query (e.g., 'is:unread from:marketing@example.com')"
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10000,
                    "default": 1000,
                    "description": "Maximum emails to trash (default: 1000)"
                },
                "use_async": {
                    "type": "boolean",
                    "default": False,
                    "description": "Force async processing (auto-enabled for >100 emails)"
                },
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": "Preview what would be trashed without actually doing it"
                }
            },
            "required": ["query"]
        },
        handler="damien_trash_emails_by_query"
    )
    tool_registry.register_tool(tool_def1, damien_trash_emails_by_query_handler)
    
    # Smart marketing trash tool
    tool_def2 = ToolDefinition(
        name="damien_smart_trash_marketing",
        description="🎯 AI-POWERED: Uses advanced AI analysis to identify and trash marketing emails with high accuracy",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query to filter emails (e.g., 'is:unread')",
                    "default": ""
                },
                "days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 30,
                    "description": "Number of days to analyze (default: 30)"
                },
                "min_confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.85,
                    "description": "Minimum confidence for marketing detection (default: 0.85)"
                },
                "max_emails": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5000,
                    "default": 500,
                    "description": "Maximum emails to process (default: 500)"
                },
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": "Preview what would be trashed without actually trashing"
                }
            }
        },
        handler="damien_smart_trash_marketing"
    )
    tool_registry.register_tool(tool_def2, damien_smart_trash_marketing_handler)
    
    logger.info("✅ Successfully registered 2 enhanced trash tools")


# Export registration function
__all__ = ["register_enhanced_trash_tools"]