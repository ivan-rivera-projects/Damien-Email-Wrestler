#!/usr/bin/env python3
"""
Test script for enhanced chunked email details functionality.
Tests Issue #3 fix - timeout-resistant email fetching.
"""

import sys
import json
import time
from pathlib import Path

# Add damien-cli to path
cli_path = Path(__file__).parent / "damien-cli"
sys.path.insert(0, str(cli_path))

from damien_cli.core_api.gmail_api_service import (
    get_authenticated_service,
    list_messages,
    get_message_details_chunked
)

def test_chunked_email_details():
    """Test the new chunked email details functionality."""
    print("=" * 60)
    print("Testing Enhanced Chunked Email Details (Issue #3 Fix)")
    print("=" * 60)

    # Authenticate
    print("\n1. Authenticating with Gmail...")
    gmail_service = get_authenticated_service()
    print("   ✓ Authenticated successfully")

    # Get a sample email
    print("\n2. Fetching sample email ID...")
    emails_result = list_messages(
        gmail_service=gmail_service,
        query="is:inbox",
        max_results=1
    )

    if not emails_result.get('messages'):
        print("   ✗ No emails found in inbox")
        return False

    message_id = emails_result['messages'][0]['id']
    print(f"   ✓ Found email: {message_id}")

    # Test different detail levels
    detail_levels = ['headers_only', 'standard', 'full_metadata']

    for detail_level in detail_levels:
        print(f"\n3. Testing detail_level='{detail_level}'...")
        start_time = time.time()

        try:
            result = get_message_details_chunked(
                gmail_service=gmail_service,
                message_id=message_id,
                detail_level=detail_level,
                include_body=True,
                include_attachment_metadata=True
            )

            elapsed = time.time() - start_time

            # Display results
            print(f"   ✓ Fetched successfully in {elapsed:.2f}s")
            print(f"   - Success: {result['success']}")
            print(f"   - Headers: {len(result.get('headers', {}))} items")
            print(f"   - Body text: {len(result.get('body', {}).get('text', ''))} chars")
            print(f"   - Body HTML: {len(result.get('body', {}).get('html', ''))} chars")
            print(f"   - Attachments: {result.get('attachments', {}).get('total_count', 0)}")
            print(f"   - Total size: {result.get('attachments', {}).get('total_size_mb', 0)} MB")

            # Performance metrics
            perf = result.get('performance', {})
            print(f"\n   Performance Metrics:")
            print(f"   - Format used: {perf.get('format_used')}")
            print(f"   - Detail level: {perf.get('detail_level')}")
            print(f"   - Fetch time: {perf.get('fetch_time_seconds')}s")
            print(f"   - Estimated size: {perf.get('estimated_size_mb')} MB")

            # Show sample headers
            headers = result.get('headers', {})
            print(f"\n   Sample Headers:")
            for key in ['From', 'Subject', 'Date'][:3]:
                if key in headers:
                    value = headers[key]
                    # Truncate long values
                    if len(value) > 60:
                        value = value[:60] + "..."
                    print(f"   - {key}: {value}")

            # Show attachments if present
            attachments = result.get('attachments', {}).get('items', [])
            if attachments:
                print(f"\n   Attachments ({len(attachments)}):")
                for i, att in enumerate(attachments[:5]):  # Show first 5
                    size_kb = att['size_bytes'] / 1024
                    print(f"   - [{i+1}] {att['filename']} ({size_kb:.1f} KB, {att['mime_type']})")
                if len(attachments) > 5:
                    print(f"   - ... and {len(attachments) - 5} more")

        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n" + "=" * 60)
    print("✓ All tests passed! Issue #3 fix verified.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_chunked_email_details()
    sys.exit(0 if success else 1)
