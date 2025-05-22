"""Pydantic models for the MCP general protocol structures.

This module defines the Pydantic models that represent the core MCP (Model Context Protocol)
data structures used for communication between the MCP client (e.g., Claude) and the
Damien MCP Server.

The models include:
1. MCPToolCallInput - Base class for tool-specific input parameters
2. MCPExecuteToolServerRequest - Request structure for executing a tool
3. MCPExecuteToolServerResponse - Response structure with tool results or errors

These models provide validation, serialization, and documentation for the MCP protocol
data structures, ensuring type safety and consistent API interactions.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import uuid

class MCPToolCallInput(BaseModel):
    """
    Base model for specific tool inputs.
    
    This class serves as a base class for all tool-specific parameter models.
    It allows for extensibility while maintaining a consistent structure.
    
    Example usage:
        class ListEmailsParams(MCPToolCallInput):
            query: Optional[str] = None
            max_results: int = 10
    
    Note:
        The extra="allow" configuration permits additional fields beyond those
        defined in subclasses, which can be useful during development or for
        backward compatibility as tools evolve.
    """
    # Using model_config to allow extra fields if a tool sends more than defined,
    # though strict parsing into specific models is preferred at the tool dispatch level.
    model_config = {"extra": "allow"} 
    pass


class MCPExecuteToolServerRequest(BaseModel):
    """Request model for the server's /execute_tool endpoint.
    
    This model defines the structure of requests sent to the /execute_tool endpoint.
    It contains all the information needed to execute a specific tool and maintain
    session context across multiple interactions.
    
    Attributes:
        tool_name: The name of the tool to execute (e.g., "damien_list_emails")
        input: Tool-specific parameters, which will be parsed into the appropriate
               MCPToolCallInput subclass based on the tool_name
        session_id: Unique identifier for the conversation session, used for
                   maintaining context across multiple interactions
        user_id: Identifier for the user, defaults to a generic user ID for
                single-user deployments
    
    Note:
        The tool_name must match one of the tools registered in the tools router.
        The input dictionary must contain valid parameters for the specified tool.
    """
    tool_name: str
    input: Dict[str, Any] # Tool-specific parameters, to be parsed into a specific MCPToolCallInput subclass
    session_id: str
    user_id: str = Field(default="damien_user_default") # Default user for now, can be overridden
    # context_id: Optional[str] = None # Consider adding if needed for chaining within a session


class MCPExecuteToolServerResponse(BaseModel):
    """Response model for the server's /execute_tool endpoint.
    
    This model defines the structure of responses returned from the /execute_tool endpoint.
    It contains either the successful result of the tool execution or error information.
    
    Attributes:
        tool_result_id: Unique identifier for this tool execution result,
                       generated automatically if not provided
        is_error: Flag indicating whether an error occurred during tool execution
        output: The tool's output data, structure varies by tool (null if error)
        error_message: Human-readable error message (null if success)
    
    Note:
        Even when is_error is True, the response HTTP status code is still 200.
        Error handling is done within the MCP protocol layer, not at the HTTP level.
        This allows the MCP client to handle tool-specific errors gracefully.
    """
    tool_result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # tool_name: str # Implicit from the request, not usually in MCP response
    is_error: bool = False
    output: Optional[Any] = None # Can be a dict, string, list.
    error_message: Optional[str] = None