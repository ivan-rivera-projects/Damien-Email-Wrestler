"""
Test suite for BatchProcessor component

Tests the enterprise-grade batch processing capabilities including:
- Multiple processing strategies (sequential, parallel, streaming, adaptive)
- Memory optimization and garbage collection
- Progress tracking and real-time updates
- Integration with IntelligentChunker
- Privacy protection with PII detection
- Error handling and recovery mechanisms
- Performance monitoring and metrics

Test Categories:
1. Basic functionality tests
2. Processing strategy tests  
3. Memory optimization tests
4. Progress tracking tests
5. Error handling tests
6. Integration tests
7. Performance tests
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import List, Dict, Any

from damien_cli.features.ai_intelligence.llm_integration.processing.batch import (
    BatchProcessor, BatchConfig, BatchResult, ProcessingStrategy, BatchStatus,
    EmailItem, ProcessingResult, BatchProgress
)
from damien_cli.features.ai_intelligence.llm_integration.processing.chunker import (
    ChunkingConfig, ChunkingStrategy
)
from damien_cli.features.ai_intelligence.llm_integration.privacy.guardian import PrivacyGuardian


class TestEmailItem:
    """Test EmailItem dataclass functionality."""
    
    def test_email_item_creation(self):
        """Test creating EmailItem instances."""
        email = EmailItem(
            email_id="test_001",
            content="Test email content",
            metadata={"sender": "test@example.com"},
            priority=1
        )
        
        assert email.email_id == "test_001"
        assert email.content == "Test email content"
        assert email.metadata["sender"] == "test@example.com"
        assert email.priority == 1
        assert email.size_bytes > 0  # Auto-calculated
    
    def test_email_item_auto_size_calculation(self):
        """Test automatic size calculation."""
        content = "Hello" * 100  # 500 characters
        email = EmailItem(email_id="size_test", content=content)
        
        expected_size = len(content.encode('utf-8'))
        assert email.size_bytes == expected_size
    
    def test_email_item_manual_size(self):
        """Test manual size specification."""
        email = EmailItem(
            email_id="manual_size",
            content="test",
            size_bytes=1000
        )
        
        assert email.size_bytes == 1000  # Should use manual value


class TestBatchProgress:
    """Test BatchProgress tracking functionality."""
    
    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation."""
        progress = BatchProgress(
            batch_id="test_batch",
            status=BatchStatus.RUNNING,
            total_items=100,
            processed_items=25,
            successful_items=23,
            failed_items=2
        )
        
        assert progress.progress_percentage == 25.0
    
    def test_progress_percentage_empty_batch(self):
        """Test progress percentage with empty batch."""
        progress = BatchProgress(
            batch_id="empty_batch",
            status=BatchStatus.PENDING,
            total_items=0,
            processed_items=0,
            successful_items=0,
            failed_items=0
        )
        
        assert progress.progress_percentage == 0.0
    
    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation."""
        start_time = datetime.now(timezone.utc)
        
        progress = BatchProgress(
            batch_id="time_test",
            status=BatchStatus.RUNNING,
            total_items=10,
            processed_items=5,
            successful_items=5,
            failed_items=0,
            start_time=start_time
        )
        
        # Should have some elapsed time
        time.sleep(0.01)  # Small delay
        elapsed = progress.elapsed_time_seconds
        assert elapsed > 0


class TestBatchConfig:
    """Test BatchConfig configuration functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BatchConfig()
        
        assert config.batch_size == 100
        assert config.max_concurrent_workers == 4
        assert config.max_memory_usage_mb == 1500.0
        assert config.processing_strategy == ProcessingStrategy.ADAPTIVE
        assert config.enable_chunking is True
        assert config.enable_privacy_protection is True
        assert config.max_retries == 3
    
    def test_chunking_config_auto_creation(self):
        """Test automatic chunking config creation."""
        config = BatchConfig(enable_chunking=True)
        
        assert config.chunking_config is not None
        assert config.chunking_config.strategy == ChunkingStrategy.HYBRID
        assert config.chunking_config.enable_pii_protection is True
    
    def test_custom_chunking_config(self):
        """Test custom chunking configuration."""
        custom_chunking = ChunkingConfig(
            max_chunk_size=500,
            strategy=ChunkingStrategy.TOKEN_BASED
        )
        
        config = BatchConfig(
            enable_chunking=True,
            chunking_config=custom_chunking
        )
        
        assert config.chunking_config.max_chunk_size == 500
        assert config.chunking_config.strategy == ChunkingStrategy.TOKEN_BASED


