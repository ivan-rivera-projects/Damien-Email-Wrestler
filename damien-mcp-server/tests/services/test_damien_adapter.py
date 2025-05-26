import sys
import os
from pathlib import Path

# Add project and integration module paths for imports
_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_root / "damien-cli"))
sys.path.insert(0, str(_root / "damien-mcp-server"))

"""Tests for the DamienAdapter service."""

import sys
from pathlib import Path
# Ensure damien_cli module is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "damien-mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.damien_adapter import DamienAdapter

# Mark all tests in this module as asyncio tests
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_damien_integration_module():
    """Fixture to mock the Damien Gmail integration module."""
    mock = MagicMock()
    # Methods should match damien_cli.integrations.gmail_integration
    mock.get_gmail_service = MagicMock(return_value=MagicMock(name="g_service_client_mock"))
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
def adapter(mock_damien_integration_module, mock_rules_module):
    """Fixture to create a DamienAdapter with mocked modules."""
    adapter = DamienAdapter()
    adapter.damien_gmail_integration_module = mock_damien_integration_module
    adapter.damien_rules_module = mock_rules_module
    adapter._g_service_client = MagicMock()
    return adapter

@patch("app.services.damien_adapter.settings")
async def test_ensure_g_service_client(mock_settings, adapter, mock_damien_integration_module):
    """Test _ensure_g_service_client method."""
    # Cached client should be returned without calling integration
    existing_client = adapter._g_service_client
    result = await adapter._ensure_g_service_client()
    assert result is existing_client
    mock_damien_integration_module.get_gmail_service.assert_not_called()

    # Initialize when no client cached
    adapter._g_service_client = None
    result = await adapter._ensure_g_service_client()
    mock_damien_integration_module.get_gmail_service.assert_called_once_with()
    assert result is mock_damien_integration_module.get_gmail_service.return_value

async def test_list_emails_tool(adapter, mock_damien_integration_module):
    """Test list_emails_tool method."""
    # Mock client initialization
    adapter._ensure_g_service_client = AsyncMock(return_value=MagicMock())

    # Default parameters
    result = await adapter.list_emails_tool()
    mock_damien_integration_module.list_messages.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        query_string=None,
        max_results=10,
        page_token=None,
        include_headers=None
    )
    assert result["success"] is True
    assert "email_summaries" in result["data"]
    assert len(result["data"]["email_summaries"]) == 1

    # Custom parameters
    mock_damien_integration_module.list_messages.reset_mock()
    result = await adapter.list_emails_tool(
        query="is:unread", max_results=20, page_token="token456", include_headers=["Subject"]
    )
    mock_damien_integration_module.list_messages.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        query_string="is:unread",
        max_results=20,
        page_token="token456",
        include_headers=["Subject"]
    )

    # Error handling
    mock_damien_integration_module.list_messages.side_effect = Exception("Test error")
    result = await adapter.list_emails_tool()
    assert result["success"] is False
    assert "error_message" in result and "error_code" in result

async def test_get_email_details_tool(adapter, mock_damien_integration_module):
    """Test get_email_details_tool method."""
    adapter._ensure_g_service_client = AsyncMock(return_value=MagicMock())

    # Default format
    result = await adapter.get_email_details_tool(message_id="msg_id_123")
    mock_damien_integration_module.get_message_details.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_id="msg_id_123",
        email_format="metadata"
    )
    assert result["success"] is True
    assert result["data"]["id"] == "msg1"

    # Custom format
    mock_damien_integration_module.get_message_details.reset_mock()
    await adapter.get_email_details_tool(message_id="msg_id_123", format_option="full")
    mock_damien_integration_module.get_message_details.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_id="msg_id_123",
        email_format="full"
    )

    # Error handling
    mock_damien_integration_module.get_message_details.side_effect = Exception("Test error")
    result = await adapter.get_email_details_tool(message_id="msg_id_123")
    assert result["success"] is False
    assert "error_message" in result and "error_code" in result

async def test_trash_emails_tool(adapter, mock_damien_integration_module):
    """Test trash_emails_tool method."""
    adapter._ensure_g_service_client = AsyncMock(return_value=MagicMock())

    # Valid IDs
    result = await adapter.trash_emails_tool(message_ids=["msg1", "msg2"])
    mock_damien_integration_module.batch_trash_messages.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_ids=["msg1", "msg2"]
    )
    assert result["success"] is True
    assert result["data"]["trashed_count"] == 2

    # Empty IDs
    mock_damien_integration_module.batch_trash_messages.reset_mock()
    result = await adapter.trash_emails_tool(message_ids=[])
    assert result["success"] is False
    mock_damien_integration_module.batch_trash_messages.assert_not_called()

    # Error handling
    mock_damien_integration_module.batch_trash_messages.side_effect = Exception("Test error")
    result = await adapter.trash_emails_tool(message_ids=["msg1"])
    assert result["success"] is False
    assert "error_message" in result and "error_code" in result

async def test_label_emails_tool(adapter, mock_damien_integration_module):
    """Test label_emails_tool method."""
    adapter._ensure_g_service_client = AsyncMock(return_value=MagicMock())

    # Add labels
    result = await adapter.label_emails_tool(
        message_ids=["msg1"],
        add_label_names=["Label1", "Label2"],
        remove_label_names=None
    )
    mock_damien_integration_module.batch_modify_message_labels.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_ids=["msg1"],
        add_label_names=["Label1", "Label2"],
        remove_label_names=None
    )
    assert result["success"] is True
    assert result["data"]["modified_count"] == 1

    # Remove labels
    mock_damien_integration_module.batch_modify_message_labels.reset_mock()
    result = await adapter.label_emails_tool(
        message_ids=["msg1", "msg2"],
        add_label_names=None,
        remove_label_names=["Label3"]
    )
    mock_damien_integration_module.batch_modify_message_labels.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_ids=["msg1", "msg2"],
        add_label_names=None,
        remove_label_names=["Label3"]
    )
    assert result["success"] is True
    assert result["data"]["modified_count"] == 2

    # Both add and remove
    mock_damien_integration_module.batch_modify_message_labels.reset_mock()
    await adapter.label_emails_tool(
        message_ids=["msg1"],
        add_label_names=["Label1"],
        remove_label_names=["Label2"]
    )
    mock_damien_integration_module.batch_modify_message_labels.assert_called_once_with(
        service=adapter._ensure_g_service_client.return_value,
        message_ids=["msg1"],
        add_label_names=["Label1"],
        remove_label_names=["Label2"]
)