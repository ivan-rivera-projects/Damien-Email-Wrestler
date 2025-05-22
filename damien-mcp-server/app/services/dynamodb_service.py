"""DynamoDB service for managing MCP session context using aioboto3.

This module provides functions for interacting with the DynamoDB table
used to store MCP session context data asynchronously.

The module supports:
1. Retrieving session context data for a specific user and session
2. Saving session context data with an optional TTL
3. Deleting session context data when no longer needed
4. JSON serialization for DynamoDB-specific data types (e.g., Decimal)

Session context data is crucial for maintaining state across multiple interactions
between an MCP client (like Claude) and the Damien MCP Server, allowing for
multi-turn conversations that reference previous results.
"""

import aioboto3 # Changed from boto3
import time
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone
import json
from decimal import Decimal

# Set up logger
logger = logging.getLogger(__name__)

# Helper class for JSON serialization of Decimal (remains the same)
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            # Convert Decimal to float or str. For DynamoDB, numbers are preferred.
            # If precision is critical and numbers cause issues, consider string.
            return float(o) 
        return super().default(o)

# Global aioboto3 session (recommended by aioboto3 for reuse)
_aioboto3_session = None

def get_aioboto3_session():
    """Initialize or return the existing aioboto3 Session."""
    global _aioboto3_session
    if _aioboto3_session is None:
        logger.debug("Initializing new aioboto3 session")
        _aioboto3_session = aioboto3.Session()
    return _aioboto3_session

async def get_session_context(table_name: str, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """Get context data for a session from DynamoDB asynchronously.
    
    This function retrieves the context data for a specific user session from DynamoDB.
    Context data typically includes:
    - Tool call history
    - Previously returned results (e.g., email IDs)
    - User preferences or settings
    
    Args:
        table_name: Name of the DynamoDB table
        user_id: Identifier for the user (typically static for single-user deployments)
        session_id: Unique identifier for the conversation session
        
    Returns:
        Optional[Dict[str, Any]]: The session context data if found, None otherwise
        
    Note:
        - This function handles both JSON-string and native object formats for context_data
        - Errors are caught and logged, returning None instead of raising exceptions
        - Uses aioboto3 for async access to DynamoDB
    """
    try:
        logger.debug(f"Async getting context data for user_id={user_id}, session_id={session_id}")
        logger.debug(f"Using table_name={table_name}")
        
        session = get_aioboto3_session()
        async with session.resource('dynamodb') as dynamodb_resource:
            table = await dynamodb_resource.Table(table_name)
            logger.debug(f"Got async table reference: {table}")
            
            response = await table.get_item(
                Key={
                    'user_id': user_id,
                    'session_id': session_id
                }
            )
            
            logger.debug(f"Async DynamoDB get_item response: {json.dumps(response, cls=DecimalEncoder)}")
            
            if 'Item' in response and 'context_data' in response['Item']:
                context_data = response['Item']['context_data']
                if isinstance(context_data, str):
                    try:
                        return json.loads(context_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse context_data JSON: {e}")
                        return None
                return context_data
            
            logger.warning(f"No context data found for user_id={user_id}, session_id={session_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting session context from DynamoDB async: {e}", exc_info=True)
        return None

async def save_session_context(
    table_name: str, 
    user_id: str, 
    session_id: str, 
    context_data: Dict[str, Any], 
    ttl_seconds: Optional[int] = None
) -> bool:
    """Save or update context data for a session in DynamoDB asynchronously.
    
    This function saves or updates the context data for a specific user session in DynamoDB.
    It can optionally set a TTL (Time-To-Live) value for automatic cleanup of old sessions.
    
    Args:
        table_name: Name of the DynamoDB table
        user_id: Identifier for the user (typically static for single-user deployments)
        session_id: Unique identifier for the conversation session
        context_data: Dictionary containing the session context to save
        ttl_seconds: Optional number of seconds after which the item should expire
                     (if omitted, the item won't automatically expire)
        
    Returns:
        bool: True if saved successfully, False otherwise
        
    Note:
        - If ttl_seconds is provided, the current Unix timestamp is added to it
          and stored in the 'ttl' attribute for DynamoDB's TTL feature
        - The 'last_updated' timestamp is automatically added in ISO format
        - The full item is replaced, not merged with existing data
        - Uses aioboto3 for async access to DynamoDB
    """
    try:
        logger.debug(f"Async saving context data for user_id={user_id}, session_id={session_id}")
        
        item = {
            'user_id': user_id,
            'session_id': session_id,
            'context_data': context_data,
            'last_updated': datetime.now(timezone.utc).isoformat() + 'Z'
        }
        
        if ttl_seconds is not None:
            item['ttl'] = int(time.time()) + ttl_seconds
        
        logger.debug(f"Async putting item into DynamoDB: {item}")
        
        session = get_aioboto3_session()
        async with session.resource('dynamodb') as dynamodb_resource:
            table = await dynamodb_resource.Table(table_name)
            await table.put_item(Item=item)
        
        logger.info(f"Successfully saved context async for user_id={user_id}, session_id={session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving session context to DynamoDB async: {e}", exc_info=True)
        return False

async def delete_session_context(table_name: str, user_id: str, session_id: str) -> bool:
    """Delete context data for a session from DynamoDB asynchronously."""
    try:
        logger.debug(f"Async deleting context data for user_id={user_id}, session_id={session_id}")
        session = get_aioboto3_session()
        async with session.resource('dynamodb') as dynamodb_resource:
            table = await dynamodb_resource.Table(table_name)
            await table.delete_item(
                Key={
                    'user_id': user_id,
                    'session_id': session_id
                }
            )
        
        logger.info(f"Successfully deleted context async for user_id={user_id}, session_id={session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting session context from DynamoDB async: {e}", exc_info=True)
        return False
