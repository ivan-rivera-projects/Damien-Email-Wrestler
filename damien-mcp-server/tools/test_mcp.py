#!/usr/bin/env python
"""
Test script for the Damien MCP Server.
This script makes a simple request to the MCP endpoint to list emails.
"""

import json
import sys
import uuid
import requests

# Configuration
BASE_URL = "http://localhost:8892"  # Change this to your ngrok URL if testing remotely
API_KEY = "7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_health():
    """Test the health endpoint."""
    url = f"{BASE_URL}/health"
    response = requests.get(url)
    print(f"Health endpoint: {response.status_code}")
    print(response.json())
    print()
    assert response.status_code == 200

def test_gmail():
    """Test the Gmail connection."""
    url = f"{BASE_URL}/mcp/gmail-test"
    response = requests.get(url, headers=HEADERS)
    print(f"Gmail test endpoint: {response.status_code}")
    print(response.json())
    print()
    assert response.status_code == 200

def test_list_emails():
    """Test the list_emails tool."""
    url = f"{BASE_URL}/mcp/execute_tool"
    payload = {
        "tool_name": "damien_list_emails",
        "input": {
            "query": "is:unread",
            "max_results": 3
        },
        "session_id": str(uuid.uuid4())
    }
    
    print(f"Testing list_emails with payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    response = requests.post(url, headers=HEADERS, json=payload)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Tool result ID: {result.get('tool_result_id')}")
        print(f"Is error: {result.get('is_error')}")
        if result.get('is_error'):
            print(f"Error: {result.get('error')}")
        else:
            # Just show summary of the output
            output = result.get('output', {})
            email_summaries = output.get('email_summaries', [])
            print(f"Retrieved {len(email_summaries)} emails")
            for i, email in enumerate(email_summaries, 1):
                print(f"  Email {i}: ID={email.get('id')} Subject={email.get('subject', 'N/A')}")
            print(f"Next page token: {output.get('next_page_token')}")
    else:
        print(f"Error: {response.text}")
    
    print()
    assert response.status_code == 200

def main():
    """Run all tests."""
    print("=== Damien MCP Server Test ===")
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Run tests with try/except to catch assertion errors
    tests_passed = 0
    total_tests = 3
    
    try:
        test_health()
        print("Health endpoint: ✅ PASS")
        tests_passed += 1
    except AssertionError:
        print("Health endpoint: ❌ FAIL")
    
    try:
        test_gmail()
        print("Gmail connection: ✅ PASS")
        tests_passed += 1
    except AssertionError:
        print("Gmail connection: ❌ FAIL")
    
    try:
        test_list_emails()
        print("List emails tool: ✅ PASS")
        tests_passed += 1
    except AssertionError:
        print("List emails tool: ❌ FAIL")
    
    # Summary
    print(f"\n=== Test Summary: {tests_passed}/{total_tests} passed ===")
    
    # Final result
    if tests_passed == total_tests:
        print("\n✅ All tests passed! The server is ready for Claude integration.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the logs and fix the issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
