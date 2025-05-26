from ..services.tool_registry import tool_registry, ToolDefinition
from ..services.damien_adapter import DamienAdapter # Changed from get_damien_adapter
from damien_cli.core_api import gmail_api_service
from damien_cli.core_api.exceptions import SettingsOperationError
import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Define settings tool schemas
SETTINGS_TOOLS = {
    "damien_get_vacation_settings": ToolDefinition(
        name="damien_get_vacation_settings",
        description="Retrieves current vacation responder settings including enabled status, subject, message body, and schedule.",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False
        },
        handler="get_vacation_settings_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.settings.basic"],
        rate_limit_group="read_operations"
    ),
    
    "damien_update_vacation_settings": ToolDefinition(
        name="damien_update_vacation_settings",
        description="Updates vacation responder settings. Can enable/disable auto-replies and configure message content and schedule.",
        input_schema={
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Whether vacation responder should be enabled"
                },
                "subject": {
                    "type": "string",
                    "description": "Subject line for auto-reply messages (required if enabled=true)",
                    "maxLength": 500
                },
                "body": {
                    "type": "string",
                    "description": "Body text for auto-reply messages (required if enabled=true)",
                    "maxLength": 10000
                },
                "start_time": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Optional start time for vacation responder (ISO 8601 format)"
                },
                "end_time": {
                    "type": "string", 
                    "format": "date-time",
                    "description": "Optional end time for vacation responder (ISO 8601 format)"
                },
                "restrict_to_contacts": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only send auto-replies to people in contacts"
                },
                "restrict_to_domain": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only send auto-replies to people in the same domain"
                }
            },
            "required": ["enabled"],
            "additionalProperties": False
        },
        handler="update_vacation_settings_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.settings.basic"],
        rate_limit_group="write_operations",
        confirmation_required=False
    ),
    
    "damien_get_imap_settings": ToolDefinition(
        name="damien_get_imap_settings",
        description="Retrieves current IMAP access settings for the Gmail account.",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False
        },
        handler="get_imap_settings_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.settings.basic"],
        rate_limit_group="read_operations"
    ),
    
    "damien_update_imap_settings": ToolDefinition(
        name="damien_update_imap_settings",
        description="Updates IMAP access settings including enable/disable and expunge behavior.",
        input_schema={
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Whether IMAP access should be enabled"
                },
                "auto_expunge": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to automatically expunge deleted messages"
                },
                "expunge_behavior": {
                    "type": "string",
                    "enum": ["archive", "trash", "delete"],
                    "default": "archive",
                    "description": "What to do with expunged messages"
                },
                "max_folder_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10000,
                    "description": "Maximum folder size in MB (optional)"
                }
            },
            "required": ["enabled"],
            "additionalProperties": False
        },
        handler="update_imap_settings_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.settings.basic"],
        rate_limit_group="write_operations",
        confirmation_required=True
    ),
    
    "damien_get_pop_settings": ToolDefinition(
        name="damien_get_pop_settings", 
        description="Retrieves current POP access settings for the Gmail account.",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False
        },
        handler="get_pop_settings_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.settings.basic"],
        rate_limit_group="read_operations"
    ),
    
    "damien_update_pop_settings": ToolDefinition(
        name="damien_update_pop_settings",
        description="Updates POP access settings including access window and message disposition.",
        input_schema={
            "type": "object",
            "properties": {
                "access_window": {
                    "type": "string",
                    "enum": ["allMail", "fromNowOn", "disabled"],
                    "description": "When POP clients can access mail"
                },
                "disposition": {
                    "type": "string",
                    "enum": ["leaveInInbox", "archive", "trash", "delete"],
                    "description": "What happens to mail after POP access"
                }
            },
            "required": ["access_window", "disposition"],
            "additionalProperties": False
        },
        handler="update_pop_settings_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.settings.basic"], 
        rate_limit_group="write_operations",
        confirmation_required=True
    )
}

