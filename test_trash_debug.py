#!/usr/bin/env python3
"""Debug script to test Gmail trash functionality and identify the issue"""

import os
import sys
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add the damien-cli directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'damien-cli'))

def test_trash_methods():
    """Test different methods of trashing emails to identify which works"""
    
    # Load credentials
    token_path = os.path.expanduser('~/.config/damien-cli/token.json')
    if not os.path.exists(token_path):
        print(f"❌ Token file not found at {token_path}")
        return
        
    creds = Credentials.from_authorized_user_file(token_path)
    service = build('gmail', 'v1', credentials=creds)
    
    # First, get a test email (most recent one)
    try:
        results = service.users().messages().list(
            userId='me',
            maxResults=1,
            q='is:unread'
        ).execute()
        
        if not results.get('messages'):
            print("❌ No unread messages found to test with")
            return
            
        test_message_id = results['messages'][0]['id']
        print(f"✓ Found test message ID: {test_message_id}")
        
        # Get message details before trashing
        msg = service.users().messages().get(userId='me', id=test_message_id).execute()
        print(f"✓ Message snippet: {msg.get('snippet', '')[:50]}...")
        print(f"✓ Current labels: {msg.get('labelIds', [])}")
        
    except HttpError as e:
        print(f"❌ Error getting test message: {e}")
        return
        
    # Method 1: Using batchModify with TRASH label (current implementation)
    print("\n🔧 Testing Method 1: batchModify with TRASH label")
    try:
        result = service.users().messages().batchModify(
            userId='me',
            body={
                'ids': [test_message_id],
                'addLabelIds': ['TRASH']
            }
        ).execute()
        print(f"✓ batchModify returned: {result}")
        
        # Check if message is actually in trash
        msg = service.users().messages().get(userId='me', id=test_message_id).execute()
        labels = msg.get('labelIds', [])
        print(f"✓ Labels after batchModify: {labels}")
        
        if 'TRASH' in labels:
            print("✅ Message successfully moved to trash with Method 1")
            # Move it back out of trash for next test
            service.users().messages().modify(
                userId='me',
                id=test_message_id,
                body={'removeLabelIds': ['TRASH']}
            ).execute()
        else:
            print("❌ TRASH label not found - Method 1 failed")
            
    except HttpError as e:
        print(f"❌ Method 1 error: {e}")
        
    # Method 2: Using individual message trash() method
    print("\n🔧 Testing Method 2: Individual message trash()")
    try:
        result = service.users().messages().trash(
            userId='me',
            id=test_message_id
        ).execute()
        print(f"✓ trash() returned: {result}")
        
        # Verify it's in trash
        labels = result.get('labelIds', [])
        print(f"✓ Labels after trash(): {labels}")
        
        if 'TRASH' in labels:
            print("✅ Message successfully moved to trash with Method 2")
            # Untrash for next test
            service.users().messages().untrash(userId='me', id=test_message_id).execute()
        else:
            print("❌ TRASH label not found - Method 2 failed")
            
    except HttpError as e:
        print(f"❌ Method 2 error: {e}")
        
    # Method 3: Using batchModify with both add TRASH and remove INBOX
    print("\n🔧 Testing Method 3: batchModify with TRASH + remove INBOX/UNREAD")
    try:
        result = service.users().messages().batchModify(
            userId='me',
            body={
                'ids': [test_message_id],
                'addLabelIds': ['TRASH'],
                'removeLabelIds': ['INBOX', 'UNREAD']
            }
        ).execute()
        print(f"✓ batchModify returned: {result}")
        
        # Check labels
        msg = service.users().messages().get(userId='me', id=test_message_id).execute()
        labels = msg.get('labelIds', [])
        print(f"✓ Labels after batchModify: {labels}")
        
        if 'TRASH' in labels and 'INBOX' not in labels:
            print("✅ Message successfully moved to trash with Method 3")
        else:
            print("❌ Method 3 failed - labels incorrect")
            
    except HttpError as e:
        print(f"❌ Method 3 error: {e}")
        
    # Check API quotas and permissions
    print("\n🔍 Checking API permissions")
    try:
        # List all available labels to verify permissions
        labels = service.users().labels().list(userId='me').execute()
        system_labels = [l for l in labels.get('labels', []) if l.get('type') == 'system']
        trash_label = next((l for l in system_labels if l['id'] == 'TRASH'), None)
        
        if trash_label:
            print(f"✅ TRASH label found: {trash_label}")
        else:
            print("❌ TRASH label not found in system labels")
            
    except HttpError as e:
        print(f"❌ Error checking labels: {e}")

if __name__ == "__main__":
    print("🔍 Gmail Trash Functionality Debug Test")
    print("=" * 50)
    test_trash_methods()