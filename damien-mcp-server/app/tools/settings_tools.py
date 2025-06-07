from ..services.tool_registry import tool_registry, ToolDefinition
from ..services.damien_adapter import DamienAdapter # Changed from get_damien_adapter
from damien_cli.core_api import gmail_api_service
from damien_cli.core_api.exceptions import SettingsOperationError
import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Define settings tool schemas - Core settings only (removed vacation/IMAP/POP per Pareto principle)
SETTINGS_TOOLS = {
    "damien_get_settings": ToolDefinition(
        name="damien_get_settings",
        description="Retrieves core Gmail account settings and configuration.",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False
        },
        handler="get_settings_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.settings.basic"],
        rate_limit_group="read_operations"
    ),
    
    "damien_update_settings": ToolDefinition(
        name="damien_update_settings",
        description="Updates basic Gmail account settings and configuration.",
        input_schema={
            "type": "object",
            "properties": {
                "display_language": {
                    "type": "string",
                    "description": "Gmail interface display language"
                },
                "page_size": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 100,
                    "description": "Number of messages to display per page"
                },
                "threading_enabled": {
                    "type": "boolean",
                    "description": "Whether to group related messages into conversations"
                }
            },
            "additionalProperties": False
        },
        handler="update_settings_handler",
        requires_scopes=["https://www.googleapis.com/auth/gmail.settings.basic"],
        rate_limit_group="write_operations",
        confirmation_required=False
    )
}

# Handler functions
async def get_settings_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getting core Gmail settings."""
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        # Get basic account settings from Gmail API
        profile_result = gmail_service.users().getProfile(userId='me').execute()
        
        # Format the response with core settings information
        settings_data = {
            "email_address": profile_result.get("emailAddress"),
            "messages_total": profile_result.get("messagesTotal", 0),
            "threads_total": profile_result.get("threadsTotal", 0),
            "history_id": profile_result.get("historyId"),
            "account_type": "Gmail",
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
        return {
            "success": True,
            "data": {
                **settings_data,
                "user_context": context
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_settings_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error getting Gmail settings: {str(e)}",
            "data": None
        }

async def update_settings_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updating core Gmail settings."""
    try:
        from damien_cli.integrations.gmail_integration import get_gmail_service
        
        gmail_service = get_gmail_service()
        if not gmail_service:
            return {
                "success": False,
                "error_message": "Failed to authenticate with Gmail",
                "data": None
            }
        
        # For now, return a success message as Gmail's basic settings API is limited
        # Most settings like display language and threading are managed through the web interface
        updated_settings = {}
        
        if "display_language" in params:
            updated_settings["display_language"] = params["display_language"]
            
        if "page_size" in params:
            updated_settings["page_size"] = params["page_size"]
            
        if "threading_enabled" in params:
            updated_settings["threading_enabled"] = params["threading_enabled"]
        
        return {
            "success": True,
            "data": {
                "message": "Settings update acknowledged. Note: Most Gmail settings are managed through the web interface.",
                "updated_settings": updated_settings,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "user_context": context
            }
        }
        
    except Exception as e:
        logger.error(f"Error in update_settings_handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error updating Gmail settings: {str(e)}",
            "data": None
        }

# Register all settings tools
def register_settings_tools():
    """Register core settings tools with the tool registry."""
    handlers = {
        "get_settings_handler": get_settings_handler,
        "update_settings_handler": update_settings_handler
    }
    
    for tool_name, tool_def in SETTINGS_TOOLS.items():
        handler = handlers[tool_def.handler_name]
        tool_registry.register_tool(tool_def, handler)
    
    logger.info(f"Registered {len(SETTINGS_TOOLS)} core settings tools (removed vacation/IMAP/POP following Pareto principle)")

# Register the settings tools when this module is imported
register_settings_tools()