class TestBatchProcessor:
    """Test BatchProcessor main functionality."""
    
    @pytest.fixture
    def sample_emails(self) -> List[EmailItem]:
        """Create sample emails for testing."""
        return [
            EmailItem(
                email_id=f"email_{i:03d}",
                content=f"This is test email number {i} with some content to process.",
                metadata={"index": i}
            )
            for i in range(10)
        ]
    
    @pytest.fixture
    def batch_processor(self) -> BatchProcessor:
        """Create BatchProcessor instance for testing."""
        config = BatchConfig(
            batch_size=5,
            max_concurrent_workers=2,
            processing_strategy=ProcessingStrategy.SEQUENTIAL,
            enable_chunking=False,  # Disable for simpler testing
            enable_privacy_protection=False  # Disable for simpler testing
        )
        return BatchProcessor(config=config)
    
    def test_processor_initialization(self):
        """Test BatchProcessor initialization."""
        processor = BatchProcessor()
        
        assert processor.config is not None
        assert processor.privacy_guardian is not None
        assert processor.chunker is not None  # Should be created by default
        assert len(processor._active_batches) == 0
    
    def test_processor_with_custom_config(self):
        """Test BatchProcessor with custom configuration."""
        config = BatchConfig(
            enable_chunking=False,
            enable_privacy_protection=False
        )
        processor = BatchProcessor(config=config)
        
        assert processor.config.enable_chunking is False
        assert processor.chunker is None
    
    def test_process_empty_batch(self, batch_processor):
        """Test processing empty email batch."""
        with pytest.raises(ValueError, match="Email list cannot be empty"):
            batch_processor.process_batch([])
    
    def test_process_sequential_strategy(self, batch_processor, sample_emails):
        """Test sequential processing strategy."""
        # Use subset for faster testing
        emails = sample_emails[:3]
        
        result = batch_processor.process_batch(emails)
        
        assert result.batch_id is not None
        assert result.progress.status == BatchStatus.COMPLETED
        assert result.progress.total_items == 3
        assert result.progress.processed_items == 3
        assert len(result.results) == 3
        
        # Check all emails were processed successfully
        for email_result in result.results:
            assert email_result.success is True
            assert email_result.error_message is None
    
    def test_process_with_progress_callback(self, batch_processor, sample_emails):
        """Test processing with progress callback."""
        progress_updates = []
        
        def progress_callback(progress: BatchProgress):
            progress_updates.append(progress.progress_percentage)
        
        emails = sample_emails[:3]
        result = batch_processor.process_batch(emails, progress_callback=progress_callback)
        
        assert result.progress.status == BatchStatus.COMPLETED
        # Should have received at least one progress update
        assert len(progress_updates) >= 1
    
    def test_adaptive_strategy_selection(self):
        """Test adaptive strategy selection logic."""
        processor = BatchProcessor()
        
        # Small batch should use sequential
        small_emails = [EmailItem(f"small_{i}", "short content") for i in range(10)]
        strategy = processor._select_processing_strategy(small_emails)
        assert strategy == ProcessingStrategy.SEQUENTIAL
        
        # Large batch should use different strategy
        large_emails = [EmailItem(f"large_{i}", "content" * 100) for i in range(100)]
        strategy = processor._select_processing_strategy(large_emails)
        assert strategy in [ProcessingStrategy.PARALLEL, ProcessingStrategy.STREAMING]
    
    def test_memory_usage_tracking(self, batch_processor):
        """Test memory usage tracking."""
        memory_usage = batch_processor._get_current_memory_usage()
        assert isinstance(memory_usage, float)
        assert memory_usage >= 0
    
    def test_batch_cancellation(self, batch_processor):
        """Test batch cancellation functionality."""
        # This is a unit test, so we'll test the cancel mechanism
        batch_id = "test_cancel_batch"
        
        # Simulate active batch
        progress = BatchProgress(
            batch_id=batch_id,
            status=BatchStatus.RUNNING,
            total_items=100,
            processed_items=10,
            successful_items=10,
            failed_items=0
        )
        
        with batch_processor._batch_lock:
            batch_processor._active_batches[batch_id] = progress
        
        # Test cancellation
        success = batch_processor.cancel_batch(batch_id)
        assert success is True
        
        # Check status was updated
        assert batch_processor._active_batches[batch_id].status == BatchStatus.CANCELLED
        
        # Test cancelling non-existent batch
        success = batch_processor.cancel_batch("non_existent")
        assert success is False
    
    def test_get_active_batches(self, batch_processor):
        """Test getting active batch list."""
        # Initially empty
        active_batches = batch_processor.get_active_batches()
        assert len(active_batches) == 0
        
        # Add some mock active batches
        batch_ids = ["batch_1", "batch_2"]
        for batch_id in batch_ids:
            progress = BatchProgress(
                batch_id=batch_id,
                status=BatchStatus.RUNNING,
                total_items=10,
                processed_items=5,
                successful_items=5,
                failed_items=0
            )
            with batch_processor._batch_lock:
                batch_processor._active_batches[batch_id] = progress
        
        active_batches = batch_processor.get_active_batches()
        assert len(active_batches) == 2
        assert set(active_batches) == set(batch_ids)
    
    def test_performance_stats(self, batch_processor):
        """Test performance statistics generation."""
        stats = batch_processor.get_performance_stats()
        
        assert 'total_emails_processed' in stats
        assert 'total_processing_time_seconds' in stats
        assert 'average_processing_time_per_email_ms' in stats
        assert 'peak_memory_usage_mb' in stats
        assert 'active_batches' in stats
        assert 'processor_config' in stats
        
        # Check processor config details
        config = stats['processor_config']
        assert 'batch_size' in config
        assert 'max_workers' in config
        assert 'memory_limit_mb' in config
        assert 'strategy' in config


