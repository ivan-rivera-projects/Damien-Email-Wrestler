# Phase 3: LLM Integration Technical Implementation Guide
## Detailed Code Examples and Integration Patterns

---
---
## A. Current Project Status, Troubleshooting, and Immediate Next Steps (As of 2025-05-28)

This section summarizes the progress made, issues encountered, and the immediate actions required before proceeding with further feature implementation.

### A.1. Summary of Implemented Components (Phase 3.1 Foundation)

The following foundational components for LLM integration have had their initial structures and code created in the `damien-cli/features/ai_intelligence/llm_integration/` directory:

*   **Core LLM Abstractions (`base.py`):**
    *   `LLMProvider` (Enum)
    *   `LLMRequest`, `LLMResponse` (Dataclasses)
    *   `BaseLLMService` (ABC for providers)
    *   `ProviderSelector` (Class with refined selection logic based on task type, complexity, privacy, etc.)
    *   `LLMServiceOrchestrator` (Class to manage providers, uses `ProviderSelector` and `UsageTracker`)
*   **LLM Providers (`providers/` sub-directory):**
    *   `OpenAIProvider` (`openai_provider.py`)
    *   `AnthropicProvider` (`anthropic_provider.py`)
    *   `LocalLLMProvider` (`local_provider.py`) (for Ollama-like servers)
*   **Prompt Engineering (`prompts.py`):**
    *   `PromptTemplate` (ABC)
    *   `EmailAnalysisPrompts` (Collection of predefined prompts)
    *   `DynamicExampleSelector` (Refined to potentially use an embedding service)
    *   `PromptOptimizer` (Structure exists)
*   **Privacy Framework (`privacy.py`):**
    *   `PIIEntity` (Dataclass)
    *   `PrivacyGuardian`
    *   `PIITokenizer`
    *   `AuditLogger`
*   **Context Management (`context_optimizer.py`):**
    *   `ContextItem` (Dataclass)
    *   `ContextWindowOptimizer`
    *   `ContextPrioritizer` (Placeholder)
*   **Routing & Utilities:**
    *   `IntelligenceRouter`, `ComplexityAnalyzer`, `PerformancePredictor` (Placeholders in `router.py`)
    *   `TokenCounter` (Implemented in `utils.py`)
    *   `CostEstimator`, `UsageTracker` (Initial versions in `cost_management.py`)
*   **Core Application Modules (`damien-cli/core/`):**
    *   `config.py`: Manages application settings, including LLM API keys and defaults, using `os.getenv` and loading from a root `.env` file.
    *   `app_logging.py`: Custom logging setup (renamed from `logging.py`).
    *   `__init__.py` files added to `core`, `features`, and relevant subdirectories to ensure proper package structure.
*   **Environment Configuration:**
    *   Root `.env` file updated with necessary API keys and model preferences.
*   **Testing:**
    *   `tests/test_base_structs.py`: Passes.
    *   `tests/test_token_counter.py`: Passes.
    *   `tests/test_context_optimizer.py`: Passes.
    *   `tests/test_llm_orchestrator.py`: Created, but currently blocked.
    *   `tests/test_connectivity.py`: Created, but currently blocked.

### A.2. Troubleshooting Journey & Current Blocker

We encountered a persistent `AttributeError: partially initialized module 'logging' has no attribute 'getLogger'` when trying to run any script that imported `damien_cli.core.config.settings`.

*   **Initial Suspicion:** Pydantic `ValidationError` due to misconfiguration of `BaseSettings` in `config.py`.
*   **Attempts to Fix Pydantic:**
    *   Refactored `config.py` to use `pydantic-settings.BaseSettings` correctly with `SettingsConfigDict`, `extra='ignore'`, `case_sensitive=False`, then `case_sensitive=True`, and `Field(validation_alias=...)`. None of these resolved the Pydantic error appearing in the traceback.
    *   Simplified `config.py` to minimal fields; error persisted.
*   **Shift to Plain Python `Settings`:** Refactored `config.py` to remove Pydantic `BaseSettings` inheritance and use direct `os.getenv()` calls, loading the root `.env` with `python-dotenv`.
*   **New Blocker Identified:** When running `core/config.py` directly (after user confirmed cache clearing and old `logging.py` deletion), a new error emerged: `ImportError: attempted relative import with no known parent package` in `core/logging.py` (when it tried `from .config import settings`). This was fixed by changing to an absolute import `from damien_cli.core.config import settings`.
*   **Current Blocker Re-evaluation:** The subsequent execution of `core/config.py` (as reported by the user) then failed with the `AttributeError: partially initialized module 'logging' has no attribute 'getLogger'`. This error's traceback indicated that `dotenv` (imported by `config.py`) imports the standard `logging` module, which was then being shadowed by our old `damien-cli/core/logging.py` file.
*   **Resolution Attempt:**
    1.  Renamed `damien-cli/core/logging.py` to `damien-cli/core/app_logging.py`.
    2.  Updated all provider files (`openai_provider.py`, `anthropic_provider.py`, `local_provider.py`) to import `get_logger` from `.....core.app_logging`.

### A.3. Immediate Next Steps (To Resolve Blocker)

Before any further feature development or testing can reliably proceed, the import/initialization issue must be resolved.

1.  **DELETE Old Logging File (CRITICAL USER ACTION):**
    *   The file `damien-cli/core/logging.py` **MUST BE DELETED**. Its continued presence, even if not directly imported by our refactored code, can still be picked up by Python's import system under certain conditions (especially if `__pycache__` for it exists or if other modules try to import `logging` and it's found first in `sys.path`).
2.  **Thoroughly Clear Python Bytecode Cache (CRITICAL USER ACTION):**
    *   All `__pycache__` directories within the entire `damien-cli` project structure (including subdirectories like `core`, `features`, `tests`, etc.) must be deleted.
    *   All `*.pyc` files should also be deleted.
    *   Suggested command from the workspace root (`/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler`):
        ```bash
        find damien-cli -type d -name "__pycache__" -exec rm -rf {} +
        find damien-cli -type f -name "*.pyc" -delete
        ```
3.  **Verify `config.py` Initialization:**
    *   After the above steps, run `poetry run python3 core/config.py` from within the `damien-cli` directory.
    *   This command should now execute successfully and print the loaded settings without any Pydantic or logging-related `AttributeError`. The output should be similar to what was seen at 3:43 PM by the user.
4.  **Retry Connectivity Test:**
    *   If `core/config.py` initializes correctly, then run `poetry run python3 tests/test_connectivity.py` (from `damien-cli` directory). This will test the actual LLM API calls.
    *   Ensure `openai` and `anthropic` libraries are in `pyproject.toml` and installed (`poetry add openai anthropic`).

Once these steps confirm a stable environment, we can proceed with further development or the architectural discussions you requested.

---

## 1. LLM Service Implementation

### Complete OpenAI Provider Implementation

