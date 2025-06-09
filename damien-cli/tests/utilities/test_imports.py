
# Simple test script to verify imports
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
except Exception as e:
    print(f"Error importing torch: {e}")

try:
    import sentence_transformers
    print(f"Sentence-Transformers version: {sentence_transformers.__version__}")
except Exception as e:
    print(f"Error importing sentence_transformers: {e}")

print("Import test completed!")
