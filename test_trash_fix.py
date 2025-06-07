#!/usr/bin/env python3
"""Test script to verify the trash functionality fix"""

import subprocess
import json
import time

def test_trash_fix():
    """Test the fixed trash functionality through the MCP server"""
    
    print("🔧 Testing Fixed Trash Functionality")
    print("=" * 50)
    
    # Check if MCP server is running
    print("1️⃣ Checking MCP server status...")
    result = subprocess.run(
        ["curl", "-s", "http://localhost:8892/health"],
        capture_output=True,
        text=True
    )
    
    if "healthy" not in result.stdout:
        print("❌ MCP server not running. Start it with: ./scripts/start-all.sh")
        return False
        
    print("✅ MCP server is healthy")
    
    # Get API key
    with open("damien-mcp-server/.env", "r") as f:
        api_key = None
        for line in f:
            if line.startswith("DAMIEN_MCP_SERVER_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break
    
    if not api_key:
        print("❌ Could not find API key")
        return False
    
    # First, list some emails to get test IDs
    print("\n2️⃣ Getting test emails...")
    list_payload = json.dumps({
        "tool_name": "damien_list_emails",
        "input": {
            "max_results": 2,
            "query": ""
        },
        "session_id": "test-trash-fix"
    })
    
    result = subprocess.run([
        "curl", "-X", "POST", "http://localhost:8892/mcp/execute_tool",
        "-H", "Content-Type: application/json",
        "-H", f"X-API-Key: {api_key}",
        "-d", list_payload
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to list emails: {result.stderr}")
        return False
    
    try:
        response = json.loads(result.stdout)
        if response.get("is_error"):
            print(f"❌ Error listing emails: {response.get('output')}")
            return False
            
        emails = response.get("output", {}).get("email_summaries", [])
        if not emails:
            print("❌ No emails found to test with")
            return False
            
        test_email_id = emails[0]["id"]
        test_subject = emails[0].get("subject", "N/A")[:50]
        print(f"✅ Found test email: {test_email_id}")
        print(f"   Subject: {test_subject}")
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse response: {e}")
        print(f"Response: {result.stdout}")
        return False
    
    # Now test the fixed trash functionality
    print(f"\n3️⃣ Testing trash operation on email {test_email_id}...")
    trash_payload = json.dumps({
        "tool_name": "damien_trash_emails",
        "input": {
            "message_ids": [test_email_id]
        },
        "session_id": "test-trash-fix"
    })
    
    result = subprocess.run([
        "curl", "-X", "POST", "http://localhost:8892/mcp/execute_tool",
        "-H", "Content-Type: application/json",
        "-H", f"X-API-Key: {api_key}",
        "-d", trash_payload
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to call trash tool: {result.stderr}")
        return False
    
    try:
        response = json.loads(result.stdout)
        print(f"📥 Trash Response: {json.dumps(response, indent=2)}")
        
        if response.get("is_error"):
            print(f"❌ Trash operation failed: {response.get('output')}")
            return False
            
        if response.get("output", {}).get("success"):
            print("✅ Trash operation reported success")
        else:
            print("❌ Trash operation reported failure")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse trash response: {e}")
        return False
    
    # Wait a moment for Gmail to process
    print("\n4️⃣ Waiting for Gmail to process...")
    time.sleep(3)
    
    # Verify the email is actually in trash
    print("5️⃣ Verifying email is in trash...")
    verify_payload = json.dumps({
        "tool_name": "damien_list_emails",
        "input": {
            "max_results": 1,
            "query": f"is:trash id:{test_email_id}"
        },
        "session_id": "test-trash-fix"
    })
    
    result = subprocess.run([
        "curl", "-X", "POST", "http://localhost:8892/mcp/execute_tool",
        "-H", "Content-Type: application/json",
        "-H", f"X-API-Key: {api_key}",
        "-d", verify_payload
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            emails_in_trash = response.get("output", {}).get("email_summaries", [])
            
            if emails_in_trash and any(email["id"] == test_email_id for email in emails_in_trash):
                print("🎉 SUCCESS! Email found in trash - fix is working!")
                return True
            else:
                print("❌ FAILURE! Email not found in trash - fix needs more work")
                return False
                
        except json.JSONDecodeError:
            print("❌ Failed to parse verification response")
            return False
    else:
        print(f"❌ Failed to verify trash: {result.stderr}")
        return False

if __name__ == "__main__":
    success = test_trash_fix()
    exit(0 if success else 1)