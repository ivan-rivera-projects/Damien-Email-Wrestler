import sys
import os

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from damien_cli.features.ai_intelligence.llm_integration.base import LLMRequest, LLMResponse, LLMProvider

def run_test():
    print("Testing LLMRequest instantiation...")
    try:
        request = LLMRequest(
            prompt="This is a test prompt.",
            system_prompt="System prompt for testing.",
            max_tokens=100,
            temperature=0.7,
            metadata={"test_id": "req_001"}
        )
        print(f"LLMRequest created successfully: {request}")
    except Exception as e:
        print(f"Error creating LLMRequest: {e}")

    print("\nTesting LLMResponse instantiation...")
    try:
        response = LLMResponse(
            content="This is a test response content.",
            model="test-model-v1",
            provider=LLMProvider.OPENAI,
            usage={'prompt_tokens': 50, 'completion_tokens': 50, 'total_tokens': 100, 'estimated_cost': 0.001},
            latency_ms=500.0,
            finish_reason="stop",
            metadata={"test_id": "res_001"}
        )
        print(f"LLMResponse created successfully: {response}")
    except Exception as e:
        print(f"Error creating LLMResponse: {e}")

if __name__ == "__main__":
    run_test()