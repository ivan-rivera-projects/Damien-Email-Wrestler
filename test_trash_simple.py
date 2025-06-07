#!/usr/bin/env python3
"""Simple test to debug trash functionality using Damien's existing infrastructure"""

import subprocess
import json
import time

def test_trash_with_damien():
    """Test trash functionality through Damien CLI"""
    
    print("🔍 Testing Trash Functionality Through Damien")
    print("=" * 50)
    
    # First, list some recent emails to get IDs
    print("\n1️⃣ Getting recent emails...")
    result = subprocess.run(
        ["python3", "-m", "damien_cli.cli_entry", "emails", "list", "--max-results", "5", "--format", "json"],
        cwd="damien-cli",
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to list emails: {result.stderr}")
        return
        
    try:
        emails = json.loads(result.stdout)
        if not emails or not emails.get('messages'):
            print("❌ No emails found")
            return
            
        # Get the first email ID
        test_email_id = emails['messages'][0]['id']
        print(f"✓ Found test email ID: {test_email_id}")
        print(f"  Subject: {emails['messages'][0].get('subject', 'N/A')}")
        
    except json.JSONDecodeError:
        print(f"❌ Failed to parse email list output: {result.stdout}")
        return
        
    # Now test trashing through MCP server
    print("\n2️⃣ Testing trash through MCP server...")
    
    # First, check if MCP server is running
    mcp_test = subprocess.run(
        ["curl", "-s", "http://localhost:8892/health"],
        capture_output=True,
        text=True
    )
    
    if "healthy" not in mcp_test.stdout:
        print("❌ MCP server not running. Start it with: ./scripts/start-all.sh")
        return
        
    # Call the trash endpoint
    trash_payload = json.dumps({
        "tool": "damien_trash_emails",
        "arguments": {
            "message_ids": [test_email_id]
        }
    })
    
    print(f"📤 Sending trash request for email ID: {test_email_id}")
    
    result = subprocess.run(
        ["curl", "-X", "POST", "http://localhost:8892/tools/call",
         "-H", "Content-Type: application/json",
         "-d", trash_payload],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to call trash tool: {result.stderr}")
        return
        
    try:
        response = json.loads(result.stdout)
        print(f"📥 Response: {json.dumps(response, indent=2)}")
        
        # Check if it reports success
        if response.get('result', {}).get('success'):
            print("✓ Trash operation reported success")
        else:
            print("❌ Trash operation reported failure")
            
    except json.JSONDecodeError:
        print(f"❌ Failed to parse response: {result.stdout}")
        
    # Now verify if email is actually in trash
    print("\n3️⃣ Verifying email is actually in trash...")
    time.sleep(2)  # Give Gmail a moment to process
    
    # Search for the email in trash
    result = subprocess.run(
        ["python3", "-m", "damien_cli.cli_entry", "emails", "list", "--query", f"is:trash {test_email_id}", "--format", "json"],
        cwd="damien-cli",
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        try:
            trash_emails = json.loads(result.stdout)
            if trash_emails.get('messages'):
                found_in_trash = any(msg['id'] == test_email_id for msg in trash_emails['messages'])
                if found_in_trash:
                    print("✅ Email FOUND in trash - operation successful!")
                else:
                    print("❌ Email NOT found in trash - operation failed!")
            else:
                print("❌ No emails found in trash - operation likely failed!")
        except json.JSONDecodeError:
            print(f"❌ Failed to parse trash search output: {result.stdout}")
    else:
        print(f"❌ Failed to search trash: {result.stderr}")
        
    # Also check if it's still in inbox
    print("\n4️⃣ Checking if email is still in inbox...")
    result = subprocess.run(
        ["python3", "-m", "damien_cli.cli_entry", "emails", "list", "--query", f"is:inbox {test_email_id}", "--format", "json"],
        cwd="damien-cli",
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        try:
            inbox_emails = json.loads(result.stdout)
            if inbox_emails.get('messages'):
                found_in_inbox = any(msg['id'] == test_email_id for msg in inbox_emails['messages'])
                if found_in_inbox:
                    print("❌ Email STILL in inbox - trash operation definitely failed!")
                else:
                    print("✓ Email NOT in inbox anymore")
            else:
                print("✓ Email not found in inbox (good)")
        except json.JSONDecodeError:
            print(f"❌ Failed to parse inbox search output: {result.stdout}")

if __name__ == "__main__":
    test_trash_with_damien()