```python
# damien_cli/features/ai_intelligence/llm_integration/providers/openai_provider.py

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
from openai import AsyncOpenAI
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

from ..base import BaseLLMService, LLMRequest, LLMResponse, LLMProvider
from .....core.config import settings # Note: Actual path after refactoring
from .....core.app_logging import get_logger # Note: Actual path after refactoring to app_logging.py

logger = get_logger(__name__)

class OpenAIProvider(BaseLLMService):
    """Production-ready OpenAI provider with advanced features"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=30.0,
            max_retries=3
        )
        self.model = config.get('model', 'gpt-4-turbo-preview')
        self.encoding = tiktoken.encoding_for_model(self.model)
        
        # Model-specific token limits
        self.model_limits = {
            'gpt-4-turbo-preview': 128000,
            'gpt-4': 8192,
            'gpt-3.5-turbo': 16384,
            'gpt-3.5-turbo-16k': 16384
        }
        
        # Cost per 1k tokens (input/output)
        self.model_costs = {
            'gpt-4-turbo-preview': (0.01, 0.03),
            'gpt-4': (0.03, 0.06),
            'gpt-3.5-turbo': (0.0005, 0.0015),
            'gpt-3.5-turbo-16k': (0.003, 0.004)
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion with retry logic"""
        
        start_time = time.time()
        
        try:
            # Validate request
            if not self.validate_request(request):
                raise ValueError("Invalid request parameters")
            
            # Check cache
            cache_key = self._generate_cache_key(request)
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for request: {cache_key}")
                return cached_response
            
            # Prepare messages
            messages = self._build_messages(request)
            
            # API call with structured output if specified
            call_params = {
                "model": self.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "stream": False
            }
            
            if request.response_format:
                call_params["response_format"] = request.response_format
            
            if request.stop_sequences:
                call_params["stop"] = request.stop_sequences
            
            response = await self.client.chat.completions.create(**call_params)
            
            # Calculate costs
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)
            
            # Build response
            llm_response = LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                provider=LLMProvider.OPENAI,
                usage={
                    'prompt_tokens': input_tokens,
                    'completion_tokens': output_tokens,
                    'total_tokens': response.usage.total_tokens,
                    'estimated_cost': cost
                },
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    'cache_key': cache_key,
                    'system_fingerprint': getattr(response, 'system_fingerprint', None)
                }
            )
            
            # Cache successful response
            await self.cache.set(cache_key, llm_response, ttl=3600)
            
            # Track usage
            await self._track_usage(llm_response)
            
            return llm_response
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Track error
            await self._track_error(e, request)
            raise
    
    async def stream_complete(
        self, request: LLMRequest
    ) -> AsyncGenerator[str, None]:
        """Stream completion for real-time responses"""
        
        messages = self._build_messages(request)
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def validate_request(self, request: LLMRequest) -> bool:
        """Validate request parameters"""
        
        # Check token limits
        estimated_tokens = self.count_tokens(request.prompt)
        if request.system_prompt:
            estimated_tokens += self.count_tokens(request.system_prompt)
        
        max_context = self.model_limits.get(self.model, 4096)
        if estimated_tokens + request.max_tokens > max_context:
            logger.warning(
                f"Request may exceed token limit: {estimated_tokens} + "
                f"{request.max_tokens} > {max_context}"
            )
            return False
        
        # Validate temperature
        if not 0 <= request.temperature <= 2:
            logger.warning(f"Invalid temperature: {request.temperature}")
            return False
        
        return True
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate request cost in USD"""
        
        input_tokens = self.count_tokens(request.prompt)
        if request.system_prompt:
            input_tokens += self.count_tokens(request.system_prompt)
        
        # Estimate output tokens (rough approximation)
        output_tokens = min(request.max_tokens, input_tokens * 0.5)
        
        return self._calculate_cost(input_tokens, output_tokens)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.encoding.encode(text))
    
    def _build_messages(self, request: LLMRequest) -> List[Dict[str, str]]:
        """Build message array for API"""
        messages = []
        
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        return messages
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD"""
        
        input_cost_per_1k, output_cost_per_1k = self.model_costs.get(
            self.model, (0.01, 0.03)
        )
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return round(input_cost + output_cost, 6)
    
    def _generate_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request"""
        
        import hashlib
        
        # Create deterministic key from request
        key_data = {
            'model': self.model,
            'prompt': request.prompt,
            'system_prompt': request.system_prompt,
            'temperature': request.temperature,
            'max_tokens': request.max_tokens,
            'response_format': request.response_format
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    async def _track_usage(self, response: LLMResponse):
        """Track API usage for monitoring"""
        
        # Log to monitoring system
        logger.info(
            f"LLM Usage - Model: {response.model}, "
            f"Tokens: {response.usage['total_tokens']}, "
            f"Cost: ${response.usage['estimated_cost']:.4f}, "
            f"Latency: {response.latency_ms:.0f}ms"
        )
        
        # Update metrics
        if hasattr(self, 'metrics'):
            self.metrics.increment('llm_requests_total', tags={'provider': 'openai'})
            self.metrics.histogram('llm_latency_ms', response.latency_ms)
            self.metrics.increment('llm_tokens_used', response.usage['total_tokens'])
            self.metrics.increment('llm_cost_usd', response.usage['estimated_cost'])
    
    async def _track_error(self, error: Exception, request: LLMRequest):
        """Track errors for monitoring"""
        
        logger.error(
            f"LLM Error - Type: {type(error).__name__}, "
            f"Message: {str(error)}, "
            f"Model: {self.model}"
        )
        
        if hasattr(self, 'metrics'):
            self.metrics.increment(
                'llm_errors_total',
                tags={'provider': 'openai', 'error_type': type(error).__name__}
            )
```

### Anthropic Claude Provider

```python
# damien_cli/features/ai_intelligence/llm_integration/providers/anthropic_provider.py

import anthropic
from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio

from ..base import BaseLLMService, LLMRequest, LLMResponse, LLMProvider
# Note: Actual AnthropicProvider also imports get_logger from .....core.app_logging
# and uses settings via its config dict (for api_key, default_model).
# from .....core.app_logging import get_logger
# logger = get_logger(__name__)

class AnthropicProvider(BaseLLMService):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key
        )
        self.model = config.get('model', 'claude-3-opus-20240229')
        
        self.model_limits = {
            'claude-3-opus-20240229': 200000,
            'claude-3-sonnet-20240229': 200000,
            'claude-3-haiku-20240307': 200000
        }
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using Claude"""
        
        start_time = time.time()
        
        try:
            # Build messages
            messages = self._build_messages(request)
            
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=messages,
                system=request.system_prompt if request.system_prompt else None
            )
            
            # Extract usage info
            usage = {
                'prompt_tokens': response.usage.input_tokens,
                'completion_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
            
            # Build response
            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                provider=LLMProvider.ANTHROPIC,
                usage=usage,
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason=response.stop_reason or "complete"
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise
    
    def _build_messages(self, request: LLMRequest) -> List[Dict[str, str]]:
        """Build message format for Anthropic API"""
        
        return [{
            "role": "user",
            "content": request.prompt
        }]
```

### Local LLM Provider (Ollama Example)

This provider interfaces with a local LLM server, such as Ollama.

