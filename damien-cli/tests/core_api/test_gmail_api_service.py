import pytest
from unittest.mock import MagicMock, patch, mock_open  # mock_open for file operations
from pathlib import Path
from google.oauth2.credentials import (
    Credentials,
)  # For type checking and creating mock creds
from googleapiclient.errors import HttpError  # For simulating API errors
import json

# Import the module and functions we are testing
from damien_cli.core_api import gmail_api_service
from damien_cli.core_api.exceptions import (
    DamienError,
    GmailApiError,
    InvalidParameterError,
)
from damien_cli.core import config as app_config  # To access configured paths/scopes

# --- Fixtures ---


@pytest.fixture
def mock_google_build():
    """Mocks googleapiclient.discovery.build"""
    with patch("damien_cli.core_api.gmail_api_service.build") as mock_build:
        mock_service_instance = (
            MagicMock()
        )  # This is what build().execute() would return
        mock_build.return_value = mock_service_instance
        yield mock_build, mock_service_instance


@pytest.fixture
def mock_installed_app_flow():
    """Mocks google_auth_oauthlib.flow.InstalledAppFlow"""
    with patch(
        "damien_cli.core_api.gmail_api_service.InstalledAppFlow"
    ) as mock_flow_class:
        mock_flow_instance = MagicMock()
        mock_creds = MagicMock(spec=Credentials)  # Mock credentials object
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.refresh_token = "dummy_refresh_token"
        mock_creds.to_json.return_value = (
            '{"token": "dummy_token", "refresh_token": "dummy_refresh_token"}'
        )
        mock_flow_instance.run_local_server.return_value = mock_creds
        mock_flow_class.from_client_secrets_file.return_value = mock_flow_instance
        yield mock_flow_class, mock_flow_instance


@pytest.fixture
def mock_credentials_class():
    """Mocks google.oauth2.credentials.Credentials"""
    with patch("damien_cli.core_api.gmail_api_service.Credentials") as mock_creds_class:
        yield mock_creds_class


@pytest.fixture(autouse=True)  # Apply this fixture to all tests in this module
def manage_token_file(tmp_path):
    """Manages a temporary TOKEN_FILE for tests and cleans up."""
    original_token_file = app_config.TOKEN_FILE
    original_creds_file = app_config.CREDENTIALS_FILE

    # Use a temporary directory for token and dummy credentials
    temp_data_dir = tmp_path / "data"
    temp_data_dir.mkdir(exist_ok=True)

    app_config.TOKEN_FILE = str(temp_data_dir / "token.json")  # Override config path
    app_config.CREDENTIALS_FILE = str(
        temp_data_dir / "credentials.json"
    )  # Override config path

    # Create a dummy credentials.json for tests that need it for the OAuth flow
    with open(app_config.CREDENTIALS_FILE, "w") as f:
        json.dump(
            {
                "installed": {
                    "client_id": "dummy_client_id",
                    "project_id": "dummy_project",
                    "auth_uri": "...",
                    "token_uri": "...",
                    "client_secret": "dummy_secret",
                }
            },
            f,
        )

    yield  # Test runs here

    # Clean up by restoring original config paths (important if config is module-level global)
    app_config.TOKEN_FILE = original_token_file
    app_config.CREDENTIALS_FILE = original_creds_file
    # No need to delete tmp_path files, pytest handles tmp_path cleanup


# --- Tests for get_authenticated_service ---


def test_get_authenticated_service_valid_token_exists(
    mock_credentials_class, mock_google_build
):
    # ARRANGE
    mock_creds_instance = MagicMock(spec=Credentials)
    mock_creds_instance.valid = True
    mock_creds_instance.expired = False
    mock_creds_instance.refresh_token = "dummy_refresh_token"
    mock_credentials_class.from_authorized_user_file.return_value = mock_creds_instance

    Path(app_config.TOKEN_FILE).touch()  # Ensure token file 'exists'

    # ACT
    service = gmail_api_service.get_authenticated_service()

    # ASSERT
    mock_credentials_class.from_authorized_user_file.assert_called_once_with(
        app_config.TOKEN_FILE, app_config.SCOPES
    )
    mock_google_build[0].assert_called_once_with(
        "gmail", "v1", credentials=mock_creds_instance
    )
    assert (
        service == mock_google_build[1]
    )  # mock_google_build[1] is the mock_service_instance
    Path(app_config.TOKEN_FILE).unlink()  # Clean up dummy token file


