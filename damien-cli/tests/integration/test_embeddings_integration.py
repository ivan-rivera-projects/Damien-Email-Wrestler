#!/usr/bin/env python3
"""Test embeddings system with real and mock data"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "damien_cli"))

def test_embeddings():
    """Test embedding generation"""
    
    try:
        from damien_cli.features.ai_intelligence.categorization.embeddings import EmailEmbeddingGenerator
        
        # Initialize generator
        generator = EmailEmbeddingGenerator()
        
        # Test email data
        email_data = {
            'id': 'test_email_123',
            'subject': 'Test Email Subject for Embedding',
            'snippet': 'This is a test email snippet that should generate meaningful embeddings for pattern detection',
            'from_sender': 'test@example.com',
            'label_names': ['INBOX'],
            'internal_date': '1640995200000'  # Unix timestamp
        }
        
        print("🧮 Testing embedding generation...")
        
        # Generate single embedding
        embedding = generator.generate_embedding(email_data)
        
        print(f"✅ Single embedding generated:")
        print(f"   📏 Shape: {embedding.shape}")
        print(f"   📊 Type: {type(embedding)}")
        print(f"   🔢 Dimension: {len(embedding)}")
        
        # Test batch generation
        email_batch = [email_data, email_data.copy(), email_data.copy()]
        batch_embeddings = generator.generate_batch_embeddings(email_batch)
        
        print(f"✅ Batch embeddings generated:")
        print(f"   📏 Shape: {np.array(batch_embeddings).shape}")
        print(f"   📊 Count: {len(batch_embeddings)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_embeddings()
    sys.exit(0 if success else 1)
