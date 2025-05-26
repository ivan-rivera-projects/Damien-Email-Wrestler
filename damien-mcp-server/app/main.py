"""Main FastAPI application for the Damien MCP Server.

This module initializes the FastAPI application and sets up routes and middleware.
It serves as the entry point for the server.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Body # Added Body
from typing import Optional
import logging

# Import core components
from .core.config import settings # For log level
from .core.logging_setup import setup_logging # New logging setup

# Initialize logging for the application
# This should be called once when the application starts.
# The logger instance can then be retrieved by name in other modules.
setup_logging(log_level_str=settings.log_level)
logger = logging.getLogger("damien_mcp_server_app") # Use the configured app logger

# Import our security dependency for API key verification
from .core.security import verify_api_key

# Import our dependency for getting DamienAdapter
from .dependencies.dependencies_service import get_damien_adapter # Changed from get_g_service_client
from .services.damien_adapter import DamienAdapter # To type hint adapter

# Import routers
from .routers import tools as tools_router

app = FastAPI(
    title="Damien MCP Server",
    description="MCP Server for Damien Email Management - Direct MCP tools prioritized over API endpoints",
    version="1.0.0"
)

# Import tool registration functions
from .tools.draft_tools import register_draft_tools
from .tools.settings_tools import register_settings_tools
from .services.tool_registry import tool_registry

@app.on_event("startup")
async def startup_event():
    """Initialize MCP server and register tools."""
    # Register all tool categories
    register_draft_tools()
    register_settings_tools()
    
    logger.info(f"MCP Server started with {len(tool_registry.get_all_tools())} tools registered")


@app.get("/health", summary="Health Check", tags=["System"])
async def health_check():
    """Checks if the server is running. This endpoint is publicly accessible."""
    from .core.tool_usage_config import get_tool_usage_config
    config = get_tool_usage_config()
    
    return {
        "status": "ok", 
        "message": "Damien MCP Server is healthy!",
        "tool_usage": {
            "policy": config.policy,
            "message": config.direct_tool_message,
            "recommended_approach": "Use direct MCP tools for optimal performance"
        }
    }


@app.get("/mcp/tool-usage-policy", 
         summary="Get Tool Usage Policy",
         tags=["Configuration"],
         dependencies=[Depends(verify_api_key)])
async def get_tool_usage_policy():
    """Get current tool usage policy configuration."""
    from .core.tool_usage_config import get_tool_usage_config
    config = get_tool_usage_config()
    
    return {
        "policy": config.policy,
        "warn_on_api_usage": config.warn_on_api_usage,
        "add_tool_usage_headers": config.add_tool_usage_headers,
        "direct_tool_message": config.direct_tool_message,
        "guidance": "MCP Server is configured to prioritize direct tool calls over API endpoints"
    }


@app.post("/mcp/tool-usage-policy",
          summary="Update Tool Usage Policy", 
          tags=["Configuration"],
          dependencies=[Depends(verify_api_key)])
async def update_tool_usage_policy(policy_update: dict = Body(...)):
    """Update tool usage policy configuration.
    
    Body should be a JSON object with one or more of these properties:
    - policy: "direct_mcp_preferred" or "direct_mcp_only"
    - warn_on_api_usage: true/false
    - add_tool_usage_headers: true/false
    """
    from .core.tool_usage_config import update_tool_usage_config, ToolUsagePolicy
    
    update_params = {}
    
    if "policy" in policy_update:
        policy = policy_update["policy"]
        try:
            valid_policies = [p.value for p in ToolUsagePolicy]
            if policy not in valid_policies:
                raise ValueError(f"Invalid policy: {policy}")
            update_params["policy"] = policy
        except ValueError as e:
            valid_policies_str = ", ".join([p.value for p in ToolUsagePolicy])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid policy value. Valid options are: {valid_policies_str}"
            )
            
    if "warn_on_api_usage" in policy_update:
        update_params["warn_on_api_usage"] = policy_update["warn_on_api_usage"]
        
    if "add_tool_usage_headers" in policy_update:
        update_params["add_tool_usage_headers"] = policy_update["add_tool_usage_headers"]
    
    updated_config = update_tool_usage_config(**update_params)
    
    return {
        "message": "Tool usage policy updated successfully",
        "updated_config": {
            "policy": updated_config.policy,
            "warn_on_api_usage": updated_config.warn_on_api_usage,
            "add_tool_usage_headers": updated_config.add_tool_usage_headers,
            "direct_tool_message": updated_config.direct_tool_message
        }
    }


@app.get("/mcp/gmail-test", 
         summary="Test Gmail Connection",
         tags=["Test"],
         dependencies=[Depends(verify_api_key)])
async def gmail_test_route(adapter: DamienAdapter = Depends(get_damien_adapter)):
    """Test Gmail connection via the adapter."""
    try:
        # This will test Gmail authentication without performing any actual operations
        await adapter._ensure_g_service_client()
        return {"message": "Gmail connection successful!"}
    except Exception as e:
        logger.error(f"Gmail test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gmail connection failed: {str(e)}"
        )
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
