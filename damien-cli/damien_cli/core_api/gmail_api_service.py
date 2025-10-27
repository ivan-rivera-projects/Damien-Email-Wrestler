from .rate_limiter import with_rate_limiting
from .exceptions import SettingsOperationError, GmailApiError, InvalidParameterError, DamienError
from typing import Dict, Any, Optional, List
import logging
import os
import json
import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

# Global label cache
_label_name_to_id_cache = {}

# Gmail API Scopes - Include specific settings scopes
GMAIL_SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/gmail.settings.sharing'
]

# Authentication Functions
def get_authenticated_service(token_path: str = None, credentials_path: str = None, scopes: List[str] = None):
    """
    Get authenticated Gmail service client.
    
    Args:
        token_path: Path to token.json file
        credentials_path: Path to credentials.json file  
        scopes: List of OAuth scopes
        
    Returns:
        Authenticated Gmail service client
        
    Raises:
        GmailApiError: If authentication fails
    """
    try:
        from damien_cli.core import config as app_config
        
        if scopes is None:
            scopes = app_config.SCOPES
        if token_path is None:
            token_path = str(app_config.TOKEN_FILE)
        if credentials_path is None:
            credentials_path = str(app_config.CREDENTIALS_FILE)
            
        creds = None
        
        # Load existing token if available
        if token_path and os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, scopes)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path or not os.path.exists(credentials_path):
                    raise GmailApiError(f"Credentials file not found at {credentials_path}")
                    
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            if token_path:
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
        
        service = build('gmail', 'v1', credentials=creds)
        return service
        
    except Exception as e:
        logger.error(f"Failed to authenticate Gmail service: {str(e)}")
        raise GmailApiError(f"Failed to authenticate Gmail service: {str(e)}")


def get_g_service_client_from_token(token_path: str = None, credentials_path: str = None, scopes: List[str] = None):
    """
    Get Gmail service client from existing token (non-interactive).
    
    Args:
        token_path: Path to token.json file
        credentials_path: Path to credentials.json file
        scopes: List of OAuth scopes
        
    Returns:
        Authenticated Gmail service client
        
    Raises:
        GmailApiError: If authentication fails or token is invalid
    """
    try:
        from damien_cli.core import config as app_config
        
        if scopes is None:
            scopes = app_config.SCOPES
        if token_path is None:
            token_path = str(app_config.TOKEN_FILE)
        if credentials_path is None:
            credentials_path = str(app_config.CREDENTIALS_FILE)
            
        if not os.path.exists(token_path):
            raise GmailApiError(f"Token file not found at {token_path}")
            
        creds = Credentials.from_authorized_user_file(token_path, scopes)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed token
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    raise GmailApiError(f"Failed to refresh token: {str(e)}")
            else:
                raise GmailApiError("Token is invalid and cannot be refreshed non-interactively")
        
        service = build('gmail', 'v1', credentials=creds)
        return service
        
    except Exception as e:
        logger.error(f"Failed to get Gmail service from token: {str(e)}")
        raise GmailApiError(f"Failed to get Gmail service from token: {str(e)}")


# Label Management Functions
@with_rate_limiting
def _populate_label_cache(gmail_service):
    """
    Populate the label name to ID cache.
    
    Args:
        gmail_service: Authenticated Gmail service client
        
    Raises:
        GmailApiError: If API call fails
    """
    global _label_name_to_id_cache
    
    try:
        logger.debug("Populating label cache")
        
        results = gmail_service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        _label_name_to_id_cache.clear()
        for label in labels:
            # Store label names in lowercase for consistent, case-insensitive lookup
            _label_name_to_id_cache[label['name'].lower()] = label['id']
            # Also store the ID itself as a key, so get_label_id can pass through IDs
            _label_name_to_id_cache[label['id']] = label['id']
            
        logger.info(f"Populated label cache with {len(_label_name_to_id_cache)} entries (name->id and id->id)")
        
    except Exception as e:
        logger.error(f"Failed to populate label cache: {str(e)}")
        raise GmailApiError(f"Failed to populate label cache: {str(e)}")


def get_label_id(gmail_service, label_name: str) -> Optional[str]:
    """
    Get label ID from label name.
    
    Args:
        gmail_service: Authenticated Gmail service client
        label_name: Name of the label
        
    Returns:
        Label ID if found, None otherwise
        
    Raises:
        GmailApiError: If API call fails
    """
    global _label_name_to_id_cache
    
    # System labels have their names as IDs (usually uppercase)
    system_labels = ["INBOX", "SPAM", "TRASH", "UNREAD", "IMPORTANT", "STARRED", "SENT", "DRAFT",
                     "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS"]
    
    # Check if it's a system label (case-insensitive)
    for system_label in system_labels:
        if label_name.upper() == system_label:
            return system_label
    
    # Cache stores names as lowercase and IDs as themselves.
    # First, try direct lookup (could be an ID or already lowercased name)
    if label_name in _label_name_to_id_cache:
        return _label_name_to_id_cache[label_name]

    # Try lowercase version of the input name
    lower_label_name = label_name.lower()
    if lower_label_name in _label_name_to_id_cache:
        return _label_name_to_id_cache[lower_label_name]
    
    # If cache is empty or label not found, populate/refresh and try again
    # The first call to _populate_label_cache will happen if cache is empty.
    # The second call (after this block) acts as a refresh if still not found.
    if not _label_name_to_id_cache:
        logger.debug(f"Label cache empty, populating for '{label_name}'")
        _populate_label_cache(gmail_service)
        # Check again after initial population
        if lower_label_name in _label_name_to_id_cache:
            return _label_name_to_id_cache[lower_label_name]
        if label_name in _label_name_to_id_cache: # Check original name if it was an ID
            return _label_name_to_id_cache[label_name]

    # If still not found, perform a forced refresh and final check
    logger.debug(f"Label '{label_name}' not found in cache, forcing refresh.")
    _populate_label_cache(gmail_service) # This is the second call if not found initially
    
    if lower_label_name in _label_name_to_id_cache:
        return _label_name_to_id_cache[lower_label_name]
    if label_name in _label_name_to_id_cache: # Check original name if it was an ID
            return _label_name_to_id_cache[label_name]
            
    logger.warning(f"Label '{label_name}' not found even after cache refresh.")
    return None

