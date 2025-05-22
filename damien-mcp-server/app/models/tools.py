"""Pydantic models for specific MCP tool parameters and outputs.

This module defines the Pydantic models that represent the input parameters
and output structures for each Damien MCP tool. These models are used for:

1. Validating tool parameters from MCP clients
2. Providing JSON schemas for the list_tools endpoint
3. Documenting the expected structure of each tool's inputs and outputs
4. Enabling auto-completion and type checking during development

Each tool typically has a corresponding *Params model for inputs and 
an *Output model for its results. The models leverage Pydantic's validation,
field descriptions, and examples to provide comprehensive documentation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Literal

from .mcp_protocol import MCPToolCallInput # Base class for tool inputs

# --- damien_list_emails Tool Models ---

class ListEmailsParams(MCPToolCallInput):
    """Parameters for the damien_list_emails tool.
    
    This model defines the parameters for listing emails from Gmail with
    optional filtering, pagination, and limiting the number of results.
    """
    query: Optional[str] = Field(
        default=None,
        description="Optional Gmail search query string to filter emails (e.g., 'is:unread from:boss@example.com', 'subject:report older_than:7d'). If omitted, lists recent emails. See Gmail search operators: https://support.google.com/mail/answer/7190"
    )
    max_results: Optional[int] = Field(
        default=10,
        description="Optional. Maximum number of email summaries to return in this call. Default is 10. Must be > 0 and <= 100. Higher values may impact performance or hit API rate limits.",
        gt=0,
        le=100
    )
    page_token: Optional[str] = Field(
        default=None,
        description="Optional. An opaque token received from a previous 'damien_list_emails' call to fetch the next page of results."
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "is:unread from:newsletter@example.com subject:important",
                "max_results": 25,
                "page_token": " nextPageTokenFromPreviousCall"
            }
        }
    )

class EmailSummary(BaseModel):
    """Represents a summary of an email message, typically returned by list operations."""
    id: str = Field(description="The unique immutable ID of the email message.")
    thread_id: Optional[str] = Field(default=None, description="The ID of the email thread this message belongs to.")
    subject: Optional[str] = Field(default=None, description="The subject line of the email.")
    from_address: Optional[str] = Field(default=None, alias="from", description="The sender's email address and optional name (e.g., 'John Doe <john.doe@example.com>').")
    snippet: Optional[str] = Field(default=None, description="A short snippet of the email's content.")
    date: Optional[str] = Field(default=None, description="The date the email was received, typically in RFC 3339 format (e.g., '2023-10-26T10:30:00Z').")
    has_attachments: Optional[bool] = Field(default=False, description="Indicates if the email has one or more attachments.")
    label_ids: Optional[List[str]] = Field(default_factory=list, description="List of label IDs applied to this email (e.g., ['INBOX', 'UNREAD', 'IMPORTANT']).")

    model_config = ConfigDict(populate_by_name=True)


class ListEmailsOutput(BaseModel):
    """Output structure for the damien_list_emails tool."""
    email_summaries: List[EmailSummary] = Field(description="A list containing summaries of the fetched emails.")
    next_page_token: Optional[str] = Field(default=None, description="An opaque token for retrieving the next page of results. If null or omitted, there are no more results.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_summaries": [
                    {
                        "id": "18b9e3f2a1b0c8d7",
                        "thread_id": "18b9e3f2a1b0c8d7",
                        "subject": "Project Update Q4",
                        "from_address": "manager@example.com", # Changed from 'from' to 'from_address' to match field name
                        "snippet": "Here is the latest update on Project Phoenix...",
                        "date": "2023-11-15T14:22:01Z",
                        "has_attachments": True,
                        "label_ids": ["INBOX", "IMPORTANT"]
                    },
                    {
                        "id": "18b9e3c5f0a9b7e6",
                        "thread_id": "18b9e3c5f0a9b7e6",
                        "subject": "Team Lunch Next Week",
                        "from_address": "colleague@example.com", # Changed from 'from' to 'from_address'
                        "snippet": "Are you free for a team lunch next Tuesday?",
                        "date": "2023-11-14T10:05:30Z",
                        "has_attachments": False,
                        "label_ids": ["INBOX", "UNREAD"]
                    }
                ],
                "next_page_token": "CiAKGjBpbmJveC1wYWdlLTItMTY2ODg4NjQwMDAwORAB"
            }
        }
    )

# --- damien_get_email_details Tool Models ---

class GetEmailDetailsParams(MCPToolCallInput):
    """Input model for the damien_get_email_details tool."""
    message_id: str = Field(..., description="The unique immutable ID of the email message to retrieve.")
    format: Optional[str] = Field(
        default="full",
        description="Specifies the level of detail for the email. 'full' returns complete data including payload. 'metadata' returns headers and snippet. 'raw' returns the full email as a raw, RFC 2822 formatted string (base64url encoded)."
    )
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "message_id": "18b9e3f2a1b0c8d7",
                "format": "full"
            }
        }
    )

class EmailHeader(BaseModel):
    """Represents a single email header."""
    name: str = Field(description="The name of the header (e.g., 'From', 'Subject', 'Content-Type').")
    value: str = Field(description="The value of the header.")

class EmailPartBody(BaseModel):
    """Represents the body of an email part."""
    attachment_id: Optional[str] = Field(default=None, alias="attachmentId", description="ID of the attachment if this part is an attachment. Can be used with 'get_attachment' tool.")
    size: int = Field(description="Size of the body in bytes.")
    data: Optional[str] = Field(default=None, description="The body data, base64url encoded. Omitted if the body is fetched separately (e.g. for large attachments).")

class EmailPart(BaseModel):
    """Represents a part of a multipart email message."""
    part_id: Optional[str] = Field(default=None, alias="partId", description="The unique ID of this part within the message.")
    mime_type: Optional[str] = Field(default=None, alias="mimeType", description="The MIME type of this part (e.g., 'text/plain', 'image/jpeg').")
    filename: Optional[str] = Field(default=None, description="The filename of this part, if it's an attachment or has a specified filename.")
    headers: Optional[List[EmailHeader]] = Field(default_factory=list, description="List of headers specific to this part.")
    body: Optional[EmailPartBody] = Field(default=None, description="The body of this part.")
    parts: Optional[List['EmailPart']] = Field(default=None, description="For multipart messages (e.g., multipart/alternative, multipart/mixed), this contains a list of nested parts.")

EmailPart.model_rebuild() # Ensure forward reference is resolved

class EmailPayload(BaseModel):
    """Represents the payload of an email message, which can be structured and contain multiple parts."""
    part_id: Optional[str] = Field(default=None, alias="partId", description="The ID of the top-level part of the payload.")
    mime_type: Optional[str] = Field(default=None, alias="mimeType", description="The MIME type of the payload (e.g., 'text/html', 'multipart/alternative').")
    filename: Optional[str] = Field(default=None, description="The filename of the payload, if applicable (usually for single-part messages that are attachments).")
    headers: Optional[List[EmailHeader]] = Field(default_factory=list, description="List of headers for the top-level payload part.")
    body: Optional[EmailPartBody] = Field(default=None, description="The body of the top-level payload part. May be empty if the payload is multipart.")
    parts: Optional[List[EmailPart]] = Field(default=None, description="A list of sub-parts if the payload is multipart.")

class GetEmailDetailsOutput(BaseModel):
    """Output model for the damien_get_email_details tool."""
    id: str = Field(description="The unique immutable ID of the message.")
    thread_id: Optional[str] = Field(default=None, alias="threadId", description="The ID of the thread the message belongs to.")
    label_ids: Optional[List[str]] = Field(default_factory=list, alias="labelIds", description="List of IDs of labels applied to this message.")
    snippet: Optional[str] = Field(default=None, description="A short part of the message text, usually the first few lines.")
    history_id: Optional[str] = Field(default=None, alias="historyId", description="The ID of the last history record that modified this message.")
    internal_date: Optional[str] = Field(default=None, alias="internalDate", description="Internal message creation timestamp (epoch milliseconds) as a string.")
    payload: Optional[EmailPayload] = Field(default=None, description="The parsed email structure (headers, body, parts). Present when format is 'full' or 'metadata' (partially).")
    size_estimate: Optional[int] = Field(default=None, alias="sizeEstimate", description="Estimated size in bytes of the message.")
    raw: Optional[str] = Field(default=None, description="The entire email message in RFC 2822 format, base64url encoded. Present when format is 'raw'.")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra = {
            "example": {
                "id": "18b9e3f2a1b0c8d7",
                "threadId": "18b9e3f2a1b0c8d7",
                "labelIds": ["INBOX", "IMPORTANT", "STARRED"],
                "snippet": "Here is the latest update on Project Phoenix, please review the attached document.",
                "historyId": "987650",
                "internalDate": "1699986121000",
                "payload": {
                    "mimeType": "multipart/alternative",
                    "headers": [
                        {"name": "Subject", "value": "Project Update Q4"},
                        {"name": "From", "value": "Manager <manager@example.com>"},
                        {"name": "To", "value": "Team <team@example.com>"}
                    ],
                    "parts": [
                        {"mimeType": "text/plain", "body": {"size": 150, "data": "SGVsbG8gVGVhbSwKClNlZSBhdHRhY2hlZCBkb2N1bWVudC4uLg=="}},
                        {"mimeType": "text/html", "body": {"size": 300, "data": "PGh0bWw+PGJvZHk+SGVsbG8gVGVhbSw8YnI+ClNlZSBhdHRhY2hlZCBkb2N1bWVudC4uLjwvcD48L2JvZHk+PC9odG1sPg=="}}
                    ]
                },
                "sizeEstimate": 12345
            }
        }
    )

# --- damien_trash_emails Tool Models ---

class TrashEmailsParams(MCPToolCallInput):
    """Input model for the damien_trash_emails tool."""
    message_ids: List[str] = Field(..., description="A list of unique message IDs to be moved to the trash folder.")
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {"message_ids": ["18b9e3f2a1b0c8d7", "18b9e3c5f0a9b7e6"]}
        }
    )

class TrashEmailsOutput(BaseModel):
    """Output model for the damien_trash_emails tool."""
    trashed_count: int = Field(description="The number of emails successfully moved to trash.")
    status_message: str = Field(description="A message indicating the outcome of the operation.")
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {"trashed_count": 2, "status_message": "Successfully moved 2 email(s) to trash."}
        }
    )

# --- damien_label_emails Tool Models ---

class LabelEmailsParams(MCPToolCallInput):
    """Input model for the damien_label_emails tool."""
    message_ids: List[str] = Field(..., description="A list of unique message IDs to apply label changes to.")
    add_label_names: Optional[List[str]] = Field(default=None, description="Optional. List of label names to add to the specified emails. System labels (e.g., 'IMPORTANT', 'STARRED') and custom label names are supported.")
    remove_label_names: Optional[List[str]] = Field(default=None, description="Optional. List of label names to remove from the specified emails. System labels (e.g., 'UNREAD') and custom label names are supported.")
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "message_ids": ["18b9e3f2a1b0c8d7", "18b9e3c5f0a9b7e6"],
                "add_label_names": ["Work", "FollowUp"],
                "remove_label_names": ["UNREAD"]
            }
        }
    )

class LabelEmailsOutput(BaseModel):
    """Output model for the damien_label_emails tool."""
    modified_count: int = Field(description="The number of emails successfully modified.")
    status_message: str = Field(description="A message indicating the outcome of the label modification operation.")
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {"modified_count": 2, "status_message": "Successfully initiated label modification for 2 email(s). Added: ['Work', 'FollowUp']. Removed: ['UNREAD']."}
        }
    )

# --- damien_mark_emails Tool Models ---

class MarkEmailsParams(MCPToolCallInput):
    """Input model for the damien_mark_emails tool."""
    message_ids: List[str] = Field(..., description="A list of unique message IDs to mark as read or unread.")
    mark_as: Literal["read", "unread"] = Field(..., description="Specify whether to mark messages as 'read' or 'unread'. This is case-sensitive.")
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "message_ids": ["18b9e3f2a1b0c8d7", "18b9e3c5f0a9b7e6"],
                "mark_as": "read"
            }
        }
    )

class MarkEmailsOutput(BaseModel):
    """Output model for the damien_mark_emails tool."""
    modified_count: int = Field(description="The number of emails successfully marked as read or unread.")
    status_message: str = Field(description="A message indicating the outcome of the mark operation.")
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {"modified_count": 2, "status_message": "Successfully marked 2 email(s) as read."}
        }
    )

# --- damien_apply_rules Tool Models ---

class ApplyRulesParams(MCPToolCallInput):
    """Input model for the damien_apply_rules tool."""
    gmail_query_filter: Optional[str] = Field(
        default=None,
        description="Optional. Base Gmail query string to narrow down messages for rule application. See Gmail search operators: https://support.google.com/mail/answer/7190"
    )
    rule_ids_to_apply: Optional[List[str]] = Field(
        default=None,
        description="Optional. A list of specific rule IDs to apply. If omitted, all enabled rules stored in Damien are considered for application against the message set."
    )
    dry_run: bool = Field(
        default=False,
        description="If True, the tool will simulate rule application and return a summary of actions that would be taken, without making any actual changes to emails."
    )
    scan_limit: Optional[int] = Field(
        default=None,
        description="Optional. Limits the number of messages scanned from the Gmail query results for rule application. Useful for testing or performing partial runs on large mailboxes."
    )
    date_after: Optional[str] = Field(
        default=None,
        description="Optional. Apply rules only to emails received after this date. Format: YYYY/MM/DD."
    )
    date_before: Optional[str] = Field(
        default=None,
        description="Optional. Apply rules only to emails received before this date. Format: YYYY/MM/DD."
    )
    all_mail: Optional[bool] = Field(
        default=False,
        description="Optional. If True, ignores all other query filters (including `gmail_query_filter` and date ranges) and attempts to apply rules to all mail in the account. Use with extreme caution due to potential for widespread changes."
    )
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "gmail_query_filter": "is:unread from:example.com subject:(report OR update)",
                "rule_ids_to_apply": ["rule_archive_old_newsletters", "rule_label_urgent_reports"],
                "dry_run": True,
                "scan_limit": 500,
                "date_after": "2023/01/01",
                "date_before": "2023/12/31"
            }
        }
    )

class RuleApplicationResult(BaseModel):
    """Detailed result of applying a single rule to a set of messages."""
    rule_id: str = Field(description="The ID of the rule that was applied.")
    rule_name: str = Field(description="The name of the rule that was applied.")
    matched_message_count: int = Field(description="Number of messages that matched this rule's conditions.")
    actions_taken_summary: Dict[str, int] = Field(description="Summary of actions taken by this rule (e.g., {'labeled': 10, 'archived': 5}).")

class ApplyRulesOutput(BaseModel):
    """Output model for the damien_apply_rules tool."""
    total_messages_scanned: int = Field(description="Total number of messages scanned against the rules.")
    total_rules_evaluated: int = Field(description="Total number of unique rules evaluated.")
    total_actions_taken: int = Field(description="Total number of actions (across all rules and messages) taken or that would be taken if not a dry run.")
    dry_run: bool = Field(description="Indicates if the operation was a dry run (simulation).")
    results_by_rule: List[RuleApplicationResult] = Field(description="A list detailing the outcome of each rule that was applied or matched.")
    overall_status_message: str = Field(description="A summary message of the rule application process.")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "total_messages_scanned": 480,
                "total_rules_evaluated": 2,
                "total_actions_taken": 15,
                "dry_run": True,
                "results_by_rule": [
                    {
                        "rule_id": "rule_archive_old_newsletters",
                        "rule_name": "Archive Old Newsletters",
                        "matched_message_count": 10,
                        "actions_taken_summary": {"archived": 10}
                    },
                    {
                        "rule_id": "rule_label_urgent_reports",
                        "rule_name": "Label Urgent Reports",
                        "matched_message_count": 5,
                        "actions_taken_summary": {"labeled_urgent": 5}
                    }
                ],
                "overall_status_message": "Dry run complete. 15 actions would have been taken on 15 messages across 2 rules."
            }
        }
    )

# --- Rule Definition Model (used by ListRulesOutput and AddRuleOutput) ---
class RuleConditionModel(BaseModel):
    """Defines a single condition within a rule."""
    field: str = Field(description="The email field to check (e.g., 'subject', 'from', 'body', 'to', 'cc', 'label', 'has_attachment', 'size').")
    operator: str = Field(description="The operator to apply (e.g., 'contains', 'not_contains', 'equals', 'not_equals', 'starts_with', 'ends_with', 'regex_match', 'greater_than', 'less_than').")
    value: Any = Field(description="The value to compare against. Type depends on field and operator (e.g., string for subject, int for size in bytes).")

class RuleActionModel(BaseModel):
    """Defines a single action to be taken if a rule's conditions are met."""
    type: str = Field(description="The type of action (e.g., 'add_label', 'remove_label', 'archive', 'mark_as_read', 'mark_as_unread', 'trash'). Actual support depends on CLI implementation.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action, e.g., {'label_name': 'MyLabel'} for 'add_label'.")

