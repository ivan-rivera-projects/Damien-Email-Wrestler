#!/usr/bin/env python3
"""
End-to-end tests for the optimized email operations.

This script tests the optimized email operations with real Gmail accounts.
It validates query optimization and progressive batching.

Usage:
    python test_optimizations_e2e.py

Note: Requires an authenticated Gmail account and environment setup.
"""

import asyncio
import time
import logging
import os
import sys

# Add parent directory to path if needed to handle imports from different directories
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_optimization_tests():
    """Run end-to-end tests for the optimized email operations."""
    # Import here after path setup
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        from damien_mcp_server.app.services.damien_adapter import DamienAdapter
    except ImportError as e:
        logger.error(f"Error importing required modules: {e}")
        logger.error("Make sure you're running this from the damien-cli directory.")
        logger.error("Try: cd damien-cli && poetry run python ../tests/test_optimizations_e2e.py")
        return
    
    # Initialize components
    logger.info("Initializing Gmail service...")
    g_service = get_gmail_service()
    
    if not g_service:
        logger.error("Failed to initialize Gmail service. Aborting tests.")
        return
        
    adapter = DamienAdapter()
    
    # Test 1: List emails with optimization
    logger.info("TESTING OPTIMIZED EMAIL LISTING")
    logger.info("==============================")
    
    # First without optimization (baseline)
    start_time = time.time()
    result_standard = await adapter.list_emails_tool(
        query="older_than:30d",
        max_results=100,
        include_headers=["From", "Subject", "Date"],
        optimize_query=False
    )
    standard_time = time.time() - start_time
    
    if result_standard["success"]:
        logger.info(f"Standard query found {len(result_standard['data']['email_summaries'])} emails in {standard_time:.2f} seconds")
    else:
        logger.error(f"Standard query failed: {result_standard['error_message']}")
        return
    
    # Then with optimization
    start_time = time.time()
    result_optimized = await adapter.list_emails_tool(
        query="older_than:30d",
        max_results=100,
        include_headers=["From", "Subject", "Date"],
        optimize_query=True
    )
    optimized_time = time.time() - start_time
    
    if result_optimized["success"]:
        logger.info(f"Optimized query found {len(result_optimized['data']['email_summaries'])} emails in {optimized_time:.2f} seconds")
    else:
        logger.error(f"Optimized query failed: {result_optimized['error_message']}")
        return
    
    # Calculate improvement
    if standard_time > 0:
        improvement = ((standard_time - optimized_time) / standard_time) * 100
        logger.info(f"Query optimization improvement: {improvement:.1f}%")
    
    # Test 2: Progressive trash operation (with a very small subset for safety)
    logger.info("\nTESTING PROGRESSIVE TRASH OPERATION")
    logger.info("===================================")
    
    # Use a very safe test query that won't trash important emails
    # IMPORTANT: This query should be very specific to avoid trashing important emails
    test_query = "older_than:180d in:promotions subject:newsletter"
    
    # First check how many emails match this query
    count_result = await adapter.list_emails_tool(
        query=test_query,
        max_results=5  # Limit to 5 for safety
    )
    
    if count_result["success"]:
        email_count = len(count_result.get("data", {}).get("email_summaries", []))
        logger.info(f"Found {email_count} test emails to process")
        
        # Only proceed if we found test emails (limit to 5 for safety)
        if email_count > 0:
            # Run trash operation with progressive batching (limit to max 5)
            test_count = min(email_count, 5)
            logger.info(f"Starting progressive trash operation for {test_count} emails...")
            start_time = time.time()
            
            trash_result = await adapter.trash_emails_tool(
                query=test_query,
                estimated_count=test_count,
                use_progressive=True,
                optimize_query=True
            )
            
            total_time = time.time() - start_time
            
            if trash_result["success"]:
                logger.info(f"Successfully trashed {trash_result['data']['trashed_count']} emails in {total_time:.2f} seconds")
                logger.info(f"Processing mode: {trash_result['data']['mode']}")
                
                if total_time > 0 and trash_result['data']['trashed_count'] > 0:
                    rate = trash_result['data']['trashed_count'] / total_time
                    logger.info(f"Processing rate: {rate:.1f} emails/second")
            else:
                logger.error(f"Trash operation failed: {trash_result.get('error_message', 'Unknown error')}")
        else:
            logger.warning("No test emails found matching the query. Skipping trash test.")
    else:
        logger.error(f"Failed to count test emails: {count_result.get('error_message', 'Unknown error')}")
    
    logger.info("\nOPTIMIZATION TESTS COMPLETED")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_optimization_tests())
