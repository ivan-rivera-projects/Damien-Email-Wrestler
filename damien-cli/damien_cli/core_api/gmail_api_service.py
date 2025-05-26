from .rate_limiter import with_rate_limiting
from .exceptions import SettingsOperationError
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

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
    """
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
            raise GmailApiError(f"Thread {thread_id} not found")
        elif e.resp.status == 403:
            raise GmailApiError("Insufficient permissions to access thread")
        else:
            error_details = e.error_details[0] if e.error_details else {}
            raise GmailApiError(
                f"Failed to get thread details: {error_details.get('message', str(e))}"
            )
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
