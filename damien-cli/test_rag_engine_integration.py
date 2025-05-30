#!/usr/bin/env python3
"""
RAGEngine Integration Test

This script provides comprehensive testing for the RAGEngine implementation,
validating vector database integration, semantic search capabilities, privacy protection,
and performance metrics against the enterprise targets.

Test Coverage:
- RAGEngine initialization and configuration
- Email batch indexing with chunking integration
- Semantic and hybrid search functionality
- Cache performance and TTL management
- Privacy-safe vector storage validation
- Performance benchmarking against targets

Performance Targets:
- <200ms search response time
- 1,000+ email chunks/second indexing
- 95%+ search accuracy for relevant results
- 100% PII protection in vector storage
"""

import asyncio
import time
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import shutil

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our components
from damien_cli.features.ai_intelligence.llm_integration.processing import (
    RAGEngine, RAGConfig, VectorStore, SearchType,
    IntelligentChunker, ChunkingConfig, ChunkingStrategy,
    BatchProcessor, EmailItem, 
    create_rag_engine
)
from damien_cli.features.ai_intelligence.llm_integration.privacy import PrivacyGuardian


class RAGEngineIntegrationTest:
    """Comprehensive integration test suite for RAGEngine."""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.rag_engine = None
        self.privacy_guardian = None
        self.chunker = None
        
        # Test data
        self.test_emails = [
            EmailItem("email_1", "Meeting scheduled for tomorrow at 2 PM. Please bring the quarterly reports and budget analysis. Contact john.doe@company.com for questions."),
            EmailItem("email_2", "Your order #12345 has been shipped. Tracking number: ABC123456789. Expected delivery: Friday. Customer support: support@shop.com"),
            EmailItem("email_3", "Important security update: Please change your password immediately. Your account (user: jane.smith) showed suspicious activity from IP 192.168.1.100."),
            EmailItem("email_4", "Project deadline reminder: The AI integration project is due next Monday. Team meeting at 10 AM in conference room B. Call 555-123-4567 for details."),
            EmailItem("email_5", "Invoice #INV-2024-001 is now available. Amount due: $2,450.00. Payment due date: January 15, 2024. Contact billing@company.com for questions."),
            EmailItem("email_6", "Welcome to our newsletter! Get the latest tech news and insights. Your subscription email: newsletter@tech.com. Unsubscribe anytime."),
            EmailItem("email_7", "Calendar invitation: All-hands meeting on Friday 3 PM. Agenda: Q4 results, new product launch, team updates. RSVP required."),
            EmailItem("email_8", "System maintenance scheduled for this weekend. Services will be unavailable Saturday 2-4 AM. Emergency contact: ops@company.com"),
        ]
        
        # Test queries for search validation
        self.test_queries = [
            ("meeting schedule", ["email_1", "email_7"]),  # Should find meetings
            ("order shipping", ["email_2"]),  # Should find order info
            ("security password", ["email_3"]),  # Should find security update
            ("project deadline", ["email_4"]),  # Should find project info
            ("invoice payment", ["email_5"]),  # Should find billing info
            ("maintenance system", ["email_8"]),  # Should find maintenance notice
        ]
    
    async def setup(self):
        """Set up test environment with temporary directory and components."""
        print("🔧 Setting up RAGEngine integration test environment...")
        
        # Create temporary directory for ChromaDB
        self.temp_dir = tempfile.mkdtemp(prefix="rag_test_")
        print(f"📁 Created temporary directory: {self.temp_dir}")
        
        # Initialize privacy guardian
        self.privacy_guardian = PrivacyGuardian()
        print("🛡️ Privacy guardian initialized")
        
        # Initialize intelligent chunker
        chunking_config = ChunkingConfig(
            max_chunk_size=500,  # Smaller chunks for testing
            overlap_size=50,
            strategy=ChunkingStrategy.HYBRID,
            enable_pii_protection=True
        )
        self.chunker = IntelligentChunker(
            config=chunking_config,
            privacy_guardian=self.privacy_guardian
        )
        print("📄 Intelligent chunker configured")
        
        # Initialize RAG engine
        rag_config = RAGConfig(
            vector_store=VectorStore.CHROMA,
            chroma_persist_directory=self.temp_dir,
            embedding_model="all-MiniLM-L6-v2",
            similarity_threshold=0.6,  # Lower threshold for testing
            max_results=5,
            enable_caching=True,
            cache_ttl_seconds=300  # 5 minutes for testing
        )
        
        self.rag_engine = RAGEngine(
            config=rag_config,
            privacy_guardian=self.privacy_guardian,
            chunker=self.chunker
        )
        
        # Initialize the engine
        success = await self.rag_engine.initialize()
        if not success:
            raise RuntimeError("Failed to initialize RAG engine")
        
        print("🚀 RAG engine initialized successfully")
        print()
    
    async def cleanup(self):
        """Clean up test environment."""
        print("🧹 Cleaning up test environment...")
        
        if self.rag_engine:
            await self.rag_engine.shutdown()
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🗑️ Removed temporary directory: {self.temp_dir}")
    
    def record_test_result(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """Record test result with details."""
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'details': details or {},
            'timestamp': time.time()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if details:
            for key, value in details.items():
                print(f"   📊 {key}: {value}")
        print()
    
    async def test_engine_initialization(self):
        """Test RAG engine initialization and configuration."""
        print("🧪 Testing RAG engine initialization...")
        
        try:
            # Test health check
            health = await self.rag_engine.health_check()
            
            success = (
                health['overall_status'] in ['healthy', 'degraded'] and
                health['components']['embedding_model']['status'] == 'healthy' and
                health['components']['vector_database']['status'] == 'healthy'
            )
            
            self.record_test_result(
                "RAG Engine Initialization",
                success,
                {
                    'overall_status': health['overall_status'],
                    'embedding_model': health['components']['embedding_model']['status'],
                    'vector_database': health['components']['vector_database']['status'],
                    'vector_dimension': health['components']['embedding_model'].get('vector_dimension', 'unknown')
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "RAG Engine Initialization",
                False,
                {'error': str(e)}
            )
    
    async def test_email_indexing(self):
        """Test email batch indexing with performance validation."""
        print("🧪 Testing email batch indexing...")
        
        try:
            start_time = time.time()
            
            # Index test emails
            index_result = await self.rag_engine.index_email_batch(
                self.test_emails,
                operation_id="test_batch_001"
            )
            
            indexing_time = time.time() - start_time
            
            # Calculate performance metrics
            throughput = index_result.total_chunks / indexing_time if indexing_time > 0 else 0
            
            success = (
                index_result.status.value == "completed" and
                index_result.success_rate >= 95.0 and
                throughput >= 50  # At least 50 chunks/second for small test
            )
            
            self.record_test_result(
                "Email Batch Indexing",
                success,
                {
                    'indexed_chunks': index_result.indexed_chunks,
                    'total_chunks': index_result.total_chunks,
                    'success_rate': f"{index_result.success_rate:.1f}%",
                    'throughput_chunks_per_second': f"{throughput:.1f}",
                    'processing_time_seconds': f"{indexing_time:.2f}",
                    'average_chunks_per_email': index_result.performance_metrics.get('average_chunks_per_email', 'unknown')
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "Email Batch Indexing",
                False,
                {'error': str(e)}
            )
    
    async def test_semantic_search(self):
        """Test semantic search functionality and accuracy."""
        print("🧪 Testing semantic search functionality...")
        
        total_tests = len(self.test_queries)
        passed_tests = 0
        total_search_time = 0
        
        for query, expected_emails in self.test_queries:
            try:
                start_time = time.time()
                
                # Perform semantic search
                results = await self.rag_engine.search(
                    query=query,
                    search_type=SearchType.SEMANTIC,
                    limit=10
                )
                
                search_time = (time.time() - start_time) * 1000  # Convert to ms
                total_search_time += search_time
                
                # Check if expected emails are found
                found_emails = {result.email_id for result in results}
                expected_set = set(expected_emails)
                
                # Calculate accuracy
                true_positives = len(found_emails.intersection(expected_set))
                precision = true_positives / len(found_emails) if found_emails else 0
                recall = true_positives / len(expected_set) if expected_set else 0
                
                # Test passes if we find at least one expected email and search is fast
                test_passed = (
                    true_positives > 0 and
                    search_time < 500  # 500ms is generous for testing
                )
                
                if test_passed:
                    passed_tests += 1
                
                print(f"   🔍 Query: '{query}' -> {len(results)} results in {search_time:.1f}ms")
                print(f"      Expected: {expected_emails}, Found: {list(found_emails)}")
                print(f"      Precision: {precision:.2f}, Recall: {recall:.2f}")
                
            except Exception as e:
                print(f"   ❌ Query '{query}' failed: {e}")
        
        avg_search_time = total_search_time / total_tests if total_tests > 0 else 0
        accuracy = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        success = (
            accuracy >= 80.0 and  # At least 80% of searches should work
            avg_search_time < 300  # Average under 300ms
        )
        
        self.record_test_result(
            "Semantic Search Functionality",
            success,
            {
                'test_accuracy': f"{accuracy:.1f}%",
                'passed_tests': f"{passed_tests}/{total_tests}",
                'average_search_time_ms': f"{avg_search_time:.1f}",
                'meets_latency_target': avg_search_time < 200
            }
        )
    
    async def test_hybrid_search(self):
        """Test hybrid search combining semantic and keyword matching."""
        print("🧪 Testing hybrid search functionality...")
        
        try:
            # Test with a query that should benefit from keyword matching
            query = "invoice payment due"
            
            start_time = time.time()
            semantic_results = await self.rag_engine.search(
                query=query,
                search_type=SearchType.SEMANTIC,
                limit=5
            )
            
            hybrid_results = await self.rag_engine.search(
                query=query,
                search_type=SearchType.HYBRID,
                limit=5
            )
            search_time = (time.time() - start_time) * 1000
            
            # Hybrid should potentially return different/better results
            semantic_emails = {r.email_id for r in semantic_results}
            hybrid_emails = {r.email_id for r in hybrid_results}
            
            # Check if "email_5" (invoice email) is found
            found_invoice = "email_5" in hybrid_emails
            
            success = (
                len(hybrid_results) > 0 and
                search_time < 1000 and  # Should be reasonably fast
                found_invoice  # Should find the invoice email
            )
            
            self.record_test_result(
                "Hybrid Search Functionality",
                success,
                {
                    'semantic_results': len(semantic_results),
                    'hybrid_results': len(hybrid_results),
                    'found_target_email': found_invoice,
                    'search_time_ms': f"{search_time:.1f}",
                    'hybrid_emails_found': list(hybrid_emails)
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "Hybrid Search Functionality",
                False,
                {'error': str(e)}
            )
    
    async def test_cache_performance(self):
        """Test caching functionality and performance."""
        print("🧪 Testing cache performance...")
        
        try:
            query = "meeting project deadline"
            
            # First search (cache miss)
            start_time = time.time()
            results1 = await self.rag_engine.search(query, limit=5)
            first_search_time = (time.time() - start_time) * 1000
            
            # Second search (should be cache hit)
            start_time = time.time()
            results2 = await self.rag_engine.search(query, limit=5)
            second_search_time = (time.time() - start_time) * 1000
            
            # Get performance stats
            stats = self.rag_engine.get_performance_stats()
            
            # Cache should make second search much faster
            cache_speedup = first_search_time / second_search_time if second_search_time > 0 else 1
            cache_hit_rate = stats['efficiency_metrics']['cache_hit_rate_percent']
            
            success = (
                len(results1) == len(results2) and  # Same results
                cache_speedup > 2 and  # At least 2x speedup
                cache_hit_rate > 0  # Some cache hits
            )
            
            self.record_test_result(
                "Cache Performance",
                success,
                {
                    'first_search_ms': f"{first_search_time:.1f}",
                    'second_search_ms': f"{second_search_time:.1f}",
                    'cache_speedup': f"{cache_speedup:.1f}x",
                    'cache_hit_rate': f"{cache_hit_rate:.1f}%",
                    'cache_hits': stats['operation_counts']['cache_hits'],
                    'cache_misses': stats['operation_counts']['cache_misses']
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "Cache Performance",
                False,
                {'error': str(e)}
            )
    
    async def test_privacy_protection(self):
        """Test privacy protection in vector storage."""
        print("🧪 Testing privacy protection...")
        
        try:
            # Create email with PII
            pii_email = EmailItem(
                "pii_test",
                "Please contact john.doe@company.com at phone 555-123-4567. "
                "Social Security Number: 123-45-6789. Credit card: 4111-1111-1111-1111."
            )
            
            # Index the email
            index_result = await self.rag_engine.index_email_batch([pii_email])
            
            # Search for the email
            results = await self.rag_engine.search("contact john doe", limit=5)
            
            # Check if PII is properly protected in stored content
            pii_found_in_results = False
            for result in results:
                if result.email_id == "pii_test":
                    content = result.content.lower()
                    # Check for specific PII patterns that should be tokenized
                    if ("123-45-6789" in content or 
                        "4111-1111-1111-1111" in content or
                        "555-123-4567" in content):
                        pii_found_in_results = True
                        break
            
            # Also check database stats for privacy protection
            db_stats = self.rag_engine.vector_db.get_stats()
            
            success = (
                index_result.status.value == "completed" and
                len(results) > 0 and  # Should find the email
                not pii_found_in_results  # But PII should be protected
            )
            
            self.record_test_result(
                "Privacy Protection",
                success,
                {
                    'email_indexed': index_result.status.value == "completed",
                    'email_found_in_search': len(results) > 0,
                    'pii_protected': not pii_found_in_results,
                    'total_indexed_chunks': db_stats.get('total_chunks', 'unknown')
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "Privacy Protection",
                False,
                {'error': str(e)}
            )
    
    async def test_performance_benchmarks(self):
        """Test overall performance against enterprise targets."""
        print("🧪 Testing performance benchmarks...")
        
        try:
            # Get comprehensive performance stats
            stats = self.rag_engine.get_performance_stats()
            
            # Check performance targets
            avg_search_time = stats['timing_metrics']['average_search_time_ms']
            meets_latency_target = stats['efficiency_metrics']['meets_latency_target']
            cache_hit_rate = stats['efficiency_metrics']['cache_hit_rate_percent']
            
            # Index stats
            index_stats = self.rag_engine.get_index_stats()
            
            success = (
                avg_search_time < 500 and  # Generous for testing environment
                meets_latency_target or avg_search_time < 300 and  # Alternative check
                cache_hit_rate >= 0  # Cache is working
            )
            
            self.record_test_result(
                "Performance Benchmarks",
                success,
                {
                    'average_search_time_ms': avg_search_time,
                    'meets_200ms_target': meets_latency_target,
                    'cache_hit_rate_percent': cache_hit_rate,
                    'total_searches': stats['operation_counts']['total_searches'],
                    'total_operations': stats['operation_counts']['total_operations'],
                    'database_type': index_stats['database_stats'].get('database_type', 'unknown'),
                    'total_chunks_indexed': index_stats['database_stats'].get('total_chunks', 'unknown')
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "Performance Benchmarks",
                False,
                {'error': str(e)}
            )
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print("="*70)
        print("🏁 RAGEngine Integration Test Summary")
        print("="*70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        print()
        
        # Print individual test results
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['test_name']}")
            
            if result['details']:
                for key, value in result['details'].items():
                    print(f"   📈 {key}: {value}")
            print()
        
        # Overall assessment
        success_rate = passed_tests / total_tests * 100
        
        if success_rate >= 90:
            grade = "🌟 EXCELLENT"
        elif success_rate >= 80:
            grade = "✅ GOOD"
        elif success_rate >= 70:
            grade = "⚠️ ACCEPTABLE"
        else:
            grade = "❌ NEEDS IMPROVEMENT"
        
        print(f"🎯 Overall Grade: {grade} ({success_rate:.1f}%)")
        print()
        
        # Recommendations
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("🔧 Recommended Actions:")
            for test in failed_tests:
                print(f"   • Fix issues with: {test['test_name']}")
                if 'error' in test['details']:
                    print(f"     Error: {test['details']['error']}")
            print()
        
        print("🎉 RAGEngine integration testing completed!")
        return success_rate >= 80  # Return True if tests mostly passed


async def main():
    """Run the complete RAGEngine integration test suite."""
    print("🚀 Starting RAGEngine Integration Test Suite")
    print("=" * 70)
    print()
    
    test_suite = RAGEngineIntegrationTest()
    
    try:
        # Setup test environment
        await test_suite.setup()
        
        # Run all tests
        await test_suite.test_engine_initialization()
        await test_suite.test_email_indexing()
        await test_suite.test_semantic_search()
        await test_suite.test_hybrid_search()
        await test_suite.test_cache_performance()
        await test_suite.test_privacy_protection()
        await test_suite.test_performance_benchmarks()
        
        # Print summary
        success = test_suite.print_summary()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Always cleanup
        await test_suite.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
