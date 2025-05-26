from pydantic import BaseModel, Field, ConfigDict, field_validator, validator, ValidationInfo
from typing import List, Optional, Dict, Any, Literal

from .mcp_protocol import MCPToolCallInput # Base class for tool inputs

# --- Drafts Tool Models ---

class ListDraftsParams(MCPToolCallInput):
    """Parameters for listing draft emails."""
    query: Optional[str] = Field(
        default=None,
        description="Optional Gmail search query to filter drafts (e.g., 'subject:urgent')"
    )
    max_results: Optional[int] = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of drafts to return (1-100)"
    )
    page_token: Optional[str] = Field(
        default=None,
        description="Token for fetching next page of results"
    )
    include_headers: Optional[List[str]] = Field(
        default=None,
        description="Optional list of header names to include in the response. Can be a JSON string list."
    )

    @field_validator('include_headers', mode='before')
    def parse_include_headers(cls, v):
        if isinstance(v, str):
            try:
                import json
                parsed_v = json.loads(v)
                if isinstance(parsed_v, list) and all(isinstance(item, str) for item in parsed_v):
                    return parsed_v
                else:
                    raise ValueError("include_headers string must be a valid JSON array of strings.")
            except json.JSONDecodeError:
                raise ValueError("include_headers parsing error: not a valid JSON string.")
        elif v is not None and not (isinstance(v, list) and all(isinstance(item, str) for item in v)):
            raise ValueError("include_headers must be a list of strings or a JSON string array.")
        return v

class GetDraftDetailsParams(MCPToolCallInput):
    """Parameters for getting draft details."""
    message_id: str = Field( # Changed from draft_id
        ...,
        description="The unique ID of the draft/message to retrieve"
    )
    format: Optional[str] = Field(
        default="full",
        pattern="^(full|metadata|minimal)$",
        description="Level of detail to retrieve (full, metadata, minimal)"
    )
    include_headers: Optional[List[str]] = Field(
        default=None,
        description="Optional list of header names to include in the response. Can be a JSON string list."
    )

    @field_validator('include_headers', mode='before')
    def parse_include_headers_for_details(cls, v): # Renamed to avoid clash if in same scope, though class scope is fine
        if isinstance(v, str):
            try:
                import json
                parsed_v = json.loads(v)
                if isinstance(parsed_v, list) and all(isinstance(item, str) for item in parsed_v):
                    return parsed_v
                else:
                    raise ValueError("include_headers string must be a valid JSON array of strings.")
            except json.JSONDecodeError:
                raise ValueError("include_headers parsing error: not a valid JSON string.")
        elif v is not None and not (isinstance(v, list) and all(isinstance(item, str) for item in v)):
            raise ValueError("include_headers must be a list of strings or a JSON string array.")
        return v

class CreateDraftParams(MCPToolCallInput):
    """Parameters for creating a new draft email."""
    to: List[str] = Field(
        ...,
        min_items=1,
        description="List of recipient email addresses"
    )
    subject: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Email subject line"
    )
    body: str = Field(
        ...,
        min_length=1,
        description="Email body content (plain text)"
    )
    cc: Optional[List[str]] = Field(
        default=None,
        description="Optional CC recipients"
    )
    bcc: Optional[List[str]] = Field(
        default=None,
        description="Optional BCC recipients"
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Optional thread ID for replies"
    )
    
    @field_validator('to', 'cc', 'bcc', mode='before')
    def validate_email_addresses(cls, v):
        if v:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            for email in v:
                if not re.match(email_pattern, email):
                    raise ValueError(f"Invalid email address: {email}")
        return v

# --- Rules Tool Models (Placeholder) ---

