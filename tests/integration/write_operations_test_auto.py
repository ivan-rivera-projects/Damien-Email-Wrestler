#!/usr/bin/env python3
"""
Automated Write Operations Test - No user input required
"""

import asyncio
import sys
import os

# Add the write operations test module
sys.path.insert(0, os.path.dirname(__file__))

from write_operations_test import WriteOperationsTester
import json


async def main():
    """Main entry point - automated version"""
    tester = WriteOperationsTester()
    
    if not await tester.initialize():
        print("❌ Failed to initialize. Exiting.")
        return
    
    print("\n🚀 Damien Email Wrestler - Write Operations Testing (Automated)")
    print("="*60)
    print("📝 Creating minimal test data...")
    print("🧹 Will clean up automatically after testing")
    print("="*60)
    
    try:
        # Run tests without user confirmation
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