class TestBatchResult:
    """Test BatchResult functionality and summary generation."""
    
    def test_batch_result_summary_generation(self):
        """Test automatic summary generation."""
        # Create mock results
        results = [
            ProcessingResult(
                email_id="email_1",
                success=True,
                chunks=[{"chunk_1": "data"}],
                tokens_used=100,
                pii_entities=[]
            ),
            ProcessingResult(
                email_id="email_2", 
                success=True,
                chunks=[{"chunk_2": "data"}, {"chunk_3": "data"}],
                tokens_used=150,
                pii_entities=[]
            ),
            ProcessingResult(
                email_id="email_3",
                success=False,
                error_message="Processing failed"
            )
        ]
        
        # Create progress
        progress = BatchProgress(
            batch_id="test_summary",
            status=BatchStatus.COMPLETED,
            total_items=3,
            processed_items=3,
            successful_items=2,
            failed_items=1
        )
        
        # Create result with auto-summary
        batch_result = BatchResult(
            batch_id="test_summary",
            progress=progress,
            results=results
        )
        
        # Check summary
        summary = batch_result.summary
        assert summary['total_emails_processed'] == 3
        assert summary['successful_emails'] == 2
        assert summary['failed_emails'] == 1
        assert summary['success_rate_percent'] == (2/3 * 100)
        assert summary['total_chunks_created'] == 3
        assert summary['total_tokens_processed'] == 250
        assert summary['average_chunks_per_email'] == 1.0  # 3 chunks / 3 emails
    
    def test_batch_result_efficiency_score(self):
        """Test efficiency score calculation."""
        # Create high-performance results
        results = [
            ProcessingResult(
                email_id=f"email_{i}",
                success=True,
                processing_time_ms=50.0,  # Fast processing
                memory_usage_mb=10.0      # Low memory
            )
            for i in range(10)
        ]
        
        progress = BatchProgress(
            batch_id="efficiency_test",
            status=BatchStatus.COMPLETED,
            total_items=10,
            processed_items=10,
            successful_items=10,
            failed_items=0,
            processing_rate_per_second=20.0  # Fast rate
        )
        
        batch_result = BatchResult(
            batch_id="efficiency_test",
            progress=progress,
            results=results
        )
        
        efficiency = batch_result.performance_metrics['efficiency_score']
        assert isinstance(efficiency, float)
        assert 0 <= efficiency <= 100
        assert efficiency > 50  # Should be reasonably high for good performance


class TestProcessingStrategies:
    """Test different processing strategies."""
    
    @pytest.fixture
    def processor_parallel(self) -> BatchProcessor:
        """Create processor configured for parallel processing."""
        config = BatchConfig(
            processing_strategy=ProcessingStrategy.PARALLEL,
            max_concurrent_workers=2,
            enable_chunking=False,
            enable_privacy_protection=False
        )
        return BatchProcessor(config=config)
    
    @pytest.fixture
    def processor_streaming(self) -> BatchProcessor:
        """Create processor configured for streaming processing."""
        config = BatchConfig(
            processing_strategy=ProcessingStrategy.STREAMING,
            batch_size=3,  # Small batches for testing
            enable_chunking=False,
            enable_privacy_protection=False
        )
        return BatchProcessor(config=config)
    
    def test_parallel_processing(self, processor_parallel):
        """Test parallel processing strategy."""
        emails = [
            EmailItem(f"parallel_{i}", f"Content {i}")
            for i in range(5)
        ]
        
        result = processor_parallel.process_batch(emails)
        
        assert result.progress.status == BatchStatus.COMPLETED
        assert result.progress.total_items == 5
        assert result.progress.successful_items == 5
        assert len(result.results) == 5
    
    def test_streaming_processing(self, processor_streaming):
        """Test streaming processing strategy."""
        emails = [
            EmailItem(f"stream_{i}", f"Content {i}")
            for i in range(7)  # More than batch_size to test streaming
        ]
        
        result = processor_streaming.process_batch(emails)
        
        assert result.progress.status == BatchStatus.COMPLETED
        assert result.progress.total_items == 7
        assert result.progress.successful_items == 7
        assert len(result.results) == 7


