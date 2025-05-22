"""FastAPI router for MCP tool endpoints.

This module defines the FastAPI router and endpoints for executing
MCP tools that interact with Damien's core_api functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import ValidationError 
from typing import Any, Dict, Optional
import logging
import json

# Import dependencies and services
from ..core.security import verify_api_key
from ..dependencies.dependencies_service import get_damien_adapter # Updated path
from ..services.damien_adapter import DamienAdapter
from ..services import dynamodb_service
from ..core.config import settings
from ..models.mcp_protocol import ( # Changed from ..models.mcp
    MCPExecuteToolServerRequest,    # Renamed from MCPExecuteToolRequest
    MCPExecuteToolServerResponse    # Renamed from MCPExecuteToolResponse
)
from ..models.tools import (
    ListEmailsParams, ListEmailsOutput,
    GetEmailDetailsParams, GetEmailDetailsOutput,
    TrashEmailsParams, TrashEmailsOutput,
    LabelEmailsParams, LabelEmailsOutput,
    MarkEmailsParams, MarkEmailsOutput,
    ApplyRulesParams, ApplyRulesOutput,
    # For ListRulesOutput, AddRuleOutput, DeleteRuleOutputData, DeleteEmailsPermanentlyOutputData
    # we used specific Pydantic models in tools.py, so we need to import them.
    # Assuming ListRulesOutput is a model, not just a type alias anymore.
    # If they are still type aliases, this part of the import would be different.
    # Based on the previous diff, these should be actual Pydantic models now.
    ListRulesOutput, # Was ListRulesOutputData = List[Dict[str, Any]]
    AddRuleParams, AddRuleOutput, # Was AddRuleOutputData = Dict[str, Any]
    DeleteRuleParams, DeleteRuleOutput, # Was DeleteRuleOutputData (BaseModel)
    DeleteEmailsPermanentlyParams, DeleteEmailsPermanentlyOutput # Was DeleteEmailsPermanentlyOutputData (BaseModel)
)

# Set up logger
logger = logging.getLogger(__name__)

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
    tool_name = request_body.tool_name
    params_dict = request_body.input # Correctly using input for tool parameters
    session_id = request_body.session_id
    # user_id from request_body.user_id can be used if needed, else SERVER_USER_ID

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
                list_emails_params = ListEmailsParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True; error_message = f"Invalid parameters for {tool_name}: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.list_emails_tool(
                    query=list_emails_params.query,
                    max_results=list_emails_params.max_results,
                    page_token=list_emails_params.page_token
                )
            if api_response.get("success"): tool_output_data = api_response.get("data")
            else: is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from list_emails tool.")
        
        elif tool_name == "damien_get_email_details":
            try:
                get_details_params = GetEmailDetailsParams(**params_dict)
            except ValidationError as e:
                is_error_flag = True; error_message = f"Invalid parameters for {tool_name}: {e.errors()}"
            if not is_error_flag:
                api_response = await adapter.get_email_details_tool(
                    message_id=get_details_params.message_id, format_option=get_details_params.format
                )
                if api_response.get("success"): tool_output_data = api_response.get("data")
                else: is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from damien_get_email_details tool.")

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
                    if api_response.get("success"):
                        tool_output_data = api_response.get("data")
                    else:
                        is_error_flag = True
                        error_message = api_response.get("error_message", "Unknown error from damien_label_emails tool.")
                # If the inner 'if' (line 121) was true, is_error_flag is already set,
                # and api_response was not called, so we skip the above.

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
                api_response = await adapter.apply_rules_tool(params=apply_rules_params_model)
                if api_response.get("success"): tool_output_data = api_response.get("data")
                else: is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from damien_apply_rules tool.")

        elif tool_name == "damien_list_rules":
            api_response = await adapter.list_rules_tool()
            if api_response.get("success"): tool_output_data = api_response.get("data")
            else: is_error_flag = True; error_message = api_response.get("error_message", "Unknown error from damien_list_rules tool.")

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
    tools = [
        {
            "name": "damien_list_emails",
            "description": "Lists email messages based on a query, with support for pagination. Provides summaries including ID, thread ID, subject, sender, snippet, date, attachment status, and labels.",
            "input_schema": ListEmailsParams.model_json_schema(),
            "output_schema": ListEmailsOutput.model_json_schema()
        },
        {
            "name": "damien_get_email_details",
            "description": "Retrieves the full details of a specific email message, including headers, payload (body, parts), and raw content based on the specified format.",
            "input_schema": GetEmailDetailsParams.model_json_schema(),
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
            "description": "Lists all configured filtering rules in Damien, including their definitions (name, conditions, actions).",
            "input_schema": {}, # No parameters needed for listing all rules
            "output_schema": ListRulesOutput.model_json_schema()
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
    return tools
