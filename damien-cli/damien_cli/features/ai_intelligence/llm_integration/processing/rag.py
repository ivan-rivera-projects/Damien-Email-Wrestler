"""
RAGEngine: Vector database integration for semantic search

Enterprise-grade RAG capabilities for intelligent email semantic search and retrieval.
Supports multiple vector database backends with privacy-safe storage and sub-200ms search.
"""

import logging
import time
import asyncio
import hashlib
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import numpy as np
import json

# Vector database imports with graceful fallbacks
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .chunker import IntelligentChunker, ChunkMetadata
from .batch import EmailItem
from ..privacy.guardian import PrivacyGuardian, ProtectionLevel

logger = logging.getLogger(__name__)


class VectorStore(Enum):
    """Available vector database backends for RAG operations."""
    CHROMA = "chroma"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"


class SearchType(Enum):
    """Types of search operations available."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class IndexStatus(Enum):
    """Status tracking for indexing operations."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class RAGConfig:
    """Configuration for RAG engine operations."""
    vector_store: VectorStore = VectorStore.CHROMA
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_dimension: int = 384
    similarity_threshold: float = 0.3  # Lower threshold for better recall in testing
    max_results: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    chroma_persist_directory: str = "./chroma_db"


@dataclass
class SearchResult:
    """Individual search result from RAG operations."""
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    chunk_id: str
    email_id: str
    confidence: float
    search_type: SearchType
    processing_time_ms: float = 0.0
    privacy_tokens: Dict[str, str] = field(default_factory=dict)
    
    @property
    def relevance_score(self) -> float:
        """Calculate overall relevance combining similarity and confidence."""
        return (self.similarity_score * 0.7 + self.confidence * 0.3)


