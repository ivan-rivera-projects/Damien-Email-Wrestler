"""Configuration file for pytest."""

import pytest

# This enables the asyncio fixture
pytest_plugins = ["pytest_asyncio"]

# Configure asyncio mode
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as an asyncio coroutine")