```python
# damien_cli/features/ai_intelligence/llm_integration/providers/local_provider.py
import httpx
import json
import time
from typing import Dict, List, Optional, Any, AsyncGenerator

from ..base import BaseLLMService, LLMRequest, LLMResponse, LLMProvider
from .....core.app_logging import get_logger # Note: Actual path after refactoring

logger = get_logger(__name__)

class LocalLLMProvider(BaseLLMService):
    """Provider for interfacing with a local LLM server (e.g., Ollama)."""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.base_url = self.config.get('base_url', 'http://localhost:11434')
        self.model = self.config.get('default_model', 'llama3')
        self.client = httpx.AsyncClient(timeout=60.0)
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.chat_endpoint = f"{self.base_url}/api/chat"
        # ... (Implementation for complete, stream_complete, estimate_cost, validate_request)
        # (Refer to actual local_provider.py for full details)
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        # Simplified example - actual implementation is more detailed
        start_time = time.time()
        payload = {
            "model": self.model, "prompt": request.prompt, "stream": False,
            "options": {"temperature": request.temperature, "num_predict": request.max_tokens}
        }
        if request.system_prompt: # Basic handling for generate endpoint
            payload["prompt"] = f"{request.system_prompt}\\n\\nUser: {request.prompt}\\nAssistant:"
        
        try:
            response_http = await self.client.post(self.generate_endpoint, json=payload, timeout=60.0)
            response_http.raise_for_status()
            data = response_http.json()
            content = data.get("response", "").strip()
            # Token counts from Ollama are specific (prompt_eval_count, eval_count)
            prompt_tokens = data.get('prompt_eval_count', 0)
            completion_tokens = data.get('eval_count', 0)

            return LLMResponse(
                content=content, model=self.model, provider=LLMProvider.LOCAL,
                usage={'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens,
                       'total_tokens': prompt_tokens + completion_tokens, 'estimated_cost': 0.0},
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason="stop" if data.get("done") else "unknown",
                metadata={"raw_response": data}
            )
        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            raise
    
    # Other methods (stream_complete, estimate_cost, validate_request) would be here.
    # estimate_cost would return 0.0.
    # validate_request would check for non-empty prompt.
    # stream_complete would require handling streaming responses from Ollama.
```
*(Note: The LocalLLMProvider snippet above is a condensed representation. The actual file contains more detailed logic for chat vs. generate endpoints and error handling.)*

---

## 2. Intelligent Router Implementation

```python
# damien_cli/features/ai_intelligence/llm_integration/router.py

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np

class ProcessingPipeline(Enum):
    EMBEDDING_ONLY = "embedding_only"
    LLM_ONLY = "llm_only"
    HYBRID = "hybrid"

class IntelligenceRouter:
    """Routes requests to appropriate processing pipeline"""
    
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.cost_estimator = CostEstimator()
        self.performance_predictor = PerformancePredictor()
    
    def route_request(
        self,
        email: Dict[str, Any],
        task_type: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[ProcessingPipeline, Dict[str, Any]]:
        """
        Determine optimal processing pipeline
        
        Returns:
            - Selected pipeline
            - Routing metadata and reasoning
        """
        
        # Analyze email complexity
        complexity_score = self.complexity_analyzer.analyze(email)
        
        # Estimate costs for each pipeline
        costs = {
            ProcessingPipeline.EMBEDDING_ONLY: 0.0001,  # Minimal cost
            ProcessingPipeline.LLM_ONLY: self.cost_estimator.estimate_llm_cost(email), # Note: Actual CostEstimator (now in cost_management.py) might take an LLMRequest or more detailed inputs.
            ProcessingPipeline.HYBRID: self.cost_estimator.estimate_hybrid_cost(email) # Note: Similar to above.
        }
        
        # Predict performance
        performance = {
            ProcessingPipeline.EMBEDDING_ONLY: 0.95,  # Fast
            ProcessingPipeline.LLM_ONLY: 0.85,  # Slower
            ProcessingPipeline.HYBRID: 0.90  # Balanced
        }
        
        # Apply constraints
        if constraints:
            max_cost = constraints.get('max_cost', float('inf'))
            min_accuracy = constraints.get('min_accuracy', 0.0)
            max_latency_ms = constraints.get('max_latency_ms', 5000)
        else:
            max_cost = 0.01  # Default 1 cent per email
            min_accuracy = 0.8
            max_latency_ms = 3000
        
        # Decision logic
        selected_pipeline = self._select_pipeline(
            task_type=task_type,
            complexity_score=complexity_score,
            costs=costs,
            performance=performance,
            max_cost=max_cost,
            min_accuracy=min_accuracy
        )
        
        # Build routing metadata
        metadata = {
            'complexity_score': complexity_score,
            'estimated_costs': costs,
            'performance_predictions': performance,
            'selected_pipeline': selected_pipeline.value,
            'reasoning': self._explain_routing_decision(
                selected_pipeline, complexity_score, costs
            )
        }
        
        return selected_pipeline, metadata
    
    def _select_pipeline(
        self,
        task_type: str,
        complexity_score: float,
        costs: Dict[ProcessingPipeline, float],
        performance: Dict[ProcessingPipeline, float],
        max_cost: float,
        min_accuracy: float
    ) -> ProcessingPipeline:
        """Select optimal pipeline based on multiple factors"""
        
        # Task-specific routing rules
        if task_type == "simple_categorization":
            if complexity_score < 0.3:
                return ProcessingPipeline.EMBEDDING_ONLY
        
        elif task_type == "natural_language_rule":
            # Always need LLM for natural language understanding
            return ProcessingPipeline.LLM_ONLY
        
        elif task_type == "pattern_detection":
            if complexity_score < 0.5:
                return ProcessingPipeline.EMBEDDING_ONLY
            elif complexity_score < 0.8:
                return ProcessingPipeline.HYBRID
            else:
                return ProcessingPipeline.LLM_ONLY
        
        elif task_type == "importance_ranking":
            # Hybrid approach works best for nuanced ranking
            return ProcessingPipeline.HYBRID
        
        # Default logic based on constraints
        valid_pipelines = []
        
        for pipeline, cost in costs.items():
            if cost <= max_cost and performance[pipeline] >= min_accuracy:
                valid_pipelines.append(pipeline)
        
        if not valid_pipelines:
            # Fallback to cheapest option
            return ProcessingPipeline.EMBEDDING_ONLY
        
        # Select best performance within constraints
        return max(valid_pipelines, key=lambda p: performance[p])
    
    def _explain_routing_decision(
        self,
        pipeline: ProcessingPipeline,
        complexity: float,
        costs: Dict[ProcessingPipeline, float]
    ) -> str:
        """Generate human-readable explanation"""
        
        if pipeline == ProcessingPipeline.EMBEDDING_ONLY:
            return (
                f"Using embedding-only pipeline due to low complexity "
                f"({complexity:.2f}) and cost efficiency (${costs[pipeline]:.4f})"
            )
        elif pipeline == ProcessingPipeline.LLM_ONLY:
            return (
                f"Using LLM-only pipeline for high complexity task "
                f"({complexity:.2f}) requiring advanced reasoning"
            )
        else:
            return (
                f"Using hybrid pipeline to balance accuracy and cost "
                f"(complexity: {complexity:.2f}, cost: ${costs[pipeline]:.4f})"
            )


class ComplexityAnalyzer:
    """Analyzes email complexity for routing decisions"""
    
    def analyze(self, email: Dict[str, Any]) -> float:
        """
        Calculate complexity score (0-1)
        
        Factors:
        - Content length and structure
        - Language complexity
        - Number of topics
        - Ambiguity indicators
        - Attachment complexity
        """
        
        scores = []
        
        # Length complexity
        content_length = len(email.get('content', ''))
        length_score = min(content_length / 5000, 1.0)
        scores.append(length_score * 0.2)
        
        # Structural complexity
        line_count = email.get('content', '').count('\n')
        structure_score = min(line_count / 50, 1.0)
        scores.append(structure_score * 0.15)
        
        # Language complexity (simplified)
        complex_words = ['however', 'therefore', 'nevertheless', 'furthermore']
        word_count = sum(1 for word in complex_words if word in email.get('content', '').lower())
        language_score = min(word_count / 5, 1.0)
        scores.append(language_score * 0.25)
        
        # Topic diversity
        # In production, use more sophisticated topic modeling
        sentences = email.get('content', '').split('.')
        topic_score = min(len(sentences) / 20, 1.0)
        scores.append(topic_score * 0.2)
        
        # Ambiguity indicators
        ambiguous_phrases = ['maybe', 'possibly', 'might', 'could be', 'not sure']
        ambiguity_count = sum(1 for phrase in ambiguous_phrases if phrase in email.get('content', '').lower())
        ambiguity_score = min(ambiguity_count / 3, 1.0)
        scores.append(ambiguity_score * 0.2)
        
        return sum(scores)
```

