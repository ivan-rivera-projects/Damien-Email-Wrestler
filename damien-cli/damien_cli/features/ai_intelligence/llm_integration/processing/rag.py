                    }
                    health_status['overall_status'] = 'degraded'
            else:
                health_status['components']['embedding_model'] = {
                    'status': 'not_loaded'
                }
                health_status['overall_status'] = 'unhealthy'
            
            # Check vector database
            if self._connected and self.vector_db:
                try:
                    db_stats = self.vector_db.get_stats()
                    health_status['components']['vector_database'] = {
                        'status': 'healthy',
                        'type': self.config.vector_store.value,
                        'stats': db_stats
                    }
                except Exception as e:
                    health_status['components']['vector_database'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
                    health_status['overall_status'] = 'degraded'
            else:
                health_status['components']['vector_database'] = {
                    'status': 'not_connected'
                }
                health_status['overall_status'] = 'unhealthy'
            
            # Check cache system
            try:
                cache_health = {
                    'status': 'healthy',
                    'active_entries': len(self.cache),
                    'hit_rate_percent': (
                        self.cache_hits / (self.cache_hits + self.cache_misses) * 100
                        if (self.cache_hits + self.cache_misses) > 0 else 0
                    )
                }
                health_status['components']['cache'] = cache_health
            except Exception as e:
                health_status['components']['cache'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['overall_status'] = 'degraded'
            
        except Exception as e:
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the RAG engine."""
        logger.info("RAG engine shutting down...")
        
        try:
            # Clear cache
            async with self._cache_lock:
                self.cache.clear()
            
            # Disconnect from vector database
            if self.vector_db:
                await self.vector_db.disconnect()
                self._connected = False
            
            # Clear embedding model
            self.embedding_model = None
            self._embedding_model_loaded = False
            
            logger.info("RAG engine shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during RAG engine shutdown: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get detailed performance statistics for monitoring and optimization.
        
        Returns:
            Dictionary containing comprehensive performance metrics
        """
        try:
            # Calculate derived metrics
            avg_search_time_ms = (
                self.total_search_time / self.search_count * 1000
                if self.search_count > 0 else 0
            )
            avg_index_time_s = (
                self.total_index_time / self.index_count
                if self.index_count > 0 else 0
            )
            total_operations = self.search_count + self.index_count
            cache_efficiency = (
                self.cache_hits / (self.cache_hits + self.cache_misses) * 100
                if (self.cache_hits + self.cache_misses) > 0 else 0
            )
            
            return {
                'operation_counts': {
                    'total_searches': self.search_count,
                    'total_indexing_operations': self.index_count,
                    'total_operations': total_operations,
                    'cache_hits': self.cache_hits,
                    'cache_misses': self.cache_misses
                },
                
                'timing_metrics': {
                    'average_search_time_ms': round(avg_search_time_ms, 2),
                    'average_index_time_seconds': round(avg_index_time_s, 2),
                    'total_search_time_seconds': round(self.total_search_time, 2),
                    'total_index_time_seconds': round(self.total_index_time, 2)
                },
                
                'efficiency_metrics': {
                    'cache_hit_rate_percent': round(cache_efficiency, 2),
                    'searches_per_second': (
                        self.search_count / self.total_search_time
                        if self.total_search_time > 0 else 0
                    ),
                    'meets_latency_target': avg_search_time_ms < 200,  # <200ms target
                    'active_cache_entries': len(self.cache)
                },
                
                'quality_metrics': {
                    'similarity_threshold': self.config.similarity_threshold,
                    'average_results_per_search': (
                        # This would need to be tracked separately in a real implementation
                        self.config.max_results  # Placeholder
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate performance stats: {e}")
            return {'error': str(e)}


# Factory function for easy initialization
async def create_rag_engine(
    vector_store: VectorStore = VectorStore.CHROMA,
    embedding_model: str = "all-MiniLM-L6-v2",
    privacy_guardian: Optional[PrivacyGuardian] = None,
    chunker: Optional[IntelligentChunker] = None,
    **config_kwargs
) -> RAGEngine:
    """
    Factory function to create and initialize a RAG engine.
    
    Args:
        vector_store: Vector database backend to use
        embedding_model: Sentence transformer model for embeddings
        privacy_guardian: Privacy protection system (optional)
        chunker: Intelligent chunker for content preparation (optional)
        **config_kwargs: Additional configuration parameters
        
    Returns:
        Initialized RAGEngine instance
        
    Raises:
        RuntimeError: If initialization fails
    """
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
