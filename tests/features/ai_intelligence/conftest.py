
import pytest
from unittest.mock import patch, MagicMock

# Create a mock for torch to avoid the dependency on the actual library
# This helps tests run without needing the real PyTorch
class MockTorch:
    class device:
        def __init__(self, *args, **kwargs):
            pass
            
    @staticmethod
    def tensor(*args, **kwargs):
        return MagicMock()
        
    class cuda:
        @staticmethod
        def is_available():
            return False
            
    @staticmethod
    def get_default_device():
        return "cpu"
        
    class _C:
        @staticmethod
        def _get_default_device():
            return "cpu"

# Create a mock for SentenceTransformer
class MockSentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass
        
    def encode(self, *args, **kwargs):
        return MagicMock()

@pytest.fixture(autouse=True)
def mock_torch():
    """Mock torch library for tests"""
    with patch.dict('sys.modules', {'torch': MockTorch()}):
        yield

@pytest.fixture(autouse=True)
def mock_sentence_transformers():
    """Mock sentence_transformers library for tests"""
    mock_st = MagicMock()
    mock_st.SentenceTransformer = MockSentenceTransformer
    mock_st.util.cos_sim = lambda x, y: MagicMock()
    
    with patch.dict('sys.modules', {'sentence_transformers': mock_st}):
        yield
