from ..services.tool_registry import tool_registry, ToolDefinition
from ..services.damien_adapter import DamienAdapter
from damien_cli.core_api import gmail_api_service
from damien_cli.core_api.exceptions import GmailApiError
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Define draft tool schemas
DRAFT_TOOLS = {
    "damien_create_draft": ToolDefinition(
        name="damien_create_draft",
        description="Creates a new draft email with specified recipients, subject, and body content.",
        input_schema={
            "type": "object",
            "properties": {
                "to": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "List of recipient email addresses",
                    "minItems": 1,
                    "maxItems": 100
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line",
                    "maxLength": 500
                },
                "body": {
                    "type": "string",
                    "description": "Email body content",
                    "maxLength": 10000
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "Optional CC recipient email addresses",
                    "maxItems": 50
                },
                "bcc": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "Optional BCC recipient email addresses",
                    "maxItems": 50
                },
                "thread_id": {
                    "type": "string",
                    "description": "Optional thread ID for creating a reply draft"
                }
            },
            "required": ["to", "subject", "body"],
            "additionalProperties": False
        },
        handler="create_draft_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.compose"],
        rate_limit_group="write_operations"
    ),
    
    "damien_update_draft": ToolDefinition(
        name="damien_update_draft",
        description="Updates an existing draft email with new content.",
        input_schema={
            "type": "object",
            "properties": {
                "draft_id": {
                    "type": "string",
                    "description": "ID of the draft to update"
                },
                "to": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "Updated recipient email addresses",
                    "maxItems": 100
                },
                "subject": {
                    "type": "string",
                    "description": "Updated email subject line",
                    "maxLength": 500
                },
                "body": {
                    "type": "string",
                    "description": "Updated email body content",
                    "maxLength": 10000
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "Updated CC recipient email addresses",
                    "maxItems": 50
                },
                "bcc": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "Updated BCC recipient email addresses",
                    "maxItems": 50
                }
            },
            "required": ["draft_id"],
            "additionalProperties": False
        },
        handler="update_draft_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.compose"],
        rate_limit_group="write_operations"
    ),
    
    "damien_send_draft": ToolDefinition(
        name="damien_send_draft",
        description="Sends an existing draft email immediately.",
        input_schema={
            "type": "object",
            "properties": {
                "draft_id": {
                    "type": "string",
                    "description": "ID of the draft to send"
                }
            },
            "required": ["draft_id"],
            "additionalProperties": False
        },
        handler="send_draft_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.send"],
        rate_limit_group="write_operations",
        confirmation_required=True
    ),
    
    "damien_list_drafts": ToolDefinition(
        name="damien_list_drafts",
        description="Lists draft emails with optional filtering and pagination support.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional Gmail search query to filter drafts (e.g., 'subject:urgent')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of drafts to return",
                    "minimum": 1,
                    "maximum": 500,
                    "default": 100
                },
                "page_token": {
                    "type": "string",
                    "description": "Token for fetching the next page of results"
                }
            },
            "additionalProperties": False
        },
        handler="list_drafts_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        rate_limit_group="read_operations"
    ),
    
    "damien_get_draft_details": ToolDefinition(
        name="damien_get_draft_details",
        description="Retrieves detailed information about a specific draft email.",
        input_schema={
            "type": "object",
            "properties": {
                "draft_id": {
                    "type": "string",
                    "description": "ID of the draft to retrieve"
                },
                "format": {
                    "type": "string",
                    "enum": ["full", "metadata", "minimal"],
                    "default": "full",
                    "description": "Level of detail to retrieve"
                }
            },
            "required": ["draft_id"],
            "additionalProperties": False
        },
        handler="get_draft_details_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        rate_limit_group="read_operations"
    ),
    
    "damien_delete_draft": ToolDefinition(
        name="damien_delete_draft",
        description="Permanently deletes a draft email.",
        input_schema={
            "type": "object",
            "properties": {
                "draft_id": {
                    "type": "string",
                    "description": "ID of the draft to delete"
                }
            },
            "required": ["draft_id"],
            "additionalProperties": False
        },
        handler="delete_draft_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.compose"],
        rate_limit_group="write_operations",
        confirmation_required=True
    )
}

