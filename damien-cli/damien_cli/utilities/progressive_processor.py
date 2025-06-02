"""
Progressive batch processing utilities for Gmail API operations.

This module provides functions to perform batch operations on emails with
real-time progress feedback, optimizing for both performance and user experience.
"""

import logging
import time
from typing import List, Dict, Any, Optional, AsyncGenerator, Callable

# Set up logger
logger = logging.getLogger(__name__)

async def progressive_batch_operation(
    fetch_function: Callable,
    process_function: Callable,
    query: str,
    estimated_count: Optional[int] = None,
    batch_sizing: Optional[Dict[str, Any]] = None,
    operation_name: str = "process"
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Process emails in progressive batches with real-time feedback.
    
    Args:
        fetch_function: Function to fetch email IDs (with pagination)
        process_function: Function to process batches of email IDs
        query: Gmail search query string
        estimated_count: Estimated number of emails to process
        batch_sizing: Batch size configuration dictionary
        operation_name: Name of the operation for logging
        
    Yields:
        Progress information dictionaries
    """
    # Initialize tracking variables
    total_processed = 0
    start_time = time.time()
    page_token = None
    
    # Default batch sizing if not provided
    if not batch_sizing:
        batch_sizing = {
            "initial_batch_size": 25,
            "max_batch_size": 100,
            "growth_factor": 1.5,
            "provide_feedback_every": 50
        }
    
    # Extract batch sizing parameters
    batch_size = batch_sizing["initial_batch_size"]
    max_batch_size = batch_sizing["max_batch_size"]
    growth_factor = batch_sizing["growth_factor"]
    feedback_interval = batch_sizing["provide_feedback_every"]
    
    # Continue until we've processed everything
    while True:
        # Calculate current batch size based on remaining items
        if estimated_count is not None:
            remaining = estimated_count - total_processed
            current_batch_size = min(batch_size, remaining)
            if current_batch_size <= 0:
                break
        else:
            current_batch_size = batch_size
        
        # Fetch the next batch of IDs
        try:
            fetch_result = await fetch_function(
                query=query, 
                max_results=current_batch_size, 
                page_token=page_token
            )
            
            if not fetch_result or not fetch_result.get("messages", []):
                logger.info(f"No more emails to {operation_name}")
                break
                
            messages = fetch_result.get("messages", [])
            batch_ids = [msg["id"] for msg in messages]
            
            # Process this batch immediately
            if batch_ids:
                process_result = await process_function(batch_ids)
                
                # Update processed count
                batch_processed = len(batch_ids)
                total_processed += batch_processed
                
                # Calculate progress percentage if we have an estimate
                progress_percentage = None
                if estimated_count is not None and estimated_count > 0:
                    progress_percentage = (total_processed / estimated_count) * 100
                
                # Calculate processing rate
                elapsed_time = time.time() - start_time
                processing_rate = total_processed / elapsed_time if elapsed_time > 0 else 0
                
                # Provide progress feedback
                progress_info = {
                    f"{operation_name}ed_count": batch_processed,
                    f"total_{operation_name}ed": total_processed,
                    "estimated_total": estimated_count,
                    "progress_percentage": progress_percentage,
                    "processing_rate": processing_rate,  # items per second
                    "elapsed_time": elapsed_time
                }
                
                logger.info(
                    f"{operation_name.capitalize()}ed {batch_processed} emails. "
                    f"Total: {total_processed}. "
                    f"Progress: {progress_percentage:.1f}%" if progress_percentage else "Progress: Unknown"
                )
                
                # Yield progress information
                yield progress_info
            
            # Get next page token for pagination
            page_token = fetch_result.get("nextPageToken")
            if not page_token:
                break
                
            # Increase batch size for efficiency after first few batches,
            # but don't exceed maximum
            batch_size = min(batch_size * growth_factor, max_batch_size)
                
        except Exception as e:
            logger.error(f"Error during progressive {operation_name} operation: {str(e)}")
            yield {
                "error": str(e),
                f"total_{operation_name}ed": total_processed,
                "estimated_total": estimated_count,
                "success": False
            }
            break
    
    # Final progress update
    total_time = time.time() - start_time
    final_rate = total_processed / total_time if total_time > 0 else 0
    
    yield {
        "operation_complete": True,
        f"total_{operation_name}ed": total_processed,
        "estimated_total": estimated_count,
        "total_time": total_time,
        "final_processing_rate": final_rate,
        "success": True
    }