class TestIntegrationWithChunker:
    """Test integration with IntelligentChunker."""
    
    @pytest.fixture
    def processor_with_chunking(self) -> BatchProcessor:
        """Create processor with chunking enabled."""
        config = BatchConfig(
            enable_chunking=True,
            chunking_config=ChunkingConfig(
                max_chunk_size=50,  # Small size to force chunking
                strategy=ChunkingStrategy.TOKEN_BASED,
                enable_pii_protection=False
            ),
            enable_privacy_protection=False
        )
        return BatchProcessor(config=config)
    
    def test_chunking_integration(self, processor_with_chunking):
        """Test that large emails get chunked properly."""
        # Create large email that will be chunked
        large_content = "This is a long email content. " * 20  # Should exceed 50 token limit
        emails = [
            EmailItem("chunked_email", large_content)
        ]
        
        result = processor_with_chunking.process_batch(emails)
        
        assert result.progress.status == BatchStatus.COMPLETED
        assert len(result.results) == 1
        
        email_result = result.results[0]
        assert email_result.success is True
        assert len(email_result.chunks) > 1  # Should be chunked into multiple pieces
    
    def test_small_email_no_chunking(self, processor_with_chunking):
        """Test that small emails don't get unnecessarily chunked."""
        small_content = "Short email"
        emails = [
            EmailItem("small_email", small_content)
        ]
        
        result = processor_with_chunking.process_batch(emails)
        
        assert result.progress.status == BatchStatus.COMPLETED
        email_result = result.results[0]
        assert email_result.success is True
        assert len(email_result.chunks) == 1  # Should remain as single chunk


@pytest.mark.integration
class TestBatchProcessorIntegration:
    """Integration tests for BatchProcessor with real dependencies."""
    
    def test_full_integration_with_privacy(self):
        """Test full integration with privacy protection enabled."""
        config = BatchConfig(
            batch_size=2,
            enable_chunking=True,
            enable_privacy_protection=True,
            processing_strategy=ProcessingStrategy.SEQUENTIAL
        )
        
        processor = BatchProcessor(config=config)
        
        # Create emails with potential PII
        emails = [
            EmailItem(
                "email_with_pii",
                "Contact me at john.doe@example.com or call 555-123-4567"
            ),
            EmailItem(
                "normal_email",
                "This is a normal email without any sensitive information"
            )
        ]
        
        result = processor.process_batch(emails)
        
        assert result.progress.status == BatchStatus.COMPLETED
        assert result.progress.successful_items == 2
        
        # Check that PII was detected
        pii_result = result.results[0]
        assert pii_result.success is True
        # Should have detected email and phone number PII
        assert len(pii_result.pii_entities) > 0
    
    def test_large_batch_performance(self):
        """Test performance with larger batch size."""
        config = BatchConfig(
            batch_size=50,
            processing_strategy=ProcessingStrategy.PARALLEL,
            max_concurrent_workers=4,
            enable_chunking=False,
            enable_privacy_protection=False
        )
        
        processor = BatchProcessor(config=config)
        
        # Create 100 emails for performance testing
        emails = [
            EmailItem(
                f"perf_email_{i:03d}",
                f"Performance test email number {i} with content to process."
            )
            for i in range(100)
        ]
        
        start_time = time.time()
        result = processor.process_batch(emails)
        processing_time = time.time() - start_time
        
        assert result.progress.status == BatchStatus.COMPLETED
        assert result.progress.successful_items == 100
        assert processing_time < 30  # Should complete within 30 seconds
        
        # Check performance metrics
        performance = result.performance_metrics
        assert performance['processing_rate_emails_per_second'] > 1  # At least 1 email/second
        assert performance['efficiency_score'] > 30  # Reasonable efficiency


if __name__ == "__main__":
    """Run the test suite directly."""
    pytest.main([__file__, "-v", "--tb=short"])