---

## 3. Privacy-Preserving Email Processing

```python
# damien_cli/features/ai_intelligence/llm_integration/privacy.py

from typing import Dict, List, Any, Tuple, Optional
import re
import hashlib
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PIIEntity:
    """Represents a PII entity found in text"""
    entity_type: str
    value: str
    start_pos: int
    end_pos: int
    confidence: float
    replacement_token: str

class PrivacyGuardian:
    """Comprehensive privacy protection for LLM processing"""
    
    def __init__(self):
        self.pii_patterns = self._compile_patterns()
        self.tokenizer = PIITokenizer()
        self.audit_logger = AuditLogger()
    
    def process_email_privately(
        self,
        email: Dict[str, Any],
        protection_level: str = "standard"  # minimal, standard, maximum
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process email with privacy protection
        
        Returns:
            - Sanitized email safe for LLM
            - Privacy metadata for restoration
        """
        
        # Start privacy audit trail
        audit_id = self.audit_logger.start_audit(email['id'])
        
        # Deep copy to avoid modifying original
        import copy
        sanitized = copy.deepcopy(email)
        
        # Detect all PII
        pii_report = self.detect_pii_comprehensive(email)
        
        # Apply protection based on level
        if protection_level == "minimal":
            sanitized, mappings = self._apply_minimal_protection(sanitized, pii_report)
        elif protection_level == "standard":
            sanitized, mappings = self._apply_standard_protection(sanitized, pii_report)
        else:  # maximum
            sanitized, mappings = self._apply_maximum_protection(sanitized, pii_report)
        
        # Create privacy metadata
        privacy_metadata = {
            'audit_id': audit_id,
            'protection_level': protection_level,
            'pii_detected': len(pii_report['entities']),
            'pii_types': list(set(e.entity_type for e in pii_report['entities'])),
            'token_mappings': mappings,
            'processing_timestamp': datetime.utcnow().isoformat(),
            'original_hash': hashlib.sha256(str(email).encode()).hexdigest()
        }
        
        # Log privacy action
        self.audit_logger.log_action(
            audit_id,
            'sanitization_complete',
            privacy_metadata
        )
        
        return sanitized, privacy_metadata
    
    def detect_pii_comprehensive(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive PII detection across all email fields"""
        
        entities = []
        
        # Check all text fields
        text_fields = ['subject', 'content', 'snippet', 'from_sender', 'to_recipients']
        
        for field in text_fields:
            if field in email and email[field]:
                field_entities = self._detect_pii_in_text(
                    email[field],
                    field_name=field
                )
                entities.extend(field_entities)
        
        # Check structured data
        if 'attachments' in email:
            for attachment in email['attachments']:
                if 'filename' in attachment:
                    filename_entities = self._detect_pii_in_text(
                        attachment['filename'],
                        field_name='attachment_filename'
                    )
                    entities.extend(filename_entities)
        
        return {
            'has_pii': len(entities) > 0,
            'entity_count': len(entities),
            'entities': entities,
            'risk_score': self._calculate_privacy_risk(entities)
        }
    
    def _detect_pii_in_text(
        self,
        text: str,
        field_name: str
    ) -> List[PIIEntity]:
        """Detect PII entities in a text field"""
        
        entities = []
        
        for pii_type, pattern in self.pii_patterns.items():
            for match in pattern.finditer(text):
                # Generate unique token for this PII
                token = self.tokenizer.generate_token(
                    pii_type,
                    match.group(),
                    field_name
                )
                
                entity = PIIEntity(
                    entity_type=pii_type,
                    value=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=self._get_confidence(pii_type, match.group()),
                    replacement_token=token
                )
                
                entities.append(entity)
        
        # Additional detection using NER (if available)
        if hasattr(self, 'ner_model'):
            ner_entities = self._detect_pii_with_ner(text, field_name)
            entities.extend(ner_entities)
        
        return entities
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for PII detection"""
        
        patterns = {
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            'phone': re.compile(
                r'(\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                re.IGNORECASE
            ),
            'ssn': re.compile(
                r'\b\d{3}-?\d{2}-?\d{4}\b'
            ),
            'credit_card': re.compile(
                r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
            ),
            'ip_address': re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),
            'date_of_birth': re.compile(
                r'\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12][0-9]|3[01])[/-](?:19|20)\d{2}\b'
            ),
            'passport': re.compile(
                r'\b[A-Z]{1,2}\d{6,9}\b'
            ),
            'bank_account': re.compile(
                r'\b\d{8,17}\b'  # Simplified - needs context
            ),
            'medical_record': re.compile(
                r'\b(?:MRN|Medical Record Number)[:\s]*\w+\b',
                re.IGNORECASE
            )
        }
        
        return patterns
    
    def _apply_standard_protection(
        self,
        email: Dict[str, Any],
        pii_report: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Apply standard privacy protection"""
        
        mappings = {}
        
        # Sort entities by position (reverse) to maintain positions
        entities = sorted(
            pii_report['entities'],
            key=lambda e: (e.start_pos, e.end_pos),
            reverse=True
        )
        
        # Process each field
        for field in ['subject', 'content', 'snippet']:
            if field not in email:
                continue
            
            field_text = email[field]
            field_entities = [e for e in entities if field in str(e)]
            
            # Replace PII with tokens
            for entity in field_entities:
                # Store mapping
                mappings[entity.replacement_token] = entity.value
                
                # Replace in text
                field_text = (
                    field_text[:entity.start_pos] +
                    entity.replacement_token +
                    field_text[entity.end_pos:]
                )
            
            email[field] = field_text
        
        # Sanitize sender/recipient fields
        if 'from_sender' in email:
            sender_token = f"[SENDER_{hashlib.md5(email['from_sender'].encode()).hexdigest()[:8]}]"
            mappings[sender_token] = email['from_sender']
            email['from_sender'] = sender_token
        
        return email, mappings
    
    def restore_pii(
        self,
        processed_content: str,
        mappings: Dict[str, str]
    ) -> str:
        """Restore PII tokens to original values"""
        
        restored = processed_content
        
        # Sort by token length (descending) to avoid partial replacements
        sorted_mappings = sorted(
            mappings.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for token, original in sorted_mappings:
            restored = restored.replace(token, original)
        
        return restored


class PIITokenizer:
    """Generate consistent tokens for PII replacement"""
    
    def __init__(self):
        self.token_cache = {}
    
    def generate_token(
        self,
        pii_type: str,
        value: str,
        context: str
    ) -> str:
        """Generate a consistent token for PII value"""
        
        # Create cache key
        cache_key = f"{pii_type}:{value}:{context}"
        
        if cache_key in self.token_cache:
            return self.token_cache[cache_key]
        
        # Generate token
        value_hash = hashlib.md5(value.encode()).hexdigest()[:8]
        token = f"[{pii_type.upper()}_{value_hash}]"
        
        self.token_cache[cache_key] = token
        return token


class AuditLogger:
    """Audit trail for privacy operations"""
    
    def __init__(self):
        self.audit_store = {}
    
    def start_audit(self, email_id: str) -> str:
        """Start a new audit trail"""
        
        audit_id = f"audit_{email_id}_{datetime.utcnow().timestamp()}"
        
        self.audit_store[audit_id] = {
            'email_id': email_id,
            'start_time': datetime.utcnow(),
            'actions': []
        }
        
        return audit_id
    
    def log_action(
        self,
        audit_id: str,
        action: str,
        details: Dict[str, Any]
    ):
        """Log a privacy action"""
        
        if audit_id in self.audit_store:
            self.audit_store[audit_id]['actions'].append({
                'timestamp': datetime.utcnow(),
                'action': action,
                'details': details
            })
    
    def get_audit_trail(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve audit trail"""
        return self.audit_store.get(audit_id)
```

