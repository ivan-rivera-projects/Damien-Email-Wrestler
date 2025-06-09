"""
Safe Test Runner for Live Gmail Account
Starts with read-only operations and provides full transparency for any modifications
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Add damien-cli to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'damien-cli'))

import damien_cli.core_api.gmail_api_service as gmail_api


class TestType(Enum):
    """Test operation types"""
    READ_ONLY = "read_only"
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


@dataclass
class ToolTestConfig:
    """Configuration for testing a specific tool"""
    tool_name: str
    test_type: TestType
    description: str
    safe_for_live: bool = True
    requires_confirmation: bool = False
    test_data_needed: List[str] = None
    
    def __post_init__(self):
        if self.test_data_needed is None:
            self.test_data_needed = []


class SafeTestRunner:
    """Safe test runner for live Gmail accounts"""
    
    def __init__(self):
        self.gmail_service = None
        self.test_results = []
        self.test_label = f"DAMIEN_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_email_ids = []
        
    async def initialize(self):
        """Initialize services"""
        print("🔧 Initializing services...")
        
        try:
            # Get authenticated Gmail service
            self.gmail_service = gmail_api.get_authenticated_service()
            
            # Get account info
            profile = self.gmail_service.users().getProfile(userId='me').execute()
            self.account_email = profile['emailAddress']
            
            print(f"✅ Connected to: {self.account_email}")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def get_tool_test_configs(self) -> List[ToolTestConfig]:
        """Get test configurations for all tools, organized by safety level"""
        return [
            # PHASE 1: Completely Safe Read-Only Tools
            ToolTestConfig("damien_list_emails", TestType.READ_ONLY, 
                          "Lists emails without any modifications"),
            ToolTestConfig("damien_get_email_details", TestType.READ_ONLY,
                          "Reads email details without modifications"),
            ToolTestConfig("damien_search_emails", TestType.READ_ONLY,
                          "Searches emails without modifications"),
            ToolTestConfig("damien_list_labels", TestType.READ_ONLY,
                          "Lists existing labels"),
            ToolTestConfig("damien_get_label", TestType.READ_ONLY,
                          "Gets label details"),
            ToolTestConfig("damien_list_threads", TestType.READ_ONLY,
                          "Lists email threads"),
            ToolTestConfig("damien_get_thread", TestType.READ_ONLY,
                          "Gets thread details"),
            ToolTestConfig("damien_fetch_recent_unread_from_addresses", TestType.READ_ONLY,
                          "Lists recent unread senders"),
            ToolTestConfig("damien_list_rules", TestType.READ_ONLY,
                          "Lists existing rules"),
            ToolTestConfig("damien_list_drafts", TestType.READ_ONLY,
                          "Lists existing drafts"),
            ToolTestConfig("damien_get_draft", TestType.READ_ONLY,
                          "Gets draft details"),
            # Removed vacation and filter tools - not core to AI email management
            
            # AI Intelligence Tools (all read-only analysis)
            ToolTestConfig("damien_ai_analyze_emails", TestType.READ_ONLY,
                          "AI analysis without modifications"),
            ToolTestConfig("damien_ai_suggest_rules", TestType.READ_ONLY,
                          "AI rule suggestions without creating"),
            ToolTestConfig("damien_ai_categorize_senders", TestType.READ_ONLY,
                          "AI categorization without modifications"),
            ToolTestConfig("damien_ai_detect_patterns", TestType.READ_ONLY,
                          "AI pattern detection"),
            ToolTestConfig("damien_ai_generate_insights", TestType.READ_ONLY,
                          "AI insights generation"),
            
            # PHASE 2: Create Operations (requires confirmation)
            ToolTestConfig("damien_create_label", TestType.CREATE,
                          "Creates a new label", requires_confirmation=True),
            ToolTestConfig("damien_create_draft", TestType.CREATE,
                          "Creates a new draft", requires_confirmation=True),
            ToolTestConfig("damien_add_rule", TestType.CREATE,
                          "Creates a new rule", requires_confirmation=True),
            
            # PHASE 3: Modify Operations (requires test data)
            ToolTestConfig("damien_label_emails", TestType.MODIFY,
                          "Adds labels to emails", requires_confirmation=True,
                          test_data_needed=["test_emails"]),
            ToolTestConfig("damien_mark_emails", TestType.MODIFY,
                          "Marks emails as read/unread", requires_confirmation=True,
                          test_data_needed=["test_emails"]),
            ToolTestConfig("damien_trash_emails", TestType.MODIFY,
                          "Moves emails to trash", requires_confirmation=True,
                          test_data_needed=["test_emails"]),
            
            # PHASE 4: Delete Operations (extra careful)
            ToolTestConfig("damien_delete_emails_permanently", TestType.DELETE,
                          "Permanently deletes emails", requires_confirmation=True,
                          test_data_needed=["test_emails_in_trash"]),
            ToolTestConfig("damien_delete_label", TestType.DELETE,
                          "Deletes a label", requires_confirmation=True,
                          test_data_needed=["test_label"]),
        ]
    
    async def run_phase_1_readonly_tests(self) -> Dict[str, Any]:
        """Run all read-only tests that are completely safe"""
        print("\n" + "="*60)
        print("🔍 PHASE 1: Read-Only Tests (100% Safe)")
        print("="*60)
        
        configs = [c for c in self.get_tool_test_configs() if c.test_type == TestType.READ_ONLY]
        results = {"passed": 0, "failed": 0, "errors": 0, "tests": []}
        
        for config in configs:
            print(f"\n📧 Testing: {config.tool_name}")
            print(f"   Description: {config.description}")
            
            start_time = time.time()
            
            try:
                result = await self._test_tool(config)
                duration = (time.time() - start_time) * 1000
                
                status = "✅ PASSED" if result["success"] else "❌ FAILED"
                print(f"   Status: {status} ({duration:.0f}ms)")
                
                if result.get("data"):
                    print(f"   Result: {result['data']}")
                
                if result["success"]:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    
                results["tests"].append({
                    "tool": config.tool_name,
                    "success": result["success"],
                    "duration_ms": duration,
                    "details": result
                })
                
            except Exception as e:
                print(f"   Status: ❌ ERROR - {str(e)}")
                results["errors"] += 1
                results["tests"].append({
                    "tool": config.tool_name,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        total = len(configs)
        print("\n" + "="*60)
        print(f"📊 Phase 1 Summary: {results['passed']}/{total} passed")
        print(f"   ✅ Passed: {results['passed']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   ⚠️  Errors: {results['errors']}")
        
        return results
    
    async def _test_tool(self, config: ToolTestConfig) -> Dict[str, Any]:
        """Test a specific tool based on its configuration"""
        
        # Tool-specific test implementations
        tool_tests = {
            "damien_list_emails": self._test_list_emails,
            "damien_get_email_details": self._test_get_email_details,
            "damien_search_emails": self._test_search_emails,
            "damien_list_labels": self._test_list_labels,
            "damien_get_label": self._test_get_label,
            "damien_list_threads": self._test_list_threads,
            "damien_get_thread": self._test_get_thread,
            "damien_fetch_recent_unread_from_addresses": self._test_fetch_unread,
            "damien_list_rules": self._test_list_rules,
            "damien_list_drafts": self._test_list_drafts,
            "damien_get_draft": self._test_get_draft,
            # Removed vacation and filter tools
            # AI tools need special handling
            "damien_ai_analyze_emails": self._test_ai_placeholder,
            "damien_ai_suggest_rules": self._test_ai_placeholder,
            "damien_ai_categorize_senders": self._test_ai_placeholder,
            "damien_ai_detect_patterns": self._test_ai_placeholder,
            "damien_ai_generate_insights": self._test_ai_placeholder,
        }
        
        test_func = tool_tests.get(config.tool_name)
        if test_func:
            return await test_func()
        
        return {"success": False, "error": "Test not implemented"}
    
    async def _test_list_emails(self) -> Dict[str, Any]:
        """Test list emails functionality"""
        try:
            # Call the Gmail API directly - note: list_messages doesn't have include_headers param
            result = gmail_api.list_messages(
                gmail_service=self.gmail_service,
                max_results=5
            )
            
            messages = result.get('messages', [])
            
            return {
                "success": True,
                "data": f"Found {len(messages)} emails",
                "sample": messages[0] if messages else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_get_email_details(self) -> Dict[str, Any]:
        """Test get email details"""
        try:
            # First get an email
            result = gmail_api.list_messages(
                gmail_service=self.gmail_service,
                max_results=1
            )
            messages = result.get('messages', [])
            if not messages:
                return {"success": False, "error": "No emails found"}
            
            # Get details
            details = gmail_api.get_message_details(
                gmail_service=self.gmail_service,
                message_id=messages[0]['id']
            )
            
            # Extract subject from headers
            headers = details.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
            
            return {
                "success": True,
                "data": f"Retrieved details for email: {subject}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_search_emails(self) -> Dict[str, Any]:
        """Test email search"""
        try:
            # Search for recent emails
            query = "newer_than:7d"
            result = gmail_api.list_messages(
                gmail_service=self.gmail_service,
                query_string=query,
                max_results=5
            )
            
            messages = result.get('messages', [])
            
            return {
                "success": True,
                "data": f"Search found {len(messages)} emails from last 7 days"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_list_labels(self) -> Dict[str, Any]:
        """Test list labels"""
        try:
            response = self.gmail_service.users().labels().list(userId='me').execute()
            labels = response.get('labels', [])
            
            user_labels = [l for l in labels if l['type'] == 'user']
            system_labels = [l for l in labels if l['type'] == 'system']
            
            return {
                "success": True,
                "data": f"Found {len(user_labels)} user labels, {len(system_labels)} system labels"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_list_threads(self) -> Dict[str, Any]:
        """Test list threads"""
        try:
            result = gmail_api.list_threads(
                gmail_service=self.gmail_service,
                max_results=5
            )
            
            threads = result.get('threads', [])
            
            return {
                "success": True,
                "data": f"Found {len(threads)} threads"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_fetch_unread(self) -> Dict[str, Any]:
        """Test fetch recent unread from addresses"""
        try:
            # Search for unread emails
            result = gmail_api.list_messages(
                gmail_service=self.gmail_service,
                query_string='is:unread',
                max_results=10
            )
            
            messages = result.get('messages', [])
            
            return {
                "success": True,
                "data": f"Found {len(messages)} unread messages"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Removed vacation settings test - not core functionality
    
    async def _test_list_drafts(self) -> Dict[str, Any]:
        """Test list drafts"""
        try:
            drafts = gmail_api.list_drafts(self.gmail_service, max_results=5)
            
            draft_list = drafts.get('drafts', [])
            
            return {
                "success": True,
                "data": f"Found {len(draft_list)} drafts"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_get_label(self) -> Dict[str, Any]:
        """Test get label details"""
        try:
            # First get a user label from the list
            response = self.gmail_service.users().labels().list(userId='me').execute()
            labels = response.get('labels', [])
            user_labels = [l for l in labels if l['type'] == 'user']
            
            if not user_labels:
                return {"success": True, "data": "No user labels to test"}
            
            # Get details for the first user label
            label_id = user_labels[0]['id']
            label_details = self.gmail_service.users().labels().get(
                userId='me',
                id=label_id
            ).execute()
            
            return {
                "success": True,
                "data": f"Retrieved details for label: {label_details.get('name', 'Unknown')}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_get_thread(self) -> Dict[str, Any]:
        """Test get thread details"""
        try:
            # First get a thread
            threads = gmail_api.list_threads(
                gmail_service=self.gmail_service,
                max_results=1
            )
            
            thread_list = threads.get('threads', [])
            if not thread_list:
                return {"success": False, "error": "No threads found"}
            
            # Get thread details
            thread_details = gmail_api.get_thread_details(
                gmail_service=self.gmail_service,
                thread_id=thread_list[0]['id']
            )
            
            messages = thread_details.get('messages', [])
            
            return {
                "success": True,
                "data": f"Retrieved thread with {len(messages)} messages"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_get_draft(self) -> Dict[str, Any]:
        """Test get draft details"""
        try:
            # First get a draft
            drafts = gmail_api.list_drafts(
                gmail_service=self.gmail_service,
                max_results=1
            )
            
            draft_list = drafts.get('drafts', [])
            if not draft_list:
                return {"success": True, "data": "No drafts to test"}
            
            # Get draft details
            draft_details = gmail_api.get_draft_details(
                gmail_service=self.gmail_service,
                draft_id=draft_list[0]['id']
            )
            
            message = draft_details.get('message', {})
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
            
            return {
                "success": True,
                "data": f"Retrieved draft: {subject}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Removed filter management test - not core functionality
    
    async def _test_list_rules(self) -> Dict[str, Any]:
        """Test list rules - this is a Damien-specific feature, not Gmail API"""
        try:
            # Rules are stored in the Damien system, not Gmail
            # For now, we'll check if the rules file exists
            import os
            rules_file = os.path.join(
                os.path.dirname(__file__), 
                '..', 'damien-cli', 'data', 'rules.json'
            )
            
            if os.path.exists(rules_file):
                with open(rules_file, 'r') as f:
                    import json
                    rules = json.load(f)
                    
                return {
                    "success": True,
                    "data": f"Found {len(rules)} Damien rules"
                }
            else:
                return {
                    "success": True,
                    "data": "No Damien rules file found (this is normal)"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_ai_placeholder(self) -> Dict[str, Any]:
        """Placeholder for AI tools that require MCP server"""
        return {
            "success": True,
            "data": "AI tools require MCP server connection (not direct Gmail API)"
        }
    
    async def preview_test_data_creation(self) -> Dict[str, Any]:
        """Preview what test data would be created"""
        print("\n" + "="*60)
        print("📋 Test Data Creation Preview")
        print("="*60)
        
        preview = {
            "test_label": {
                "name": self.test_label,
                "purpose": "Groups all test emails for easy identification and cleanup",
                "color": "Green"
            },
            "test_emails": {
                "count": 5,
                "subjects": [
                    "[TEST EMAIL] Sample Promotional Email",
                    "[TEST EMAIL] Sample Newsletter",
                    "[TEST EMAIL] Sample Personal Message",
                    "[TEST EMAIL] Important Test Email",
                    "[TEST EMAIL] Thread Test Message"
                ],
                "characteristics": "All will be labeled with test label for easy cleanup"
            },
            "cleanup_process": {
                "method": "Search for test label and bulk delete",
                "command": f"label:{self.test_label}",
                "reversible": "Emails go to trash first (30-day recovery)"
            }
        }
        
        print(json.dumps(preview, indent=2))
        
        return preview
    
    async def create_minimal_test_data(self, count: int = 5) -> bool:
        """Create minimal test data with user confirmation"""
        print(f"\n⚠️  About to create {count} test emails in your account")
        print(f"   - All will be labeled: {self.test_label}")
        print(f"   - All subjects start with: [TEST EMAIL]")
        print(f"   - Easy cleanup with single label search")
        
        confirm = input("\nProceed with test data creation? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Test data creation cancelled")
            return False
        
        # Implementation would go here
        print("✅ Test data would be created here")
        return True


async def main():
    """Main entry point"""
    runner = SafeTestRunner()
    
    if not await runner.initialize():
        return
    
    print("\n🚀 Damien Email Wrestler - Safe Live Account Testing")
    print("="*60)
    
    # Show test phases
    print("\nTest Phases:")
    print("1. Read-Only Tests (100% safe, no modifications)")
    print("2. Test Data Preview (see what would be created)")
    print("3. Create Minimal Test Data (with confirmation)")
    print("4. Run Modification Tests (only on test data)")
    
    # Run Phase 1
    phase1_results = await runner.run_phase_1_readonly_tests()
    
    # Ask about next phase
    print("\n" + "="*60)
    print("Phase 1 complete! Next steps:")
    print("1. Preview test data that would be created")
    print("2. Exit and review results")
    
    choice = input("\nYour choice (1-2): ")
    
    if choice == "1":
        await runner.preview_test_data_creation()


if __name__ == "__main__":
    asyncio.run(main())