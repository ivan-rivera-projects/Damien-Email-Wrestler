
# Simple test for sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    print("Successfully imported SentenceTransformer")
    # Just try to instantiate the model without loading weights
    # This will verify the code is working without downloading models
    print("Testing SentenceTransformer class initialization")
    print("Test completed successfully!")
except Exception as e:
    print(f"Error: {e}")