# Handler functions
async def get_vacation_settings_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getting vacation settings."""
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        result = gmail_api_service.get_vacation_settings(gmail_service=gmail_service)
        
        return {
            "success": True,
            "data": {
                **result,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "user_context": context
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_vacation_settings_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error getting vacation settings: {str(e)}",
            "data": None
        }

async def update_vacation_settings_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updating vacation settings."""
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        # Parse datetime strings to Unix timestamps if provided
        start_time = None
        end_time = None
        
        if params.get("start_time"):
            start_dt = datetime.fromisoformat(params["start_time"].replace('Z', '+00:00'))
            start_time = int(start_dt.timestamp() * 1000)  # Convert to milliseconds
        
        if params.get("end_time"):
            end_dt = datetime.fromisoformat(params["end_time"].replace('Z', '+00:00'))
            end_time = int(end_dt.timestamp() * 1000)  # Convert to milliseconds
        
        # Validate required fields for enabled vacation responder
        if params["enabled"] and (not params.get("subject") or not params.get("body")):
            return {
                "success": False,
                "error_message": "Subject and body are required when enabling vacation responder",
                "data": None
            }
        
        result = gmail_api_service.update_vacation_settings(
            gmail_service=gmail_service,
            enabled=params["enabled"],
            subject=params.get("subject"),
            body=params.get("body"),
            start_time=start_time,
            end_time=end_time,
            restrict_to_contacts=params.get("restrict_to_contacts", False),
            restrict_to_domain=params.get("restrict_to_domain", False)
        )
        
        return {
            "success": True,
            "data": {
                **result,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "settings_updated": {
                    "enabled": params["enabled"],
                    "subject": params.get("subject", ""),
                },
                "user_context": context
            }
        }
        
    except SettingsOperationError as e:
        logger.error(f"Settings operation error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Settings operation failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        logger.error(f"Unexpected error in update_vacation_settings_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error updating vacation settings: {str(e)}",
            "data": None
        }

async def get_imap_settings_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getting IMAP settings."""
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        result = gmail_api_service.get_imap_settings(gmail_service=gmail_service)
        
        return {
            "success": True,
            "data": {
                **result,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "user_context": context
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_imap_settings_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error getting IMAP settings: {str(e)}",
            "data": None
        }

async def update_imap_settings_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updating IMAP settings."""
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        result = gmail_api_service.update_imap_settings(
            gmail_service=gmail_service,
            enabled=params["enabled"],
            auto_expunge=params.get("auto_expunge", False),
            expunge_behavior=params.get("expunge_behavior", "archive"),
            max_folder_size=params.get("max_folder_size")
        )
        
        return {
            "success": True,
            "data": {
                **result,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "user_context": context
            }
        }
        
    except Exception as e:
        logger.error(f"Error in update_imap_settings_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error updating IMAP settings: {str(e)}",
            "data": None
        }

async def get_pop_settings_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getting POP settings."""
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        result = gmail_api_service.get_pop_settings(gmail_service=gmail_service)
        
        return {
            "success": True,
            "data": {
                **result,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "user_context": context
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_pop_settings_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error getting POP settings: {str(e)}",
            "data": None
        }

async def update_pop_settings_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updating POP settings."""
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        result = gmail_api_service.update_pop_settings(
            gmail_service=gmail_service,
            access_window=params["access_window"],
            disposition=params["disposition"]
        )
        
        return {
            "success": True,
            "data": {
                **result,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "user_context": context
            }
        }
        
    except Exception as e:
        logger.error(f"Error in update_pop_settings_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error updating POP settings: {str(e)}",
            "data": None
        }

# Register all settings tools
def register_settings_tools():
    """Register all settings-related tools with the tool registry."""
    handlers = {
        "get_vacation_settings_handler": get_vacation_settings_handler,
        "update_vacation_settings_handler": update_vacation_settings_handler,
        "get_imap_settings_handler": get_imap_settings_handler,
        "update_imap_settings_handler": update_imap_settings_handler,
        "get_pop_settings_handler": get_pop_settings_handler,
        "update_pop_settings_handler": update_pop_settings_handler
    }
    
    for tool_name, tool_def in SETTINGS_TOOLS.items():
        handler = handlers[tool_def.handler_name]
        tool_registry.register_tool(tool_def, handler)
    
    logger.info(f"Registered {len(SETTINGS_TOOLS)} settings tools")

# Register the settings tools when this module is imported
register_settings_tools()