class RuleModelInput(BaseModel):
    """Represents the input structure for creating or updating a filtering rule.
    Server-generated fields like 'id', 'created_at', 'updated_at' should be omitted."""
    name: str = Field(description="User-defined name for the rule.")
    description: Optional[str] = Field(default=None, description="Optional detailed description of the rule's purpose.")
    is_enabled: bool = Field(default=True, description="Whether the rule is currently active and will be applied.")
    conditions: List[RuleConditionModel] = Field(description="A list of conditions that must be met for the rule to trigger.")
    condition_conjunction: Literal["AND", "OR"] = Field(default="AND", description="How multiple conditions are combined ('AND' means all must be true, 'OR' means any can be true).")
    actions: List[RuleActionModel] = Field(description="A list of actions to perform if the conditions are met.")
    # id, created_at, updated_at are intentionally omitted as they are server-generated or not part of input.

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Archive Old Newsletters",
                "description": "Automatically archives newsletters older than 30 days.",
                "is_enabled": True,
                "conditions": [
                    {"field": "from_address", "operator": "contains", "value": "newsletter@"},
                    {"field": "date", "operator": "older_than_days", "value": 30}
                ],
                "condition_conjunction": "AND",
                "actions": [
                    {"type": "archive", "parameters": {}},
                    {"type": "mark_as_read", "parameters": {}}
                ]
            }
        }
    )

