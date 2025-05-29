"""
Unit tests for the PII detection system in detector.py.

This test suite aims to achieve 99.9% accuracy validation for PII detection
as per the Phase 3 Implementation Roadmap. It will be expanded significantly
as more detection mechanisms (NER, Transformers) and PII types are added.
"""
import pytest
from typing import List

from damien_cli.features.ai_intelligence.llm_integration.privacy.detector import PIIDetector, PIIEntity

# Test cases: (text_to_scan, expected_pii_entities)
# Each PIIEntity in expected_pii_entities should be a tuple:
# (text, entity_type, start_char, end_char, confidence_score_min, detection_method)
# Using confidence_score_min to allow for slight variations if scores become dynamic.
# For regex, confidence is currently fixed.

REGEX_TEST_CASES = [
    # Email Addresses
    ("My email is test@example.com.", [("test@example.com", "EMAIL_ADDRESS", 12, 28, 0.9, "REGEX")]),
    ("Contact us at support@domain.co.uk or sales.team@another-domain.io.", [
        ("support@domain.co.uk", "EMAIL_ADDRESS", 14, 34, 0.9, "REGEX"),
        ("sales.team@another-domain.io", "EMAIL_ADDRESS", 38, 66, 0.9, "REGEX")
    ]),
    ("No email here.", []),
    ("Invalid email test@.com", []), # Simple regex might catch parts, but full validation is complex
    ("Email: name+tag@example.com", [("name+tag@example.com", "EMAIL_ADDRESS", 7, 27, 0.9, "REGEX")]),

    # Phone Numbers (US-centric for now, based on current regex in PIIDetector)
    ("Call me at 555-123-4567.", [("555-123-4567", "PHONE_NUMBER", 11, 23, 0.9, "REGEX")]),
    ("My number is (123) 456-7890.", [("(123) 456-7890", "PHONE_NUMBER", 13, 27, 0.9, "REGEX")]),
    ("Phone: 123.456.7890 or 9876543210", [
        ("123.456.7890", "PHONE_NUMBER", 7, 19, 0.9, "REGEX"),
        ("9876543210", "PHONE_NUMBER", 23, 33, 0.9, "REGEX") # Assuming regex handles no separators
    ]),
    ("Not a phone 123-45-6789", []), # Invalid format based on typical US
    ("Office line: (555)5555555", [("(555)5555555", "PHONE_NUMBER", 13, 26, 0.9, "REGEX")]),

    # Mixed PII
    ("My info: user@host.com, phone (111) 222-3333.", [
        ("user@host.com", "EMAIL_ADDRESS", 10, 23, 0.9, "REGEX"),
        ("(111) 222-3333", "PHONE_NUMBER", 31, 45, 0.9, "REGEX")
    ]),
    ("Empty string", []),
    ("", []),

    # US Social Security Numbers (US_SSN)
    ("Her SSN is 123-45-6789.", [("123-45-6789", "US_SSN", 13, 24, 0.9, "REGEX")]),
    ("SSN: 987-65-4321", [("987-65-4321", "US_SSN", 5, 16, 0.9, "REGEX")]),
    ("No SSN here.", []),

    # Credit Card Numbers (CREDIT_CARD_NUMBER) - Basic patterns
    ("My card is 1234-5678-9012-3456.", [("1234-5678-9012-3456", "CREDIT_CARD_NUMBER", 12, 31, 0.9, "REGEX")]),
    ("Visa: 4111222233334444", [("4111222233334444", "CREDIT_CARD_NUMBER", 6, 22, 0.9, "REGEX")]),
    ("Mastercard: 5100223344556677", [("5100223344556677", "CREDIT_CARD_NUMBER", 12, 28, 0.9, "REGEX")]),
    ("Amex: 340000000000000", [("340000000000000", "CREDIT_CARD_NUMBER", 6, 21, 0.9, "REGEX")]),
    ("Discover: 6011000000000000", [("6011000000000000", "CREDIT_CARD_NUMBER", 10, 26, 0.9, "REGEX")]),
    ("Not a card 12345", []),

    # Basic US Street Address (US_STREET_ADDRESS_BASIC)
    ("Lives at 123 Main St, Anytown.", [("123 Main St", "US_STREET_ADDRESS_BASIC", 9, 20, 0.9, "REGEX")]),
    ("Office: 456 Oak Avenue.", [("456 Oak Avenue", "US_STREET_ADDRESS_BASIC", 8, 22, 0.9, "REGEX")]),
    ("No address here.", []),
    ("10 Downing Street", [("10 Downing Street", "US_STREET_ADDRESS_BASIC", 0, 17, 0.9, "REGEX")]), # Catches this too

    # IP Address V4 (IP_ADDRESS_V4)
    ("Server IP is 192.168.1.1.", [("192.168.1.1", "IP_ADDRESS_V4", 13, 24, 0.9, "REGEX")]),
    ("Localhost: 127.0.0.1", [("127.0.0.1", "IP_ADDRESS_V4", 11, 20, 0.9, "REGEX")]),
    ("Invalid IP 256.0.0.1", []), # Regex should not catch invalid octets

    # MAC Address (MAC_ADDRESS)
    ("MAC address: 00:1A:2B:3C:4D:5E", [("00:1A:2B:3C:4D:5E", "MAC_ADDRESS", 13, 29, 0.9, "REGEX")]),
    ("Another MAC: 01-23-45-67-89-AB", [("01-23-45-67-89-AB", "MAC_ADDRESS", 13, 29, 0.9, "REGEX")]),
    ("Not a MAC 12345", []),
]

