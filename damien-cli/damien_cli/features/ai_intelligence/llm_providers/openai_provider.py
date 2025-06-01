import openai
import tiktoken
import os
import json
import time
from typing import List, Optional, Dict, Any, Literal, AsyncGenerator
import asyncio
from datetime import datetime
from pathlib import Path
from damien_cli.core.config import settings
from .base import BaseLLMProvider

class TokenUsageTracker:
    """Track and analyze OpenAI token usage for cost optimization."""
    
    def __init__(self):
        self.log_path = os.getenv('TOKEN_USAGE_LOG_PATH', './logs/token_usage.json')
        self.cost_threshold = float(os.getenv('COST_ALERT_THRESHOLD_USD', '10.0'))
        
        # Latest OpenAI pricing (2024)
        self.pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},  # per 1K tokens
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # per 1K tokens
            "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
            "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
        }
    
    def track_usage(self, operation: str, model: str, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track token usage with cost calculation."""
        input_tokens = usage_data.get('prompt_tokens', 0)
        output_tokens = usage_data.get('completion_tokens', 0)
        
        # Calculate cost
        cost_usd = 0.0
        if model in self.pricing:
            pricing = self.pricing[model]
            cost_usd = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
        
        usage_event = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost_usd,
            "usage_data": usage_data
        }
        
        # Log to file if tracking enabled
        if os.getenv('TRACK_TOKEN_USAGE', 'false').lower() == 'true':
            self._save_usage(usage_event)
        
        # Alert if cost threshold exceeded
        if cost_usd > self.cost_threshold:
            print(f"⚠️ Cost alert: ${cost_usd:.4f} exceeds threshold ${self.cost_threshold}")
        
        return usage_event
    
    def _save_usage(self, event: Dict[str, Any]):
        """Save usage event to log file."""
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            
            # Load existing data
            if os.path.exists(self.log_path):
                with open(self.log_path, 'r') as f:
                    data = json.load(f)
            else:
                data = []
            
            data.append(event)
            
            # Save updated data
            with open(self.log_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to save token usage: {e}")


class SmartModelRouter:
    """Intelligently route between models based on complexity and cost."""
    
    def __init__(self):
        self.strategy = os.getenv('AI_MODEL_STRATEGY', 'cost_optimized')
        self.simple_threshold = int(os.getenv('SIMPLE_TASK_MAX_TOKENS', '1000'))
        self.complex_confidence = float(os.getenv('COMPLEX_TASK_MIN_CONFIDENCE', '0.8'))
    
    def select_model(self, task_type: str = "general", estimated_tokens: int = 500, 
                    complexity: Literal["simple", "medium", "complex"] = "medium") -> str:
        """Select optimal model based on task characteristics."""
        
        if self.strategy == "cost_optimized":
            # Use gpt-4o-mini for most tasks, gpt-4o only for complex
            if complexity == "complex" or estimated_tokens > 3000:
                return os.getenv('OPENAI_COMPLEX_MODEL', 'gpt-4o')
            else:
                return os.getenv('OPENAI_DEFAULT_MODEL', 'gpt-4o-mini')
        
        elif self.strategy == "performance_optimized":
            # Always use best model
            return os.getenv('OPENAI_COMPLEX_MODEL', 'gpt-4o')
        
        else:  # balanced
            # Smart selection based on task characteristics
            if complexity == "simple" and estimated_tokens < self.simple_threshold:
                return os.getenv('OPENAI_DEFAULT_MODEL', 'gpt-4o-mini')
            else:
                return os.getenv('OPENAI_COMPLEX_MODEL', 'gpt-4o')


class OpenAIProvider(BaseLLMProvider):
    """
    Enhanced OpenAI API provider with latest best practices.
    
    Features:
    - Smart model routing for cost optimization
    - Token usage tracking and cost analysis
    - Async/await with proper resource management
    - Streaming support with usage monitoring
    - Fallback to local models when configured
    """
    
    def __init__(self):
        # Initialize clients
        api_key = os.getenv('OPENAI_API_KEY') or settings.openai_api_key
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
        # Initialize tracking and routing
        self.token_tracker = TokenUsageTracker()
        self.model_router = SmartModelRouter()
        
        # Default models
        self.default_model = os.getenv('OPENAI_DEFAULT_MODEL', 'gpt-4o-mini')
        self.embedding_model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model(self.default_model)
        except:
            self.encoding = tiktoken.get_encoding("o200k_base")  # Latest encoding
    
    async def complete(self, prompt: str, temperature: float = 0.3, 
                      max_tokens: int = 2000, task_type: str = "general",
                      complexity: Literal["simple", "medium", "complex"] = "medium",
                      **kwargs) -> str:
        """
        Generate completion using OpenAI API with smart model selection.
        
        Args:
            prompt: The prompt text
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            task_type: Type of task (for model selection)
            complexity: Task complexity level
            **kwargs: Additional parameters
        """
        try:
            # Smart model selection
            estimated_tokens = self.count_tokens(prompt)
            model = self.model_router.select_model(task_type, estimated_tokens, complexity)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": "You are an expert email analysis assistant for the Damien Email Wrestling system."},
                {"role": "user", "content": prompt}
            ]
            
            start_time = time.time()
            
            # Make API call with latest best practices
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Track usage for cost optimization
            if response.usage:
                self.token_tracker.track_usage(
                    operation=f"completion_{task_type}", 
                    model=model,
                    usage_data=response.usage.model_dump()
                )
            
            duration = time.time() - start_time
            
            # Log performance metrics
            if os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true':
                print(f"✅ OpenAI completion: {model} | {duration:.2f}s | {response.usage.total_tokens if response.usage else 'N/A'} tokens")
            
            return response.choices[0].message.content
            
        except openai.APIConnectionError as e:
            # Fallback to local model if configured
            if os.getenv('LOCAL_MODEL_FALLBACK', 'false').lower() == 'true':
                print(f"⚠️ OpenAI connection failed, falling back to local model: {e}")
                # This would call local provider - placeholder for now
                raise Exception(f"OpenAI connection failed and local fallback not implemented: {e}")
            raise Exception(f"OpenAI API connection error: {e}")
            
        except openai.RateLimitError as e:
            print(f"⚠️ OpenAI rate limit hit: {e}")
            await asyncio.sleep(2)  # Brief backoff
            raise Exception(f"OpenAI rate limit error: {e}")
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def complete_streaming(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate streaming completion with token usage tracking.
        """
        try:
            model = self.model_router.select_model(kwargs.get('task_type', 'general'))
            
            messages = [
                {"role": "system", "content": "You are an expert email analysis assistant."},
                {"role": "user", "content": prompt}
            ]
            
            # Stream with usage tracking
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                stream_options={"include_usage": True},
                **kwargs
            )
            
            full_content = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield content
                
                # Track usage from final chunk
                if chunk.usage:
                    self.token_tracker.track_usage(
                        operation="streaming_completion",
                        model=model,
                        usage_data=chunk.usage.model_dump()
                    )
                    
        except Exception as e:
            raise Exception(f"OpenAI streaming error: {str(e)}")
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API with cost tracking."""
        try:
            start_time = time.time()
            
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            # Track embedding usage
            if response.usage:
                self.token_tracker.track_usage(
                    operation="embedding",
                    model=self.embedding_model,
                    usage_data=response.usage.model_dump()
                )
            
            duration = time.time() - start_time
            
            if os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true':
                print(f"✅ OpenAI embedding: {self.embedding_model} | {duration:.2f}s | {response.usage.total_tokens if response.usage else 'N/A'} tokens")
            
            return response.data[0].embedding
            
        except Exception as e:
            raise Exception(f"OpenAI Embedding error: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken with latest encoding."""
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # Fallback estimation
            return len(text.split()) * 1.3  # Rough approximation
    
    async def close(self):
        """Properly close the async client."""
        await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()