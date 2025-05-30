"""
Scalable Processing Module for AI Intelligence Layer

This module provides enterprise-grade scalable processing capabilities for email intelligence,
including intelligent chunking, batch processing, RAG integration, hierarchical processing,
and progress tracking for large-scale operations.

Components:
- IntelligentChunker: Token-aware document splitting with semantic coherence (✅ COMPLETE)
- BatchProcessor: Scalable email processing with progress tracking (✅ COMPLETE)
- RAGEngine: Vector database integration for semantic search (✅ COMPLETE)
- HierarchicalProcessor: Multi-level analysis for complex tasks (📅 PLANNED)
- ProgressTracker: Real-time processing updates for large operations (📅 PLANNED)

Phase 3 Week 5-6 Implementation Status: 75% Complete (3/4 major components implemented)
Performance Targets:
- Process 100K+ emails in batch mode
- RAG search response < 200ms
- Maintain context coherence in chunking
- Real-time progress tracking for operations
"""

from .chunker import IntelligentChunker, ChunkingStrategy, ChunkMetadata, ChunkingConfig
from .batch import BatchProcessor, BatchConfig, BatchResult, ProcessingStrategy, BatchStatus, EmailItem, ProcessingResult, BatchProgress
from .rag import RAGEngine, RAGConfig, SearchResult, SearchType, IndexResult, IndexStatus, VectorStore, CacheEntry, VectorDatabase, ChromaDatabase, create_rag_engine

# Planned imports - will be implemented next
# from .hierarchical import HierarchicalProcessor, ProcessingLevel, AnalysisResult
# from .tracker import ProgressTracker, ProgressUpdate, OperationStatus

__all__ = [
    # Chunking (✅ COMPLETE)
    'IntelligentChunker', 'ChunkingStrategy', 'ChunkMetadata', 'ChunkingConfig',
    
    # Batch Processing (✅ COMPLETE)
    'BatchProcessor', 'BatchConfig', 'BatchResult', 'ProcessingStrategy', 
    'BatchStatus', 'EmailItem', 'ProcessingResult', 'BatchProgress',
    
    # RAG Engine (✅ COMPLETE)
    'RAGEngine', 'RAGConfig', 'SearchResult', 'SearchType', 'IndexResult', 
    'IndexStatus', 'VectorStore', 'CacheEntry', 'VectorDatabase', 
    'ChromaDatabase', 'create_rag_engine',
    
    # Planned components
    # 'HierarchicalProcessor', 'ProcessingLevel', 'AnalysisResult',
    # 'ProgressTracker', 'ProgressUpdate', 'OperationStatus'
]

# Module version and metadata
__version__ = "1.1.0"
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
MIN_SEARCH_ACCURACY = 0.95  # minimum RAG search accuracy
MAX_SEARCH_LATENCY = 200  # milliseconds maximum search time

# RAG Configuration defaults
DEFAULT_SIMILARITY_THRESHOLD = 0.7  # minimum similarity for search results
DEFAULT_VECTOR_DIMENSION = 384  # all-MiniLM-L6-v2 dimension
DEFAULT_CACHE_TTL = 3600  # cache time-to-live in seconds
DEFAULT_MAX_RESULTS = 10  # maximum search results to return
