#!/usr/bin/env python3
"""
Automated safe test runner that doesn't require user input
"""

import asyncio
from safe_test_runner import SafeTestRunner
import json


async def main():
    """Main entry point"""
    runner = SafeTestRunner()
    
    if not await runner.initialize():
        print("❌ Failed to initialize. Exiting.")
        return
    
    print("\n🚀 Damien Email Wrestler - Safe Live Account Testing")
    print("="*60)
    
    # Run Phase 1 tests automatically
    phase1_results = await runner.run_phase_1_readonly_tests()
    
    # Save results
    with open("test_results_phase1.json", "w") as f:
        json.dump(phase1_results, f, indent=2)
    
    print(f"\n📄 Results saved to test_results_phase1.json")
    
    # Show summary
    print("\n📊 Test Summary:")
    print(f"   Total tools tested: {phase1_results['passed'] + phase1_results['failed'] + phase1_results['errors']}")
    print(f"   ✅ Passed: {phase1_results['passed']}")
    print(f"   ❌ Failed: {phase1_results['failed']}")
    print(f"   ⚠️  Errors: {phase1_results['errors']}")


if __name__ == "__main__":
    asyncio.run(main())