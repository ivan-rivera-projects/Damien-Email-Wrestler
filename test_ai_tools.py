#!/usr/bin/env python3
"""
Test script for all 8 AI Intelligence tools in the Damien platform.
Tests each tool with real functionality to ensure 100% operational status.
"""

import requests
import json
import time
import sys

# Configuration
API_KEY = "7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
BASE_URL = "http://localhost:8892"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_tool(tool_name, params):
    """Test a single tool and return results."""
    print(f"\n{'='*60}")
    print(f"Testing: {tool_name}")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/mcp/tools/{tool_name}"
    
    try:
        print(f"Parameters: {json.dumps(params, indent=2)}")
        response = requests.post(url, headers=HEADERS, json=params)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS - Status Code: {response.status_code}")
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")  # First 500 chars
            return True, result
        else:
            print(f"❌ FAILED - Status Code: {response.status_code}")
            print(f"Error: {response.text[:500]}")
            return False, response.text
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False, str(e)

def main():
    """Test all 8 AI tools."""
    print("🚀 Damien AI Intelligence Tools Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test 1: damien_ai_quick_test - Quick validation
    print("\n1️⃣ Testing Quick Test (Health Check)")
    success, result = test_tool("damien_ai_quick_test", {
        "sample_size": 10,
        "days": 7,
        "include_performance": True,
        "validate_components": True
    })
    results["damien_ai_quick_test"] = success
    
    # Test 2: damien_ai_analyze_emails - Email analysis
    print("\n2️⃣ Testing Email Analysis")
    success, result = test_tool("damien_ai_analyze_emails", {
        "days": 7,
        "max_emails": 50,
        "min_confidence": 0.7,
        "output_format": "summary"
    })
    results["damien_ai_analyze_emails"] = success
    
    # Test 3: damien_ai_suggest_rules - Rule suggestions
    print("\n3️⃣ Testing Rule Suggestions")
    success, result = test_tool("damien_ai_suggest_rules", {
        "limit": 3,
        "min_confidence": 0.8,
        "include_business_impact": True,
        "auto_validate": True
    })
    results["damien_ai_suggest_rules"] = success
    
    # Test 4: damien_ai_create_rule - Natural language rule creation
    print("\n4️⃣ Testing Natural Language Rule Creation")
    success, result = test_tool("damien_ai_create_rule", {
        "rule_description": "Archive all newsletters and marketing emails older than 7 days",
        "validate_before_create": True,
        "dry_run": True,
        "confidence_threshold": 0.8
    })
    results["damien_ai_create_rule"] = success
    
    # Test 5: damien_ai_get_insights - Email insights
    print("\n5️⃣ Testing Email Insights")
    success, result = test_tool("damien_ai_get_insights", {
        "insight_type": "summary",
        "time_range": 30,
        "include_predictions": False,
        "format": "text"
    })
    results["damien_ai_get_insights"] = success
    
    # Test 6: damien_ai_optimize_inbox - Inbox optimization
    print("\n6️⃣ Testing Inbox Optimization")
    success, result = test_tool("damien_ai_optimize_inbox", {
        "optimization_type": "all",
        "aggressiveness": "moderate",
        "dry_run": True,
        "max_actions": 50
    })
    results["damien_ai_optimize_inbox"] = success
    
    # Test 7: damien_ai_analyze_emails_large_scale - Large scale analysis
    print("\n7️⃣ Testing Large Scale Analysis")
    success, result = test_tool("damien_ai_analyze_emails_large_scale", {
        "target_count": 100,
        "days": 14,
        "min_confidence": 0.75,
        "use_statistical_validation": True
    })
    results["damien_ai_analyze_emails_large_scale"] = success
    
    # Test 8: damien_ai_analyze_emails_async - Async analysis
    print("\n8️⃣ Testing Async Email Analysis")
    success, result = test_tool("damien_ai_analyze_emails_async", {
        "days": 7,
        "max_emails": 50
    })
    results["damien_ai_analyze_emails_async"] = success
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for tool, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {tool}")
    
    print(f"\nTotal: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! AI Intelligence at 100% 🎉")
        return 0
    else:
        print(f"\n❌ {failed} tests failed. Target: 100% operational status")
        return 1

if __name__ == "__main__":
    sys.exit(main())