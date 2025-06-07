#!/usr/bin/env python3
"""Test MCP server the same way Claude Desktop does"""

import subprocess
import json

def test_mcp_parity():
    """Test MCP server exactly like Claude Desktop"""
    
    api_key = "7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
    
    # Test exactly like Claude Desktop did
    print("🔍 Testing MCP server exactly like Claude Desktop")
    print("=" * 60)
    
    result = subprocess.run([
        "curl", "-s", "-X", "POST", "http://localhost:8892/mcp/execute_tool",
        "-H", "Content-Type: application/json",
        "-H", f"X-API-Key: {api_key}",
        "-d", json.dumps({
            "tool_name": "damien_list_emails",
            "input": {
                "query": "from:news@notice.alibaba.com",
                "max_results": "5",
                "include_headers": ["Subject", "Date", "From"]
            },
            "session_id": "claude_max_session"
        })
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed: {result.stderr}")
        return
    
    try:
        data = json.loads(result.stdout)
        emails = data.get('output', {}).get('email_summaries', [])
        
        print('✅ Response structure:')
        print(f'   is_error: {data.get("is_error")}')
        print(f'   Number of emails: {len(emails)}')
        print()
        
        for i, email in enumerate(emails):
            print(f'📧 Email {i+1}:')
            print(f'   ID: {email["id"]}')
            print(f'   Subject: {email.get("Subject", "N/A")}')
            print(f'   From: {email.get("From", "N/A")}')
            print(f'   Date: {email.get("Date", "N/A")}')
            print()
            
        # Check if we got the "Beat the heat" email
        target_email = None
        for email in emails:
            if "Beat the heat" in email.get("Subject", ""):
                target_email = email
                break
                
        if target_email:
            print(f"🎯 Found target email:")
            print(f"   Subject: {target_email.get('Subject')}")
            print(f"   From: {target_email.get('From')}")
            print(f"   Date: {target_email.get('Date')}")
            print(f"   ID: {target_email['id']}")
            return target_email['id']
        else:
            print("❌ Target email 'Beat the heat' not found")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {result.stdout}")

if __name__ == "__main__":
    email_id = test_mcp_parity()
    if email_id:
        print(f"\n🚀 Ready to test trash functionality with email ID: {email_id}")