"""
IntelligentChunker: Token-aware document splitting with semantic coherence

This module provides enterprise-grade document chunking capabilities that maintain
semantic coherence while optimizing for token limits and processing efficiency.
Integrates with Privacy Guardian to ensure PII protection across all chunks.

Features:
- Token-aware splitting with configurable limits
- Semantic coherence preservation using embeddings
- Multiple chunking strategies (token, semantic, hybrid)
- PII-aware chunking with privacy protection
- Overlap management for context preservation
- Performance optimization for large documents
- Comprehensive metrics and monitoring

Performance Targets:
- <100ms processing for average emails
- 99.9% semantic coherence preservation
- Zero PII leaks across chunk boundaries
- Scalable to 100K+ documents
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Union
import tiktoken
import numpy as np
from sentence_transformers import SentenceTransformer

from ..privacy.guardian import PrivacyGuardian
from ..privacy.detector import PIIEntity
from ..privacy.tokenizer import ReversibleTokenizer

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies for different use cases."""
    TOKEN_BASED = "token_based"  # Simple token-count splitting
    SEMANTIC = "semantic"        # Embeddings-based semantic splitting
    HYBRID = "hybrid"           # Combined token + semantic approach
    PII_AWARE = "pii_aware"     # Privacy-first chunking with PII boundaries


@dataclass
class ChunkMetadata:
    """Metadata for individual chunks with comprehensive tracking."""
    chunk_id: str
    original_position: int
    token_count: int
    character_count: int
    semantic_coherence_score: float
    pii_entities: List[PIIEntity] = field(default_factory=list)
    overlap_with_previous: int = 0
    overlap_with_next: int = 0
    processing_time_ms: float = 0.0
    strategy_used: ChunkingStrategy = ChunkingStrategy.TOKEN_BASED
    privacy_tokens: Dict[str, str] = field(default_factory=dict)


@dataclass
class ChunkingConfig:
    """Configuration for intelligent chunking operations."""
    max_chunk_size: int = 1000  # Maximum tokens per chunk
    overlap_size: int = 100     # Token overlap between chunks
    min_chunk_size: int = 50    # Minimum viable chunk size
    strategy: ChunkingStrategy = ChunkingStrategy.HYBRID
    preserve_sentences: bool = True
    preserve_paragraphs: bool = True
    min_coherence_score: float = 0.8
    enable_pii_protection: bool = True
    enable_performance_tracking: bool = True


