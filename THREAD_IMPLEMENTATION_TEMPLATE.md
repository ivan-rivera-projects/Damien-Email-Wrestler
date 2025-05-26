 trash.
    
    Args:
        gmail_service: Authenticated Gmail service instance
        thread_id: Thread ID to trash
        
    Returns:
        Dict containing trash operation result
        
    Raises:
        GmailApiError: If Gmail API call fails
    """
    try:
        result = gmail_service.users().threads().trash(
            userId='me',
            id=thread_id
        ).execute()
        
        return {
            "success": True,
            "thread": result,
            "thread_id": thread_id,
            "action": "trashed"
        }
        
    except HttpError as e:
        if e.resp.status == 404:
            raise GmailApiError(f"Thread {thread_id} not found")
        else:
            error_details = e.error_details[0] if e.error_details else {}
            raise GmailApiError(
                f"Failed to trash thread: {error_details.get('message', str(e))}"
            )
    except Exception as e:
        raise GmailApiError(f"Unexpected error trashing thread: {str(e)}")


@with_rate_limiting 
def delete_thread_permanently(gmail_service, thread_id: str) -> Dict:
    """
    Permanently delete entire thread (irreversible).
    
    Args:
        gmail_service: Authenticated Gmail service instance
        thread_id: Thread ID to delete permanently
        
    Returns:
        Dict containing deletion result
        
    Raises:
        GmailApiError: If Gmail API call fails
    """
    try:
        gmail_service.users().threads().delete(
            userId='me',
            id=thread_id
        ).execute()
        
        return {
            "success": True,
            "thread_id": thread_id,
            "action": "permanently_deleted",
            "message": "Thread permanently deleted"
        }
        
    except HttpError as e:
        if e.resp.status == 404:
            raise GmailApiError(f"Thread {thread_id} not found")
        else:
            error_details = e.error_details[0] if e.error_details else {}
            raise GmailApiError(
                f"Failed to delete thread: {error_details.get('message', str(e))}"
            )
    except Exception as e:
        raise GmailApiError(f"Unexpected error deleting thread: {str(e)}")
```

## MCP Handler Template (Create app/tools/thread_tools.py)

```python
"""
Thread management tools for Gmail operations.
Provides thread-level email management capabilities.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator

from app.services.tool_registry import tool_registry
from damien_cli.core_api import gmail_api_service
from damien_cli.core_api.exceptions import GmailApiError


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
    
    @field_validator('add_labels', 'remove_labels')
    def validate_label_lists(cls, v):
        if v is not None and len(v) == 0:
            return None  # Convert empty lists to None
        return v


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
        gmail_service = gmail_api_service.get_gmail_service()
        
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
        gmail_service = gmail_api_service.get_gmail_service()
        
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
    """
    Add or remove labels from an entire thread.
    
    Gmail scope required: gmail.modify
    Rate limit group: gmail_api_write
    """
    try:
        if not params.add_labels and not params.remove_labels:
            return {
                "success": False,
                "error_message": "Must specify either add_labels or remove_labels",
                "error_type": "validation_error",
                "thread_id": params.thread_id,
                "context": context
            }
        
        gmail_service = gmail_api_service.get_gmail_service()
        
        result = gmail_api_service.modify_thread_labels(
            gmail_service=gmail_service,
            thread_id=params.thread_id,
            add_labels=params.add_labels,
            remove_labels=params.remove_labels
        )
        
        # Enhance response with context
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
    """
    Move an entire thread to trash.
    
    Gmail scope required: gmail.modify
    Rate limit group: gmail_api_write
    Confirmation required: No (reversible action)
    """
    try:
        gmail_service = gmail_api_service.get_gmail_service()
        
        result = gmail_api_service.trash_thread(
            gmail_service=gmail_service,
            thread_id=params.thread_id
        )
        
        # Enhance response with context
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
    """
    Permanently delete an entire thread (irreversible).
    
    Gmail scope required: gmail.modify
    Rate limit group: gmail_api_write
    Confirmation required: Yes (irreversible action)
    """
    try:
        gmail_service = gmail_api_service.get_gmail_service()
        
        result = gmail_api_service.delete_thread_permanently(
            gmail_service=gmail_service,
            thread_id=params.thread_id
        )
        
        # Enhance response with context and warning
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
    
    tool_registry.register_tool(
        name="damien_list_threads",
        handler_name="list_threads_handler",
        params_class=ListThreadsParams,
        handler_func=list_threads_handler
    )
    
    tool_registry.register_tool(
        name="damien_get_thread_details", 
        handler_name="get_thread_details_handler",
        params_class=GetThreadDetailsParams,
        handler_func=get_thread_details_handler
    )
    
    tool_registry.register_tool(
        name="damien_modify_thread_labels",
        handler_name="modify_thread_labels_handler", 
        params_class=ModifyThreadLabelsParams,
        handler_func=modify_thread_labels_handler
    )
    
    tool_registry.register_tool(
        name="damien_trash_thread",
        handler_name="trash_thread_handler",
        params_class=TrashThreadParams, 
        handler_func=trash_thread_handler
    )
    
    tool_registry.register_tool(
        name="damien_delete_thread_permanently",
        handler_name="delete_thread_permanently_handler",
        params_class=DeleteThreadPermanentlyParams,
        handler_func=delete_thread_permanently_handler
    )
