import sys
import os

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from damien_cli.features.ai_intelligence.llm_integration.utils import TokenCounter

def run_tests():
    print("Testing TokenCounter functionality...")
    counter = TokenCounter()

    test_cases = [
        {"text": "Hello world", "model": "gpt-3.5-turbo", "expected_tokens": 2, "description": "Simple sentence with gpt-3.5-turbo"},
        {"text": "Hello world", "model": "gpt-4", "expected_tokens": 2, "description": "Simple sentence with gpt-4"},
        {"text": "こんにちは世界", "model": "gpt-3.5-turbo", "expected_tokens": 4, "description": "Japanese sentence with gpt-3.5-turbo"}, # Updated to actual tiktoken output
        {"text": "This is a slightly longer sentence for testing tokenization.", "model": "gpt-3.5-turbo", "expected_tokens": 11, "description": "Longer sentence"},
        {"text": "", "model": "gpt-3.5-turbo", "expected_tokens": 0, "description": "Empty string"},
        {"text": "Test with a\nnewline character.", "model": "gpt-3.5-turbo", "expected_tokens": 7, "description": "String with newline"},
        {"text": "ModelNotInTiktokenLib", "model": "custom-model-x", "expected_tokens": 7, "description": "Fallback encoding test"}, # Updated to actual tiktoken output for cl100k_base
    ]

    all_passed = True
    for i, case in enumerate(test_cases):
        print(f"\nRunning Test Case {i+1}: {case['description']}")
        try:
            actual_tokens = counter.count(case["text"], model_name=case["model"])
            if actual_tokens == case["expected_tokens"]:
                print(f"PASS: Text: '{case['text']}', Model: {case['model']}, Expected: {case['expected_tokens']}, Got: {actual_tokens}")
            else:
                print(f"FAIL: Text: '{case['text']}', Model: {case['model']}, Expected: {case['expected_tokens']}, Got: {actual_tokens}")
                all_passed = False
        except Exception as e:
            print(f"ERROR during test case {i+1}: {e}")
            all_passed = False

    if all_passed:
        print("\nAll TokenCounter tests passed!")
    else:
        print("\nSome TokenCounter tests FAILED.")

if __name__ == "__main__":
    run_tests()