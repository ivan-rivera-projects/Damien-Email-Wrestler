"""FastAPI router for MCP tool endpoints.

This module defines the FastAPI router and endpoints for executing
MCP tools that interact with Damien's core_api functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import ValidationError 
from typing import Any, Dict, Optional
import logging
import json
from datetime import datetime, timezone

# Import dependencies and services
from ..core.security import verify_api_key
from ..dependencies.dependencies_service import get_damien_adapter # Updated path
from ..services.damien_adapter import DamienAdapter
from ..services import dynamodb_service
from ..core.config import settings


def preprocess_list_parameter(param):
    """
    Preprocess list parameters that may come as JSON strings from MCP clients.
    
    Args:
        param: Parameter value that might be a JSON string representation of a list
        
    Returns:
        Parsed list if input was a valid JSON string, otherwise returns the original parameter
    """
    if param is None:
        return param
    if isinstance(param, str):
        try:
            parsed_param = json.loads(param)
            if isinstance(parsed_param, list) and all(isinstance(item, str) for item in parsed_param):
                return parsed_param
            else:
                logger.warning(f"Parameter JSON string did not parse to a list of strings: {parsed_param}")
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse parameter as JSON: {param}")
    return param


def preprocess_mcp_parameters(params_dict):
    """
    Preprocess common MCP parameters that are often sent as JSON strings.
    
    Args:
        params_dict: Dictionary of parameters from MCP request
        
    Returns:
        Updated parameters dictionary with parsed list parameters
    """
    # List of parameters that are commonly sent as JSON strings by MCP clients
    list_parameters = [
        'message_ids', 'add_label_names', 'remove_label_names', 
        'include_headers', 'rule_ids_to_apply'
    ]
    
    for param_name in list_parameters:
        if param_name in params_dict:
            params_dict[param_name] = preprocess_list_parameter(params_dict[param_name])
    
    return params_dict
from ..models.mcp_protocol import ( # Changed from ..models.mcp
    MCPExecuteToolServerRequest,    # Renamed from MCPExecuteToolRequest
    MCPExecuteToolServerResponse    # Renamed from MCPExecuteToolResponse
)
from ..models.tools import (
    ListDraftsParams, ListEmailsOutput,
    GetDraftDetailsParams, GetEmailDetailsOutput,
    TrashEmailsParams, TrashEmailsOutput,
    LabelEmailsParams, LabelEmailsOutput,
    MarkEmailsParams, MarkEmailsOutput,
    ApplyRulesParams, ApplyRulesOutput,
    ListRulesParams, # New Params model for list_rules
    ListRulesOutput,
    RuleModelOutput, # For GetRuleDetailsOutput
    GetRuleDetailsParams, # New tool
    AddRuleParams, AddRuleOutput,
    DeleteRuleParams, DeleteRuleOutput,
    DeleteEmailsPermanentlyParams, DeleteEmailsPermanentlyOutput
)

# Set up logger
logger = logging.getLogger("damien_mcp_server_app") # Use the configured app logger

# Create router
router = APIRouter()

# Fixed user ID for now, assuming personal use
SERVER_USER_ID = settings.default_user_id


@router.post(
    "/execute_tool", # Plan mentions /execute, current is /execute_tool. Keeping /execute_tool for now.
    response_model=MCPExecuteToolServerResponse, # Updated response model
    summary="Execute a Damien Tool via MCP",
    dependencies=[Depends(verify_api_key)],
    description="Execute one of Damien's Gmail management tools via the Model Context Protocol (MCP)",
    responses={
        200: {
            "description": "Successfully executed the tool or encountered a tool-specific error",
            "content": {
                "application/json": {
                    "example": {
                        "tool_result_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                        "is_error": False,
                        "output": {
                            "email_summaries": [
                                {"id": "msg1", "thread_id": "thread1", "snippet": "Email content..."}
                            ]
                        },
                        "error_message": None
                    }
                }
            }
        }
    }
)
async def execute_tool_endpoint(
    request_body: MCPExecuteToolServerRequest, # Updated request model
    adapter: DamienAdapter = Depends(get_damien_adapter)
):
    """Execute a Damien tool via the MCP protocol.
    
    This endpoint accepts a tool name, parameters, and session context information,
    then executes the requested tool on the user's Gmail account using the Damien
    core_api layer. Results and context are saved for multi-turn conversations.
    
    Args:
        request_body: The MCP tool execution request containing the tool name, 
                     parameters, and session information
        adapter: The DamienAdapter instance (injected via dependency)
                
    Returns:
        MCPExecuteToolServerResponse: The tool execution result with output or error details
        
    Note:
        - The endpoint handles tool-specific errors within the MCPExecuteToolServerResponse
        - Session context is maintained in DynamoDB for multi-turn conversations
        - All requests to Gmail API are made through the Damien core_api layer
    """
    # Apply tool usage policy
    from ..core.tool_usage_config import get_tool_usage_config, ToolUsagePolicy
    config = get_tool_usage_config()
    
    # Log API endpoint usage warning
    if config.warn_on_api_usage:
        logger.warning(f"API endpoint used instead of direct MCP tool call for {request_body.tool_name}")
    
    # Check if we're enforcing direct MCP only
    if config.policy == ToolUsagePolicy.DIRECT_MCP_ONLY:
        return MCPExecuteToolServerResponse(
            tool_result_id="policy_enforcement",
            is_error=True,
            error_message=f"Direct MCP tools required. Please use '{request_body.tool_name}' tool directly instead of API endpoint.",
            output=None
        )
        
    tool_name = request_body.tool_name
    params_dict = request_body.input # Correctly using input for tool parameters
    session_id = request_body.session_id
    # user_id from request_body.user_id can be used if needed, else SERVER_USER_ID

    # Preprocess parameters to handle JSON string lists from MCP clients
    params_dict = preprocess_mcp_parameters(params_dict)

    # Debug logging to see exactly what we're receiving
    logger.info(f"=== DEBUGGING PARAMETERS ===")
    logger.info(f"Tool: {tool_name}")
    logger.info(f"Raw params_dict: {params_dict}")
    logger.info(f"Type of params_dict: {type(params_dict)}")
    if "include_headers" in params_dict:
        logger.info(f"include_headers value: {params_dict['include_headers']}")
        logger.info(f"include_headers type: {type(params_dict['include_headers'])}")

    # Pre-process include_headers parameter if it exists and is a JSON string
    # This handles the MCP client sending arrays as JSON strings
    if "include_headers" in params_dict and isinstance(params_dict["include_headers"], str):
        try:
            import json
            parsed_headers = json.loads(params_dict["include_headers"])
            if isinstance(parsed_headers, list) and all(isinstance(item, str) for item in parsed_headers):
                params_dict["include_headers"] = parsed_headers
                logger.info(f"Successfully parsed include_headers from JSON string: {parsed_headers}")
            else:
                logger.warning(f"include_headers JSON string did not parse to a list of strings: {parsed_headers}")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse include_headers as JSON: {e}")

    user_id = SERVER_USER_ID
    
    previous_context = None
    try:
        # dynamodb_service methods are now async
        previous_context = await dynamodb_service.get_session_context(
            settings.dynamodb.table_name, user_id, session_id
        )
        logger.debug(f"Loaded context for session_id={session_id}: {previous_context}")
    except Exception as e:
        logger.warning(f"Failed to load context for session_id={session_id}: {e}")
    
    tool_output_data = None
    error_message = None
    is_error_flag = False
    
    try:
        if tool_name == "damien_list_emails":
            try:
                list_emails_params = ListDraftsParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True; error_message = f"Invalid parameters for {tool_name}: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.list_emails_tool(
                    query=list_emails_params.query,
                    max_results=list_emails_params.max_results,
                    page_token=list_emails_params.page_token,
                    include_headers=list_emails_params.include_headers # Pass new field
                )
            # Ensure api_response is checked before accessing .get, in case of validation error
            if not is_error_flag and api_response.get("success"):
                tool_output_data = api_response.get("data")
            elif not is_error_flag: # Implies api_response exists but success is false
                is_error_flag = True
                error_message = api_response.get("error_message", "Unknown error from list_emails tool.")
            # If is_error_flag was already true from validation, error_message is already set
        
        elif tool_name == "damien_get_email_details":
            try:
                get_details_params = GetDraftDetailsParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True; error_message = f"Invalid parameters for {tool_name}: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.get_email_details_tool(
                    message_id=get_details_params.message_id,
                    format_option=get_details_params.format,
                    include_headers=get_details_params.include_headers # Pass new field
                )
                # Ensure api_response is checked before accessing .get
                if not is_error_flag and api_response.get("success"):
                    tool_output_data = api_response.get("data")
                elif not is_error_flag: # Implies api_response exists but success is false
                    is_error_flag = True
                    error_message = api_response.get("error_message", "Unknown error from damien_get_email_details tool.")
                # If is_error_flag was already true from validation, error_message is already set

        elif tool_name == "damien_trash_emails":
            try:
                trash_params = TrashEmailsParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True; error_message = f"Invalid parameters for {tool_name}: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.trash_emails_tool(message_ids=trash_params.message_ids)
                if api_response.get("success"): tool_output_data = api_response.get("data")
                else: is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from damien_trash_emails tool.")
        
        elif tool_name == "damien_label_emails":
            try:
                label_params = LabelEmailsParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True; error_message = f"Invalid parameters for {tool_name}: {e.errors()}"
            if not is_error_flag:
                if not label_params.add_label_names and not label_params.remove_label_names: # Specific validation from plan
                     is_error_flag = True; error_message = "Missing both 'add_label_names' and 'remove_label_names'. At least one must be provided for damien_label_emails."
                else:
                    api_response = await adapter.label_emails_tool(
                        message_ids=label_params.message_ids,
                        add_label_names=label_params.add_label_names,
                        remove_label_names=label_params.remove_label_names
                    )
                    # This block should be inside the else, only if api_response is set
                    if not is_error_flag and api_response.get("success"): # Check is_error_flag
                        tool_output_data = api_response.get("data")
                    elif not is_error_flag: # Implies api_response exists but success is false
                        is_error_flag = True
                        error_message = api_response.get("error_message", "Unknown error from damien_label_emails tool.")
                # If is_error_flag was already true from validation, error_message is already set

        elif tool_name == "damien_mark_emails":
            try:
                mark_params = MarkEmailsParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True; error_message = f"Invalid parameters for {tool_name}: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.mark_emails_tool(
                    message_ids=mark_params.message_ids, mark_as=mark_params.mark_as
                )
                if api_response.get("success"): tool_output_data = api_response.get("data")
                else: is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from damien_mark_emails tool.")
        
        elif tool_name == "damien_apply_rules":
            try: apply_rules_params_model = ApplyRulesParams(**params_dict)
            except ValidationError as e: is_error_flag = True; error_message = f"Invalid parameters for damien_apply_rules: {e.errors()}"
            if not is_error_flag:
                # apply_rules_params_model is an instance of ApplyRulesParams
                # which now has include_detailed_ids
                api_response = await adapter.apply_rules_tool(params=apply_rules_params_model) # The adapter method now handles this.
                if api_response.get("success"): tool_output_data = api_response.get("data")
                else: is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from damien_apply_rules tool.")

        elif tool_name == "damien_list_rules":
            try:
                list_rules_params = ListRulesParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True; error_message = f"Invalid parameters for {tool_name}: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.list_rules_tool(summary_view=list_rules_params.summary_view)
                if api_response.get("success"): tool_output_data = api_response.get("data")
                else: is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from damien_list_rules tool.")

        elif tool_name == "damien_get_rule_details":
            try:
                get_rule_params = GetRuleDetailsParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True; error_message = f"Invalid parameters for {tool_name}: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.get_rule_details_tool(rule_id_or_name=get_rule_params.rule_id_or_name)
                if api_response.get("success"): tool_output_data = api_response.get("data")
                else:
                    is_error_flag = True; error_message = api_response.get("error_message", f"Unknown error from {tool_name} tool.")
                    if api_response.get("error_code") == "RULE_NOT_FOUND": error_message = f"Rule '{get_rule_params.rule_id_or_name}' not found."
        
        elif tool_name == "damien_add_rule":
            try: add_rule_params_model = AddRuleParams(**params_dict)
            except ValidationError as e: is_error_flag = True; error_message = f"Invalid parameters for damien_add_rule: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.add_rule_tool(rule_definition=add_rule_params_model.rule_definition)
                if api_response.get("success"): tool_output_data = api_response.get("data")
                else: is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from damien_add_rule tool.")
        
        elif tool_name == "damien_delete_rule":
            try: delete_rule_params_model = DeleteRuleParams(**params_dict)
            except ValidationError as e: is_error_flag = True; error_message = f"Invalid parameters for damien_delete_rule: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.delete_rule_tool(rule_identifier=delete_rule_params_model.rule_identifier)
                if api_response.get("success"): tool_output_data = api_response.get("data")
                else:
                    is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from damien_delete_rule tool.")
                    if api_response.get("error_code") == "RULE_NOT_FOUND": error_message = f"Rule '{delete_rule_params_model.rule_identifier}' not found."
        
        elif tool_name == "damien_delete_emails_permanently":
            try:
                delete_params_model = DeleteEmailsPermanentlyParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True
                error_message = f"Invalid parameters for damien_delete_emails_permanently: {e.errors()}"
            
            if not is_error_flag:
                # Critical action: Log a strong warning before proceeding
                logger.warning(f"Attempting PERMANENT DELETION of emails: {delete_params_model.message_ids} for session {session_id}")
                api_response = await adapter.delete_emails_permanently_tool(message_ids=delete_params_model.message_ids)
                if api_response.get("success"):
                    tool_output_data = api_response.get("data")
                else:
                    is_error_flag = True
                    error_message = api_response.get("error_message", "Unknown error from damien_delete_emails_permanently tool.")

        # Registry-based Tools (Draft, Settings, and Thread Tools) - Route to tool registry handlers
        elif tool_name in ["damien_create_draft", "damien_update_draft", "damien_send_draft", 
                           "damien_list_drafts", "damien_get_draft_details", "damien_delete_draft",
                           "damien_get_vacation_settings", "damien_update_vacation_settings",
                           "damien_get_imap_settings", "damien_update_imap_settings", 
                           "damien_get_pop_settings", "damien_update_pop_settings",
                           # Thread tools added here
                           "damien_list_threads", "damien_get_thread_details",
                           "damien_modify_thread_labels", "damien_trash_thread",
                           "damien_delete_thread_permanently"]:
            try:
                # Import tool registry to get the handler
                from ..services.tool_registry import tool_registry
                
                # Log the registry lookup attempt
                logger.info(f"Looking up tool '{tool_name}' in registry")
                
                # Get the tool definition and handler
                tool_def = tool_registry.get_tool_definition(tool_name)
                if not tool_def:
                    is_error_flag = True
                    error_message = f"Tool '{tool_name}' not found in registry"
                    logger.error(f"Tool '{tool_name}' not found in registry. Available tools: {list(tool_registry.get_all_tools().keys())}")
                else:
                    logger.info(f"Found tool definition for '{tool_name}' with handler '{tool_def.handler_name}'")
                    handler_func = tool_registry.get_handler(tool_def.handler_name)
                    if not handler_func:
                        is_error_flag = True
                        error_message = f"Handler for tool '{tool_name}' not found"
                        logger.error(f"Handler '{tool_def.handler_name}' not found for tool '{tool_name}'")
                    else:
                        # Prepare context for the handler
                        context = {
                            "session_id": session_id,
                            "user_id": user_id,
                            "tool_name": tool_name,
                            "timestamp": datetime.now(timezone.utc).isoformat()  # Use current timestamp
                        }
                        
                        logger.info(f"Executing handler for '{tool_name}'")
                        # Execute the handler with the parameters and context
                        api_response = await handler_func(params_dict, context)
                        if api_response.get("success", True):  # Assume success if not specified
                            tool_output_data = api_response
                            logger.info(f"Successfully executed '{tool_name}'")
                        else:
                            is_error_flag = True
                            error_message = api_response.get("error_message", f"Unknown error from {tool_name} tool.")
                            logger.error(f"Error executing '{tool_name}': {error_message}")
                            
            except Exception as e:
                logger.error(f"Error executing registered tool {tool_name}: {e}", exc_info=True)
                is_error_flag = True
                error_message = f"Error executing {tool_name}: {str(e)}"

        else:
            is_error_flag = True
            error_message = f"Unknown tool_name: {tool_name}"

    except Exception as e: 
        logger.error(f"Unexpected error processing tool {tool_name}: {e}", exc_info=True)
        is_error_flag = True
        error_message = f"An unexpected server error occurred while processing tool {tool_name}."
    # End of main try...except for tool processing

    # Construct the response
    mcp_response = MCPExecuteToolServerResponse(
        is_error=is_error_flag,
        output=tool_output_data,
        error_message=error_message
    )
    
    # Add tool usage policy headers to encourage direct MCP tool usage
    from ..core.tool_usage_config import get_tool_usage_config
    config = get_tool_usage_config()
    
    # We need to set headers in FastAPI's response object
    # This requires using a response_model_exclude_none=True parameter in the router decorator
    # But we can also add a note in the response for AI engines to see
    if not is_error_flag and config.warn_on_api_usage:
        if tool_output_data is None:
            tool_output_data = {}
        
        if isinstance(tool_output_data, dict):
            tool_output_data["_api_usage_guidance"] = {
                "message": config.direct_tool_message,
                "recommendation": f"Use '{tool_name}' tool directly for optimal performance",
                "policy": config.policy
            }
            mcp_response.output = tool_output_data
    
    # Try to save context (should not prevent returning the tool response)
    try:
        if not is_error_flag: # Only save context if the tool call itself wasn't an error initially
            current_call_context = {
                "tool_result_id": mcp_response.tool_result_id,
                "tool_name": tool_name,
                "input": params_dict,
                "output_summary": tool_output_data
            }
            new_session_data_to_save = previous_context or {}
            if "interactions" not in new_session_data_to_save: new_session_data_to_save["interactions"] = []
            new_session_data_to_save["interactions"].append(current_call_context)
            await dynamodb_service.save_session_context(
                settings.dynamodb.table_name, user_id, session_id, new_session_data_to_save,
                ttl_seconds=settings.dynamodb.session_ttl_seconds
            )
            logger.debug(f"Saved context for session_id={session_id}")
        elif previous_context is not None: # If tool errored but context existed, maybe save error? For now, just log.
            logger.debug(f"Tool execution for {tool_name} resulted in an error. Context not updated with this interaction.")
        else:
            logger.debug(f"Tool execution for {tool_name} resulted in an error. No prior context to update.")

    except Exception as e: # Catch errors specifically from context saving
        logger.error(f"Failed to save context for session_id={session_id} after tool execution: {e}", exc_info=True)
    
    return mcp_response

@router.get(
    "/list_tools", 
    summary="List Available Tools", 
    description="Returns a list of all available Damien MCP tools with their schemas",
    responses={
        200: {
            "description": "List of available tools with their descriptions and JSON schemas",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "name": "damien_list_emails",
                            "description": "Lists email messages based on a query, with support for pagination.",
                            "input_schema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Gmail search query"
                                    },
                                    "max_results": {
                                        "type": "integer",
                                        "description": "Maximum number of emails to retrieve",
                                        "default": 10
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
)
async def list_tools_endpoint():
    """Returns a list of available tools with their definitions.
    
    This endpoint provides discovery capabilities for MCP clients like Claude,
    enabling them to understand what tools are available and how to use them.
    For each tool, it returns:
    
    - Name: The unique identifier for the tool
    - Description: A human-readable description of what the tool does
    - Input Schema: JSON Schema describing the required and optional parameters
    
    Returns:
        list: A list of tool definitions containing name, description, and input schema
    """
    # Import tool registry to get dynamically registered tools
    from ..services.tool_registry import tool_registry
    
    tools = []
    
    # First, add all registry-based tools (draft tools, settings tools)
    all_registered_tools = tool_registry.get_all_tools()
    for tool_name, tool_def in all_registered_tools.items():
        tools.append({
            "name": tool_def.name,
            "description": tool_def.description,
            "input_schema": tool_def.input_schema,
        })
    
    # Then, add the hardcoded email/rules tools that have handlers but aren't registered
    hardcoded_tools = [
        {
            "name": "damien_list_emails",
            "description": "⚡ OPTIMIZATION REQUIRED: Lists email messages with support for pagination. ALWAYS use 'include_headers' parameter to fetch all needed data in ONE call instead of making multiple get_email_details calls. This saves 10x time and tokens. Example: include_headers=[\"From\", \"Subject\", \"Date\", \"To\", \"List-Unsubscribe\"]",
            "input_schema": ListDraftsParams.model_json_schema(),
            "output_schema": ListEmailsOutput.model_json_schema()
        },
        {
            "name": "damien_get_email_details",
            "description": "Retrieves the full details of a specific email message, including headers, payload (body, parts), and raw content based on the specified format.",
            "input_schema": GetDraftDetailsParams.model_json_schema(),
            "output_schema": GetEmailDetailsOutput.model_json_schema()
        },
        {
            "name": "damien_trash_emails",
            "description": "Moves specified emails to the trash folder. Returns a count of trashed emails and a status message.",
            "input_schema": TrashEmailsParams.model_json_schema(),
            "output_schema": TrashEmailsOutput.model_json_schema()
        },
        {
            "name": "damien_label_emails",
            "description": "Adds or removes specified labels from emails. Returns a count of modified emails and a status message.",
            "input_schema": LabelEmailsParams.model_json_schema(),
            "output_schema": LabelEmailsOutput.model_json_schema()
        },
        {
            "name": "damien_mark_emails",
            "description": "Marks specified emails as read or unread. Returns a count of modified emails and a status message.",
            "input_schema": MarkEmailsParams.model_json_schema(),
            "output_schema": MarkEmailsOutput.model_json_schema()
        },
        {
            "name": "damien_apply_rules",
            "description": "Applies filtering rules to emails in your Gmail account based on various criteria. Can be run in dry-run mode. Returns a detailed summary of actions taken or that would be taken.",
            "input_schema": ApplyRulesParams.model_json_schema(),
            "output_schema": ApplyRulesOutput.model_json_schema()
        },
        {
            "name": "damien_list_rules",
            "description": "Lists filtering rules in Damien. Can return summaries or full definitions.",
            "input_schema": ListRulesParams.model_json_schema(),
            "output_schema": ListRulesOutput.model_json_schema()
        },
        {
            "name": "damien_get_rule_details",
            "description": "Retrieves the full definition of a specific filtering rule by its ID or name.",
            "input_schema": GetRuleDetailsParams.model_json_schema(),
            "output_schema": RuleModelOutput.model_json_schema()
        },
        {
            "name": "damien_add_rule",
            "description": "Adds a new filtering rule to Damien. Expects a full rule definition and returns the created rule, including its server-generated ID and timestamps.",
            "input_schema": AddRuleParams.model_json_schema(),
            "output_schema": AddRuleOutput.model_json_schema()
        },
        {
            "name": "damien_delete_rule",
            "description": "Deletes a filtering rule from Damien by its ID or name. Returns a status message and the identifier of the deleted rule.",
            "input_schema": DeleteRuleParams.model_json_schema(),
            "output_schema": DeleteRuleOutput.model_json_schema()
        },
        {
            "name": "damien_delete_emails_permanently",
            "description": "PERMANENTLY deletes specified emails from Gmail. This action is irreversible and emails cannot be recovered. Returns a count of deleted emails and a status message.",
            "input_schema": DeleteEmailsPermanentlyParams.model_json_schema(),
            "output_schema": DeleteEmailsPermanentlyOutput.model_json_schema()
        }
    ]
    
    # Add hardcoded tools to the list
    tools.extend(hardcoded_tools)
    
    return tools

# Import the tool modules to register their tools
from ..tools import settings_tools
from ..tools import draft_tools
from ..tools import thread_tools
