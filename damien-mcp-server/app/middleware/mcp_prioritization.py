"""
MCP Tool Prioritization Middleware
Automatically enforces direct MCP tool usage and deprecates API endpoints
"""

from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import json
from typing import Dict, Any

from ..core.tool_usage_config import get_tool_usage_config, ToolUsagePolicy

logger = logging.getLogger("damien_mcp_server_app")

class MCPToolPrioritizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.usage_stats = {
            "mcp_direct_calls": 0,
            "api_calls": 0,
            "total_requests": 0,
            "efficiency_score": 100.0
        }

    async def dispatch(self, request: Request, call_next):
        config = get_tool_usage_config()
        start_time = time.time()
        
        # Track and analyze request
        request_analysis = self._analyze_request(request)
        self.usage_stats["total_requests"] += 1
        
        # Handle API endpoint requests based on policy
        if request_analysis["is_api_endpoint"]:
            self.usage_stats["api_calls"] += 1
            
            if config.default_policy == ToolUsagePolicy.DIRECT_MCP_ONLY:
                return await self._reject_api_request(request_analysis)
            
            if config.warn_on_api_usage:
                logger.warning(
                    f"API endpoint used instead of direct MCP tools. "
                    f"Tool: {request_analysis['tool_name']} "
                    f"Path: {request.url.path}"
                )
        
        elif request_analysis["is_mcp_tool"]:
            self.usage_stats["mcp_direct_calls"] += 1
            if config.log_tool_usage:
                logger.info(f"Direct MCP tool call: {request_analysis['tool_name']}")
        
        # Process the request
        response = await call_next(request)
        
        # Add enforcement headers
        if config.return_usage_headers:
            self._add_usage_headers(response, request_analysis, start_time)
        
        # Update efficiency score
        self._update_efficiency_score()
        
        return response    
    def _analyze_request(self, request: Request) -> Dict[str, Any]:
        """Analyze the incoming request to determine its type"""
        path = request.url.path
        
        # Detect API endpoint usage
        is_api_endpoint = path.startswith("/mcp/execute_tool")
        
        # Detect direct MCP tool usage (these come through different mechanisms)
        is_mcp_tool = (
            hasattr(request.state, 'mcp_tool_call') or
            path.startswith("/tools/") or
            request.headers.get("X-MCP-Tool-Call") == "direct"
        )
        
        # Extract tool name if possible
        tool_name = None
        if is_api_endpoint and hasattr(request, '_json'):
            try:
                body = request._json
                tool_name = body.get('tool_name')
            except:
                pass
        elif is_mcp_tool:
            tool_name = path.split('/')[-1] if '/' in path else None
        
        return {
            "is_api_endpoint": is_api_endpoint,
            "is_mcp_tool": is_mcp_tool,
            "tool_name": tool_name,
            "path": path,
            "method": request.method
        }
    
    async def _reject_api_request(self, request_analysis: Dict[str, Any]) -> JSONResponse:
        """Reject API requests when direct MCP only policy is active"""
        return JSONResponse(
            status_code=422,
            content={
                "error": "API endpoints disabled - use direct MCP tools only",
                "message": f"Tool '{request_analysis['tool_name']}' should be called directly via MCP interface",
                "enforcement_policy": "direct_mcp_only",
                "suggested_action": f"Use damien_{request_analysis['tool_name']} tool directly",
                "documentation": "/docs for available MCP tools"
            }
        )
    
    def _add_usage_headers(self, response: Response, request_analysis: Dict[str, Any], start_time: float):
        """Add tool usage tracking headers to response"""
        process_time = time.time() - start_time
        
        response.headers["X-Tool-Usage-Type"] = (
            "api-endpoint" if request_analysis["is_api_endpoint"] 
            else "direct-mcp" if request_analysis["is_mcp_tool"]
            else "other"
        )
        response.headers["X-Tool-Name"] = request_analysis["tool_name"] or "unknown"
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Efficiency-Score"] = f"{self.usage_stats['efficiency_score']:.1f}"
        response.headers["X-MCP-Preferred"] = "true"
        
        # Add suggestion for API users
        if request_analysis["is_api_endpoint"]:
            response.headers["X-Suggestion"] = f"Use damien_{request_analysis['tool_name']} directly for better performance"
    
    def _update_efficiency_score(self):
        """Update efficiency score based on MCP vs API usage ratio"""
        total = self.usage_stats["total_requests"]
        if total > 0:
            mcp_ratio = self.usage_stats["mcp_direct_calls"] / total
            self.usage_stats["efficiency_score"] = mcp_ratio * 100
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        total = self.usage_stats["total_requests"]
        if total > 0:
            mcp_percentage = (self.usage_stats["mcp_direct_calls"] / total) * 100
            api_percentage = (self.usage_stats["api_calls"] / total) * 100
        else:
            mcp_percentage = api_percentage = 0
        
        return {
            **self.usage_stats,
            "mcp_usage_percentage": round(mcp_percentage, 2),
            "api_usage_percentage": round(api_percentage, 2),
            "efficiency_rating": "excellent" if mcp_percentage > 80 else "good" if mcp_percentage > 60 else "needs_improvement",
            "recommendation": "Increase direct MCP tool usage for better performance" if mcp_percentage < 80 else "Great tool usage patterns!"
        }