def test_get_authenticated_service_expired_token_refreshes(
    mock_credentials_class, mock_installed_app_flow, mock_google_build
):
    # ARRANGE
    mock_creds_instance = MagicMock(spec=Credentials)
    mock_creds_instance.valid = False  # Initially invalid
    mock_creds_instance.expired = True
    mock_creds_instance.refresh_token = "dummy_refresh_token"
    # Simulate successful refresh
    mock_creds_instance.refresh.return_value = None  # refresh modifies in place

    # After refresh, it should be valid
    def set_valid_after_refresh(*args):
        mock_creds_instance.valid = True

    mock_creds_instance.refresh.side_effect = set_valid_after_refresh

    mock_credentials_class.from_authorized_user_file.return_value = mock_creds_instance
    Path(app_config.TOKEN_FILE).touch()

    # Patch open for saving the token
    with patch("builtins.open", mock_open()) as mocked_file_save:
        # ACT
        service = gmail_api_service.get_authenticated_service()

    # ASSERT
    mock_creds_instance.refresh.assert_called_once()
    mocked_file_save.assert_called_once_with(
        Path(app_config.TOKEN_FILE), "w"
    )  # Check token saved
    mock_google_build[0].assert_called_once_with(
        "gmail", "v1", credentials=mock_creds_instance
    )
    assert service == mock_google_build[1]
    Path(app_config.TOKEN_FILE).unlink()


def test_get_authenticated_service_no_token_runs_flow(
    mock_installed_app_flow, mock_google_build, mock_credentials_class
):
    # ARRANGE
    mock_credentials_class.from_authorized_user_file.side_effect = (
        FileNotFoundError  # Simulate token file not found or invalid
    )
    # mock_installed_app_flow is already set up to return mock_creds from run_local_server

    # Ensure CREDENTIALS_FILE exists for the flow to proceed
    Path(app_config.CREDENTIALS_FILE).write_text(
        '{"installed": {}}'
    )  # Minimal dummy content

    with patch(
        "builtins.open", mock_open()
    ) as mocked_file_save:  # For saving new token
        # ACT
        service = gmail_api_service.get_authenticated_service()

    # ASSERT
    mock_installed_app_flow[0].from_client_secrets_file.assert_called_once_with(
        app_config.CREDENTIALS_FILE, app_config.SCOPES
    )
    mock_installed_app_flow[1].run_local_server.assert_called_once()
    mocked_file_save.assert_called_once_with(Path(app_config.TOKEN_FILE), "w")

    # The credentials passed to build should be the ones from run_local_server
    expected_creds_from_flow = mock_installed_app_flow[1].run_local_server.return_value
    mock_google_build[0].assert_called_once_with(
        "gmail", "v1", credentials=expected_creds_from_flow
    )
    assert service == mock_google_build[1]


def test_get_authenticated_service_no_credentials_file_raises_error(
    mock_installed_app_flow, mock_credentials_class
):
    # ARRANGE
    mock_credentials_class.from_authorized_user_file.side_effect = FileNotFoundError
    if Path(
        app_config.CREDENTIALS_FILE
    ).exists():  # Ensure it doesn't exist for this test
        Path(app_config.CREDENTIALS_FILE).unlink()

    # ACT & ASSERT
    with pytest.raises(DamienError, match="Credentials file not found"):
        gmail_api_service.get_authenticated_service()
    mock_installed_app_flow[0].from_client_secrets_file.assert_not_called()


# --- Tests for get_label_id and _populate_label_cache ---
@pytest.fixture
def mock_gservice_for_labels():  # A specific service mock for label tests
    service = MagicMock()
    return service


def test_get_label_id_system_label(mock_gservice_for_labels):
    assert gmail_api_service.get_label_id(mock_gservice_for_labels, "INBOX") == "INBOX"
    mock_gservice_for_labels.users.return_value.labels.return_value.list.assert_not_called()


