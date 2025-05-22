import pytest
from unittest.mock import MagicMock, patch # Removed call
from googleapiclient.errors import HttpError

from damien_cli.integrations import gmail_integration
# from damien_cli.core import config # Removed unused import


@pytest.fixture(autouse=True)  # Apply this fixture to all tests in this module
def clear_label_cache():
    """Clears the label cache before each test."""
    gmail_integration._label_name_to_id_cache.clear()
    yield  # This allows the test to run
    gmail_integration._label_name_to_id_cache.clear()  # Clear after if needed, though before is usually enough


@pytest.fixture
def mock_service():
    service = MagicMock()
    # Default execute returns for common patterns if not overridden by a specific test
    service.users.return_value.messages.return_value.list.return_value.execute.return_value = (
        {}
    )
    service.users.return_value.messages.return_value.get.return_value.execute.return_value = (
        {}
    )
    service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": []
    }
    service.users.return_value.messages.return_value.batchModify.return_value.execute.return_value = (
        {}
    )  # Simulates 204 No Content
    service.users.return_value.messages.return_value.batchDelete.return_value.execute.return_value = (
        {}
    )  # Simulates 204 No Content
    return service


# --- Tests for Read Operations (Existing, ensure they still pass) ---
def test_list_messages_success(mock_service):
    expected_response = {
        "messages": [
            {"id": "123", "threadId": "abc"},
            {"id": "456", "threadId": "def"},
        ],
        "nextPageToken": "some_token",
    }
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = (
        expected_response
    )
    result = gmail_integration.list_messages(
        mock_service, query_string="is:unread", max_results=5
    )
    mock_service.users.return_value.messages.return_value.list.assert_called_once_with(
        userId="me", q="is:unread", maxResults=5
    )
    assert result == expected_response


def test_list_messages_with_page_token(mock_service):
    expected_response = {"messages": [{"id": "789"}], "nextPageToken": "final_token"}
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = (
        expected_response
    )
    result = gmail_integration.list_messages(
        mock_service, query_string="is:read", max_results=3, page_token="start_token"
    )
    mock_service.users.return_value.messages.return_value.list.assert_called_once_with(
        userId="me", q="is:read", maxResults=3, pageToken="start_token"
    )
    assert result == expected_response


def test_list_messages_no_query(mock_service):
    expected_response = {
        "messages": [],
        "nextPageToken": None,
    }  # Ensure nextPageToken is expected
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = (
        expected_response
    )
    result = gmail_integration.list_messages(mock_service, max_results=20)
    mock_service.users.return_value.messages.return_value.list.assert_called_once_with(
        userId="me", maxResults=20
    )
    assert result == expected_response


def test_list_messages_api_error(mock_service, capsys):
    mock_service.users.return_value.messages.return_value.list.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=403), content=b"Forbidden"
    )
    result = gmail_integration.list_messages(mock_service, query_string="test")
    assert result is None
    captured = capsys.readouterr()
    assert "Damien encountered an API error" in captured.out


def test_list_messages_no_service(capsys):
    result = gmail_integration.list_messages(None, query_string="test")
    assert result is None
    captured = capsys.readouterr()
    assert "Damien cannot list messages: Gmail service not available." in captured.out


def test_get_message_details_success(mock_service):
    expected_message_data = {"id": "msg1", "snippet": "Hello", "payload": {}}
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = (
        expected_message_data
    )
    message_id_to_get = "msg1"
    format_to_use = "metadata"
    result = gmail_integration.get_message_details(
        mock_service, message_id_to_get, email_format=format_to_use
    )
    mock_service.users.return_value.messages.return_value.get.assert_called_once_with(
        userId="me", id=message_id_to_get, format=format_to_use
    )
    assert result == expected_message_data


