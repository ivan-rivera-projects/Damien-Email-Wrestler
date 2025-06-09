#!/usr/bin/env python3
"""Test pattern detection algorithms"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "damien_cli"))

def test_pattern_detection():
    """Test pattern detection functionality"""
    
    try:
        from damien_cli.features.ai_intelligence.categorization.patterns import EmailPatternDetector
        
        # Initialize detector
        detector = EmailPatternDetector()
        
        # Create sample email data
        sample_emails = [
            {
                'id': f'email_{i}',
                'subject': f'Newsletter Update #{i}' if i % 3 == 0 else f'Meeting Invitation {i}',
                'from_sender': 'newsletter@company.com' if i % 3 == 0 else f'person{i}@company.com',
                'snippet': f'This is email content {i}',
                'label_names': ['INBOX'],
                'internal_date': str(1640995200000 + i * 86400000)  # Daily increments
            }
            for i in range(10)
        ]
        
        # Create sample embeddings (mock)
        sample_embeddings = [np.random.rand(384) for _ in sample_emails]
        
        print("🎯 Testing pattern detection...")
        
        # Detect patterns
        patterns = detector.detect_patterns(sample_emails, sample_embeddings)
        
        print(f"✅ Pattern detection completed:")
        print(f"   📊 Patterns found: {len(patterns)}")
        
        for i, pattern in enumerate(patterns[:3]):  # Show first 3
            print(f"   🔍 Pattern {i+1}: {pattern.pattern_name}")
            print(f"      📧 Email count: {pattern.email_count}")
            print(f"      🎯 Confidence: {pattern.confidence:.2f}")
            print(f"      📝 Type: {pattern.pattern_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pattern_detection()
    sys.exit(0 if success else 1)
