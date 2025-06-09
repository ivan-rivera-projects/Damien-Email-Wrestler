#!/usr/bin/env python3
"""Test the complete AI analysis pipeline end-to-end"""

import sys
from pathlib import Path
import asyncio
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "damien_cli"))

async def test_complete_analysis_pipeline():
    """Test the full Gmail analysis pipeline"""
    
    try:
        from damien_cli.features.ai_intelligence.categorization.gmail_analyzer import GmailEmailAnalyzer
        from damien_cli.core_api.gmail_api_service import get_authenticated_service
        
        print("🔍 Testing complete AI analysis pipeline...")
        
        # Get Gmail service
        try:
            gmail_service = get_authenticated_service()
            print("✅ Gmail authentication successful")
        except Exception as e:
            print(f"⚠️ Gmail authentication failed: {e}")
            print("ℹ️ Using None service (will test with mock data)")
            gmail_service = None
        
        # Initialize analyzer
        analyzer = GmailEmailAnalyzer(gmail_service=gmail_service)
        print("✅ GmailEmailAnalyzer initialized")
        
        # Test analysis with small dataset
        print("🔄 Running analysis...")
        
        result = await analyzer.analyze_inbox(
            max_emails=10,
            days_back=3,
            min_confidence=0.5
        )
        
        print("✅ Analysis completed successfully!")
        print(f"   📧 Emails analyzed: {result.total_emails_analyzed}")
        print(f"   🎯 Patterns detected: {len(result.patterns_detected)}")
        print(f"   💡 Suggestions created: {len(result.category_suggestions)}")
        
        # Test business impact calculation
        if result.category_suggestions:
            business_impact = result.calculate_business_impact()
            print(f"   💰 Business impact calculated:")
            print(f"      📈 Automation rate: {business_impact['automation_rate_percent']:.1f}%")
            print(f"      ⏰ Time savings: {business_impact['time_savings_hours']:.1f} hours")
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the end-to-end test"""
    return asyncio.run(test_complete_analysis_pipeline())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
