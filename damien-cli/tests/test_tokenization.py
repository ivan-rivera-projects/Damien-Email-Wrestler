"""
Unit tests for the ReversibleTokenizer in tokenizer.py.

This test suite focuses on ensuring the tokenizer can correctly replace PII
with tokens and perfectly reverse the process to reconstruct the original text.
It also tests the management of the token store.
"""
import pytest

from damien_cli.features.ai_intelligence.llm_integration.privacy.tokenizer import ReversibleTokenizer
from damien_cli.features.ai_intelligence.llm_integration.privacy.detector import PIIEntity # Used by tokenizer

@pytest.fixture
def tokenizer() -> ReversibleTokenizer:
    """Fixture to provide a fresh ReversibleTokenizer instance for each test."""
    return ReversibleTokenizer()

def test_tokenize_single_pii(tokenizer: ReversibleTokenizer):
    """Tests tokenization of a single PII entity."""
    text = "My email is test@example.com."
    pii_entities = [
        PIIEntity(text="test@example.com", entity_type="EMAIL_ADDRESS", start_char=12, end_char=28, confidence_score=0.99, detection_method="REGEX")
    ]
    tokenized_text, token_map = tokenizer.tokenize_pii(text, pii_entities)

    assert tokenized_text != text
    assert "test@example.com" not in tokenized_text
    assert len(token_map) == 1
    
    token = list(token_map.keys())[0]
    assert token in tokenized_text
    assert token_map[token] == "test@example.com"
    assert tokenizer.get_original_value(token) == "test@example.com"

def test_detokenize_single_pii(tokenizer: ReversibleTokenizer):
    """Tests detokenization of a single PII token."""
    original_text = "My email is test@example.com."
    pii_entities = [
        PIIEntity(text="test@example.com", entity_type="EMAIL_ADDRESS", start_char=12, end_char=28, confidence_score=0.99, detection_method="REGEX")
    ]
    tokenized_text, token_map = tokenizer.tokenize_pii(original_text, pii_entities)
    
    detokenized_text = tokenizer.detokenize_text(tokenized_text, token_map)
    assert detokenized_text == original_text

def test_tokenize_multiple_pii(tokenizer: ReversibleTokenizer):
    """Tests tokenization of multiple PII entities in a single string."""
    text = "Email: user@example.com, Phone: 123-456-7890."
    pii_entities = [
        PIIEntity(text="user@example.com", entity_type="EMAIL_ADDRESS", start_char=7, end_char=23, confidence_score=0.99, detection_method="REGEX"),
        PIIEntity(text="123-456-7890", entity_type="PHONE_NUMBER", start_char=32, end_char=44, confidence_score=0.95, detection_method="REGEX")
    ]
    tokenized_text, token_map = tokenizer.tokenize_pii(text, pii_entities)

    assert "user@example.com" not in tokenized_text
    assert "123-456-7890" not in tokenized_text
    assert len(token_map) == 2

    # Check that both tokens are in the text and map correctly
    original_values_from_map = set(token_map.values())
    assert "user@example.com" in original_values_from_map
    assert "123-456-7890" in original_values_from_map

    for token, original_value in token_map.items():
        assert token in tokenized_text
        assert tokenizer.get_original_value(token) == original_value

def test_detokenize_multiple_pii(tokenizer: ReversibleTokenizer):
    """Tests detokenization of multiple PII tokens."""
    original_text = "Email: user@example.com, Phone: 123-456-7890."
    pii_entities = [
        PIIEntity(text="user@example.com", entity_type="EMAIL_ADDRESS", start_char=7, end_char=23, confidence_score=0.99, detection_method="REGEX"),
        PIIEntity(text="123-456-7890", entity_type="PHONE_NUMBER", start_char=32, end_char=44, confidence_score=0.95, detection_method="REGEX")
    ]
    tokenized_text, token_map = tokenizer.tokenize_pii(original_text, pii_entities)
    
    detokenized_text = tokenizer.detokenize_text(tokenized_text, token_map)
    assert detokenized_text == original_text

def test_tokenize_no_pii(tokenizer: ReversibleTokenizer):
    """Tests tokenization when no PII entities are provided."""
    text = "This string has no PII."
    pii_entities = []
    tokenized_text, token_map = tokenizer.tokenize_pii(text, pii_entities)

    assert tokenized_text == text
    assert len(token_map) == 0

def test_detokenize_no_tokens(tokenizer: ReversibleTokenizer):
    """Tests detokenization when the text contains no known tokens."""
    text = "This string has no tokens."
    token_map = {"[SOME_TOKEN_123]": "some_value"} # A map with a token not in text
    
    detokenized_text = tokenizer.detokenize_text(text, token_map)
    assert detokenized_text == text

    detokenized_text_no_map = tokenizer.detokenize_text(text) # No map provided
    assert detokenized_text_no_map == text


def test_tokenize_empty_string(tokenizer: ReversibleTokenizer):
    """Tests tokenization of an empty string."""
    text = ""
    pii_entities = []
    tokenized_text, token_map = tokenizer.tokenize_pii(text, pii_entities)
    assert tokenized_text == ""
    assert len(token_map) == 0

def test_detokenize_empty_string(tokenizer: ReversibleTokenizer):
    """Tests detokenization of an empty string."""
    text = ""
    token_map = {}
    detokenized_text = tokenizer.detokenize_text(text, token_map)
    assert detokenized_text == ""

