import anthropic
from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio
import time
import json

from ..base import BaseLLMService, LLMRequest, LLMResponse, LLMProvider
from damien_cli.core.app_logging import get_logger

logger = get_logger(__name__)

class AnthropicProvider(BaseLLMService):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.client = anthropic.AsyncAnthropic(
            api_key=config.get('api_key') if config else None
        )
        self.model = config.get('model', 'claude-3-opus-20240229') if config else 'claude-3-opus-20240229'
        
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
    
    async def stream_complete(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream completion for real-time responses"""
        messages = self._build_messages(request)
        
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=messages,
            system=request.system_prompt if request.system_prompt else None
        ) as stream:
            async for text in stream.text_stream:
                yield text
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate request cost in USD"""
        # Anthropic pricing per 1M tokens (as of 2024)
        # Claude 3 Opus: $15/$75 (input/output)
        # Claude 3 Sonnet: $3/$15 (input/output)
        # Claude 3 Haiku: $0.25/$1.25 (input/output)
        
        model_costs = {
            'claude-3-opus-20240229': (0.015, 0.075),  # per 1k tokens
            'claude-3-sonnet-20240229': (0.003, 0.015),
            'claude-3-haiku-20240307': (0.00025, 0.00125),
            'claude-3-5-sonnet-20240620': (0.003, 0.015),  # Claude 3.5 Sonnet
        }
        
        # Rough token estimation (Anthropic uses similar tokenization to OpenAI)
        input_tokens = len(request.prompt.split()) * 1.3  # Rough estimate
        if request.system_prompt:
            input_tokens += len(request.system_prompt.split()) * 1.3
        
        output_tokens = min(request.max_tokens, input_tokens * 0.5)
        
        input_cost_per_1k, output_cost_per_1k = model_costs.get(
            self.model, (0.003, 0.015)  # Default to Sonnet pricing
        )
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return round(input_cost + output_cost, 6)
    
    def validate_request(self, request: LLMRequest) -> bool:
        """Validate request parameters"""
        # Check if prompt is provided
        if not request.prompt:
            logger.warning("Request has no prompt")
            return False
        
        # Check token limits
        max_context = self.model_limits.get(self.model, 200000)
        # Rough token estimation
        estimated_tokens = len(request.prompt.split()) * 1.3
        if request.system_prompt:
            estimated_tokens += len(request.system_prompt.split()) * 1.3
        
        if estimated_tokens + request.max_tokens > max_context:
            logger.warning(
                f"Request may exceed token limit: {estimated_tokens} + "
                f"{request.max_tokens} > {max_context}"
            )
            return False
        
        # Validate temperature
        if not 0 <= request.temperature <= 1:
            logger.warning(f"Invalid temperature: {request.temperature}")
            return False
        
        return True