---

## 4. Advanced Pattern Detection with LLM

```python
# damien_cli/features/ai_intelligence/llm_integration/advanced_patterns.py

from typing import List, Dict, Any, Optional, Set
import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from collections import defaultdict
import asyncio

class AdvancedPatternDetector:
    """Enhanced pattern detection using LLM reasoning"""
    
    def __init__(
        self,
        llm_service: BaseLLMService, # Defined in base.py
        embedding_service: EmbeddingService # Placeholder ABC, e.g., defined in prompts.py or a new embeddings.py
    ):
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.pattern_analyzer = PatternAnalyzer() # Assumed helper class for this context
    
    async def detect_complex_patterns(
        self,
        emails: List[Dict[str, Any]],
        existing_patterns: List[Dict[str, Any]],
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect complex patterns using hybrid approach
        """
        
        # Step 1: Generate embeddings for all emails
        embeddings = await self._generate_email_embeddings(emails)
        
        # Step 2: Cluster emails using multiple algorithms
        clusters = self._multi_algorithm_clustering(embeddings)
        
        # Step 3: Analyze each cluster with LLM
        pattern_candidates = []
        
        for cluster_id, cluster_emails in clusters.items():
            if len(cluster_emails) < 3:  # Skip small clusters
                continue
            
            # Get LLM analysis of cluster
            analysis = await self._analyze_cluster_with_llm(
                cluster_emails,
                user_context
            )
            
            if analysis['is_meaningful_pattern']:
                pattern_candidates.append({
                    'cluster_id': cluster_id,
                    'emails': cluster_emails,
                    'llm_analysis': analysis,
                    'confidence': analysis['confidence']
                })
        
        # Step 4: Refine patterns with cross-validation
        refined_patterns = await self._refine_patterns(
            pattern_candidates,
            existing_patterns
        )
        
        # Step 5: Generate actionable insights
        actionable_patterns = await self._make_patterns_actionable(
            refined_patterns,
            user_context
        )
        
        return actionable_patterns
    
    async def _generate_email_embeddings(
        self,
        emails: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Generate embeddings for emails"""
        
        embeddings = []
        
        # Batch process for efficiency
        batch_size = 50
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            
            # Create combined text for embedding
            texts = []
            for email in batch:
                combined_text = f"{email.get('subject', '')} {email.get('snippet', '')}"
                texts.append(combined_text)
            
            # Generate embeddings
            batch_embeddings = await self.embedding_service.embed_batch(texts)
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
    
    def _multi_algorithm_clustering(
        self,
        embeddings: np.ndarray
    ) -> Dict[str, List[int]]:
        """Apply multiple clustering algorithms"""
        
        clusters = {}
        
        # DBSCAN for density-based patterns
        dbscan = DBSCAN(eps=0.3, min_samples=3, metric='cosine')
        dbscan_labels = dbscan.fit_predict(embeddings)
        
        for label in set(dbscan_labels):
            if label != -1:  # Skip noise
                cluster_indices = np.where(dbscan_labels == label)[0].tolist()
                clusters[f'dbscan_{label}'] = cluster_indices
        
        # Agglomerative for hierarchical patterns
        if len(embeddings) > 10:
            n_clusters = min(len(embeddings) // 5, 20)
            agglo = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric='cosine',
                linkage='average'
            )
            agglo_labels = agglo.fit_predict(embeddings)
            
            for label in set(agglo_labels):
                cluster_indices = np.where(agglo_labels == label)[0].tolist()
                if len(cluster_indices) >= 3:
                    clusters[f'agglo_{label}'] = cluster_indices
        
        return clusters
    
    async def _analyze_cluster_with_llm(
        self,
        cluster_emails: List[Dict[str, Any]],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to analyze email cluster"""
        
        # Prepare cluster summary
        cluster_summary = self._create_cluster_summary(cluster_emails)
        
        # Create analysis prompt
        prompt = f"""
Analyze this cluster of similar emails to identify meaningful patterns:

Cluster Summary:
{json.dumps(cluster_summary, indent=2)}

Sample Emails (first 5):
{json.dumps([self._summarize_email(e) for e in cluster_emails[:5]], indent=2)}

User Context:
- Email volume: {user_context.get('total_emails', 'unknown')}
- Time period: {user_context.get('time_period', 'unknown')}

Identify:
1. What makes these emails similar (be specific)
2. Is this a meaningful pattern worth automating?
3. What conditions would accurately identify this pattern?
4. Potential exceptions or edge cases
5. Suggested automation actions

Output JSON:
{{
  "pattern_type": "sender|subject|content|behavioral|temporal",
  "pattern_description": "clear description",
  "is_meaningful_pattern": true/false,
  "confidence": 0.0-1.0,
  "identifying_features": ["feature1", "feature2"],
  "suggested_conditions": [
    {{"field": "", "operator": "", "value": ""}}
  ],
  "potential_exceptions": ["exception1"],
  "automation_suggestions": [
    {{"action": "", "reasoning": ""}}
  ],
  "business_impact": "description of impact"
}}
"""
        
        request = LLMRequest(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json"}
        )
        
        response = await self.llm_service.complete(request)
        return json.loads(response.content)
    
    def _create_cluster_summary(
        self,
        emails: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create statistical summary of email cluster"""
        
        summary = {
            'email_count': len(emails),
            'unique_senders': len(set(e.get('from_sender', '') for e in emails)),
            'common_subjects': self._get_common_phrases(
                [e.get('subject', '') for e in emails]
            ),
            'time_distribution': self._analyze_time_distribution(emails),
            'common_labels': self._get_common_labels(emails),
            'avg_length': np.mean([len(e.get('content', '')) for e in emails])
        }
        
        return summary
    
    def _get_common_phrases(
        self,
        texts: List[str],
        min_length: int = 3,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """Extract common phrases from texts"""
        
        from collections import Counter
        import re
        
        # Simple n-gram extraction
        all_phrases = []
        
        for text in texts:
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Bigrams and trigrams
            for n in [2, 3]:
                for i in range(len(words) - n + 1):
                    phrase = ' '.join(words[i:i+n])
                    if len(phrase) >= min_length:
                        all_phrases.append(phrase)
        
        # Count and return top phrases
        phrase_counts = Counter(all_phrases)
        
        return [
            {'phrase': phrase, 'count': count}
            for phrase, count in phrase_counts.most_common(top_n)
        ]
    
    async def _refine_patterns(
        self,
        candidates: List[Dict[str, Any]],
        existing_patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Refine pattern candidates"""
        
        refined = []
        
        for candidate in candidates:
            # Check overlap with existing patterns
            overlap_score = self._calculate_pattern_overlap(
                candidate,
                existing_patterns
            )
            
            if overlap_score > 0.7:
                # Too similar to existing pattern
                continue
            
            # Validate pattern with additional analysis
            validation = await self._validate_pattern(candidate)
            
            if validation['is_valid']:
                refined.append({
                    **candidate,
                    'validation': validation,
                    'uniqueness_score': 1 - overlap_score
                })
        
        return refined
    
    async def _make_patterns_actionable(
        self,
        patterns: List[Dict[str, Any]],
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert patterns to actionable insights"""
        
        actionable = []
        
        for pattern in patterns:
            # Generate rule suggestions
            rules = await self._generate_rule_suggestions(pattern)
            
            # Calculate impact
            impact = self._calculate_pattern_impact(
                pattern,
                user_context
            )
            
            # Create actionable pattern
            actionable.append({
                'pattern_id': f"pattern_{hash(str(pattern))}"[:12],
                'pattern_type': pattern['llm_analysis']['pattern_type'],
                'description': pattern['llm_analysis']['pattern_description'],
                'confidence': pattern['confidence'],
                'email_count': len(pattern['emails']),
                'suggested_rules': rules,
                'impact_analysis': impact,
                'implementation_priority': self._calculate_priority(
                    pattern, impact
                )
            })
        
        # Sort by priority
        actionable.sort(
            key=lambda x: x['implementation_priority'],
            reverse=True
        )
        
        return actionable
```

