import logging
from pathlib import Path  # Let's use Path
from typing import Optional, List, Dict, Any  # Make sure these are imported
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from damien_cli.core import config as app_config  # For paths and SCOPES
from .exceptions import (
    GmailApiError,
    InvalidParameterError,
    DamienError,
)  # Your custom exceptions

logger = logging.getLogger(__name__)


# --- Authentication ---
def get_authenticated_service(interactive_auth_ok: bool = True):
    """
    Authenticates with Gmail using OAuth 2.0 and returns a service object.
    Handles token loading, refreshing, and the initial OAuth flow if necessary.

    Args:
        interactive_auth_ok (bool): If False and interactive authentication (e.g., browser)
                                   would be required, returns None instead of starting it.
                                   Defaults to True.

    Returns:
        Optional[googleapiclient.discovery.Resource]: The Gmail service object, or None
                                                     if authentication fails or non-interactive
                                                     auth is requested but not possible.
    """
    creds = None
    token_file_path = Path(
        app_config.TOKEN_FILE
    )  # Ensure TOKEN_FILE is a Path object or string
    credentials_file_path = Path(app_config.CREDENTIALS_FILE)

    if token_file_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(token_file_path), app_config.SCOPES
            )
        except Exception as e:  # Catch potential errors loading token file
            logger.warning(
                f"Could not load token from {token_file_path}: {e}. Will attempt re-authentication."
            )
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Gmail access token is expired. Attempting to refresh.")
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(
                    f"Failed to refresh Gmail token: {e}. Re-authentication required.",
                    exc_info=True,
                )
                creds = None  # Force re-login by nullifying creds

        if not creds:  # If still no valid creds, need to run the flow
            if not interactive_auth_ok:
                logger.info(
                    "Non-interactive authentication requested, but interactive flow would be required. Returning None."
                )
                return None  # Non-interactive mode and requires browser flow

            logger.info("No valid Gmail credentials found. Starting OAuth flow.")
            if not credentials_file_path.exists():
                err_msg = f"Credentials file not found at {credentials_file_path}. Cannot authenticate."
                logger.error(err_msg)
                raise DamienError(
                    err_msg
                    + " Please ensure 'credentials.json' is present and run login."
                )
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_file_path), app_config.SCOPES
                )
                logger.info("OAuth flow will require user interaction (browser).")
                creds = flow.run_local_server(
                    port=0,
                    prompt="consent",
                    authorization_prompt_message="DamienCLI needs to authorize Gmail access. Please follow browser instructions.",
                )
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}", exc_info=True)
                raise DamienError(f"OAuth authorization failed: {e}")

        # Save the credentials for the next run (if obtained/refreshed)
        if (
            creds
        ):  # Only try to save if creds exist (e.g. interactive flow was successful)
            try:
                with open(token_file_path, "w") as token_file_handle:
                    token_file_handle.write(creds.to_json())
                logger.info(
                    f"Gmail access token stored successfully at: {token_file_path}"
                )
            except IOError as e:
                logger.error(
                    f"Failed to save token file at {token_file_path}: {e}",
                    exc_info=True,
                )
                # Non-fatal if creds object is still valid in memory for this session

    if not creds:  # Could happen if non-interactive and no valid token/refresh
        logger.warning("Failed to obtain valid Gmail credentials.")
        return None  # Explicitly return None if creds are still not available

    try:
        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API service built successfully.")
        return service
    except HttpError as error:
        logger.error(
            f"API error building Gmail service: {error.resp.status} - {error.content}",
            exc_info=True,
        )
        raise GmailApiError(
            f"API error building Gmail service: {error.resp.status}",
            original_exception=error,
        )
    except Exception as e:
        logger.error(f"Unexpected error building Gmail service: {e}", exc_info=True)
        raise DamienError(f"Unexpected error building Gmail service: {e}")


