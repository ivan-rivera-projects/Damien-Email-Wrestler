
# Test script for embedding manager
from damien_cli.embeddings import EmbeddingManager

def test_embedding_manager():
    print("Testing EmbeddingManager...")
    
    # Initialize without loading model
    manager = EmbeddingManager()
    print(f"Initialized EmbeddingManager with model: {manager.model_name}")
    
    # No need to load the actual model for this test
    print("EmbeddingManager successfully imported and initialized!")

if __name__ == "__main__":
    test_embedding_manager()