# Handler functions
async def create_draft_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for creating draft emails."""
    try:
        # Get authenticated Gmail service from Damien core_api
        from damien_cli.core_api import gmail_api_service as damien_gmail_service
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        # Get the Gmail service client
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        result = damien_gmail_service.create_draft(
            gmail_service=gmail_service,
            to_addresses=params["to"],
            subject=params["subject"],
            body=params["body"],
            cc=params.get("cc"),
            bcc=params.get("bcc"),
            thread_id=params.get("thread_id")
        )
        
        # Enhance result with user-friendly formatting
        enhanced_result = {
            "success": True,
            "data": {
                **result,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "recipients": {
                    "to": params["to"],
                    "cc": params.get("cc", []),
                    "bcc": params.get("bcc", [])
                },
                "user_context": {
                    "session_id": context.get("session_id"),
                    "user_id": context.get("user_id")
                }
            }
        }
        
        return enhanced_result
        
    except Exception as e:
        logger.error(f"Error in create_draft_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error creating draft: {str(e)}",
            "data": None
        }

async def update_draft_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updating draft emails."""
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        result = gmail_api_service.update_draft(
            gmail_service=gmail_service,
            draft_id=params["draft_id"],
            to_addresses=params.get("to"),
            subject=params.get("subject"),
            body=params.get("body"),
            cc=params.get("cc"),
            bcc=params.get("bcc")
        )
        
        return {
            "success": True,
            "data": {
                **result,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "changes_made": {key: value for key, value in params.items() if key != "draft_id" and value is not None},
                "user_context": context
            }
        }
        
    except Exception as e:
        logger.error(f"Error in update_draft_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error updating draft: {str(e)}",
            "data": None
        }

async def send_draft_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for sending draft emails."""
    try:
        damien_adapter = DamienAdapter()
        gmail_service = await damien_adapter.get_gmail_service()
        
        result = gmail_api_service.send_draft(
            gmail_service=gmail_service,
            draft_id=params["draft_id"]
        )
        
        # Enhance result with sending information
        enhanced_result = {
            **result,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "draft_id": params["draft_id"],
            "status": "sent",
            "user_context": {
                "session_id": context.get("session_id"),
                "user_id": context.get("user_id")
            }
        }
        
        return enhanced_result
        
    except Exception as e:
        logger.error(f"Error in send_draft_handler: {str(e)}")
        raise

async def list_drafts_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for listing draft emails."""
    try:
        damien_adapter = DamienAdapter()
        gmail_service = await damien_adapter.get_gmail_service()
        
        result = gmail_api_service.list_drafts(
            gmail_service=gmail_service,
            query=params.get("query"),
            max_results=params.get("max_results", 100),
            page_token=params.get("page_token")
        )
        
        # Enhance result with user-friendly formatting
        enhanced_result = {
            **result,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "total_drafts": len(result.get("drafts", [])),
            "query_used": params.get("query", "No filter"),
            "user_context": {
                "session_id": context.get("session_id"),
                "user_id": context.get("user_id")
            }
        }
        
        return enhanced_result
        
    except Exception as e:
        logger.error(f"Error in list_drafts_handler: {str(e)}")
        raise

async def get_draft_details_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getting draft details."""
    try:
        damien_adapter = DamienAdapter()
        gmail_service = await damien_adapter.get_gmail_service()
        
        result = gmail_api_service.get_draft_details(
            gmail_service=gmail_service,
            draft_id=params["draft_id"],
            format=params.get("format", "full")
        )
        
        # Enhance result with user-friendly formatting
        enhanced_result = {
            **result,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "format_used": params.get("format", "full"),
            "user_context": {
                "session_id": context.get("session_id"),
                "user_id": context.get("user_id")
            }
        }
        
        return enhanced_result
        
    except Exception as e:
        logger.error(f"Error in get_draft_details_handler: {str(e)}")
        raise

async def delete_draft_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for deleting draft emails."""
    try:
        damien_adapter = DamienAdapter()
        gmail_service = await damien_adapter.get_gmail_service()
        
        result = gmail_api_service.delete_draft(
            gmail_service=gmail_service,
            draft_id=params["draft_id"]
        )
        
        # Enhance result with deletion information
        enhanced_result = {
            **result,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "draft_id": params["draft_id"],
            "user_context": {
                "session_id": context.get("session_id"),
                "user_id": context.get("user_id")
            }
        }
        
        return enhanced_result
        
    except Exception as e:
        logger.error(f"Error in delete_draft_handler: {str(e)}")
        raise

# Register all draft tools
def register_draft_tools():
    """Register all draft-related tools with the tool registry."""
    handlers = {
        "create_draft_handler": create_draft_handler,
        "update_draft_handler": update_draft_handler,
        "send_draft_handler": send_draft_handler,
        "list_drafts_handler": list_drafts_handler,
        "get_draft_details_handler": get_draft_details_handler,
        "delete_draft_handler": delete_draft_handler
    }
    
    for tool_name, tool_def in DRAFT_TOOLS.items():
        handler = handlers[tool_def.handler_name]  # Fixed: use handler_name
        tool_registry.register_tool(tool_def, handler)
    
    logger.info(f"Registered {len(DRAFT_TOOLS)} draft tools")

# Register the draft tools when this module is imported
register_draft_tools()
