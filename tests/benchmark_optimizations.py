#!/usr/bin/env python3
"""
Performance benchmark for the optimized email operations.

This script benchmarks optimized vs. standard operations to measure
the performance improvements achieved by the optimizations.

Usage:
    python benchmark_optimizations.py

Note: Requires an authenticated Gmail account and environment setup.
"""

import asyncio
import time
import statistics
import logging
import os
import sys

# Add parent directory to path if needed to handle imports from different directories
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Define PrettyTable class here
class PrettyTable:
    def __init__(self):
        self.field_names = []
        self.rows = []
        self.align = "l"
    
    def add_row(self, row):
        self.rows.append(row)
    
    def __str__(self):
        result = "| " + " | ".join(self.field_names) + " |\n"
        result += "|-" + "-|-".join(["-" * len(name) for name in self.field_names]) + "-|\n"
        
        for row in self.rows:
            result += "| " + " | ".join(str(item) for item in row) + " |\n"
        
        return result

# Try to import real PrettyTable if available
try:
    from prettytable import PrettyTable
except ImportError:
    # We already defined a fallback above
    pass

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def benchmark_operations():
    """Benchmark optimized vs. standard operations."""
    # Import here after path setup
    try:
        from damien_mcp_server.app.services.damien_adapter import DamienAdapter
    except ImportError as e:
        logger.error(f"Error importing required modules: {e}")
        logger.error("Make sure you're running this from the damien-cli directory.")
        logger.error("Try: cd damien-cli && poetry run python ../tests/benchmark_optimizations.py")
        return
    
    adapter = DamienAdapter()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Small List (≤50 emails)",
            "query": "is:unread newer_than:7d",
            "max_results": 50,
            "iterations": 3
        },
        {
            "name": "Medium List (≤200 emails)",
            "query": "older_than:30d newer_than:60d",
            "max_results": 200,
            "iterations": 3
        },
        {
            "name": "Large List (≤500 emails)",
            "query": "older_than:60d",
            "max_results": 500,
            "iterations": 3
        }
    ]
    
    # Results table
    results_table = PrettyTable()
    results_table.field_names = ["Scenario", "Standard Avg (s)", "Optimized Avg (s)", "Improvement (%)", "Emails Retrieved"]
    results_table.align = "l"
    
    # Run tests
    for scenario in scenarios:
        logger.info(f"\nBenchmarking: {scenario['name']}")
        logger.info("=" * 50)
        
        # Record email count for consistency check
        email_count = 0
        
        # Run standard operation
        standard_times = []
        for i in range(scenario["iterations"]):
            start_time = time.time()
            result = await adapter.list_emails_tool(
                query=scenario["query"],
                max_results=scenario["max_results"],
                optimize_query=False
            )
            elapsed = time.time() - start_time
            
            if result["success"]:
                count = len(result["data"]["email_summaries"])
                email_count = count  # Save for consistency check
                standard_times.append(elapsed)
                logger.info(f"Standard run {i+1}: {elapsed:.3f}s, {count} emails")
            else:
                logger.error(f"Standard run failed: {result.get('error_message', 'Unknown error')}")
        
        # Run optimized operation
        optimized_times = []
        for i in range(scenario["iterations"]):
            start_time = time.time()
            result = await adapter.list_emails_tool(
                query=scenario["query"],
                max_results=scenario["max_results"],
                optimize_query=True
            )
            elapsed = time.time() - start_time
            
            if result["success"]:
                count = len(result["data"]["email_summaries"])
                # Check consistency with standard run
                if abs(count - email_count) > email_count * 0.1:  # Allow 10% variance
                    logger.warning(f"Inconsistent result count: Standard={email_count}, Optimized={count}")
                
                optimized_times.append(elapsed)
                logger.info(f"Optimized run {i+1}: {elapsed:.3f}s, {count} emails")
            else:
                logger.error(f"Optimized run failed: {result.get('error_message', 'Unknown error')}")
        
        # Calculate statistics
        if standard_times and optimized_times:
            std_avg = statistics.mean(standard_times)
            opt_avg = statistics.mean(optimized_times)
            improvement = ((std_avg - opt_avg) / std_avg) * 100 if std_avg > 0 else 0
            
            logger.info("\nResults:")
            logger.info(f"Standard average: {std_avg:.3f}s")
            logger.info(f"Optimized average: {opt_avg:.3f}s")
            logger.info(f"Improvement: {improvement:.1f}%")
            
            # Add to table
            results_table.add_row([
                scenario["name"],
                f"{std_avg:.3f}",
                f"{opt_avg:.3f}",
                f"{improvement:.1f}",
                email_count
            ])
        else:
            logger.error("Insufficient data to calculate statistics")
            results_table.add_row([
                scenario["name"],
                "ERROR",
                "ERROR",
                "ERROR",
                email_count
            ])
    
    # Print summary table
    logger.info("\n\nBENCHMARK SUMMARY")
    logger.info("=" * 50)
    logger.info("\n" + str(results_table))
    logger.info("\nBenchmark completed!")

    # Save results to file
    with open("optimization_benchmark_results.txt", "w") as f:
        f.write("DAMIEN EMAIL WRESTLER - OPTIMIZATION BENCHMARK RESULTS\n")
        f.write("=" * 60 + "\n\n")
        f.write(str(results_table) + "\n\n")
        f.write("Notes:\n")
        f.write("- Each scenario was run multiple times to ensure reliable results\n")
        f.write("- 'Improvement' shows performance gains from the optimizations\n")
        f.write("- Tests run on: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
        
    logger.info(f"Results saved to optimization_benchmark_results.txt")

if __name__ == "__main__":
    try:
        # Run the benchmark
        asyncio.run(benchmark_operations())
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
