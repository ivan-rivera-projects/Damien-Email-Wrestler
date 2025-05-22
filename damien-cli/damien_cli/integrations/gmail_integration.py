import click
from typing import Optional # Removed List, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from damien_cli.core import config  # Our config file


def get_gmail_service():
    """
    Authenticates with Gmail and returns a service object to interact with the API.
    Handles token loading, refreshing, and the initial OAuth flow.
    """
    creds = None
    if config.TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(config.TOKEN_FILE), config.SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                click.echo("Damien is refreshing your Gmail access token...")
                creds.refresh(Request())
            except Exception as e:
                click.echo(f"Damien couldn't refresh token: {e}. Please log in again.")
                creds = None

        if not creds:
            click.echo(
                "Damien needs to open your web browser to authorize Gmail access."
            )
            click.echo(f"Using credentials from: {config.CREDENTIALS_FILE}")
            if not config.CREDENTIALS_FILE.exists():
                click.echo(
                    f"ERROR: Credentials file not found at {config.CREDENTIALS_FILE}"
                )
                click.echo(
                    "Please ensure 'credentials.json' from Google Cloud is in the project root."
                )
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.CREDENTIALS_FILE), config.SCOPES
            )
            creds = flow.run_local_server(
                port=0,
                prompt="consent",
                authorization_prompt_message="Please authorize Damien-CLI in the browser window that just opened (or will open shortly)...",
            )

        with open(config.TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
        click.echo(f"Damien has stored your access token at: {config.TOKEN_FILE}")

    try:
        service = build("gmail", "v1", credentials=creds)
        # Removed the "successfully connected" echo from here to avoid printing during tests too often
        # click.echo("Damien has successfully connected to your Gmail account!")
        return service
    except HttpError as error:
        click.echo(f"Damien encountered an API error building service: {error}")
        return None
    except Exception as e:
        click.echo(f"Damien encountered an unexpected error building service: {e}")
        return None


_label_name_to_id_cache = {}
_system_labels = [
    "INBOX",
    "SPAM",
    "TRASH",
    "UNREAD",
    "IMPORTANT",
    "STARRED",
    "SENT",
    "DRAFT",
    "CATEGORY_PERSONAL",
    "CATEGORY_SOCIAL",
    "CATEGORY_PROMOTIONS",
    "CATEGORY_UPDATES",
    "CATEGORY_FORUMS",
]


def get_label_id(service, label_name: str) -> Optional[str]:
    """
    Gets the ID of a label given its name.
    Caches results to minimize API calls.
    Returns None if the label name is not found.
    """
    # System labels have their names as IDs (usually uppercase)
    if label_name.upper() in _system_labels:
        return label_name.upper()

    # Check cache first
    if not _label_name_to_id_cache:  # If cache is empty, populate it
        try:
            # click.echo("Damien is fetching user labels to build mapping...") # Potentially noisy
            results = service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            for lbl in labels:
                _label_name_to_id_cache[lbl["name"].lower()] = lbl[
                    "id"
                ]  # Store names lowercase for case-insensitive lookup
                _label_name_to_id_cache[lbl["id"]] = lbl[
                    "id"
                ]  # Also allow passing ID directly
        except HttpError as e:
            click.echo(f"Damien: Error fetching labels: {e}")
            return None  # Cannot resolve if label list fetch fails

    # Lookup in cache
    if (
        label_name in _label_name_to_id_cache
    ):  # Direct lookup first (good for IDs or exact case names)
        return _label_name_to_id_cache[label_name]
    return _label_name_to_id_cache.get(
        label_name.lower()
    )  # Fallback to lowercase lookup for names


def list_labels(service):  # Kept for potential debugging, can be removed if unused
    if not service:
        click.echo("Cannot list labels, Gmail service not available.")
        return
    try:
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        if not labels:
            click.echo("No labels found.")
            return
        click.echo("Labels:")
        for label in labels:
            click.echo(label["name"])
    except HttpError as error:
        click.echo(f"Damien encountered an API error while listing labels: {error}")
    except Exception as e:
        click.echo(f"Damien encountered an unexpected error while listing labels: {e}")


def list_messages(
    service, query_string: str = None, max_results: int = 10, page_token: str = None
):
    if not service:
        click.echo("Damien cannot list messages: Gmail service not available.")
        return None
    try:
        list_params = {"userId": "me", "maxResults": max_results}
        if query_string:
            list_params["q"] = query_string
        if page_token:  # Only add pageToken to params if it has a value
            list_params["pageToken"] = page_token

        # Reduced chattiness for tests, actual user feedback is in commands.py
        # click.echo(f"Damien is fetching emails with query: '{query_string if query_string else 'ALL'}'...")
        results = service.users().messages().list(**list_params).execute()

        messages = results.get("messages", [])
        next_page_token = results.get("nextPageToken")

        # click.echo(f"Damien found {len(messages)} message stubs. Next page token: {next_page_token}")
        return {"messages": messages, "nextPageToken": next_page_token}

    except HttpError as error:
        click.echo(f"Damien encountered an API error while listing messages: {error}")
        return None
    except Exception as e:
        click.echo(
            f"Damien encountered an unexpected error while listing messages: {e}"
        )
        return None


def get_message_details(service, message_id: str, email_format: str = "metadata"):
    if not service:
        click.echo("Damien cannot get message details: Gmail service not available.")
        return None
    try:
        valid_formats = ["full", "metadata", "raw"]
        if email_format.lower() not in valid_formats:
            click.echo(
                f"Damien received an invalid format '{email_format}'. Using 'metadata'."
            )
            email_format = "metadata"

        # click.echo(f"Damien is fetching details for message ID: {message_id} (format: {email_format})...")
        message = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format=email_format)
            .execute()
        )
        return message

    except HttpError as error:
        click.echo(f"Damien encountered an API error getting message details: {error}")
        return None
    except Exception as e:
        click.echo(
            f"Damien encountered an unexpected error getting message details: {e}"
        )
        return None


