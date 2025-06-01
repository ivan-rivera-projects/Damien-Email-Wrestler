#!/usr/bin/env python3
"""
OpenAI Token Usage Analysis Tool
Tracks and analyzes token consumption patterns for cost optimization.

Run from: damien-cli directory
Usage: cd damien-cli && poetry run python ../analyze_token_usage.py
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️ No .env file found at {env_path}")

# Load environment variables first
load_env_file()

# Add CLI module to Python path
import sys
CLI_PATH = Path(__file__).parent / "damien-cli"
if CLI_PATH.exists():
    sys.path.insert(0, str(CLI_PATH))
else:
    print("⚠️ Note: Run this script from the damien-cli directory for full functionality")
    print("Usage: cd damien-cli && poetry run python ../analyze_token_usage.py")

class TokenUsageTracker:
    """Track OpenAI token usage and costs."""
    
    def __init__(self, log_path: str = "./logs/token_usage.json"):
        self.log_path = log_path
        self.log_data = self._load_existing_data()
        
        # OpenAI pricing (as of 2024)
        self.pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},  # per 1K tokens
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # per 1K tokens
            "text-embedding-3-small": {"input": 0.00002, "output": 0.0},  # per 1K tokens
            "text-embedding-3-large": {"input": 0.00013, "output": 0.0},  # per 1K tokens
        }
    
    def _load_existing_data(self) -> List[Dict[str, Any]]:
        """Load existing usage data."""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def track_usage(self, 
                   operation: str,
                   model: str, 
                   input_tokens: int,
                   output_tokens: int = 0,
                   cost_usd: Optional[float] = None) -> Dict[str, Any]:
        """Track a token usage event."""
        
        # Calculate cost if not provided
        if cost_usd is None and model in self.pricing:
            pricing = self.pricing[model]
            cost_usd = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
        
        usage_event = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost_usd,
            "session_id": f"session_{int(time.time())}"
        }
        
        self.log_data.append(usage_event)
        self._save_data()
        
        return usage_event
    
    def _save_data(self):
        """Save usage data to file."""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, 'w') as f:
            json.dump(self.log_data, f, indent=2)
    
    def analyze_usage(self, days: int = 7) -> Dict[str, Any]:
        """Analyze token usage patterns."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_data = [
            event for event in self.log_data 
            if datetime.fromisoformat(event["timestamp"]) > cutoff_date
        ]
        
        if not recent_data:
            return {"message": "No recent usage data found"}
        
        # Calculate totals
        total_tokens = sum(event["total_tokens"] for event in recent_data)
        total_cost = sum(event.get("cost_usd", 0) for event in recent_data)
        
        # Operation breakdown
        operations = {}
        for event in recent_data:
            op = event["operation"]
            if op not in operations:
                operations[op] = {"count": 0, "tokens": 0, "cost": 0}
            operations[op]["count"] += 1
            operations[op]["tokens"] += event["total_tokens"]
            operations[op]["cost"] += event.get("cost_usd", 0)
        
        # Model breakdown
        models = {}
        for event in recent_data:
            model = event["model"]
            if model not in models:
                models[model] = {"count": 0, "tokens": 0, "cost": 0}
            models[model]["count"] += 1
            models[model]["tokens"] += event["total_tokens"]
            models[model]["cost"] += event.get("cost_usd", 0)
        
        return {
            "analysis_period_days": days,
            "total_operations": len(recent_data),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "average_tokens_per_operation": round(total_tokens / len(recent_data), 2),
            "average_cost_per_operation": round(total_cost / len(recent_data), 4),
            "operations_breakdown": operations,
            "models_breakdown": models,
            "optimization_recommendations": self._generate_recommendations(operations, models)
        }
    
    def _generate_recommendations(self, operations: Dict, models: Dict) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Check for expensive operations
        for op, data in operations.items():
            if data["cost"] > 1.0:  # Operations costing more than $1
                recommendations.append(f"⚠️ Operation '{op}' is expensive (${data['cost']:.2f}) - consider optimization")
        
        # Check model usage efficiency
        for model, data in models.items():
            if "gpt-4o" in model and data["cost"] > 0.5:
                recommendations.append(f"💡 Consider using gpt-4o-mini instead of {model} for simpler tasks")
        
        # Token efficiency
        for op, data in operations.items():
            avg_tokens = data["tokens"] / data["count"]
            if avg_tokens > 5000:
                recommendations.append(f"📊 Operation '{op}' uses high tokens ({avg_tokens:.0f}/call) - consider input optimization")
        
        if not recommendations:
            recommendations.append("✅ Token usage appears optimized")
        
        return recommendations


