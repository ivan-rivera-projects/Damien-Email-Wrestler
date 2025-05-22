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
API_KEY = "FiVz_QjpHbfffIktJOip_HKByZhqWTvDlDRv0kFbGKw"
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
    return response.status_code == 200

def test_protected():
    """Test the protected endpoint."""
    url = f"{BASE_URL}/mcp/protected-test"
    response = requests.get(url, headers=HEADERS)
    print(f"Protected endpoint: {response.status_code}")
    print(response.json())
    print()
    return response.status_code == 200

def test_gmail():
    """Test the Gmail connection."""
    url = f"{BASE_URL}/mcp/gmail-test"
    response = requests.get(url, headers=HEADERS)
    print(f"Gmail test endpoint: {response.status_code}")
    print(response.json())
    print()
    return response.status_code == 200

def test_list_emails():
    """Test the list_emails tool."""
    url = f"{BASE_URL}/mcp/execute_tool"
    payload = {
        "tool_name": "damien_list_emails",
        "params": {
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
    return response.status_code == 200

def main():
    """Run all tests."""
    print("=== Damien MCP Server Test ===")
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Run tests
    health_ok = test_health()
    protected_ok = test_protected()
    gmail_ok = test_gmail()
    list_emails_ok = test_list_emails()
    
    # Summary
    print("=== Test Summary ===")
    print(f"Health endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Protected endpoint: {'✅ PASS' if protected_ok else '❌ FAIL'}")
    print(f"Gmail connection: {'✅ PASS' if gmail_ok else '❌ FAIL'}")
    print(f"List emails tool: {'✅ PASS' if list_emails_ok else '❌ FAIL'}")
    
    # Final result
    if all([health_ok, protected_ok, gmail_ok, list_emails_ok]):
        print("\n✅ All tests passed! The server is ready for Claude integration.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the logs and fix the issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
