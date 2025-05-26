"""Tests for the DamienAdapter service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.damien_adapter import DamienAdapter

# Mark all tests in this module as asyncio tests
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_gmail_module():
    """Fixture to mock the Gmail module."""
    mock = MagicMock()
    # Mock critical methods
    mock.get_g_service_client_from_token = MagicMock(return_value=MagicMock())
    mock.list_messages = MagicMock(return_value={
        "messages": [{"id": "msg1", "threadId": "thread1"}],
        "nextPageToken": "token123"
    })
    mock.get_message_details = MagicMock(return_value={
        "id": "msg1", 
        "threadId": "thread1",
        "payload": {"headers": []}
    })
    mock.batch_trash_messages = MagicMock(return_value=True)
    mock.batch_modify_message_labels = MagicMock(return_value=True)
    mock.batch_mark_messages = MagicMock(return_value=True)
    mock.batch_delete_permanently = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_rules_module():
    """Fixture to mock the Rules module."""
    mock = MagicMock()
    mock.apply_rules_to_mailbox = MagicMock(return_value={
        "total_emails_scanned": 10,
        "emails_matching_any_rule": 5,
        "actions_summary": {"trash": 2, "label": 3}
    })
    mock.load_rules = MagicMock(return_value=[
        MagicMock(model_dump=MagicMock(return_value={"id": "rule1", "name": "Rule 1"}))
    ])
    mock.add_rule = MagicMock(
        return_value=MagicMock(model_dump=MagicMock(return_value={"id": "new_rule", "name": "New Rule"}))
    )
    mock.delete_rule = MagicMock(return_value=True)
    return mock


@pytest.fixture
def adapter(mock_gmail_module, mock_rules_module):
    """Fixture to create a DamienAdapter with mocked modules."""
    adapter = DamienAdapter()
    adapter.damien_gmail_module = mock_gmail_module
    adapter.damien_rules_module = mock_rules_module
    adapter._g_service_client = MagicMock()
    return adapter


@patch("app.services.damien_adapter.settings")
async def test_ensure_g_service_client(mock_settings, adapter, mock_gmail_module):
    """Test _ensure_g_service_client method."""
    # Test when client is already cached
    existing_client = adapter._g_service_client
    result = await adapter._ensure_g_service_client()
    assert result is existing_client
    mock_gmail_module.get_g_service_client_from_token.assert_not_called()
    
    # Test when client needs to be initialized
    adapter._g_service_client = None
    mock_settings.gmail_token_path = "token_path"
    mock_settings.gmail_credentials_path = "creds_path"
    mock_settings.gmail_scopes = ["scope1", "scope2"]
    
    result = await adapter._ensure_g_service_client()
    
    mock_gmail_module.get_g_service_client_from_token.assert_called_once_with(
        token_file_path_str="token_path",
        credentials_file_path_str="creds_path",
        scopes=["scope1", "scope2"]
    )
    assert result is mock_gmail_module.get_g_service_client_from_token.return_value


async def test_list_emails_tool(adapter, mock_gmail_module):
    """Test list_emails_tool method."""
    # Patch _ensure_g_service_client to avoid mocking configuration
    adapter._ensure_g_service_client = AsyncMock(return_value=MagicMock())
    
    # Test with default parameters
    result = await adapter.list_emails_tool()
    
    mock_gmail_module.list_messages.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        query_string=None,
        max_results=10,
        page_token=None,
        include_headers=None
    )
    assert result["success"] is True
    assert "email_summaries" in result["data"]
    assert len(result["data"]["email_summaries"]) == 1
    
    # Test with custom parameters
    mock_gmail_module.list_messages.reset_mock()
    result = await adapter.list_emails_tool(
        query="is:unread", max_results=20, page_token="token456"
    )
    
    mock_gmail_module.list_messages.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        query_string="is:unread",
        max_results=20,
        page_token="token456",
        include_headers=None # Assuming default call in adapter passes None
    )
    
    # Test error handling
    mock_gmail_module.list_messages.side_effect = Exception("Test error")
    result = await adapter.list_emails_tool()
    assert result["success"] is False
    assert "error_message" in result
    assert "error_code" in result


async def test_get_email_details_tool(adapter, mock_gmail_module):
    """Test get_email_details_tool method."""
    adapter._ensure_g_service_client = AsyncMock(return_value=MagicMock())
    
    # Test with default format
    result = await adapter.get_email_details_tool(message_id="msg_id_123")
    
    mock_gmail_module.get_message_details.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_id="msg_id_123",
        email_format="metadata",
        include_headers=None
    )
    assert result["success"] is True
    assert result["data"]["id"] == "msg1"
    
    # Test with custom format
    mock_gmail_module.get_message_details.reset_mock()
    await adapter.get_email_details_tool(message_id="msg_id_123", format_option="metadata")
    
    mock_gmail_module.get_message_details.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_id="msg_id_123",
        email_format="metadata",
        include_headers=None # Assuming default call in adapter passes None
    )
    
    # Test error handling
    mock_gmail_module.get_message_details.side_effect = Exception("Test error")
    result = await adapter.get_email_details_tool(message_id="msg_id_123")
    assert result["success"] is False
    assert "error_message" in result
    assert "error_code" in result


async def test_trash_emails_tool(adapter, mock_gmail_module):
    """Test trash_emails_tool method."""
    adapter._ensure_g_service_client = AsyncMock(return_value=MagicMock())
    
    # Test with valid message IDs
    result = await adapter.trash_emails_tool(message_ids=["msg1", "msg2"])
    
    mock_gmail_module.batch_trash_messages.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_ids=["msg1", "msg2"]
    )
    assert result["success"] is True
    assert result["data"]["trashed_count"] == 2
    
    # Test with empty message IDs
    result = await adapter.trash_emails_tool(message_ids=[])
    assert result["success"] is False
    assert "No message IDs provided" in result["error_message"]
    
    # Test error handling
    mock_gmail_module.batch_trash_messages.side_effect = Exception("Test error")
    result = await adapter.trash_emails_tool(message_ids=["msg1"])
    assert result["success"] is False
    assert "error_message" in result
    assert "error_code" in result


async def test_label_emails_tool(adapter, mock_gmail_module):
    """Test label_emails_tool method."""
    adapter._ensure_g_service_client = AsyncMock(return_value=MagicMock())
    
    # Test with add labels
    result = await adapter.label_emails_tool(
        message_ids=["msg1"], 
        add_label_names=["Label1", "Label2"],
        remove_label_names=None
    )
    
    mock_gmail_module.batch_modify_message_labels.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_ids=["msg1"],
        add_label_names=["Label1", "Label2"],
        remove_label_names=None
    )
    assert result["success"] is True
    assert result["data"]["modified_count"] == 1
    
    # Test with remove labels
    mock_gmail_module.batch_modify_message_labels.reset_mock()
    result = await adapter.label_emails_tool(
        message_ids=["msg1", "msg2"], 
        add_label_names=None,
        remove_label_names=["Label3"]
    )
    
    mock_gmail_module.batch_modify_message_labels.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_ids=["msg1", "msg2"],
        add_label_names=None,
        remove_label_names=["Label3"]
    )
    assert result["success"] is True
    assert result["data"]["modified_count"] == 2
    
    # Test with both add and remove
    mock_gmail_module.batch_modify_message_labels.reset_mock()
    await adapter.label_emails_tool(
        message_ids=["msg1"], 
        add_label_names=["Label1"],
        remove_label_names=["Label2"]
    )
    
    mock_gmail_module.batch_modify_message_labels.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_ids=["msg1"],
        add_label_names=["Label1"],
        remove_label_names=["Label2"]
    )