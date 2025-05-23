"""Server configuration settings using Pydantic BaseSettings.

This module provides configuration for the Damien MCP Server with support for 
loading settings from environment variables or a .env file.
"""

from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator # BaseModel removed if Settings inherits BaseSettings
from pydantic_settings import BaseSettings, SettingsConfigDict # Import SettingsConfigDict
import os
from pathlib import Path


class MdbSettings(BaseSettings): # Changed to BaseSettings
    """DynamoDB settings for storing session context."""
    
    table_name: str = Field(default="DamienMCPSessions", alias="DAMIEN_DYNAMODB_SESSION_TABLE_NAME")
    region: Optional[str] = Field(default=os.environ.get("AWS_REGION", "us-east-1"), alias="DAMIEN_DYNAMODB_REGION")
    session_ttl_seconds: int = Field(default=86400, alias="DAMIEN_DYNAMODB_SESSION_TTL_SECONDS")

    model_config = SettingsConfigDict(
        extra='ignore',
        env_file='.env',
        env_file_encoding='utf-8'
    )


class Settings(BaseSettings): # Changed to BaseSettings
    """Main application settings."""
    
    # Server settings
    app_name: str = "DamienMCPServer"
    api_key: str = Field(default="", alias="DAMIEN_MCP_SERVER_API_KEY") # Use Field with alias
    log_level: str = Field(default="INFO", alias="DAMIEN_LOG_LEVEL")
    log_file_path: Optional[str] = Field(default=None, alias="DAMIEN_MCP_LOG_FILE_PATH") # Added for MCP server log file
    
    # Path settings
    gmail_token_path: str = Field(default="", alias="DAMIEN_GMAIL_TOKEN_JSON_PATH")
    gmail_credentials_path: str = Field(default="", alias="DAMIEN_GMAIL_CREDENTIALS_JSON_PATH")
    
    # Gmail API settings
    gmail_scopes: List[str] = ["https://mail.google.com/"] # This usually doesn't come from env
    
    # DynamoDB settings - Now properly initialized in __init__
    dynamodb: MdbSettings = Field(default_factory=MdbSettings)

    # User settings - For single-user mode initially
    default_user_id: str = Field(default="damien_default_user", alias="DAMIEN_DEFAULT_USER_ID")
    
    # API Timeouts
    request_timeout_seconds: int = Field(default=30, alias="DAMIEN_REQUEST_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    @field_validator("gmail_token_path", "gmail_credentials_path", mode='before')
    def validate_file_paths(cls, v: Any) -> str:
        """Validate that file paths exist and are accessible."""
        if not isinstance(v, str): # Ensure it's a string before Path conversion
            # This case might not be strictly necessary if env vars are always strings,
            # but good for robustness if default values could be non-strings.
            raise ValueError("File path must be a string")
        path = Path(v)
        if not path.exists():
            # Log warning but don't fail - files might be created later
            print(f"Warning: File not found at path: {path}. Ensure it exists before server starts.")
        return v


# Create a singleton instance
settings = Settings()