def test_populate_label_cache_success(mock_gservice_for_labels):
    mock_labels_response = {
        "labels": [
            {"id": "Label_1", "name": "MyLabelOne"},
            {"id": "Label_2", "name": "Another Label"},
        ]
    }
    mock_gservice_for_labels.users.return_value.labels.return_value.list.return_value.execute.return_value = (
        mock_labels_response
    )

    gmail_api_service._populate_label_cache(
        mock_gservice_for_labels
    )  # Test private helper

    assert gmail_api_service._label_name_to_id_cache["mylabelone"] == "Label_1"
    assert (
        gmail_api_service._label_name_to_id_cache["Label_1"] == "Label_1"
    )  # For ID passthrough
    assert gmail_api_service._label_name_to_id_cache["another label"] == "Label_2"
    mock_gservice_for_labels.users.return_value.labels.return_value.list.assert_called_once_with(
        userId="me"
    )


def test_populate_label_cache_api_error(mock_gservice_for_labels):
    mock_gservice_for_labels.users.return_value.labels.return_value.list.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=500), content=b"Server Error"
    )
    with pytest.raises(GmailApiError, match="API error fetching labels"):
        gmail_api_service._populate_label_cache(mock_gservice_for_labels)


def test_get_label_id_user_label_uses_cache_after_population(mock_gservice_for_labels):
    # Populate cache first by mocking the API call for _populate_label_cache
    mock_labels_response = {"labels": [{"id": "L_USER1", "name": "UserLabelXYZ"}]}
    mock_gservice_for_labels.users.return_value.labels.return_value.list.return_value.execute.return_value = (
        mock_labels_response
    )

    # First call for a user label (triggers _populate_label_cache)
    assert (
        gmail_api_service.get_label_id(mock_gservice_for_labels, "UserLabelXYZ")
        == "L_USER1"
    )
    mock_gservice_for_labels.users.return_value.labels.return_value.list.assert_called_once()  # API called once

    # Second call for the same label (should use cache)
    assert (
        gmail_api_service.get_label_id(mock_gservice_for_labels, "userlabelxyz")
        == "L_USER1"
    )
    mock_gservice_for_labels.users.return_value.labels.return_value.list.assert_called_once()  # Still only called once

    # Call with an ID that's now in cache
    assert (
        gmail_api_service.get_label_id(mock_gservice_for_labels, "L_USER1") == "L_USER1"
    )
    mock_gservice_for_labels.users.return_value.labels.return_value.list.assert_called_once()


def test_get_label_id_not_found_after_refresh(mock_gservice_for_labels):
    # ARRANGE
    # Ensure the module-level cache is empty at the start of this test
    gmail_api_service._label_name_to_id_cache.clear()

    # Use patch to spy on the _populate_label_cache function itself
    with patch(
        "damien_cli.core_api.gmail_api_service._populate_label_cache",
        wraps=gmail_api_service._populate_label_cache,
    ) as spy_populate_cache:

        # Configure mock to return empty labels
        mock_gservice_for_labels.users().labels().list().execute.return_value = {
            "labels": []
        }

        # ACT
        result = gmail_api_service.get_label_id(
            mock_gservice_for_labels, "MissingLabel"
        )

        # ASSERT
        assert result is None
        assert (
            spy_populate_cache.call_count == 2
        )  # The cache population function should be called twice


def test_get_label_id_not_found_after_refresh_alt(mock_gservice_for_labels):
    # ARRANGE - Create a more controlled mock chain
    from unittest.mock import MagicMock

    # IMPORTANT: Clear the module-level cache before the test
    gmail_api_service._label_name_to_id_cache.clear()

    # Create a mock for the execute method that we can track
    mock_execute = MagicMock(return_value={"labels": []})

    # Set up the chain to always return our controlled mock_execute
    mock_list = MagicMock()
    mock_list.return_value.execute = mock_execute

    mock_labels = MagicMock()
    mock_labels.return_value.list = mock_list

    mock_users = MagicMock()
    mock_users.return_value.labels = mock_labels

    # Replace the users method on the service mock
    mock_gservice_for_labels.users = mock_users

    # ACT
    result = gmail_api_service.get_label_id(mock_gservice_for_labels, "MissingLabel")

    # ASSERT
    assert result is None
    assert mock_execute.call_count == 2  # Should be called twice


# --- Tests for list_messages ---
@pytest.fixture
def mock_gservice_for_messages():  # A specific service mock for message tests
    service = MagicMock()
    return service