# TODO: Add test cases for NER-based detection
NER_TEST_CASES = [
    # ("His name is John Doe and he lives in New York.", [("John Doe", "PERSON", ...), ("New York", "LOCATION", ...)])
]

# TODO: Add test cases for Transformer-based detection
TRANSFORMER_TEST_CASES = [
    # Similar to NER, but potentially more nuanced or context-aware
]

# TODO: Add test cases for multi-language support
MULTI_LANGUAGE_TEST_CASES = [
    # ("Mi correo es prueba@ejemplo.es", [("prueba@ejemplo.es", "EMAIL_ADDRESS", ...)], "es")
]


@pytest.fixture(scope="module")
def pii_detector() -> PIIDetector:
    """Fixture to provide a PIIDetector instance for tests."""
    return PIIDetector(languages=["en"]) # Add more languages as support grows

def compare_pii_lists(found: List[PIIEntity], expected: List[tuple]):
    """
    Compares a list of found PIIEntity objects with a list of expected PII tuples.
    The order of entities does not matter.
    """
    assert len(found) == len(expected), \
        f"Number of PII entities found ({len(found)}) does not match expected ({len(expected)}).\nFound: {found}\nExpected: {expected}"

    # Convert found PIIEntities to a set of comparable tuples
    # (text, entity_type, start_char, end_char, detection_method)
    # We check confidence score separately if needed, or use a range.
    found_set = set()
    for pii in found:
        found_set.add((pii.text, pii.entity_type, pii.start_char, pii.end_char, pii.detection_method))

    expected_set = set()
    for exp_text, exp_type, exp_start, exp_end, exp_confidence_min, exp_method in expected:
        expected_set.add((exp_text, exp_type, exp_start, exp_end, exp_method))
        # Check confidence for each found item that matches the core tuple
        # This is a bit more complex if we match by set.
        # For now, let's assume confidence is part of the PIIEntity and fixed for regex.
        # A more robust check would iterate and match, then check confidence.

    assert found_set == expected_set, \
        f"Found PII entities do not match expected.\nFound: {sorted(list(found_set))}\nExpected: {sorted(list(expected_set))}"

    # Additionally, check confidence scores for exact matches if they are critical
    for pii_obj in found:
        for exp_text, exp_type, exp_start, exp_end, exp_confidence_min, exp_method in expected:
            if (pii_obj.text == exp_text and
                pii_obj.entity_type == exp_type and
                pii_obj.start_char == exp_start and
                pii_obj.end_char == exp_end and
                pii_obj.detection_method == exp_method):
                assert pii_obj.confidence_score >= exp_confidence_min
                break


@pytest.mark.parametrize("text_to_scan, expected_pii_tuples", REGEX_TEST_CASES)
def test_pii_detection_with_regex(pii_detector: PIIDetector, text_to_scan: str, expected_pii_tuples: List[tuple]):
    """
    Tests PII detection using the regex-based method in PIIDetector.
    """
    # Currently, detector.detect() calls _detect_with_regex internally.
    # If we want to test _detect_with_regex in isolation, we might need to make it public
    # or use a friendlier way to invoke only regex part. For now, detect() is fine.
    detected_pii = pii_detector.detect(text_to_scan, language="en")
    compare_pii_lists(detected_pii, expected_pii_tuples)

