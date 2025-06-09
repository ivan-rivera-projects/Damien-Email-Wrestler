#!/usr/bin/env python3
"""
Safe Write Operations Test Suite for Damien Email Wrestler
Tests modification operations with minimal, controlled test data
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Add damien-cli to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'damien-cli'))

import damien_cli.core_api.gmail_api_service as gmail_api


@dataclass
class TestData:
    """Track all test data created for cleanup"""
    label_ids: List[str] = None
    email_ids: List[str] = None
    draft_ids: List[str] = None
    rule_ids: List[str] = None
    
    def __post_init__(self):
        if self.label_ids is None:
            self.label_ids = []
        if self.email_ids is None:
            self.email_ids = []
        if self.draft_ids is None:
            self.draft_ids = []
        if self.rule_ids is None:
            self.rule_ids = []


class WriteOperationsTester:
    """Test write operations with controlled test data"""
    
    def __init__(self):
        self.gmail_service = None
        self.test_label = f"DAMIEN_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_data = TestData()
        self.results = []
        
    async def initialize(self):
        """Initialize Gmail service"""
        print("🔧 Initializing services...")
        
        try:
            self.gmail_service = gmail_api.get_authenticated_service()
            
            # Get account info
            profile = self.gmail_service.users().getProfile(userId='me').execute()
            self.account_email = profile['emailAddress']
            
            print(f"✅ Connected to: {self.account_email}")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def create_test_label(self) -> Optional[str]:
        """Create a test label for our test emails"""
        print(f"\n📝 Creating test label: {self.test_label}")
        
        try:
            label_body = {
                'name': self.test_label,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show',
                'color': {
                    'backgroundColor': '#16a765',
                    'textColor': '#ffffff'
                }
            }
            
            result = self.gmail_service.users().labels().create(
                userId='me',
                body=label_body
            ).execute()
            
            label_id = result['id']
            self.test_data.label_ids.append(label_id)
            
            print(f"✅ Created test label (ID: {label_id})")
            return label_id
            
        except Exception as e:
            print(f"❌ Failed to create test label: {e}")
            return None
    
    async def create_test_draft(self, label_id: str) -> Optional[str]:
        """Create a test draft email"""
        print(f"\n📝 Creating test draft...")
        
        try:
            # Use the correct function signature
            result = gmail_api.create_draft(
                gmail_service=self.gmail_service,
                to_addresses=[self.account_email],
                subject=f"[TEST DRAFT] Damien Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                body="[TEST EMAIL] This is a test draft created by Damien test suite"
            )
            
            draft_id = result['id']
            self.test_data.draft_ids.append(draft_id)
            
            # Add label to the draft message
            if label_id:
                try:
                    message_id = result['message']['id']
                    gmail_api.batch_modify_message_labels(
                        gmail_service=self.gmail_service,
                        message_ids=[message_id],
                        add_label_names=[self.test_label]
                    )
                except:
                    pass  # Label adding is optional
            
            print(f"✅ Created test draft (ID: {draft_id})")
            return draft_id
            
        except Exception as e:
            print(f"❌ Failed to create test draft: {e}")
            return None
    
    async def test_update_draft(self, draft_id: str) -> bool:
        """Test updating a draft"""
        print(f"\n🔄 Testing draft update...")
        
        try:
            # Update draft with new content
            updated_draft = gmail_api.update_draft(
                gmail_service=self.gmail_service,
                draft_id=draft_id,
                subject=f"[TEST DRAFT - UPDATED] Damien Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                body="[TEST EMAIL - UPDATED] This draft was updated by Damien test suite"
            )
            
            print(f"✅ Successfully updated draft")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update draft: {e}")
            return False
    
    async def test_label_operations(self, label_id: str) -> bool:
        """Test label update operations"""
        print(f"\n🏷️  Testing label operations...")
        
        try:
            # Update label name
            updated_label_body = {
                'name': f"{self.test_label}_UPDATED",
                'color': {
                    'backgroundColor': '#4986e7',
                    'textColor': '#ffffff'
                }
            }
            
            result = self.gmail_service.users().labels().update(
                userId='me',
                id=label_id,
                body=updated_label_body
            ).execute()
            
            print(f"✅ Successfully updated label to: {result['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update label: {e}")
            return False
    
    # Removed filter and vacation settings test methods - not core functionality
    # These features are better handled by AI smart filtering and manual Gmail settings
    
    async def cleanup_test_data(self):
        """Clean up all test data created"""
        print("\n🧹 Cleaning up test data...")
        
        cleanup_results = {
            "labels_deleted": 0,
            "drafts_deleted": 0,
            "errors": []
        }
        
        # Delete test drafts
        for draft_id in self.test_data.draft_ids:
            try:
                gmail_api.delete_draft(
                    gmail_service=self.gmail_service,
                    draft_id=draft_id
                )
                cleanup_results["drafts_deleted"] += 1
                print(f"   ✅ Deleted draft {draft_id}")
            except Exception as e:
                cleanup_results["errors"].append(f"Failed to delete draft {draft_id}: {e}")
        
        # Removed filter cleanup - no longer creating filters
        
        # Delete test labels
        for label_id in self.test_data.label_ids:
            try:
                self.gmail_service.users().labels().delete(
                    userId='me',
                    id=label_id
                ).execute()
                cleanup_results["labels_deleted"] += 1
                print(f"   ✅ Deleted label {label_id}")
            except Exception as e:
                cleanup_results["errors"].append(f"Failed to delete label {label_id}: {e}")
        
        print(f"\n📊 Cleanup Summary:")
        print(f"   Labels deleted: {cleanup_results['labels_deleted']}")
        print(f"   Drafts deleted: {cleanup_results['drafts_deleted']}")
        
        if cleanup_results["errors"]:
            print(f"   ⚠️  Errors: {len(cleanup_results['errors'])}")
            for error in cleanup_results["errors"]:
                print(f"      - {error}")
        
        return cleanup_results
    
    async def run_write_tests(self):
        """Run all write operation tests"""
        print("\n" + "="*60)
        print("📝 PHASE 2: Write Operations Tests")
        print("="*60)
        
        results = {
            "tests": [],
            "passed": 0,
            "failed": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # Test 1: Create label
        label_id = await self.create_test_label()
        if label_id:
            results["passed"] += 1
            results["tests"].append({"name": "create_label", "status": "passed"})
        else:
            results["failed"] += 1
            results["tests"].append({"name": "create_label", "status": "failed"})
            print("⚠️  Cannot proceed without test label")
            return results
        
        # Test 2: Update label
        if await self.test_label_operations(label_id):
            results["passed"] += 1
            results["tests"].append({"name": "update_label", "status": "passed"})
        else:
            results["failed"] += 1
            results["tests"].append({"name": "update_label", "status": "failed"})
        
        # Test 3: Create draft
        draft_id = await self.create_test_draft(label_id)
        if draft_id:
            results["passed"] += 1
            results["tests"].append({"name": "create_draft", "status": "passed"})
            
            # Test 4: Update draft
            if await self.test_update_draft(draft_id):
                results["passed"] += 1
                results["tests"].append({"name": "update_draft", "status": "passed"})
            else:
                results["failed"] += 1
                results["tests"].append({"name": "update_draft", "status": "failed"})
        else:
            results["failed"] += 1
            results["tests"].append({"name": "create_draft", "status": "failed"})
        
        # Removed filter and vacation settings tests - not core functionality
        # These features are better handled by AI smart filtering and manual Gmail settings
        
        results["end_time"] = datetime.now().isoformat()
        
        # Summary
        total = results["passed"] + results["failed"]
        print("\n" + "="*60)
        print(f"📊 Write Operations Summary: {results['passed']}/{total} passed")
        print(f"   ✅ Passed: {results['passed']}")
        print(f"   ❌ Failed: {results['failed']}")
        
        return results


async def main():
    """Main entry point"""
    tester = WriteOperationsTester()
    
    if not await tester.initialize():
        return
    
    print("\n🚀 Damien Email Wrestler - Write Operations Testing")
    print("="*60)
    print("⚠️  This will create temporary test data in your Gmail account")
    print("   All test data will be cleaned up automatically")
    print("="*60)
    
    # Get user confirmation
    confirm = input("\nProceed with write operations testing? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Testing cancelled")
        return
    
    try:
        # Run tests
        results = await tester.run_write_tests()
        
        # Save results
        with open("test_results_write_operations.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to test_results_write_operations.json")
        
    finally:
        # Always cleanup
        print("\n" + "="*60)
        cleanup = await tester.cleanup_test_data()
        
        if not cleanup["errors"]:
            print("\n✅ All test data cleaned up successfully!")
        else:
            print("\n⚠️  Some cleanup errors occurred. Please check your Gmail for any remaining test data.")


if __name__ == "__main__":
    asyncio.run(main())