import unittest
from damien_cli.utilities.query_optimizer import optimize_bulk_query, get_batch_size_strategy

class TestQueryOptimizer(unittest.TestCase):
    def test_optimize_bulk_query_with_date_query(self):
        """Test optimization of a date-based query."""
        query = "older_than:30d"
        optimized = optimize_bulk_query(query, 500)
        
        # Should return multiple optimized queries
        self.assertGreater(len(optimized), 1)
        self.assertTrue(any("in:promotions" in q for q in optimized))
        
    def test_optimize_bulk_query_with_specific_query(self):
        """Test that specific queries aren't split."""
        query = "from:example.com older_than:30d"
        optimized = optimize_bulk_query(query, 500)
        
        # Should return original query (already targeted)
        self.assertEqual(len(optimized), 1)
        self.assertEqual(optimized[0], query)
        
    def test_get_batch_size_strategy(self):
        """Test batch sizing strategy."""
        strategy = get_batch_size_strategy("trash", 1000)
        
        # Should have required keys
        self.assertIn("initial_batch_size", strategy)
        self.assertIn("max_batch_size", strategy)
        self.assertIn("growth_factor", strategy)
        
    def test_optimize_bulk_query_small_operation(self):
        """Test that small operations don't get optimized."""
        query = "older_than:30d"
        optimized = optimize_bulk_query(query, 50)  # Small count
        
        # Should return just the original query
        self.assertEqual(len(optimized), 1)
        self.assertEqual(optimized[0], query)
        
    def test_optimize_bulk_query_with_category(self):
        """Test that queries with category don't get split."""
        query = "in:promotions older_than:30d"
        optimized = optimize_bulk_query(query, 500)
        
        # Should return original query (already has category)
        self.assertEqual(len(optimized), 1)
        self.assertEqual(optimized[0], query)
        
    def test_batch_size_strategy_by_operation(self):
        """Test that different operations get different strategies."""
        trash_strategy = get_batch_size_strategy("trash", 1000)
        label_strategy = get_batch_size_strategy("label", 1000)
        
        # Strategies should be different
        self.assertNotEqual(trash_strategy["initial_batch_size"], 
                           label_strategy["initial_batch_size"])


if __name__ == "__main__":
    unittest.main()