def get_label_name_from_id(gmail_service, label_id: str) -> Optional[str]:
    """
    Get label name from label ID using the cache.
    This is primarily for user display or logging; most API calls use IDs.

    Args:
        gmail_service: Authenticated Gmail service client (used to populate cache if needed)
        label_id: ID of the label

    Returns:
        Label name if found, None otherwise
    """
    global _label_name_to_id_cache

    # System labels are often their own names/IDs
    system_labels = ["INBOX", "SPAM", "TRASH", "UNREAD", "IMPORTANT", "STARRED", "SENT", "DRAFT",
                     "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS"]
    if label_id.upper() in system_labels:
        return label_id.upper()

    # Check cache: Iterate through cache items to find the name for the given ID
    # The cache stores {name.lower(): id} and {id: id}. We need to find a key (name) whose value is label_id.
    
    # First pass: check if the label_id itself is a key that maps to itself (from id->id storage)
    # and then try to find a name that maps to this ID. This is a bit convoluted due to current cache structure.
    # A better cache might be {id: {"name": "Actual Name", "lower_name": "actual name"}}

    # Attempt to find a name that maps to this ID
    for name_key, id_val in _label_name_to_id_cache.items():
        if id_val == label_id and name_key != label_id: # Ensure we are getting a name, not the ID itself as key
            # We stored names as lowercase, but we don't have the original case here.
            # This is a limitation. For now, returning the lowercase name found as key.
            # Ideally, _populate_label_cache would store original names too.
            # For now, we can't reliably get the original casing from just the ID if it's not a system label.
            # Let's try to find the original name by re-populating and checking. This is inefficient.
            
            # A simpler approach for now: if ID is in cache values, we can't directly get its original name
            # unless the ID itself was also stored as a name (which it isn't for user labels).
            # The current get_label_id stores name.lower() -> id and id -> id.
            # So, if label_id is a value, we need to find the key that is name.lower().
            
            # Let's try to find a key that is not an ID itself but whose value is the label_id
            if name_key != id_val: # This means name_key is a lowercase name
                 # This is imperfect as it returns the lowercase name.
                 # To get the original cased name, the cache structure would need to be {id: name} or similar.
                 # Given current cache, this is the best we can do without fetching all labels again.
                 # Let's assume for now that if an ID is passed, and it's a user label,
                 # we might not have its original casing easily from this cache structure.
                 # The test data implies we might just need to return the ID if not a system label.
                 pass # Fall through to populate and re-check

    # Populate cache if empty or if we couldn't find it (hoping it appears)
    if not _label_name_to_id_cache or label_id not in _label_name_to_id_cache.values():
        _populate_label_cache(gmail_service)

    # Second attempt after populating/refreshing
    for name_key, id_val in _label_name_to_id_cache.items():
        if id_val == label_id and name_key != label_id: # name_key is lowercased name
            # Attempt to find the original cased name if possible (this is hard with current cache)
            # For now, returning the key which is lowercased.
            # This function might need a redesign or the cache needs to store original names.
            # A direct lookup `_label_id_to_name_cache` would be better.
            # Given the existing cache, we can only reliably return the ID itself if it's not a system label.
            # The tests seem to imply that if a label ID is given, and it's not a system label,
            # returning the ID itself is acceptable if the name isn't readily available.
            # Let's refine: if label_id is in _label_name_to_id_cache, it means it was stored as id->id.
            # We need to find the *other* key (the name) that maps to this label_id.
            
            # Search for the name that corresponds to this ID
            for potential_name, stored_id in _label_name_to_id_cache.items():
                if stored_id == label_id and potential_name != label_id: # Found the name mapping
                    # This potential_name is lowercase. We don't have original case.
                    return potential_name # Return the lowercase name
    
    # If after all attempts, we can't find a name, return the ID itself as a fallback
    # This matches behavior where get_label_id returns the ID if it's passed in.
    logger.warning(f"Could not resolve a distinct name for label ID '{label_id}' from cache. Returning ID.")
    return label_id

def get_label_id_from_name(gmail_service, label_name: str) -> Optional[str]:
    """Alias for get_label_id for backward compatibility."""
    return get_label_id(gmail_service, label_name)


@with_rate_limiting
def create_label(gmail_service, label_name: str, label_list_visibility: str = "labelShow", 
                message_list_visibility: str = "show", background_color: str = None,
                text_color: str = None) -> Dict[str, Any]:
    """
    Create a new Gmail label.
    
    Args:
        gmail_service: Authenticated Gmail service client
        label_name: Name of the label to create
        label_list_visibility: Visibility in label list ("labelShow", "labelShowIfUnread", "labelHide")
        message_list_visibility: Visibility in message list ("show", "hide")
        background_color: Hex color for label background (e.g., "#42d692")
        text_color: Hex color for label text (e.g., "#094228")
        
    Returns:
        Dict containing the created label information
        
    Raises:
        GmailApiError: If API call fails or label already exists
    """
    try:
        # Check if label already exists
        existing_id = get_label_id(gmail_service, label_name)
        if existing_id:
            logger.info(f"Label '{label_name}' already exists with ID: {existing_id}")
            return {
                "success": True,
                "already_exists": True,
                "label_id": existing_id,
                "label_name": label_name,
                "message": f"Label '{label_name}' already exists"
            }
        
        # Prepare label body
        label_body = {
            "name": label_name,
            "labelListVisibility": label_list_visibility,
            "messageListVisibility": message_list_visibility
        }
        
        # Add color if specified
        if background_color or text_color:
            label_body["color"] = {}
            if background_color:
                label_body["color"]["backgroundColor"] = background_color
            if text_color:
                label_body["color"]["textColor"] = text_color
        
        # Create the label
        result = gmail_service.users().labels().create(
            userId='me',
            body=label_body
        ).execute()
        
        # Update cache with new label
        _label_name_to_id_cache[label_name.lower()] = result['id']
        _label_name_to_id_cache[result['id']] = result['id']
        
        logger.info(f"Created label '{label_name}' with ID: {result['id']}")
        
        return {
            "success": True,
            "label_id": result['id'],
            "label_name": result['name'],
            "created": True,
            "message": f"Successfully created label '{label_name}'"
        }
        
    except HttpError as e:
        if e.resp.status == 409:
            # Label already exists (shouldn't happen due to our check, but just in case)
            raise GmailApiError(f"Label '{label_name}' already exists")
        else:
            error_details = e.error_details[0] if e.error_details else {}
            raise GmailApiError(
                f"Failed to create label: {error_details.get('message', str(e))}"
            )
    except Exception as e:
        raise GmailApiError(f"Unexpected error creating label: {str(e)}")


@with_rate_limiting
def delete_label(gmail_service, label_name: str) -> Dict[str, Any]:
    """
    Delete a Gmail label.
    
    Args:
        gmail_service: Authenticated Gmail service client
        label_name: Name or ID of the label to delete
        
    Returns:
        Dict containing deletion result
        
    Raises:
        GmailApiError: If API call fails or label not found
    """
    try:
        # Get label ID
        label_id = get_label_id(gmail_service, label_name)
        if not label_id:
            raise GmailApiError(f"Label '{label_name}' not found")
        
        # System labels cannot be deleted
        system_labels = ["INBOX", "SPAM", "TRASH", "UNREAD", "IMPORTANT", "STARRED", "SENT", "DRAFT",
                        "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS"]
        if label_id in system_labels:
            raise GmailApiError(f"Cannot delete system label '{label_name}'")
        
        # Delete the label
        gmail_service.users().labels().delete(
            userId='me',
            id=label_id
        ).execute()
        
        # Remove from cache
        if label_name.lower() in _label_name_to_id_cache:
            del _label_name_to_id_cache[label_name.lower()]
        if label_id in _label_name_to_id_cache:
            del _label_name_to_id_cache[label_id]
        
        logger.info(f"Deleted label '{label_name}' (ID: {label_id})")
        
        return {
            "success": True,
            "label_id": label_id,
            "label_name": label_name,
            "deleted": True,
            "message": f"Successfully deleted label '{label_name}'"
        }
        
    except HttpError as e:
        if e.resp.status == 404:
            raise GmailApiError(f"Label '{label_name}' not found")
        else:
            error_details = e.error_details[0] if e.error_details else {}
            raise GmailApiError(
                f"Failed to delete label: {error_details.get('message', str(e))}"
            )
    except Exception as e:
        raise GmailApiError(f"Unexpected error deleting label: {str(e)}")


