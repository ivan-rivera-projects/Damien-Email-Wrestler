#!/usr/bin/env python3
"""
Direct Lambda Client Test

This script tests the Lambda client directly to see if it can connect to AWS Lambda functions.
"""

import sys
import json
from pathlib import Path

# Add the MCP server path
sys.path.insert(0, str(Path(__file__).parent / "damien-mcp-server"))

try:
    from app.services.aws_lambda_client import LambdaClient
    
    print("🧪 Testing AWS Lambda Client Direct Connection")
    print("=" * 60)
    print()
    
    # Test 1: Initialize Lambda client
    print("Test 1: 🔧 Lambda Client Initialization")
    print("-" * 40)
    
    try:
        lambda_client = LambdaClient()
        print("✅ Lambda client initialized successfully")
        print(f"   Region: {lambda_client.region_name}")
        print(f"   Functions configured: {list(lambda_client.functions.keys())}")
    except Exception as e:
        print(f"❌ Lambda client initialization failed: {e}")
        sys.exit(1)
    
    print()
    
    # Test 2: Health check
    print("Test 2: 🏥 Lambda Functions Health Check")
    print("-" * 40)
    
    health_results = lambda_client.health_check()
    
    for function_key, status in health_results.items():
        status_icon = "✅" if status["status"] == "healthy" else "❌"
        print(f"{status_icon} {function_key}: {status['status']}")
        if status["status"] == "error":
            print(f"   Error: {status.get('error', 'Unknown error')}")
    
    print()
    
    # Test 3: Simple function call
    print("Test 3: 🚀 Simple Lambda Function Call")
    print("-" * 40)
    
    try:
        # Test email processor with minimal payload
        test_result = lambda_client.call_email_processor(
            user_id="test_user",
            email_data={"id": "test123", "internalDate": "1701234567000"}
        )
        
        if test_result.get("statusCode") == 200:
            print("✅ Email processor function call successful")
            body = test_result.get("body", {})
            if isinstance(body, str):
                body = json.loads(body)
            print(f"   Response: {body.get('success', 'unknown')}")
        else:
            print(f"❌ Email processor function call failed: {test_result}")
    
    except Exception as e:
        print(f"❌ Lambda function call error: {e}")
    
    print()
    
    # Test 4: Check why MCP integration might not be working
    print("Test 4: 🔍 MCP Integration Analysis")
    print("-" * 40)
    
    # Import the AI Intelligence tools to see if Lambda client is properly initialized there
    try:
        from app.tools.ai_intelligence import ai_intelligence_tools
        
        if hasattr(ai_intelligence_tools, 'lambda_client') and ai_intelligence_tools.lambda_client:
            print("✅ AI Intelligence tools have Lambda client initialized")
            print("   This means Lambda enhancement should be available")
        else:
            print("❌ AI Intelligence tools do NOT have Lambda client")
            print("   This explains why Lambda enhancement is not working")
            
            # Check initialization logs
            if hasattr(ai_intelligence_tools, 'lambda_client'):
                if ai_intelligence_tools.lambda_client is None:
                    print("   Lambda client is explicitly set to None")
                    print("   Check MCP server startup logs for initialization errors")
            
    except Exception as e:
        print(f"❌ Cannot import AI Intelligence tools: {e}")
    
    print()
    print("🎯 Summary")
    print("=" * 40)
    print("Direct Lambda client testing completed.")
    print("Check the results above to understand Lambda enhancement status.")

except ImportError as e:
    print(f"❌ Cannot import Lambda client: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)