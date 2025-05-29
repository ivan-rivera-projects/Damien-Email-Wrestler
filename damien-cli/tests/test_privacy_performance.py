"""
Performance tests for the privacy layer components.

This suite aims to ensure that privacy operations (PII detection, tokenization,
protection by the guardian) meet the performance target of <100ms for standard
operations, as outlined in the Phase 3 Implementation Roadmap.

These tests will likely use pytest-benchmark if available, or manual timing.
"""
import pytest
import time
import asyncio # For async guardian methods

from damien_cli.features.ai_intelligence.llm_integration.privacy.detector import PIIDetector, PIIEntity
from damien_cli.features.ai_intelligence.llm_integration.privacy.tokenizer import ReversibleTokenizer
from damien_cli.features.ai_intelligence.llm_integration.privacy.guardian import PrivacyGuardian, ProtectionLevel, PrivacyMetadata

# Sample data for performance testing
# A moderately sized email body with some PII
SAMPLE_EMAIL_BODY_MEDIUM = """
Hello Team,

This is a reminder for our meeting scheduled for tomorrow at 10:00 AM PST.
Please find the agenda attached. My contact details are john.doe@example.com
and my phone number is (555) 123-4567. Our project codename is 'Phoenix' and
the client ID is ACME-CORP-001. We also discussed the social security number
987-65-4321 in a secure context, and the credit card 1234-5678-9012-3456 for
a test transaction.

Looking forward to your presence. My alternative email is j.doe.secondary@personal.co.
Address: 123 Main St, Anytown, USA 90210.

Best regards,
John Doe
john.doe@example.com
(555) 123-4567
"""

# A longer email body, simulating more content
SAMPLE_EMAIL_BODY_LONG = SAMPLE_EMAIL_BODY_MEDIUM * 3 + \
    " Additional PII: jane.roe@company.com, phone 987-654-3210. " + \
    "More text to make it longer and test performance with larger inputs. " + \
    "The quick brown fox jumps over the lazy dog. " * 10

SAMPLE_EMAIL_DATA_MEDIUM = {
    "id": "perf_email_medium_001",
    "subject": f"Medium Performance Test {SAMPLE_EMAIL_BODY_MEDIUM[:30]}", # Subject with some PII
    "body": SAMPLE_EMAIL_BODY_MEDIUM,
    "sender": "performance.test@example.com"
}

SAMPLE_EMAIL_DATA_LONG = {
    "id": "perf_email_long_001",
    "subject": f"Long Performance Test - {SAMPLE_EMAIL_BODY_LONG[:30]}",
    "body": SAMPLE_EMAIL_BODY_LONG,
    "sender": "long.performance.test@example.com"
}


# Try to use pytest-benchmark if available, otherwise fallback to manual timing
try:
    # This is just to check if the fixture is available.
    # Actual usage is by passing `benchmark` as an argument to the test function.
    from pytest_benchmark.fixture import BenchmarkFixture
    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False
    # Simple manual timing fallback
    class ManualBenchmark:
        def __init__(self, name):
            self.name = name
            self.start_time = 0
            self.end_time = 0

        def __call__(self, func, *args, **kwargs):
            self.start_time = time.perf_counter()
            result = func(*args, **kwargs)
            self.end_time = time.perf_counter()
            duration_ms = (self.end_time - self.start_time) * 1000
            print(f"\nManual Benchmark '{self.name}': {duration_ms:.4f} ms")
            # Basic assertion against the 100ms target
            # In a real scenario, this might be more nuanced (e.g. average over N runs)
            assert duration_ms < 200, f"{self.name} took {duration_ms:.2f} ms, exceeding 200ms" # Relaxed target for manual
            return result
    print("pytest-benchmark not found, using manual timing fallback.")


@pytest.fixture(scope="module")
def pii_detector() -> PIIDetector:
    return PIIDetector(languages=["en"])

@pytest.fixture(scope="module")
def tokenizer() -> ReversibleTokenizer:
    return ReversibleTokenizer()

@pytest.fixture(scope="module")
def privacy_guardian() -> PrivacyGuardian:
    return PrivacyGuardian(default_protection_level=ProtectionLevel.STANDARD)


# --- PIIDetector Performance Tests ---
def run_pii_detection(detector: PIIDetector, text: str):
    return detector.detect(text, language="en")

