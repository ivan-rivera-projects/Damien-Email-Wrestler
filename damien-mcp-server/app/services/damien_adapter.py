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
import time
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

    async def count_emails_by_label_tool(self, label_name: str, max_count: int = 10000) -> Dict[str, Any]:
        """
        Counts total emails with a specific label using pagination-aware search.
        
        This function automatically handles Gmail's 100-result-per-page limit by
        using pagination to count all emails, making it suitable for enterprise
        use cases with thousands of emails per label.
        
        Args:
            label_name: Name of the label to count emails for
            max_count: Maximum number of emails to count (safety limit)
            
        Returns:
            Dict containing success status, total count, and pagination details
        """
        try:
            g_client = await self._ensure_g_service_client()
            logger.info(f"🔢 Starting pagination-aware count for label: {label_name}")
            
            total_count = 0
            page_count = 0
            page_token = None
            query = f"label:{label_name}"
            
            # Track timing for performance analysis
            import time
            start_time = time.time()
            
            while total_count < max_count:
                page_count += 1
                logger.debug(f"📄 Processing page {page_count} for label count")
                
                # Get batch of 100 (Gmail's maximum per request)
                result_data = self.damien_gmail_integration_module.list_messages(
                    service=g_client,
                    query_string=query,
                    max_results=100,  # Gmail's hard limit
                    page_token=page_token
                )
                
                if not result_data:
                    break
                
                # Count emails in this batch
                batch_emails = result_data.get("messages", [])
                batch_count = len(batch_emails)
                total_count += batch_count
                
                logger.debug(f"📊 Page {page_count}: Found {batch_count} emails (total: {total_count})")
                
                # Check for next page
                page_token = result_data.get("nextPageToken")
                if not page_token:
                    logger.info(f"✅ Reached end of results at page {page_count}")
                    break
                
                # Safety check to prevent infinite loops
                if page_count > 100:  # 100 pages = 10,000 emails max
                    logger.warning(f"⚠️ Hit page limit (100 pages) for safety - counting stopped")
                    break
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Check if we hit the max_count limit
            potentially_more = total_count >= max_count
            
            status_msg = f"Counted {total_count} emails with label '{label_name}' across {page_count} pages in {duration:.2f}s"
            if potentially_more:
                status_msg += f" (may have more - hit {max_count} limit)"
            
            logger.info(f"🎯 {status_msg}")
            
            return {
                "success": True,
                "data": {
                    "label_name": label_name,
                    "total_count": total_count,
                    "pages_processed": page_count,
                    "duration_seconds": round(duration, 2),
                    "potentially_more_emails": potentially_more,
                    "status_message": status_msg
                }
            }
            
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in count_emails_by_label_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in count_emails_by_label_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}

    async def get_all_emails_by_label_tool(self, label_name: str, max_emails: int = 5000) -> Dict[str, Any]:
        """
        Gets ALL email IDs for a specific label using pagination.
        
        Enterprise-ready function that can handle thousands of emails by
        automatically paginating through Gmail's 100-result-per-page limit.
        
        Args:
            label_name: Name of the label to get emails for
            max_emails: Maximum number of emails to retrieve (safety limit)
            
        Returns:
            Dict containing all email IDs and metadata for bulk operations
        """
        try:
            g_client = await self._ensure_g_service_client()
            logger.info(f"📧 Getting ALL emails for label: {label_name} (max: {max_emails})")
            
            all_emails = []
            page_count = 0
            page_token = None
            query = f"label:{label_name}"
            
            import time
            start_time = time.time()
            
            while len(all_emails) < max_emails:
                page_count += 1
                logger.debug(f"📄 Fetching page {page_count} for label emails")
                
                # Get batch of 100 (Gmail's maximum per request)
                result_data = self.damien_gmail_integration_module.list_messages(
                    service=g_client,
                    query_string=query,
                    max_results=100,  # Gmail's hard limit
                    page_token=page_token
                )
                
                if not result_data:
                    break
                
                # Collect emails in this batch
                batch_emails = result_data.get("messages", [])
                all_emails.extend(batch_emails)
                
                logger.debug(f"📊 Page {page_count}: Added {len(batch_emails)} emails (total: {len(all_emails)})")
                
                # Check for next page
                page_token = result_data.get("nextPageToken")
                if not page_token:
                    logger.info(f"✅ Retrieved all emails at page {page_count}")
                    break
                
                # Safety check
                if page_count > 50:  # 50 pages = 5,000 emails max
                    logger.warning(f"⚠️ Hit page limit (50 pages) for safety")
                    break
            
            # Truncate to max_emails if needed
            if len(all_emails) > max_emails:
                all_emails = all_emails[:max_emails]
                logger.info(f"✂️ Truncated to {max_emails} emails")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Extract just the IDs for bulk operations
            message_ids = [email["id"] for email in all_emails]
            
            status_msg = f"Retrieved {len(message_ids)} email IDs for label '{label_name}' in {duration:.2f}s"
            logger.info(f"🎯 {status_msg}")
            
            return {
                "success": True,
                "data": {
                    "label_name": label_name,
                    "message_ids": message_ids,
                    "total_count": len(message_ids),
                    "pages_processed": page_count,
                    "duration_seconds": round(duration, 2),
                    "ready_for_bulk_operations": True,
                    "status_message": status_msg
                }
            }
            
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in get_all_emails_by_label_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in get_all_emails_by_label_tool: {e}", exc_info=True)
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
                try:
                    # Use the robust gmail_api_service instead of gmail_integration
                    result = damien_gmail_module.batch_trash_messages(
                        gmail_service=g_client, 
                        message_ids=message_ids
                    )
                    
                    if result.get("success"):
                        status_msg = result.get("message", f"Successfully moved {len(message_ids)} email(s) to trash.")
                        logger.info(status_msg)
                        return {
                            "success": True, 
                            "data": {
                                "trashed_count": result.get("trashed_count", len(message_ids)), 
                                "status_message": status_msg,
                                "mode": "direct"
                            }
                        }
                    else:
                        status_msg = f"Operation to move {len(message_ids)} email(s) to trash failed."
                        logger.warning(status_msg)
                        return {
                            "success": False, 
                            "error_message": status_msg, 
                            "error_code": "GMAIL_API_OPERATION_FAILED", 
                            "data": {
                                "trashed_count": 0, 
                                "status_message": status_msg
                            }
                        }
                except Exception as e:
                    status_msg = f"Exception during trash operation: {str(e)}"
                    logger.error(status_msg)
                    return {
                        "success": False, 
                        "error_message": status_msg, 
                        "error_code": "GMAIL_API_EXCEPTION", 
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
        """
        Smart rule application with automatic async routing for large operations.
        
        Automatically detects large-scale operations and routes them to async processing
        to prevent timeouts and provide better user experience.
        """
        try:
            # Smart threshold detection for auto-async routing
            ASYNC_THRESHOLD = 300  # Auto-async for 300+ emails (lowered for demo)
            scan_limit = params.scan_limit or 1000
            
            query_parts = []
            if params.gmail_query_filter: query_parts.append(params.gmail_query_filter)
            if params.date_after: query_parts.append(f"after:{params.date_after.replace('/', '-')}") 
            if params.date_before: query_parts.append(f"before:{params.date_before.replace('/', '-')}")
            final_query = " ".join(query_parts).strip()
            if params.all_mail: final_query = ""
            
            # Determine if operation should be async based on size
            should_use_async = scan_limit > ASYNC_THRESHOLD
            
            if should_use_async and not params.dry_run:
                # Route to async processing for large operations
                logger.info(
                    f"🚀 Auto-routing to async processing: {scan_limit} emails > {ASYNC_THRESHOLD} threshold"
                )
                
                return await self._apply_rules_async(params, final_query)
            else:
                # Process synchronously for smaller operations or dry runs
                logger.info(
                    f"⚡ Processing synchronously: {scan_limit} emails <= {ASYNC_THRESHOLD} threshold"
                )
                
                return await self._apply_rules_sync(params, final_query)
                
        except (DamienError, GmailApiError, InvalidParameterError, RuleStorageError) as e:
            logger.error(f"Error in apply_rules_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in apply_rules_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}
    
    async def _apply_rules_sync(self, params: ApplyRulesParams, final_query: str) -> Dict[str, Any]:
        """Synchronous rule application for smaller operations."""
        g_client = await self._ensure_g_service_client()
        logger.info(
            f"Adapter: Applying rules synchronously with query: '{final_query}', Dry run: {params.dry_run}, "
            f"Detailed IDs: {params.include_detailed_ids}"
        )
        
        summary_dict = self.damien_rules_module.apply_rules_to_mailbox(
            g_service_client=g_client,
            gmail_api_service=self.damien_gmail_module,
            gmail_query_filter=final_query if final_query else None,
            rule_ids_to_apply=params.rule_ids_to_apply,
            dry_run=params.dry_run,
            scan_limit=params.scan_limit,
            include_detailed_ids=params.include_detailed_ids
        )
        
        return {
            "success": True, 
            "data": summary_dict,
            "processing_mode": "synchronous"
        }
    
    async def _apply_rules_async(self, params: ApplyRulesParams, final_query: str) -> Dict[str, Any]:
        """Asynchronous rule application for large operations."""
        try:
            # Import async processor
            from ..tools.async_tools import async_processor
            
            # Create task parameters
            task_params = {
                "gmail_query_filter": final_query,
                "rule_ids_to_apply": params.rule_ids_to_apply,
                "dry_run": params.dry_run,
                "scan_limit": params.scan_limit,
                "include_detailed_ids": params.include_detailed_ids,
                "date_after": params.date_after,
                "date_before": params.date_before,
                "all_mail": params.all_mail
            }
            
            # Submit to async processing
            job_id = await async_processor.submit_task(
                name=f"Rule application ({params.scan_limit} emails)",
                processor_func=self._async_rule_processor,
                parameters=task_params
            )
            
            # Estimate processing time
            estimated_minutes = max(1, params.scan_limit // 200)  # ~1 minute per 200 emails
            
            logger.info(f"🎯 Started async rule application job {job_id} for {params.scan_limit} emails")
            
            return {
                "success": True,
                "processing_mode": "asynchronous",
                "job_id": job_id,
                "status": "started",
                "message": f"Background rule application started for {params.scan_limit} emails",
                "estimated_duration_minutes": estimated_minutes,
                "data": {
                    "emails_to_process": params.scan_limit,
                    "async_threshold_triggered": True,
                    "tracking_info": {
                        "check_progress": f"damien_job_get_status(job_id='{job_id}')",
                        "get_results": f"damien_job_get_result(job_id='{job_id}') when complete"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to start async rule processing: {e}")
            # Fallback to sync processing if async fails
            logger.info("🔄 Falling back to synchronous processing due to async failure")
            return await self._apply_rules_sync(params, final_query)
    
    async def _async_rule_processor(self, task_params: Dict[str, Any]) -> Dict[str, Any]:
        """Background processor for rule application."""
        try:
            # Get authenticated client
            g_client = await self._ensure_g_service_client()
            
            logger.info(f"📊 Background processing: Applying rules to {task_params.get('scan_limit')} emails")
            
            # Apply rules using the standard method
            summary_dict = self.damien_rules_module.apply_rules_to_mailbox(
                g_service_client=g_client,
                gmail_api_service=self.damien_gmail_module,
                gmail_query_filter=task_params.get("gmail_query_filter"),
                rule_ids_to_apply=task_params.get("rule_ids_to_apply"),
                dry_run=task_params.get("dry_run", False),
                scan_limit=task_params.get("scan_limit", 1000),
                include_detailed_ids=task_params.get("include_detailed_ids", False)
            )
            
            # Add async processing metadata
            summary_dict["processing_mode"] = "asynchronous_completed"
            summary_dict["async_benefits"] = {
                "no_timeout_risk": True,
                "background_processing": True,
                "user_workflow_uninterrupted": True
            }
            
            logger.info(f"✅ Background rule application completed successfully")
            
            return {
                "status": "success",
                "summary": summary_dict,
                "emails_processed": summary_dict.get("emails_scanned", 0),
                "rules_applied": summary_dict.get("total_rules_applied", 0),
                "processing_time_seconds": summary_dict.get("total_time_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Background rule processing failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "error_type": "background_processing_error"
            }

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

    async def delete_emails_permanently_tool(
        self, 
        message_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        max_emails: int = 1000,
        batch_size: int = 1000,
        use_async: bool = False
    ) -> Dict[str, Any]:
        """
        Enhanced bulk delete tool supporting both message IDs and query-based deletion.
        Follows Gmail API best practices with efficient batch processing.
        """
        # Validate parameters
        if not message_ids and not query:
            return {
                "success": False, 
                "error_message": "Either 'message_ids' or 'query' must be provided for deletion.", 
                "error_code": "INVALID_PARAMETER", 
                "data": {"deleted_count": 0, "status_message": "No deletion criteria provided."}
            }
        
        if message_ids and query:
            return {
                "success": False,
                "error_message": "Cannot specify both 'message_ids' and 'query'. Choose one deletion method.",
                "error_code": "INVALID_PARAMETER",
                "data": {"deleted_count": 0, "status_message": "Conflicting deletion parameters."}
            }

        try:
            g_client = await self._ensure_g_service_client()
            
            # Handle message_ids approach (existing functionality)
            if message_ids:
                return await self._delete_by_message_ids(g_client, message_ids, batch_size)
            
            # Handle query-based approach (new functionality)
            if query:
                return await self._delete_by_query(g_client, query, max_emails, batch_size, use_async)

        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in delete_emails_permanently_tool: {e}", exc_info=True)
            return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__, "data": {"deleted_count": 0, "status_message": str(e)}}
        except Exception as e:
            logger.error(f"Unexpected error in delete_emails_permanently_tool: {e}", exc_info=True)
            return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR", "data": {"deleted_count": 0, "status_message": f"Unexpected error: {str(e)}"}}

    async def _delete_by_message_ids(self, g_client, message_ids: List[str], batch_size: int) -> Dict[str, Any]:
        """Handle deletion by specific message IDs with batching."""
        if not message_ids:
            return {"success": False, "error_message": "No message IDs provided.", "error_code": "INVALID_PARAMETER", "data": {"deleted_count": 0, "status_message": "No message IDs provided."}}
        
        logger.warning(f"Adapter: PERMANENTLY DELETING {len(message_ids)} emails by IDs. THIS IS IRREVERSIBLE.")
        
        total_deleted = 0
        
        # Process in chunks following Gmail API best practices
        for i in range(0, len(message_ids), batch_size):
            chunk = message_ids[i:i + batch_size]
            logger.debug(f"Processing deletion batch {i//batch_size + 1}: {len(chunk)} emails")
            
            success = self.damien_gmail_integration_module.batch_delete_permanently(
                service=g_client,
                message_ids=chunk
            )
            
            if success:
                total_deleted += len(chunk)
                logger.info(f"Successfully deleted batch of {len(chunk)} emails")
            else:
                logger.error(f"Failed to delete batch of {len(chunk)} emails")
                return {
                    "success": False,
                    "error_message": f"Batch deletion failed after deleting {total_deleted} emails",
                    "error_code": "BATCH_OPERATION_FAILED",
                    "data": {"deleted_count": total_deleted, "status_message": f"Partial deletion: {total_deleted}/{len(message_ids)}"}
                }
        
        status_msg = f"Successfully initiated permanent deletion for {total_deleted} email(s)."
        logger.info(status_msg)
        return {"success": True, "data": {"deleted_count": total_deleted, "status_message": status_msg}}

    async def _delete_by_query(self, g_client, query: str, max_emails: int, batch_size: int, use_async: bool) -> Dict[str, Any]:
        """Handle deletion by Gmail query with efficient batch processing."""
        logger.warning(f"Adapter: PERMANENTLY DELETING emails matching query '{query}' (max: {max_emails}). THIS IS IRREVERSIBLE.")
        
        # For large operations, consider async processing
        if use_async and max_emails >= 500:
            return await self._delete_by_query_async(g_client, query, max_emails, batch_size)
        
        # Get message IDs matching the query
        try:
            # Use existing list_messages functionality to get IDs
            result = self.damien_gmail_integration_module.list_messages(
                service=g_client,
                query_string=query,
                max_results=max_emails,
                page_token=None,
                include_headers=[]  # We only need IDs
            )
            
            if not result or "messages" not in result:
                return {
                    "success": True,
                    "data": {"deleted_count": 0, "status_message": "No emails found matching the query."}
                }
            
            # Extract message IDs
            message_ids = [msg["id"] for msg in result["messages"]]
            
            if not message_ids:
                return {
                    "success": True,
                    "data": {"deleted_count": 0, "status_message": "No emails found matching the query."}
                }
            
            logger.info(f"Found {len(message_ids)} emails matching query '{query}'")
            
            # Use the existing batch deletion logic
            return await self._delete_by_message_ids(g_client, message_ids, batch_size)
            
        except Exception as e:
            logger.error(f"Error getting emails for query '{query}': {e}")
            return {
                "success": False,
                "error_message": f"Failed to retrieve emails for query: {str(e)}",
                "error_code": "QUERY_PROCESSING_ERROR",
                "data": {"deleted_count": 0, "status_message": f"Query failed: {query}"}
            }

    async def _delete_by_query_async(self, g_client, query: str, max_emails: int, batch_size: int) -> Dict[str, Any]:
        """Handle large-scale deletion with async job processing."""
        # Import async processor if available
        try:
            from app.services.async_processor import AsyncProcessor
            
            job_id = f"bulk_delete_{int(time.time())}"
            
            # Create async job for large deletion
            async_processor = AsyncProcessor()
            await async_processor.create_job(
                job_id=job_id,
                job_type="bulk_delete",
                parameters={
                    "query": query,
                    "max_emails": max_emails,
                    "batch_size": batch_size
                }
            )
            
            # Start async processing
            await async_processor.start_bulk_delete_job(job_id, g_client, query, max_emails, batch_size)
            
            return {
                "success": True,
                "data": {
                    "job_id": job_id,
                    "status": "processing",
                    "status_message": f"Async bulk deletion started for query '{query}'. Use job_get_status to track progress."
                }
            }
            
        except ImportError:
            logger.warning("Async processor not available, falling back to synchronous processing")
            return await self._delete_by_query(g_client, query, max_emails, batch_size, use_async=False)

    async def delete_emails_by_query_tool(
        self,
        query: str,
        max_emails: int = 1000,
        batch_size: int = 1000,
        use_async: bool = True,
        optimize_query: bool = True,
        confirm_deletion: bool = False
    ) -> Dict[str, Any]:
        """
        Dedicated bulk delete tool optimized for query-based operations.
        Designed for large-scale email management with safety features.
        """
        # Safety validation
        if not confirm_deletion:
            return {
                "success": False,
                "error_message": "confirm_deletion must be set to true for bulk deletion operations. This action is IRREVERSIBLE.",
                "error_code": "CONFIRMATION_REQUIRED",
                "data": {"deleted_count": 0, "status_message": "Deletion not confirmed."}
            }
        
        logger.warning(f"Adapter: BULK DELETE BY QUERY '{query}' with confirmation. THIS IS IRREVERSIBLE.")
        
        try:
            g_client = await self._ensure_g_service_client()
            
            # Apply query optimization if enabled
            if optimize_query:
                try:
                    from damien_cli.utilities.query_optimizer import optimize_bulk_query
                    optimized_queries = optimize_bulk_query(query, max_emails)
                    
                    if len(optimized_queries) > 1:
                        logger.info(f"Query optimized into {len(optimized_queries)} targeted queries")
                        return await self._delete_optimized_queries(g_client, optimized_queries, max_emails, batch_size, use_async)
                except ImportError:
                    logger.debug("Query optimizer not available, using original query")
            
            # Standard single query deletion
            return await self._delete_by_query(g_client, query, max_emails, batch_size, use_async)
            
        except Exception as e:
            logger.error(f"Error in delete_emails_by_query_tool: {e}", exc_info=True)
            return {
                "success": False,
                "error_message": f"Bulk deletion failed: {str(e)}",
                "error_code": "BULK_DELETE_ERROR",
                "data": {"deleted_count": 0, "status_message": str(e)}
            }

    async def _delete_optimized_queries(self, g_client, optimized_queries: List[str], max_emails: int, batch_size: int, use_async: bool) -> Dict[str, Any]:
        """Handle deletion for multiple optimized queries."""
        total_deleted = 0
        emails_per_query = max(1, max_emails // len(optimized_queries))
        
        for i, opt_query in enumerate(optimized_queries):
            logger.info(f"Processing optimized query {i+1}/{len(optimized_queries)}: {opt_query}")
            
            result = await self._delete_by_query(g_client, opt_query, emails_per_query, batch_size, use_async=False)
            
            if result.get("success", False):
                query_deleted = result.get("data", {}).get("deleted_count", 0)
                total_deleted += query_deleted
                logger.info(f"Deleted {query_deleted} emails from optimized query {i+1}")
            else:
                logger.error(f"Failed to process optimized query {i+1}: {opt_query}")
                return {
                    "success": False,
                    "error_message": f"Optimized query {i+1} failed after deleting {total_deleted} emails",
                    "error_code": "OPTIMIZED_QUERY_FAILED",
                    "data": {"deleted_count": total_deleted, "status_message": f"Partial deletion from {i} optimized queries"}
                }
            
            # Stop if we've reached the max limit
            if total_deleted >= max_emails:
                break
        
        status_msg = f"Successfully deleted {total_deleted} emails using {len(optimized_queries)} optimized queries."
        logger.info(status_msg)
        return {
            "success": True,
            "data": {
                "deleted_count": total_deleted,
                "status_message": status_msg,
                "optimization_used": True,
                "queries_processed": len(optimized_queries)
            }
        }

    async def list_labels_tool(self) -> Dict[str, Any]:
        """List all Gmail labels for the authenticated user.
        
        Returns:
            Dict containing success status and label data including:
            - labels: List of label objects with id, name, type, and metadata
            - total_count: Total number of labels
            - system_labels: Count of system labels (INBOX, SENT, etc.)
            - user_labels: Count of user-created labels
        """
        try:
            g_client = await self._ensure_g_service_client()
            logger.debug("Adapter: Fetching all Gmail labels")
            
            # Use Gmail API to list all labels
            results = g_client.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Process and categorize labels
            processed_labels = []
            system_label_count = 0
            user_label_count = 0
            
            for label in labels:
                label_info = {
                    "id": label.get("id", ""),
                    "name": label.get("name", ""),
                    "type": label.get("type", ""),
                    "messages_total": label.get("messagesTotal", 0),
                    "messages_unread": label.get("messagesUnread", 0),
                    "threads_total": label.get("threadsTotal", 0),
                    "threads_unread": label.get("threadsUnread", 0)
                }
                
                # Categorize labels
                if label.get("type") == "system":
                    system_label_count += 1
                else:
                    user_label_count += 1
                
                processed_labels.append(label_info)
            
            # Sort labels: system labels first, then user labels alphabetically
            processed_labels.sort(key=lambda x: (x["type"] != "system", x["name"].lower()))
            
            status_msg = f"Successfully retrieved {len(processed_labels)} labels ({system_label_count} system, {user_label_count} user-created)"
            logger.info(status_msg)
            
            return {
                "success": True,
                "data": {
                    "labels": processed_labels,
                    "total_count": len(processed_labels),
                    "system_labels": system_label_count,
                    "user_labels": user_label_count,
                    "status_message": status_msg
                }
            }
            
        except (DamienError, GmailApiError, InvalidParameterError) as e:
            logger.error(f"Error in list_labels_tool: {e}", exc_info=True)
            return {
                "success": False,
                "error_message": str(e),
                "error_code": e.__class__.__name__,
                "data": {
                    "labels": [],
                    "total_count": 0,
                    "system_labels": 0,
                    "user_labels": 0,
                    "status_message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error in list_labels_tool: {e}", exc_info=True)
            return {
                "success": False,
                "error_message": f"Unexpected error: {str(e)}",
                "error_code": "UNEXPECTED_ADAPTER_ERROR",
                "data": {
                    "labels": [],
                    "total_count": 0,
                    "system_labels": 0,
                    "user_labels": 0,
                    "status_message": f"Unexpected error: {str(e)}"
                }
            }

    # Add more methods for other tools here
