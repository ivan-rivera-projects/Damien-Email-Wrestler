"""DamienAdapter for bridging FastAPI to Damien's core_api.

This module provides the DamienAdapter class which serves as an adapter/bridge
between FastAPI endpoints and Damien's core_api functionality.

The adapter is responsible for:
1. Maintaining an authenticated Gmail service client
2. Translating between MCP tool requests and Damien core_api calls  
3. Handling exceptions and providing consistent error responses
4. Formatting responses in a way that's compatible with the MCP protocol

Each tool method in this adapter corresponds to a specific Gmail management 
functionality provided by Damien's core_api.
"""

from typing import Any, Dict, List, Optional
import logging
import logging as py_logging # To get logging.DEBUG
from damien_cli.core import logging_setup as damien_cli_logging_setup # For CLI logging setup

# Import Damien core_api components
from damien_cli.core_api import gmail_api_service as damien_gmail_module
from damien_cli.core_api import rules_api_service as damien_rules_module
from damien_cli.core_api.exceptions import (
    DamienError,
    GmailApiError,
    InvalidParameterError,
    RuleStorageError,
    RuleNotFoundError
)
from damien_cli.features.rule_management.models import RuleModel
from ..models.tools import ApplyRulesParams # Changed from ..models.mcp
from pydantic import ValidationError
from ..core.config import settings # For accessing paths for Gmail client

# Set up logger
logger = logging.getLogger(__name__)