---

## 5. Cost Management System

```python
# damien_cli/features/ai_intelligence/llm_integration/cost_manager.py

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

class CostManagementSystem:
    """Comprehensive cost tracking and optimization"""
    
    def __init__(self):
        # Note: The actual cost_management.py file currently implements UsageTracker and CostEstimator.
        # BudgetController and CostOptimizer are conceptual components of a more complete system
        # and are shown here as part of the CostManagementSystem's potential composition.
        self.usage_tracker = UsageTracker() # Implemented in cost_management.py
        self.budget_controller = BudgetController() # Placeholder/Conceptual for this snippet
        self.optimizer = CostOptimizer() # Placeholder/Conceptual for this snippet
    
    async def process_with_budget(
        self,
        request: LLMRequest,
        budget_limit: float,
        user_id: str
    ) -> Optional[LLMResponse]:
        """Process request within budget constraints"""
        
        # Check remaining budget
        remaining_budget = self.budget_controller.get_remaining_budget(user_id)
        
        if remaining_budget <= 0:
            raise BudgetExceededError(
                f"User {user_id} has exceeded budget limit"
            )
        
        # Estimate cost
        estimated_cost = self.estimate_request_cost(request)
        
        if estimated_cost > remaining_budget:
            # Try to optimize request
            optimized_request = await self.optimizer.optimize_request(
                request,
                target_cost=remaining_budget
            )
            
            if optimized_request:
                request = optimized_request
                estimated_cost = self.estimate_request_cost(request)
            else:
                raise BudgetExceededError(
                    f"Request cost (${estimated_cost:.4f}) exceeds "
                    f"remaining budget (${remaining_budget:.4f})"
                )
        
        # Process request
        response = await self.llm_service.complete(request)
        
        # Track usage
        actual_cost = response.usage['estimated_cost']
        self.usage_tracker.track_usage(
            user_id=user_id,
            cost=actual_cost,
            tokens=response.usage['total_tokens'],
            model=response.model,
            request_type=request.metadata.get('type', 'unknown')
        )
        
        # Update budget
        self.budget_controller.deduct_from_budget(user_id, actual_cost)
        
        return response
    
    def get_usage_report(
        self,
        user_id: str,
        time_period: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """Generate comprehensive usage report"""
        
        usage_data = self.usage_tracker.get_usage_data(user_id, time_period)
        
        report = {
            'user_id': user_id,
            'period': {
                'start': (datetime.utcnow() - time_period).isoformat(),
                'end': datetime.utcnow().isoformat()
            },
            'total_cost': sum(u['cost'] for u in usage_data),
            'total_tokens': sum(u['tokens'] for u in usage_data),
            'request_count': len(usage_data),
            'cost_by_model': self._aggregate_by_field(usage_data, 'model', 'cost'),
            'tokens_by_model': self._aggregate_by_field(usage_data, 'model', 'tokens'),
            'cost_by_type': self._aggregate_by_field(usage_data, 'request_type', 'cost'),
            'daily_usage': self._calculate_daily_usage(usage_data),
            'cost_trends': self._analyze_cost_trends(usage_data),
            'optimization_suggestions': self._generate_optimization_suggestions(usage_data)
        }
        
        return report
    
    def _aggregate_by_field(
        self,
        data: List[Dict[str, Any]],
        field: str,
        metric: str
    ) -> Dict[str, float]:
        """Aggregate metric by field"""
        
        aggregated = defaultdict(float)
        
        for item in data:
            key = item.get(field, 'unknown')
            value = item.get(metric, 0)
            aggregated[key] += value
        
        return dict(aggregated)
    
    def _generate_optimization_suggestions(
        self,
        usage_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate cost optimization suggestions"""
        
        suggestions = []
        
        # Analyze model usage
        model_costs = self._aggregate_by_field(usage_data, 'model', 'cost')
        
        if 'gpt-4' in model_costs and 'gpt-3.5-turbo' in model_costs:
            gpt4_ratio = model_costs['gpt-4'] / sum(model_costs.values())
            
            if gpt4_ratio > 0.7:
                suggestions.append({
                    'type': 'model_optimization',
                    'description': 'Consider using GPT-3.5 for simpler tasks',
                    'potential_savings': model_costs['gpt-4'] * 0.5 * 0.9,  # 50% to GPT-3.5 saves 90%
                    'priority': 'high'
                })
        
        # Analyze request patterns
        hourly_distribution = self._calculate_hourly_distribution(usage_data)
        peak_hours = sorted(
            hourly_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        if peak_hours[0][1] > sum(hourly_distribution.values()) * 0.3:
            suggestions.append({
                'type': 'batching_optimization',
                'description': f'Batch process emails during peak hours {peak_hours[0][0]}:00',
                'potential_savings': sum(model_costs.values()) * 0.15,  # 15% savings from batching
                'priority': 'medium'
            })
        
        return suggestions


class CostOptimizer:
    """Optimize LLM requests for cost efficiency"""
    
    async def optimize_request(
        self,
        request: LLMRequest,
        target_cost: float
    ) -> Optional[LLMRequest]:
        """Optimize request to meet cost target"""
        
        optimized = request.model_copy()
        
        # Strategy 1: Reduce max tokens
        if optimized.max_tokens > 1000:
            optimized.max_tokens = min(1000, int(optimized.max_tokens * 0.7))
        
        # Strategy 2: Compress prompt
        compressed_prompt = await self._compress_prompt(optimized.prompt)
        if len(compressed_prompt) < len(optimized.prompt) * 0.8:
            optimized.prompt = compressed_prompt
        
        # Strategy 3: Switch to cheaper model
        if hasattr(optimized, 'model') and optimized.model == 'gpt-4':
            # Check if task is suitable for GPT-3.5
            if self._is_suitable_for_cheaper_model(request):
                optimized.model = 'gpt-3.5-turbo'
        
        # Verify optimization meets target
        new_cost = self.estimate_request_cost(optimized)
        
        if new_cost <= target_cost:
            return optimized
        
        return None
    
    async def _compress_prompt(self, prompt: str) -> str:
        """Intelligently compress prompt while maintaining meaning"""
        
        # Remove redundant whitespace
        compressed = ' '.join(prompt.split())
        
        # Remove examples if prompt is too long
        if len(compressed) > 2000 and 'Example:' in compressed:
            parts = compressed.split('Example:')
            compressed = parts[0] + 'Example: [Examples removed for brevity]'
        
        # Summarize long content blocks
        if len(compressed) > 3000:
            # Use a simple summarization
            lines = compressed.split('\n')
            if len(lines) > 20:
                # Keep first 10 and last 5 lines
                compressed = '\n'.join(lines[:10] + ['...'] + lines[-5:])
        
        return compressed
```