# Message Management Functions
@with_rate_limiting  
def list_messages(gmail_service, query_string: str = None, max_results: int = 100, 
                 page_token: str = None) -> Dict[str, Any]:
    """
    List Gmail messages based on query.
    
    Args:
        gmail_service: Authenticated Gmail service client
        query_string: Gmail query string for filtering
        max_results: Maximum number of messages to return
        page_token: Token for pagination
        
    Returns:
        Dict containing messages list and pagination info (Gmail API format)
        
    Raises:
        GmailApiError: If API call fails
        InvalidParameterError: If parameters are invalid
    """
    if not gmail_service:
        raise InvalidParameterError("Gmail service client is required")

    try:
        request_params = {
            'userId': 'me',
            'maxResults': min(max_results, 500)  # Gmail API max is 500
        }
        
        if query_string:
            request_params['q'] = query_string
        if page_token:
            request_params['pageToken'] = page_token
            
        logger.debug(f"Listing messages with params: {request_params}")
        
        result = gmail_service.users().messages().list(**request_params).execute()
        
        messages = result.get('messages', [])
        logger.info(f"Retrieved {len(messages)} messages")
        
        # Return Gmail API format for consistency with tests
        return result
        
    except HttpError as e:
        logger.error(
            f"HttpError in list_messages: type(e)={type(e)}, "
            f"e.resp.status={e.resp.status if e.resp else 'N/A'}, "
            f"e.error_details={e.error_details!r}, type(e.error_details)={type(e.error_details)}, "
            f"e.content={e.content!r}, str(e)={str(e)}"
        )
        # Original line that might be problematic:
        error_detail_obj = e.error_details[0] if isinstance(e.error_details, list) and e.error_details else (e.error_details if isinstance(e.error_details, dict) else {})
        
        message_from_details = None
        if isinstance(error_detail_obj, dict):
            message_from_details = error_detail_obj.get('message')

        final_message_str = message_from_details or str(e)
        raise GmailApiError(f"Failed to list messages: {final_message_str}", original_exception=e)
    except Exception as e:
        logger.error(f"Unexpected exception in list_messages: type(e)={type(e)}, str(e)={str(e)}")
        raise GmailApiError(f"Unexpected error listing messages: {str(e)}", original_exception=e)


@with_rate_limiting
def get_message_details(gmail_service, message_id: str, format: str = 'full') -> Dict[str, Any]:
    """
    Get detailed information about a specific message.

    Args:
        gmail_service: Authenticated Gmail service client
        message_id: ID of the message to retrieve
        format: Format of the message ('full', 'metadata', 'minimal', 'raw')

    Returns:
        Dict containing detailed message information

    Raises:
        GmailApiError: If API call fails or message not found
    """
    try:
        logger.debug(f"Getting details for message {message_id}")

        result = gmail_service.users().messages().get(
            userId='me',
            id=message_id,
            format=format
        ).execute()

        logger.info(f"Retrieved details for message {message_id}")
        return result

    except HttpError as e:
        if e.resp.status == 404:
            raise GmailApiError(f"Message {message_id} not found")
        else:
            error_details = e.error_details[0] if e.error_details else {}
            raise GmailApiError(f"Failed to get message details: {error_details.get('message', str(e))}")
    except Exception as e:
        raise GmailApiError(f"Unexpected error getting message details: {str(e)}")


# Helper functions for enhanced email fetching
def _extract_headers_from_payload(payload: Dict) -> Dict[str, str]:
    """
    Extract email headers from Gmail API payload.

    Args:
        payload: Gmail API message payload

    Returns:
        Dict of header name -> value
    """
    headers = {}
    for header in payload.get('headers', []):
        headers[header['name']] = header['value']
    return headers


def _extract_body_parts_from_payload(payload: Dict) -> Dict[str, str]:
    """
    Extract text and HTML body parts from Gmail API payload.
    Handles both simple and multipart messages.

    Args:
        payload: Gmail API message payload

    Returns:
        Dict with 'text' and 'html' keys containing decoded body content
    """
    result = {'text': '', 'html': ''}

    def decode_body_data(data: str) -> str:
        """Decode base64url-encoded body data."""
        try:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        except Exception as e:
            logger.warning(f"Failed to decode body data: {e}")
            return ""

    def extract_from_part(part: Dict):
        """Recursively extract text/html from a message part."""
        mime_type = part.get('mimeType', '')
        body = part.get('body', {})

        # Check if this part has body data
        if body.get('data'):
            if mime_type == 'text/plain' and not result['text']:
                result['text'] = decode_body_data(body['data'])
            elif mime_type == 'text/html' and not result['html']:
                result['html'] = decode_body_data(body['data'])

        # Recursively process sub-parts
        if part.get('parts'):
            for sub_part in part['parts']:
                extract_from_part(sub_part)

    # Handle simple message (body data directly in payload)
    if payload.get('body', {}).get('data'):
        mime_type = payload.get('mimeType', '')
        data = payload['body']['data']
        if mime_type == 'text/plain':
            result['text'] = decode_body_data(data)
        elif mime_type == 'text/html':
            result['html'] = decode_body_data(data)

    # Handle multipart message
    if payload.get('parts'):
        for part in payload['parts']:
            extract_from_part(part)

    return result


def _extract_attachment_metadata_from_payload(payload: Dict) -> List[Dict[str, Any]]:
    """
    Extract attachment metadata from Gmail API payload without downloading attachment data.

    Args:
        payload: Gmail API message payload

    Returns:
        List of dicts containing attachment metadata (id, filename, size, mimeType)
    """
    attachments = []

    def extract_from_part(part: Dict):
        """Recursively extract attachment metadata from message parts."""
        # Check if this part is an attachment
        if part.get('filename') and part.get('body', {}).get('attachmentId'):
            attachment_info = {
                'attachment_id': part['body']['attachmentId'],
                'filename': part['filename'],
                'size_bytes': part['body'].get('size', 0),
                'mime_type': part.get('mimeType', 'application/octet-stream')
            }
            attachments.append(attachment_info)

        # Recursively process sub-parts
        if part.get('parts'):
            for sub_part in part['parts']:
                extract_from_part(sub_part)

    # Process all parts
    if payload.get('parts'):
        for part in payload['parts']:
            extract_from_part(part)

    return attachments


