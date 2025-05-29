from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime
from .cost_management import UsageTracker # Added import
# Provider imports will be moved into LLMServiceOrchestrator to avoid circular dependencies
# from .providers.openai_provider import OpenAIProvider
# from .providers.anthropic_provider import AnthropicProvider
# from .providers.local_provider import LocalLLMProvider
# from .providers.google_provider import GoogleProvider # If/when implemented
from damien_cli.core.config import settings # If loading config globally

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"

# Placeholder for ProviderSelector
class ProviderSelector:
    """
    Selects the most appropriate LLM provider based on various factors.
    This is a placeholder and needs a proper implementation.
    """
    def __init__(self, providers: Dict[LLMProvider, 'BaseLLMService'], provider_configs: Dict[str, Dict[str, Any]]):
        self.providers = providers
        self.provider_configs = provider_configs # Store loaded provider configs for model name access

    def select_provider( # Renamed from select_provider to select_llm_service_provider
        self,
        request: 'LLMRequest', # LLMRequest.metadata will contain hints
        # task_type: str, # Now expected in request.metadata.get('task_type')
        # email_complexity_score: Optional[float] = None, # in request.metadata
        # current_confidence: Optional[float] = None, # in request.metadata
        # privacy_requirements: Optional[Dict[str, Any]] = None, # in request.metadata
        preferred_provider_enum: Optional[LLMProvider] = None, # User's explicit preference
        budget_limit: Optional[float] = None, # Overall budget for the operation
        provider_status: Optional[Dict[str, Any]] = None # Health/status of providers
    ) -> Optional['BaseLLMService']:
        """
        Selects an LLM provider instance based on request metadata and other factors.
        The actual model string (e.g., "gpt-4o-mini") is typically configured
        within each provider instance (via its default_model).
        """
        metadata = request.metadata or {}
        task_type = metadata.get('task_type', 'unknown')
        email_complexity_score = metadata.get('email_complexity_score')
        current_confidence = metadata.get('current_confidence')
        privacy_requires_local = metadata.get('privacy_requires_local_processing', False)
        needs_strong_reasoning = metadata.get('needs_strong_reasoning', False)
        is_ambiguous = metadata.get('is_ambiguous', False)

        # Rule 1: Privacy requires local processing
        if privacy_requires_local:
            if LLMProvider.LOCAL in self.providers:
                print(f"ProviderSelector: Selecting LOCAL due to privacy requirements.")
                return self.providers[LLMProvider.LOCAL]
            else:
                print("Warning: Privacy requires local processing, but LOCAL provider is not available.")
                # Fall through to other rules or handle as an error depending on policy

        # Rule 2: Preferred provider if valid and available
        if preferred_provider_enum and preferred_provider_enum in self.providers:
            # TODO: Check provider_status if available
            print(f"ProviderSelector: Selecting preferred provider: {preferred_provider_enum.name}")
            return self.providers[preferred_provider_enum]

        # Rule 3: Strong reasoning or ambiguous tasks
        if needs_strong_reasoning or is_ambiguous:
            # Prefer OpenAI (GPT-4o/mini) or Anthropic (Opus/Sonnet)
            # For now, let's assume configured defaults for OpenAI/Anthropic are strong enough
            if LLMProvider.OPENAI in self.providers: # Assumes OpenAI default is gpt-4o or similar
                print(f"ProviderSelector: Selecting OpenAI for strong reasoning/ambiguity.")
                return self.providers[LLMProvider.OPENAI]
            if LLMProvider.ANTHROPIC in self.providers: # Assumes Anthropic default is Opus or Sonnet
                print(f"ProviderSelector: Selecting Anthropic for strong reasoning/ambiguity as fallback.")
                return self.providers[LLMProvider.ANTHROPIC]

        # Rule 4: Low complexity and high confidence tasks
        if email_complexity_score is not None and current_confidence is not None:
            if email_complexity_score < 0.5 and current_confidence > 0.7:
                # Prefer cost-effective models: OpenAI (GPT-3.5T/gpt-4o-mini) or Anthropic (Sonnet/Haiku)
                # The actual model used is the default for the provider.
                # We can add logic here to pick between OpenAI/Anthropic based on which has a more suitable default.
                if LLMProvider.OPENAI in self.providers: # e.g. gpt-4o-mini is cost-effective
                     print(f"ProviderSelector: Selecting OpenAI for low complexity/high confidence task.")
                     return self.providers[LLMProvider.OPENAI]
                if LLMProvider.ANTHROPIC in self.providers: # e.g. claude-3.5-sonnet
                     print(f"ProviderSelector: Selecting Anthropic for low complexity/high confidence task.")
                     return self.providers[LLMProvider.ANTHROPIC]
        
        # Rule 5: Default for structured tasks (intent, summarization, pattern extraction, basic rule gen)
        # This often overlaps with Rule 4. For now, let's assume the defaults for OpenAI/Anthropic are suitable.
        structured_tasks = ["intent_classification", "summarization", "pattern_extraction", "basic_rule_generation"]
        if task_type in structured_tasks:
            if LLMProvider.OPENAI in self.providers:
                print(f"ProviderSelector: Selecting OpenAI for structured task: {task_type}")
                return self.providers[LLMProvider.OPENAI]
            if LLMProvider.ANTHROPIC in self.providers:
                print(f"ProviderSelector: Selecting Anthropic for structured task: {task_type}")
                return self.providers[LLMProvider.ANTHROPIC]

        # Fallback Logic:
        # 1. Try Anthropic (Sonnet or Haiku if available - current default is Sonnet)
        if LLMProvider.ANTHROPIC in self.providers:
            print(f"ProviderSelector: Fallback - Selecting Anthropic.")
            return self.providers[LLMProvider.ANTHROPIC]
        # 2. Try OpenAI (GPT-3.5 Turbo or current default like gpt-4o-mini)
        if LLMProvider.OPENAI in self.providers:
            print(f"ProviderSelector: Fallback - Selecting OpenAI.")
            return self.providers[LLMProvider.OPENAI]
        # 3. Try Local
        if LLMProvider.LOCAL in self.providers:
            print(f"ProviderSelector: Fallback - Selecting Local.")
            return self.providers[LLMProvider.LOCAL]
        
        print("Warning: ProviderSelector could not select any provider based on rules and availability.")
        return None