class ApplyRulesParams(MCPToolCallInput):
    """Parameters for applying rules. (Placeholder)"""
    rule_ids_to_apply: Optional[List[str]] = Field(default=None, description="List of rule IDs to apply.")
    gmail_query_filter: Optional[str] = Field(default=None) # From test
    dry_run: bool = Field(default=False) # From test
    scan_limit: Optional[int] = Field(default=None) # From test
    date_after: Optional[str] = Field(default=None) # From test
    date_before: Optional[str] = Field(default=None) # From test
    all_mail: bool = Field(default=False) # From test
    include_detailed_ids: bool = Field(default=False) # From adapter usage

    @field_validator('rule_ids_to_apply', mode='before')
    def parse_rule_ids_list(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                import json
                parsed_v = json.loads(v)
                if isinstance(parsed_v, list) and all(isinstance(item, str) for item in parsed_v):
                    return parsed_v
                else:
                    raise ValueError("rule_ids_to_apply string must be a valid JSON array of strings.")
            except json.JSONDecodeError:
                raise ValueError("rule_ids_to_apply parsing error: not a valid JSON string.")
        elif not isinstance(v, list) or not all(isinstance(item, str) for item in v):
            raise ValueError("rule_ids_to_apply must be a list of strings or a JSON string array.")
        return v
# --- Settings Tool Models ---

class GetVacationSettingsParams(MCPToolCallInput):
    """Parameters for getting vacation responder settings."""
    # No parameters needed

class UpdateVacationSettingsParams(MCPToolCallInput):
    """Parameters for updating vacation responder settings."""
    enabled: bool = Field(..., description="Whether vacation responder should be enabled")
    subject: Optional[str] = Field(None, max_length=500, description="Subject line for auto-reply messages")
    body: Optional[str] = Field(None, max_length=10000, description="Body text for auto-reply messages")
    start_time: Optional[str] = Field(None, description="Optional start time for vacation responder (ISO 8601 format)")
    end_time: Optional[str] = Field(None, description="Optional end time for vacation responder (ISO 8601 format)")
    restrict_to_contacts: Optional[bool] = Field(False, description="Only send auto-replies to people in contacts")
    restrict_to_domain: Optional[bool] = Field(False, description="Only send auto-replies to people in the same domain")

    @field_validator('subject', 'body')
    def required_if_enabled(cls, v, info: ValidationInfo):
        if info.data.get('enabled') and not v:
            raise ValueError(f"{info.field_name} is required when vacation responder is enabled")
        return v

class GetImapSettingsParams(MCPToolCallInput):
    """Parameters for getting IMAP settings."""
    # No parameters needed

class UpdateImapSettingsParams(MCPToolCallInput):
    """Parameters for updating IMAP settings."""
    enabled: bool = Field(..., description="Whether IMAP access should be enabled")
    auto_expunge: Optional[bool] = Field(False, description="Whether to auto-expunge deleted messages")
    expunge_behavior: Optional[Literal['archive', 'trash', 'delete']] = Field('archive', description="What to do with expunged messages")
    max_folder_size: Optional[int] = Field(None, description="Maximum folder size in MB")

class GetPopSettingsParams(MCPToolCallInput):
    """Parameters for getting POP settings."""
    # No parameters needed

class UpdatePopSettingsParams(MCPToolCallInput):
    """Parameters for updating POP settings."""
    access_window: Literal['allMail', 'fromNowOn', 'disabled'] = Field(..., description="When POP clients can access mail")
    disposition: Literal['leaveInInbox', 'archive', 'trash', 'delete'] = Field(..., description="What happens to mail after POP access")
# --- Other Email Tool Models (Placeholders) ---

class TrashEmailsParams(MCPToolCallInput):
    """Parameters for trashing emails. (Placeholder)"""
    message_ids: List[str] = Field(..., description="List of message IDs to trash.")

    @field_validator('message_ids', mode='before')
    def parse_message_ids_list(cls, v):
        if isinstance(v, str):
            try:
                import json
                parsed_v = json.loads(v)
                if isinstance(parsed_v, list) and all(isinstance(item, str) for item in parsed_v):
                    return parsed_v
                else:
                    raise ValueError("message_ids string must be a valid JSON array of strings.")
            except json.JSONDecodeError:
                raise ValueError("message_ids parsing error: not a valid JSON string.")
        elif not isinstance(v, list) or not all(isinstance(item, str) for item in v):
            raise ValueError("message_ids must be a list of strings or a JSON string array.")
        return v

class LabelEmailsParams(MCPToolCallInput):
    """Parameters for labeling emails. (Placeholder)"""
    message_ids: List[str] = Field(..., description="List of message IDs to label.")
    add_label_names: Optional[List[str]] = Field(default=None, description="Labels to add.")
    remove_label_names: Optional[List[str]] = Field(default=None, description="Labels to remove.")

    @field_validator('message_ids', mode='before')
    def parse_message_ids_list(cls, v):
        if isinstance(v, str):
            try:
                import json
                parsed_v = json.loads(v)
                if isinstance(parsed_v, list) and all(isinstance(item, str) for item in parsed_v):
                    return parsed_v
                else:
                    raise ValueError("message_ids string must be a valid JSON array of strings.")
            except json.JSONDecodeError:
                raise ValueError("message_ids parsing error: not a valid JSON string.")
        elif not isinstance(v, list) or not all(isinstance(item, str) for item in v):
            raise ValueError("message_ids must be a list of strings or a JSON string array.")
        return v

    @field_validator('add_label_names', 'remove_label_names', mode='before')
    def parse_label_names_list(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                import json
                parsed_v = json.loads(v)
                if isinstance(parsed_v, list) and all(isinstance(item, str) for item in parsed_v):
                    return parsed_v
                else:
                    raise ValueError("Label names string must be a valid JSON array of strings.")
            except json.JSONDecodeError:
                raise ValueError("Label names parsing error: not a valid JSON string.")
        elif not isinstance(v, list) or not all(isinstance(item, str) for item in v):
            raise ValueError("Label names must be a list of strings or a JSON string array.")
        return v

class MarkEmailsParams(MCPToolCallInput):
    """Parameters for marking emails. (Placeholder)"""
    message_ids: List[str] = Field(..., description="List of message IDs to mark.")
    mark_as: Literal["read", "unread"] = Field(..., description="Mark as 'read' or 'unread'.")

    @field_validator('message_ids', mode='before')
    def parse_message_ids_list(cls, v):
        if isinstance(v, str):
            try:
                import json
                parsed_v = json.loads(v)
                if isinstance(parsed_v, list) and all(isinstance(item, str) for item in parsed_v):
                    return parsed_v
                else:
                    raise ValueError("message_ids string must be a valid JSON array of strings.")
            except json.JSONDecodeError:
                raise ValueError("message_ids parsing error: not a valid JSON string.")
        elif not isinstance(v, list) or not all(isinstance(item, str) for item in v):
            raise ValueError("message_ids must be a list of strings or a JSON string array.")
        return v

class DeleteEmailsPermanentlyParams(MCPToolCallInput):
    """Parameters for permanently deleting emails. (Placeholder)"""
    message_ids: List[str] = Field(..., description="List of message IDs to permanently delete.")

    @field_validator('message_ids', mode='before')
    def parse_message_ids_list(cls, v):
        if isinstance(v, str):
            try:
                import json
                parsed_v = json.loads(v)
                if isinstance(parsed_v, list) and all(isinstance(item, str) for item in parsed_v):
                    return parsed_v
                else:
                    raise ValueError("message_ids string must be a valid JSON array of strings.")
            except json.JSONDecodeError:
                raise ValueError("message_ids parsing error: not a valid JSON string.")
        elif not isinstance(v, list) or not all(isinstance(item, str) for item in v):
            raise ValueError("message_ids must be a list of strings or a JSON string array.")
        return v

# --- Rules Tool Models (Actual definitions might be more complex) ---

class ListRulesParams(MCPToolCallInput):
    """Parameters for listing rules. (Placeholder)"""
    summary_view: bool = Field(default=True, description="Return summary view or full details.")

class GetRuleDetailsParams(MCPToolCallInput):
    """Parameters for getting rule details. (Placeholder)"""
    rule_id_or_name: str = Field(..., description="ID or name of the rule.")

class RuleDefinitionModel(BaseModel): # A sub-model for AddRuleParams
    name: str
    description: Optional[str] = None
    is_enabled: bool = True
    conditions: List[Dict[str, Any]] # Simplified
    condition_conjunction: Literal["AND", "OR"] = "AND"
    actions: List[Dict[str, Any]] # Simplified

class AddRuleParams(MCPToolCallInput):
    """Parameters for adding a rule. (Placeholder)"""
    rule_definition: RuleDefinitionModel

class DeleteRuleParams(MCPToolCallInput):
    """Parameters for deleting a rule. (Placeholder)"""
    rule_identifier: str = Field(..., description="ID or name of the rule to delete.")


# --- Output Models (Placeholders) ---

class ListEmailsOutput(BaseModel): # Renamed from ListDraftsOutput
    """Output for listing drafts. (Placeholder)"""
    email_summaries: List[Dict[str, Any]] = []
    next_page_token: Optional[str] = None

class GetEmailDetailsOutput(BaseModel): # Renamed from GetDraftDetailsOutput
    """Output for getting draft details. (Placeholder)"""
    id: str
    thread_id: Optional[str] = None
    subject: Optional[str] = None
    # Add more fields as needed

class TrashEmailsOutput(BaseModel):
    """Output for trashing emails. (Placeholder)"""
    trashed_count: int = 0
    status_message: str = ""

class LabelEmailsOutput(BaseModel):
    """Output for labeling emails. (Placeholder)"""
    modified_count: int = 0
    status_message: str = ""

class MarkEmailsOutput(BaseModel):
    """Output for marking emails. (Placeholder)"""
    modified_count: int = 0
    status_message: str = ""

class ApplyRulesOutput(BaseModel):
    """Output for applying rules. (Placeholder)"""
    summary: Dict[str, Any] = {}

class ListRulesOutput(BaseModel):
    """Output for listing rules. (Placeholder)"""
    rules: List[Dict[str, Any]] = []

class RuleModelOutput(BaseModel): # For GetRuleDetails
    """Output for rule details - typically the full rule model. (Placeholder)"""
    id: str
    name: str
    # ... other fields from RuleDefinitionModel

class AddRuleOutput(BaseModel):
    """Output for adding a rule. (Placeholder)"""
    id: str
    name: str
    # ... other fields

class DeleteRuleOutput(BaseModel):
    """Output for deleting a rule. (Placeholder)"""
    status_message: str = ""
    deleted_rule_identifier: str

class DeleteEmailsPermanentlyOutput(BaseModel):
    """Output for permanently deleting emails. (Placeholder)"""
    deleted_count: int = 0
    status_message: str = ""