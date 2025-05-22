import pytest
import json
import click # Ensure click is imported
from click.testing import CliRunner
from unittest.mock import patch, MagicMock # Removed call

from damien_cli import cli_entry
from damien_cli.core_api.exceptions import (
    GmailApiError,
    InvalidParameterError,
)  # For simulating errors

# Mock data remains the same
MOCK_MESSAGE_STUBS_PAGE1 = {
    "messages": [{"id": "111", "threadId": "aaa"}, {"id": "222", "threadId": "bbb"}],
    "nextPageToken": "page2_token",
}
MOCK_MESSAGE_STUBS_EMPTY = {"messages": [], "nextPageToken": None}
MOCK_MESSAGE_DETAIL_111 = {
    "id": "111",
    "threadId": "aaa",
    "snippet": "Hello from 111",
    "payload": {
        "headers": [
            {"name": "Subject", "value": "Test Subject 1"},
            {"name": "From", "value": "sender1@example.com"},
            {"name": "Date", "value": "Some Date 1"},
        ]
    },
}


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_gmail_service_in_context():  # This represents the raw Google API client resource
    return MagicMock(name="MockedRawGoogleServiceClient")


@pytest.fixture(autouse=True)
def mock_logging_setup_for_cli_tests():
    with patch("damien_cli.cli_entry.setup_logging") as mock_setup:
        mock_logger = MagicMock(name="MockLoggerFromCLIEntry")
        mock_setup.return_value = mock_logger
        # The nested patch below was causing the AttributeError and is not needed
        # if commands correctly get the logger from ctx.obj.
        yield mock_logger


