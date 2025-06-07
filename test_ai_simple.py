#!/usr/bin/env python3
"""Simple test of AI analysis to see actual output"""

import subprocess
import json

def call_ai_tool(query="from:news@notice.alibaba.com", max_results=5):
    """Test AI analysis and show actual output"""
    api_key = "7e508adf3ccf8b9376c312df8cebd488f3988f310afbdf5077d5d3ce63ed7c8f"
    
    result = subprocess.run([
        "curl", "-s", "-X", "POST", "http://localhost:8892/mcp/execute_tool",
        "-H", "Content-Type: application/json",
        "-H", f"X-API-Key: {api_key}",
        "-d", json.dumps({
            "tool_name": "damien_ai_analyze_emails",
            "input": {
                "query": query,
                "max_results": max_results,
                "analysis_type": "comprehensive"
            },
            "session_id": "ai_debug"
        })
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ cURL failed: {result.stderr}")
        return
    
    try:
        response = json.loads(result.stdout)
        print("🤖 AI Analysis Response:")
        print("=" * 50)
        print(json.dumps(response, indent=2))
        
        if response.get("is_error"):
            print(f"\n❌ Error: {response.get('output')}")
        else:
            output = response.get("output", {})
            print(f"\n📊 Analysis Summary:")
            print(f"   Status: {'Success' if not response.get('is_error') else 'Error'}")
            print(f"   Patterns found: {len(output.get('patterns', []))}")
            print(f"   Email count: {output.get('email_count', 0)}")
            print(f"   Analysis type: {output.get('analysis_type', 'Unknown')}")
            
            patterns = output.get("patterns", [])
            if patterns:
                print(f"\n🔍 Patterns:")
                for i, pattern in enumerate(patterns):
                    print(f"   {i+1}. {pattern}")
            
            actions = output.get("suggested_actions", [])
            if actions:
                print(f"\n💡 Suggested Actions:")
                for i, action in enumerate(actions):
                    print(f"   {i+1}. {action}")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {result.stdout}")

if __name__ == "__main__":
    print("🔍 Testing AI Analysis Output")
    call_ai_tool()