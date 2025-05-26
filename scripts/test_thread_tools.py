#!/usr/bin/env python3
"""
Test script to verify thread tools API integration
"""

import requests
import json
import sys

# API endpoint
API_BASE_URL = "http://localhost:8895/mcp"
API_KEY = "7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"  # Replace with your API key

def test_list_tools():
    """Test to verify thread tools are listed in available tools"""
    url = f"{API_BASE_URL}/list_tools"
    headers = {"X-API-Key": API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: Failed to list tools. Status code: {response.status_code}")
        print(response.text)
        return False
    
    tools = response.json()
    thread_tools_count = 0
    thread_tool_names = []
    
    for tool in tools:
        if tool["name"].startswith("damien_thread") or tool["name"] in ["damien_list_threads", "damien_get_thread_details"]:
            thread_tools_count += 1
            thread_tool_names.append(tool["name"])
    
    print(f"Found {thread_tools_count} thread tools: {', '.join(thread_tool_names)}")
    return thread_tools_count > 0

def test_list_threads():
    """Test to execute the list_threads tool"""
    url = f"{API_BASE_URL}/execute_tool"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    data = {
        "tool_name": "damien_list_threads",
        "input": {
            "max_results": 3
        },
        "session_id": "test_session_123"
    }
    
    print(f"Sending request to {url} with data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Response status code: {response.status_code}")
    
    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200 and not result.get("is_error", False)
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.text}")
        return False

def main():
    print("Testing thread tools integration...")
    
    # Test if thread tools are listed
    print("\n1. Testing if thread tools are listed in available tools...")
    if not test_list_tools():
        print("❌ Thread tools not found in available tools list")
        return 1
    print("✅ Thread tools found in available tools list")
    
    # Test executing list_threads
    print("\n2. Testing execution of damien_list_threads tool...")
    if not test_list_threads():
        print("❌ Failed to execute damien_list_threads")
        return 1
    print("✅ Successfully executed damien_list_threads")
    
    print("\nAll tests passed! Thread tools are properly integrated.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