```

## Test Template (Create test/test_thread_tools.py)

```python
"""
Tests for thread management tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.tools.thread_tools import (
    list_threads_handler,
    get_thread_details_handler, 
    modify_thread_labels_handler,
    trash_thread_handler,
    delete_thread_permanently_handler,
    register_thread_tools,
    ListThreadsParams,
    GetThreadDetailsParams,
    ModifyThreadLabelsParams,
    TrashThreadParams,
    DeleteThreadPermanentlyParams
)
from app.services.tool_registry import tool_registry


@pytest.mark.asyncio
async def test_list_threads_handler():
    """Test listing threads with various parameters."""
    # Mock Gmail service response
    mock_response = {
        "success": True,
        "threads": [
            {"id": "thread_1", "snippet": "Test thread 1"},
            {"id": "thread_2", "snippet": "Test thread 2"}
        ],
        "next_page_token": "next_token_123",
        "result_size_estimate": 2
    }
    
    with patch('app.tools.thread_tools.gmail_api_service') as mock_service:
        mock_service.get_gmail_service.return_value = MagicMock()
        mock_service.list_threads.return_value = mock_response
        
        params = ListThreadsParams(query="is:unread", max_results=50)
        context = {"user_id": "test_user", "session_id": "test_session", "tool_name": "damien_list_threads"}
        
        result = await list_threads_handler(params, context)
        
        assert result["success"] is True
        assert len(result["threads"]) == 2
        assert result["total_threads"] == 2
        assert result["query_used"] == "is:unread"
        assert "context" in result
        
        # Verify Gmail service was called correctly
        mock_service.list_threads.assert_called_once_with(
            gmail_service=mock_service.get_gmail_service.return_value,
            query="is:unread",
            max_results=50,
            page_token=None
        )


@pytest.mark.asyncio
async def test_get_thread_details_handler():
    """Test getting thread details."""
    mock_response = {
        "success": True,
        "thread": {
            "id": "thread_123",
            "messages": [
                {"id": "msg_1", "snippet": "First message"},
                {"id": "msg_2", "snippet": "Second message"}
            ]
        },
        "thread_id": "thread_123",
        "message_count": 2
    }
    
    with patch('app.tools.thread_tools.gmail_api_service') as mock_service:
        mock_service.get_gmail_service.return_value = MagicMock()
        mock_service.get_thread_details.return_value = mock_response
        
        params = GetThreadDetailsParams(thread_id="thread_123", format="full")
        context = {"user_id": "test_user", "session_id": "test_session", "tool_name": "damien_get_thread_details"}
        
        result = await get_thread_details_handler(params, context)
        
        assert result["success"] is True
        assert result["thread"]["id"] == "thread_123"
        assert result["message_count"] == 2
        assert result["format_requested"] == "full"
        assert "context" in result
        
        # Verify Gmail service was called correctly
        mock_service.get_thread_details.assert_called_once_with(
            gmail_service=mock_service.get_gmail_service.return_value,
            thread_id="thread_123",
            format="full"
        )


@pytest.mark.asyncio
async def test_modify_thread_labels_handler():
    """Test modifying thread labels."""
    mock_response = {
        "success": True,
        "thread": {"id": "thread_123"},
        "thread_id": "thread_123", 
        "labels_added": ["Important"],
        "labels_removed": ["Spam"]
    }
    
    with patch('app.tools.thread_tools.gmail_api_service') as mock_service:
        mock_service.get_gmail_service.return_value = MagicMock()
        mock_service.modify_thread_labels.return_value = mock_response
        
        params = ModifyThreadLabelsParams(
            thread_id="thread_123",
            add_labels=["Important"], 
            remove_labels=["Spam"]
        )
        context = {"user_id": "test_user", "session_id": "test_session", "tool_name": "damien_modify_thread_labels"}
        
        result = await modify_thread_labels_handler(params, context)
        
        assert result["success"] is True
        assert result["thread_id"] == "thread_123"
        assert result["operation_summary"]["labels_added"] == 1
        assert result["operation_summary"]["labels_removed"] == 1
        assert "context" in result
        
        # Verify Gmail service was called correctly
        mock_service.modify_thread_labels.assert_called_once_with(
            gmail_service=mock_service.get_gmail_service.return_value,
            thread_id="thread_123",
            add_labels=["Important"],
            remove_labels=["Spam"]
        )


@pytest.mark.asyncio
async def test_trash_thread_handler():
    """Test trashing a thread."""
    mock_response = {
        "success": True,
        "thread": {"id": "thread_123"},
        "thread_id": "thread_123",
        "action": "trashed"
    }
    
    with patch('app.tools.thread_tools.gmail_api_service') as mock_service:
        mock_service.get_gmail_service.return_value = MagicMock()
        mock_service.trash_thread.return_value = mock_response
        
        params = TrashThreadParams(thread_id="thread_123")
        context = {"user_id": "test_user", "session_id": "test_session", "tool_name": "damien_trash_thread"}
        
        result = await trash_thread_handler(params, context)
        
        assert result["success"] is True
        assert result["thread_id"] == "thread_123"
        assert result["operation"] == "trash_thread"
        assert result["reversible"] is True
        assert "context" in result
        
        # Verify Gmail service was called correctly
        mock_service.trash_thread.assert_called_once_with(
            gmail_service=mock_service.get_gmail_service.return_value,
            thread_id="thread_123"
        )


@pytest.mark.asyncio 
async def test_delete_thread_permanently_handler():
    """Test permanently deleting a thread."""
    mock_response = {
        "success": True,
        "thread_id": "thread_123",
        "action": "permanently_deleted",
        "message": "Thread permanently deleted"
    }
    
    with patch('app.tools.thread_tools.gmail_api_service') as mock_service:
        mock_service.get_gmail_service.return_value = MagicMock()
        mock_service.delete_thread_permanently.return_value = mock_response
        
        params = DeleteThreadPermanentlyParams(thread_id="thread_123")
        context = {"user_id": "test_user", "session_id": "test_session", "tool_name": "damien_delete_thread_permanently"}
        
        result = await delete_thread_permanently_handler(params, context)
        
        assert result["success"] is True
        assert result["thread_id"] == "thread_123"
        assert result["operation"] == "delete_thread_permanently"
        assert result["reversible"] is False
        assert "warning" in result
        assert "context" in result
        
        # Verify Gmail service was called correctly
        mock_service.delete_thread_permanently.assert_called_once_with(
            gmail_service=mock_service.get_gmail_service.return_value,
            thread_id="thread_123"
        )


def test_register_thread_tools():
    """Test that all thread tools register correctly."""
    # Clear registry to ensure clean test
    tool_registry._tools.clear()
    tool_registry._handlers.clear()
    
    # Register thread tools
    register_thread_tools()
    
    # Verify all 5 tools are registered
    expected_tools = [
        "damien_list_threads",
        "damien_get_thread_details", 
        "damien_modify_thread_labels",
        "damien_trash_thread",
        "damien_delete_thread_permanently"
    ]
    
    for tool_name in expected_tools:
        assert tool_name in tool_registry._tools
        assert tool_registry._tools[tool_name].handler_name in tool_registry._handlers
    
    # Verify handler functions are correctly mapped
    assert tool_registry._handlers["list_threads_handler"] == list_threads_handler
    assert tool_registry._handlers["get_thread_details_handler"] == get_thread_details_handler
    assert tool_registry._handlers["modify_thread_labels_handler"] == modify_thread_labels_handler
    assert tool_registry._handlers["trash_thread_handler"] == trash_thread_handler
    assert tool_registry._handlers["delete_thread_permanently_handler"] == delete_thread_permanently_handler


@pytest.mark.asyncio
async def test_thread_handler_error_handling():
    """Test error handling in thread handlers."""
    from damien_cli.core_api.exceptions import GmailApiError
    
    with patch('app.tools.thread_tools.gmail_api_service') as mock_service:
        # Simulate Gmail API error
        mock_service.get_gmail_service.return_value = MagicMock()
        mock_service.list_threads.side_effect = GmailApiError("Gmail API rate limit exceeded")
        
        params = ListThreadsParams(query="is:unread")
        context = {"user_id": "test_user", "session_id": "test_session", "tool_name": "damien_list_threads"}
        
        result = await list_threads_handler(params, context)
        
        assert result["success"] is False
        assert "Gmail API rate limit exceeded" in result["error_message"] 
        assert result["error_type"] == "gmail_api_error"
        assert "context" in result


# Test parameter validation
def test_thread_params_validation():
    """Test parameter validation for thread tools."""
    # Valid parameters
    params = ListThreadsParams(query="is:unread", max_results=50)
    assert params.query == "is:unread"
    assert params.max_results == 50
    
    # Invalid max_results (too high)
    with pytest.raises(ValueError):
        ListThreadsParams(max_results=1000)
    
    # Invalid format
    with pytest.raises(ValueError):
        GetThreadDetailsParams(thread_id="123", format="invalid")
    
    # Valid format
    params = GetThreadDetailsParams(thread_id="123", format="metadata")
    assert params.format == "metadata"
```

## Integration Steps

### 1. Add to main.py
```python
# Add this import
from app.tools import thread_tools

# In the lifespan function, add:
register_thread_tools()
```

### 2. Test Registration
```bash
cd damien-mcp-server
poetry run pytest test/test_thread_tools.py -v
```

### 3. Test via MCP Server
```bash
# Start server
poetry run uvicorn app.main:app --reload --port 8892

# List tools (should show 5 new thread tools)
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8892/mcp/list_tools | grep thread

# Test thread listing
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_API_KEY" \
-d '{"tool_name": "damien_list_threads", "input": {"max_results": 5}, "session_id": "test"}' \
http://localhost:8892/mcp/execute_tool
```

This template provides complete, production-ready code following all established patterns in the Damien codebase.
