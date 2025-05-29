"""
Module docstring explaining purpose and usage.

This module implements the ReversibleTokenizer, responsible for
generating unique, reversible tokens for detected Personally Identifiable
Information (PII). This allows PII to be replaced with non-sensitive
placeholders during processing and later restored if necessary.

Example:
    >>> from damien_cli.features.ai_intelligence.llm_integration.privacy.tokenizer import ReversibleTokenizer
    >>> from damien_cli.features.ai_intelligence.llm_integration.privacy.detector import PIIEntity # Assuming PIIEntity structure
    >>> tokenizer = ReversibleTokenizer()
    >>> text = "My email is test@example.com and my phone is 123-456-7890."
    >>> pii_entities = [
    ...     PIIEntity("test@example.com", "EMAIL_ADDRESS", 14, 30, 0.99, "REGEX"),
    ...     PIIEntity("123-456-7890", "PHONE_NUMBER", 48, 60, 0.95, "REGEX")
    ... ]
    >>> tokenized_text, token_map = tokenizer.tokenize_pii(text, pii_entities)
    >>> print(f"Tokenized: {tokenized_text}")
    >>> print(f"Token Map: {token_map}")
    >>> detokenized_text = tokenizer.detokenize_text(tokenized_text, token_map)
    >>> print(f"Detokenized: {detokenized_text}")

Note:
    The tokenization process must be deterministic and secure.
    Future enhancements will include secure token storage, automatic
    expiration, and batch operation support as per architectural specifications.
"""
from typing import List, Dict, Tuple, Set, Optional
import uuid
import hashlib # For deterministic token generation based on value if needed

# Assuming PIIEntity is defined in detector.py as it was in previous steps
from .detector import PIIEntity

class ReversibleTokenizer:
    """
    Handles the tokenization of PII and detokenization back to original values.

    This class is designed to:
    - Generate unique and deterministic tokens for PII entities.
    - Maintain a mapping between tokens and their original PII values.
    - Allow for the reconstruction of original text from its tokenized version.

    Future considerations based on architectural specifications:
    - Secure token-to-value mapping (e.g., using a secure vault or database).
    - Automatic token expiration policies.
    - Support for batch tokenization/detokenization operations.
    """

    def __init__(self):
        """
        Initializes the ReversibleTokenizer.
        
        The internal token store (`self.token_value_store`) is a simplified
        in-memory store for demonstration. In a production system, this would
        be replaced by a secure and persistent storage mechanism.
        """
        self.token_value_store: Dict[str, str] = {} # token -> original_value

    def _generate_token(self, pii_entity: PIIEntity) -> str:
        """
        Generates a unique token for a given PII entity.

        The token format is [ENTITY_TYPE_UUID].
        This ensures tokens are somewhat descriptive while remaining unique.
        A more robust system might involve a dedicated token management service.

        Args:
            pii_entity (PIIEntity): The PII entity to generate a token for.

        Returns:
            str: A unique token string.
        """
        unique_id = uuid.uuid4().hex[:8] # Shortened UUID for readability
        token = f"[{pii_entity.entity_type.upper()}_{unique_id}]"
        return token

    def tokenize_pii(self, text: str, pii_entities: List[PIIEntity]) -> Tuple[str, Dict[str, str]]:
        """
        Replaces detected PII in a text string with unique tokens.

        Args:
            text (str): The original text string.
            pii_entities (List[PIIEntity]): A list of PIIEntity objects detected in the text.
                                            Entities should be sorted by start_char to avoid
                                            issues with index changes during replacement.

        Returns:
            Tuple[str, Dict[str, str]]:
                - The text string with PII replaced by tokens.
                - A map where keys are tokens and values are the original PII strings.
        """
        token_map: Dict[str, str] = {}
        sorted_entities = sorted(pii_entities, key=lambda p: p.start_char, reverse=True)

        modified_text = text
        for entity in sorted_entities:
            token = self._generate_token(entity)
            
            self.token_value_store[token] = entity.text
            token_map[token] = entity.text
            
            modified_text = modified_text[:entity.start_char] + token + modified_text[entity.end_char:]
            
        return modified_text, token_map

    def detokenize_text(self, tokenized_text: str, token_map: Optional[Dict[str, str]] = None) -> str:
        """
        Replaces tokens in a text string with their original PII values.

        Args:
            tokenized_text (str): The text string containing tokens.
            token_map (Optional[Dict[str, str]]): A map of tokens to their original PII values.
                                         If None, uses the tokenizer's internal store.
                                         Providing this allows detokenization of text
                                         tokenized in a specific context/run.

        Returns:
            str: The text string with tokens replaced by their original PII values.
        """
        current_map = token_map if token_map is not None else self.token_value_store
        
        detokenized_text = tokenized_text
        for token in sorted(current_map.keys(), key=len, reverse=True):
            if token in detokenized_text:
                detokenized_text = detokenized_text.replace(token, current_map[token])
        return detokenized_text

    def get_original_value(self, token: str) -> Optional[str]:
        """
        Retrieves the original PII value for a given token.

        Args:
            token (str): The token to look up.

        Returns:
            Optional[str]: The original PII value if the token is found, otherwise None.
        """
        return self.token_value_store.get(token)

    def clear_token_store(self):
        """
        Clears the internal token-value store.
        
        Caution: This will make previously tokenized text using this instance's
        store non-detokenizable unless the token_map was preserved externally.
        """
        self.token_value_store.clear()

if __name__ == '__main__':
    # Example Usage
    tokenizer = ReversibleTokenizer()

    sample_pii_entities = [
        PIIEntity(text="john.doe@example.com", entity_type="EMAIL_ADDRESS", start_char=18, end_char=38, confidence_score=0.99, detection_method="REGEX"),
        PIIEntity(text="secretpass", entity_type="PASSWORD_GUESS", start_char=54, end_char=64, confidence_score=0.7, detection_method="PATTERN"),
        PIIEntity(text="john.doe@example.com", entity_type="EMAIL_ADDRESS", start_char=80, end_char=100, confidence_score=0.98, detection_method="REGEX"),
    ]
    original_text = "Contact details: john.doe@example.com, password might be secretpass. Repeat: john.doe@example.com."

    print(f"Original Text: {original_text}")

    tokenized_text, local_token_map = tokenizer.tokenize_pii(original_text, sample_pii_entities)
    print(f"\nTokenized Text: {tokenized_text}")
    print(f"Local Token Map: {local_token_map}")

    detokenized_text = tokenizer.detokenize_text(tokenized_text, local_token_map)
    print(f"\nDetokenized Text (using local map): {detokenized_text}")

    assert original_text == detokenized_text, "Detokenization failed!"
    print("\nTokenization and detokenization successful.")

    if local_token_map:
        a_token = list(local_token_map.keys())[0]
        original_val = tokenizer.get_original_value(a_token)
        print(f"\nOriginal value for token '{a_token}': {original_val}")

    tokenizer.clear_token_store()
    print(f"\nCleared internal token store. Size: {len(tokenizer.token_value_store)}")