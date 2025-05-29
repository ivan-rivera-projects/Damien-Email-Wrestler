import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the Settings class definition, not the instance
from damien_cli.core.config import Settings
from damien_cli.features.ai_intelligence.llm_integration.base import LLMServiceOrchestrator, LLMRequest, LLMProvider

async def run_connectivity_tests():
    # Explicitly load .env from the root for this test script
    # This path assumes tests/test_connectivity.py is in damien-cli/tests/
    # So, ../../.env should point to the workspace root .env
    root_dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(root_dotenv_path):
        load_dotenv(dotenv_path=root_dotenv_path, override=True)
        print(f"Connectivity Test: Loaded .env from {root_dotenv_path}")
    else:
        print(f"Connectivity Test: Root .env file not found at {root_dotenv_path}. Relying on system env vars.")

    # Instantiate Settings locally for this test
    try:
        local_settings = Settings()
        print("Connectivity Test: Successfully instantiated local_settings.")
        print(f"Loaded OpenAI Key: {'SET' if local_settings.openai_api_key else 'NOT SET'}")
        print(f"Loaded Anthropic Key: {'SET' if local_settings.anthropic_api_key else 'NOT SET'}")
        print(f"OpenAI default model from local_settings: {local_settings.LLM_PROVIDERS_CONFIGURATION.get('openai', {}).get('default_model')}")
        print(f"Anthropic default model from local_settings: {local_settings.LLM_PROVIDERS_CONFIGURATION.get('anthropic', {}).get('default_model')}")
    except Exception as e:
        print(f"Error instantiating Settings locally in test: {e}")
        return

    print("\nInitializing LLMServiceOrchestrator with local_settings...")
    try:
        # Pass the configuration from our locally instantiated settings
        orchestrator = LLMServiceOrchestrator(providers_config_map=local_settings.LLM_PROVIDERS_CONFIGURATION)
    except Exception as e:
        print(f"Error initializing LLMServiceOrchestrator: {e}")
        return

    if not orchestrator.providers:
        print("No providers were initialized in the orchestrator. Check config and .env file.")
        return

    # Test OpenAI
    if LLMProvider.OPENAI in orchestrator.providers:
        print("\n--- Testing OpenAI Connectivity ---")
        openai_request = LLMRequest(
            prompt="Translate 'hello world' to French."
        )
        try:
            # Use local_settings for checking model name for print statement
            openai_model_to_test = local_settings.LLM_PROVIDERS_CONFIGURATION.get('openai', {}).get('default_model', 'unknown_openai_model')
            print(f"Sending request to OpenAI (model: {openai_model_to_test})...")
            response = await orchestrator.process(openai_request, preferred_provider=LLMProvider.OPENAI)
            print(f"OpenAI Response Content: {response.content}")
            print(f"OpenAI Model Used: {response.model}")
            print(f"OpenAI Usage: {response.usage}")
        except Exception as e:
            print(f"Error during OpenAI test: {e}")
    else:
        print("\nOpenAI provider not configured or enabled in local_settings.")

    # Test Anthropic
    if LLMProvider.ANTHROPIC in orchestrator.providers:
        print("\n--- Testing Anthropic Connectivity ---")
        anthropic_request = LLMRequest(
            prompt="Translate 'hello world' to Spanish."
        )
        try:
            anthropic_model_to_test = local_settings.LLM_PROVIDERS_CONFIGURATION.get('anthropic', {}).get('default_model', 'unknown_anthropic_model')
            print(f"Sending request to Anthropic (model: {anthropic_model_to_test})...")
            response = await orchestrator.process(anthropic_request, preferred_provider=LLMProvider.ANTHROPIC)
            print(f"Anthropic Response Content: {response.content}")
            print(f"Anthropic Model Used: {response.model}")
            print(f"Anthropic Usage: {response.usage}")
        except Exception as e:
            print(f"Error during Anthropic test: {e}")
    else:
        print("\nAnthropic provider not configured or enabled in local_settings.")


if __name__ == "__main__":
    # Instantiate settings here just for the pre-flight check
    temp_settings_for_check = Settings()
    if not temp_settings_for_check.openai_api_key and not temp_settings_for_check.anthropic_api_key:
        print("Neither openai_api_key nor anthropic_api_key seem to be loaded from your .env file for pre-flight check.")
        print("Connectivity tests will likely fail for configured providers.")
    elif not temp_settings_for_check.openai_api_key:
        print("Warning (pre-flight): openai_api_key is not set. OpenAI test will fail if provider is enabled.")
    elif not temp_settings_for_check.anthropic_api_key:
        print("Warning (pre-flight): anthropic_api_key is not set. Anthropic test will fail if provider is enabled.")
        
    asyncio.run(run_connectivity_tests())