def get_g_service_client_from_token(
    token_file_path_str: str,
    credentials_file_path_str: str,  # Needed for robust refresh
    scopes: List[str]
) -> Any:  # Returns the Google API client resource 'Any' or raises error
    """
    Gets an authenticated Gmail API service client non-interactively using stored tokens.
    Refreshes the token if expired and possible. Saves refreshed token.
    Raises DamienError or GmailApiError if authentication fails.
    
    Args:
        token_file_path_str (str): Path to the token.json file
        credentials_file_path_str (str): Path to credentials.json file (needed for refresh)
        scopes (List[str]): OAuth scopes required for authentication
        
    Returns:
        Any: The Gmail service object
        
    Raises:
        DamienError: If token file is missing, invalid, or refresh fails
        GmailApiError: If API errors occur during service build
    """
    logger.debug(f"Attempting to get Gmail service client from token file: {token_file_path_str}")
    token_file = Path(token_file_path_str)
    creds_file = Path(credentials_file_path_str)  # For refresh context
    
    if not token_file.exists():
        msg = f"Token file not found at {token_file}. Please ensure Damien CLI has been logged in."
        logger.error(msg)
        raise DamienError(msg)
    
    creds: Optional[Credentials] = None
    try:
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
    except Exception as e:
        logger.error(f"Failed to load credentials from token file {token_file}: {e}", exc_info=True)
        raise DamienError(f"Could not load token from {token_file}: {e}", original_exception=e)
    
    if not creds:  # Should be caught by above, but as a safeguard
        raise DamienError(f"Unknown error loading credentials from {token_file}.")
    
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            logger.info(f"Access token from {token_file} is expired. Attempting refresh.")
            if not creds_file.exists():  # Check for credentials.json needed for robust refresh
                msg = f"Credentials file ({creds_file}) not found, which may be needed for token refresh."
                logger.warning(msg)
                # Depending on the grant type, refresh might still work without it if refresh_token is powerful enough.
                # But for some OAuth client types, client_secret from credentials.json is needed.
            
            try:
                # The google-auth library's refresh mechanism will try to use client secrets
                # from credentials if the flow was originally an installed app flow.
                # We pass the credentials_file to from_client_secrets_file in InstalledAppFlow,
                # so the refresh token should be associated with that client_id/secret.
                creds.refresh(Request())  # Request() is a transport adapter
                logger.info(f"Access token refreshed successfully using token from {token_file}.")
                
                try:
                    with open(token_file, 'w') as tf:
                        tf.write(creds.to_json())
                    logger.info(f"Refreshed token saved to {token_file}.")
                except IOError as e_io:
                    logger.error(f"Failed to save refreshed token to {token_file}: {e_io}", exc_info=True)
                    # Continue with in-memory refreshed token, but log error
            except Exception as e_refresh:  # Catch specific refresh errors if possible
                logger.error(f"Failed to refresh access token from {token_file}: {e_refresh}", exc_info=True)
                raise DamienError(
                    f"Token refresh failed for {token_file}. Re-authentication via CLI 'damien login' may be required.",
                    original_exception=e_refresh
                )
        else:
            msg = f"Token from {token_file} is invalid and cannot be refreshed (expired: {creds.expired}, has_refresh: {bool(creds.refresh_token)})."
            logger.error(msg)
            raise DamienError(msg + " Re-authentication via CLI 'damien login' may be required.")
    
    # At this point, creds should be valid
    if not creds.valid:  # Final check
        raise DamienError(f"Failed to obtain valid credentials from {token_file} even after refresh attempt.")
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        logger.debug(f"Gmail API service client built successfully using token from {token_file}.")
        return service
    except HttpError as error:
        logger.error(f"API error building Gmail service with token from {token_file}: {error.resp.status} - {error.content}", exc_info=True)
        raise GmailApiError(f"API error building Gmail service: {error.resp.status}", original_exception=error)
    except Exception as e:
        logger.error(f"Unexpected error building Gmail service with token from {token_file}: {e}", exc_info=True)
        raise DamienError(f"Unexpected error building Gmail service: {e}")


# --- Label Operations ---
_label_name_to_id_cache: Dict[str, str] = {}
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


def _clear_label_cache_for_testing():
    """ONLY FOR TESTING: Clears the internal label cache."""
    _label_name_to_id_cache.clear()

def _populate_label_cache(service: Any):
    """Helper to fetch and populate the label cache. Stores name->id, id->id, and id->name."""
    if not service:
        raise InvalidParameterError(
            "Gmail service not available for populating label cache."
        )

    try:
        logger.debug("Populating Gmail label cache...")
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        
        current_cache = _label_name_to_id_cache.copy()  # Preserve existing entries if any
        _label_name_to_id_cache.clear()  # Clear before repopulating for a full refresh
        for lbl in labels:
            _label_name_to_id_cache[lbl["name"].lower()] = lbl["id"]  # For name lookup (name -> id)
            _label_name_to_id_cache[lbl["id"]] = lbl["id"]  # For ID passthrough (id -> id)
            _label_name_to_id_cache[f"name_for_{lbl['id']}"] = lbl["name"]  # For ID to Name lookup (id -> name)
        
        logger.debug(
            f"Label cache populated. New size: {len(_label_name_to_id_cache)} entries."
        )
    except HttpError as e:
        logger.error(
            f"API error fetching labels for cache: {e.resp.status} - {e.content}",
            exc_info=True,
        )
        raise GmailApiError(
            f"API error fetching labels: {e.resp.status}", original_exception=e
        )


