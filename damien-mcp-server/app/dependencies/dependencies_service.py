# Updated to try and break caching
"""FastAPI dependencies for the MCP server.

This module provides FastAPI dependencies that can be injected into route handlers.
Dependencies include things like getting an authenticated Gmail service client.
"""

from fastapi import HTTPException, status, Depends
from typing import Any, Optional
import logging
# import importlib # No longer needed

# Import Damien core_api components
from damien_cli.core_api import gmail_api_service
from damien_cli.core_api.exceptions import DamienError, GmailApiError

# Import local settings
from ..core.config import settings # Changed to ..core

# Standard top-level import for DamienAdapter
from ..services.damien_adapter import DamienAdapter # Changed to ..services

# Set up logger
logger = logging.getLogger("damien_mcp_server_app") # Use the configured app logger

# The get_g_service_client logic has been moved into DamienAdapter._ensure_g_service_client()
# So, the standalone get_g_service_client dependency is removed from this file.

async def get_damien_adapter() -> DamienAdapter: # No longer depends on a g_client parameter
    """Dependency to get an instance of DamienAdapter.
        
    Returns:
        DamienAdapter: An instance of DamienAdapter.
                       The adapter now manages its own Gmail client initialization.
    """
    # DamienAdapter now manages its own g_service_client internally
    adapter_instance = DamienAdapter()
    return adapter_instance


def get_damien_adapter_instance() -> DamienAdapter:
    """Get a DamienAdapter instance for non-FastAPI contexts like async tasks.
    
    Returns:
        DamienAdapter: An instance of DamienAdapter for background processing.
    """
    return DamienAdapter()