def test_get_message_details_invalid_format_uses_metadata(mock_service, capsys):
    expected_message_data = {"id": "msg2", "snippet": "Test"}
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = (
        expected_message_data
    )
    message_id_to_get = "msg2"
    result = gmail_integration.get_message_details(
        mock_service, message_id_to_get, email_format="bad_format"
    )
    mock_service.users.return_value.messages.return_value.get.assert_called_once_with(
        userId="me", id=message_id_to_get, format="metadata"
    )
    assert result == expected_message_data
    captured = capsys.readouterr()
    assert (
        "Damien received an invalid format 'bad_format'. Using 'metadata'."
        in captured.out
    )


def test_get_message_details_api_error(mock_service, capsys):
    mock_service.users.return_value.messages.return_value.get.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=404), content=b"Not Found"
    )
    result = gmail_integration.get_message_details(mock_service, "non_existent_id")
    assert result is None
    captured = capsys.readouterr()
    assert "Damien encountered an API error getting message details" in captured.out


def test_get_message_details_no_service(capsys):
    result = gmail_integration.get_message_details(None, "any_id")
    assert result is None
    captured = capsys.readouterr()
    assert (
        "Damien cannot get message details: Gmail service not available."
        in captured.out
    )


# --- NEW TESTS for Phase 2 ---


def test_get_label_id_system_label(mock_service):
    assert gmail_integration.get_label_id(mock_service, "INBOX") == "INBOX"
    assert gmail_integration.get_label_id(mock_service, "TRASH") == "TRASH"
    assert (
        gmail_integration.get_label_id(mock_service, "UnReAd") == "UNREAD"
    )  # Test case insensitivity for system labels
    mock_service.users.return_value.labels.return_value.list.assert_not_called()  # Should not call API for system labels


def test_get_label_id_user_label_found_and_cached(mock_service):
    mock_labels_response = {
        "labels": [
            {"id": "Label_1", "name": "MyLabelOne"},
            {"id": "Label_2", "name": "Another Label"},
        ]
    }
    mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = (
        mock_labels_response
    )

    # First call - populates cache
    assert gmail_integration.get_label_id(mock_service, "MyLabelOne") == "Label_1"
    mock_service.users.return_value.labels.return_value.list.assert_called_once()

    # Second call - should use cache
    assert (
        gmail_integration.get_label_id(mock_service, "mylabelone") == "Label_1"
    )  # Test case insensitivity for user labels
    mock_service.users.return_value.labels.return_value.list.assert_called_once()  # Still called only once

    assert gmail_integration.get_label_id(mock_service, "Another Label") == "Label_2"
    mock_service.users.return_value.labels.return_value.list.assert_called_once()

    # Also test passing an ID directly (should return the ID)
    assert gmail_integration.get_label_id(mock_service, "Label_1") == "Label_1"
    mock_service.users.return_value.labels.return_value.list.assert_called_once()


def test_get_label_id_user_label_not_found(mock_service):
    mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": []
    }
    assert gmail_integration.get_label_id(mock_service, "NonExistentLabel") is None
    mock_service.users.return_value.labels.return_value.list.assert_called_once()


def test_get_label_id_api_error_fetching_labels(mock_service, capsys):
    mock_service.users.return_value.labels.return_value.list.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=500), content=b"Server Error"
    )
    assert gmail_integration.get_label_id(mock_service, "AnyLabel") is None
    captured = capsys.readouterr()
    assert "Damien: Error fetching labels:" in captured.out


def test_batch_modify_message_labels_success(mock_service):
    message_ids = ["id1", "id2"]
    # Mock get_label_id to return known IDs
    with patch.object(
        gmail_integration,
        "get_label_id",
        side_effect=lambda svc, name: f"ID_{name.upper()}",
    ) as mock_get_id:
        result = gmail_integration.batch_modify_message_labels(
            mock_service,
            message_ids,
            add_label_names=["NewLabel", "TRASH"],
            remove_label_names=["OldLabel", "INBOX"],
        )
        assert result is True
        mock_get_id.assert_any_call(mock_service, "NewLabel")
        mock_get_id.assert_any_call(mock_service, "TRASH")
        mock_get_id.assert_any_call(mock_service, "OldLabel")
        mock_get_id.assert_any_call(mock_service, "INBOX")

        expected_body = {
            "ids": message_ids,
            "addLabelIds": [
                "ID_NEWLABEL",
                "ID_TRASH",
            ],  # Assuming get_label_id returns these
            "removeLabelIds": ["ID_OLDLABEL", "ID_INBOX"],
        }
        mock_service.users.return_value.messages.return_value.batchModify.assert_called_once_with(
            userId="me", body=expected_body
        )


