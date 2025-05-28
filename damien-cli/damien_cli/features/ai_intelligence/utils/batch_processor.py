"""Batch processing utilities for efficient email handling"""

import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from tqdm import tqdm
import numpy as np

from ..models import BatchProcessingResult, EmailEmbedding

logger = logging.getLogger(__name__)

class BatchEmailProcessor:
    """Handles batch processing of emails for efficiency"""
    
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        
    async def process_embeddings(
        self, 
        emails: List[Dict], 
        embedding_generator
    ) -> Tuple[BatchProcessingResult, np.ndarray]:
        """Process emails in batches to generate embeddings"""
        
        start_time = datetime.now()
        processed_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        embeddings = []
        
        try:
            # Process in batches
            total_batches = (len(emails) + self.batch_size - 1) // self.batch_size
            
            for i in tqdm(range(0, len(emails), self.batch_size), desc="Processing email batches"):
                batch = emails[i:i + self.batch_size]
                
                try:
                    # Generate embeddings for batch
                    batch_embeddings = await self._process_batch_embeddings(
                        batch, embedding_generator
                    )
                    
                    embeddings.extend(batch_embeddings)
                    processed_count += len(batch)
                    
                except Exception as e:
                    error_msg = f"Error processing batch {i//self.batch_size + 1}: {str(e)}"
                    logger.warning(error_msg)
                    errors.append({
                        'type': 'batch_processing_error',
                        'message': error_msg,
                        'batch_index': i//self.batch_size + 1,
                        'timestamp': datetime.now().isoformat()
                    })
                    error_count += len(batch)
                    
                    # Add zero embeddings for failed batch
                    for _ in batch:
                        embeddings.append(np.zeros(384))  # Default embedding size
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate throughput
            throughput = processed_count / processing_time if processing_time > 0 else 0
            
            # Create result object
            result = BatchProcessingResult(
                total_items=len(emails),
                processed_successfully=processed_count,
                failed_items=error_count,
                skipped_items=skipped_count,
                processing_time_seconds=processing_time,
                throughput_per_second=throughput,
                embeddings_generated=len(embeddings),
                errors=errors,
                batch_size=self.batch_size,
                parallel_workers=1  # Single-threaded for now
            )
            
            return result, np.array(embeddings)
            
        except Exception as e:
            logger.error(f"Critical error in batch processing: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Return error result
            error_result = BatchProcessingResult(
                total_items=len(emails),
                processed_successfully=0,
                failed_items=len(emails),
                skipped_items=0,
                processing_time_seconds=processing_time,
                throughput_per_second=0.0,
                embeddings_generated=0,
                batch_size=self.batch_size,
                parallel_workers=1
            )
            error_result.add_error('critical_error', str(e))
            
            return error_result, np.array([])
    
    async def _process_batch_embeddings(
        self, 
        batch: List[Dict], 
        embedding_generator
    ) -> List[np.ndarray]:
        """Process a single batch of emails for embeddings"""
        
        try:
            # Use batch processing if available
            if hasattr(embedding_generator, 'generate_batch_embeddings'):
                return embedding_generator.generate_batch_embeddings(batch)
            else:
                # Fall back to individual processing
                embeddings = []
                for email in batch:
                    try:
                        embedding = embedding_generator.generate_embedding(email)
                        embeddings.append(embedding)
                    except Exception as e:
                        logger.warning(f"Error processing email {email.get('id', 'unknown')}: {str(e)}")
                        # Add zero embedding for failed email
                        embeddings.append(np.zeros(384))
                return embeddings
                
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {str(e)}")
            raise
    
    def process_emails_sync(
        self, 
        emails: List[Dict], 
        processing_function,
        description: str = "Processing emails"
    ) -> BatchProcessingResult:
        """Synchronous batch processing for general email operations"""
        
        start_time = datetime.now()
        processed_count = 0
        error_count = 0
        errors = []
        results = []
        
        try:
            # Process in batches with progress bar
            for i in tqdm(range(0, len(emails), self.batch_size), desc=description):
                batch = emails[i:i + self.batch_size]
                
                for email in batch:
                    try:
                        result = processing_function(email)
                        results.append(result)
                        processed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing email {email.get('id', 'unknown')}: {str(e)}"
                        logger.warning(error_msg)
                        errors.append({
                            'type': 'email_processing_error',
                            'message': error_msg,
                            'email_id': email.get('id', 'unknown'),
                            'timestamp': datetime.now().isoformat()
                        })
                        error_count += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return BatchProcessingResult(
                total_items=len(emails),
                processed_successfully=processed_count,
                failed_items=error_count,
                skipped_items=0,
                processing_time_seconds=processing_time,
                throughput_per_second=processed_count / processing_time if processing_time > 0 else 0,
                errors=errors,
                batch_size=self.batch_size,
                parallel_workers=1
            )
            
        except Exception as e:
            logger.error(f"Critical error in sync batch processing: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            error_result = BatchProcessingResult(
                total_items=len(emails),
                processed_successfully=processed_count,
                failed_items=len(emails) - processed_count,
                skipped_items=0,
                processing_time_seconds=processing_time,
                throughput_per_second=0.0,
                batch_size=self.batch_size,
                parallel_workers=1
            )
            error_result.add_error('critical_error', str(e))
            
            return error_result
    
    def get_optimal_batch_size(self, total_items: int, memory_limit_mb: int = 512) -> int:
        """Calculate optimal batch size based on available memory"""
        
        # Rough estimation: assume each email embedding takes ~1.5KB
        # Plus email metadata ~2KB per email = ~3.5KB per email
        estimated_memory_per_email = 3.5  # KB
        
        # Convert memory limit to KB
        memory_limit_kb = memory_limit_mb * 1024
        
        # Calculate max items that fit in memory
        max_items_in_memory = int(memory_limit_kb / estimated_memory_per_email)
        
        # Use smaller of: calculated max, current batch size, or total items
        optimal_size = min(max_items_in_memory, self.batch_size, total_items)
        
        # Ensure minimum batch size of 10
        return max(optimal_size, 10)
    
    def estimate_processing_time(
        self, 
        total_items: int, 
        time_per_item_seconds: float = 0.1
    ) -> Dict[str, float]:
        """Estimate processing time for a given number of items"""
        
        total_time = total_items * time_per_item_seconds
        
        # Account for batch overhead (assume 5% overhead)
        overhead_factor = 1.05
        total_time_with_overhead = total_time * overhead_factor
        
        return {
            'total_time_seconds': total_time_with_overhead,
            'total_time_minutes': total_time_with_overhead / 60,
            'estimated_throughput_per_second': 1 / time_per_item_seconds,
            'estimated_batches': (total_items + self.batch_size - 1) // self.batch_size
        }