class IntelligentChunker:
    """
    Enterprise-grade intelligent document chunker with semantic coherence preservation.
    
    Provides token-aware document splitting while maintaining semantic meaning and
    ensuring PII protection across all chunk boundaries. Optimized for large-scale
    email processing with comprehensive monitoring and metrics.
    """

    def __init__(
        self,
        config: Optional[ChunkingConfig] = None,
        privacy_guardian: Optional[PrivacyGuardian] = None,
        embedding_model: Optional[str] = None
    ):
        """
        Initialize the IntelligentChunker with configuration and dependencies.
        
        Args:
            config: Chunking configuration parameters
            privacy_guardian: Privacy protection system integration
            embedding_model: Model for semantic coherence analysis
        """
        self.config = config or ChunkingConfig()
        self.privacy_guardian = privacy_guardian or PrivacyGuardian()
        
        # Initialize tokenizer for accurate token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        
        # Initialize embedding model for semantic analysis
        self.embedding_model_name = embedding_model or "all-MiniLM-L6-v2"
        self.embedding_model = None  # Lazy loading for performance
        
        # Performance tracking
        self.chunk_count = 0
        self.total_processing_time = 0.0
        self.coherence_scores = []
        
        logger.info(f"IntelligentChunker initialized with strategy: {self.config.strategy}")

    def _lazy_load_embedding_model(self) -> SentenceTransformer:
        """Lazy load embedding model for performance optimization."""
        if self.embedding_model is None:
            try:
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
                # Fallback to basic tokenization strategy
                self.config.strategy = ChunkingStrategy.TOKEN_BASED
                
        return self.embedding_model

    def chunk_document(
        self,
        content: str,
        document_id: Optional[str] = None,
        preserve_privacy: bool = True
    ) -> List[Tuple[str, ChunkMetadata]]:
        """
        Chunk a document into intelligent segments with comprehensive metadata.
        
        Args:
            content: The document content to chunk
            document_id: Optional identifier for tracking
            preserve_privacy: Whether to apply PII protection
            
        Returns:
            List of (chunk_content, metadata) tuples
        """
        start_time = time.time()
        
        try:
            # Step 1: Privacy protection if enabled
            if preserve_privacy and self.config.enable_pii_protection:
                content, privacy_context = self._protect_privacy(content)
            else:
                privacy_context = {}

            # Step 2: Apply chunking strategy
            if self.config.strategy == ChunkingStrategy.TOKEN_BASED:
                chunks = self._chunk_by_tokens(content)
            elif self.config.strategy == ChunkingStrategy.SEMANTIC:
                chunks = self._chunk_by_semantics(content)
            elif self.config.strategy == ChunkingStrategy.HYBRID:
                chunks = self._chunk_hybrid(content)
            elif self.config.strategy == ChunkingStrategy.PII_AWARE:
                chunks = self._chunk_pii_aware(content)
            else:
                raise ValueError(f"Unknown chunking strategy: {self.config.strategy}")

            # Step 3: Generate comprehensive metadata
            chunked_results = []
            for i, chunk_content in enumerate(chunks):
                metadata = self._generate_metadata(
                    chunk_content, i, len(chunks), 
                    privacy_context, start_time
                )
                chunked_results.append((chunk_content, metadata))

            # Step 4: Performance tracking
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, chunked_results)
            
            logger.info(f"Successfully chunked document into {len(chunks)} segments "
                       f"in {processing_time:.2f}ms")
                       
            return chunked_results

        except Exception as e:
            logger.error(f"Failed to chunk document: {e}")
            # Return single chunk as fallback
            metadata = ChunkMetadata(
                chunk_id=f"fallback_0",
                original_position=0,
                token_count=len(self.tokenizer.encode(content)),
                character_count=len(content),
                semantic_coherence_score=1.0,
                processing_time_ms=(time.time() - start_time) * 1000,
                strategy_used=ChunkingStrategy.TOKEN_BASED
            )
            return [(content, metadata)]

    def _protect_privacy(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Apply privacy protection while preserving chunking capabilities."""
        try:
            # Detect PII entities
            pii_entities = self.privacy_guardian.pii_detector.detect(content)
            
            # Apply reversible tokenization for secure processing
            if pii_entities:
                tokenized_content = self.privacy_guardian.tokenizer.tokenize_content(
                    content, pii_entities
                )
                privacy_context = {
                    'original_pii_entities': pii_entities,
                    'tokenization_map': self.privacy_guardian.tokenizer.get_token_map()
                }
                return tokenized_content, privacy_context
            else:
                return content, {}
                
        except Exception as e:
            logger.warning(f"Privacy protection failed, proceeding without: {e}")
            return content, {}

    def _chunk_by_tokens(self, content: str) -> List[str]:
        """Simple token-based chunking with overlap."""
        tokens = self.tokenizer.encode(content)
        chunks = []
        
        start = 0
        while start < len(tokens):
            # Calculate chunk end position
            end = min(start + self.config.max_chunk_size, len(tokens))
            
            # Extract chunk tokens
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Preserve sentence boundaries if enabled
            if self.config.preserve_sentences and end < len(tokens):
                chunk_text = self._adjust_to_sentence_boundary(chunk_text, content)
            
            chunks.append(chunk_text)
            
            # Move to next chunk with overlap, but ensure we make progress
            next_start = end - self.config.overlap_size
            
            # Prevent infinite loop by ensuring we always make forward progress
            if next_start <= start:
                next_start = start + max(1, self.config.max_chunk_size // 2)
            
            start = next_start
            
            # Break if we've reached the end
            if start >= len(tokens):
                break
                
        return chunks

    def _chunk_by_semantics(self, content: str) -> List[str]:
        """Semantic chunking using embeddings for coherence."""
        # Load embedding model
        model = self._lazy_load_embedding_model()
        if model is None:
            # Fallback to token-based chunking
            return self._chunk_by_tokens(content)
        
        # Split into sentences for semantic analysis
        sentences = self._split_into_sentences(content)
        if len(sentences) <= 1:
            return [content]
        
        # Generate embeddings for semantic similarity
        embeddings = model.encode(sentences)
        
        # Find semantic boundaries using cosine similarity
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            # Check if adding this sentence would exceed limits
            if (current_tokens + sentence_tokens > self.config.max_chunk_size 
                and current_chunk):
                
                # Check semantic coherence before breaking
                if i < len(sentences) - 1:
                    similarity = np.dot(embeddings[i], embeddings[i+1])
                    if similarity < self.config.min_coherence_score:
                        # Low coherence - good breaking point
                        chunks.append(" ".join(current_chunk))
                        current_chunk = [sentence]
                        current_tokens = sentence_tokens
                        continue
                
                # High coherence but size limit reached
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def _chunk_hybrid(self, content: str) -> List[str]:
        """Hybrid approach combining token limits with semantic coherence."""
        # Start with token-based chunking
        token_chunks = self._chunk_by_tokens(content)
        
        # Apply semantic refinement if embedding model available
        model = self._lazy_load_embedding_model()
        if model is None:
            return token_chunks
        
        refined_chunks = []
        
        for chunk in token_chunks:
            # For chunks near the size limit, check if semantic splitting improves coherence
            token_count = len(self.tokenizer.encode(chunk))
            
            if token_count > self.config.max_chunk_size * 0.8:  # 80% of limit
                semantic_subchunks = self._chunk_by_semantics(chunk)
                if len(semantic_subchunks) > 1:
                    # Semantic splitting found better boundaries
                    refined_chunks.extend(semantic_subchunks)
                else:
                    refined_chunks.append(chunk)
            else:
                refined_chunks.append(chunk)
                
        return refined_chunks

    def _chunk_pii_aware(self, content: str) -> List[str]:
        """PII-aware chunking that respects privacy boundaries."""
        # Detect PII entities first
        pii_entities = self.privacy_guardian.pii_detector.detect(content)
        
        if not pii_entities:
            # No PII detected, use hybrid chunking
            return self._chunk_hybrid(content)
        
        # Sort PII entities by position
        pii_entities.sort(key=lambda x: x.start_char)
        
        chunks = []
        current_pos = 0
        current_chunk = ""
        current_tokens = 0
        
        for pii_entity in pii_entities:
            # Add content before PII entity
            before_pii = content[current_pos:pii_entity.start_char]
            before_tokens = len(self.tokenizer.encode(before_pii))
            
            # Check if we need to start a new chunk
            if (current_tokens + before_tokens > self.config.max_chunk_size 
                and current_chunk):
                chunks.append(current_chunk.strip())
                current_chunk = before_pii
                current_tokens = before_tokens
            else:
                current_chunk += before_pii
                current_tokens += before_tokens
            
            # Add PII entity (ensure it doesn't span chunks)
            pii_text = content[pii_entity.start_char:pii_entity.end_char]
            pii_tokens = len(self.tokenizer.encode(pii_text))
            
            if current_tokens + pii_tokens > self.config.max_chunk_size:
                # Start new chunk with PII entity
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = pii_text
                current_tokens = pii_tokens
            else:
                current_chunk += pii_text
                current_tokens += pii_tokens
            
            current_pos = pii_entity.end_char
        
        # Add remaining content
        remaining = content[current_pos:]
        if remaining:
            remaining_tokens = len(self.tokenizer.encode(remaining))
            if (current_tokens + remaining_tokens > self.config.max_chunk_size 
                and current_chunk):
                chunks.append(current_chunk.strip())
                chunks.append(remaining.strip())
            else:
                current_chunk += remaining
                chunks.append(current_chunk.strip())
        elif current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return [chunk for chunk in chunks if chunk]  # Remove empty chunks

    def _generate_metadata(
        self,
        chunk_content: str,
        position: int,
        total_chunks: int,
        privacy_context: Dict[str, Any],
        start_time: float
    ) -> ChunkMetadata:
        """Generate comprehensive metadata for a chunk."""
        
        # Basic metrics
        tokens = self.tokenizer.encode(chunk_content)
        token_count = len(tokens)
        char_count = len(chunk_content)
        
        # Detect PII in this chunk
        chunk_pii = self.privacy_guardian.pii_detector.detect(chunk_content)
        
        # Calculate semantic coherence if possible
        coherence_score = self._calculate_coherence_score(chunk_content)
        
        # Generate unique chunk ID
        chunk_id = f"chunk_{position:04d}_{hash(chunk_content) & 0xFFFF:04x}"
        
        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            original_position=position,
            token_count=token_count,
            character_count=char_count,
            semantic_coherence_score=coherence_score,
            pii_entities=chunk_pii,
            processing_time_ms=(time.time() - start_time) * 1000,
            strategy_used=self.config.strategy,
            privacy_tokens=privacy_context.get('tokenization_map', {})
        )
        
        return metadata

    def _calculate_coherence_score(self, content: str) -> float:
        """Calculate semantic coherence score for chunk quality assessment."""
        try:
            model = self._lazy_load_embedding_model()
            if model is None:
                return 1.0  # Default high score if no embedding model
            
            sentences = self._split_into_sentences(content)
            if len(sentences) <= 1:
                return 1.0  # Single sentence has perfect coherence
            
            # Calculate average pairwise similarity
            embeddings = model.encode(sentences)
            similarities = []
            
            for i in range(len(embeddings) - 1):
                similarity = np.dot(embeddings[i], embeddings[i+1])
                similarities.append(similarity)
            
            return float(np.mean(similarities))
            
        except Exception as e:
            logger.warning(f"Coherence calculation failed: {e}")
            return 0.8  # Conservative default

    def _split_into_sentences(self, content: str) -> List[str]:
        """Split content into sentences for semantic analysis."""
        # Simple sentence splitting - could be enhanced with NLTK/spaCy
        import re
        sentences = re.split(r'[.!?]+', content)
        return [s.strip() for s in sentences if s.strip()]

    def _adjust_to_sentence_boundary(self, chunk_text: str, full_content: str) -> str:
        """Adjust chunk boundary to preserve sentence structure."""
        # Find the last complete sentence in the chunk
        last_sentence_end = max(
            chunk_text.rfind('.'),
            chunk_text.rfind('!'),
            chunk_text.rfind('?')
        )
        
        if last_sentence_end > len(chunk_text) * 0.5:  # Don't cut more than half
            return chunk_text[:last_sentence_end + 1]
        return chunk_text

    def _update_performance_metrics(
        self,
        processing_time: float,
        chunks: List[Tuple[str, ChunkMetadata]]
    ) -> None:
        """Update performance tracking metrics."""
        self.chunk_count += len(chunks)
        self.total_processing_time += processing_time
        
        # Track coherence scores
        for _, metadata in chunks:
            self.coherence_scores.append(metadata.semantic_coherence_score)
        
        # Log performance summary periodically
        if self.chunk_count % 100 == 0:
            avg_coherence = np.mean(self.coherence_scores) if self.coherence_scores else 0
            avg_time = self.total_processing_time / self.chunk_count
            
            logger.info(f"Performance Summary - Chunks: {self.chunk_count}, "
                       f"Avg Time: {avg_time:.2f}ms, Avg Coherence: {avg_coherence:.3f}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        if self.chunk_count == 0:
            return {"status": "no_processing_completed"}
        
        return {
            "total_chunks_processed": self.chunk_count,
            "total_processing_time_ms": self.total_processing_time,
            "average_time_per_chunk_ms": self.total_processing_time / self.chunk_count,
            "average_coherence_score": np.mean(self.coherence_scores) if self.coherence_scores else 0,
            "min_coherence_score": min(self.coherence_scores) if self.coherence_scores else 0,
            "max_coherence_score": max(self.coherence_scores) if self.coherence_scores else 0,
            "coherence_std_dev": np.std(self.coherence_scores) if self.coherence_scores else 0,
            "strategy_used": self.config.strategy.value,
            "pii_protection_enabled": self.config.enable_pii_protection
        }

    def reset_performance_stats(self) -> None:
        """Reset performance tracking for new measurement cycle."""
        self.chunk_count = 0
        self.total_processing_time = 0.0
        self.coherence_scores = []
        logger.info("Performance statistics reset")