This technical implementation guide provides detailed code examples for the core components of the Phase 3 LLM integration. The implementation follows enterprise-grade standards with comprehensive error handling, monitoring, and optimization strategies.
---
## 6. Advanced Content Handling (Large Volume Emails)

Processing a large corpus of emails (e.g., 100K+) introduces challenges related to API rate limits, token limits per request, cost, and overall processing time. This section outlines strategies and architectural components to address these challenges.

### 6.1. Batch Processing API Integration

For bulk analysis of existing emails or large volumes of new emails where real-time results are not critical, using provider-specific Batch APIs is highly recommended for cost savings and improved throughput.

*   **Abstract Batch Interface (`BaseLLMService`):**
    *   The `BaseLLMService` abstract class (in `damien_cli/features/ai_intelligence/llm_integration/base.py`) should be extended with methods for batch operations:
        ```python
        # In BaseLLMService
        @abstractmethod
        async def submit_batch(self, requests: List[LLMRequest]) -> str: # Returns job_id
            pass

        @abstractmethod
        async def get_batch_status(self, job_id: str) -> Dict[str, Any]: # Returns status, progress
            pass

        @abstractmethod
        async def get_batch_results(self, job_id: str) -> List[LLMResponse]: # Returns list of responses
            pass
        ```
*   **Provider-Specific Implementations:**
    *   `OpenAIProvider`, `AnthropicProvider` (and potentially others) will implement these batch methods, handling the specifics of their respective Batch APIs (e.g., file upload formats, API calls for job creation, status polling, and results retrieval).
*   **`BatchProcessingService` (New Component):**
    *   A dedicated service, e.g., `damien_cli.features.ai_intelligence.batch_processor.BatchProcessingService`.
    *   **Responsibilities:**
        *   Accepting a large list of processing tasks (e.g., email IDs and desired operations).
        *   Preparing `LLMRequest`-like objects for each task.
        *   **Batch Splitting:** Determining the target provider's batch limits (e.g., max requests per file, max file size) and splitting the overall job into multiple smaller, API-compliant sub-batches.
        *   **Provider Selection for Batch:** Deciding which LLM provider to use for the batch job (could be a simplified version of `ProviderSelector` logic or direct configuration).
        *   Submitting each sub-batch using the chosen provider's `submit_batch` method.
        *   Managing and tracking all submitted batch job IDs.
        *   **Job Monitoring:** Implementing a polling mechanism (e.g., using background tasks or a scheduled job system like Celery with beat) to check `get_batch_status` for each job ID. Alternatively, handle API callbacks/webhooks if supported by the provider.
        *   Retrieving results using `get_batch_results` upon completion.
        *   Aggregating results from all sub-batches.
        *   Handling errors and retries for batch submission and result retrieval.
    *   **Workflow Example:**
        ```mermaid
        graph TD
            A[Corpus Manager (provides 100K email tasks)] --> B[BatchProcessingService];
            B -- Prepare LLMRequests --> B;
            B -- Split into Sub-Batches (e.g., Batch1, Batch2) --> B;
            B -- Select Provider (e.g., Anthropic) --> B;
            B -- For Each Sub-Batch --> SBP[Submit via Provider.submit_batch()];
            SBP -- JobID_1, JobID_2... --> B;
            B -- Poll Provider.get_batch_status(JobID) --> PBS[Provider Batch API];
            PBS -- Status --> B;
            B -- If Complete --> GBR[Provider.get_batch_results(JobID)];
            GBR -- LLMResponses --> B;
            B -- Aggregate & Store Results --> Z[Results Datastore];
        ```
