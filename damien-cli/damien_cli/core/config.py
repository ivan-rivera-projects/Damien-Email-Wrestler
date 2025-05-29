import os
from pathlib import Path
from typing import Dict, Any, Optional, Literal
from dotenv import load_dotenv

# Path configuration remains the same for Gmail-related files
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = DATA_DIR / "token.json"
RULES_FILE = DATA_DIR / "rules.json"

# Make sure DATA_DIR exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Gmail API Scopes
SCOPES = ["https://mail.google.com/"]

# Load environment variables from root .env file
ROOT_DOTENV_PATH = PROJECT_ROOT / ".env"
if ROOT_DOTENV_PATH.exists():
    load_dotenv(dotenv_path=ROOT_DOTENV_PATH, override=True)

class Settings:
    """Unified settings for Damien CLI"""
    
    APP_NAME: str = "Damien CLI"
    
    # Logging configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # API Keys
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Model configurations
    openai_default_model: str = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
    anthropic_default_model: str = os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20240620")
    google_default_model: str = os.getenv("GOOGLE_DEFAULT_MODEL", "gemini-1.5-pro-latest")
    
    # Local LLM configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_default_model: str = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3")
    
    # Legacy AI settings (for backward compatibility)
    ai_model: str = os.getenv("AI_MODEL", os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"))
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")
    local_model_path: str = os.getenv("LOCAL_MODEL_PATH", "/path/to/local/model")
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.3"))
    ai_max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "2000"))
    
    # LLM Provider Configuration
    @property
    def LLM_PROVIDERS_CONFIGURATION(self) -> Dict[str, Dict[str, Any]]:
        """Dynamic LLM provider configuration"""
        config = {
            "openai": {
                "enabled": bool(self.openai_api_key),
                "api_key": self.openai_api_key,
                "default_model": self.openai_default_model,
                "model": self.openai_default_model,  # Alias for compatibility
            },
            "anthropic": {
                "enabled": bool(self.anthropic_api_key),
                "api_key": self.anthropic_api_key,
                "default_model": self.anthropic_default_model,
                "model": self.anthropic_default_model,  # Alias for compatibility
            },
            "local": {
                "enabled": True,
                "base_url": self.ollama_base_url,
                "default_model": self.ollama_default_model,
            },
            "google": {
                "enabled": bool(self.google_api_key),
                "api_key": self.google_api_key,
                "default_model": self.google_default_model,
            }
        }
        # Return only enabled providers
        return {k: v for k, v in config.items() if v.get("enabled", False)}

# Create singleton instance
settings = Settings()
