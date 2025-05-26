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
        with patch('app.tools.thread_tools.DamienAdapter') as mock_adapter_class:
            mock_adapter_instance = mock_adapter_class.return_value
            mock_adapter_instance.get_gmail_service = AsyncMock(return_value=MagicMock())
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
                gmail_service=mock_adapter_instance.get_gmail_service.return_value,
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
        with patch('app.tools.thread_tools.DamienAdapter') as mock_adapter_class:
            mock_adapter_instance = mock_adapter_class.return_value
            mock_adapter_instance.get_gmail_service = AsyncMock(return_value=MagicMock())
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
                gmail_service=mock_adapter_instance.get_gmail_service.return_value,
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
        with patch('app.tools.thread_tools.DamienAdapter') as mock_adapter_class:
            mock_adapter_instance = mock_adapter_class.return_value
            mock_adapter_instance.get_gmail_service = AsyncMock(return_value=MagicMock())
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
                gmail_service=mock_adapter_instance.get_gmail_service.return_value,
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
        with patch('app.tools.thread_tools.DamienAdapter') as mock_adapter_class:
            mock_adapter_instance = mock_adapter_class.return_value
            mock_adapter_instance.get_gmail_service = AsyncMock(return_value=MagicMock())
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
                gmail_service=mock_adapter_instance.get_gmail_service.return_value,
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
        with patch('app.tools.thread_tools.DamienAdapter') as mock_adapter_class:
            mock_adapter_instance = mock_adapter_class.return_value
            mock_adapter_instance.get_gmail_service = AsyncMock(return_value=MagicMock())
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
                gmail_service=mock_adapter_instance.get_gmail_service.return_value,
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
        with patch('app.tools.thread_tools.DamienAdapter') as mock_adapter_class:
            # Simulate Gmail API error
            mock_adapter_instance = mock_adapter_class.return_value
            mock_adapter_instance.get_gmail_service = AsyncMock(return_value=MagicMock())
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