def get_label_id(service: Any, label_name_or_id: str) -> Optional[str]:
    """Gets the ID of a label given its name or confirms an ID. Caches results."""
    if not service:
        # This path should ideally not be hit if service is always checked by caller
        logger.error("get_label_id called with no service.")
        raise InvalidParameterError("Gmail service not available for get_label_id.")
    if not label_name_or_id:
        raise InvalidParameterError("Label name or ID cannot be empty.")
    
    label_name_or_id_upper = label_name_or_id.upper()
    if label_name_or_id_upper in _system_labels:
        return label_name_or_id_upper
    
    if not _label_name_to_id_cache: 
        _populate_label_cache(service)
    
    # Check 1: Direct match (could be an ID or a case-sensitive name that's already an ID)
    if label_name_or_id in _label_name_to_id_cache:
        return _label_name_to_id_cache[label_name_or_id] 
    
    # Check 2: Case-insensitive name lookup
    found_id = _label_name_to_id_cache.get(label_name_or_id.lower())
    
    if not found_id: 
        logger.warning(f"Label '{label_name_or_id}' not found in cache after initial population. Forcing refresh.")
        _populate_label_cache(service) 
        
        if label_name_or_id in _label_name_to_id_cache: # Re-check direct
            return _label_name_to_id_cache[label_name_or_id]
        found_id = _label_name_to_id_cache.get(label_name_or_id.lower()) # Re-check lowercase
        
        if not found_id:
            logger.warning(f"Label '{label_name_or_id}' still not found after cache refresh.")
            return None
    return found_id


def get_label_name_from_id(service: Any, label_id: str) -> Optional[str]:
    """Gets the display name of a label given its ID. Caches results."""
    if not service:
        raise InvalidParameterError("Gmail service not available for get_label_name_from_id.")
    if not label_id:
        raise InvalidParameterError("Label ID cannot be empty for get_label_name_from_id.")
    
    label_id_upper = label_id.upper()
    if label_id_upper in _system_labels: # System labels use their name as ID
        return label_id_upper
    
    cache_key_for_name = f"name_for_{label_id}"
    if not _label_name_to_id_cache or cache_key_for_name not in _label_name_to_id_cache: 
        _populate_label_cache(service) # Populate if cache is empty or specific ID->name mapping missing
    
    found_name = _label_name_to_id_cache.get(cache_key_for_name)
    if not found_name:
        logger.warning(f"Label name for ID '{label_id}' not found in cache even after populating. Forcing refresh.")
        _populate_label_cache(service) # Try one more time
        found_name = _label_name_to_id_cache.get(cache_key_for_name)
        if not found_name:
            logger.warning(f"Label name for ID '{label_id}' still not found after cache refresh.")
            return None # Or return the ID itself if a name can't be found? Or raise error?
    return found_name


