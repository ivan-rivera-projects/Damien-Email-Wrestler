import asyncio
import json
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
from openai import AsyncOpenAI
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

from ..base import BaseLLMService, LLMRequest, LLMResponse, LLMProvider
from damien_cli.core.config import settings
from damien_cli.core.app_logging import get_logger

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
            if self.cache:
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
            if self.cache:
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