def test_list_messages_success(mock_gservice_for_messages):
    expected_api_response = {
        "messages": [{"id": "msg1"}, {"id": "msg2"}],
        "nextPageToken": "nextToken123",
    }
    mock_gservice_for_messages.users.return_value.messages.return_value.list.return_value.execute.return_value = (
        expected_api_response
    )

    result = gmail_api_service.list_messages(
        mock_gservice_for_messages,
        query_string="is:important",
        max_results=5,
        page_token="prevToken",
    )

    mock_gservice_for_messages.users.return_value.messages.return_value.list.assert_called_once_with(
        userId="me", q="is:important", maxResults=5, pageToken="prevToken"
    )
    assert result == expected_api_response


def test_list_messages_no_query_or_page_token(mock_gservice_for_messages):
    expected_api_response = {"messages": [], "nextPageToken": None}
    mock_gservice_for_messages.users.return_value.messages.return_value.list.return_value.execute.return_value = (
        expected_api_response
    )

    result = gmail_api_service.list_messages(mock_gservice_for_messages, max_results=20)

    mock_gservice_for_messages.users.return_value.messages.return_value.list.assert_called_once_with(
        userId="me", maxResults=20  # No q or pageToken
    )
    assert result == expected_api_response


def test_list_messages_api_error_raises_gmailapierror(mock_gservice_for_messages):
    mock_gservice_for_messages.users.return_value.messages.return_value.list.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=401), content=b"Unauthorized"
    )
    with pytest.raises(GmailApiError, match="API error listing messages: 401"):
        gmail_api_service.list_messages(mock_gservice_for_messages, query_string="test")


def test_list_messages_no_service_raises_invalidparametererror():
    with pytest.raises(
        InvalidParameterError, match="Gmail service not available for list_messages"
    ):
        gmail_api_service.list_messages(None)


# --- Tests for message write operations ---
@pytest.fixture
def mock_gservice_for_write_operations():
    """Service mock specifically configured for write operations"""
    service = MagicMock()
    # Set up basic success responses
    service.users.return_value.messages.return_value.batchModify.return_value.execute.return_value = (
        None  # Returns nothing on success
    )
    service.users.return_value.messages.return_value.batchDelete.return_value.execute.return_value = (
        None  # Returns nothing on success
    )
    return service


def test_batch_modify_message_labels_success(mock_gservice_for_write_operations):
    # ARRANGE
    message_ids = ["msg1", "msg2", "msg3"]
    add_labels = ["IMPORTANT", "Label_A"]
    remove_labels = ["UNREAD", "Label_B"]

    # Set up label resolution via get_label_id
    with patch(
        "damien_cli.core_api.gmail_api_service.get_label_id"
    ) as mock_get_label_id:
        # Mock label ID resolution (assume all labels exist)
        mock_get_label_id.side_effect = lambda service, name: (
            name.upper() if name == "Label_A" or name == "Label_B" else name
        )

        # ACT
        result = gmail_api_service.batch_modify_message_labels(
            mock_gservice_for_write_operations, message_ids, add_labels, remove_labels
        )

        # ASSERT
        assert result is True  # Function returns True on success

        # Check the batchModify was called with correct parameters
        mock_gservice_for_write_operations.users.return_value.messages.return_value.batchModify.assert_called_once()

        # Extract the call arguments
        call_args = (
            mock_gservice_for_write_operations.users.return_value.messages.return_value.batchModify.call_args
        )

        # Verify userId and body parameters
        assert call_args[1]["userId"] == "me"
        assert "ids" in call_args[1]["body"]
        assert call_args[1]["body"]["ids"] == message_ids
        assert "addLabelIds" in call_args[1]["body"]
        assert "removeLabelIds" in call_args[1]["body"]

        # Labels should be in uppercase when resolved from names
        assert set(call_args[1]["body"]["addLabelIds"]) == set(["IMPORTANT", "LABEL_A"])
        assert set(call_args[1]["body"]["removeLabelIds"]) == set(["UNREAD", "LABEL_B"])


def test_batch_modify_message_labels_no_messages(mock_gservice_for_write_operations):
    # ARRANGE: empty message_ids list
    message_ids = []

    # ACT
    result = gmail_api_service.batch_modify_message_labels(
        mock_gservice_for_write_operations, message_ids, ["IMPORTANT"], ["UNREAD"]
    )

    # ASSERT
    assert result is True
    # Verify batchModify was NOT called (no-op when message_ids is empty)
    mock_gservice_for_write_operations.users.return_value.messages.return_value.batchModify.assert_not_called()


