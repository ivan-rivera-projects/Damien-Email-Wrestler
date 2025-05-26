"""
MCP Tool Usage Enforcement Middleware
Tracks direct MCP tool usage vs API fallback usage
"""

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ToolUsageEnforcementMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, warn_on_api_usage: bool = True):
        super().__init__(app)
        self.warn_on_api_usage = warn_on_api_usage
        self.usage_stats = {
            "mcp_direct_calls": 0,
            "api_fallback_calls": 0,
            "total_requests": 0
        }
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Track request type
        is_api_fallback = request.url.path.startswith("/mcp/execute_tool")
        is_direct_mcp = hasattr(request, 'mcp_tool_call') 
        
        self.usage_stats["total_requests"] += 1
        
        if is_api_fallback:
            self.usage_stats["api_fallback_calls"] += 1
            if self.warn_on_api_usage:
                logger.warning(
                    f"API fallback used for tool execution. "
                    f"Direct MCP tools should be preferred. "
                    f"Path: {request.url.path}"
                )
        elif is_direct_mcp:
            self.usage_stats["mcp_direct_calls"] += 1
            logger.info("Direct MCP tool call - optimal usage")
        
        # Process request
        response = await call_next(request)
        
        # Add usage headers
        response.headers["X-Tool-Usage-Type"] = "api-fallback" if is_api_fallback else "direct-mcp"
        response.headers["X-Tool-Usage-Stats"] = str(self.usage_stats)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get usage statistics report"""
        total = self.usage_stats["total_requests"]
        if total > 0:
            mcp_percentage = (self.usage_stats["mcp_direct_calls"] / total) * 100
            api_percentage = (self.usage_stats["api_fallback_calls"] / total) * 100
        else:
            mcp_percentage = api_percentage = 0
            
        return {
            **self.usage_stats,
            "mcp_usage_percentage": round(mcp_percentage, 2),
            "api_fallback_percentage": round(api_percentage, 2),
            "efficiency_score": round(mcp_percentage, 2)
        }
