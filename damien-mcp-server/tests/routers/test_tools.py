"""Tests for the tools router."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.tools import router


@pytest.fixture
def mock_adapter():
    """Creates a mock DamienAdapter."""
    adapter = MagicMock()
    adapter.list_emails_tool = MagicMock(return_value={
        "success": True,
        "data": {
            "email_summaries": [
                {"id": "msg1", "thread_id": "thread1"},
                {"id": "msg2", "thread_id": "thread2"}
            ],
            "next_page_token": "next_token"
        }
    })
    return adapter


@pytest.fixture
def app(mock_adapter):
    """Creates a test FastAPI app with the tools router."""
    app = FastAPI()
    
    # Override the dependencies
    async def mock_get_adapter():
        return mock_adapter
        
    async def mock_verify_api_key():
        return "test_api_key"
    
    app.dependency_overrides = {
        "app.dependencies.dependencies_service.get_damien_adapter": mock_get_adapter,
        "app.core.security.verify_api_key": mock_verify_api_key
    }
    
    app.include_router(router, prefix="/mcp")
    return app


@pytest.fixture
def client(app):
    """Creates a test client for the FastAPI app."""
    return TestClient(app)


def test_list_tools_endpoint(client):
    """Test the list_tools endpoint."""
    response = client.get("/mcp/list_tools")
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    assert len(tools) > 0
