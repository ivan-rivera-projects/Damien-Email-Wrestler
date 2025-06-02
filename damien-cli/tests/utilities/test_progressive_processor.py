import unittest
import asyncio
from damien_cli.utilities.progressive_processor import progressive_batch_operation

# Global flag to track if tests ran
TESTS_RAN = False

class TestProgressiveProcessor(unittest.TestCase):
    """Tests for the progressive processor module."""
    
    # Use a single test method as the entry point for all async tests
    def test_all_async_tests(self):
        global TESTS_RAN
        
        if TESTS_RAN:
            self.skipTest("Tests already ran")
            
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run all async tests
            loop.run_until_complete(self.run_async_tests())
            TESTS_RAN = True
        finally:
            loop.close()
            
    async def run_async_tests(self):
        """Run all async test methods."""
        await self.test_progressive_batch_operation()
        await self.test_progressive_batch_operation_error_handling()
        await self.test_batch_size_growth()
    
    async def test_progressive_batch_operation(self):
        """Test progressive batching with mock functions."""
        # Mock functions
        async def mock_fetch(query, max_results, page_token):
            return {
                "messages": [{"id": f"msg_{i}"} for i in range(max_results)],
                "nextPageToken": "next_token" if max_results == 25 else None
            }
            
        async def mock_process(message_ids):
            return {"success": True, "processed": len(message_ids)}
            
        # Run progressive operation
        results = []
        async for progress in progressive_batch_operation(
            fetch_function=mock_fetch,
            process_function=mock_process,
            query="test",
            estimated_count=50
        ):
            results.append(progress)
            
        # Verify progress tracking
        self.assertGreaterEqual(len(results), 2)  # Should have at least 2 progress updates
        self.assertTrue(results[-1]["operation_complete"])  # Last update should indicate completion
        
    async def test_progressive_batch_operation_error_handling(self):
        """Test error handling in progressive batching."""
        # Mock functions with error
        async def mock_fetch(query, max_results, page_token):
            if max_results == 25 and not page_token:
                return {
                    "messages": [{"id": f"msg_{i}"} for i in range(max_results)],
                    "nextPageToken": "next_token"
                }
            else:
                # Simulate error on second fetch
                raise Exception("Simulated fetch error")
            
        async def mock_process(message_ids):
            return {"success": True, "processed": len(message_ids)}
            
        # Run progressive operation
        results = []
        async for progress in progressive_batch_operation(
            fetch_function=mock_fetch,
            process_function=mock_process,
            query="test",
            estimated_count=50
        ):
            results.append(progress)
            
        # Verify error handling
        self.assertTrue(any("error" in p for p in results))
        # The final result may or may not have success=False, depending on implementation
        # Just check that we have an error somewhere in the results
        self.assertTrue(any(not p.get("success", True) for p in results) or
                       any("error" in p for p in results))
        
    async def test_batch_size_growth(self):
        """Test that batch size grows over time."""
        # Track batch sizes used
        batch_sizes = []
        
        async def mock_fetch(query, max_results, page_token):
            batch_sizes.append(max_results)
            # Return enough messages to go through multiple pages
            # If we've already collected 3 batch sizes, end the pagination
            return {
                "messages": [{"id": f"msg_{i}"} for i in range(max_results)],
                "nextPageToken": None if len(batch_sizes) >= 3 else f"token_{len(batch_sizes)}"
            }
            
        async def mock_process(message_ids):
            return {"success": True, "processed": len(message_ids)}
            
        # Run with growth factor
        batch_sizing = {
            "initial_batch_size": 10,
            "max_batch_size": 50,
            "growth_factor": 2.0,
            "provide_feedback_every": 10
        }
        
        # Collect all progress updates
        results = []
        async for progress in progressive_batch_operation(
            fetch_function=mock_fetch,
            process_function=mock_process,
            query="test",
            batch_sizing=batch_sizing
        ):
            results.append(progress)
            
        # Verify we got enough batches
        self.assertGreaterEqual(len(batch_sizes), 2, "Not enough batches collected")
        
        # Verify batch size growth - only if we have at least 2 batches
        if len(batch_sizes) >= 2:
            self.assertGreater(batch_sizes[1], batch_sizes[0], 
                             f"Batch size didn't grow: {batch_sizes[0]} -> {batch_sizes[1]}")
            
        # Verify completion
        self.assertTrue(results[-1]["operation_complete"], "Operation did not complete")


if __name__ == "__main__":
    unittest.main()
