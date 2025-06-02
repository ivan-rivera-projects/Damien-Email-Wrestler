"""
Query optimization utilities for Gmail API operations.

This module provides functions to optimize Gmail search queries for better performance,
especially for bulk operations involving large numbers of emails.
"""

import logging
from typing import List, Optional

# Set up logger
logger = logging.getLogger(__name__)

def optimize_bulk_query(original_query: str, estimated_count: Optional[int] = None) -> List[str]:
    """
    Split large queries into targeted sub-queries for better performance.
    
    Args:
        original_query: The original Gmail search query
        estimated_count: Estimated number of results (to determine optimization strategy)
        
    Returns:
        List of optimized queries that collectively cover the same search space
        as the original query, but with better performance characteristics.
    """
    # For small operations, no optimization needed
    if estimated_count is not None and estimated_count < 100:
        return [original_query]
    
    # Initialize targeted queries list
    targeted_queries = []
    
    # If query contains date-based criteria without specific categories, split by category
    if any(date_term in original_query for date_term in ["older_than:", "before:", "older:", "date:"]) and \
       not any(category in original_query for category in ["in:", "from:", "label:", "category:"]):
        
        # Extract base query
        base_query = original_query
        
        # Add category-specific queries for common categories
        categories = ["in:promotions", "in:social", "in:updates", "in:forums"]
        for category in categories:
            targeted_queries.append(f"{category} {base_query}")
        
        # Add a catch-all for emails not in categories
        targeted_queries.append(f"-in:promotions -in:social -in:updates -in:forums {base_query}")
    
    # If query already has specific targeting or is otherwise specific, use as is
    else:
        targeted_queries = [original_query]
    
    logger.debug(f"Optimized query '{original_query}' into {len(targeted_queries)} targeted queries")
    
    return targeted_queries


def get_batch_size_strategy(operation_type: str, estimated_count: Optional[int] = None) -> dict:
    """
    Determine optimal batch sizes for progressive operations.
    
    Args:
        operation_type: Type of operation (e.g., 'trash', 'label', 'mark_read')
        estimated_count: Estimated number of items to process
        
    Returns:
        Dictionary with batch sizing strategy
    """
    # Default batch sizing strategy
    strategy = {
        "initial_batch_size": 25,
        "max_batch_size": 100,
        "growth_factor": 1.5,
        "provide_feedback_every": 50
    }
    
    # Adjust based on operation type
    if operation_type == "trash" or operation_type == "delete":
        # Trashing/deleting is usually faster
        strategy["initial_batch_size"] = 30
        strategy["max_batch_size"] = 150
    elif operation_type == "label":
        # Labeling can handle larger batches
        strategy["initial_batch_size"] = 40
        strategy["max_batch_size"] = 200
    
    # Adjust based on estimated count
    if estimated_count is not None:
        if estimated_count > 1000:
            # For very large operations, start with larger batches
            strategy["initial_batch_size"] = min(100, strategy["initial_batch_size"] * 2)
            strategy["provide_feedback_every"] = 100
        elif estimated_count < 100:
            # For small operations, use simpler approach
            strategy["initial_batch_size"] = min(estimated_count, strategy["initial_batch_size"])
            strategy["growth_factor"] = 1.0  # No growth for small operations
    
    return strategy