# LLMProvider enum was moved above ProviderSelector.
# This comment was from a previous attempt and is no longer accurate here.
# It should be: class LLMProvider(Enum): ... (already moved)

@dataclass
class LLMRequest:
    """Standardized LLM request format"""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.3
    top_p: float = 0.95
    stream: bool = False
    response_format: Optional[Dict[str, Any]] = None
    stop_sequences: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None # Made Optional, can carry hints for ProviderSelector
                                             # e.g., {"task_type": "summarization",
                                             #        "email_complexity_score": 0.3,
                                             #        "current_confidence": 0.9,
                                             #        "privacy_requires_local_processing": False,
                                             #        "needs_strong_reasoning": False,
                                             #        "is_ambiguous": False }
@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    model: str
    provider: LLMProvider
    usage: Dict[str, int]  # tokens, cost
    latency_ms: float
    finish_reason: str
    metadata: Dict[str, Any] = None

class BaseLLMService(ABC):
    """Abstract base for LLM service providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limiter = self._init_rate_limiter() # Placeholder
        self.cache = self._init_cache() # Placeholder
    
    def _init_rate_limiter(self) -> Optional[Any]:
        """Placeholder for rate limiter initialization."""
        # TODO: Implement rate limiting (e.g., using asyncio-limiter)
        print(f"Warning: Rate limiter not implemented for {self.__class__.__name__}")
        return None

    def _init_cache(self) -> Optional[Any]:
        """Placeholder for cache initialization."""
        # TODO: Implement caching (e.g., using aiocache or a custom solution)
        # The OpenAIProvider has its own cache example, this could be a shared cache.
        print(f"Warning: Cache not implemented for {self.__class__.__name__}")
        return None

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion"""
        pass
    
    @abstractmethod
    async def stream_complete(
        self, request: LLMRequest
    ) -> AsyncGenerator[str, None]:
        """Stream completion"""
        pass
    
    @abstractmethod
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate request cost"""
        pass
    
    @abstractmethod
    def validate_request(self, request: LLMRequest) -> bool:
        """Validate request parameters"""
        pass

class LLMServiceOrchestrator:
    """Orchestrates multiple LLM providers with fallback"""
    
    # Moved provider imports here to break circular dependency
    from .providers.openai_provider import OpenAIProvider
    from .providers.anthropic_provider import AnthropicProvider
    from .providers.local_provider import LocalLLMProvider
    # from .providers.google_provider import GoogleProvider # Add when implemented

    PROVIDER_CLASS_MAP = {
        LLMProvider.OPENAI: OpenAIProvider, # Now OpenAIProvider is defined
        LLMProvider.ANTHROPIC: AnthropicProvider, # Now AnthropicProvider is defined
        LLMProvider.LOCAL: LocalLLMProvider, # Now LocalLLMProvider is defined
        # LLMProvider.GOOGLE: GoogleProvider,
    }
    
    def __init__(self, providers_config_map: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initializes the LLMServiceOrchestrator.

        Args:
            providers_config_map: A dictionary where keys are provider names (strings like "openai")
                                 and values are their specific configuration dictionaries.
                                 If None, it will attempt to load from `damien_cli.core.config.settings`.
        """
        final_providers_config = providers_config_map
        if final_providers_config is None:
            if hasattr(settings, 'LLM_PROVIDERS_CONFIGURATION'):
                final_providers_config = settings.LLM_PROVIDERS_CONFIGURATION
                print("LLMServiceOrchestrator: Loaded provider configuration from global settings.")
            else:
                print("Warning: LLMServiceOrchestrator received no provider config and global settings not found or misconfigured.")
                final_providers_config = {}
        
        self.providers: Dict[LLMProvider, BaseLLMService] = self._init_providers(final_providers_config or {})
        self.provider_selector = ProviderSelector(self.providers)
        self.monitor = UsageTracker()
    
    def _init_providers(self, config_map: Dict[str, Dict[str, Any]]) -> Dict[LLMProvider, BaseLLMService]:
        """
        Initializes and returns a dictionary of LLM provider instances
        based on the provided configuration map.
        """
        initialized_providers: Dict[LLMProvider, BaseLLMService] = {}
        
        for provider_key_str, provider_specific_config in config_map.items():
            try:
                # Convert string key (e.g., "openai") to LLMProvider enum member
                provider_enum_member = LLMProvider(provider_key_str.lower())
            except ValueError:
                print(f"Warning: Unknown provider key '{provider_key_str}' in configuration. Skipping.")
                continue

            if provider_enum_member in self.PROVIDER_CLASS_MAP:
                ProviderClass = self.PROVIDER_CLASS_MAP[provider_enum_member]
                try:
                    # Provider-specific config is passed directly.
                    # Each provider's __init__ is responsible for extracting what it needs,
                    # including API keys (e.g., config.get('api_key')).
                    # API keys should ideally be part of the provider_specific_config
                    # loaded from a secure source (env variables via a settings module).
                    
                    # Example: Ensure API key is present for providers that need it
                    # if provider_enum_member in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC] \
                    #   and 'api_key' not in provider_specific_config:
                    #     print(f"Warning: API key missing for {provider_enum_member.name}. Skipping.")
                    #     continue
                            
                    instance = ProviderClass(config=provider_specific_config)
                    initialized_providers[provider_enum_member] = instance
                    print(f"Successfully initialized provider: {provider_enum_member.name}")
                except Exception as e:
                    print(f"Error initializing provider {provider_enum_member.name}: {e}")
            else:
                print(f"Warning: No implementation class found for provider {provider_enum_member.name}. Skipping.")
        
        if not initialized_providers:
            print("Warning: No LLM providers were successfully initialized by LLMServiceOrchestrator.")
        return initialized_providers

    def _get_provider_status(self) -> Dict[str, Any]:
        """
        Gets the current status of all configured providers.
        Placeholder: This should query provider health, load, etc.
        """
        # Example:
        # status = {}
        # for provider_name, provider_instance in self.providers.items():
        #     status[provider_name.value] = {"healthy": True, "load": 0.5} # Query actual status
        # return status
        print("Warning: LLMServiceOrchestrator._get_provider_status() is a placeholder.")
        return {"openai": {"healthy": True}, "anthropic": {"healthy": True}} # Placeholder

    async def _execute_with_fallback(
        self, request: LLMRequest, provider: Optional[BaseLLMService]
    ) -> LLMResponse:
        """
        Executes the request with the given provider, with fallback logic.
        Placeholder: Needs to handle provider being None and implement actual fallback.
        """
        if not provider:
            # TODO: Implement fallback logic (e.g., try next provider in a preference list)
            print("Error: No provider selected or available in _execute_with_fallback.")
            # For now, raising an error. A real implementation might try other providers.
            raise ValueError("No LLM provider available to handle the request.")
        
        print(f"Executing request with provider: {provider.__class__.__name__}")
        # Actual call to the provider's complete method
        return await provider.complete(request)

    async def _handle_error(self, error: Exception, request: LLMRequest, provider: Optional[BaseLLMService]):
        """
        Handles errors during LLM processing.
        Placeholder: Implement error logging, retries, or other error handling strategies.
        """
        provider_name = provider.__class__.__name__ if provider else "None"
        print(f"Error during LLM processing with {provider_name}: {error}. Request: {request}")
        # Potentially re-raise, or implement specific error handling (e.g. if it's a rate limit error)
        # For now, the original 'raise' in the process method will propagate the error.
        pass

    async def process(
        self,
        request: LLMRequest,
        preferred_provider: Optional[LLMProvider] = None,
        budget_limit: Optional[float] = None
    ) -> LLMResponse:
        """Process request with intelligent routing"""
        
        # Select provider based on multiple factors
        # The select_provider method now primarily uses hints from request.metadata
        provider = self.provider_selector.select_llm_service_provider( # Renamed method
            request=request,
            preferred_provider_enum=preferred_provider, # Pass the enum directly
            budget_limit=budget_limit,
            provider_status=self._get_provider_status()
        )
        
        if not provider:
            # Handle case where no provider could be selected
            # This could be logging an error and raising an exception,
            # or attempting a default provider if one is configured.
            # For now, we'll let _execute_with_fallback handle provider being None.
            print("Warning: No provider selected by ProviderSelector.")


        # Execute with fallback
        try:
            response = await self._execute_with_fallback(
                request, provider
            )
            
            # Track usage
            self.monitor.track(provider, response)
            
            return response
            
        except Exception as e:
            # Log and handle errors
            await self._handle_error(e, request, provider)
            raise