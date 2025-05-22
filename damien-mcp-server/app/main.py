"""Main FastAPI application for the Damien MCP Server.

This module initializes the FastAPI application and sets up routes and middleware.
It serves as the entry point for the server.
"""

from fastapi import FastAPI, Depends
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import our security dependency for API key verification
from .core.security import verify_api_key

# Import our dependency for getting DamienAdapter
from .dependencies.dependencies_service import get_damien_adapter # Changed from get_g_service_client
from .services.damien_adapter import DamienAdapter # To type hint adapter

# Import routers
from .routers import tools as tools_router

app = FastAPI(
    title="Damien MCP Server", 
    version="0.1.0",
    description="An MCP server for Damien-CLI functionalities, allowing AI assistants like Claude to manage Gmail.",
)


@app.get("/health", summary="Health Check", tags=["System"])
async def health_check():
    """Checks if the server is running. This endpoint is publicly accessible."""
    return {"status": "ok", "message": "Damien MCP Server is healthy!"}


@app.get("/mcp/protected-test", 
         summary="Test Protected Endpoint", 
         tags=["Test"],
         dependencies=[Depends(verify_api_key)])
async def protected_test_route():
    """A test endpoint to verify that API key authentication is working.
    
    This endpoint requires a valid API key in the X-API-Key header.
    """
    return {"message": "Access granted to protected route!"}


@app.get("/mcp/gmail-test", 
         summary="Test Gmail Connection",
         tags=["Test"],
         dependencies=[Depends(verify_api_key)])
async def gmail_test_route(adapter: DamienAdapter = Depends(get_damien_adapter)): # Depend on adapter
   """A test endpoint to verify that Gmail authentication is working.
   
   This endpoint requires a valid API key and tests the Gmail service client connection
   by asking the adapter to ensure its client is initialized.
   """
   try:
       # Ask the adapter to ensure its client is ready (this will initialize it if not)
       g_client = await adapter._ensure_g_service_client() # Call the adapter's method
       
       return {
           "message": "Gmail authentication successful via DamienAdapter!",
           "gmail_client_type": str(type(g_client).__name__)
       }
   except Exception as e:
       logger.error(f"Error in /mcp/gmail-test: {e}", exc_info=True)
       raise HTTPException(
           status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
           detail=f"Failed to initialize Gmail service via adapter: {str(e)}"
       )


# Later, routers will be included here:
# from .routers import context
# app.include_router(context.router, prefix="/mcp/context", tags=["MCP Context"], dependencies=[Depends(verify_api_key)])

# Include the tools router
app.include_router(
    tools_router.router,
    prefix="/mcp",
    tags=["MCP Tools"],
    dependencies=[Depends(verify_api_key)]
)