class DamienAdapter:
    """Adapter class to bridge FastAPI endpoints with Damien's core_api functionalities.
    
    This class serves as the primary interface between the MCP server's FastAPI
    endpoints and the Damien-CLI core_api layer. It's responsible for:
    
    1. Maintaining an authenticated Gmail service client session
    2. Translating between MCP tool requests and Damien core_api function calls
    3. Handling exceptions from the core_api layer and providing consistent error responses
    4. Formatting responses in a way that's compatible with the MCP protocol
    
    Each method in this class corresponds to a specific Gmail management capability
    provided by Damien's core_api, wrapped in error handling and response formatting
    logic specific to the MCP server's needs.
    
    Attributes:
        _g_service_client: Cached Gmail service client instance
        damien_gmail_module: Reference to Damien's gmail_api_service module
        damien_rules_module: Reference to Damien's rules_api_service module
    """
    
    def __init__(self):
        # Explicitly setup damien-cli logging if not already done or to ensure level
        # This helps ensure that when damien-cli is used as a library by the MCP server,
        # its logging (especially file logging and debug level) is active.
        try:
            damien_cli_logger = damien_cli_logging_setup.setup_logging(log_level=py_logging.DEBUG)
            # Check if file handler is present and path is as expected
            cli_file_handler_path = None
            for handler in damien_cli_logger.handlers:
                if isinstance(handler, py_logging.FileHandler):
                    cli_file_handler_path = handler.baseFilename
                    break
            logger.info(f"DamienAdapter: Damien CLI logging configured by adapter. Level: DEBUG. Expected CLI log file: {cli_file_handler_path or 'Not Set'}")
        except Exception as e:
            logger.error(f"DamienAdapter: Failed to explicitly configure Damien CLI logging: {e}", exc_info=True)

        self._g_service_client: Optional[Any] = None # Cached client
        self.damien_gmail_module = damien_gmail_module
        self.damien_rules_module = damien_rules_module

    async def _ensure_g_service_client(self) -> Any:
        """Ensures the Gmail service client is initialized and returns it.
        
        This method implements a lazy initialization pattern for the Gmail service client.
        It checks if the client is already cached, and if not, initializes it using the
        non-interactive authentication method provided by Damien's core_api.
        
        Returns:
            Any: An authenticated Gmail service client object
            
        Raises:
            DamienError: If authentication fails or the client can't be initialized
            
        Note:
            This method uses a cached client when possible to reduce authentication overhead
            It leverages token.json for authentication without requiring interactive login
        """
        if self._g_service_client is None:
            logger.info("Gmail service client not initialized. Initializing...")
            try:
                # Use the instance's mocked/actual module
                client = self.damien_gmail_module.get_g_service_client_from_token(
                    token_file_path_str=settings.gmail_token_path,
                    credentials_file_path_str=settings.gmail_credentials_path,
                    scopes=settings.gmail_scopes
                )
                if client is None:
                    logger.error("Gmail service client initialization returned None from damien_cli")
                    raise DamienError("Failed to initialize Gmail service client (returned None).")
                self._g_service_client = client
                logger.info("Gmail service client initialized and cached successfully.")
            except DamienError as e:
                logger.error(f"DamienError during Gmail client initialization: {e}", exc_info=True)
                raise # Re-raise to be caught by tool methods
            except Exception as e:
                logger.error(f"Unexpected error during Gmail client initialization: {e}", exc_info=True)
                raise DamienError(f"Unexpected error initializing Gmail service: {e}") # Wrap in DamienError
        return self._g_service_client

    async def list_emails_tool(
        self,
        query: Optional[str] = None,
        max_results: int = 10,
        page_token: Optional[str] = None,
        include_headers: Optional[List[str]] = None  # New parameter
    ) -> Dict[str, Any]:
        """Lists emails from Gmail based on search criteria.
        
        Can include specified headers in the response to optimize data fetching.
        
        Args:
            query: Optional Gmail search query string.
            max_results: Maximum number of emails to retrieve.
            page_token: Optional token for pagination.
            include_headers: Optional list of header names to include in summaries.
            
        Returns:
            Dict[str, Any]: A dictionary containing operation status, data or error.
        """
        try:
            g_client = await self._ensure_g_service_client()
            logger.debug(
                f"Adapter: list_emails_tool called with query='{query}', max_results={max_results}, "
                f"page_token='{page_token}', include_headers={include_headers}"
            )
            result_data = self.damien_gmail_module.list_messages(
                service=g_client, # Corrected parameter name
                query_string=query,
                max_results=max_results,
                page_token=page_token,
                include_headers=include_headers # Pass new parameter
            )
            # The damien_cli.list_messages will now return richer objects if include_headers was used.
            # If include_headers was None, it returns basic stubs (id, threadId).
            # If include_headers was provided, it returns a list of dicts, each potentially having
            # 'id', 'threadId', requested headers, or an 'error' field per message.
            email_summaries = result_data.get("messages", [])
            
            return {
                "success": True,
                "data": {
                    "email_summaries": email_summaries,
                    "next_page_token": result_data.get("nextPageToken")
                }
            }
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in list_emails_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in list_emails_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}
    
    async def get_email_details_tool(
        self,
        message_id: str,
        format_option: str = "metadata", # Defaulting to metadata as 'full' is heavy
        include_headers: Optional[List[str]] = None # New parameter
    ) -> Dict[str, Any]:
        """
        Retrieves details for a specific email message.
        Can include only specified headers if format_option is 'metadata' and include_headers is provided.
        """
        try:
            g_client = await self._ensure_g_service_client()
            logger.debug(
                f"Adapter: get_email_details_tool called for ID: {message_id}, "
                f"format_option: {format_option}, include_headers: {include_headers}"
            )
            email_data = self.damien_gmail_module.get_message_details(
                service=g_client, # Corrected parameter name
                message_id=message_id,
                email_format=format_option,
                include_headers=include_headers # Pass new parameter
            )
            return {"success": True, "data": email_data}
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in get_email_details_tool for ID {message_id}: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in get_email_details_tool for ID {message_id}: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}

    async def trash_emails_tool(self, message_ids: List[str]) -> Dict[str, Any]:
        if not message_ids: return {"success": False, "error_message": "No message IDs provided to trash.", "error_code": "INVALID_PARAMETER", "data": {"trashed_count": 0, "status_message": "No message IDs provided."}}
        try:
            g_client = await self._ensure_g_service_client()
            logger.debug(f"Adapter: Trashing {len(message_ids)} emails: {message_ids}")
            success = self.damien_gmail_module.batch_trash_messages(service=g_client, message_ids=message_ids)
            if success:
                status_msg = f"Successfully moved {len(message_ids)} email(s) to trash."
                logger.info(status_msg)
                return {"success": True, "data": {"trashed_count": len(message_ids), "status_message": status_msg}}
            else:
                status_msg = f"Operation to move {len(message_ids)} email(s) to trash reported non-true by core API."
                logger.warning(status_msg)
                return {"success": False, "error_message": status_msg, "error_code": "CORE_API_OPERATION_FAILED", "data": {"trashed_count": 0, "status_message": status_msg}}
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in trash_emails_tool for IDs {message_ids}: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__, "data": {"trashed_count": 0, "status_message": str(e)}}
        except Exception as e:
            logger.error(f"Unexpected error in trash_emails_tool for IDs {message_ids}: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR", "data": {"trashed_count": 0, "status_message": f"Unexpected error: {str(e)}"}}

    async def label_emails_tool(self, message_ids: List[str], add_label_names: Optional[List[str]], remove_label_names: Optional[List[str]]) -> Dict[str, Any]:
        if not message_ids: return {"success": False, "error_message": "No message IDs provided to label.", "error_code": "INVALID_PARAMETER", "data": {"modified_count": 0, "status_message": "No message IDs provided."}}
        if not add_label_names and not remove_label_names: return {"success": False, "error_message": "No labels provided to add or remove.", "error_code": "INVALID_PARAMETER", "data": {"modified_count": 0, "status_message": "No labels specified for modification."}}
        try:
            g_client = await self._ensure_g_service_client()
            logger.debug(f"Adapter: Labeling {len(message_ids)} emails: {message_ids}. Add: {add_label_names}, Remove: {remove_label_names}")
            success = self.damien_gmail_module.batch_modify_message_labels(
                service=g_client, message_ids=message_ids, add_label_names=add_label_names, remove_label_names=remove_label_names
            )
            if success:
                modified_count = len(message_ids)
                status_msg = f"Successfully initiated label modification for {modified_count} email(s)."
                if add_label_names: status_msg += f" Added: {add_label_names}."
                if remove_label_names: status_msg += f" Removed: {remove_label_names}."
                logger.info(status_msg)
                return {"success": True, "data": {"modified_count": modified_count, "status_message": status_msg}}
            else:
                status_msg = "Label modification operation reported non-true by core API."
                logger.warning(status_msg)
                return {"success": False, "error_message": status_msg, "error_code": "CORE_API_OPERATION_FAILED", "data": {"modified_count": 0, "status_message": status_msg}}
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in label_emails_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__, "data": {"modified_count": 0, "status_message": str(e)}}
        except Exception as e:
            logger.error(f"Unexpected error in label_emails_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR", "data": {"modified_count": 0, "status_message": f"Unexpected error: {str(e)}"}}

    async def mark_emails_tool(self, message_ids: List[str], mark_as: str) -> Dict[str, Any]:
        if not message_ids: return {"success": False, "error_message": "No message IDs provided to mark.", "error_code": "INVALID_PARAMETER", "data": {"modified_count": 0, "status_message": "No message IDs provided."}}
        normalized_mark_as = mark_as.lower()
        if normalized_mark_as not in ["read", "unread"]: return {"success": False, "error_message": f"Invalid 'mark_as' value: {mark_as}.", "error_code": "INVALID_PARAMETER", "data": {"modified_count": 0, "status_message": f"Invalid 'mark_as' value: {mark_as}."}}
        try:
            g_client = await self._ensure_g_service_client()
            logger.debug(f"Adapter: Marking {len(message_ids)} emails as {normalized_mark_as}: {message_ids}")
            success = self.damien_gmail_module.batch_mark_messages(
                service=g_client, message_ids=message_ids, mark_as=normalized_mark_as
            )
            if success:
                modified_count = len(message_ids)
                status_msg = f"Successfully marked {modified_count} email(s) as {normalized_mark_as}."
                logger.info(status_msg)
                return {"success": True, "data": {"modified_count": modified_count, "status_message": status_msg}}
            else:
                status_msg = f"Mark as '{normalized_mark_as}' operation reported non-true by core API."
                logger.warning(status_msg)
                return {"success": False, "error_message": status_msg, "error_code": "CORE_API_OPERATION_FAILED", "data": {"modified_count": 0, "status_message": status_msg}}
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in mark_emails_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__, "data": {"modified_count": 0, "status_message": str(e)}}
        except Exception as e:
            logger.error(f"Unexpected error in mark_emails_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR", "data": {"modified_count": 0, "status_message": f"Unexpected error: {str(e)}"}}

    async def apply_rules_tool(self, params: ApplyRulesParams) -> Dict[str, Any]:
        try:
            query_parts = []
            if params.gmail_query_filter: query_parts.append(params.gmail_query_filter)
            if params.date_after: query_parts.append(f"after:{params.date_after.replace('/', '-')}") 
            if params.date_before: query_parts.append(f"before:{params.date_before.replace('/', '-')}")
            final_query = " ".join(query_parts).strip()
            if params.all_mail: final_query = ""
            g_client = await self._ensure_g_service_client()
            logger.info(
                f"Adapter: Applying rules with effective query: '{final_query}', Dry run: {params.dry_run}, "
                f"Detailed IDs: {params.include_detailed_ids}"
            )
            summary_dict = self.damien_rules_module.apply_rules_to_mailbox(
                g_service_client=g_client,
                gmail_api_service=self.damien_gmail_module,
                gmail_query_filter=final_query if final_query else None,
                rule_ids_to_apply=params.rule_ids_to_apply,
                dry_run=params.dry_run,
                scan_limit=params.scan_limit,
                include_detailed_ids=params.include_detailed_ids # Pass new parameter
            )
            return {"success": True, "data": summary_dict}
        except (DamienError, GmailApiError, InvalidParameterError, RuleStorageError) as e:
            logger.error(f"Error in apply_rules_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in apply_rules_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}

    async def list_rules_tool(self, summary_view: bool = True) -> Dict[str, Any]:
        try:
            logger.debug(f"Adapter: Listing rules. Summary view: {summary_view}")
            rule_models = self.damien_rules_module.load_rules()
            
            output_data: List[Dict[str, Any]] = []
            if summary_view:
                for rule in rule_models:
                    output_data.append({
                        "id": rule.id,
                        "name": rule.name,
                        "description": rule.description,
                        "is_enabled": rule.is_enabled
                    })
            else:
                output_data = [rule.model_dump(mode="json") for rule in rule_models]
                
            return {"success": True, "data": {"rules": output_data, "summary_view_active": summary_view}}
        except RuleStorageError as e:
            logger.error(f"Error loading rules in list_rules_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": "RULE_STORAGE_ERROR"}
        except Exception as e:
            logger.error(f"Unexpected error in list_rules_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}

    async def get_rule_details_tool(self, rule_id_or_name: str) -> Dict[str, Any]:
        try:
            logger.debug(f"Adapter: Getting details for rule: {rule_id_or_name}")
            # We need a function in damien_rules_module to get a single rule by ID or name
            # For now, let's assume it exists or load all and filter.
            # Ideally: rule_model = self.damien_rules_module.get_rule(rule_id_or_name)
            
            # Temporary workaround: load all and find
            all_rules = self.damien_rules_module.load_rules()
            found_rule: Optional[RuleModel] = None
            for r in all_rules:
                if r.id == rule_id_or_name or r.name.lower() == rule_id_or_name.lower():
                    found_rule = r
                    break
            
            if not found_rule:
                raise RuleNotFoundError(f"Rule '{rule_id_or_name}' not found.")
                
            return {"success": True, "data": found_rule.model_dump(mode="json")}
        except RuleNotFoundError as e:
            logger.warning(f"Rule not found in get_rule_details_tool: {e}")
            return {"success": False, "error_message": str(e), "error_code": "RULE_NOT_FOUND"}
        except (RuleStorageError, InvalidParameterError) as e: # RuleStorageError if load_rules fails
            logger.error(f"Error in get_rule_details_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in get_rule_details_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}

    async def add_rule_tool(self, rule_definition: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.debug(f"Adapter: Adding new rule: {rule_definition}")
            new_rule_model = RuleModel(**rule_definition)
            added_rule = self.damien_rules_module.add_rule(new_rule_model)
            return {"success": True, "data": added_rule.model_dump(mode="json")}
        except ValidationError as e: 
            logger.error(f"Invalid rule definition for add_rule_tool: {e.errors()}", exc_info=True)
            return {"success": False, "error_message": f"Invalid rule definition: {e.errors()}", "error_code": "INVALID_RULE_DEFINITION"}
        except (RuleStorageError, InvalidParameterError) as e: 
            logger.error(f"Error adding rule in add_rule_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in add_rule_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}

    async def delete_rule_tool(self, rule_identifier: str) -> Dict[str, Any]:
        try:
            logger.debug(f"Adapter: Deleting rule with identifier: {rule_identifier}")
            success = self.damien_rules_module.delete_rule(rule_id_or_name=rule_identifier)
            if success: 
                status_msg = f"Successfully deleted rule: {rule_identifier}"
                logger.info(status_msg)
                return {"success": True, "data": {"status_message": status_msg, "deleted_rule_identifier": rule_identifier}}
            else:
                status_msg = f"Rule deletion for '{rule_identifier}' reported non-true by core API, but no exception was raised."
                logger.warning(status_msg)
                return {"success": False, "error_message": status_msg, "error_code": "CORE_API_OPERATION_FAILED"}
        except RuleNotFoundError as e:
            logger.warning(f"Rule not found in delete_rule_tool: {e}") 
            return {"success": False, "error_message": str(e), "error_code": "RULE_NOT_FOUND"}
        except (RuleStorageError, InvalidParameterError) as e:
            logger.error(f"Error deleting rule in delete_rule_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in delete_rule_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}

    async def delete_emails_permanently_tool(self, message_ids: List[str]) -> Dict[str, Any]:
        """Permanently deletes a list of emails using Damien's core_api. This action is IRREVERSIBLE."""
        if not message_ids:
            return {"success": False, "error_message": "No message IDs provided to permanently delete.", "error_code": "INVALID_PARAMETER", "data": {"deleted_count": 0, "status_message": "No message IDs provided."}}
        try:
            logger.warning(f"Adapter: PERMANENTLY DELETING {len(message_ids)} emails: {message_ids}. THIS IS IRREVERSIBLE.")
            g_client = await self._ensure_g_service_client()
            # The CLI's batch_delete_permanently function returns a boolean.
            success = self.damien_gmail_module.batch_delete_permanently(
                service=g_client,
                message_ids=message_ids
            )
            
            if success:
                deleted_count = len(message_ids)
                status_msg = f"Successfully initiated permanent deletion for {deleted_count} email(s)."
                logger.info(status_msg)
                return {"success": True, "data": {"deleted_count": deleted_count, "status_message": status_msg}}
            else:
                status_msg = f"Permanent deletion operation reported non-true by core API for {len(message_ids)} email(s)."
                logger.warning(status_msg)
                return {"success": False, "error_message": status_msg, "error_code": "CORE_API_OPERATION_FAILED", "data": {"deleted_count": 0, "status_message": status_msg}}

        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in delete_emails_permanently_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__, "data": {"deleted_count": 0, "status_message": str(e)}}
        except Exception as e:
            logger.error(f"Unexpected error in delete_emails_permanently_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR", "data": {"deleted_count": 0, "status_message": f"Unexpected error: {str(e)}"}}

    # Add more methods for other tools here
