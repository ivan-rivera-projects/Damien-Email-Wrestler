#!/usr/bin/env python3

"""
Quick test script to verify thread tools functionality
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-mcp-server')

from app.tools.thread_tools import list_threads_handler, get_thread_details_handler, ListThreadsParams, GetThreadDetailsParams

async def test_thread_functionality():
    """Test the thread tools directly"""
    
    print("🧪 Testing Thread Tools Functionality")
    print("=" * 50)
    
    # Test 1: List threads with the Burbs query
    print("\n📋 Test 1: List threads for 'Burbs' subject")
    try:
        params = ListThreadsParams(query='subject:Burbs', max_results=5)
        context = {'user_id': 'test', 'session_id': 'test', 'tool_name': 'damien_list_threads'}
        result = await list_threads_handler(params, context)
        
        if result.get('success'):
            threads = result.get('threads', [])
            print(f"✅ SUCCESS: Found {len(threads)} threads")
            for i, thread in enumerate(threads[:3]):  # Show first 3
                print(f"   Thread {i+1}: {thread.get('id')}")
        else:
            print(f"❌ FAILED: {result.get('error_message')}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Get details for the main thread
    print(f"\n🔍 Test 2: Get details for main thread")
    try:
        thread_id = "194bd65e470d1f51"  # Main thread ID from the search
        params = GetThreadDetailsParams(thread_id=thread_id, format="metadata")
        context = {'user_id': 'test', 'session_id': 'test', 'tool_name': 'damien_get_thread_details'}
        result = await get_thread_details_handler(params, context)
        
        if result.get('success'):
            thread = result.get('thread', {})
            message_count = result.get('message_count', 0)
            print(f"✅ SUCCESS: Thread has {message_count} messages")
            print(f"   Thread ID: {thread.get('id')}")
            if 'messages' in thread:
                print(f"   Messages: {len(thread['messages'])} found")
        else:
            print(f"❌ FAILED: {result.get('error_message')}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Thread Tools Test Complete")

if __name__ == "__main__":
    asyncio.run(test_thread_functionality())
