import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.tools import draft_tools

@pytest.mark.asyncio
@patch("damien_cli.integrations.gmail_integration.get_gmail_service")
async def test_create_draft_handler(mock_get_gmail_service_original_location):
    mock_gmail_service = AsyncMock()
    mock_get_gmail_service_original_location.return_value = mock_gmail_service

    # Mock the gmail_api_service.create_draft function
    with patch("app.tools.draft_tools.gmail_api_service.create_draft") as mock_create_draft:
        mock_create_draft.return_value = {
            "id": "draft_123",
            "message": {"id": "msg_456"}
        }
        
        params = {
            "to": ["test@example.com"],
            "subject": "Test Subject",
            "body": "Test body content",
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"]
        }
        context = {"session_id": "test_session", "user_id": "test_user"}
        
        result = await draft_tools.create_draft_handler(params, context)
        
        assert result["data"]["id"] == "draft_123"
        assert "created_at" in result["data"]
        assert "recipients" in result["data"]
        assert result["data"]["recipients"]["to"] == ["test@example.com"]
        assert result["data"]["recipients"]["cc"] == ["cc@example.com"]
        assert result["data"]["recipients"]["bcc"] == ["bcc@example.com"]
        assert "user_context" in result["data"]
        
        mock_create_draft.assert_called_once_with(
            gmail_service=mock_gmail_service,
            to_addresses=["test@example.com"],
            subject="Test Subject",
            body="Test body content",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            thread_id=None
        )

@pytest.mark.asyncio
@patch("damien_cli.integrations.gmail_integration.get_gmail_service")
async def test_create_draft_handler_minimal_params(mock_get_gmail_service_original_location):
    """Test creating draft with only required parameters."""
    mock_gmail_service = AsyncMock()
    mock_get_gmail_service_original_location.return_value = mock_gmail_service

    with patch("app.tools.draft_tools.gmail_api_service.create_draft") as mock_create_draft:
        mock_create_draft.return_value = {"id": "draft_123"}
        
        params = {
            "to": ["test@example.com"],
            "subject": "Test Subject",
            "body": "Test body content"
        }
        context = {"session_id": "test_session", "user_id": "test_user"}
        
        result = await draft_tools.create_draft_handler(params, context)
        
        assert result["data"]["id"] == "draft_123"
        assert result["data"]["recipients"]["cc"] == []
        assert result["data"]["recipients"]["bcc"] == []
        mock_create_draft.assert_called_once_with(
            gmail_service=mock_gmail_service,
            to_addresses=["test@example.com"],
            subject="Test Subject",
            body="Test body content",
            cc=None,
            bcc=None,
            thread_id=None
        )

@pytest.mark.asyncio
@patch("app.tools.draft_tools.DamienAdapter")
async def test_send_draft_handler(mock_damien_adapter_class):
    mock_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_gmail_service)
    
    with patch("app.tools.draft_tools.gmail_api_service.send_draft") as mock_send_draft:
        mock_send_draft.return_value = {
            "id": "msg_789",
            "threadId": "thread_456"
        }
        
        params = {"draft_id": "draft_123"}
        context = {"session_id": "test_session", "user_id": "test_user"}
        
        result = await draft_tools.send_draft_handler(params, context)
        
        assert result["id"] == "msg_789"
        assert result["draft_id"] == "draft_123"
        assert result["status"] == "sent"
        assert "sent_at" in result
        mock_send_draft.assert_called_once_with(
            gmail_service=mock_gmail_service,
            draft_id="draft_123"
        )

@pytest.mark.asyncio
@patch("app.tools.draft_tools.DamienAdapter")
async def test_list_drafts_handler(mock_damien_adapter_class):
    mock_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_gmail_service)
    
    with patch("app.tools.draft_tools.gmail_api_service.list_drafts") as mock_list_drafts:
        mock_list_drafts.return_value = {
            "drafts": [
                {"id": "draft_1", "message": {"id": "msg_1"}},
                {"id": "draft_2", "message": {"id": "msg_2"}}
            ],
            "nextPageToken": "token_123"
        }
        
        params = {
            "query": "subject:urgent",
            "max_results": 50
        }
        context = {"session_id": "test_session", "user_id": "test_user"}
        
        result = await draft_tools.list_drafts_handler(params, context)
        
        assert len(result["drafts"]) == 2
        assert result["total_drafts"] == 2
        assert result["query_used"] == "subject:urgent"
        assert "retrieved_at" in result
        mock_list_drafts.assert_called_once_with(
            gmail_service=mock_gmail_service,
            query="subject:urgent",
            max_results=50,
            page_token=None
        )

@pytest.mark.asyncio
@patch("app.tools.draft_tools.DamienAdapter")
async def test_delete_draft_handler(mock_damien_adapter_class):
    mock_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_gmail_service)
    
    with patch("app.tools.draft_tools.gmail_api_service.delete_draft") as mock_delete_draft:
        mock_delete_draft.return_value = {
            "status": "success",
            "message": "Draft draft_123 deleted successfully"
        }
        
        params = {"draft_id": "draft_123"}
        context = {"session_id": "test_session", "user_id": "test_user"}
        
        result = await draft_tools.delete_draft_handler(params, context)
        
        assert result["status"] == "success"
        assert result["draft_id"] == "draft_123"
        assert "deleted_at" in result
        mock_delete_draft.assert_called_once_with(
            gmail_service=mock_gmail_service,
            draft_id="draft_123"
        )

# Test the registration function
def test_register_draft_tools():
    """Test that draft tools are properly registered."""
    with patch("app.tools.draft_tools.tool_registry.register_tool") as mock_register:
        draft_tools.register_draft_tools()
        
        # Should register 6 tools
        assert mock_register.call_count == 6
        
        # Check that all expected tools are registered
        registered_tool_names = [call[0][0].name for call in mock_register.call_args_list]
        expected_tools = [
            "damien_create_draft",
            "damien_update_draft", 
            "damien_send_draft",
            "damien_list_drafts",
            "damien_get_draft_details",
            "damien_delete_draft"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in registered_tool_names
