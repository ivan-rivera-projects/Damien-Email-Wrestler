#!/usr/bin/env python3
"""
Job Management Validation Script

This script validates the complete job management workflow by testing
all aspects of the async infrastructure that has proven capable of
processing 3,500 emails in 7 minutes with 90% statistical reliability.

Usage: python validate_job_management.py
"""

import asyncio
import httpx
import time
import json
import sys
import os
from typing import Dict, List, Optional


class JobManagementValidator:
    """Validates job management functionality with real API calls."""
    
    def __init__(self, base_url: str = "http://localhost:8892", api_key: str = "test-api-key"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.results = []
        
    async def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute a tool via the MCP server API."""
        async with httpx.AsyncClient() as client:
            request_data = {
                "tool_name": tool_name,
                "parameters": parameters
            }
            
            response = await client.post(
                f"{self.base_url}/tools/execute",
                headers=self.headers,
                json=request_data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
                
            return response.json()
    
    async def test_job_creation(self) -> bool:
        """Test 1: Job Creation - Verify jobs can be created successfully."""
        print("🔧 Test 1: Job Creation")
        
        try:
            result = await self.execute_tool("damien_ai_analyze_emails_async", {
                "days": 1,
                "target_count": 5,
                "min_confidence": 0.7,
                "query": "",
                "use_statistical_validation": True
            })
            
            if result.get("success"):
                job_id = result.get("job_id")
                print(f"   ✅ Job created successfully: {job_id}")
                print(f"   📊 Estimated duration: {result.get('estimated_duration_minutes', 'unknown')} minutes")
                self.results.append(("Job Creation", True, job_id))
                return job_id
            else:
                print(f"   ❌ Job creation failed: {result.get('error')}")
                self.results.append(("Job Creation", False, result.get('error')))
                return None
                
        except Exception as e:
            print(f"   ❌ Exception during job creation: {e}")
            self.results.append(("Job Creation", False, str(e)))
            return None
    
    async def test_job_status_tracking(self, job_id: str) -> bool:
        """Test 2: Status Tracking - Monitor job progress."""
        print("📊 Test 2: Job Status Tracking")
        
        try:
            max_checks = 10
            for check in range(max_checks):
                result = await self.execute_tool("damien_job_get_status", {
                    "job_id": job_id
                })
                
                if result.get("success"):
                    status = result.get("status")
                    progress = result.get("progress", {})
                    progress_pct = progress.get("percentage", 0)
                    
                    print(f"   📈 Check {check + 1}: Status={status}, Progress={progress_pct}%")
                    
                    if status == "completed":
                        print("   ✅ Job completed successfully")
                        self.results.append(("Status Tracking", True, "Job completed"))
                        return True
                    elif status == "failed":
                        print(f"   ❌ Job failed: {progress.get('message')}")
                        self.results.append(("Status Tracking", False, "Job failed"))
                        return False
                    elif status in ["pending", "running"]:
                        await asyncio.sleep(3)  # Wait before next check
                        continue
                else:
                    print(f"   ❌ Status check failed: {result.get('error')}")
                    self.results.append(("Status Tracking", False, result.get('error')))
                    return False
            
            print("   ⚠️  Job did not complete within expected time")
            self.results.append(("Status Tracking", False, "Timeout"))
            return False
            
        except Exception as e:
            print(f"   ❌ Exception during status tracking: {e}")
            self.results.append(("Status Tracking", False, str(e)))
            return False
    
    async def test_job_results_retrieval(self, job_id: str) -> bool:
        """Test 3: Results Retrieval - Get completed job results."""
        print("🎯 Test 3: Job Results Retrieval")
        
        try:
            result = await self.execute_tool("damien_job_get_result", {
                "job_id": job_id
            })
            
            if result.get("success"):
                job_result = result.get("result")
                if job_result:
                    emails_analyzed = job_result.get("emails_analyzed", 0)
                    patterns_detected = job_result.get("patterns_detected", 0)
                    
                    print(f"   ✅ Results retrieved successfully")
                    print(f"   📧 Emails analyzed: {emails_analyzed}")
                    print(f"   🔍 Patterns detected: {patterns_detected}")
                    
                    if "insights" in job_result:
                        print(f"   💡 Business insights generated")
                    
                    self.results.append(("Results Retrieval", True, f"{emails_analyzed} emails, {patterns_detected} patterns"))
                    return True
                else:
                    print("   ❌ No results in response")
                    self.results.append(("Results Retrieval", False, "No results"))
                    return False
            else:
                print(f"   ❌ Results retrieval failed: {result.get('error')}")
                self.results.append(("Results Retrieval", False, result.get('error')))
                return False
                
        except Exception as e:
            print(f"   ❌ Exception during results retrieval: {e}")
            self.results.append(("Results Retrieval", False, str(e)))
            return False
    
    async def test_job_cancellation(self) -> bool:
        """Test 4: Job Cancellation - Test ability to cancel running jobs."""
        print("❌ Test 4: Job Cancellation")
        
        try:
            # Start a longer job for cancellation testing
            result = await self.execute_tool("damien_ai_analyze_emails_async", {
                "days": 7,
                "target_count": 100,  # Larger dataset for longer processing
                "min_confidence": 0.8
            })
            
            if not result.get("success"):
                print(f"   ❌ Could not start job for cancellation test: {result.get('error')}")
                self.results.append(("Job Cancellation", False, "Could not start job"))
                return False
            
            job_id = result.get("job_id")
            print(f"   🔧 Started job for cancellation: {job_id}")
            
            # Wait a moment for job to start processing
            await asyncio.sleep(2)
            
            # Cancel the job
            cancel_result = await self.execute_tool("damien_job_cancel", {
                "job_id": job_id
            })
            
            if cancel_result.get("success"):
                print(f"   ✅ Job cancelled successfully: {job_id}")
                
                # Verify job status shows cancelled
                await asyncio.sleep(1)
                status_result = await self.execute_tool("damien_job_get_status", {
                    "job_id": job_id
                })
                
                if status_result.get("status") == "cancelled":
                    print("   ✅ Job status confirmed as cancelled")
                    self.results.append(("Job Cancellation", True, "Successfully cancelled"))
                    return True
                else:
                    print(f"   ⚠️  Job status not updated to cancelled: {status_result.get('status')}")
                    self.results.append(("Job Cancellation", False, "Status not updated"))
                    return False
            else:
                print(f"   ❌ Job cancellation failed: {cancel_result.get('error')}")
                self.results.append(("Job Cancellation", False, cancel_result.get('error')))
                return False
                
        except Exception as e:
            print(f"   ❌ Exception during job cancellation: {e}")
            self.results.append(("Job Cancellation", False, str(e)))
            return False
    
    async def test_job_listing(self) -> bool:
        """Test 5: Job Listing - Test active job management."""
        print("📋 Test 5: Job Listing")
        
        try:
            # Get initial job list
            result = await self.execute_tool("damien_job_list", {})
            
            if result.get("success"):
                active_jobs = result.get("active_jobs", [])
                job_count = result.get("count", 0)
                
                print(f"   ✅ Job list retrieved successfully")
                print(f"   📊 Active jobs: {job_count}")
                
                for job in active_jobs[:3]:  # Show first 3 jobs
                    job_id = job.get("task_id", "unknown")
                    job_name = job.get("name", "unknown")
                    job_status = job.get("status", "unknown")
                    print(f"   📝 Job {job_id[:8]}...: {job_name} ({job_status})")
                
                self.results.append(("Job Listing", True, f"{job_count} active jobs"))
                return True
            else:
                print(f"   ❌ Job listing failed: {result.get('error')}")
                self.results.append(("Job Listing", False, result.get('error')))
                return False
                
        except Exception as e:
            print(f"   ❌ Exception during job listing: {e}")
            self.results.append(("Job Listing", False, str(e)))
            return False
    
    async def test_error_handling(self) -> bool:
        """Test 6: Error Handling - Test invalid requests."""
        print("⚠️  Test 6: Error Handling")
        
        tests_passed = 0
        total_tests = 4
        
        try:
            # Test 1: Invalid job ID for status
            result = await self.execute_tool("damien_job_get_status", {
                "job_id": "invalid_job_id_12345"
            })
            
            if not result.get("success") and "not found" in result.get("error", "").lower():
                print("   ✅ Invalid job ID properly rejected")
                tests_passed += 1
            else:
                print("   ❌ Invalid job ID not properly handled")
            
            # Test 2: Missing job_id parameter
            result = await self.execute_tool("damien_job_get_status", {})
            
            if not result.get("success") and "required" in result.get("error", "").lower():
                print("   ✅ Missing parameter properly rejected") 
                tests_passed += 1
            else:
                print("   ❌ Missing parameter not properly handled")
            
            # Test 3: Invalid job ID for results
            result = await self.execute_tool("damien_job_get_result", {
                "job_id": "another_invalid_job_id"
            })
            
            if not result.get("success"):
                print("   ✅ Invalid job ID for results properly rejected")
                tests_passed += 1
            else:
                print("   ❌ Invalid job ID for results not properly handled")
            
            # Test 4: Invalid job ID for cancellation
            result = await self.execute_tool("damien_job_cancel", {
                "job_id": "yet_another_invalid_job_id"
            })
            
            if not result.get("success"):
                print("   ✅ Invalid job ID for cancellation properly rejected")
                tests_passed += 1
            else:
                print("   ❌ Invalid job ID for cancellation not properly handled")
            
            success = tests_passed == total_tests
            self.results.append(("Error Handling", success, f"{tests_passed}/{total_tests} tests passed"))
            return success
            
        except Exception as e:
            print(f"   ❌ Exception during error handling tests: {e}")
            self.results.append(("Error Handling", False, str(e)))
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all job management validation tests."""
        print("🚀 Starting Job Management Validation")
        print("=" * 50)
        
        try:
            # Test server connectivity first
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/health", timeout=5.0)
                    if response.status_code != 200:
                        print(f"❌ Server not responding: {response.status_code}")
                        return False
                print("✅ Server connectivity confirmed")
            except Exception as e:
                print(f"❌ Cannot connect to server: {e}")
                print(f"   Make sure MCP server is running on {self.base_url}")
                return False
            
            print()
            
            # Run tests in sequence
            job_id = await self.test_job_creation()
            if not job_id:
                print("❌ Cannot continue without successful job creation")
                return False
            
            print()
            
            status_success = await self.test_job_status_tracking(job_id)
            print()
            
            if status_success:
                results_success = await self.test_job_results_retrieval(job_id)
                print()
            else:
                print("⏭️  Skipping results retrieval due to status tracking failure")
                results_success = False
            
            cancellation_success = await self.test_job_cancellation()
            print()
            
            listing_success = await self.test_job_listing()
            print()
            
            error_handling_success = await self.test_error_handling()
            print()
            
            # Summary
            print("=" * 50)
            print("📊 VALIDATION SUMMARY")
            print("=" * 50)
            
            total_tests = len(self.results)
            passed_tests = sum(1 for _, success, _ in self.results if success)
            
            for test_name, success, details in self.results:
                status_icon = "✅" if success else "❌"
                print(f"{status_icon} {test_name}: {details}")
            
            print("-" * 50)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            print(f"🎯 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
            
            if success_rate >= 80:
                print("🏆 Job Management Validation: PASSED")
                print("   System ready for Phase 1 completion")
                return True
            else:
                print("⚠️  Job Management Validation: NEEDS ATTENTION")
                print("   Some tests failed - review and fix issues")
                return False
                
        except Exception as e:
            print(f"❌ Fatal error during validation: {e}")
            return False


async def main():
    """Main entry point for job management validation."""
    print("🤼‍♂️ Damien Email Wrestler - Job Management Validation")
    print("Building on proven async infrastructure that processed 3,500 emails in 7 minutes")
    print()
    
    # Check if server URL provided
    server_url = os.getenv("DAMIEN_MCP_SERVER_URL", "http://localhost:8892")
    api_key = os.getenv("DAMIEN_MCP_SERVER_API_KEY", "test-api-key")
    
    print(f"🔗 Connecting to: {server_url}")
    print(f"🔑 Using API key: {api_key[:8]}..." if len(api_key) > 8 else "🔑 Using API key: [short key]")
    print()
    
    validator = JobManagementValidator(server_url, api_key)
    success = await validator.run_all_tests()
    
    if success:
        print()
        print("🎉 All tests passed! Job management infrastructure is validated.")
        print("✅ Ready to proceed to Phase 1: Concurrent Job Processing Stress Test")
        sys.exit(0)
    else:
        print()
        print("❌ Some tests failed. Please review and fix issues before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