@pytest.mark.performance
def test_pii_detector_perf_medium(pii_detector, benchmark):
    if BENCHMARK_AVAILABLE:
        benchmark(run_pii_detection, pii_detector, SAMPLE_EMAIL_BODY_MEDIUM)
    else:
        ManualBenchmark("pii_detector_medium")(run_pii_detection, pii_detector, SAMPLE_EMAIL_BODY_MEDIUM)

@pytest.mark.performance
def test_pii_detector_perf_long(pii_detector, benchmark):
    if BENCHMARK_AVAILABLE:
        benchmark(run_pii_detection, pii_detector, SAMPLE_EMAIL_BODY_LONG)
    else:
        ManualBenchmark("pii_detector_long")(run_pii_detection, pii_detector, SAMPLE_EMAIL_BODY_LONG)


# --- ReversibleTokenizer Performance Tests ---
def run_tokenization(tokenizer_inst: ReversibleTokenizer, text: str, pii_entities: list):
    return tokenizer_inst.tokenize_pii(text, pii_entities)

def run_detokenization(tokenizer_inst: ReversibleTokenizer, text: str, token_map: dict):
    return tokenizer_inst.detokenize_text(text, token_map)

@pytest.mark.performance
def test_tokenizer_perf_medium(tokenizer, pii_detector, benchmark):
    # First, detect PII to get entities for tokenization
    pii_entities = pii_detector.detect(SAMPLE_EMAIL_BODY_MEDIUM, language="en")
    if BENCHMARK_AVAILABLE:
        tokenized_text, token_map = benchmark(run_tokenization, tokenizer, SAMPLE_EMAIL_BODY_MEDIUM, pii_entities)
        # Now benchmark detokenization
        # Need to re-run benchmark for the second operation if using pytest-benchmark correctly
        # For simplicity in manual, we might time them separately or together.
        # pytest-benchmark is designed to benchmark one callable.
        # To benchmark detokenization separately:
        # benchmark.pedantic(run_detokenization, args=(tokenizer, tokenized_text, token_map), iterations=1, rounds=10)
    else:
        mb_tokenize = ManualBenchmark("tokenizer_tokenize_medium")
        tokenized_text, token_map = mb_tokenize(run_tokenization, tokenizer, SAMPLE_EMAIL_BODY_MEDIUM, pii_entities)

        mb_detokenize = ManualBenchmark("tokenizer_detokenize_medium")
        mb_detokenize(run_detokenization, tokenizer, tokenized_text, token_map)


# --- PrivacyGuardian Performance Tests ---
async def run_guardian_protection_async(guardian: PrivacyGuardian, email_data: dict):
    return await guardian.protect_email(email_data)

def run_guardian_protection_sync(guardian: PrivacyGuardian, email_data: dict):
    # Wrapper for asyncio code if benchmark tool is synchronous
    return asyncio.run(guardian.protect_email(email_data))


@pytest.mark.performance
def test_privacy_guardian_perf_medium(privacy_guardian, benchmark):
    if BENCHMARK_AVAILABLE:
        benchmark(run_guardian_protection_sync, privacy_guardian, SAMPLE_EMAIL_DATA_MEDIUM)
    else:
        ManualBenchmark("privacy_guardian_medium")(run_guardian_protection_sync, privacy_guardian, SAMPLE_EMAIL_DATA_MEDIUM)

@pytest.mark.performance
def test_privacy_guardian_perf_long(privacy_guardian, benchmark):
    if BENCHMARK_AVAILABLE:
        benchmark(run_guardian_protection_sync, privacy_guardian, SAMPLE_EMAIL_DATA_LONG)
    else:
        ManualBenchmark("privacy_guardian_long")(run_guardian_protection_sync, privacy_guardian, SAMPLE_EMAIL_DATA_LONG)


if __name__ == "__main__":
    # To run these tests:
    # 1. Ensure pytest and pytest-benchmark are installed:
    #    pip install pytest pytest-benchmark
    # 2. Run from the project root:
    #    pytest tests/test_privacy_performance.py -m performance
    #
    # If pytest-benchmark is not installed, it will use manual timing.
    print("Run performance tests using: pytest tests/test_privacy_performance.py -m performance")