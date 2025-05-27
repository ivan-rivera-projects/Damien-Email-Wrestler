import openai
import tiktoken
from typing import List, Optional
import asyncio
from damien_cli.core.config import settings
from .base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider for LLM operations"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.ai_model
        self.embedding_model = settings.embedding_model
        self.encoding = tiktoken.encoding_for_model(self.model)
        
    async def complete(self, prompt: str, temperature: float = 0.3, 
                      max_tokens: int = 2000, **kwargs) -> str:
        """Generate completion using OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert email rule parser for the Damien Email Wrestler system."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"OpenAI Embedding error: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.encoding.encode(text))