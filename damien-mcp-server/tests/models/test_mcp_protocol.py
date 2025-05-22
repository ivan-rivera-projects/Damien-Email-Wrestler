"""Tests for MCP protocol models."""

import pytest
from pydantic import ValidationError
from app.models.mcp_protocol import (
    MCPToolCallInput, 
    MCPExecuteToolServerRequest, 
    MCPExecuteToolServerResponse
)


def test_mcp_tool_call_input_basic():
    """Test the base MCPToolCallInput model."""
    # Simple case: no fields required
    tool_input = MCPToolCallInput()
    assert tool_input.model_dump() == {}
    
    # Extra fields should be allowed
    tool_input = MCPToolCallInput(extra_field="value")
    assert tool_input.model_dump() == {"extra_field": "value"}


def test_mcp_execute_tool_server_request():
    """Test the MCPExecuteToolServerRequest model."""
    # Valid request
    request_data = {
        "tool_name": "damien_list_emails",
        "input": {"query": "is:unread", "max_results": 5},
        "session_id": "test_session_123"
    }
    request = MCPExecuteToolServerRequest(**request_data)
    assert request.tool_name == "damien_list_emails"
    assert request.input == {"query": "is:unread", "max_results": 5}
    assert request.session_id == "test_session_123"
    assert request.user_id == "damien_user_default"  # Default value
    
    # Custom user_id
    request_data["user_id"] = "custom_user"
    request = MCPExecuteToolServerRequest(**request_data)
    assert request.user_id == "custom_user"
    
    # Missing required fields
    with pytest.raises(ValidationError):
        MCPExecuteToolServerRequest(input={}, session_id="test")  # Missing tool_name
    
    with pytest.raises(ValidationError):
        MCPExecuteToolServerRequest(tool_name="test", session_id="test")  # Missing input
    
    with pytest.raises(ValidationError):
        MCPExecuteToolServerRequest(tool_name="test", input={})  # Missing session_id


def test_mcp_execute_tool_server_response():
    """Test the MCPExecuteToolServerResponse model."""
    # Success response
    response = MCPExecuteToolServerResponse(
        is_error=False,
        output={"emails": [{"id": "123", "subject": "Test"}]}
    )
    assert response.is_error is False
    assert response.output == {"emails": [{"id": "123", "subject": "Test"}]}
    assert response.error_message is None
    assert response.tool_result_id is not None  # UUID should be generated
    
    # Error response
    response = MCPExecuteToolServerResponse(
        is_error=True,
        error_message="Test error message"
    )
    assert response.is_error is True
    assert response.output is None
    assert response.error_message == "Test error message"
    assert response.tool_result_id is not None
    
    # Custom tool_result_id
    response = MCPExecuteToolServerResponse(
        tool_result_id="custom_id_123",
        is_error=False,
        output={"result": "test"}
    )
    assert response.tool_result_id == "custom_id_123"
