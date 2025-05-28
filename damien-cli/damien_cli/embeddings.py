
"""
Sentence embedding utility for the Damien CLI.
This module provides functions to create and use sentence embeddings 
for semantic search and similarity operations.
"""

import torch
from sentence_transformers import SentenceTransformer, util


class EmbeddingManager:
    """Manages sentence embeddings for the Damien email platform."""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initialize the embedding manager with a specific model.
        
        Args:
            model_name (str): Name of the sentence-transformers model to use.
                Default: "all-MiniLM-L6-v2" (fast and lightweight)
        """
        # Only attempt to load the model when specifically needed
        self.model_name = model_name
        self.model = None
        
    def _ensure_model_loaded(self):
        """Ensures the model is loaded before operations."""
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
                print(f"Loaded sentence transformer model: {self.model_name}")
            except Exception as e:
                print(f"Error loading model: {e}")
                raise
    
    def encode_text(self, text):
        """
        Create embeddings for a piece of text.
        
        Args:
            text (str): Text to embed
            
        Returns:
            tensor: The embedding vector
        """
        self._ensure_model_loaded()
        return self.model.encode(text, convert_to_tensor=True)
    
    def encode_batch(self, texts):
        """
        Create embeddings for a list of texts.
        
        Args:
            texts (List[str]): List of texts to embed
            
        Returns:
            tensor: The embedding vectors
        """
        self._ensure_model_loaded()
        return self.model.encode(texts, convert_to_tensor=True)
    
    def similarity_score(self, text1, text2):
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            
        Returns:
            float: Similarity score between 0 and 1
        """
        self._ensure_model_loaded()
        embedding1 = self.model.encode(text1, convert_to_tensor=True)
        embedding2 = self.model.encode(text2, convert_to_tensor=True)
        return util.cos_sim(embedding1, embedding2).item()
    
    def find_most_similar(self, query, corpus):
        """
        Find the most similar items in a corpus to a query.
        
        Args:
            query (str): The query text
            corpus (List[str]): List of texts to search through
            
        Returns:
            List[Tuple[int, float]]: List of (index, score) tuples sorted by score
        """
        self._ensure_model_loaded()
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        corpus_embeddings = self.model.encode(corpus, convert_to_tensor=True)
        
        # Calculate cosine similarities
        cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
        
        # Sort results by score
        results = [(idx, score.item()) for idx, score in enumerate(cos_scores)]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results


# Simple demonstration
if __name__ == "__main__":
    # Only for demonstration purposes
    print("Sentence Transformers utility loaded successfully")
    print("PyTorch version:", torch.__version__)
    print("This module can be imported into your Damien CLI for semantic email processing")