class RuleModelOutput(BaseModel):
    """Represents a single filtering rule as defined in Damien, including server-generated fields."""
    id: str = Field(description="Unique identifier for the rule.")
    name: str = Field(description="User-defined name for the rule.")
    description: Optional[str] = Field(default=None, description="Optional detailed description of the rule's purpose.")
    is_enabled: bool = Field(default=True, description="Whether the rule is currently active and will be applied.")
    conditions: List[RuleConditionModel] = Field(description="A list of conditions that must be met for the rule to trigger.")
    condition_conjunction: Literal["AND", "OR"] = Field(default="AND", description="How multiple conditions are combined ('AND' means all must be true, 'OR' means any can be true).")
    actions: List[RuleActionModel] = Field(description="A list of actions to perform if the conditions are met.")
    created_at: Optional[str] = Field(default=None, description="Timestamp of when the rule was created (ISO 8601 format).")
    updated_at: Optional[str] = Field(default=None, description="Timestamp of when the rule was last updated (ISO 8601 format).")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "rule_123xyz",
                "name": "Archive Old Newsletters",
                "description": "Automatically archives newsletters older than 30 days.",
                "is_enabled": True,
                "conditions": [
                    {"field": "from_address", "operator": "contains", "value": "newsletter@"},
                    {"field": "date", "operator": "older_than_days", "value": 30}
                ],
                "condition_conjunction": "AND",
                "actions": [
                    {"type": "archive", "parameters": {}},
                    {"type": "mark_as_read", "parameters": {}}
                ],
                "created_at": "2023-01-10T10:00:00Z",
                "updated_at": "2023-05-15T11:30:00Z"
            }
        }
    )