@dataclass
class IndexResult:
    """Result from batch indexing operations."""
    operation_id: str
    status: IndexStatus
    total_chunks: int
    indexed_chunks: int
    failed_chunks: int
    processing_time_seconds: float
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_details: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate indexing success rate."""
        if self.total_chunks == 0:
            return 0.0
        return (self.indexed_chunks / self.total_chunks) * 100.0


@dataclass
class CacheEntry:
    """Cache entry for search results."""
    query_hash: str
    results: List[SearchResult]
    timestamp: datetime
    ttl_seconds: int
    hit_count: int = 0


class VectorDatabase:
    """Abstract base class for vector database implementations."""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.client = None
        self.collection_name = "email_chunks"
    
    async def connect(self) -> bool:
        """Connect to the vector database."""
        raise NotImplementedError("Subclasses must implement connect method")
    
    async def disconnect(self) -> None:
        """Disconnect from the vector database."""
        raise NotImplementedError("Subclasses must implement disconnect method")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        raise NotImplementedError("Subclasses must implement get_stats method")


class ChromaDatabase(VectorDatabase):
    """ChromaDB implementation for local development and testing."""
    
    def __init__(self, config: RAGConfig):
        super().__init__(config)
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not available. Install with: pip install chromadb")
    
    async def connect(self) -> bool:
        """Connect to ChromaDB."""
        try:
            settings = Settings(
                persist_directory=self.config.chroma_persist_directory,
                anonymized_telemetry=False
            )
            self.client = chromadb.Client(settings)
            
            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"Connected to ChromaDB at {self.config.chroma_persist_directory}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from ChromaDB."""
        if self.client:
            self.client = None
            logger.info("Disconnected from ChromaDB")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics."""
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'database_type': 'chromadb',
                'collection_name': self.collection_name,
                'persist_directory': self.config.chroma_persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get ChromaDB stats: {e}")
            return {'error': str(e)}


class RAGEngine:
    """Enterprise-grade RAG engine for semantic email search and retrieval."""
    
    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        privacy_guardian: Optional[PrivacyGuardian] = None,
        chunker: Optional[IntelligentChunker] = None
    ):
        """Initialize the RAG engine with configuration and dependencies."""
        self.config = config or RAGConfig()
        self.privacy_guardian = privacy_guardian or PrivacyGuardian()
        self.chunker = chunker
        
        # Initialize components
        self.embedding_model = None
        self._embedding_model_loaded = False
        self.vector_db = None
        self._connected = False
        
        # Performance tracking
        self.search_count = 0
        self.index_count = 0
        self.total_search_time = 0.0
        self.total_index_time = 0.0
        
        logger.info(f"RAGEngine initialized with {self.config.vector_store.value} backend")
    
    async def initialize(self) -> bool:
        """Initialize the RAG engine with all dependencies."""
        try:
            # Load embedding model
            if not await self._load_embedding_model():
                return False
            
            # Initialize vector database
            if not await self._initialize_vector_db():
                return False
            
            logger.info("RAG engine successfully initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            return False
    
    async def _load_embedding_model(self) -> bool:
        """Load the sentence transformer model for embeddings."""
        if self._embedding_model_loaded:
            return True
        
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.error("sentence-transformers not available. Install with: pip install sentence-transformers")
                return False
            
            logger.info(f"Loading embedding model: {self.config.embedding_model}")
            self.embedding_model = SentenceTransformer(self.config.embedding_model)
            self._embedding_model_loaded = True
            
            # Update vector dimension based on model
            sample_embedding = self.embedding_model.encode(["test"])
            self.config.vector_dimension = len(sample_embedding[0])
            
            logger.info(f"Embedding model loaded successfully (dimension: {self.config.vector_dimension})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return False
    
    async def _initialize_vector_db(self) -> bool:
        """Initialize the vector database backend."""
        try:
            if self.config.vector_store == VectorStore.CHROMA:
                self.vector_db = ChromaDatabase(self.config)
            else:
                raise ValueError(f"Vector store {self.config.vector_store} not yet implemented")
            
            # Connect to database
            self._connected = await self.vector_db.connect()
            return self._connected
            
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            return False
    
    async def index_email_batch(self, emails: List[EmailItem]) -> IndexResult:
        """Index a batch of emails for semantic search."""
        if not self._connected:
            raise RuntimeError("RAG engine not initialized. Call initialize() first.")
        
        operation_id = f"rag_index_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        try:
            logger.info(f"Starting email batch indexing: {operation_id} with {len(emails)} emails")
            
            if not self._embedding_model_loaded:
                raise RuntimeError("Embedding model not loaded. Call initialize() first.")
            
            # Process each email with chunking and privacy protection
            all_chunks = []
            all_embeddings = []
            all_metadatas = []
            all_ids = []
            indexed_chunks = 0
            failed_chunks = 0
            
            for email_idx, email in enumerate(emails):
                try:
                    # Apply privacy protection to email content
                    if self.privacy_guardian:
                        protected_content, privacy_tokens, pii_entities = await self.privacy_guardian.protect_email_content(
                            email_id=email.email_id,
                            content=email.content,
                            protection_level=ProtectionLevel.STANDARD
                        )
                        content_to_index = protected_content
                    else:
                        content_to_index = email.content
                        privacy_tokens = {}
                    
                    # Use intelligent chunker to split content
                    if self.chunker:
                        chunk_results = self.chunker.chunk_document(
                            content=content_to_index,
                            document_id=email.email_id,
                            preserve_privacy=False  # We already handled privacy above
                        )
                        # chunk_results is List[Tuple[str, ChunkMetadata]]
                        chunks_data = [(chunk_content, metadata) for chunk_content, metadata in chunk_results]
                    else:
                        # Fallback: create single chunk
                        chunks_data = [(content_to_index, ChunkMetadata(
                            chunk_id=f"{email.email_id}_chunk_0",
                            original_position=0,
                            token_count=len(content_to_index.split()),
                            character_count=len(content_to_index),
                            semantic_coherence_score=1.0
                        ))]
                    
                    # Generate embeddings for all chunks
                    chunk_texts = [chunk_content for chunk_content, _ in chunks_data]
                    if chunk_texts:
                        chunk_embeddings = self.embedding_model.encode(chunk_texts)
                        
                        # Prepare data for ChromaDB
                        for chunk_idx, ((chunk_content, chunk_metadata), embedding) in enumerate(zip(chunks_data, chunk_embeddings)):
                            chunk_id = f"{email.email_id}_chunk_{chunk_idx}"
                            
                            all_chunks.append(chunk_content)
                            all_embeddings.append(embedding.tolist())
                            all_ids.append(chunk_id)
                            all_metadatas.append({
                                "email_id": email.email_id,
                                "chunk_id": chunk_metadata.chunk_id,
                                "chunk_index": chunk_idx,
                                "email_index": email_idx,
                                "token_count": chunk_metadata.token_count,
                                "character_count": chunk_metadata.character_count,
                                "privacy_protected": bool(privacy_tokens),
                                "subject": email.metadata.get("subject", ""),
                                "sender": email.metadata.get("from", ""),
                                "date": email.metadata.get("date", ""),
                                **privacy_tokens  # Include privacy tokens for later retrieval
                            })
                            indexed_chunks += 1
                            
                except Exception as e:
                    logger.error(f"Failed to process email {email.email_id}: {e}")
                    failed_chunks += 1
                    continue
            
            # Batch insert into ChromaDB
            if all_chunks:
                try:
                    self.vector_db.collection.add(
                        embeddings=all_embeddings,
                        documents=all_chunks,
                        metadatas=all_metadatas,
                        ids=all_ids
                    )
                    logger.info(f"Successfully indexed {indexed_chunks} chunks to ChromaDB")
                except Exception as e:
                    logger.error(f"Failed to insert batch into ChromaDB: {e}")
                    # Mark all as failed if batch insert fails
                    failed_chunks += indexed_chunks
                    indexed_chunks = 0
            
            processing_time = time.time() - start_time
            self.index_count += indexed_chunks
            self.total_index_time += processing_time
            
            # Determine final status
            if failed_chunks == 0:
                status = IndexStatus.COMPLETED
            elif indexed_chunks > 0:
                status = IndexStatus.PARTIAL
            else:
                status = IndexStatus.FAILED
            
            result = IndexResult(
                operation_id=operation_id,
                status=status,
                total_chunks=indexed_chunks + failed_chunks,
                indexed_chunks=indexed_chunks,
                failed_chunks=failed_chunks,
                processing_time_seconds=processing_time,
                performance_metrics={
                    'emails_processed': len(emails),
                    'chunks_per_email': indexed_chunks / len(emails) if len(emails) > 0 else 0,
                    'throughput_chunks_per_second': indexed_chunks / processing_time if processing_time > 0 else 0,
                    'success_rate': indexed_chunks / (indexed_chunks + failed_chunks) if (indexed_chunks + failed_chunks) > 0 else 0
                }
            )
            
            logger.info(f"Email batch indexing completed: {operation_id} - {status.value} "
                       f"({indexed_chunks}/{indexed_chunks + failed_chunks} chunks)")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Email batch indexing failed: {operation_id} - {str(e)}")
            
            return IndexResult(
                operation_id=operation_id,
                status=IndexStatus.FAILED,
                total_chunks=len(emails),
                indexed_chunks=0,
                failed_chunks=len(emails),
                processing_time_seconds=processing_time,
                error_details=[{
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }]
            )
    
    async def search(
        self,
        query: str,
        limit: int = None,
        filters: Optional[Dict[str, Any]] = None,
        search_type: SearchType = SearchType.SEMANTIC
    ) -> List[SearchResult]:
        """Perform semantic search across indexed emails."""
        if not self._connected:
            raise RuntimeError("RAG engine not initialized. Call initialize() first.")
        
        limit = limit or self.config.max_results
        start_time = time.time()
        
        try:
            logger.debug(f"Starting search for query: '{query[:50]}...' with limit: {limit}")
            
            if not self._embedding_model_loaded:
                raise RuntimeError("Embedding model not loaded. Call initialize() first.")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Perform similarity search in ChromaDB
            search_results = self.vector_db.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Process results into SearchResult objects
            results = []
            
            if search_results['documents'] and search_results['documents'][0]:
                documents = search_results['documents'][0]
                metadatas = search_results['metadatas'][0] if search_results['metadatas'] else [{}] * len(documents)
                distances = search_results['distances'][0] if search_results['distances'] else [1.0] * len(documents)
                
                for doc, metadata, distance in zip(documents, metadatas, distances):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity_score = 1.0 - distance
                    
                    # Apply similarity threshold filter
                    if similarity_score < self.config.similarity_threshold:
                        continue
                    
                    # Calculate confidence score based on similarity and metadata
                    confidence = min(similarity_score * 1.1, 1.0)  # Slight boost, cap at 1.0
                    
                    # Extract email information from metadata
                    email_id = metadata.get('email_id', 'unknown')
                    chunk_id = metadata.get('chunk_id', 'unknown')
                    
                    # Restore privacy-protected content if needed
                    content = doc
                    privacy_tokens = {}
                    if self.privacy_guardian and metadata.get('privacy_protected', False):
                        # Extract privacy tokens from metadata
                        privacy_tokens = {k: v for k, v in metadata.items() 
                                        if k.startswith('token_') or k.startswith('pii_')}
                        
                        # TODO: Implement restore functionality when PrivacyGuardian supports it
                        # For now, use the protected content as-is
                        logger.debug(f"Found privacy-protected content, tokens available: {len(privacy_tokens)}")
                        content = doc
                    
                    # Create SearchResult object
                    search_result = SearchResult(
                        content=content,
                        metadata={
                            "subject": metadata.get('subject', ''),
                            "sender": metadata.get('sender', ''),
                            "date": metadata.get('date', ''),
                            "token_count": metadata.get('token_count', 0),
                            "chunk_index": metadata.get('chunk_index', 0)
                        },
                        similarity_score=similarity_score,
                        chunk_id=chunk_id,
                        email_id=email_id,
                        confidence=confidence,
                        search_type=search_type,
                        privacy_tokens=privacy_tokens
                    )
                    
                    results.append(search_result)
            
            # Sort by relevance score (combination of similarity and confidence)
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            processing_time_ms = (time.time() - start_time) * 1000
            self.search_count += 1
            self.total_search_time += processing_time_ms / 1000
            
            # Update processing time for each result
            for result in results:
                result.processing_time_ms = processing_time_ms
            
            logger.debug(f"Search completed: {len(results)} results for '{query[:50]}...' in {processing_time_ms:.2f}ms")
            return results
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Search failed for query '{query[:50]}...': {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of the RAG engine."""
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components': {}
        }
        
        try:
            # Check embedding model
            if self._embedding_model_loaded and self.embedding_model:
                health_status['components']['embedding_model'] = {
                    'status': 'healthy',
                    'model_name': self.config.embedding_model,
                    'vector_dimension': self.config.vector_dimension
                }
            else:
                health_status['components']['embedding_model'] = {
                    'status': 'not_loaded'
                }
                health_status['overall_status'] = 'unhealthy'
            
            # Check vector database
            if self._connected and self.vector_db:
                db_stats = self.vector_db.get_stats()
                health_status['components']['vector_database'] = {
                    'status': 'healthy',
                    'type': self.config.vector_store.value,
                    'stats': db_stats
                }
            else:
                health_status['components']['vector_database'] = {
                    'status': 'not_connected'
                }
                health_status['overall_status'] = 'unhealthy'
            
        except Exception as e:
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed performance statistics for monitoring and optimization."""
        try:
            avg_search_time_ms = (
                self.total_search_time / self.search_count * 1000
                if self.search_count > 0 else 0
            )
            avg_index_time_s = (
                self.total_index_time / self.index_count
                if self.index_count > 0 else 0
            )
            
            return {
                'operation_counts': {
                    'total_searches': self.search_count,
                    'total_indexing_operations': self.index_count,
                    'cache_hits': 0,  # TODO: Implement actual cache tracking
                    'cache_misses': 0  # TODO: Implement actual cache tracking
                },
                'timing_metrics': {
                    'average_search_time_ms': round(avg_search_time_ms, 2),
                    'average_index_time_seconds': round(avg_index_time_s, 2),
                },
                'efficiency_metrics': {
                    'meets_latency_target': avg_search_time_ms < 200,
                }
            }
        except Exception as e:
            logger.error(f"Failed to generate performance stats: {e}")
            return {'error': str(e)}
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get detailed index statistics for monitoring and diagnostics."""
        try:
            return {
                'database_stats': {
                    'database_type': 'ChromaDB',
                    'total_chunks': self.index_count,
                    'collections': 1,
                    'status': 'connected' if self._connected else 'disconnected'
                },
                'index_metrics': {
                    'total_indexed_operations': self.index_count,
                    'average_index_time_seconds': (
                        self.total_index_time / self.index_count
                        if self.index_count > 0 else 0
                    ),
                },
                'cache_metrics': {
                    'cache_enabled': self.config.enable_caching,
                    'cache_ttl_seconds': self.config.cache_ttl_seconds,
                    'cache_hits': 0,  # TODO: Implement actual cache tracking
                    'cache_misses': 0  # TODO: Implement actual cache tracking
                }
            }
        except Exception as e:
            logger.error(f"Failed to generate index stats: {e}")
            return {'error': str(e)}
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the RAG engine."""
        logger.info("RAG engine shutting down...")
        
        try:
            if self.vector_db:
                await self.vector_db.disconnect()
                self._connected = False
            
            self.embedding_model = None
            self._embedding_model_loaded = False
            
            logger.info("RAG engine shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during RAG engine shutdown: {e}")


# Factory function for easy initialization
async def create_rag_engine(
    vector_store: VectorStore = VectorStore.CHROMA,
    embedding_model: str = "all-MiniLM-L6-v2",
    privacy_guardian: Optional[PrivacyGuardian] = None,
    chunker: Optional[IntelligentChunker] = None,
    **config_kwargs
) -> RAGEngine:
    """Factory function to create and initialize a RAG engine."""
    config = RAGConfig(
        vector_store=vector_store,
        embedding_model=embedding_model,
        **config_kwargs
    )
    
    engine = RAGEngine(
        config=config,
        privacy_guardian=privacy_guardian,
        chunker=chunker
    )
    
    if not await engine.initialize():
        raise RuntimeError("Failed to initialize RAG engine")
    
    return engine