async def test_openai_integration():
    """Test OpenAI integration and compare with local models."""
    print("🧪 Testing OpenAI Integration...")
    
    # Test basic environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return None
    
    print(f"✅ OpenAI API key configured (ends with: ...{api_key[-8:]})")
    
    # Test if we can import providers
    try:
        # Try to import from the CLI directory
        sys.path.insert(0, './damien_cli')
        from damien_cli.features.ai_intelligence.llm_providers.openai_provider import OpenAIProvider
        print("✅ OpenAI provider import successful")
    except ImportError as e:
        print(f"⚠️ Could not import OpenAI provider: {e}")
        print("💡 Run this script from the damien-cli directory for full functionality")
        return None
    
    # Create tracker
    tracker = TokenUsageTracker()
    
    try:
        # Test provider
        async with OpenAIProvider() as provider:
            test_prompt = "Analyze this email subject for importance: 'Meeting with CEO tomorrow - urgent'"
            
            print("\n📊 Testing OpenAI Provider...")
            start_time = time.time()
            
            # Test completion
            result = await provider.complete(
                test_prompt, 
                complexity="simple",
                task_type="test_analysis"
            )
            
            duration = time.time() - start_time
            
            print(f"✅ OpenAI Response Time: {duration:.2f}s")
            print(f"📝 OpenAI Result Preview: {result[:100]}...")
            
            # Estimate tokens (rough calculation)
            estimated_tokens = provider.count_tokens(test_prompt + result)
            tracker.track_usage("test_analysis", "gpt-4o-mini", estimated_tokens // 2, estimated_tokens // 2)
            
            print(f"🔢 Estimated Tokens: {estimated_tokens}")
            
    except Exception as e:
        print(f"❌ OpenAI Test Failed: {e}")
        return None
    
    # Analyze usage
    if tracker.log_data:
        analysis = tracker.analyze_usage(days=1)
        print(f"\n💰 OpenAI Cost Analysis:")
        print(f"   Total Cost: ${analysis['total_cost_usd']:.4f}")
        print(f"   Avg Cost/Operation: ${analysis['average_cost_per_operation']:.4f}")
        
        print(f"\n🎯 Recommendations:")
        for rec in analysis['optimization_recommendations']:
            print(f"   {rec}")
            
        return analysis
    
    return None


def main():
    """Main function for script execution."""
    print("🚀 OpenAI Token Usage Analysis Tool")
    print("=" * 50)
    
    # Check if we're in the right directory
    if os.path.exists('./damien_cli'):
        print("✅ Running from project root")
    elif os.path.exists('./pyproject.toml') and 'damien_cli' in str(Path.cwd()):
        print("✅ Running from damien-cli directory")
    else:
        print("⚠️ For full functionality, run from damien-cli directory:")
        print("   cd damien-cli && poetry run python ../analyze_token_usage.py")
    
    # Run integration test
    result = asyncio.run(test_openai_integration())
    
    print("\n🎯 Next Steps:")
    print("1. Monitor token usage with: TokenUsageTracker().analyze_usage()")
    print("2. Set cost alerts in environment variables")
    print("3. Use gpt-4o-mini for simple tasks, gpt-4o for complex analysis")
    print("4. Check logs at: ./logs/token_usage.json")
    
    if result:
        print("\n✅ OpenAI integration test completed successfully!")
    else:
        print("\n⚠️ Some tests failed. Check error messages above.")


if __name__ == "__main__":
    main()
