import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from features.ai_intelligence.llm_integration.base import LLMServiceOrchestrator, LLMProvider, BaseLLMService
from features.ai_intelligence.llm_integration.providers.openai_provider import OpenAIProvider
from features.ai_intelligence.llm_integration.providers.anthropic_provider import AnthropicProvider
from features.ai_intelligence.llm_integration.providers.local_provider import LocalLLMProvider

# Mock the core.config.settings for testing purposes
# This allows us to inject different LLM_PROVIDERS_CONFIGURATION values
# without actually needing a .env file or modifying a real config.py during tests.

class MockSettings:
    def __init__(self, llm_providers_config=None):
        self.LLM_PROVIDERS_CONFIGURATION = llm_providers_config if llm_providers_config is not None else {}
        # Mock API keys that might be checked directly by config.py's Settings class __init__
        self.OPENAI_API_KEY = "test_openai_key" if "openai" in self.LLM_PROVIDERS_CONFIGURATION else None
        self.ANTHROPIC_API_KEY = "test_anthropic_key" if "anthropic" in self.LLM_PROVIDERS_CONFIGURATION else None

@patch('features.ai_intelligence.llm_integration.base.OpenAIProvider', MagicMock(spec=OpenAIProvider))
@patch('features.ai_intelligence.llm_integration.base.AnthropicProvider', MagicMock(spec=AnthropicProvider))
@patch('features.ai_intelligence.llm_integration.base.LocalLLMProvider', MagicMock(spec=LocalLLMProvider))
class TestLLMServiceOrchestratorInit(unittest.TestCase):

    def test_init_with_no_config(self):
        print("\nRunning test_init_with_no_config...")
        # Test orchestrator initialization when no config is passed and settings might be empty
        with patch('damien_cli.core.config.settings', MockSettings(llm_providers_config={})):
            orchestrator = LLMServiceOrchestrator(providers_config_map=None) # Simulate loading from (empty) settings
            self.assertEqual(len(orchestrator.providers), 0)
            print("PASS: Orchestrator initialized with no providers when config is empty.")

    def test_init_with_openai_provider(self):
        print("\nRunning test_init_with_openai_provider...")
        config = {
            "openai": {"api_key": "test_key_openai", "default_model": "gpt-test"}
        }
        # Patch the settings that might be accessed by the real config.py if it were imported by base.py
        mock_settings_instance = MockSettings(llm_providers_config=config)
        mock_settings_instance.OPENAI_API_KEY = "test_key_openai"

        with patch('damien_cli.core.config.settings', mock_settings_instance):
             # We pass the config directly to orchestrator to test its _init_providers logic primarily
            orchestrator = LLMServiceOrchestrator(providers_config_map=config)
            self.assertIn(LLMProvider.OPENAI, orchestrator.providers)
            self.assertIsInstance(orchestrator.providers[LLMProvider.OPENAI], MagicMock) # Check it's our mocked class
            # Check if the mocked OpenAIProvider was called with the correct config
            OpenAIProvider.__init__.assert_called_with(config=config["openai"])
            print("PASS: Orchestrator initialized OpenAIProvider correctly.")
            OpenAIProvider.__init__.reset_mock()


    def test_init_with_anthropic_provider(self):
        print("\nRunning test_init_with_anthropic_provider...")
        config = {
            "anthropic": {"api_key": "test_key_anthropic", "default_model": "claude-test"}
        }
        mock_settings_instance = MockSettings(llm_providers_config=config)
        mock_settings_instance.ANTHROPIC_API_KEY = "test_key_anthropic"
        with patch('damien_cli.core.config.settings', mock_settings_instance):
            orchestrator = LLMServiceOrchestrator(providers_config_map=config)
            self.assertIn(LLMProvider.ANTHROPIC, orchestrator.providers)
            self.assertIsInstance(orchestrator.providers[LLMProvider.ANTHROPIC], MagicMock)
            AnthropicProvider.__init__.assert_called_with(config=config["anthropic"])
            print("PASS: Orchestrator initialized AnthropicProvider correctly.")
            AnthropicProvider.__init__.reset_mock()

    def test_init_with_local_provider(self):
        print("\nRunning test_init_with_local_provider...")
        config = {
            "local": {"base_url": "http://localhost:1111", "default_model": "local-test"}
        }
        with patch('damien_cli.core.config.settings', MockSettings(llm_providers_config=config)):
            orchestrator = LLMServiceOrchestrator(providers_config_map=config)
            self.assertIn(LLMProvider.LOCAL, orchestrator.providers)
            self.assertIsInstance(orchestrator.providers[LLMProvider.LOCAL], MagicMock)
            LocalLLMProvider.__init__.assert_called_with(config=config["local"])
            print("PASS: Orchestrator initialized LocalLLMProvider correctly.")
            LocalLLMProvider.__init__.reset_mock()

    def test_init_with_multiple_providers(self):
        print("\nRunning test_init_with_multiple_providers...")
        config = {
            "openai": {"api_key": "test_key_o", "default_model": "gpt-m"},
            "local": {"base_url": "http://local:1234", "default_model": "local-m"}
        }
        mock_settings_instance = MockSettings(llm_providers_config=config)
        mock_settings_instance.OPENAI_API_KEY = "test_key_o"

        with patch('damien_cli.core.config.settings', mock_settings_instance):
            orchestrator = LLMServiceOrchestrator(providers_config_map=config)
            self.assertEqual(len(orchestrator.providers), 2)
            self.assertIn(LLMProvider.OPENAI, orchestrator.providers)
            self.assertIn(LLMProvider.LOCAL, orchestrator.providers)
            OpenAIProvider.__init__.assert_called_with(config=config["openai"])
            LocalLLMProvider.__init__.assert_called_with(config=config["local"])
            print("PASS: Orchestrator initialized multiple providers correctly.")
            OpenAIProvider.__init__.reset_mock()
            LocalLLMProvider.__init__.reset_mock()

    def test_init_with_unknown_provider_key(self):
        print("\nRunning test_init_with_unknown_provider_key...")
        config = {
            "unknown_provider": {"some_setting": "value"}
        }
        # Suppress print warnings for this test
        with patch('sys.stdout', MagicMock()):
            with patch('damien_cli.core.config.settings', MockSettings(llm_providers_config=config)):
                orchestrator = LLMServiceOrchestrator(providers_config_map=config)
                self.assertEqual(len(orchestrator.providers), 0)
        print("PASS: Orchestrator handled unknown provider key gracefully.")

    def test_init_provider_class_not_in_map(self):
        print("\nRunning test_init_provider_class_not_in_map...")
        # Temporarily remove a provider from the class map for this test
        original_map = LLMServiceOrchestrator.PROVIDER_CLASS_MAP
        LLMServiceOrchestrator.PROVIDER_CLASS_MAP = {k: v for k, v in original_map.items() if k != LLMProvider.OPENAI}
        
        config = {"openai": {"api_key": "key", "default_model": "model"}}
        mock_settings_instance = MockSettings(llm_providers_config=config)
        mock_settings_instance.OPENAI_API_KEY = "key"

        with patch('sys.stdout', MagicMock()): # Suppress print warnings
            with patch('damien_cli.core.config.settings', mock_settings_instance):
                orchestrator = LLMServiceOrchestrator(providers_config_map=config)
                self.assertNotIn(LLMProvider.OPENAI, orchestrator.providers)
                self.assertEqual(len(orchestrator.providers), 0)
        
        LLMServiceOrchestrator.PROVIDER_CLASS_MAP = original_map # Restore map
        print("PASS: Orchestrator handled provider class not in map correctly.")


if __name__ == '__main__':
    # To ensure mocks are applied correctly when running directly
    # We need to apply class-level patches here if not using unittest.main() discovery
    # However, unittest.main() handles this.
    unittest.main()