def test_batch_modify_message_labels_unknown_label_name(mock_service, capsys):
    message_ids = ["id1"]
    with patch.object(
        gmail_integration,
        "get_label_id",
        side_effect=lambda svc, name: "ID_Known" if name == "Known" else None,
    ) as _: # Assign to _ if mock_get_id is not used
        result = gmail_integration.batch_modify_message_labels(
            mock_service, message_ids, add_label_names=["Unknown", "Known"]
        )

        assert (
            result is True
        )  # Still true because one label was valid and API call was made
        expected_body = {"ids": message_ids, "addLabelIds": ["ID_Known"]}
        mock_service.users.return_value.messages.return_value.batchModify.assert_called_once_with(
            userId="me", body=expected_body
        )
        captured = capsys.readouterr()
        assert (
            "Damien Warning: Label name 'Unknown' not found, skipping for 'add'."
            in captured.out
        )


def test_batch_modify_message_labels_no_valid_labels(mock_service):
    message_ids = ["id1"]
    with patch.object(
        gmail_integration, "get_label_id", return_value=None
    ) as _: # Assign to _ if mock_get_id is not used
        result = gmail_integration.batch_modify_message_labels(
            mock_service, message_ids, add_label_names=["Unknown"]
        )
        assert result is True  # True because no API call needed
        mock_service.users.return_value.messages.return_value.batchModify.assert_not_called()


def test_batch_modify_message_labels_api_error(mock_service):
    mock_service.users.return_value.messages.return_value.batchModify.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=400), content=b"Bad Request"
    )
    with patch.object(
        gmail_integration, "get_label_id", return_value="ID_ANY"
    ):  # Ensure it tries to make the call
        result = gmail_integration.batch_modify_message_labels(
            mock_service, ["id1"], add_label_names=["Any"]
        )
        assert result is False


def test_batch_trash_messages(mock_service):
    message_ids = ["id1", "id2"]
    with patch.object(
        gmail_integration, "batch_modify_message_labels"
    ) as mock_batch_modify:
        gmail_integration.batch_trash_messages(mock_service, message_ids)
        mock_batch_modify.assert_called_once_with(
            mock_service,
            message_ids,
            add_label_names=["TRASH"],
            remove_label_names=["INBOX", "UNREAD"],
        )


def test_batch_mark_messages_read(mock_service):
    message_ids = ["id1"]
    with patch.object(
        gmail_integration, "batch_modify_message_labels"
    ) as mock_batch_modify:
        gmail_integration.batch_mark_messages(mock_service, message_ids, mark_as="read")
        mock_batch_modify.assert_called_once_with(
            mock_service, message_ids, remove_label_names=["UNREAD"]
        )


def test_batch_mark_messages_unread(mock_service):
    message_ids = ["id1"]
    with patch.object(
        gmail_integration, "batch_modify_message_labels"
    ) as mock_batch_modify:
        gmail_integration.batch_mark_messages(
            mock_service, message_ids, mark_as="unread"
        )
        mock_batch_modify.assert_called_once_with(
            mock_service, message_ids, add_label_names=["UNREAD"]
        )


def test_batch_delete_permanently_success(mock_service):
    message_ids = ["id1", "id2"]
    result = gmail_integration.batch_delete_permanently(mock_service, message_ids)
    assert result is True
    expected_body = {"ids": message_ids}
    mock_service.users.return_value.messages.return_value.batchDelete.assert_called_once_with(
        userId="me", body=expected_body
    )


def test_batch_delete_permanently_api_error(mock_service):
    mock_service.users.return_value.messages.return_value.batchDelete.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=403), content=b"Forbidden"
    )
    result = gmail_integration.batch_delete_permanently(mock_service, ["id1"])
    assert result is False
