from typing import List, Optional
from .base import BaseLLMProvider

try:
    from transformers import pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    # Define dummy classes/functions if transformers is not available
    class pipeline:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Transformers not installed. Local models are not available.")
        def __call__(self, *args, **kwargs):
            raise RuntimeError("Transformers not installed. Local models are not available.")
    class torch:
        @staticmethod
        def cuda():
            class Cuda:
                @staticmethod
                def is_available():
                    return False
            return Cuda()
        @staticmethod
        def tensor(*args, **kwargs):
             raise RuntimeError("Torch not installed. Local models are not available.")


class LocalModelProvider(BaseLLMProvider):
    """Local model provider for offline operation"""
    
    def __init__(self, model_path: Optional[str] = None):
        if not TRANSFORMERS_AVAILABLE:
             raise RuntimeError("Transformers or Torch not installed. Local models are not available.")
             
        # Use a small model like Flan-T5 or GPT-J
        self.model_name = model_path or "google/flan-t5-base"
        self.generator = pipeline(
            "text2text-generation",
            model=self.model_name,
            device=0 if torch.cuda.is_available() else -1
        )
        
        # For embeddings
        self.embedder = pipeline(
            "feature-extraction",
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion using local model"""
        if not TRANSFORMERS_AVAILABLE:
             raise RuntimeError("Transformers or Torch not installed. Local models are not available.")
             
        # Truncate prompt if needed
        max_length = kwargs.get("max_tokens", 512)
        
        result = self.generator(
            prompt,
            max_length=max_length,
            temperature=kwargs.get("temperature", 0.3),
            do_sample=True
        )
        
        return result[0]["generated_text"]
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using local model"""
        if not TRANSFORMERS_AVAILABLE:
             raise RuntimeError("Transformers or Torch not installed. Local models are not available.")
             
        result = self.embedder(text)
        # Average pooling
        embeddings = torch.tensor(result[0]).mean(dim=0)
        return embeddings.tolist()
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count"""
        if not TRANSFORMERS_AVAILABLE:
             # Provide a rough estimate even if transformers is not available
             return len(text) // 4
             
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4