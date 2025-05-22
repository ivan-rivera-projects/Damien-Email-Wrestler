#!/usr/bin/env python
"""
Simple Python script to tunnel localhost:8892 using pyngrok.
This bypasses the need to install ngrok directly.
"""

import os
import sys
import subprocess

try:
    from pyngrok import ngrok
except ImportError:
    # Install pyngrok if needed
    print("Installing pyngrok...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok"])
    from pyngrok import ngrok

# Get auth token from env or prompt user
auth_token = os.environ.get("NGROK_AUTH_TOKEN")
if not auth_token:
    auth_token = input("Enter your ngrok auth token (create one at https://dashboard.ngrok.com): ")
    if auth_token.strip():
        ngrok.set_auth_token(auth_token.strip())

# Open tunnel to port 8892
port = 8892
print(f"Opening tunnel to localhost:{port}...")
public_url = ngrok.connect(port).public_url
print(f"Damien MCP Server is now accessible at: {public_url}")
print(f"Claude should use: {public_url}/mcp/execute_tool as the endpoint URL")
print(f"API Key: FiVz_QjpHbfffIktJOip_HKByZhqWTvDlDRv0kFbGKw")
print("\nPress Ctrl+C to stop")

# Keep the tunnel open
try:
    ngrok_process = ngrok.get_ngrok_process()
    ngrok_process.proc.wait()
except KeyboardInterrupt:
    print("Shutting down tunnel...")
    ngrok.kill()