# --- Tests for Read Commands ---
@patch("damien_cli.core_api.gmail_api_service.get_message_details")
@patch("damien_cli.core_api.gmail_api_service.list_messages")
def test_emails_list_human_output(
    mock_api_list_messages,
    mock_api_get_details,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_api_list_messages.return_value = MOCK_MESSAGE_STUBS_PAGE1

    def side_effect_get_details(service_client, msg_id, email_format):
        assert (
            service_client == mock_gmail_service_in_context
        )  # Ensure correct service passed
        if msg_id == "111":
            return MOCK_MESSAGE_DETAIL_111
        if msg_id == "222":
            return (
                MOCK_MESSAGE_DETAIL_111  # Using same detail for simplicity for stub 2
            )
        return None

    mock_api_get_details.side_effect = side_effect_get_details

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "list"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    mock_api_list_messages.assert_called_once_with(
        mock_gmail_service_in_context,
        query_string=None,
        max_results=10,
        page_token=None,
    )
    assert mock_api_get_details.call_count == 2
    assert "ID: 111" in result.output
    assert 'To see more, use --page-token "page2_token"' in result.output


@patch("damien_cli.core_api.gmail_api_service.get_message_details")
@patch("damien_cli.core_api.gmail_api_service.list_messages")
def test_emails_list_json_output(
    mock_api_list_messages,
    mock_api_get_details,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_api_list_messages.return_value = MOCK_MESSAGE_STUBS_PAGE1

    def side_effect_get_details(service_client, msg_id, email_format):
        if msg_id == "111":
            return MOCK_MESSAGE_DETAIL_111
        if msg_id == "222":
            return (
                MOCK_MESSAGE_DETAIL_111  # Using same detail for simplicity for stub 2
            )
        return None

    mock_api_get_details.side_effect = side_effect_get_details

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "list", "--output-format", "json"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    assert mock_api_get_details.call_count == 2
    try:
        full_response_obj = json.loads(result.output)
        assert full_response_obj["status"] == "success"
        assert "data" in full_response_obj
        data_payload = full_response_obj["data"]
        assert len(data_payload["messages"]) == 2
        assert data_payload["messages"][0]["id"] == "111"
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to decode JSON: {e}\nOutput was:\n{result.output}")


@patch("damien_cli.core_api.gmail_api_service.list_messages")
def test_emails_list_no_results_human(
    mock_api_list_messages,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_api_list_messages.return_value = MOCK_MESSAGE_STUBS_EMPTY
    result = runner.invoke(
        cli_entry.damien,
        ["emails", "list"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )
    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    assert "No emails found." in result.output  # Adjusted message for no query


@patch("damien_cli.core_api.gmail_api_service.get_message_details")
def test_emails_get_human_output(
    mock_api_get_details,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_api_get_details.return_value = MOCK_MESSAGE_DETAIL_111
    result = runner.invoke(
        cli_entry.damien,
        ["emails", "get", "--id", "111", "--format", "full"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )
    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    mock_api_get_details.assert_called_once_with(
        mock_gmail_service_in_context, "111", email_format="full"
    )
    assert "Details for Email ID: 111" in result.output


@patch("damien_cli.core_api.gmail_api_service.get_message_details")
def test_emails_get_json_output(
    mock_api_get_details,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_api_get_details.return_value = MOCK_MESSAGE_DETAIL_111

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "get", "--id", "111", "--output-format", "json"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )
    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    try:
        full_response_obj = json.loads(result.output)
        assert full_response_obj["status"] == "success"
        assert "data" in full_response_obj
        output_data = full_response_obj["data"]
        assert output_data["id"] == "111"
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to decode JSON: {e}\nOutput was:\n{result.output}")


@patch("damien_cli.core_api.gmail_api_service.get_message_details")
def test_emails_get_not_found_human(
    mock_api_get_details,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    # Simulate API raising an error for not found
    mock_api_get_details.side_effect = GmailApiError(
        "Message with ID ghost_id not found.",
        original_exception=Exception("Simulated 404"),
    )

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "get", "--id", "ghost_id"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 1
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    assert (
        "Error during 'damien emails get': Message with ID ghost_id not found."
        in result.output
    )


# --- NEW TESTS for Phase 2 Write Commands ---
# Note: For commands using the new _confirm_action, we'll patch that instead of click.confirm directly.
@patch("damien_cli.features.email_management.commands._confirm_action") # Corrected patch target
@patch("damien_cli.core_api.gmail_api_service.batch_trash_messages")
def test_emails_trash_cmd_dry_run(
    mock_api_batch_trash,
    mock_shared_confirm_action, # Updated mock name
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    result = runner.invoke(
        cli_entry.damien,
        ["emails", "trash", "--ids", "id1,id2", "--dry-run"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )
    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    assert (
        "DRY RUN: 2 email(s) would be moved to Trash. No actual changes made."
        in result.output
    )
    mock_api_batch_trash.assert_not_called()
    mock_shared_confirm_action.assert_not_called() # _confirm_action is not called in dry_run


@patch("damien_cli.features.email_management.commands._confirm_action") # Corrected patch target
@patch("damien_cli.core_api.gmail_api_service.batch_trash_messages")
def test_emails_trash_cmd_confirmed_interactively( # Renamed for clarity
    mock_api_batch_trash,
    mock_shared_confirm_action, # Updated mock name
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_shared_confirm_action.return_value = (True, "") # Simulate user saying yes, no specific msg from util
    # mock_api_batch_trash.return_value = True # API returns None

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "trash", "--ids", "id1,id2"], # No --yes flag
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    mock_shared_confirm_action.assert_called_once_with(
        prompt_message="Are you sure you want to move these 2 email(s) to Trash?",
        yes_flag=False # Explicitly False as --yes was not used
    )
    mock_api_batch_trash.assert_called_once_with(
        mock_gmail_service_in_context, ["id1", "id2"]
    )
    assert "Successfully moved 2 email(s) to Trash." in result.output


@patch("damien_cli.features.email_management.commands._confirm_action") # Corrected patch target
@patch("damien_cli.core_api.gmail_api_service.batch_trash_messages")
def test_emails_trash_cmd_aborted_interactively( # Renamed for clarity
    mock_api_batch_trash,
    mock_shared_confirm_action, # Updated mock name
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_shared_confirm_action.return_value = (False, "Action aborted by user.") # Simulate user saying no
    # The command will echo the "Action aborted by user." message.
    result = runner.invoke(
        cli_entry.damien,
        ["emails", "trash", "--ids", "id1"], # No --yes flag
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    mock_shared_confirm_action.assert_called_once_with(
        prompt_message="Are you sure you want to move these 1 email(s) to Trash?",
        yes_flag=False # Explicitly False
    )
    mock_api_batch_trash.assert_not_called()
    assert "Action aborted by user." in result.output # This message is now echoed by the command


@patch("damien_cli.features.email_management.commands._confirm_action") # Corrected patch target
@patch("damien_cli.core_api.gmail_api_service.batch_trash_messages")
def test_emails_trash_cmd_with_yes_flag(
    mock_api_batch_trash,
    mock_shared_confirm_action, # Updated mock name
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    # When yes_flag is True, _confirm_action returns (True, "Confirmation bypassed...")
    # The test will assert that this message is part of the output.
    # We don't need to set mock_shared_confirm_action.return_value here if we are asserting its call_args.
    # However, to ensure the command proceeds, the mock should reflect what the real function does.
    # The real _confirm_action returns (True, bypass_message) when yes_flag is True.
    # Let's make the mock behave similarly for this specific test path.
    mock_shared_confirm_action.return_value = (True, "Confirmation bypassed by --yes flag for: Are you sure you want to move these 2 email(s) to Trash?")


    result = runner.invoke(
        cli_entry.damien,
        ["emails", "trash", "--ids", "id1,id2", "--yes"], # --yes flag is present
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert result.exit_code == 0, f"Output: {result.output}"
    mock_shared_confirm_action.assert_called_once_with(
        prompt_message="Are you sure you want to move these 2 email(s) to Trash?",
        yes_flag=True # Crucial: assert it was called with yes_flag=True
    )
    mock_api_batch_trash.assert_called_once_with(
        mock_gmail_service_in_context, ["id1", "id2"]
    )
    assert "Confirmation bypassed by --yes flag for: Are you sure you want to move these 2 email(s) to Trash?" in result.output
    assert "Successfully moved 2 email(s) to Trash." in result.output


# Tests for 'damien emails delete'
@patch("damien_cli.features.email_management.commands.click.prompt") # Still need for YESIDO
@patch("damien_cli.features.email_management.commands._confirm_action") # Corrected patch target
@patch("damien_cli.core_api.gmail_api_service.batch_delete_permanently")
def test_emails_delete_cmd_confirmed_interactively( # Renamed
    mock_api_batch_delete,
    mock_shared_confirm_action, # Updated mock name
    mock_click_prompt,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    # _confirm_action is called twice. It needs to return (True, "") for both.
    mock_shared_confirm_action.return_value = (True, "")
    mock_click_prompt.return_value = "YESIDO"
    # mock_api_batch_delete.return_value = True # API returns None

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "delete", "--ids", "id_perm_del"], # No --yes flag
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    # Check calls to the shared _confirm_action
    assert mock_shared_confirm_action.call_count == 2
    mock_shared_confirm_action.assert_any_call(
        prompt_message="Are you absolutely sure you want to PERMANENTLY DELETE these 1 email(s)? This is IRREVERSIBLE.",
        yes_flag=False
    )
    mock_shared_confirm_action.assert_any_call(
        prompt_message=click.style("FINAL WARNING: All checks passed. Confirm PERMANENT DELETION of these emails?", fg="red", bold=True),
        yes_flag=False,
        default_abort_message="Permanent deletion aborted at final warning." # Corrected parameter name
    )
    mock_click_prompt.assert_called_once() # YESIDO prompt
    mock_api_batch_delete.assert_called_once_with(
        mock_gmail_service_in_context, ["id_perm_del"]
    )
    assert "Successfully PERMANENTLY DELETED 1 email(s)." in result.output


@patch("damien_cli.features.email_management.commands.click.prompt") # Still need for YESIDO
@patch("damien_cli.features.email_management.commands._confirm_action") # Corrected patch target
@patch("damien_cli.core_api.gmail_api_service.batch_delete_permanently")
def test_emails_delete_cmd_abort_at_type_yesido_interactively( # Renamed
    mock_api_batch_delete,
    mock_shared_confirm_action, # Updated mock name
    mock_click_prompt,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_shared_confirm_action.return_value = (True, "") # First _confirm_action passes
    mock_click_prompt.return_value = "NOPE" # User types NOPE for YESIDO

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "delete", "--ids", "id_perm_del"], # No --yes flag
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 0 # Command itself doesn't error, user aborted
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    mock_shared_confirm_action.assert_called_once_with( # Only the first _confirm_action is called
        prompt_message="Are you absolutely sure you want to PERMANENTLY DELETE these 1 email(s)? This is IRREVERSIBLE.",
        yes_flag=False
    )
    mock_click_prompt.assert_called_once()
    mock_api_batch_delete.assert_not_called()
    assert (
        "Confirmation text did not match. Permanent deletion aborted." in result.output # This is echoed by the command
    )


@patch("damien_cli.features.email_management.commands.click.prompt") # click.prompt for YESIDO is not used if --yes
@patch("damien_cli.features.email_management.commands._confirm_action") # Corrected patch target
@patch("damien_cli.core_api.gmail_api_service.batch_delete_permanently")
def test_emails_delete_cmd_with_yes_flag(
    mock_api_batch_delete,
    mock_shared_confirm_action, # Updated mock name
    mock_click_prompt, # Will assert this is NOT called
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    # When yes_flag is True, _confirm_action returns (True, "Confirmation bypassed...")
    # The command will call it twice.
    # We can use side_effect if different bypass messages are critical to distinguish,
    # or a single tuple if the message content isn't part of this specific mock's check.
    # For simplicity, let's assume the command logic handles echoing the correct bypass messages.
    # The key is that _confirm_action returns True as the first element of the tuple.
    mock_shared_confirm_action.return_value = (True, "Confirmation bypassed by --yes flag for: some prompt")


    result = runner.invoke(
        cli_entry.damien,
        ["emails", "delete", "--ids", "id_perm_del", "--yes"], # --yes flag is present
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert result.exit_code == 0, f"Output: {result.output}"
    # _confirm_action should be called twice (for the two main confirmations)
    assert mock_shared_confirm_action.call_count == 2
    mock_shared_confirm_action.assert_any_call(
        prompt_message="Are you absolutely sure you want to PERMANENTLY DELETE these 1 email(s)? This is IRREVERSIBLE.",
        yes_flag=True
    )
    mock_shared_confirm_action.assert_any_call(
        prompt_message=click.style("FINAL WARNING: All checks passed. Confirm PERMANENT DELETION of these emails?", fg="red", bold=True),
        yes_flag=True,
        default_abort_message="Permanent deletion aborted at final warning." # Corrected parameter name
    )
    
    mock_click_prompt.assert_not_called() # YESIDO prompt should be skipped

    mock_api_batch_delete.assert_called_once_with(
        mock_gmail_service_in_context, ["id_perm_del"]
    )
    assert "Successfully PERMANENTLY DELETED 1 email(s)." in result.output
    # Check if the generic bypass message (from the mock's return_value) is present.
    # Since _confirm_action is called twice, this message (or parts of it) should appear.
    # The command itself echoes the message part of the tuple returned by _confirm_action.
    assert "Confirmation bypassed by --yes flag for: some prompt" in result.output
    assert "Confirmation 'YESIDO' bypassed by --yes flag." in result.output # This is echoed directly by the command


# Tests for 'damien emails label'
@patch("damien_cli.core_api.gmail_api_service.batch_modify_message_labels")
def test_emails_label_cmd_add_label(
    mock_api_batch_modify,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    # mock_api_batch_modify.return_value = True # API returns None on success

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "label", "--ids", "id1", "--add-labels", "NewLabel,TRASH"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    mock_api_batch_modify.assert_called_once_with(
        mock_gmail_service_in_context,
        ["id1"],
        add_label_names=["NewLabel", "TRASH"],
        remove_label_names=[],  # Explicitly check for empty list if that's the default
    )
    assert "Successfully applied label changes" in result.output


# Tests for 'damien emails mark'
@patch("damien_cli.core_api.gmail_api_service.batch_mark_messages")
def test_emails_mark_cmd_read(
    mock_api_batch_mark,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    # mock_api_batch_mark.return_value = True # API returns None or raises

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "mark", "--ids", "id1,id2", "--action", "read"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 0
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    mock_api_batch_mark.assert_called_once_with(
        mock_gmail_service_in_context, ["id1", "id2"], mark_as="read"
    )
    assert "Successfully marked 2 email(s) as read." in result.output


# Example tests for API error handling by CLI commands
@patch("damien_cli.features.email_management.commands.click.confirm")
@patch("damien_cli.core_api.gmail_api_service.batch_trash_messages")
def test_emails_trash_cmd_api_error(
    mock_api_batch_trash,
    mock_click_confirm,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_click_confirm.return_value = True  # User confirms
    mock_api_batch_trash.side_effect = GmailApiError(
        "API error trashing", original_exception=Exception("Original")
    )

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "trash", "--ids", "id1,id2", "--output-format", "human"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 1
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    mock_api_batch_trash.assert_called_once_with(
        mock_gmail_service_in_context, ["id1", "id2"]
    )
    assert "Error during 'damien emails trash': API error trashing" in result.output


@patch("damien_cli.features.email_management.commands.click.confirm")
@patch("damien_cli.core_api.gmail_api_service.batch_trash_messages")
def test_emails_trash_cmd_invalid_param_error_from_api(
    mock_api_batch_trash,
    mock_click_confirm,
    runner,
    mock_gmail_service_in_context,
    mock_logging_setup_for_cli_tests,
):
    mock_click_confirm.return_value = True  # User confirms
    mock_api_batch_trash.side_effect = InvalidParameterError("Invalid ID from API")

    result = runner.invoke(
        cli_entry.damien,
        ["emails", "trash", "--ids", "invalid_id_for_api"],
        obj={
            "logger": mock_logging_setup_for_cli_tests,
            "gmail_service": mock_gmail_service_in_context,
        },
    )

    assert (
        result.exit_code == 1
    ), f"CLI exited with {result.exit_code}, output: {result.output}"
    assert (
        "Error during 'damien emails trash': Invalid ID from API" in result.output
    )  # Check for the specific message from the exception
