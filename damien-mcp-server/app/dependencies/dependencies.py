"""FastAPI dependencies for the MCP server.

This module provides FastAPI dependencies that can be injected into route handlers.
Dependencies include things like getting an authenticated Gmail service client.
"""

from fastapi import HTTPException, status, Depends
from typing import Any, Optional
import logging

# Import Damien core_api components
from damien_cli.core_api import gmail_api_service
from damien_cli.core_api.exceptions import DamienError, GmailApiError

# Import local settings
from .core.config import settings

# Set up logger
logger = logging.getLogger(__name__)


async def get_g_service_client() -> Any:
    """Dependency to get an authenticated Gmail API service client.
    
    Uses the non-interactive method from Damien's core_api to get an
    authenticated Gmail service client. This would typically be used by
    the DamienAdapter.
    
    Returns:
        Any: The authenticated Google API client resource for Gmail
        
    Raises:
        HTTPException: If authentication fails or another error occurs
    """
    try:
        # These paths come from the MCP server's config
        client = gmail_api_service.get_g_service_client_from_token(
            token_file_path_str=settings.gmail_token_path,
            credentials_file_path_str=settings.gmail_credentials_path,
            scopes=settings.gmail_scopes
        )
        
        if client is None:  # Should not happen if get_g_service_client_from_token raises on failure
            logger.error("Gmail service client initialization returned None")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to initialize Gmail service client (returned None)."
            )
            
        return client
        
    except DamienError as e:  # Catch specific errors from Damien's auth logic
        logger.error(f"Gmail authentication error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gmail authentication error: {e}"
        )
        
    except Exception as e:  # Catch any other unexpected error
        logger.error(f"Unexpected error initializing Gmail service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error initializing Gmail service: {e}"
        )


# Note: The DamienAdapter class will be implemented in a future step.
# It will use the g_service_client to interact with Damien's core_api.
# For now, we just have the dependency to get the g_service_client.

# Example of what will come later:
# class DamienAdapter:
#     def __init__(self, g_service_client: Any):
#         self.g_service_client = g_service_client
#         # self.gmail_api = damien_cli.core_api.gmail_api_service
#         # self.rules_api = damien_cli.core_api.rules_api_service
#     
#     async def list_emails(self, query: Optional[str] = None, max_results: int = 10):
#         # Implementation here
#         pass
# 
# async def get_damien_adapter(g_client: Any = Depends(get_g_service_client)):
#     return DamienAdapter(g_client)