@with_rate_limiting
def get_message_details_chunked(
    gmail_service,
    message_id: str,
    detail_level: str = 'full_metadata',
    include_body: bool = True,
    include_attachment_metadata: bool = True
) -> Dict[str, Any]:
    """
    Get email details with timeout-resistant chunked/progressive fetching.

    This function uses format='metadata' to fetch email structure without downloading
    attachment data, preventing timeouts on large emails.

    Args:
        gmail_service: Authenticated Gmail service client
        message_id: ID of the message to retrieve
        detail_level: Level of detail to fetch:
            - 'headers_only': Just headers (fastest, 1-2s)
            - 'standard': Headers + body text (medium, 3-7s)
            - 'full_metadata': Headers + body + attachment metadata (3-10s, never times out)
        include_body: Whether to include email body content (ignored if detail_level='headers_only')
        include_attachment_metadata: Whether to include attachment metadata

    Returns:
        Dict containing:
            - success: bool
            - email_id: str
            - headers: Dict[str, str]
            - body: Dict[str, str] (with 'text' and 'html' keys)
            - attachments: Dict with 'total_count', 'total_size_bytes', 'items'
            - performance: Dict with timing and size estimates

    Raises:
        GmailApiError: If API call fails or message not found
        InvalidParameterError: If parameters are invalid
    """
    import time
    start_time = time.time()

    # Validate parameters
    valid_detail_levels = ['headers_only', 'standard', 'full_metadata']
    if detail_level not in valid_detail_levels:
        raise InvalidParameterError(
            f"detail_level must be one of {valid_detail_levels}, got '{detail_level}'"
        )

    try:
        logger.debug(f"Getting chunked details for message {message_id} with detail_level={detail_level}")

        # PHASE 1: Fetch metadata (fast, no attachment data)
        # This is the key to avoiding timeouts - we get structure without data
        message = gmail_service.users().messages().get(
            userId='me',
            id=message_id,
            format='metadata'  # Gets headers + structure, NO attachment data
        ).execute()

        phase1_time = time.time() - start_time
        logger.debug(f"Phase 1 (metadata fetch) completed in {phase1_time:.2f}s")

        # Extract basic info
        payload = message.get('payload', {})
        thread_id = message.get('threadId', '')
        label_ids = message.get('labelIds', [])

        # Extract headers
        headers = _extract_headers_from_payload(payload)

        # Build response
        response = {
            'success': True,
            'email_id': message_id,
            'thread_id': thread_id,
            'label_ids': label_ids,
            'headers': headers,
            'body': {'text': '', 'html': ''},
            'attachments': {
                'total_count': 0,
                'total_size_bytes': 0,
                'items': []
            },
            'performance': {
                'format_used': 'metadata',
                'detail_level': detail_level,
                'fetch_time_seconds': 0.0,
                'estimated_size_mb': 0.0
            }
        }

        # PHASE 2: Extract body if requested (still fast, uses metadata response)
        if detail_level in ['standard', 'full_metadata'] and include_body:
            # Note: metadata format includes body structure and small bodies
            # Large bodies are truncated, but we get what's available
            body_parts = _extract_body_parts_from_payload(payload)
            response['body'] = body_parts
            logger.debug(f"Extracted body: text={len(body_parts['text'])} chars, html={len(body_parts['html'])} chars")

        # PHASE 3: Extract attachment metadata if requested (fast, just metadata)
        if detail_level == 'full_metadata' and include_attachment_metadata:
            attachments = _extract_attachment_metadata_from_payload(payload)
            total_size = sum(att['size_bytes'] for att in attachments)

            response['attachments'] = {
                'total_count': len(attachments),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'items': attachments
            }

            logger.debug(f"Found {len(attachments)} attachments, total size: {total_size / (1024 * 1024):.2f} MB")

        # Calculate performance metrics
        total_time = time.time() - start_time
        estimated_size_mb = response['attachments']['total_size_bytes'] / (1024 * 1024)

        response['performance'] = {
            'format_used': 'metadata',
            'detail_level': detail_level,
            'fetch_time_seconds': round(total_time, 3),
            'estimated_size_mb': round(estimated_size_mb, 2),
            'phase_1_time_seconds': round(phase1_time, 3)
        }

        logger.info(
            f"Retrieved chunked details for message {message_id}: "
            f"{len(attachments) if include_attachment_metadata else 0} attachments, "
            f"{estimated_size_mb:.2f} MB, "
            f"{total_time:.2f}s"
        )

        return response

    except HttpError as e:
        if e.resp.status == 404:
            raise GmailApiError(f"Message {message_id} not found")
        else:
            error_details = e.error_details[0] if e.error_details else {}
            raise GmailApiError(f"Failed to get message details: {error_details.get('message', str(e))}")
    except Exception as e:
        logger.error(f"Unexpected error in get_message_details_chunked: {e}", exc_info=True)
        raise GmailApiError(f"Unexpected error getting message details: {str(e)}")


# Batch Operations
@with_rate_limiting
def batch_modify_message_labels(gmail_service, message_ids: List[str], 
                               add_label_names: List[str] = None,
                               remove_label_names: List[str] = None) -> Dict[str, Any]:
    """
    Batch modify labels on multiple messages.
    
    Args:
        gmail_service: Authenticated Gmail service client
        message_ids: List of message IDs to modify
        add_label_names: List of label names to add
        remove_label_names: List of label names to remove
        
    Returns:
        Dict containing operation results
        
    Raises:
        GmailApiError: If API call fails
        InvalidParameterError: If parameters are invalid
    """
    if not gmail_service:
        raise InvalidParameterError("Gmail service client is required")

    try:
        if not message_ids:
            return {"success": True, "message": "No messages to modify", "modified_count": 0}
        
        # Convert label names to IDs
        add_label_ids = []
        remove_label_ids = []
        
        if add_label_names:
            for label_name in add_label_names:
                label_id = get_label_id(gmail_service, label_name)
                if label_id:
                    add_label_ids.append(label_id)
                    
        if remove_label_names:
            for label_name in remove_label_names:
                label_id = get_label_id(gmail_service, label_name) 
                if label_id:
                    remove_label_ids.append(label_id)
        
        if not add_label_ids and not remove_label_ids:
            return {"success": True, "message": "No valid labels to modify", "modified_count": 0}
        
        # Build batch modify request
        body = {'ids': message_ids}
        if add_label_ids:
            body['addLabelIds'] = add_label_ids
        if remove_label_ids:
            body['removeLabelIds'] = remove_label_ids
            
        logger.debug(f"Batch modifying labels on {len(message_ids)} messages")
        
        gmail_service.users().messages().batchModify(
            userId='me',
            body=body
        ).execute()
        
        logger.info(f"Successfully modified labels on {len(message_ids)} messages")
        
        return {
            "success": True,
            "modified_count": len(message_ids),
            "message": f"Successfully modified labels on {len(message_ids)} messages"
        }
        
    except HttpError as e:
        logger.error(
            f"HttpError in batch_modify_message_labels: type(e)={type(e)}, "
            f"e.resp.status={e.resp.status if e.resp else 'N/A'}, "
            f"e.error_details={e.error_details!r}, type(e.error_details)={type(e.error_details)}, "
            f"e.content={e.content!r}, str(e)={str(e)}"
        )
        error_detail_obj = e.error_details[0] if isinstance(e.error_details, list) and e.error_details else (e.error_details if isinstance(e.error_details, dict) else {})
        message_from_details = None
        if isinstance(error_detail_obj, dict):
            message_from_details = error_detail_obj.get('message')
        final_message_str = message_from_details or str(e)
        raise GmailApiError(f"Failed to batch modify message labels: {final_message_str}", original_exception=e)
    except Exception as e:
        logger.error(f"Unexpected exception in batch_modify_message_labels: type(e)={type(e)}, str(e)={str(e)}")
        raise GmailApiError(f"Unexpected error in batch modify labels: {str(e)}", original_exception=e)


