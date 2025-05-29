#!/usr/bin/env python3
"""
Test pattern creation to isolate recursion issue
"""

import sys
sys.path.append('.')

from damien_cli.features.ai_intelligence.models import (
    EmailPattern, PatternCharacteristics, PatternType, ConfidenceLevel
)

def test_pattern_creation():
    """Test creating an EmailPattern to isolate the recursion issue"""
    
    try:
        print("Creating PatternCharacteristics...")
        characteristics = PatternCharacteristics(
            primary_feature="test@example.com",
            secondary_features=["test", "email"],
            statistical_measures={
                'email_count': 5,
                'attachment_rate': 0.2,
                'prevalence': 0.1
            },
            sender_domain="example.com",
            sender_type="Regular Sender",
            common_keywords=["test", "email"]
        )
        print("✅ PatternCharacteristics created successfully")
        
        print("Creating EmailPattern...")
        pattern = EmailPattern(
            pattern_type=PatternType.SENDER,
            pattern_name="Test Pattern",
            description="Test pattern for debugging",
            email_count=5,
            total_email_universe=50,
            prevalence_rate=0.1,
            confidence=0.8,
            characteristics=characteristics,
            example_email_ids=["id1", "id2", "id3"]
        )
        print("✅ EmailPattern created successfully")
        print(f"Pattern confidence level: {pattern.confidence_level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating pattern: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing pattern creation...")
    success = test_pattern_creation()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