def test_pii_entity_structure():
    """Tests the structure and attributes of the PIIEntity named tuple."""
    entity = PIIEntity(
        text="test@example.com",
        entity_type="EMAIL",
        start_char=0,
        end_char=16,
        confidence_score=0.95,
        detection_method="REGEX"
    )
    assert entity.text == "test@example.com"
    assert entity.entity_type == "EMAIL"
    assert entity.start_char == 0
    assert entity.end_char == 16
    assert entity.confidence_score == 0.95
    assert entity.detection_method == "REGEX"

@pytest.mark.skip(reason="NER detection not yet implemented in PIIDetector.")
@pytest.mark.parametrize("text_to_scan, expected_pii_tuples", NER_TEST_CASES)
def test_pii_detection_with_ner(pii_detector: PIIDetector, text_to_scan: str, expected_pii_tuples: List[tuple]):
    """
    Tests PII detection using NER models (e.g., spaCy).
    This test will be enabled once NER integration is complete.
    """
    # detected_pii = pii_detector.detect(text_to_scan, language="en") # Assuming detect will use NER
    # compare_pii_lists(detected_pii, expected_pii_tuples)
    pass

@pytest.mark.skip(reason="Transformer-based detection not yet implemented in PIIDetector.")
@pytest.mark.parametrize("text_to_scan, expected_pii_tuples", TRANSFORMER_TEST_CASES)
def test_pii_detection_with_transformer(pii_detector: PIIDetector, text_to_scan: str, expected_pii_tuples: List[tuple]):
    """
    Tests PII detection using Transformer-based models.
    This test will be enabled once Transformer integration is complete.
    """
    # detected_pii = pii_detector.detect(text_to_scan, language="en") # Assuming detect will use Transformers
    # compare_pii_lists(detected_pii, expected_pii_tuples)
    pass

@pytest.mark.skip(reason="Multi-language support beyond basic regex needs full implementation.")
@pytest.mark.parametrize("text_to_scan, expected_pii_tuples, language", MULTI_LANGUAGE_TEST_CASES)
def test_pii_detection_multilanguage(pii_detector_multilang: PIIDetector, text_to_scan: str, expected_pii_tuples: List[tuple], language: str):
    """
    Tests PII detection for multiple languages.
    Requires PIIDetector to be initialized with multi-language models.
    """
    # detector = PIIDetector(languages=["en", "es", ...]) # Setup in a fixture
    # detected_pii = pii_detector_multilang.detect(text_to_scan, language=language)
    # compare_pii_lists(detected_pii, expected_pii_tuples)
    pass

def test_unsupported_language_detection(pii_detector: PIIDetector):
    """
    Tests that the detector handles requests for unsupported languages gracefully.
    """
    with pytest.raises(ValueError, match="Language 'fr' is not supported. Supported: \['en'\]"):
        pii_detector.detect("Ceci est un test.", language="fr")

# Further tests to consider for 99.9% accuracy validation:
# - Edge cases (e.g., PII at the very beginning/end of text, overlapping PII).
# - PII with various formatting and contexts.
# - Texts with no PII (ensure low false positive rate).
# - Very long texts (performance and accuracy).
# - Texts with unusual characters or encodings.
# - False positive tests: strings that look like PII but are not.
# - Tests for confidence scoring logic (once more sophisticated scoring is in place).
# - Tests for the combination of results from different detectors (regex, NER, transformer).

# Example of a false positive test structure:
# FALSE_POSITIVE_CASES = [
#     ("This is version 123.456.7890 of the software.", []), # Looks like a phone number
#     ("The event ID is EMAIL_NOT_A_REAL_ONE.", []),
# ]
# @pytest.mark.parametrize("text_to_scan, expected_pii_tuples", FALSE_POSITIVE_CASES)
# def test_pii_detection_false_positives(pii_detector: PIIDetector, text_to_scan: str, expected_pii_tuples: List[tuple]):
#     detected_pii = pii_detector.detect(text_to_scan, language="en")
#     compare_pii_lists(detected_pii, expected_pii_tuples)

if __name__ == "__main__":
    # This allows running pytest directly on this file if needed
    # pytest.main([__file__])
    # For more controlled execution, run `pytest tests/` from the project root.
    print("Run tests using 'pytest tests/test_pii_detection.py'")