# --- damien_list_rules Tool Models ---

class ListRulesOutput(BaseModel):
    """Output model for the damien_list_rules tool."""
    rules: List[RuleModelOutput] = Field(description="A list of all configured filtering rules in Damien.")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rules": [
                    RuleModelOutput.model_config["json_schema_extra"]["example"],
                    {
                        "id": "rule_456abc",
                        "name": "Label Important Client Emails",
                        "description": "Adds 'IMPORTANT_CLIENT' label to emails from clientdomain.com",
                        "is_enabled": True,
                        "conditions": [{"field": "from_address", "operator": "ends_with", "value": "@clientdomain.com"}],
                        "condition_conjunction": "AND",
                        "actions": [{"type": "add_label", "parameters": {"label_name": "IMPORTANT_CLIENT"}}],
                        "created_at": "2022-11-01T09:00:00Z",
                        "updated_at": "2023-03-20T14:45:00Z"
                    }
                ]
            }
        }
    )


# --- damien_add_rule Tool Models ---

class AddRuleParams(MCPToolCallInput):
    """Input model for the damien_add_rule tool."""
    rule_definition: RuleModelInput = Field(
        description="A Pydantic model representing the rule to be added. Server will generate 'id', 'created_at', 'updated_at'. See RuleModelInput for structure."
    )
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "rule_definition": { # This example should match RuleModelInput structure
                    "name": "Forward Support Tickets",
                    "description": "Forwards emails with 'support ticket' in subject to support@example.com.",
                    "is_enabled": True,
                    "conditions": [{"field": "subject", "operator": "contains", "value": "support ticket"}],
                    "condition_conjunction": "AND",
                    "actions": [{"type": "forward_to", "parameters": {"email_address": "support@example.com"}}]
                }
            }
        }
    )