def test_batch_modify_message_labels_no_valid_labels(
    mock_gservice_for_write_operations,
):
    # ARRANGE: All label_ids will resolve to None, resulting in no valid changes
    message_ids = ["msg1", "msg2"]

    # Mock label resolution to return None (no valid labels)
    with patch(
        "damien_cli.core_api.gmail_api_service.get_label_id"
    ) as mock_get_label_id:
        mock_get_label_id.return_value = None

        # ACT
        result = gmail_api_service.batch_modify_message_labels(
            mock_gservice_for_write_operations,
            message_ids,
            ["NonExistentLabel"],
            ["AlsoNonExistent"],
        )

        # ASSERT
        assert result is True  # No changes is still "success"
        # Verify no API call was made since there are no valid labels to add/remove
        mock_gservice_for_write_operations.users.return_value.messages.return_value.batchModify.assert_not_called()


def test_batch_modify_message_labels_api_error(mock_gservice_for_write_operations):
    # ARRANGE: API will raise an error
    message_ids = ["msg1", "msg2"]
    mock_gservice_for_write_operations.users.return_value.messages.return_value.batchModify.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=400), content=b"Bad Request"
    )

    # ACT & ASSERT
    with pytest.raises(
        GmailApiError, match="API error during batch label modification"
    ):
        gmail_api_service.batch_modify_message_labels(
            mock_gservice_for_write_operations, message_ids, ["IMPORTANT"], ["UNREAD"]
        )


def test_batch_modify_message_labels_no_service():
    # ARRANGE: No service provided
    # ACT & ASSERT
    with pytest.raises(InvalidParameterError, match="Gmail service not available"):
        gmail_api_service.batch_modify_message_labels(
            None, ["msg1"], ["IMPORTANT"], ["UNREAD"]
        )


def test_batch_trash_messages(mock_gservice_for_write_operations):
    # ARRANGE: batch_trash_messages just calls batch_modify_message_labels with specific parameters
    message_ids = ["msg1", "msg2"]

    # Mock batch_modify_message_labels to verify it's called correctly
    with patch(
        "damien_cli.core_api.gmail_api_service.batch_modify_message_labels"
    ) as mock_modify:
        mock_modify.return_value = True

        # ACT
        result = gmail_api_service.batch_trash_messages(
            mock_gservice_for_write_operations, message_ids
        )

        # ASSERT
        assert result is True
        mock_modify.assert_called_once_with(
            mock_gservice_for_write_operations,
            message_ids,
            add_label_names=["TRASH"],
            remove_label_names=["INBOX", "UNREAD"],
        )


def test_batch_mark_messages_read(mock_gservice_for_write_operations):
    # ARRANGE: Test marking as read
    message_ids = ["msg1", "msg2"]

    # Mock batch_modify_message_labels
    with patch(
        "damien_cli.core_api.gmail_api_service.batch_modify_message_labels"
    ) as mock_modify:
        mock_modify.return_value = True

        # ACT
        result = gmail_api_service.batch_mark_messages(
            mock_gservice_for_write_operations, message_ids, "read"
        )

        # ASSERT
        assert result is True
        mock_modify.assert_called_once_with(
            mock_gservice_for_write_operations,
            message_ids,
            remove_label_names=[
                "UNREAD"
            ],  # Only specify parameters that are explicitly passed
        )


def test_batch_mark_messages_unread(mock_gservice_for_write_operations):
    # ARRANGE: Test marking as unread
    message_ids = ["msg1", "msg2"]

    # Mock batch_modify_message_labels
    with patch(
        "damien_cli.core_api.gmail_api_service.batch_modify_message_labels"
    ) as mock_modify:
        mock_modify.return_value = True

        # ACT
        result = gmail_api_service.batch_mark_messages(
            mock_gservice_for_write_operations, message_ids, "unread"
        )

        # ASSERT
        assert result is True
        mock_modify.assert_called_once_with(
            mock_gservice_for_write_operations,
            message_ids,
            add_label_names=[
                "UNREAD"
            ],  # Only specify parameters that are explicitly passed
        )


