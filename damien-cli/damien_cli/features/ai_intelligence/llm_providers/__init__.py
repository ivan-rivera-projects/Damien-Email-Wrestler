from typing import Optional
from damien_cli.core.config import settings
from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .local_provider import LocalModelProvider

def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """Factory function to get appropriate LLM provider"""
    
    provider = provider_name or settings.ai_provider
    
    if provider == "openai":
        return OpenAIProvider()
    elif provider == "local":
        return LocalModelProvider(settings.local_model_path)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

__all__ = ["get_llm_provider", "BaseLLMProvider"]