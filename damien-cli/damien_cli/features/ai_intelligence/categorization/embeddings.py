import numpy as np
from typing import List, Dict, Optional
import numpy as np
import hashlib
import pickle
from pathlib import Path
from damien_cli.core.config import DATA_DIR
from typing import List, Dict, Optional

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    # Define a dummy class if sentence_transformers is not available
    class SentenceTransformer:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("sentence-transformers not installed. Email embeddings are not available.")
        def encode(self, *args, **kwargs):
            raise RuntimeError("sentence-transformers not installed. Email embeddings are not available.")


class EmailEmbeddingGenerator:
    """Generates and caches embeddings for emails"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
             raise RuntimeError("sentence-transformers not installed. Email embeddings are not available.")
             
        self.model = SentenceTransformer(model_name)
        self.cache_dir = Path(DATA_DIR) / "embeddings_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
    def generate_embedding(self, email_data: Dict) -> np.ndarray:
        """Generate embedding for an email"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
             raise RuntimeError("sentence-transformers not installed. Email embeddings are not available.")
             
        # Create cache key
        cache_key = self._get_cache_key(email_data)
        cached_embedding = self._load_from_cache(cache_key)
        
        if cached_embedding is not None:
            return cached_embedding
        
        # Prepare text for embedding
        text = self._prepare_email_text(email_data)
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Cache the result
        self._save_to_cache(cache_key, embedding)
        
        return embedding
    
    def generate_batch_embeddings(self, emails: List[Dict]) -> np.ndarray:
        """Generate embeddings for multiple emails efficiently"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
             raise RuntimeError("sentence-transformers not installed. Email embeddings are not available.")
             
        texts = [self._prepare_email_text(email) for email in emails]
        embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
        
        return embeddings
    
    def _prepare_email_text(self, email_data: Dict) -> str:
        """Prepare email text for embedding"""
        
        # Extract relevant fields
        from_sender = email_data.get("from_sender", "")
        subject = email_data.get("subject", "")
        snippet = email_data.get("snippet", "")
        labels = " ".join(email_data.get("label_names", []))
        
        # Combine fields with weights
        text = f"FROM: {from_sender}\nSUBJECT: {subject}\nCONTENT: {snippet}\nLABELS: {labels}"
        
        return text
    
    def _get_cache_key(self, email_data: Dict) -> str:
        """Generate cache key for email"""
        email_id = email_data.get("id", "")
        return hashlib.md5(email_id.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """Load embedding from cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        return None
    
    def _save_to_cache(self, cache_key: str, embedding: np.ndarray):
        """Save embedding to cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        with open(cache_file, "wb") as f:
            pickle.dump(embedding, f)