import sys
import os
import unittest # Using unittest for more structured tests

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from features.ai_intelligence.llm_integration.context_optimizer import ContextItem, ContextWindowOptimizer

class TestContextWindowOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = ContextWindowOptimizer(max_tokens=1000) # Default max_tokens for optimizer
        # Default reserved_tokens is 2000, so target_tokens for context is -1000 if not overridden.
        # Let's use a more realistic scenario for testing optimize_context.
        self.optimizer.reserved_tokens = 200 # Allow 800 for context

    def test_optimize_context_basic_selection(self):
        print("\nRunning test_optimize_context_basic_selection...")
        items = [
            ContextItem("item1", 0.9, 300, "catA", {}),
            ContextItem("item2", 0.8, 300, "catB", {}),
            ContextItem("item3", 0.7, 300, "catC", {}), # This one should be dropped
        ]
        # Target tokens for context = 1000 (optimizer.max_tokens) - 200 (optimizer.reserved_tokens) = 800
        selected = self.optimizer.optimize_context(items, target_tokens=700) # Explicitly set target for clarity
        self.assertEqual(len(selected), 2)
        self.assertIn(items[0], selected)
        self.assertIn(items[1], selected)
        print(f"Selected items: {[item.content for item in selected]}")

    def test_optimize_context_with_required_items(self):
        print("\nRunning test_optimize_context_with_required_items...")
        required = ContextItem("required_item", 1.0, 200, "catR", {})
        items = [
            ContextItem("item1", 0.9, 300, "catA", {}),
            ContextItem("item2", 0.8, 300, "catB", {}), # Available space = 700 - 200 (required) = 500. item2 (300) won't fit with item1 (300)
        ]
        selected = self.optimizer.optimize_context(items, required_items=[required], target_tokens=700)
        self.assertEqual(len(selected), 2) # required_item + item1
        self.assertIn(required, selected)
        self.assertIn(items[0], selected)
        print(f"Selected items: {[item.content for item in selected]}")

    def test_optimize_context_priority_and_diversity(self):
        print("\nRunning test_optimize_context_priority_and_diversity...")
        items = [
            ContextItem("high_priority_catA_1", 0.9, 200, "catA", {}),
            ContextItem("low_priority_catA_2", 0.5, 200, "catA", {}), # Should be skipped for diversity if catB fits
            ContextItem("medium_priority_catB_1", 0.7, 200, "catB", {}),
            ContextItem("high_priority_catC_1", 0.95, 250, "catC", {}),
        ]
        # Target 700.
        # Expected: high_priority_catC_1 (250), high_priority_catA_1 (200), medium_priority_catB_1 (200). Total 650.
        selected = self.optimizer.optimize_context(items, target_tokens=700)
        self.assertEqual(len(selected), 3)
        selected_contents = [item.content for item in selected]
        self.assertIn("high_priority_catC_1", selected_contents)
        self.assertIn("high_priority_catA_1", selected_contents)
        self.assertIn("medium_priority_catB_1", selected_contents)
        print(f"Selected items for diversity: {selected_contents}")

    def test_create_sliding_window_no_overlap(self):
        print("\nRunning test_create_sliding_window_no_overlap...")
        emails = [{"id": i} for i in range(5)] # 5 emails
        windows = self.optimizer.create_sliding_window(emails, window_size=2, overlap=0)
        self.assertEqual(len(windows), 3) # [[0,1], [2,3], [4]]
        self.assertEqual([w[0]["id"] for w in windows if w], [0, 2, 4])
        print(f"Windows (no overlap): {windows}")

    def test_create_sliding_window_with_overlap(self):
        print("\nRunning test_create_sliding_window_with_overlap...")
        emails = [{"id": i} for i in range(5)]
        windows = self.optimizer.create_sliding_window(emails, window_size=3, overlap=1)
        # Iter 1: i=0, emails[0:3] -> [[0,1,2]]
        # Iter 2: i=2 (0 + 3-1), emails[2:5] -> [[0,1,2], [2,3,4]]
        # Iter 3: i=4 (2 + 3-1), emails[4:7] -> [[0,1,2], [2,3,4], [4]]
        self.assertEqual(len(windows), 3)
        self.assertEqual([w[0]["id"] for w in windows if w], [0, 2, 4])
        print(f"Windows (with overlap): {windows}")
        
    def test_create_sliding_window_small_list(self):
        print("\nRunning test_create_sliding_window_small_list...")
        emails = [{"id": i} for i in range(2)] # 2 emails
        windows = self.optimizer.create_sliding_window(emails, window_size=3, overlap=1)
        self.assertEqual(len(windows), 1)
        self.assertEqual(len(windows[0]), 2)
        print(f"Windows (small list): {windows}")

    def test_compress_email_content_no_compression(self):
        print("\nRunning test_compress_email_content_no_compression...")
        email = {"content": "Short email."}
        compressed = self.optimizer.compress_email_content(email, target_length=100)
        self.assertEqual(compressed, "Short email.")
        print(f"Compressed (no change): '{compressed}'")

    def test_compress_email_content_with_compression(self):
        print("\nRunning test_compress_email_content_with_compression...")
        long_text = "This is a very long email content that definitely exceeds the target length. " * 10
        email = {"content": long_text}
        compressed = self.optimizer.compress_email_content(email, target_length=50)
        self.assertTrue(len(compressed) <= 50)
        self.assertTrue(compressed.endswith("..."))
        print(f"Compressed (truncated): '{compressed}'")

    def test_compress_email_content_with_priority_patterns(self):
        print("\nRunning test_compress_email_content_with_priority_patterns...")
        content = (
            "Normal line 1.\n"
            "ACTION REQUIRED: Please review this document by EOD.\n"
            "Normal line 2.\n"
            "Another normal line here that is quite long and might be truncated if not for priority.\n"
            "Deadline: Tomorrow. This is important.\n"
            "Final normal line."
        ) # Approx 250 chars
        email = {"content": content}
        # Target length forces some truncation, but priority lines should be kept.
        compressed = self.optimizer.compress_email_content(email, target_length=100) 
        self.assertIn("ACTION REQUIRED", compressed)
        self.assertIn("Deadline: Tomorrow", compressed)
        self.assertTrue(len(compressed) <= 100)
        print(f"Compressed (priority): '{compressed}'")

if __name__ == '__main__':
    unittest.main()