def batch_modify_message_labels(
    service,
    message_ids: list,
    add_label_names: list = None,
    remove_label_names: list = None,
):  # Renamed params for clarity
    """
    Modifies labels on a batch of messages.
    Translates label names to IDs before calling the API.
    """
    if not service:
        click.echo("Damien cannot modify messages: Gmail service not available.")
        return False
    if not message_ids:
        # click.echo("Damien received no message IDs to modify.") # Less verbose
        return True

    actual_add_label_ids = []
    if add_label_names:
        for name in add_label_names:
            label_id = get_label_id(service, name)
            if label_id:
                actual_add_label_ids.append(label_id)
            else:
                click.echo(
                    f"Damien Warning: Label name '{name}' not found, skipping for 'add'."
                )

    actual_remove_label_ids = []
    if remove_label_names:
        for name in remove_label_names:
            label_id = get_label_id(service, name)
            if label_id:
                actual_remove_label_ids.append(label_id)
            else:
                click.echo(
                    f"Damien Warning: Label name '{name}' not found, skipping for 'remove'."
                )

    body = {}
    if actual_add_label_ids:
        body["addLabelIds"] = actual_add_label_ids
    if actual_remove_label_ids:
        body["removeLabelIds"] = actual_remove_label_ids

    if not body:
        # click.echo("Damien: No valid label changes specified for batch modification.") # Less verbose
        return True  # No valid work to do, not an error

    body["ids"] = message_ids

    try:
        # click.echo(f"Damien is batch modifying labels for {len(message_ids)} messages. API Body: {body}")
        service.users().messages().batchModify(userId="me", body=body).execute()
        return True
    except HttpError as error:
        click.echo(
            f"Damien encountered an API error during batch label modification: {error}"
        )
        return False
    except Exception as e:
        click.echo(
            f"Damien encountered an unexpected error during batch label modification: {e}"
        )
        return False


# Update calls in batch_trash_messages and batch_mark_messages
def batch_trash_messages(service, message_ids: list):
    """
    Moves a batch of messages to Trash.
    This is done by adding 'TRASH' label and removing 'INBOX' (and 'UNREAD' if present).
    """
    click.echo(f"Damien preparing to move {len(message_ids)} messages to Trash.")
    # Standard labels: 'TRASH', 'INBOX', 'UNREAD', 'SPAM'
    # We remove INBOX to ensure it's not in both. Removing UNREAD is also typical.
    return batch_modify_message_labels(
        service,
        message_ids,
        add_label_names=["TRASH"],
        remove_label_names=["INBOX", "UNREAD"],
    )


def batch_mark_messages(service, message_ids: list, mark_as: str):
    """
    Marks a batch of messages as read or unread.
    'UNREAD' is a system label.
    """
    if mark_as.lower() == "read":
        click.echo(f"Damien preparing to mark {len(message_ids)} messages as read.")
        return batch_modify_message_labels(
            service, message_ids, remove_label_names=["UNREAD"]
        )
    elif mark_as.lower() == "unread":
        click.echo(f"Damien preparing to mark {len(message_ids)} messages as unread.")
        return batch_modify_message_labels(
            service, message_ids, add_label_names=["UNREAD"]
        )
    else:
        click.echo(f"Damien: Invalid mark action '{mark_as}'. Use 'read' or 'unread'.")
        return False


def batch_delete_permanently(service, message_ids: list):
    """
    Permanently deletes a batch of messages. This action is irreversible.

    Args:
        service: The authenticated Gmail API service object.
        message_ids: A list of message IDs to permanently delete.

    Returns:
        True if the batch operation was acknowledged, False otherwise.
    """
    if not service:
        click.echo("Damien cannot delete messages: Gmail service not available.")
        return False
    if not message_ids:
        click.echo("Damien received no message IDs to permanently delete.")
        return True

    body = {"ids": message_ids}
    try:
        click.echo(f"Damien is batch DELETING PERMANENTLY {len(message_ids)} messages.")
        service.users().messages().batchDelete(userId="me", body=body).execute()
        # Like batchModify, this returns a 204 No Content on success.
        return True
    except HttpError as error:
        click.echo(
            f"Damien encountered an API error during batch permanent deletion: {error}"
        )
        return False
    except Exception as e:
        click.echo(
            f"Damien encountered an unexpected error during batch permanent deletion: {e}"
        )
        return False
