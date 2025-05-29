import os
from typing import Dict, Any, Optional, Literal
from dotenv import load_dotenv # For loading the root .env file

# Determine path to the root .env file (one level up from 'damien-cli/' directory)
# __file__ is damien-cli/core/config.py
# os.path.dirname(__file__) is damien-cli/core/
# os.path.join(os.path.dirname(__file__), '..', '..', '.env') is ../.env (workspace root)
ROOT_DOTENV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

if os.path.exists(ROOT_DOTENV_PATH):
    load_dotenv(dotenv_path=ROOT_DOTENV_PATH, override=True)
    print(f"Loaded environment variables from: {ROOT_DOTENV_PATH}")
else:
    print(f"Warning: Root .env file not found at {ROOT_DOTENV_PATH}. Relying on system environment variables.")

class Settings:
    APP_NAME: str = "Damien CLI"
    
    # Load LOG_LEVEL, ensuring it's one of the allowed literals
    _raw_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    _allowed_log_levels: set[str] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if _raw_log_level not in _allowed_log_levels:
        print(f"Warning: Invalid LOG_LEVEL '{_raw_log_level}' found. Defaulting to INFO.")
        LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    else:
        LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = _raw_log_level # type: ignore

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")

    OPENAI_DEFAULT_MODEL: str = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
    ANTHROPIC_DEFAULT_MODEL: str = os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20240620")
    GOOGLE_DEFAULT_MODEL: str = os.getenv("GOOGLE_DEFAULT_MODEL", "gemini-1.5-pro-latest")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3")

    LLM_PROVIDERS_CONFIGURATION: Dict[str, Dict[str, Any]]

    def __init__(self):
        self.LLM_PROVIDERS_CONFIGURATION = {
            "openai": {
                "enabled": bool(self.OPENAI_API_KEY),
                "api_key": self.OPENAI_API_KEY,
                "default_model": self.OPENAI_DEFAULT_MODEL,
            },
            "anthropic": {
                "enabled": bool(self.ANTHROPIC_API_KEY),
                "api_key": self.ANTHROPIC_API_KEY,
                "default_model": self.ANTHROPIC_DEFAULT_MODEL,
            },
            "local": {
                "enabled": True, 
                "base_url": self.OLLAMA_BASE_URL,
                "default_model": self.OLLAMA_DEFAULT_MODEL,
            },
            "google": {
                "enabled": bool(self.GOOGLE_API_KEY),
                "api_key": self.GOOGLE_API_KEY,
                "default_model": self.GOOGLE_DEFAULT_MODEL,
            }
        }
        # Filter out disabled providers
        self.LLM_PROVIDERS_CONFIGURATION = {
            provider: config
            for provider, config in self.LLM_PROVIDERS_CONFIGURATION.items()
            if config.get("enabled", False)
        }

        # Optional: Print warnings for enabled providers with missing keys
        if self.LLM_PROVIDERS_CONFIGURATION.get("openai", {}).get("enabled") and not self.OPENAI_API_KEY:
             print("Warning: OpenAI provider is enabled in config but OPENAI_API_KEY is missing.")
        if self.LLM_PROVIDERS_CONFIGURATION.get("anthropic", {}).get("enabled") and not self.ANTHROPIC_API_KEY:
             print("Warning: Anthropic provider is enabled in config but ANTHROPIC_API_KEY is missing.")
        if self.LLM_PROVIDERS_CONFIGURATION.get("google", {}).get("enabled") and not self.GOOGLE_API_KEY:
            print("Warning: Google provider is enabled in config but GOOGLE_API_KEY is missing.")


settings = Settings()

if __name__ == '__main__':
    print(f"App Name: {settings.APP_NAME}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"OpenAI API Key Set: {bool(settings.OPENAI_API_KEY)}")
    print(f"Anthropic API Key Set: {bool(settings.ANTHROPIC_API_KEY)}")
    print(f"Google API Key Set: {bool(settings.GOOGLE_API_KEY)}")
    print(f"OpenAI Default Model: {settings.OPENAI_DEFAULT_MODEL}")
    print(f"Anthropic Default Model: {settings.ANTHROPIC_DEFAULT_MODEL}")
    print(f"Google Default Model: {settings.GOOGLE_DEFAULT_MODEL}")
    print(f"Ollama Base URL: {settings.OLLAMA_BASE_URL}")
    print(f"Ollama Default Model: {settings.OLLAMA_DEFAULT_MODEL}")
    print("\nLLM Providers Configuration (active):")
    for provider, config_data in settings.LLM_PROVIDERS_CONFIGURATION.items():
        print(f"  {provider}: {config_data}")