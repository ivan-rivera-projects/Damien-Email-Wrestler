#!/usr/bin/env python3
"""Simple test to verify the trash functionality fix"""

import subprocess
import json
import time

def test_trash_fix():
    """Test the fixed trash functionality"""
    
    print("🔧 Testing Fixed Trash Functionality")
    print("=" * 50)
    
    api_key = "7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
    
    # Get a test email
    print("1️⃣ Getting test email...")
    result = subprocess.run([
        "curl", "-s", "-X", "POST", "http://localhost:8892/mcp/execute_tool",
        "-H", "Content-Type: application/json",
        "-H", f"X-API-Key: {api_key}",
        "-d", json.dumps({
            "tool_name": "damien_list_emails",
            "input": {"max_results": 1},
            "session_id": "test-trash"
        })
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to list emails: {result.stderr}")
        return False
    
    try:
        response = json.loads(result.stdout)
        emails = response.get("output", {}).get("email_summaries", [])
        if not emails:
            print("❌ No emails found")
            return False
        
        test_email_id = emails[0]["id"]
        print(f"✅ Found test email: {test_email_id}")
        
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        return False
    
    # Test trash operation
    print(f"2️⃣ Trashing email {test_email_id}...")
    result = subprocess.run([
        "curl", "-s", "-X", "POST", "http://localhost:8892/mcp/execute_tool",
        "-H", "Content-Type: application/json",
        "-H", f"X-API-Key: {api_key}",
        "-d", json.dumps({
            "tool_name": "damien_trash_emails",
            "input": {"message_ids": [test_email_id]},
            "session_id": "test-trash"
        })
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to trash email: {result.stderr}")
        return False
    
    try:
        response = json.loads(result.stdout)
        if response.get("is_error"):
            print(f"❌ Trash operation failed: {response.get('output')}")
            return False
        
        trashed_count = response.get("output", {}).get("trashed_count", 0)
        if not response.get("is_error", True) and trashed_count > 0:
            print(f"✅ Trash operation reported success (trashed {trashed_count} emails)")
        else:
            print("❌ Trash operation reported failure")
            return False
            
    except Exception as e:
        print(f"❌ Error parsing trash response: {e}")
        return False
    
    # Verify in trash
    print("3️⃣ Verifying email is in trash...")
    time.sleep(2)
    
    result = subprocess.run([
        "curl", "-s", "-X", "POST", "http://localhost:8892/mcp/execute_tool",
        "-H", "Content-Type: application/json",
        "-H", f"X-API-Key: {api_key}",
        "-d", json.dumps({
            "tool_name": "damien_list_emails",
            "input": {"query": f"is:trash id:{test_email_id}", "max_results": 1},
            "session_id": "test-trash"
        })
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to verify trash: {result.stderr}")
        return False
    
    try:
        response = json.loads(result.stdout)
        trash_emails = response.get("output", {}).get("email_summaries", [])
        
        if trash_emails and any(email["id"] == test_email_id for email in trash_emails):
            print("🎉 SUCCESS! Email found in trash - fix is working!")
            return True
        else:
            print("❌ FAILURE! Email not found in trash")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying trash: {e}")
        return False

if __name__ == "__main__":
    success = test_trash_fix()
    exit(0 if success else 1)