# --- Message Read Operations ---
def list_messages(
    service: Any,
    query_string: Optional[str] = None,
    max_results: int = 100,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Lists messages matching the query. Returns dict with 'messages' and 'nextPageToken'."""
    if not service:
        raise InvalidParameterError("Gmail service not available for list_messages.")

    try:
        list_params: Dict[str, Any] = {"userId": "me", "maxResults": max_results}
        if query_string:
            list_params["q"] = query_string
        if page_token:
            list_params["pageToken"] = page_token

        logger.debug(f"API: Listing messages with params: {list_params}")
        results = service.users().messages().list(**list_params).execute()
        return {
            "messages": results.get("messages", []),
            "nextPageToken": results.get("nextPageToken"),
        }
    except HttpError as error:
        logger.error(
            f"API error listing messages: {error.resp.status} - {error.content}",
            exc_info=True,
        )
        raise GmailApiError(
            f"API error listing messages: {error.resp.status}", original_exception=error
        )
    except Exception as e:
        logger.error(f"Unexpected error listing messages: {e}", exc_info=True)
        raise DamienError(f"Unexpected error listing messages: {e}")


def get_message_details(
    service: Any, message_id: str, email_format: str = "metadata"
) -> Dict[str, Any]:
    """Gets a specific message by its ID."""
    if not service:
        raise InvalidParameterError(
            "Gmail service not available for get_message_details."
        )
    if not message_id:
        raise InvalidParameterError("Message ID cannot be empty.")

    valid_formats = ["full", "metadata", "raw"]
    actual_format = email_format.lower()
    if actual_format not in valid_formats:
        logger.warning(
            f"Invalid email_format '{email_format}' for get_message_details. Defaulting to 'metadata'."
        )
        actual_format = "metadata"

    try:
        logger.debug(
            f"API: Getting message details for ID: {message_id}, Format: {actual_format}"
        )
        message = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format=actual_format)
            .execute()
        )
        return message
    except HttpError as error:
        logger.error(
            f"API error getting message (ID: {message_id}): {error.resp.status} - {error.content}",
            exc_info=True,
        )
        raise GmailApiError(
            f"API error getting message (ID: {message_id}): {error.resp.status}",
            original_exception=error,
        )
    except Exception as e:
        logger.error(
            f"Unexpected error getting message (ID: {message_id}): {e}", exc_info=True
        )
        raise DamienError(f"Unexpected error getting message (ID: {message_id}): {e}")


# --- Message Write Operations ---
def batch_modify_message_labels(
    service: Any,
    message_ids: List[str],
    add_label_names: Optional[List[str]] = None,
    remove_label_names: Optional[List[str]] = None,
) -> bool:
    """Modifies labels on a batch of messages. Translates label names to IDs."""
    if not service:
        raise InvalidParameterError(
            "Gmail service not available for batch_modify_message_labels."
        )
    if not message_ids:
        logger.debug(
            "batch_modify_message_labels called with no message_ids. No action taken."
        )
        return True

    actual_add_label_ids: List[str] = []
    if add_label_names:
        for name in add_label_names:
            label_id = get_label_id(
                service, name
            )  # get_label_id now raises InvalidParameterError if service is None
            if label_id:
                actual_add_label_ids.append(label_id)
            else:
                logger.warning(f"Label name '{name}' not found, skipping for 'add'.")

    actual_remove_label_ids: List[str] = []
    if remove_label_names:
        for name in remove_label_names:
            label_id = get_label_id(service, name)
            if label_id:
                actual_remove_label_ids.append(label_id)
            else:
                logger.warning(f"Label name '{name}' not found, skipping for 'remove'.")

    body: Dict[str, Any] = {}
    if actual_add_label_ids:
        body["addLabelIds"] = actual_add_label_ids
    if actual_remove_label_ids:
        body["removeLabelIds"] = actual_remove_label_ids

    if not body:
        logger.info("No valid label changes to apply after name resolution.")
        return True

    body["ids"] = message_ids
    try:
        logger.info(
            f"API: Batch modifying labels for {len(message_ids)} messages. Request body: {body}"
        )
        service.users().messages().batchModify(userId="me", body=body).execute()
        logger.info(
            f"Successfully batch modified labels for {len(message_ids)} messages."
        )
        return True
    except HttpError as error:
        logger.error(
            f"API error during batch label modification: {error.resp.status} - {error.content}",
            exc_info=True,
        )
        raise GmailApiError(
            f"API error during batch label modification: {error.resp.status}",
            original_exception=error,
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during batch label modification: {e}", exc_info=True
        )
        raise DamienError(f"Unexpected error during batch label modification: {e}")


def batch_trash_messages(service: Any, message_ids: List[str]) -> bool:
    """Moves a batch of messages to Trash."""
    logger.info(f"API: Preparing to move {len(message_ids)} messages to Trash.")
    return batch_modify_message_labels(
        service,
        message_ids,
        add_label_names=["TRASH"],
        remove_label_names=["INBOX", "UNREAD"],
    )


def batch_mark_messages(service: Any, message_ids: List[str], mark_as: str) -> bool:
    """Marks a batch of messages as read or unread."""
    if mark_as.lower() == "read":
        logger.info(f"API: Preparing to mark {len(message_ids)} messages as read.")
        return batch_modify_message_labels(
            service, message_ids, remove_label_names=["UNREAD"]
        )
    elif mark_as.lower() == "unread":
        logger.info(f"API: Preparing to mark {len(message_ids)} messages as unread.")
        return batch_modify_message_labels(
            service, message_ids, add_label_names=["UNREAD"]
        )
    else:
        err_msg = f"Invalid mark_as action '{mark_as}'. Use 'read' or 'unread'."
        logger.error(err_msg)
        raise InvalidParameterError(err_msg)


def batch_delete_permanently(service: Any, message_ids: List[str]) -> bool:
    """Permanently deletes a batch of messages."""
    if not service:
        raise InvalidParameterError(
            "Gmail service not available for batch_delete_permanently."
        )
    if not message_ids:
        logger.debug(
            "batch_delete_permanently called with no message_ids. No action taken."
        )
        return True

    body = {"ids": message_ids}
    try:
        logger.warning(
            f"API: PERMANENTLY DELETING {len(message_ids)} messages. Request body: {body}"
        )  # Warning for destructive op
        service.users().messages().batchDelete(userId="me", body=body).execute()
        logger.info(
            f"Successfully batch deleted {len(message_ids)} messages permanently."
        )
        return True
    except HttpError as error:
        logger.error(
            f"API error during batch permanent deletion: {error.resp.status} - {error.content}",
            exc_info=True,
        )
        raise GmailApiError(
            f"API error during batch permanent deletion: {error.resp.status}",
            original_exception=error,
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during batch permanent deletion: {e}", exc_info=True
        )
        raise DamienError(f"Unexpected error during batch permanent deletion: {e}")
