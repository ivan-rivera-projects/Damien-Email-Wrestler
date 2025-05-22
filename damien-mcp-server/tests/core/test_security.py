import pytest
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.security import verify_api_key, API_KEY_HEADER_NAME # Changed from damien_mcp_server
from app.core.config import settings # Changed from damien_mcp_server

# A dummy app to test the dependency
dummy_app = FastAPI()

@dummy_app.get("/secure-resource", dependencies=[Depends(verify_api_key)])
async def get_secure_resource():
    return {"message": "Access granted to secure resource"}

client = TestClient(dummy_app)

# Store original settings to restore them
original_api_key = settings.api_key # Changed from server_api_key

def test_verify_api_key_valid():
    """Test that a valid API key grants access."""
    settings.api_key = "test_secure_api_key" # Changed from server_api_key
    
    response = client.get("/secure-resource", headers={API_KEY_HEADER_NAME: "test_secure_api_key"})
    assert response.status_code == 200
    assert response.json() == {"message": "Access granted to secure resource"}
    
    settings.api_key = original_api_key # Restore original

def test_verify_api_key_missing():
    """Test that a missing API key results in 403 Forbidden."""
    settings.api_key = "test_secure_api_key" # Changed from server_api_key
    
    response = client.get("/secure-resource") # No API key header
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Not authenticated" in response.json()["detail"]
    
    settings.api_key = original_api_key # Restore original

def test_verify_api_key_invalid():
    """Test that an invalid API key results in 403 Forbidden."""
    settings.api_key = "test_secure_api_key" # Changed from server_api_key
    
    response = client.get("/secure-resource", headers={API_KEY_HEADER_NAME: "invalid_api_key"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Invalid or missing API Key." in response.json()["detail"] # Corrected expected detail
    
    settings.api_key = original_api_key # Restore original

def test_verify_api_key_no_server_key_configured():
    """Test behavior when SERVER_API_KEY is not configured (should deny all)."""
    settings.api_key = None # Simulate no API key configured on the server, changed from server_api_key
    
    response = client.get("/secure-resource", headers={API_KEY_HEADER_NAME: "any_key_will_fail"})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR # Expect 500
    # The current implementation of verify_api_key would raise HTTPException("Invalid API Key")
    # if settings.SERVER_API_KEY is None and an api_key is provided, because "" != None.
    # If settings.SERVER_API_KEY is None and no api_key is provided, it's "Not authenticated".
    # Let's test the case where a key is provided but server has no key.
    assert "API Key not configured on server." in response.json()["detail"] # Corrected expected detail for 500

    response_no_header = client.get("/secure-resource")
    assert response_no_header.status_code == status.HTTP_403_FORBIDDEN
    assert "Not authenticated" in response_no_header.json()["detail"]
    
    settings.api_key = original_api_key # Restore original