@with_rate_limiting
def batch_trash_messages(gmail_service, message_ids: List[str]) -> Dict[str, Any]:
    """
    Batch move messages to trash.
    
    Args:
        gmail_service: Authenticated Gmail service client
        message_ids: List of message IDs to trash
        
    Returns:
        Dict containing operation results
        
    Raises:
        GmailApiError: If API call fails
    """
    try:
        if not message_ids:
            return {"success": True, "message": "No messages to trash", "trashed_count": 0}
        
        logger.debug(f"Batch trashing {len(message_ids)} messages")
        
        # For small batches, use individual trash() calls which are more reliable
        if len(message_ids) <= 10:
            logger.debug("Using individual trash() calls for small batch")
            for message_id in message_ids:
                gmail_service.users().messages().trash(
                    userId='me',
                    id=message_id
                ).execute()
        else:
            # For larger batches, use batchModify but also remove from INBOX
            logger.debug("Using batchModify for large batch")
            gmail_service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'addLabelIds': ['TRASH'],
                    'removeLabelIds': ['INBOX']  # This is crucial for proper trashing
                }
            ).execute()
        
        # Verify that emails are actually in trash for small batches
        if len(message_ids) <= 5:
            logger.debug("Verifying trash operation for small batch")
            verification_failed = []
            for message_id in message_ids:
                try:
                    msg = gmail_service.users().messages().get(
                        userId='me', 
                        id=message_id, 
                        format='minimal'
                    ).execute()
                    labels = msg.get('labelIds', [])
                    if 'TRASH' not in labels:
                        verification_failed.append(message_id)
                except Exception as e:
                    logger.warning(f"Could not verify trash status for message {message_id}: {e}")
            
            if verification_failed:
                logger.error(f"Verification failed for {len(verification_failed)} messages: {verification_failed}")
                raise GmailApiError(f"Trash operation succeeded but verification failed for {len(verification_failed)} messages")
        
        logger.info(f"Successfully trashed {len(message_ids)} messages")
        
        return {
            "success": True,
            "trashed_count": len(message_ids),
            "message": f"Successfully trashed {len(message_ids)} messages"
        }
        
    except HttpError as e:
        error_details = e.error_details[0] if e.error_details else {}
        raise GmailApiError(f"Failed to batch trash messages: {error_details.get('message', str(e))}")
    except Exception as e:
        raise GmailApiError(f"Unexpected error in batch trash: {str(e)}")


@with_rate_limiting
def batch_mark_messages(gmail_service, message_ids: List[str], action: str) -> Dict[str, Any]:
    """
    Batch mark messages as read or unread.
    
    Args:
        gmail_service: Authenticated Gmail service client
        message_ids: List of message IDs to mark
        action: 'read' or 'unread'
        
    Returns:
        Dict containing operation results
        
    Raises:
        GmailApiError: If API call fails
        InvalidParameterError: If action is invalid
    """
    # Initial parameter validations (outside the main try block for API calls)
    if not gmail_service:
        raise InvalidParameterError("Gmail service client is required")
    if action not in ['read', 'unread']:
        raise InvalidParameterError(f"Invalid action '{action}'. Must be 'read' or 'unread'")
            
    if not message_ids:
        return {"success": True, "message": f"No messages to mark as {action}", "marked_count": 0, "action": action}
        
    try:
        logger.debug(f"Batch marking {len(message_ids)} messages as {action}")
        
        if action == 'read':
            # Remove UNREAD label
            body = {
                'ids': message_ids,
                'removeLabelIds': ['UNREAD']
            }
        else:  # unread
            # Add UNREAD label
            body = {
                'ids': message_ids,
                'addLabelIds': ['UNREAD']
            }
        
        gmail_service.users().messages().batchModify(
            userId='me',
            body=body
        ).execute()
        
        logger.info(f"Successfully marked {len(message_ids)} messages as {action}")
        
        return {
            "success": True,
            "marked_count": len(message_ids),
            "action": action,
            "message": f"Successfully marked {len(message_ids)} messages as {action}"
        }
        
    except HttpError as e:
        logger.error(
            f"HttpError in batch_mark_messages: type(e)={type(e)}, "
            f"e.resp.status={e.resp.status if e.resp else 'N/A'}, "
            f"e.error_details={e.error_details!r}, type(e.error_details)={type(e.error_details)}, "
            f"e.content={e.content!r}, str(e)={str(e)}"
        )
        error_detail_obj = e.error_details[0] if isinstance(e.error_details, list) and e.error_details else (e.error_details if isinstance(e.error_details, dict) else {})
        message_from_details = None
        if isinstance(error_detail_obj, dict):
            message_from_details = error_detail_obj.get('message')
        final_message_str = message_from_details or str(e)
        raise GmailApiError(f"Failed to batch mark messages: {final_message_str}", original_exception=e)
    except Exception as e:
        logger.error(f"Unexpected exception in batch_mark_messages: type(e)={type(e)}, str(e)={str(e)}")
        raise GmailApiError(f"Unexpected error in batch mark: {str(e)}", original_exception=e)


@with_rate_limiting
def batch_delete_permanently(gmail_service, message_ids: List[str]) -> Dict[str, Any]:
    """
    Batch permanently delete messages (irreversible).
    
    Args:
        gmail_service: Authenticated Gmail service client
        message_ids: List of message IDs to delete permanently
        
    Returns:
        Dict containing operation results
        
    Raises:
        GmailApiError: If API call fails
    """
    # Initial parameter validations
    if not gmail_service:
        raise InvalidParameterError("Gmail service client is required")

    if not message_ids:
        return {"success": True, "message": "No messages to delete", "deleted_count": 0}
        
    try:
        logger.debug(f"Batch permanently deleting {len(message_ids)} messages")
        
        gmail_service.users().messages().batchDelete(
            userId='me',
            body={'ids': message_ids}
        ).execute()
        
        logger.info(f"Successfully deleted {len(message_ids)} messages permanently")
        
        return {
            "success": True,
            "deleted_count": len(message_ids),
            "message": f"Successfully deleted {len(message_ids)} messages permanently"
        }
        
    except HttpError as e:
        logger.error(
            f"HttpError in batch_delete_permanently: type(e)={type(e)}, "
            f"e.resp.status={e.resp.status if e.resp else 'N/A'}, "
            f"e.error_details={e.error_details!r}, type(e.error_details)={type(e.error_details)}, "
            f"e.content={e.content!r}, str(e)={str(e)}"
        )
        error_detail_obj = e.error_details[0] if isinstance(e.error_details, list) and e.error_details else (e.error_details if isinstance(e.error_details, dict) else {})
        message_from_details = None
        if isinstance(error_detail_obj, dict):
            message_from_details = error_detail_obj.get('message')
        final_message_str = message_from_details or str(e)
        raise GmailApiError(f"Failed to batch delete messages: {final_message_str}", original_exception=e)
    except Exception as e:
        logger.error(f"Unexpected exception in batch_delete_permanently: type(e)={type(e)}, str(e)={str(e)}")
        raise GmailApiError(f"Unexpected error in batch delete: {str(e)}", original_exception=e)