class AddRuleOutput(RuleModelOutput):
    """Output model for the damien_add_rule tool. Returns the full definition of the newly added rule, including its server-generated ID."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "rule_new789",
                "name": "Forward Support Tickets", # Example name from previous AddRuleParams
                "description": "Forwards emails with 'support ticket' in subject to support@example.com.",
                "is_enabled": True,
                "conditions": [{"field": "subject", "operator": "contains", "value": "support ticket"}],
                "condition_conjunction": "AND",
                "actions": [{"type": "forward_to", "parameters": {"email_address": "support@example.com"}}],
                "created_at": "2024-05-21T10:00:00Z",
                "updated_at": "2024-05-21T10:00:00Z"
            }
        }
    )


# --- damien_delete_rule Tool Models ---

class DeleteRuleParams(MCPToolCallInput):
    """Input model for the damien_delete_rule tool."""
    rule_identifier: str = Field(..., description="The unique ID or the exact name of the rule to be deleted.")
    model_config = ConfigDict(
        json_schema_extra = {"example": {"rule_identifier": "rule_archive_old_newsletters_or_id_string"}}
    )

class DeleteRuleOutput(BaseModel):
    """Output model for the damien_delete_rule tool."""
    status_message: str = Field(description="A message indicating the outcome of the deletion operation.")
    deleted_rule_identifier: str = Field(description="The ID or name of the rule that was confirmed deleted.")
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {"status_message": "Successfully deleted rule: rule_archive_old_newsletters_or_id_string", "deleted_rule_identifier": "rule_archive_old_newsletters_or_id_string"}
        }
    )

# --- damien_delete_emails_permanently Tool Models ---

class DeleteEmailsPermanentlyParams(MCPToolCallInput):
    """Input model for the damien_delete_emails_permanently tool. This action is IRREVERSIBLE."""
    message_ids: List[str] = Field(..., description="A list of unique message IDs to be permanently deleted. This action cannot be undone.")
    model_config = ConfigDict(
        json_schema_extra = {"example": {"message_ids": ["msg_id_to_perm_delete_1", "msg_id_to_perm_delete_2"]}}
    )

class DeleteEmailsPermanentlyOutput(BaseModel):
    """Output model for the damien_delete_emails_permanently tool."""
    deleted_count: int = Field(description="The number of emails successfully and permanently deleted.")
    status_message: str = Field(description="A message indicating the outcome of the permanent deletion operation.")
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {"deleted_count": 2, "status_message": "Successfully initiated permanent deletion for 2 email(s)."}
        }
    )