*   **Cost Tracking:** The `UsageTracker` and `CostEstimator` in `cost_management.py` must be updated to correctly account for batch job costs, including any provider-specific discounts (e.g., Anthropic's 50% discount for batch).

### 6.2. Token Limits and Chunking Strategies for Long Emails

Individual emails, especially with long threads or attachments, can exceed even large context windows (e.g., 200K tokens).

*   **A. Enhanced `EmailPreprocessor`:**
    *   **Path:** `damien_cli/features/ai_intelligence/llm_integration/preprocessor.py` (currently a placeholder in `PHASE_3_LLM_INTEGRATION_PLAN.md`).
    *   **Robust Text Extraction:** Implement reliable extraction of clean text from various email MIME types (text/plain, text/html) and common attachment types (PDF, DOCX, TXT). Libraries like `BeautifulSoup4` (for HTML), `pypdfium2` or `PyPDF2` (for PDF), `python-docx` (for DOCX) will be necessary.
    *   **Boilerplate Stripping:** Develop techniques (regex, heuristics, potentially a small specialized LLM call) to remove common signatures, disclaimers, quoted replies in threads (when only the latest reply is needed), and other non-essential content.
    *   **Structured Output:** The preprocessor should ideally output structured text, e.g., distinguishing the main body, sender, subject, date, and extracted text from key attachments, each with metadata.
*   **B. `TextChunker` Service/Utility:**
    *   **New Component:** e.g., `damien_cli.features.ai_intelligence.text_utils.TextChunker`.
    *   **Responsibilities:** Take a single large block of text and split it into smaller, overlapping chunks suitable for an LLM's context window.
    *   **Chunking Strategies (configurable, using Strategy Pattern):**
        1.  **Token-Based (Primary):** Use `TokenCounter` to split text into chunks of a specified max token length (e.g., `target_model_context_window - prompt_overhead - response_allowance`). Requires knowledge of the target LLM for accurate tokenization.
        2.  **Semantic/Recursive:** Split by paragraphs, then sentences, then words, attempting to keep semantically related text together. LangChain's `RecursiveCharacterTextSplitter` is a good reference.
        3.  **Sentence-Based:** Use libraries like `nltk` for sentence tokenization as split points.
    *   **Overlap:** Implement configurable overlap between chunks to maintain contextual coherence.
    *   **Metadata:** Each chunk must retain metadata linking it to the original email ID, its sequence number, and potentially a summary of the preceding chunk.
*   **C. `HierarchicalTaskProcessor` (Map-Reduce for LLMs):**
    *   **New Component:** e.g., `damien_cli.features.ai_intelligence.processing_strategies.HierarchicalTaskProcessor`.
    *   **Purpose:** To perform tasks like summarization or Q&A over content that has been split into multiple chunks.
    *   **Workflow (e.g., Summarization):**
        1.  **Map Step:** For each chunk of an email, send it to an LLM (potentially a cheaper, faster model like Haiku or GPT-3.5-Turbo/GPT-4o-mini) with a prompt like: "Summarize the key information in the following text chunk: {chunk_content}".
        2.  **Combine/Reduce Step:**
            *   Collect all chunk summaries.
            *   If the combined length of chunk summaries still exceeds a context window, recursively summarize the summaries themselves.
            *   Finally, send the (potentially summarized) collection of chunk summaries to a more capable LLM (e.g., Claude Sonnet, GPT-4o) with a prompt like: "Synthesize these individual summaries into a single, coherent, comprehensive summary of the original document: {list_of_chunk_summaries}".
    *   **Configuration:** This processor would be configured with specific "map" prompts, "combine/reduce" prompts, and choice of LLMs for each stage.
    *   **State Management:** For very long documents, intermediate chunk summaries might need to be stored temporarily (e.g., Redis, file system, database) before the reduce step.
    *   **Diagram:**
        ```mermaid
        graph TD
            A[Original Long Email] --> B[EmailPreprocessor (Clean & Structure)];
            B -- Cleaned Full Text --> C[TextChunker (Token-aware, Overlap)];
            C -- Chunk 1 --> D1[LLM Map (Summarize Chunk 1)];
            C -- Chunk 2 --> D2[LLM Map (Summarize Chunk 2)];
            C -- Chunk N --> Dn[LLM Map (Summarize Chunk N)];
            
            subgraph HierarchicalTaskProcessor
                D1 -- Summary 1 --> E{Combine/Reduce Stage};
                D2 -- Summary 2 --> E;
                Dn -- Summary N --> E;
                E -- Potentially Recursive Summarization of Summaries --> E;
                E -- Final Set of Summaries --> F[LLM Reduce (Final Synthesis)];
            end
            F -- Final Coherent Output --> G[Result (e.g., Full Summary)];
        ```

### 6.3. Retrieval Augmented Generation (RAG) for Corpus-Wide Analysis

When dealing with 100K+ emails, it's impossible to fit the entire corpus into an LLM's context window for broad queries (e.g., "Summarize all emails related to Project X from last quarter"). RAG is essential here.

*   **A. Indexing Pipeline:**
    *   **Preprocessing & Chunking:** Emails are preprocessed and chunked as described in 6.2.
    *   **Embedding Generation:** Each chunk is converted into a vector embedding using a sentence transformer model (e.g., `all-MiniLM-L6-v2` as currently used, or newer models like `text-embedding-3-small` from OpenAI, or Cohere/VoyageAI embeddings).
    *   **Vector Store:** Embeddings and their corresponding text chunks (plus metadata like email ID, date, sender, chunk ID) are stored in a specialized vector database (e.g., Pinecone, Weaviate, Qdrant, ChromaDB, or even PostgreSQL with `pgvector`).
    *   This indexing process needs to run for the initial corpus and incrementally for new emails.
*   **B. Retrieval & Augmentation Query Pipeline:**
    1.  **User Query/Task:** A user query (e.g., "What were the key decisions in meetings about Project X?") or an internal task.
    2.  **Query Embedding:** The query is converted into an embedding using the same model as used for indexing.
    3.  **Similarity Search:** The query embedding is used to search the vector store for the most semantically similar email chunks.
    4.  **Context Assembly:** The retrieved top-K chunks (and their original text) are assembled into a context block.
    5.  **Prompt Augmentation:** This context block is inserted into a prompt for an LLM, along with the original query. Example: "Based on the following email excerpts: {retrieved_chunks_text}\n\nAnswer the question: {user_query}".
    6.  **LLM Call:** The augmented prompt is sent to a capable LLM (e.g., GPT-4o, Claude Sonnet/Opus).
*   **Diagram for RAG Query:**
    ```mermaid
    graph TD
        UQ[User Query / Task] --> QE[Query Embedding];
        VS[Vector Store (Indexed Email Chunks + Metadata)];
        QE -- Similarity Search --> VS;
        VS -- Top-K Relevant Chunks --> CA[Context Assembler];
        CA --> AP[Augmented Prompt (Query + Retrieved Context)];
        AP --> LLM[LLM (e.g., GPT-4o, Claude Opus)];
        LLM -- Answer/Analysis --> Out[Final Output];
    ```
*   **Considerations:**
    *   Choice of embedding model and vector database.
    *   Chunking strategy for RAG might differ from summarization chunking.
    *   Re-ranking retrieved results (e.g., using a cross-encoder) for better relevance.
    *   Handling very large numbers of retrieved chunks (e.g., summarizing them before final LLM call).
    *   This is a significant architectural addition, likely a core part of a later phase (e.g., Phase 4) but planning should start.

### 6.4. Iterative Development and Cost Monitoring

*   **Iterative Development:**
    *   Start all new complex features (batch, chunking, RAG) with a small, representative subset of emails (e.g., 100-1000 diverse emails).
    *   Thoroughly test prompts, output quality, error handling, and performance on this subset before scaling.
    *   Gradually increase the volume.
*   **Cost Monitoring (Reiteration):**
    *   The `CostManagementSystem` (from `cost_management.py`) needs to be robust.
    *   Implement detailed logging of token usage and costs for every LLM call (individual, batch, map, reduce steps).
    *   Set up alerts for budget thresholds.
    *   Regularly review cost reports to identify high-cost operations or inefficient prompts.

This new section provides a strategic overview for handling large-scale email processing. The implementation of these advanced features would likely span across later parts of Phase 3 and into Phase 4.

---