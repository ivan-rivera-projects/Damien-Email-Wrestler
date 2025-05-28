"""Email embedding generation with caching and batch processing"""

import numpy as np
import pickle
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from tqdm import tqdm

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available - using mock embeddings")

from damien_cli.core.config import DATA_DIR
from ..models import EmailEmbedding

logger = logging.getLogger(__name__)

class EmailEmbeddingGenerator:
    """Generates and caches embeddings for emails using sentence transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None  # Lazy loading
        self.cache_dir = Path(DATA_DIR) / "ai_intelligence" / "embeddings_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_dim = 384  # Default dimension for MiniLM
        
    def _load_model(self):
        """Lazy load the sentence transformer model"""
        if self.model is None:
            try:
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    logger.info(f"Loading sentence transformer model: {self.model_name}")
                    self.model = SentenceTransformer(self.model_name)
                    self.embedding_dim = self.model.get_sentence_embedding_dimension()
                    logger.info(f"Model loaded successfully, embedding dimension: {self.embedding_dim}")
                else:
                    logger.warning("Using mock embeddings - install sentence-transformers for real embeddings")
                    self.model = "mock"
                    self.embedding_dim = 384
            except Exception as e:
                logger.error(f"Error loading sentence transformer model: {str(e)}")
                logger.warning("Falling back to mock embeddings")
                self.model = "mock"
                self.embedding_dim = 384
    
    def generate_embedding(self, email_data: Dict) -> np.ndarray:
        """Generate embedding for a single email"""
        
        # Check cache first
        cache_key = self._get_cache_key(email_data)
        cached_embedding = self._load_from_cache(cache_key)
        
        if cached_embedding is not None:
            return cached_embedding
        
        # Load model if needed
        self._load_model()
        
        # Prepare text for embedding
        text = self._prepare_email_text(email_data)
        
        try:
            # Generate embedding
            if self.model == "mock":
                # Create deterministic mock embedding based on email content
                embedding = self._create_mock_embedding(text)
            else:
                embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Cache the result
            self._save_to_cache(cache_key, embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return mock embedding as fallback
            return self._create_mock_embedding(text)
    
    def generate_batch_embeddings(self, emails: List[Dict]) -> np.ndarray:
        """Generate embeddings for multiple emails efficiently"""
        
        # Load model if needed
        self._load_model()
        
        # Check which emails need embeddings
        emails_to_process = []
        embeddings = []
        
        for email in emails:
            cache_key = self._get_cache_key(email)
            cached_embedding = self._load_from_cache(cache_key)
            
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                emails_to_process.append((email, len(embeddings)))
                embeddings.append(None)  # Placeholder
        
        # Process uncached emails in batch
        if emails_to_process:
            texts = [self._prepare_email_text(email) for email, _ in emails_to_process]
            
            try:
                if self.model == "mock":
                    batch_embeddings = np.array([
                        self._create_mock_embedding(text) for text in texts
                    ])
                else:
                    batch_embeddings = self.model.encode(
                        texts, 
                        convert_to_numpy=True, 
                        batch_size=32,
                        show_progress_bar=len(texts) > 10
                    )
                
                # Fill in the embeddings and cache them
                for i, (email, index) in enumerate(emails_to_process):
                    embedding = batch_embeddings[i]
                    embeddings[index] = embedding
                    
                    # Cache the embedding
                    cache_key = self._get_cache_key(email)
                    self._save_to_cache(cache_key, embedding)
                
            except Exception as e:
                logger.error(f"Error in batch embedding generation: {str(e)}")
                # Fill with mock embeddings
                for email, index in emails_to_process:
                    text = self._prepare_email_text(email)
                    embeddings[index] = self._create_mock_embedding(text)
        
        return np.array(embeddings)
    
    def _create_mock_embedding(self, text: str) -> np.ndarray:
        """Create a deterministic mock embedding based on text content"""
        
        # Use hash of text to create deterministic but varied embeddings
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # Convert hash to numbers and normalize
        np.random.seed(int(text_hash[:8], 16) % (2**31))
        embedding = np.random.normal(0, 1, self.embedding_dim).astype(np.float32)
        
        # Normalize to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _prepare_email_text(self, email_data: Dict) -> str:
        """Prepare email text for embedding with weighted fields"""
        
        # Extract relevant fields
        from_sender = email_data.get("from_sender", "")
        subject = email_data.get("subject", "")
        snippet = email_data.get("snippet", "")
        labels = " ".join(email_data.get("label_names", []))
        
        # Clean the fields
        from_sender = self._clean_text(from_sender)
        subject = self._clean_text(subject)
        snippet = self._clean_text(snippet)
        labels = self._clean_text(labels)
        
        # Combine fields with appropriate weighting
        # Subject gets most weight, then snippet, then sender, then labels
        text_parts = []
        
        if subject:
            text_parts.append(f"SUBJECT: {subject}")
        
        if snippet:
            text_parts.append(f"CONTENT: {snippet}")
        
        if from_sender:
            text_parts.append(f"FROM: {from_sender}")
        
        if labels:
            text_parts.append(f"LABELS: {labels}")
        
        # Join with newlines
        combined_text = "\n".join(text_parts)
        
        # Truncate if too long (sentence transformers have limits)
        max_length = 512  # Conservative limit
        if len(combined_text) > max_length:
            combined_text = combined_text[:max_length]
        
        return combined_text
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better embedding quality"""
        
        if not text:
            return ""
        
        # Remove email addresses from sender field (keep name part)
        if "@" in text and "<" in text:
            # Extract name from "Name <email@domain.com>" format
            name_part = text.split("<")[0].strip()
            if name_part:
                text = name_part
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Remove HTML tags if present
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        return text.strip()
    
    def _get_cache_key(self, email_data: Dict) -> str:
        """Generate cache key for email"""
        
        # Use email ID if available, otherwise hash the content
        email_id = email_data.get("id")
        if email_id:
            return hashlib.md5(email_id.encode()).hexdigest()
        
        # Fallback: hash the email content
        content = f"{email_data.get('from_sender', '')}{email_data.get('subject', '')}{email_data.get('snippet', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """Load embedding from cache"""
        
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Error loading cached embedding {cache_key}: {str(e)}")
                # Remove corrupted cache file
                cache_file.unlink(missing_ok=True)
        
        return None
    
    def _save_to_cache(self, cache_key: str, embedding: np.ndarray):
        """Save embedding to cache"""
        
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(embedding, f)
        except Exception as e:
            logger.warning(f"Error saving embedding to cache {cache_key}: {str(e)}")
    
    def clear_cache(self):
        """Clear the embedding cache"""
        
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info("Embedding cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get statistics about the cache"""
        
        try:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "cached_embeddings": len(cache_files),
                "total_cache_size_mb": total_size / (1024 * 1024),
                "cache_directory": str(self.cache_dir),
                "model_name": self.model_name,
                "embedding_dimension": self.embedding_dim,
                "using_real_model": SENTENCE_TRANSFORMERS_AVAILABLE and self.model != "mock"
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {"error": str(e)}