# Vacation Responder Functions
@with_rate_limiting
def get_vacation_settings(gmail_service) -> Dict[str, Any]:
    """
    Get current vacation responder settings.
    
    Args:
        gmail_service: Authenticated Gmail API service
        
    Returns:
        Dict containing vacation responder configuration
        
    Raises:
        SettingsOperationError: If API call fails
    """
    try:
        logger.debug("Getting vacation responder settings")
        
        response = gmail_service.users().settings().getVacation(userId='me').execute()
        
        logger.info("Retrieved vacation responder settings")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get vacation settings: {str(e)}")
        raise SettingsOperationError(f"Failed to get vacation settings: {str(e)}")

@with_rate_limiting
def update_vacation_settings(gmail_service, enabled: bool, subject: Optional[str] = None, 
                           body: Optional[str] = None, start_time: Optional[int] = None,
                           end_time: Optional[int] = None, 
                           restrict_to_contacts: bool = False,
                           restrict_to_domain: bool = False) -> Dict[str, Any]:
    """
    Update vacation responder settings.
    
    Args:
        gmail_service: Authenticated Gmail API service
        enabled: Whether vacation responder is enabled
        subject: Auto-reply subject line
        body: Auto-reply message body
        start_time: Start time (Unix timestamp in milliseconds)
        end_time: End time (Unix timestamp in milliseconds)
        restrict_to_contacts: Only reply to contacts
        restrict_to_domain: Only reply to domain members
        
    Returns:
        Dict containing updated vacation responder configuration
        
    Raises:
        SettingsOperationError: If update fails
    """
    try:
        logger.debug(f"Updating vacation responder: enabled={enabled}")
        
        # Build vacation responder object
        vacation_settings = {
            'enableAutoReply': enabled,
            'restrictToContacts': restrict_to_contacts,
            'restrictToDomain': restrict_to_domain
        }
        
        # Add optional fields if provided
        if subject is not None:
            vacation_settings['responseSubject'] = subject
        if body is not None:
            vacation_settings['responseBodyPlainText'] = body
        if start_time is not None:
            vacation_settings['startTime'] = str(start_time)
        if end_time is not None:
            vacation_settings['endTime'] = str(end_time)
        
        # Make API call
        response = gmail_service.users().settings().updateVacation(
            userId='me', 
            body=vacation_settings
        ).execute()
        
        logger.info(f"Updated vacation responder settings: enabled={enabled}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to update vacation settings: {str(e)}")
        raise SettingsOperationError(f"Failed to update vacation settings: {str(e)}")

def enable_vacation_responder(gmail_service, subject: str, body: str, 
                            start_time: Optional[int] = None, 
                            end_time: Optional[int] = None,
                            restrict_to_contacts: bool = False) -> Dict[str, Any]:
    """
    Enable vacation responder with specified message.
    
    Args:
        gmail_service: Authenticated Gmail API service
        subject: Auto-reply subject line
        body: Auto-reply message body
        start_time: Optional start time (Unix timestamp in milliseconds)
        end_time: Optional end time (Unix timestamp in milliseconds)
        restrict_to_contacts: Only reply to known contacts
        
    Returns:
        Dict containing vacation responder configuration
    """
    # Validate inputs
    if not subject.strip():
        raise ValueError("Subject cannot be empty")
    if not body.strip():
        raise ValueError("Body cannot be empty")
    
    return update_vacation_settings(
        gmail_service=gmail_service,
        enabled=True,
        subject=subject,
        body=body,
        start_time=start_time,
        end_time=end_time,
        restrict_to_contacts=restrict_to_contacts
    )

def disable_vacation_responder(gmail_service) -> Dict[str, Any]:
    """
    Disable vacation responder.
    
    Args:
        gmail_service: Authenticated Gmail API service
        
    Returns:
        Dict containing updated vacation responder configuration
    """
    return update_vacation_settings(gmail_service=gmail_service, enabled=False)

# IMAP Settings Functions
@with_rate_limiting
def get_imap_settings(gmail_service) -> Dict[str, Any]:
    """
    Get current IMAP settings.
    
    Args:
        gmail_service: Authenticated Gmail API service
        
    Returns:
        Dict containing IMAP configuration
        
    Raises:
        SettingsOperationError: If API call fails
    """
    try:
        logger.debug("Getting IMAP settings")
        
        response = gmail_service.users().settings().getImap(userId='me').execute()
        
        logger.info("Retrieved IMAP settings")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get IMAP settings: {str(e)}")
        raise SettingsOperationError(f"Failed to get IMAP settings: {str(e)}")

