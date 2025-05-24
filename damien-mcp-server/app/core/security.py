"""Security implementation for the MCP server.

This module provides authentication and security features for protecting
the MCP server API endpoints. It implements API key verification for incoming
requests using FastAPI dependency injection.
"""

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
import secrets  # For comparing keys securely
from .config import settings  # Settings singleton from config.py

# Define where the API key is expected in the header
# MCP typically uses "Authorization: Bearer <token>" or a custom header.
# We're using a custom header "X-API-Key" for simplicity
API_KEY_HEADER_NAME = "X-API-Key"
api_key_header_auth = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=True)


async def verify_api_key(api_key_header: str = Security(api_key_header_auth)):
    """Dependency to verify the provided API key against the configured server API key.
    
    Args:
        api_key_header: The API key from the request header, injected by FastAPI
        
    Returns:
        True if the key is valid
        
    Raises:
        HTTPException: If the key is invalid or missing, or if the server is not configured properly
    """
    # Import logging here to avoid circular imports
    import logging
    logger = logging.getLogger("damien_mcp_server_app")
    
    if not settings.api_key:
        # This is a server configuration error, should not happen in prod
        logger.error("API Key not configured on server")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key not configured on server."
        )
    
    # Debug logging for authentication issues
    logger.info(f"=== API KEY AUTHENTICATION ===")
    logger.info(f"Received API key: {api_key_header[:10]}... (first 10 chars)")
    logger.info(f"Expected API key: {settings.api_key[:10]}... (first 10 chars)")
    logger.info(f"Full received key length: {len(api_key_header) if api_key_header else 'None'}")
    logger.info(f"Full expected key length: {len(settings.api_key)}")
    
    # Securely compare the provided key with the configured key
    # secrets.compare_digest is used to prevent timing attacks
    if not secrets.compare_digest(api_key_header, settings.api_key):
        logger.warning(f"API key mismatch - denying access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key."
        )
    
    logger.info("API key authentication successful")
    # If key is valid, the dependency allows the request to proceed.
    # We don't need to return anything specific here unless the key implies a user/tenant.
    # For now, it just grants access.
    return True  # Or return the key if you want to log it, etc.