def test_batch_mark_messages_invalid_action(mock_gservice_for_write_operations):
    # ARRANGE: Invalid mark_as value
    message_ids = ["msg1", "msg2"]

    # ACT & ASSERT
    with pytest.raises(InvalidParameterError, match="Invalid mark_as action"):
        gmail_api_service.batch_mark_messages(
            mock_gservice_for_write_operations, message_ids, "invalid_action"
        )


def test_batch_delete_permanently_success(mock_gservice_for_write_operations):
    # ARRANGE
    message_ids = ["msg1", "msg2", "msg3"]

    # ACT
    result = gmail_api_service.batch_delete_permanently(
        mock_gservice_for_write_operations, message_ids
    )

    # ASSERT
    assert result is True

    # Check batchDelete was called with correct parameters
    mock_gservice_for_write_operations.users.return_value.messages.return_value.batchDelete.assert_called_once()

    # Extract the call arguments
    call_args = (
        mock_gservice_for_write_operations.users.return_value.messages.return_value.batchDelete.call_args
    )

    # Verify userId and body parameters
    assert call_args[1]["userId"] == "me"
    assert "ids" in call_args[1]["body"]
    assert call_args[1]["body"]["ids"] == message_ids


def test_batch_delete_permanently_no_messages(mock_gservice_for_write_operations):
    # ARRANGE: empty message_ids list
    message_ids = []

    # ACT
    result = gmail_api_service.batch_delete_permanently(
        mock_gservice_for_write_operations, message_ids
    )

    # ASSERT
    assert result is True
    # Verify batchDelete was NOT called (no-op when message_ids is empty)
    mock_gservice_for_write_operations.users.return_value.messages.return_value.batchDelete.assert_not_called()


def test_batch_delete_permanently_api_error(mock_gservice_for_write_operations):
    # ARRANGE: API will raise an error
    message_ids = ["msg1", "msg2"]
    mock_gservice_for_write_operations.users.return_value.messages.return_value.batchDelete.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=400), content=b"Bad Request"
    )

    # ACT & ASSERT
    with pytest.raises(
        GmailApiError, match="API error during batch permanent deletion"
    ):
        gmail_api_service.batch_delete_permanently(
            mock_gservice_for_write_operations, message_ids
        )


def test_batch_delete_permanently_no_service():
    # ARRANGE: No service provided
    # ACT & ASSERT
    with pytest.raises(InvalidParameterError, match="Gmail service not available"):
        gmail_api_service.batch_delete_permanently(None, ["msg1"])


# --- Tests for get_g_service_client_from_token ---

def test_get_g_service_client_from_token_valid_token(mock_credentials_class, mock_google_build, tmp_path):
    # ARRANGE
    token_path = tmp_path / "test_token.json"
    creds_path = tmp_path / "test_creds.json"  # Dummy, may not be strictly needed if refresh_token is self-sufficient
    
    mock_creds_instance = MagicMock(spec=Credentials)
    mock_creds_instance.valid = True
    mock_creds_instance.expired = False
    mock_credentials_class.from_authorized_user_file.return_value = mock_creds_instance
    
    # Simulate token file existing (content doesn't matter as from_authorized_user_file is mocked)
    token_path.touch() 
    creds_path.touch()  # Ensure credentials file "exists" for the logic path
    
    # ACT
    service = gmail_api_service.get_g_service_client_from_token(
        str(token_path), str(creds_path), app_config.SCOPES
    )
    
    # ASSERT
    mock_credentials_class.from_authorized_user_file.assert_called_once_with(str(token_path), app_config.SCOPES)
    mock_google_build[0].assert_called_once_with('gmail', 'v1', credentials=mock_creds_instance)
    assert service == mock_google_build[1]  # mock_google_build[1] is the mock_service_instance


