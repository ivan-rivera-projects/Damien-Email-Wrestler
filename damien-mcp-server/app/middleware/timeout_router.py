"""
Timeout-Aware Routing Middleware for Claude Code MCP Optimization

This middleware automatically routes long-running operations to async versions
and returns job IDs immediately to prevent timeout issues in Claude Code.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolProfile:
    """Performance profile for a tool."""
    estimated_seconds: float
    has_async_version: bool
    async_tool_name: Optional[str] = None
    fast_params_threshold: Optional[Dict[str, Any]] = None


class TimeoutAwareRouter:
    """Routes tools based on estimated execution time to prevent timeouts."""
    
    # Timeout threshold for Claude Code (30 seconds with safety margin)
    CLAUDE_CODE_TIMEOUT = 25.0  # 5 second safety margin
    
    def __init__(self):
        """Initialize with tool performance profiles."""
        self.tool_profiles = {
            # AI Analysis Tools (Long-running)
            "damien_ai_analyze_emails": ToolProfile(
                estimated_seconds=60.0,
                has_async_version=True,
                async_tool_name="damien_ai_analyze_emails_async"
            ),
            "damien_ai_suggest_rules": ToolProfile(
                estimated_seconds=45.0,
                has_async_version=False  # Could be added
            ),
            "damien_ai_get_insights": ToolProfile(
                estimated_seconds=30.0,
                has_async_version=False
            ),
            "damien_ai_optimize_inbox": ToolProfile(
                estimated_seconds=120.0,
                has_async_version=False  # Could be added
            ),
            
            # Settings and System Tools (Fast)
            "damien_get_settings": ToolProfile(
                estimated_seconds=15.0,
                has_async_version=False
            ),
            "damien_list_labels": ToolProfile(
                estimated_seconds=10.0,
                has_async_version=False
            ),
            "damien_ai_quick_test": ToolProfile(
                estimated_seconds=5.0,
                has_async_version=False
            ),
            
            # Email Operations (Variable)
            "damien_list_emails": ToolProfile(
                estimated_seconds=15.0,  # Base time
                has_async_version=False,
                fast_params_threshold={"max_results": 50}  # Fast if ≤50 emails
            ),
            "damien_get_email_details": ToolProfile(
                estimated_seconds=5.0,
                has_async_version=False
            ),
            "damien_trash_emails": ToolProfile(
                estimated_seconds=20.0,
                has_async_version=True,
                async_tool_name="damien_trash_emails_by_query",
                fast_params_threshold={"message_count": 10}  # Fast if ≤10 emails
            ),
            
            # Enhanced Operations (Designed for large scale)
            "damien_trash_emails_by_query": ToolProfile(
                estimated_seconds=90.0,
                has_async_version=False  # Already optimized
            ),
            "damien_smart_trash_marketing": ToolProfile(
                estimated_seconds=75.0,
                has_async_version=False  # Already optimized  
            ),
            
            # Organization Tools (Medium)
            "damien_organize_emails": ToolProfile(
                estimated_seconds=35.0,
                has_async_version=False
            ),
            "damien_smart_rule": ToolProfile(
                estimated_seconds=25.0,
                has_async_version=False
            ),
            
            # Job Management (Always Fast)
            "damien_job_get_status": ToolProfile(
                estimated_seconds=2.0,
                has_async_version=False
            ),
            "damien_job_get_result": ToolProfile(
                estimated_seconds=3.0,
                has_async_version=False
            ),
            "damien_job_cancel": ToolProfile(
                estimated_seconds=2.0,
                has_async_version=False
            ),
            "damien_job_list": ToolProfile(
                estimated_seconds=2.0,
                has_async_version=False
            )
        }
        
        logger.info(f"TimeoutAwareRouter initialized with {len(self.tool_profiles)} tool profiles")
    
    def estimate_execution_time(self, tool_name: str, params: Dict[str, Any]) -> float:
        """Estimate execution time for a tool with given parameters."""
        if tool_name not in self.tool_profiles:
            # Unknown tool - assume moderate time
            logger.warning(f"No profile for tool '{tool_name}', assuming 30s execution time")
            return 30.0
        
        profile = self.tool_profiles[tool_name]
        base_time = profile.estimated_seconds
        
        # Adjust based on parameters
        if profile.fast_params_threshold:
            for param_name, threshold in profile.fast_params_threshold.items():
                param_value = params.get(param_name, 0)
                
                # Convert string parameters to int for comparison
                try:
                    if isinstance(param_value, str):
                        param_value = int(param_value)
                except (ValueError, TypeError):
                    param_value = 0
                
                # Handle different parameter types
                if param_name == "max_results" and param_value <= threshold:
                    # Small result set - reduce time estimate
                    base_time *= 0.5
                elif param_name == "message_count" and param_value <= threshold:
                    # Small email batch - reduce time estimate  
                    base_time *= 0.3
                elif param_name in params:
                    # Parameter-specific adjustments
                    if param_name == "days" and param_value <= 7:
                        base_time *= 0.7  # Shorter time range
                    elif param_name == "target_count" and param_value <= 100:
                        base_time *= 0.6  # Smaller analysis scope
        
        logger.debug(f"Estimated execution time for {tool_name}: {base_time:.1f}s")
        return base_time
    
    def should_route_to_async(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Determine if a tool should be routed to its async version.
        
        Returns:
            Tuple of (should_route, async_tool_name)
        """
        estimated_time = self.estimate_execution_time(tool_name, params)
        
        if estimated_time <= self.CLAUDE_CODE_TIMEOUT:
            # Fast enough for synchronous execution
            return False, None
        
        # Tool is too slow, check if async version exists
        if tool_name not in self.tool_profiles:
            return False, None
        
        profile = self.tool_profiles[tool_name]
        
        if profile.has_async_version and profile.async_tool_name:
            logger.info(
                f"Routing {tool_name} to async version {profile.async_tool_name} "
                f"(estimated {estimated_time:.1f}s > {self.CLAUDE_CODE_TIMEOUT}s threshold)"
            )
            return True, profile.async_tool_name
        
        # No async version available - will timeout
        logger.warning(
            f"Tool {tool_name} estimated at {estimated_time:.1f}s will likely timeout "
            f"(threshold: {self.CLAUDE_CODE_TIMEOUT}s) but no async version available"
        )
        return False, None
    
    def route_tool_request(self, tool_name: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool]:
        """
        Route a tool request to the optimal execution path.
        
        Returns:
            Tuple of (final_tool_name, final_params, is_async_route)
        """
        should_async, async_tool_name = self.should_route_to_async(tool_name, params)
        
        if should_async and async_tool_name:
            # Route to async version
            logger.info(f"🚀 ASYNC ROUTE: {tool_name} → {async_tool_name}")
            return async_tool_name, params, True
        else:
            # Use original tool
            estimated_time = self.estimate_execution_time(tool_name, params)
            route_type = "FAST" if estimated_time <= self.CLAUDE_CODE_TIMEOUT else "SLOW"
            logger.info(f"⚡ {route_type} ROUTE: {tool_name} (estimated: {estimated_time:.1f}s)")
            return tool_name, params, False
    
    def add_tool_profile(self, tool_name: str, profile: ToolProfile):
        """Add or update a tool profile."""
        self.tool_profiles[tool_name] = profile
        logger.info(f"Added/updated profile for tool: {tool_name}")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics for monitoring."""
        fast_tools = sum(1 for p in self.tool_profiles.values() 
                        if p.estimated_seconds <= self.CLAUDE_CODE_TIMEOUT)
        slow_tools = len(self.tool_profiles) - fast_tools
        async_available = sum(1 for p in self.tool_profiles.values() if p.has_async_version)
        
        return {
            "total_tools_profiled": len(self.tool_profiles),
            "fast_tools": fast_tools,
            "slow_tools": slow_tools,
            "async_versions_available": async_available,
            "timeout_threshold_seconds": self.CLAUDE_CODE_TIMEOUT,
            "coverage_percentage": round((len(self.tool_profiles) / 46) * 100, 1)  # Assuming 46 total tools
        }


# Global router instance
timeout_router = TimeoutAwareRouter()