@with_rate_limiting
def update_imap_settings(gmail_service, enabled: bool, 
                        auto_expunge: bool = False,
                        expunge_behavior: str = 'archive',
                        max_folder_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Update IMAP settings.
    
    Args:
        gmail_service: Authenticated Gmail API service
        enabled: Whether IMAP access is enabled
        auto_expunge: Whether to auto-expunge deleted messages
        expunge_behavior: What to do with expunged messages ('archive', 'trash', 'delete')
        max_folder_size: Maximum folder size in MB
        
    Returns:
        Dict containing updated IMAP configuration
        
    Raises:
        SettingsOperationError: If update fails
    """
    try:
        logger.debug(f"Updating IMAP settings: enabled={enabled}")
        
        # Build IMAP settings object
        imap_settings = {
            'enabled': enabled,
            'autoExpunge': auto_expunge,
            'expungeBehavior': expunge_behavior.upper()
        }
        
        if max_folder_size is not None:
            imap_settings['maxFolderSize'] = max_folder_size
        
        # Make API call
        response = gmail_service.users().settings().updateImap(
            userId='me', 
            body=imap_settings
        ).execute()
        
        logger.info(f"Updated IMAP settings: enabled={enabled}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to update IMAP settings: {str(e)}")
        raise SettingsOperationError(f"Failed to update IMAP settings: {str(e)}")

# POP Settings Functions  
@with_rate_limiting
def get_pop_settings(gmail_service) -> Dict[str, Any]:
    """
    Get current POP settings.
    
    Args:
        gmail_service: Authenticated Gmail API service
        
    Returns:
        Dict containing POP configuration
        
    Raises:
        SettingsOperationError: If API call fails
    """
    try:
        logger.debug("Getting POP settings")
        
        response = gmail_service.users().settings().getPop(userId='me').execute()
        
        logger.info("Retrieved POP settings")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get POP settings: {str(e)}")
        raise SettingsOperationError(f"Failed to get POP settings: {str(e)}")

@with_rate_limiting
def update_pop_settings(gmail_service, access_window: str, disposition: str) -> Dict[str, Any]:
    """
    Update POP settings.
    
    Args:
        gmail_service: Authenticated Gmail API service
        access_window: When to allow POP access ('allMail', 'fromNowOn', 'disabled')
        disposition: What to do with accessed messages ('leaveInInbox', 'archive', 'trash', 'delete')
        
    Returns:
        Dict containing updated POP configuration
        
    Raises:
        SettingsOperationError: If update fails
    """
    try:
        logger.debug(f"Updating POP settings: access={access_window}, disposition={disposition}")
        
        # Validate inputs
        valid_access_windows = ['allMail', 'fromNowOn', 'disabled']
        valid_dispositions = ['leaveInInbox', 'archive', 'trash', 'delete']
        
        if access_window not in valid_access_windows:
            raise ValueError(f"Invalid access_window. Must be one of: {valid_access_windows}")
        if disposition not in valid_dispositions:
            raise ValueError(f"Invalid disposition. Must be one of: {valid_dispositions}")
        
        # Build POP settings object
        pop_settings = {
            'accessWindow': access_window,
            'disposition': disposition
        }
        
        # Make API call
        response = gmail_service.users().settings().updatePop(
            userId='me', 
            body=pop_settings
        ).execute()
        
        logger.info(f"Updated POP settings: access={access_window}, disposition={disposition}")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid POP settings: {str(e)}")
        raise SettingsOperationError(f"Invalid POP settings: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to update POP settings: {str(e)}")
        raise SettingsOperationError(f"Failed to update POP settings: {str(e)}")


# Draft Management Functions
@with_rate_limiting
def create_draft(gmail_service, to_addresses: List[str], subject: str, body: str, 
                cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, 
                thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new draft email.
    
    Args:
        gmail_service: Authenticated Gmail API service
        to_addresses: List of recipient email addresses
        subject: Email subject line
        body: Email body content
        cc: Optional list of CC recipients
        bcc: Optional list of BCC recipients
        thread_id: Optional thread ID for replies
        
    Returns:
        Dict containing the created draft information
        
    Raises:
        GmailApiError: If API call fails
    """
    try:
        logger.debug(f"Creating draft to {to_addresses} with subject: {subject}")
        
        # Build the message
        message = {
            'raw': _build_email_message(to_addresses, subject, body, cc, bcc)
        }
        
        # Add thread ID if provided (for replies)
        if thread_id:
            message['threadId'] = thread_id
        
        # Create the draft
        draft_body = {'message': message}
        response = gmail_service.users().drafts().create(
            userId='me', 
            body=draft_body
        ).execute()
        
        logger.info(f"Created draft with ID: {response.get('id')}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create draft: {str(e)}")
        raise GmailApiError(f"Failed to create draft: {str(e)}")

@with_rate_limiting
def update_draft(gmail_service, draft_id: str, to_addresses: Optional[List[str]] = None,
                subject: Optional[str] = None, body: Optional[str] = None,
                cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Update an existing draft email.
    
    Args:
        gmail_service: Authenticated Gmail API service
        draft_id: ID of the draft to update
        to_addresses: Optional new recipient list
        subject: Optional new subject line
        body: Optional new body content
        cc: Optional new CC recipients
        bcc: Optional new BCC recipients
        
    Returns:
        Dict containing the updated draft information
        
    Raises:
        GmailApiError: If API call fails
    """
    try:
        logger.debug(f"Updating draft {draft_id}")
        
        # Get current draft to preserve unchanged fields
        current_draft = gmail_service.users().drafts().get(
            userId='me', 
            id=draft_id
        ).execute()
        
        # Extract current message details
        current_message = current_draft['message']
        current_payload = current_message.get('payload', {})
        current_headers = {h['name']: h['value'] for h in current_payload.get('headers', [])}
        
        # Use provided values or fall back to current ones
        final_to = to_addresses or [current_headers.get('To', '')]
        final_subject = subject or current_headers.get('Subject', '')
        final_body = body or _extract_body_from_payload(current_payload)
        final_cc = cc or ([current_headers.get('Cc')] if current_headers.get('Cc') else None)
        final_bcc = bcc or ([current_headers.get('Bcc')] if current_headers.get('Bcc') else None)
        
        # Build updated message
        message = {
            'raw': _build_email_message(final_to, final_subject, final_body, final_cc, final_bcc)
        }
        
        # Preserve thread ID if it exists
        if current_message.get('threadId'):
            message['threadId'] = current_message['threadId']
        
        # Update the draft
        draft_body = {'message': message}
        response = gmail_service.users().drafts().update(
            userId='me',
            id=draft_id,
            body=draft_body
        ).execute()
        
        logger.info(f"Updated draft {draft_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to update draft {draft_id}: {str(e)}")
        raise GmailApiError(f"Failed to update draft {draft_id}: {str(e)}")

@with_rate_limiting
def send_draft(gmail_service, draft_id: str) -> Dict[str, Any]:
    """
    Send an existing draft email.
    
    Args:
        gmail_service: Authenticated Gmail API service
        draft_id: ID of the draft to send
        
    Returns:
        Dict containing the sent message information
        
    Raises:
        GmailApiError: If API call fails
    """
    try:
        logger.debug(f"Sending draft {draft_id}")
        
        response = gmail_service.users().drafts().send(
            userId='me',
            body={'id': draft_id}
        ).execute()
        
        logger.info(f"Sent draft {draft_id} as message {response.get('id')}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to send draft {draft_id}: {str(e)}")
        raise GmailApiError(f"Failed to send draft {draft_id}: {str(e)}")

@with_rate_limiting
def list_drafts(gmail_service, query: Optional[str] = None, 
               max_results: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
    """
    List draft emails with optional filtering.
    
    Args:
        gmail_service: Authenticated Gmail API service
        query: Optional Gmail query string to filter drafts
        max_results: Maximum number of drafts to return (default: 100)
        page_token: Optional page token for pagination
        
    Returns:
        Dict containing list of drafts and pagination info
        
    Raises:
        GmailApiError: If API call fails
    """
    try:
        logger.debug(f"Listing drafts with query: {query}")
        
        # Build request parameters
        params = {
            'userId': 'me',
            'maxResults': min(max_results, 500)  # Gmail API max is 500
        }
        
        if query:
            params['q'] = query
        if page_token:
            params['pageToken'] = page_token
        
        response = gmail_service.users().drafts().list(**params).execute()
        
        drafts = response.get('drafts', [])
        logger.info(f"Retrieved {len(drafts)} drafts")
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to list drafts: {str(e)}")
        raise GmailApiError(f"Failed to list drafts: {str(e)}")

@with_rate_limiting
def get_draft_details(gmail_service, draft_id: str, format: str = 'full') -> Dict[str, Any]:
    """
    Get detailed information about a specific draft.
    
    Args:
        gmail_service: Authenticated Gmail API service
        draft_id: ID of the draft to retrieve
        format: Format of the draft ('full', 'metadata', 'minimal')
        
    Returns:
        Dict containing detailed draft information
        
    Raises:
        GmailApiError: If API call fails
    """
    try:
        logger.debug(f"Getting details for draft {draft_id}")
        
        response = gmail_service.users().drafts().get(
            userId='me',
            id=draft_id,
            format=format
        ).execute()
        
        logger.info(f"Retrieved details for draft {draft_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get draft details for {draft_id}: {str(e)}")
        raise GmailApiError(f"Failed to get draft details for {draft_id}: {str(e)}")

@with_rate_limiting
def delete_draft(gmail_service, draft_id: str) -> Dict[str, Any]:
    """
    Delete a draft email.
    
    Args:
        gmail_service: Authenticated Gmail API service
        draft_id: ID of the draft to delete
        
    Returns:
        Dict containing confirmation of deletion
        
    Raises:
        GmailApiError: If API call fails
    """
    try:
        logger.debug(f"Deleting draft {draft_id}")
        
        gmail_service.users().drafts().delete(
            userId='me',
            id=draft_id
        ).execute()
        
        logger.info(f"Deleted draft {draft_id}")
        return {"status": "success", "message": f"Draft {draft_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete draft {draft_id}: {str(e)}")
        raise GmailApiError(f"Failed to delete draft {draft_id}: {str(e)}")


# Helper Functions for Draft Operations
def _build_email_message(to_addresses: List[str], subject: str, body: str,
                        cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> str:
    """
    Build a raw email message string for Gmail API.
    
    Args:
        to_addresses: List of recipient email addresses
        subject: Email subject
        body: Email body content
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        
    Returns:
        Base64-encoded email message string
    """
    import email.mime.text
    import base64
    
    # Create the message
    message = email.mime.text.MIMEText(body)
    message['To'] = ', '.join(to_addresses)
    message['Subject'] = subject
    
    if cc:
        message['Cc'] = ', '.join(cc)
    if bcc:
        message['Bcc'] = ', '.join(bcc)
    
    # Encode the message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return raw_message

def _extract_body_from_payload(payload: Dict) -> str:
    """
    Extract email body content from Gmail API payload.
    
    Args:
        payload: Gmail API message payload
        
    Returns:
        Email body content as string
    """
    body = ""
    
    if payload.get('body', {}).get('data'):
        # Simple text message
        import base64
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    elif payload.get('parts'):
        # Multi-part message - look for text/plain part
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                import base64
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
    
    return body


# Thread Management Functions
@with_rate_limiting
def list_threads(gmail_service, query: str = None, max_results: int = 100, 
                page_token: str = None) -> Dict:
    """
    List email threads from Gmail.
    
    Args:
        gmail_service: Authenticated Gmail service instance
        query: Gmail query string for filtering threads
        max_results: Maximum number of threads to return (1-500)
        page_token: Token for pagination
        
    Returns:
        Dict containing threads list and pagination info
        
    Raises:
        GmailApiError: If Gmail API call fails
    """
    try:
        request_params = {
            'userId': 'me',
            'maxResults': max_results
        }
        
        if query:
            request_params['q'] = query
        if page_token:
            request_params['pageToken'] = page_token
            
        result = gmail_service.users().threads().list(**request_params).execute()
        
        return {
            "success": True,
            "threads": result.get('threads', []),
            "next_page_token": result.get('nextPageToken'),
            "result_size_estimate": result.get('resultSizeEstimate', 0)
        }
        
    except HttpError as e:
        error_details = e.error_details[0] if e.error_details else {}
        raise GmailApiError(
            f"Failed to list threads: {error_details.get('message', str(e))}"
        )
    except Exception as e:
        raise GmailApiError(f"Unexpected error listing threads: {str(e)}")


@with_rate_limiting
def get_thread_details(gmail_service, thread_id: str, format: str = 'full') -> Dict:
    """
    Get complete thread information including all messages.

    Args:
        gmail_service: Authenticated Gmail service instance
        thread_id: Thread ID to retrieve
        format: Detail level - 'full', 'metadata', or 'minimal'

    Returns:
        Dict containing complete thread information

    Raises:
        GmailApiError: If Gmail API call fails or thread not found
        ValueError: If input parameters are invalid
    """
    # === INPUT VALIDATION (Defense in Depth) ===

    # Validate thread_id
    if not thread_id:
        raise ValueError("thread_id is required and cannot be None or empty")

    if not isinstance(thread_id, str):
        raise ValueError(f"thread_id must be a string, got {type(thread_id).__name__}")

    thread_id = thread_id.strip()
    if not thread_id:
        raise ValueError("thread_id cannot be empty or whitespace")

    if len(thread_id) < 10:
        raise ValueError(f"thread_id appears invalid: too short (length: {len(thread_id)})")

    if len(thread_id) > 100:
        raise ValueError(f"thread_id appears invalid: too long (length: {len(thread_id)})")

    # Validate format
    allowed_formats = ['full', 'metadata', 'minimal']
    if format not in allowed_formats:
        raise ValueError(f"format must be one of {allowed_formats}, got '{format}'")

    # === GMAIL API CALL ===
    try:
        result = gmail_service.users().threads().get(
            userId='me',
            id=thread_id,
            format=format
        ).execute()

        return {
            "success": True,
            "thread": result,
            "thread_id": thread_id,
            "message_count": len(result.get('messages', []))
        }

    except HttpError as e:
        if e.resp.status == 404:
            raise GmailApiError(f"Thread '{thread_id}' not found (404)")
        elif e.resp.status == 403:
            raise GmailApiError("Insufficient permissions to access thread (403)")
        elif e.resp.status == 400:
            raise GmailApiError(f"Invalid thread_id format: '{thread_id}' (400)")
        else:
            error_details = e.error_details[0] if e.error_details else {}
            raise GmailApiError(
                f"Failed to get thread details: {error_details.get('message', str(e))}"
            )
    except ValueError as e:
        # Re-raise validation errors with clear context
        raise ValueError(f"Parameter validation failed: {str(e)}")
    except Exception as e:
        raise GmailApiError(f"Unexpected error getting thread details: {str(e)}")


@with_rate_limiting
def modify_thread_labels(gmail_service, thread_id: str, 
                        add_labels: Optional[List[str]] = None,
                        remove_labels: Optional[List[str]] = None) -> Dict:
    """
    Add or remove labels from an entire thread.
    
    Args:
        gmail_service: Authenticated Gmail service instance
        thread_id: Thread ID to modify
        add_labels: List of label names to add
        remove_labels: List of label names to remove
        
    Returns:
        Dict containing modification result
        
    Raises:
        GmailApiError: If Gmail API call fails
    """
    try:
        # Convert label names to IDs
        add_label_ids = []
        remove_label_ids = []
        
        if add_labels:
            for label_name in add_labels:
                label_id = get_label_id_from_name(gmail_service, label_name)
                if label_id:
                    add_label_ids.append(label_id)
                    
        if remove_labels:
            for label_name in remove_labels:
                label_id = get_label_id_from_name(gmail_service, label_name)
                if label_id:
                    remove_label_ids.append(label_id)
        
        body = {}
        if add_label_ids:
            body['addLabelIds'] = add_label_ids
        if remove_label_ids:
            body['removeLabelIds'] = remove_label_ids
            
        if not body:
            return {
                "success": True,
                "message": "No valid labels to modify",
                "thread_id": thread_id
            }
        
        result = gmail_service.users().threads().modify(
            userId='me',
            id=thread_id,
            body=body
        ).execute()
        
        return {
            "success": True,
            "thread": result,
            "thread_id": thread_id,
            "labels_added": add_labels or [],
            "labels_removed": remove_labels or []
        }
        
    except HttpError as e:
        if e.resp.status == 404:
            raise GmailApiError(f"Thread {thread_id} not found")
        else:
            error_details = e.error_details[0] if e.error_details else {}
            raise GmailApiError(
                f"Failed to modify thread labels: {error_details.get('message', str(e))}"
            )
    except Exception as e:
        raise GmailApiError(f"Unexpected error modifying thread labels: {str(e)}")


@with_rate_limiting
def trash_thread(gmail_service, thread_id: str) -> Dict:
    """
    Move entire thread to trash.
    
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
