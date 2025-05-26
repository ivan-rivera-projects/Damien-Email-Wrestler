"""
Simple MCP Server Tool Usage Configuration
Prioritizes direct MCP tool usage over API endpoints
"""

from enum import Enum
from pydantic import BaseModel

class ToolUsagePolicy(str, Enum):
    """Policy for tool usage prioritization"""
    DIRECT_MCP_PREFERRED = "direct_mcp_preferred"  # Default: Direct MCP tools preferred, API allowed
    DIRECT_MCP_ONLY = "direct_mcp_only"            # Strict: Only direct MCP tools allowed

class ToolUsageConfig(BaseModel):
    """Simple configuration for tool usage preferences"""
    
    # Primary policy setting
    policy: ToolUsagePolicy = ToolUsagePolicy.DIRECT_MCP_PREFERRED
    
    # Basic control settings
    warn_on_api_usage: bool = True
    add_tool_usage_headers: bool = True
    
    # Documentation and guidance
    direct_tool_message: str = "For optimal performance, use direct MCP tools instead of API endpoints"

# Global configuration instance
tool_usage_config = ToolUsageConfig()

def get_tool_usage_config() -> ToolUsageConfig:
    """Get the current tool usage configuration"""
    return tool_usage_config

def update_tool_usage_config(policy: ToolUsagePolicy = None, **kwargs) -> ToolUsageConfig:
    """Update tool usage configuration with new values"""
    global tool_usage_config
    
    if policy is not None:
        # Make sure we're handling the enum value correctly
        if isinstance(policy, str):
            try:
                policy = ToolUsagePolicy(policy)
            except ValueError:
                # Default to current policy if invalid string
                pass
        if isinstance(policy, ToolUsagePolicy):
            tool_usage_config.policy = policy
        
    for key, value in kwargs.items():
        if hasattr(tool_usage_config, key):
            setattr(tool_usage_config, key, value)
            
    return tool_usage_config
