import anthropic
from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio
import time
import json

from ..base import BaseLLMService, LLMRequest, LLMResponse, LLMProvider
from .....core.app_logging import get_logger # Changed to app_logging

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