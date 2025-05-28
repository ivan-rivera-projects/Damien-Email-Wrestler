
# Minimal test to verify torch and sentence-transformers work
print("Testing torch and sentence-transformers imports...")

import torch
print(f"PyTorch version: {torch.__version__}")

import sentence_transformers
print(f"Sentence-Transformers version: {sentence_transformers.__version__}")

print("Success! Both libraries imported correctly.")
