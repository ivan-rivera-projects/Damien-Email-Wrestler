"""Tests for the server configuration module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import contextlib
import importlib 

# Import the module to test
from app.core import config as config_module # Changed from damien_mcp_server
from app.core.config import Settings # Changed from damien_mcp_server


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for testing."""
    env_vars = {
        "DAMIEN_MCP_SERVER_API_KEY": "test_api_key",
        "DAMIEN_GMAIL_TOKEN_JSON_PATH": "/tmp/token.json",
        "DAMIEN_GMAIL_CREDENTIALS_JSON_PATH": "/tmp/credentials.json",
        "DAMIEN_DYNAMODB_SESSION_TABLE_NAME": "TestTable",
        "DAMIEN_LOG_LEVEL": "DEBUG",
    }
    
    original_env = {}
    for key in env_vars:
        if key in os.environ:
            original_env[key] = os.environ[key]
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    original_default_user_id = os.environ.pop('DAMIEN_DEFAULT_USER_ID', None)

    yield env_vars
    
    for key in env_vars:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            if key in os.environ:
                 os.environ.pop(key, None) 
    
    if original_default_user_id is not None:
        os.environ['DAMIEN_DEFAULT_USER_ID'] = original_default_user_id


def test_settings_from_env(monkeypatch):
    """Test that settings are loaded correctly from environment variables and defaults."""
    
    monkeypatch.setenv("DAMIEN_MCP_SERVER_API_KEY", "test_api_key_direct")
    monkeypatch.setenv("DAMIEN_GMAIL_TOKEN_JSON_PATH", "/test/token.json")
    monkeypatch.setenv("DAMIEN_GMAIL_CREDENTIALS_JSON_PATH", "/test/credentials.json")
    monkeypatch.setenv("DAMIEN_DYNAMODB_SESSION_TABLE_NAME", "DirectTestTable")
    monkeypatch.setenv("DAMIEN_LOG_LEVEL", "TEST_DEBUG")
    
    monkeypatch.delenv("DAMIEN_DEFAULT_USER_ID", raising=False)
    
    # Patch load_dotenv within the config module to prevent it from loading a real .env file
    # Patch Path.exists for file validation in Settings
    with patch.object(Path, 'exists', return_value=True):

        # Import the Settings class directly for local instantiation AFTER patching environment
        from app.core.config import Settings as SettingsClassForTest
        
        # Instantiate Settings directly, explicitly disabling .env file loading for this instance.
        # This ensures it reads only from the monkeypatched os.environ.
        settings_instance = SettingsClassForTest(_env_file=None)
        
        assert settings_instance.api_key == "test_api_key_direct"
        assert settings_instance.gmail_token_path == "/test/token.json"
        assert settings_instance.gmail_credentials_path == "/test/credentials.json"
        assert settings_instance.dynamodb.table_name == "DirectTestTable"
        assert settings_instance.log_level == "TEST_DEBUG"
        assert settings_instance.default_user_id == "damien_default_user"


def test_path_validation_warning(monkeypatch): # Added monkeypatch
    """Test that path validation produces warnings for non-existent files."""
    env_vars = {
        "DAMIEN_MCP_SERVER_API_KEY": "test_api_key_validation", # Use different key to avoid conflict
        "DAMIEN_GMAIL_TOKEN_JSON_PATH": "/nonexistent/path/token.json",
        "DAMIEN_GMAIL_CREDENTIALS_JSON_PATH": "/nonexistent/path/credentials.json",
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    # Ensure paths don't exist for this test
    # Patch load_dotenv to prevent interference
    with patch.object(Path, 'exists', return_value=False), \
         patch('builtins.print') as mock_print:

        # Import and instantiate locally
        from app.core.config import Settings as SettingsClassForTestValidation
        settings_instance = SettingsClassForTestValidation()
        
        assert mock_print.call_count >= 2
        warning_messages = [call_args[0][0] for call_args in mock_print.call_args_list]
        assert any("token.json" in msg for msg in warning_messages)
        assert any("credentials.json" in msg for msg in warning_messages)
    
    # Monkeypatch automatically cleans up env vars set by setenv


def test_dynamodb_settings(monkeypatch): # Added monkeypatch
    """Test DynamoDB settings configuration."""
    monkeypatch.setenv("DAMIEN_MCP_SERVER_API_KEY", "api_key_dynamo_test")
    monkeypatch.setenv("DAMIEN_GMAIL_TOKEN_JSON_PATH", "/tmp/token_dynamo.json")
    monkeypatch.setenv("DAMIEN_GMAIL_CREDENTIALS_JSON_PATH", "/tmp/credentials_dynamo.json")
    monkeypatch.setenv("DAMIEN_DYNAMODB_SESSION_TABLE_NAME", "CustomTableDynamo")
    monkeypatch.setenv("DAMIEN_DYNAMODB_REGION", "eu-west-1-dynamo")

    with patch.object(Path, 'exists', return_value=True):

        from app.core.config import Settings as SettingsClassForDynamoTest
        settings_instance = SettingsClassForDynamoTest()
        
        assert settings_instance.dynamodb.table_name == "CustomTableDynamo"
        assert settings_instance.dynamodb.region == "eu-west-1-dynamo"

    # Monkeypatch cleanup is automatic