def test_token_uniqueness_for_repeated_pii_values(tokenizer: ReversibleTokenizer):
    """
    Tests that different instances of the same PII value get unique tokens
    because tokens are generated with UUIDs.
    """
    text = "Email: repeat@example.com. Again: repeat@example.com."
    pii_entities = [
        PIIEntity(text="repeat@example.com", entity_type="EMAIL_ADDRESS", start_char=7, end_char=25, confidence_score=0.99, detection_method="REGEX"),
        PIIEntity(text="repeat@example.com", entity_type="EMAIL_ADDRESS", start_char=35, end_char=53, confidence_score=0.99, detection_method="REGEX")
    ]
    tokenized_text, token_map = tokenizer.tokenize_pii(text, pii_entities)

    assert len(token_map) == 2 # Two unique tokens
    tokens = list(token_map.keys())
    assert tokens[0] != tokens[1] # Tokens should be different
    assert token_map[tokens[0]] == "repeat@example.com"
    assert token_map[tokens[1]] == "repeat@example.com"
    
    # Ensure both unique tokens are in the text
    assert tokens[0] in tokenized_text
    assert tokens[1] in tokenized_text

    detokenized_text = tokenizer.detokenize_text(tokenized_text, token_map)
    assert detokenized_text == text

def test_token_reversibility_complex_case(tokenizer: ReversibleTokenizer):
    """A more complex reversibility test with multiple PIIs, some repeated."""
    original_text = "User: user1@test.com, Pass: secret1, User: user2@test.com, Note: user1@test.com again."
    pii_entities = [
        PIIEntity(text="user1@test.com", entity_type="EMAIL", start_char=6, end_char=20, confidence_score=0.9, detection_method="REGEX"),
        PIIEntity(text="secret1", entity_type="PASSWORD_GUESS", start_char=28, end_char=35, confidence_score=0.7, detection_method="PATTERN"),
        PIIEntity(text="user2@test.com", entity_type="EMAIL", start_char=43, end_char=57, confidence_score=0.9, detection_method="REGEX"),
        PIIEntity(text="user1@test.com", entity_type="EMAIL", start_char=65, end_char=79, confidence_score=0.9, detection_method="REGEX"),
    ]
    
    tokenized_text, token_map = tokenizer.tokenize_pii(original_text, pii_entities)
    assert len(token_map) == 4 # Each PII instance gets a unique token
    
    detokenized_text = tokenizer.detokenize_text(tokenized_text, token_map)
    assert detokenized_text == original_text

def test_get_original_value(tokenizer: ReversibleTokenizer):
    """Tests retrieving original value for a known token."""
    text = "Tokenize this: value1."
    pii_entities = [PIIEntity("value1", "GENERIC_PII", 15, 21, 0.8, "CUSTOM")]
    _, token_map = tokenizer.tokenize_pii(text, pii_entities)
    
    token = list(token_map.keys())[0]
    assert tokenizer.get_original_value(token) == "value1"
    assert tokenizer.get_original_value("UNKNOWN_TOKEN_XYZ") is None

def test_clear_token_store(tokenizer: ReversibleTokenizer):
    """Tests clearing the internal token store."""
    text = "Data: data@example.com"
    pii_entities = [PIIEntity("data@example.com", "EMAIL", 6, 22, 0.9, "REGEX")]
    tokenized_text, token_map = tokenizer.tokenize_pii(text, pii_entities)
    
    token = list(token_map.keys())[0]
    assert tokenizer.get_original_value(token) == "data@example.com" # Token is in store

    tokenizer.clear_token_store()
    assert tokenizer.get_original_value(token) is None # Token should no longer be in store
    
    # Detokenization using the instance's store should fail or not change text if token not found
    detokenized_after_clear = tokenizer.detokenize_text(tokenized_text) # No explicit map
    assert detokenized_after_clear == tokenized_text # Token not found in cleared store

    # Detokenization with the original map should still work
    detokenized_with_map_after_clear = tokenizer.detokenize_text(tokenized_text, token_map)
    assert detokenized_with_map_after_clear == text


def test_detokenization_with_overlapping_token_names_uses_longest_match(tokenizer: ReversibleTokenizer):
    """
    Tests that if tokens could be substrings of each other (unlikely with UUIDs, but good to test logic),
    the detokenizer replaces the longest match first.
    The current ReversibleTokenizer sorts tokens by length (desc) before replacing.
    """
    # Manually construct a scenario, as UUID tokens won't naturally overlap like this.
    # This tests the robustness of the detokenize_text replacement order.
    token_short = "[EMAIL_1]"
    token_long = "[EMAIL_1_EXTRA]"
    
    tokenizer.token_value_store[token_short] = "short@example.com"
    tokenizer.token_value_store[token_long] = "long_extra@example.com"
    
    text_with_long_token = f"Data: {token_long} and some other text."
    expected_detokenized_long = "Data: long_extra@example.com and some other text."
    assert tokenizer.detokenize_text(text_with_long_token) == expected_detokenized_long
    
    text_with_short_token = f"Data: {token_short} and some other text."
    expected_detokenized_short = "Data: short@example.com and some other text."
    assert tokenizer.detokenize_text(text_with_short_token) == expected_detokenized_short

    text_with_both = f"Data: {token_long} and {token_short}."
    expected_detokenized_both = "Data: long_extra@example.com and short@example.com."
    assert tokenizer.detokenize_text(text_with_both) == expected_detokenized_both


if __name__ == "__main__":
    pytest.main([__file__])