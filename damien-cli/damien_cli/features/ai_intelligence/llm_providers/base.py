from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion for a prompt"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass