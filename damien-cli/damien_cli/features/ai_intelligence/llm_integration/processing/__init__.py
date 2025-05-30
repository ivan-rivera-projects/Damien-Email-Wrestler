"""
Scalable Processing Module for AI Intelligence Layer

This module provides enterprise-grade scalable processing capabilities for email intelligence,
including intelligent chunking, batch processing, RAG integration, hierarchical processing,
and progress tracking for large-scale operations.

Components:
- IntelligentChunker: Token-aware document splitting with semantic coherence
- BatchProcessor: Scalable email processing with progress tracking (PLANNED)
- RAGEngine: Vector database integration for semantic search (PLANNED)
- HierarchicalProcessor: Multi-level analysis for complex tasks (PLANNED)
- ProgressTracker: Real-time processing updates for large operations (PLANNED)

Phase 3 Week 5-6 Implementation
Performance Targets:
- Process 100K+ emails in batch mode
- RAG search response < 200ms
- Maintain context coherence in chunking
- Real-time progress tracking for operations
"""

from .chunker import IntelligentChunker, ChunkingStrategy, ChunkMetadata
from .batch import BatchProcessor, BatchConfig, BatchResult, ProcessingStrategy, BatchStatus, EmailItem, ProcessingResult, BatchProgress

# Planned imports - will be implemented next
# from .rag import RAGEngine, SearchResult, VectorStore
# from .hierarchical import HierarchicalProcessor, ProcessingLevel, AnalysisResult
# from .tracker import ProgressTracker, ProgressUpdate, OperationStatus

__all__ = [
    # Chunking (IMPLEMENTED)
    'IntelligentChunker', 'ChunkingStrategy', 'ChunkMetadata',
    
    # Batch Processing (IMPLEMENTED)
    'BatchProcessor', 'BatchConfig', 'BatchResult', 'ProcessingStrategy', 
    'BatchStatus', 'EmailItem', 'ProcessingResult', 'BatchProgress',
    
    # Planned components
    # 'RAGEngine', 'SearchResult', 'VectorStore',
    # 'HierarchicalProcessor', 'ProcessingLevel', 'AnalysisResult',
    # 'ProgressTracker', 'ProgressUpdate', 'OperationStatus'
]

# Module version and metadata
__version__ = "1.0.0"
__author__ = "Damien Platform Development Team"
__description__ = "Enterprise-grade scalable processing for intelligent email analysis"

# Performance configuration defaults
DEFAULT_CHUNK_SIZE = 1000  # tokens
DEFAULT_OVERLAP_SIZE = 100  # tokens
DEFAULT_BATCH_SIZE = 100  # emails per batch
DEFAULT_RAG_TIMEOUT = 200  # milliseconds
DEFAULT_PROGRESS_INTERVAL = 10  # updates per second

# Quality thresholds
MIN_CHUNK_COHERENCE = 0.8  # semantic coherence score
MIN_BATCH_SUCCESS_RATE = 0.95  # minimum successful processing rate
MAX_PROCESSING_TIME = 300  # seconds per email maximum
