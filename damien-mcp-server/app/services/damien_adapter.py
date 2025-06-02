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
from damien_cli.integrations import gmail_integration as damien_gmail_integration_module
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
        self.damien_gmail_integration_module = damien_gmail_integration_module

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
                # Use the correct function from Gmail integration
                client = self.damien_gmail_integration_module.get_gmail_service()
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

    async def get_gmail_service(self) -> Any:
        """Provides the authenticated Gmail service client."""
        return await self._ensure_g_service_client()

    async def list_emails_tool(
        self,
        query: Optional[str] = None,
        max_results: int = 10,
        page_token: Optional[str] = None,
        include_headers: Optional[List[str]] = None,  # New parameter
        optimize_query: bool = False  # Enable query optimization
    ) -> Dict[str, Any]:
        """Lists emails from Gmail based on search criteria.
        
        Can include specified headers in the response to optimize data fetching.
        
        Args:
            query: Optional Gmail search query string.
            max_results: Maximum number of emails to retrieve.
            page_token: Optional token for pagination.
            include_headers: Optional list of header names to include in summaries.
            optimize_query: Whether to apply smart query optimization for large queries.
            
        Returns:
            Dict[str, Any]: A dictionary containing operation status, data or error.
        """
        try:
            g_client = await self._ensure_g_service_client()
            logger.debug(
                f"Adapter: list_emails_tool called with query='{query}', max_results={max_results}, "
                f"page_token='{page_token}', include_headers={include_headers}, optimize_query={optimize_query}"
            )
            
            # Apply query optimization if enabled
            if optimize_query and query and not page_token:
                # Only import when needed to avoid circular imports
                from damien_cli.utilities.query_optimizer import optimize_bulk_query
                
                # Get optimized queries
                optimized_queries = optimize_bulk_query(query, max_results)
                
                # If we got multiple optimized queries, handle them specially
                if len(optimized_queries) > 1:
                    logger.info(f"Query optimized into {len(optimized_queries)} targeted queries")
                    
                    # Aggregate results from all optimized queries
                    all_messages = []
                    
                    for opt_query in optimized_queries:
                        # For each optimized query, get a batch of results
                        batch_size = max(10, max_results // len(optimized_queries))
                        opt_result = self.damien_gmail_integration_module.list_messages(
                            service=g_client,
                            query_string=opt_query,
                            max_results=batch_size,
                            page_token=None,  # Don't use pagination for individual optimized queries
                            include_headers=include_headers
                        )
                        
                        if opt_result and "messages" in opt_result:
                            all_messages.extend(opt_result.get("messages", []))
                            
                            # If we have enough messages, stop querying
                            if len(all_messages) >= max_results:
                                break
                    
                    # Truncate to max_results
                    all_messages = all_messages[:max_results]
                    
                    # Since we're combining results, we don't have a real next page token
                    # We'd need a more complex pagination scheme for this case
                    return {
                        "success": True,
                        "data": {
                            "email_summaries": all_messages,
                            "next_page_token": None,
                            "optimized": True,
                            "query_count": len(optimized_queries)
                        }
                    }
            
            # Standard path - either optimization disabled or no optimization needed
            result_data = self.damien_gmail_integration_module.list_messages(
                service=g_client,
                query_string=query,
                max_results=max_results,
                page_token=page_token,
                include_headers=include_headers
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
            email_data = self.damien_gmail_integration_module.get_message_details(
                service=g_client,
                message_id=message_id,
                email_format=format_option
            )
            return {"success": True, "data": email_data}
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in get_email_details_tool for ID {message_id}: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in get_email_details_tool for ID {message_id}: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}

    async def trash_emails_tool(
        self, 
        message_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        estimated_count: Optional[int] = None,
        use_progressive: bool = True,
        optimize_query: bool = True
    ) -> Dict[str, Any]:
        """Moves emails to trash.
        
        Can operate in two modes:
        1. Direct mode: Provide message_ids list to trash specific emails
        2. Query mode: Provide query string to find and trash matching emails
        
        Args:
            message_ids: Optional list of message IDs to trash
            query: Optional Gmail search query to find emails to trash
            estimated_count: Optional estimated count for progress tracking
            use_progressive: Whether to use progressive batching (for query mode)
            optimize_query: Whether to apply smart query optimization (for query mode)
            
        Returns:
            Dict[str, Any]: A dictionary containing operation status, data or error.
        """
        # Parameter validation
        if not message_ids and not query:
            return {
                "success": False, 
                "error_message": "Either message_ids or query must be provided.", 
                "error_code": "INVALID_PARAMETER", 
                "data": {"trashed_count": 0, "status_message": "No emails specified to trash."}
            }
            
        try:
            g_client = await self._ensure_g_service_client()
            
            # CASE 1: Direct mode with message_ids
            if message_ids:
                logger.debug(f"Adapter: Trashing {len(message_ids)} emails using direct mode")
                success = self.damien_gmail_integration_module.batch_trash_messages(
                    service=g_client, 
                    message_ids=message_ids
                )
                
                if success:
                    status_msg = f"Successfully moved {len(message_ids)} email(s) to trash."
                    logger.info(status_msg)
                    return {
                        "success": True, 
                        "data": {
                            "trashed_count": len(message_ids), 
                            "status_message": status_msg,
                            "mode": "direct"
                        }
                    }
                else:
                    status_msg = f"Operation to move {len(message_ids)} email(s) to trash reported non-true by core API."
                    logger.warning(status_msg)
                    return {
                        "success": False, 
                        "error_message": status_msg, 
                        "error_code": "CORE_API_OPERATION_FAILED", 
                        "data": {
                            "trashed_count": 0, 
                            "status_message": status_msg
                        }
                    }
            
            # CASE 2: Query mode
            logger.info(f"Adapter: Trashing emails matching query '{query}' using {'progressive' if use_progressive else 'standard'} mode")
            
            # Apply query optimization if enabled
            if optimize_query:
                # Only import when needed to avoid circular imports
                from damien_cli.utilities.query_optimizer import optimize_bulk_query
                
                original_query = query
                optimized_queries = optimize_bulk_query(query, estimated_count)
                
                if len(optimized_queries) > 1:
                    logger.info(f"Optimized query '{original_query}' into {len(optimized_queries)} targeted queries")
                    
                    # If we have multiple optimized queries, process them one by one
                    total_trashed = 0
                    all_results = []
                    
                    for opt_query in optimized_queries:
                        if use_progressive:
                            # Process this query with progressive batching
                            from damien_cli.utilities.query_optimizer import get_batch_size_strategy
                            
                            # Get optimized batch sizing for this operation
                            batch_sizing = get_batch_size_strategy(
                                operation_type="trash", 
                                estimated_count=estimated_count
                            )
                            
                            # Process progressively
                            result = await self.damien_gmail_integration_module.trash_emails_progressively(
                                service=g_client,
                                query_string=opt_query,
                                estimated_count=estimated_count,
                                batch_sizing=batch_sizing
                            )
                            
                            # Track results
                            if result.get("success", False):
                                total_trashed += result.get("trashed_count", 0)
                                all_results.append(result)
                            else:
                                # Return on first error
                                return {
                                    "success": False,
                                    "error_message": result.get("error_message", "Unknown error"),
                                    "error_code": "PROGRESSIVE_OPERATION_FAILED",
                                    "data": {
                                        "trashed_count": total_trashed,
                                        "status_message": f"Error processing query: {opt_query}",
                                        "partial_results": all_results
                                    }
                                }
                        else:
                            # Standard processing (non-progressive)
                            # First get the IDs
                            emails = self.damien_gmail_integration_module.list_messages(
                                service=g_client,
                                query_string=opt_query,
                                max_results=200  # Get larger batches for efficiency
                            )
                            
                            if emails and "messages" in emails:
                                # Extract IDs
                                batch_ids = [msg["id"] for msg in emails.get("messages", [])]
                                
                                if batch_ids:
                                    # Trash this batch
                                    success = self.damien_gmail_integration_module.batch_trash_messages(
                                        service=g_client,
                                        message_ids=batch_ids
                                    )
                                    
                                    if success:
                                        total_trashed += len(batch_ids)
                                    else:
                                        # Return on first error
                                        return {
                                            "success": False,
                                            "error_message": f"Failed to trash emails for query: {opt_query}",
                                            "error_code": "BATCH_OPERATION_FAILED",
                                            "data": {
                                                "trashed_count": total_trashed,
                                                "status_message": f"Error processing query: {opt_query}"
                                            }
                                        }
                    
                    # Return success with total count
                    status_msg = f"Successfully moved {total_trashed} email(s) to trash using {len(optimized_queries)} optimized queries."
                    logger.info(status_msg)
                    return {
                        "success": True,
                        "data": {
                            "trashed_count": total_trashed,
                            "status_message": status_msg,
                            "mode": "query_optimized",
                            "queries_processed": len(optimized_queries)
                        }
                    }
                
                # If optimization didn't produce multiple queries, use original
                query = optimized_queries[0]
            
            # Single query processing (either original or the only optimized one)
            if use_progressive:
                # Progressive batching for single query
                from damien_cli.utilities.query_optimizer import get_batch_size_strategy
                
                # Get optimized batch sizing for this operation
                batch_sizing = get_batch_size_strategy(
                    operation_type="trash", 
                    estimated_count=estimated_count
                )
                
                # Process progressively
                result = await self.damien_gmail_integration_module.trash_emails_progressively(
                    service=g_client,
                    query_string=query,
                    estimated_count=estimated_count,
                    batch_sizing=batch_sizing
                )
                
                if result.get("success", False):
                    status_msg = f"Successfully moved {result.get('trashed_count', 0)} email(s) to trash using progressive processing."
                    logger.info(status_msg)
                    return {
                        "success": True,
                        "data": {
                            "trashed_count": result.get("trashed_count", 0),
                            "status_message": status_msg,
                            "mode": "query_progressive"
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error_message": result.get("error_message", "Unknown error"),
                        "error_code": "PROGRESSIVE_OPERATION_FAILED",
                        "data": {
                            "trashed_count": result.get("trashed_count", 0),
                            "status_message": result.get("error_message", "Failed to trash emails")
                        }
                    }
            else:
                # Standard processing (non-progressive) for single query
                # First get the IDs
                emails = self.damien_gmail_integration_module.list_messages(
                    service=g_client,
                    query_string=query,
                    max_results=200  # Get larger batches for efficiency
                )
                
                if emails and "messages" in emails:
                    # Extract IDs
                    batch_ids = [msg["id"] for msg in emails.get("messages", [])]
                    
                    if batch_ids:
                        # Trash this batch
                        success = self.damien_gmail_integration_module.batch_trash_messages(
                            service=g_client,
                            message_ids=batch_ids
                        )
                        
                        if success:
                            status_msg = f"Successfully moved {len(batch_ids)} email(s) to trash."
                            logger.info(status_msg)
                            return {
                                "success": True,
                                "data": {
                                    "trashed_count": len(batch_ids),
                                    "status_message": status_msg,
                                    "mode": "query_standard"
                                }
                            }
                        else:
                            status_msg = f"Operation to move {len(batch_ids)} email(s) to trash reported non-true by core API."
                            logger.warning(status_msg)
                            return {
                                "success": False,
                                "error_message": status_msg,
                                "error_code": "CORE_API_OPERATION_FAILED",
                                "data": {
                                    "trashed_count": 0,
                                    "status_message": status_msg
                                }
                            }
                else:
                    return {
                        "success": True,
                        "data": {
                            "trashed_count": 0,
                            "status_message": "No emails found matching the query.",
                            "mode": "query_standard"
                        }
                    }
                    
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in trash_emails_tool: {e}", exc_info=True)
            return {
                "success": False, 
                "error_message": str(e), 
                "error_code": e.__class__.__name__, 
                "data": {
                    "trashed_count": 0, 
                    "status_message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error in trash_emails_tool: {e}", exc_info=True)
            return {
                "success": False, 
                "error_message": f"Unexpected error: {str(e)}", 
                "error_code": "UNEXPECTED_ADAPTER_ERROR", 
                "data": {
                    "trashed_count": 0, 
                    "status_message": f"Unexpected error: {str(e)}"
                }
            }

    async def label_emails_tool(self, message_ids: List[str], add_label_names: Optional[List[str]], remove_label_names: Optional[List[str]]) -> Dict[str, Any]:
        if not message_ids: return {"success": False, "error_message": "No message IDs provided to label.", "error_code": "INVALID_PARAMETER", "data": {"modified_count": 0, "status_message": "No message IDs provided."}}
        if not add_label_names and not remove_label_names: return {"success": False, "error_message": "No labels provided to add or remove.", "error_code": "INVALID_PARAMETER", "data": {"modified_count": 0, "status_message": "No labels specified for modification."}}
        try:
            g_client = await self._ensure_g_service_client()
            logger.debug(f"Adapter: Labeling {len(message_ids)} emails: {message_ids}. Add: {add_label_names}, Remove: {remove_label_names}")
            success = self.damien_gmail_integration_module.batch_modify_message_labels(
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
            success = damien_gmail_integration_module.batch_mark_messages(
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

    async def add_rule_tool(self, rule_definition) -> Dict[str, Any]:
        try:
            logger.debug(f"Adapter: Adding new rule: {rule_definition}")
            logger.debug(f"Rule definition type: {type(rule_definition)}")
            
            # Handle both RuleDefinitionModel instances and dictionaries
            if hasattr(rule_definition, 'model_dump'):
                # It's a Pydantic model, convert to dict
                rule_dict = rule_definition.model_dump()
                logger.debug(f"Converted RuleDefinitionModel to dict: {rule_dict}")
            elif isinstance(rule_definition, dict):
                # It's already a dictionary
                rule_dict = rule_definition
                logger.debug(f"Using provided dictionary: {rule_dict}")
            else:
                raise ValidationError(f"rule_definition must be a RuleDefinitionModel or dictionary, got {type(rule_definition)}")
            
            # Convert any nested objects to dictionaries if needed
            cleaned_rule_definition = self._clean_rule_definition(rule_dict)
            
            # Create the RuleModel with validated data
            new_rule_model = RuleModel(**cleaned_rule_definition)
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

    def _clean_rule_definition(self, rule_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate rule definition for RuleModel constructor."""
        cleaned = {}
        
        # Copy basic fields
        for field in ['name', 'description', 'is_enabled', 'condition_conjunction']:
            if field in rule_definition:
                cleaned[field] = rule_definition[field]
        
        # Handle conditions (ensure they're proper dictionaries)
        if 'conditions' in rule_definition:
            cleaned['conditions'] = []
            for condition in rule_definition['conditions']:
                if isinstance(condition, dict):
                    cleaned['conditions'].append(condition)
                else:
                    # Convert condition object to dict if needed
                    cleaned['conditions'].append(condition.model_dump() if hasattr(condition, 'model_dump') else dict(condition))
        
        # Handle actions (ensure they're proper dictionaries)
        if 'actions' in rule_definition:
            cleaned['actions'] = []
            for action in rule_definition['actions']:
                if isinstance(action, dict):
                    cleaned['actions'].append(action)
                else:
                    # Convert action object to dict if needed
                    cleaned['actions'].append(action.model_dump() if hasattr(action, 'model_dump') else dict(action))
        
        return cleaned

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
            success = damien_gmail_integration_module.batch_delete_permanently(
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
