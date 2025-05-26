"""
Thread management tools for Gmail operations.
Provides thread-level email management capabilities.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator

from app.services.tool_registry import tool_registry, ToolDefinition
from damien_cli.core_api import gmail_api_service
from damien_cli.core_api.exceptions import GmailApiError
from app.services.damien_adapter import DamienAdapter
import logging

logger = logging.getLogger(__name__)


# Define thread tool schemas
THREAD_TOOLS = {
    "damien_list_threads": ToolDefinition(
        name="damien_list_threads",
        description="Lists email threads with optional filtering and pagination.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail query string to filter threads (e.g., 'is:unread', 'label:important')"
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 500,
                    "default": 100,
                    "description": "Maximum number of threads to return"
                },
                "page_token": {
                    "type": "string",
                    "description": "Token for pagination to get next page of results"
                }
            }
        },
        handler="list_threads_handler"
    ),
    
    "damien_get_thread_details": ToolDefinition(
        name="damien_get_thread_details",
        description="Get complete details for a specific email thread including all messages.",
        input_schema={
            "type": "object",
            "properties": {
                "thread_id": {
                    "type": "string",
                    "description": "Thread ID to retrieve details for"
                },
                "format": {
                    "type": "string",
                    "enum": ["full", "metadata", "minimal"],
                    "default": "full",
                    "description": "Detail level: 'full' (complete), 'metadata' (headers only), 'minimal' (IDs only)"
                }
            },
            "required": ["thread_id"]
        },
        handler="get_thread_details_handler"
    ),
    
    "damien_modify_thread_labels": ToolDefinition(
        name="damien_modify_thread_labels",
        description="Add or remove labels from an entire email thread.",
        input_schema={
            "type": "object",
            "properties": {
                "thread_id": {
                    "type": "string",
                    "description": "Thread ID to modify labels for"
                },
                "add_labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of label names to add to the thread"
                },
                "remove_labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of label names to remove from the thread"
                }
            },
            "required": ["thread_id"]
        },
        handler="modify_thread_labels_handler"
    ),
    
    "damien_trash_thread": ToolDefinition(
        name="damien_trash_thread",
        description="Move an entire email thread to trash (reversible action).",
        input_schema={
            "type": "object",
            "properties": {
                "thread_id": {
                    "type": "string",
                    "description": "Thread ID to move to trash"
                }
            },
            "required": ["thread_id"]
        },
        handler="trash_thread_handler"
    ),
    
    "damien_delete_thread_permanently": ToolDefinition(
        name="damien_delete_thread_permanently",
        description="Permanently delete an entire email thread (irreversible action).",
        input_schema={
            "type": "object",
            "properties": {
                "thread_id": {
                    "type": "string",
                    "description": "Thread ID to permanently delete (irreversible action)"
                }
            },
            "required": ["thread_id"]
        },
        handler="delete_thread_permanently_handler"
    )
}



# Pydantic Models for Input Validation
class ListThreadsParams(BaseModel):
    """Parameters for listing email threads."""
    query: Optional[str] = Field(
        None, 
        description="Gmail query string to filter threads (e.g., 'is:unread', 'label:important')"
    )
    max_results: int = Field(
        default=100, 
        ge=1, 
        le=500, 
        description="Maximum number of threads to return"
    )
    page_token: Optional[str] = Field(
        None, 
        description="Token for pagination to get next page of results"
    )


class GetThreadDetailsParams(BaseModel):
    """Parameters for getting thread details."""
    thread_id: str = Field(
        ..., 
        description="Thread ID to retrieve details for"
    )
    format: str = Field(
        default="full", 
        description="Detail level: 'full' (complete), 'metadata' (headers only), 'minimal' (IDs only)"
    )
    
    @field_validator('format')
    def validate_format(cls, v):
        allowed_formats = ['full', 'metadata', 'minimal']
        if v not in allowed_formats:
            raise ValueError(f"Format must be one of: {allowed_formats}")
        return v


class ModifyThreadLabelsParams(BaseModel):
    """Parameters for modifying thread labels."""
    thread_id: str = Field(
        ..., 
        description="Thread ID to modify labels for"
    )
    add_labels: Optional[List[str]] = Field(
        None, 
        description="List of label names to add to the thread"
    )
    remove_labels: Optional[List[str]] = Field(
        None, 
        description="List of label names to remove from the thread"
    )


class TrashThreadParams(BaseModel):
    """Parameters for trashing a thread."""
    thread_id: str = Field(
        ..., 
        description="Thread ID to move to trash"
    )


class DeleteThreadPermanentlyParams(BaseModel):
    """Parameters for permanently deleting a thread."""
    thread_id: str = Field(
        ..., 
        description="Thread ID to permanently delete (irreversible action)"
    )



# Handler Functions
async def list_threads_handler(params: ListThreadsParams, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    List email threads with optional filtering.
    
    Gmail scope required: gmail.readonly or gmail.modify
    Rate limit group: gmail_api_read
    """
    try:
        damien_adapter = DamienAdapter()
        gmail_service = await damien_adapter.get_gmail_service()
        
        result = gmail_api_service.list_threads(
            gmail_service=gmail_service,
            query=params.query,
            max_results=params.max_results,
            page_token=params.page_token
        )
        
        # Enhance response with context
        enhanced_result = {
            **result,
            "total_threads": len(result.get("threads", [])),
            "query_used": params.query,
            "context": {
                "user_id": context.get("user_id"),
                "session_id": context.get("session_id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_name": context.get("tool_name")
            }
        }
        
        return enhanced_result
        
    except GmailApiError as e:
        return {
            "success": False,
            "error_message": str(e),
            "error_type": "gmail_api_error",
            "context": context
        }
    except Exception as e:
        return {
            "success": False, 
            "error_message": f"Unexpected error listing threads: {str(e)}",
            "error_type": "internal_error",
            "context": context
        }


async def get_thread_details_handler(params: GetThreadDetailsParams, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get complete details for a specific thread.
    
    Gmail scope required: gmail.readonly or gmail.modify
    Rate limit group: gmail_api_read
    """
    try:
        damien_adapter = DamienAdapter()
        gmail_service = await damien_adapter.get_gmail_service()
        
        result = gmail_api_service.get_thread_details(
            gmail_service=gmail_service,
            thread_id=params.thread_id,
            format=params.format
        )
        
        # Enhance response with context
        enhanced_result = {
            **result,
            "format_requested": params.format,
            "context": {
                "user_id": context.get("user_id"),
                "session_id": context.get("session_id"), 
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_name": context.get("tool_name")
            }
        }
        
        return enhanced_result
        
    except GmailApiError as e:
        return {
            "success": False,
            "error_message": str(e),
            "error_type": "gmail_api_error",
            "thread_id": params.thread_id,
            "context": context
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Unexpected error getting thread details: {str(e)}",
            "error_type": "internal_error", 
            "thread_id": params.thread_id,
            "context": context
        }



async def modify_thread_labels_handler(params: ModifyThreadLabelsParams, context: Dict[str, Any]) -> Dict[str, Any]:
    """Add or remove labels from an entire thread."""
    try:
        if not params.add_labels and not params.remove_labels:
            return {
                "success": False,
                "error_message": "Must specify either add_labels or remove_labels",
                "error_type": "validation_error",
                "thread_id": params.thread_id,
                "context": context
            }
        
        damien_adapter = DamienAdapter()
        gmail_service = await damien_adapter.get_gmail_service()
        
        result = gmail_api_service.modify_thread_labels(
            gmail_service=gmail_service,
            thread_id=params.thread_id,
            add_labels=params.add_labels,
            remove_labels=params.remove_labels
        )
        
        enhanced_result = {
            **result,
            "operation_summary": {
                "labels_added": len(params.add_labels or []),
                "labels_removed": len(params.remove_labels or [])
            },
            "context": {
                "user_id": context.get("user_id"),
                "session_id": context.get("session_id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_name": context.get("tool_name")
            }
        }
        
        return enhanced_result
        
    except GmailApiError as e:
        return {
            "success": False,
            "error_message": str(e),
            "error_type": "gmail_api_error",
            "thread_id": params.thread_id,
            "context": context
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Unexpected error modifying thread labels: {str(e)}",
            "error_type": "internal_error",
            "thread_id": params.thread_id,
            "context": context
        }


async def trash_thread_handler(params: TrashThreadParams, context: Dict[str, Any]) -> Dict[str, Any]:
    """Move an entire thread to trash."""
    try:
        damien_adapter = DamienAdapter()
        gmail_service = await damien_adapter.get_gmail_service()
        
        result = gmail_api_service.trash_thread(
            gmail_service=gmail_service,
            thread_id=params.thread_id
        )
        
        enhanced_result = {
            **result,
            "operation": "trash_thread",
            "reversible": True,
            "context": {
                "user_id": context.get("user_id"),
                "session_id": context.get("session_id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_name": context.get("tool_name")
            }
        }
        
        return enhanced_result
        
    except GmailApiError as e:
        return {
            "success": False,
            "error_message": str(e),
            "error_type": "gmail_api_error",
            "thread_id": params.thread_id,
            "context": context
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Unexpected error trashing thread: {str(e)}",
            "error_type": "internal_error",
            "thread_id": params.thread_id,
            "context": context
        }



async def delete_thread_permanently_handler(params: DeleteThreadPermanentlyParams, context: Dict[str, Any]) -> Dict[str, Any]:
    """Permanently delete an entire thread (irreversible)."""
    try:
        damien_adapter = DamienAdapter()
        gmail_service = await damien_adapter.get_gmail_service()
        
        result = gmail_api_service.delete_thread_permanently(
            gmail_service=gmail_service,
            thread_id=params.thread_id
        )
        
        enhanced_result = {
            **result,
            "operation": "delete_thread_permanently",
            "reversible": False,
            "warning": "Thread has been permanently deleted and cannot be recovered",
            "context": {
                "user_id": context.get("user_id"),
                "session_id": context.get("session_id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_name": context.get("tool_name")
            }
        }
        
        return enhanced_result
        
    except GmailApiError as e:
        return {
            "success": False,
            "error_message": str(e),
            "error_type": "gmail_api_error", 
            "thread_id": params.thread_id,
            "context": context
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Unexpected error deleting thread: {str(e)}",
            "error_type": "internal_error",
            "thread_id": params.thread_id,
            "context": context
        }


# Tool Registration Function
def register_thread_tools():
    """Register all thread management tools with the tool registry."""
    print("DEBUG: register_thread_tools() called")  # Debug line
    logger.info("DEBUG: Starting thread tools registration")  # Debug line
    
    print(f"DEBUG: THREAD_TOOLS keys: {list(THREAD_TOOLS.keys())}")  # Debug line
    print(f"DEBUG: THREAD_TOOLS length: {len(THREAD_TOOLS)}")  # Debug line
    
    handlers = {
        "list_threads_handler": list_threads_handler,
        "get_thread_details_handler": get_thread_details_handler,
        "modify_thread_labels_handler": modify_thread_labels_handler,
        "trash_thread_handler": trash_thread_handler,
        "delete_thread_permanently_handler": delete_thread_permanently_handler
    }
    
    print(f"DEBUG: handlers keys: {list(handlers.keys())}")  # Debug line
    
    for tool_name, tool_def in THREAD_TOOLS.items():
        print(f"DEBUG: Processing tool: {tool_name}, handler: {tool_def.handler_name}")  # Debug line
        try:
            handler = handlers[tool_def.handler_name]
            print(f"DEBUG: Got handler for {tool_name}: {handler}")  # Debug line
            tool_registry.register_tool(tool_def, handler)
            print(f"DEBUG: Successfully registered {tool_name}")  # Debug line
            logger.info(f"DEBUG: Registered thread tool: {tool_name}")  # Debug line
        except Exception as e:
            print(f"DEBUG: ERROR registering {tool_name}: {e}")  # Debug line
            logger.error(f"Failed to register {tool_name}: {e}")  # Debug line
    
    logger.info(f"Registered {len(THREAD_TOOLS)} thread tools")
