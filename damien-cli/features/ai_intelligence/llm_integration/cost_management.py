from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

# Attempt to import LLMRequest and LLMResponse for type hinting if they are in base.py
# This might require adjusting sys.path or using relative imports if run as a script directly
try:
    from .base import LLMRequest, LLMResponse, LLMProvider
except ImportError:
    # Fallback if the direct relative import fails (e.g. when file is not part of a package being run)
    LLMRequest = Any 
    LLMResponse = Any
    LLMProvider = Any

try:
    from .utils import TokenCounter
except ImportError:
    TokenCounter = Any


class CostEstimator:
    """
    Estimates the cost of LLM requests.
    This is a basic implementation and should be expanded with more accurate models.
    """
    # TODO: Centralize model costs from providers or fetch dynamically
    MODEL_COSTS = {
        # ModelName: (input_cost_per_1k_tokens, output_cost_per_1k_tokens)
        'gpt-4-turbo-preview': (0.01, 0.03),
        'gpt-4': (0.03, 0.06),
        'gpt-3.5-turbo': (0.0005, 0.0015),
        'gpt-3.5-turbo-16k': (0.003, 0.004),
        'claude-3-opus-20240229': (0.015, 0.075), # Example, verify actuals
        'claude-3-sonnet-20240229': (0.003, 0.015), # Example, verify actuals
        'claude-3-haiku-20240307': (0.00025, 0.00125), # Example, verify actuals
        'local': (0.0, 0.0) # Assuming local models have no direct API cost
    }

    def __init__(self, token_counter: Optional[TokenCounter] = None):
        self.token_counter = token_counter if token_counter else TokenCounter()

    def estimate_llm_cost(self, llm_request: LLMRequest) -> float:
        """
        Estimates the cost of a given LLMRequest.
        """
        if not llm_request:
            return 0.0

        model_name = getattr(llm_request, 'model', 'gpt-3.5-turbo') # Default if not specified
        
        prompt_text = getattr(llm_request, 'prompt', "")
        system_prompt_text = getattr(llm_request, 'system_prompt', "")
        
        input_text = prompt_text
        if system_prompt_text:
            input_text = f"{system_prompt_text}\n{prompt_text}" # Simplistic combination

        input_tokens = self.token_counter.count(input_text, model_name=model_name)
        
        # Approximate output tokens. This is a very rough guess.
        # A better approach might involve statistical analysis or a small pre-flight request.
        output_tokens = getattr(llm_request, 'max_tokens', 200) * 0.5 
        
        input_cost_1k, output_cost_1k = self.MODEL_COSTS.get(model_name, (0.001, 0.002)) # Default cost
        
        cost = (input_tokens / 1000 * input_cost_1k) + (output_tokens / 1000 * output_cost_1k)
        return round(cost, 6)

    def estimate_hybrid_cost(self, email_data: Dict, llm_request: LLMRequest) -> float:
        """
        Estimates the cost of a hybrid approach (embedding + LLM).
        """
        embedding_cost = self.estimate_embedding_cost(len(email_data.get('content', '')))
        llm_c = self.estimate_llm_cost(llm_request)
        return embedding_cost + llm_c

    def estimate_embedding_cost(self, text_length: int) -> float:
        """
        Estimates the cost of generating embeddings.
        Placeholder: Real cost depends on embedding model and provider.
        """
        # Example: 0.0001 USD per 1000 characters for a hypothetical embedding service
        return round((text_length / 1000) * 0.0001, 6)


class UsageTracker:
    """
    Tracks API usage for monitoring and cost management.
    This acts as the 'UsageMonitor' mentioned in the LLMServiceOrchestrator.
    """
    def __init__(self):
        self.usage_data: List[Dict[str, Any]] = []

    def track(self, provider: LLMProvider, response: LLMResponse, request_type: Optional[str] = "unknown"):
        """
        Tracks a single usage event.
        Matches the signature expected by LLMServiceOrchestrator's monitor.track
        """
        usage_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "provider": str(provider.value if isinstance(provider, LLMProvider) else provider),
            "model": response.model,
            "prompt_tokens": response.usage.get('prompt_tokens'),
            "completion_tokens": response.usage.get('completion_tokens'),
            "total_tokens": response.usage.get('total_tokens'),
            "estimated_cost": response.usage.get('estimated_cost'),
            "latency_ms": response.latency_ms,
            "finish_reason": response.finish_reason,
            "request_type": request_type,
            "metadata": response.metadata
        }
        self.usage_data.append(usage_record)
        # In a production system, this would likely write to a database or logging service.
        print(f"Usage Tracked: {usage_record}")

    def get_usage_summary(self, time_period_days: int = 30) -> Dict[str, Any]:
        """
        Provides a summary of usage over a given period.
        """
        cutoff_time = datetime.utcnow() - timedelta(days=time_period_days)
        relevant_data = [d for d in self.usage_data if datetime.fromisoformat(d['timestamp']) > cutoff_time]

        summary = {
            "total_requests": len(relevant_data),
            "total_cost": sum(d.get('estimated_cost', 0) for d in relevant_data if d.get('estimated_cost')),
            "total_tokens": sum(d.get('total_tokens', 0) for d in relevant_data if d.get('total_tokens')),
            "requests_by_provider": defaultdict(int),
            "cost_by_provider": defaultdict(float),
            "tokens_by_provider": defaultdict(int),
        }

        for record in relevant_data:
            provider_key = record.get("provider", "unknown")
            summary["requests_by_provider"][provider_key] += 1
            if record.get('estimated_cost'):
                summary["cost_by_provider"][provider_key] += record['estimated_cost']
            if record.get('total_tokens'):
                summary["tokens_by_provider"][provider_key] += record['total_tokens']
        
        return summary