def test_get_g_service_client_from_token_refresh_success(mock_credentials_class, mock_google_build, tmp_path):
    # ARRANGE
    token_path = tmp_path / "test_token.json"
    creds_path = tmp_path / "test_creds.json"
    creds_path.write_text('{"installed":{}}')  # Dummy creds file for refresh context
    
    mock_creds_instance = MagicMock(spec=Credentials)
    mock_creds_instance.valid = False  # Initially invalid
    mock_creds_instance.expired = True
    mock_creds_instance.refresh_token = "a_refresh_token"
    mock_creds_instance.to_json.return_value = '{"refreshed": "new_token_data"}'
    
    # Simulate successful refresh by making 'valid' True after 'refresh' is called
    def refresh_side_effect(request):
        mock_creds_instance.valid = True
    mock_creds_instance.refresh.side_effect = refresh_side_effect
    
    mock_credentials_class.from_authorized_user_file.return_value = mock_creds_instance
    token_path.write_text('{"old": "token_data"}')  # Simulate existing token file
    
    with patch('builtins.open', new_callable=mock_open) as mocked_token_save:
        # ACT
        service = gmail_api_service.get_g_service_client_from_token(
            str(token_path), str(creds_path), app_config.SCOPES
        )
    
    # ASSERT
    mock_creds_instance.refresh.assert_called_once()
    # Check that the token file was opened for writing
    mocked_token_save.assert_called_once_with(token_path, 'w')
    # Check that the new token data was written
    mocked_token_save().write.assert_called_once_with('{"refreshed": "new_token_data"}')
    
    mock_google_build[0].assert_called_once_with('gmail', 'v1', credentials=mock_creds_instance)
    assert service == mock_google_build[1]


def test_get_g_service_client_from_token_no_token_file(mock_credentials_class, tmp_path):
    # ARRANGE
    token_path = tmp_path / "nonexistent_token.json"  # Does not exist
    creds_path = tmp_path / "test_creds.json"
    creds_path.touch()  # Ensure this one exists
    
    # ACT & ASSERT
    with pytest.raises(DamienError, match="Token file not found"):
        gmail_api_service.get_g_service_client_from_token(
            str(token_path), str(creds_path), app_config.SCOPES
        )
    
    mock_credentials_class.from_authorized_user_file.assert_not_called()


def test_get_g_service_client_from_token_refresh_failure(mock_credentials_class, tmp_path):
    # ARRANGE
    token_path = tmp_path / "test_token.json"
    creds_path = tmp_path / "test_creds.json"
    token_path.touch()
    creds_path.touch()
    
    mock_creds_instance = MagicMock(spec=Credentials)
    mock_creds_instance.valid = False
    mock_creds_instance.expired = True
    mock_creds_instance.refresh_token = "a_refresh_token"
    # Simulate refresh failure
    mock_creds_instance.refresh.side_effect = Exception("Refresh failed")
    
    mock_credentials_class.from_authorized_user_file.return_value = mock_creds_instance
    
    # ACT & ASSERT
    with pytest.raises(DamienError, match="Token refresh failed"):
        gmail_api_service.get_g_service_client_from_token(
            str(token_path), str(creds_path), app_config.SCOPES
        )
    
    mock_creds_instance.refresh.assert_called_once()


def test_get_g_service_client_from_token_invalid_token_no_refresh(mock_credentials_class, tmp_path):
    # ARRANGE
    token_path = tmp_path / "test_token.json"
    creds_path = tmp_path / "test_creds.json"
    token_path.touch()
    creds_path.touch()
    
    mock_creds_instance = MagicMock(spec=Credentials)
    mock_creds_instance.valid = False
    mock_creds_instance.expired = False  # Not expired
    mock_creds_instance.refresh_token = None  # No refresh token
    
    mock_credentials_class.from_authorized_user_file.return_value = mock_creds_instance
    
    # ACT & ASSERT
    with pytest.raises(DamienError, match="Token from .* is invalid and cannot be refreshed"):
        gmail_api_service.get_g_service_client_from_token(
            str(token_path), str(creds_path), app_config.SCOPES
        )


def test_get_g_service_client_from_token_build_api_error(mock_credentials_class, tmp_path):
    # ARRANGE
    token_path = tmp_path / "test_token.json"
    creds_path = tmp_path / "test_creds.json"
    token_path.touch()
    creds_path.touch()
    
    mock_creds_instance = MagicMock(spec=Credentials)
    mock_creds_instance.valid = True
    mock_credentials_class.from_authorized_user_file.return_value = mock_creds_instance
    
    # Mock build to raise an HttpError
    api_error = HttpError(resp=MagicMock(status=401), content=b"Unauthorized")
    with patch('damien_cli.core_api.gmail_api_service.build', side_effect=api_error):
        # ACT & ASSERT
        with pytest.raises(GmailApiError, match="API error building Gmail service: 401"):
            gmail_api_service.get_g_service_client_from_token(
                str(token_path), str(creds_path), app_config.SCOPES
            )
