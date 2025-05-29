from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from jinja2 import Template
import json
from .utils import TokenCounter # Added import
import numpy as np # For potential similarity calculations

# Placeholder for a generic EmbeddingService interface
class EmbeddingService(ABC):
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two vectors."""
    if not vec1 or not vec2:
        return 0.0
    vec1_arr = np.array(vec1)
    vec2_arr = np.array(vec2)
    dot_product = np.dot(vec1_arr, vec2_arr)
    norm_vec1 = np.linalg.norm(vec1_arr)
    norm_vec2 = np.linalg.norm(vec2_arr)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return dot_product / (norm_vec1 * norm_vec2)

class DynamicExampleSelector:
    """
    Selects relevant examples for few-shot prompting, potentially using semantic similarity.
    """
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service

    async def select_examples(
        self,
        available_examples: List[Dict[str, Any]], # Expects examples like [{"input_text": "...", "output_text": "..."}]
        current_context: Dict[str, Any], # Expects context like {"text_to_embed": "..."}
        max_examples: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Selects the most relevant examples.
        If an embedding service is provided, it uses semantic similarity.
        Otherwise, it falls back to selecting the first few examples.
        """
        if not available_examples:
            return []

        if self.embedding_service and current_context.get("text_to_embed"):
            try:
                context_text = current_context["text_to_embed"]
                context_embedding = await self.embedding_service.embed(context_text)

                example_texts = [ex.get("input_text", "") for ex in available_examples]
                if not any(example_texts): # Ensure there's text to embed
                    print("Warning: No 'input_text' found in available_examples for embedding-based selection.")
                    return available_examples[:max_examples]

                example_embeddings = await self.embedding_service.embed_batch(example_texts)
                
                similarities = []
                for i, ex_embedding in enumerate(example_embeddings):
                    sim = cosine_similarity(context_embedding, ex_embedding)
                    similarities.append((sim, available_examples[i]))
                
                # Sort by similarity in descending order
                similarities.sort(key=lambda x: x[0], reverse=True)
                
                # Return the examples from the top similarities
                return [example for sim, example in similarities[:max_examples]]
            except Exception as e:
                print(f"Error during embedding-based example selection: {e}. Falling back to basic selection.")
                # Fallback in case of error during embedding/similarity calculation
                return available_examples[:max_examples]
        else:
            # Fallback to basic selection if no embedding service or no text to embed in context
            return available_examples[:max_examples]

class PromptTemplate(ABC):
    """Base class for prompt templates"""
    
    def __init__(self, template_str: str):
        self.template = Template(template_str)
        self.examples = []
        self.constraints = []
    
    @abstractmethod
    def build(self, context: Dict[str, Any]) -> str:
        """Build prompt with context"""
        pass
    
    def add_examples(self, examples: List[Dict[str, Any]]):
        """Add few-shot examples"""
        self.examples.extend(examples)
    
    def add_constraints(self, constraints: List[str]):
        """Add output constraints"""
        self.constraints.extend(constraints)

class EmailAnalysisPrompts:
    """Collection of email analysis prompts"""
    
    INTENT_CLASSIFICATION = """
You are an expert email analyst. Analyze the following email and classify its intent.

Email Details:
- From: {{ email.from_sender }}
- Subject: {{ email.subject }}
- Content: {{ email.content | truncate(500) }}
- Metadata: {{ email.metadata | tojson }}

Classify the email intent into one of these categories:
1. TRANSACTIONAL - Order confirmations, receipts, shipping notifications
2. PROMOTIONAL - Marketing, sales, discounts, newsletters
3. PERSONAL - Personal communications from individuals
4. WORK - Work-related, professional communications
5. NOTIFICATION - System notifications, alerts, updates
6. SOCIAL - Social media notifications
7. SPAM - Unwanted, potentially harmful content

Additionally, provide:
- Confidence score (0-1)
- Key indicators that led to this classification
- Secondary intent if applicable
- Suggested actions

Output in JSON format:
{
  "primary_intent": "CATEGORY",
  "confidence": 0.95,
  "indicators": ["indicator1", "indicator2"],
  "secondary_intent": "CATEGORY or null",
  "suggested_actions": ["action1", "action2"]
}
"""

    IMPORTANCE_RANKING = """
You are an email prioritization expert. Analyze this email and determine its importance level.

Email Context:
{{ email | tojson(indent=2) }}

User Context:
- Email patterns: {{ user_patterns | tojson }}
- Historical behavior: {{ user_behavior | tojson }}
- Current priorities: {{ priorities | tojson }}

Evaluate importance based on:
1. Sender importance (known contact, VIP, frequency)
2. Content urgency (deadlines, time-sensitive info)
3. Personal relevance (mentions user, requires action)
4. Business impact (financial, project-critical)
5. Emotional significance (personal relationships)

Output a detailed importance analysis:
{
  "importance_score": 0-100,
  "urgency_level": "IMMEDIATE|HIGH|MEDIUM|LOW",
  "factors": {
    "sender_importance": 0-100,
    "content_urgency": 0-100,
    "personal_relevance": 0-100,
    "business_impact": 0-100,
    "emotional_significance": 0-100
  },
  "key_phrases": ["phrase1", "phrase2"],
  "recommended_action": "description",
  "reasoning": "detailed explanation"
}
"""

    SMART_SUMMARIZATION = """
You are an expert at creating actionable email summaries. Create a multi-level summary of this email.

Email Content:
{{ email.full_content }}

Create three summary levels:
1. One-line summary (max 100 chars) - capture the essence
2. Executive summary (max 300 chars) - key points and required actions
3. Detailed summary - all important information, structured by topic

Additionally extract:
- Action items with deadlines
- Key decisions required
- Important dates/times
- Names and roles mentioned
- Attachments and their purpose
- Links and their context

Format:
{
  "one_line": "string",
  "executive": "string",
  "detailed": {
    "main_topics": ["topic1", "topic2"],
    "key_points": ["point1", "point2"],
    "context": "string"
  },
  "extractions": {
    "action_items": [{"task": "", "deadline": "", "assignee": ""}],
    "decisions_needed": ["decision1"],
    "dates": [{"date": "", "event": ""}],
    "people": [{"name": "", "role": "", "context": ""}],
    "attachments": [{"name": "", "purpose": ""}],
    "links": [{"url": "", "context": ""}]
  }
}
"""

    PATTERN_LEARNING = """
Analyze these emails to identify patterns and suggest automation rules.

Email Set:
{{ emails | tojson(indent=2) }}

Current Rules:
{{ existing_rules | tojson }}

Identify patterns in:
1. Sender patterns (domains, individuals, frequencies)
2. Subject patterns (keywords, formats, recurring themes)
3. Content patterns (structure, language, intent)
4. Temporal patterns (time of day, day of week, frequency)
5. Action patterns (user typically archives, labels, etc.)

For each pattern found:
- Calculate confidence based on occurrence frequency
- Identify exceptions or edge cases
- Suggest specific automation rules
- Estimate time savings

Output format:
{
  "patterns": [
    {
      "type": "sender|subject|content|temporal|action",
      "description": "clear description",
      "confidence": 0.95,
      "occurrences": 45,
      "examples": ["example1", "example2"],
      "exceptions": ["exception1"],
      "suggested_rule": {
        "conditions": [{"field": "", "operator": "", "value": ""}],
        "actions": [{"type": "", "parameters": {}}],
        "estimated_impact": {
          "emails_affected_per_month": 120,
          "time_saved_minutes": 20
        }
      }
    }
  ],
  "insights": ["insight1", "insight2"],
  "optimization_opportunities": ["opportunity1"]
}
"""

class PromptOptimizer:
    """Optimizes prompts for better performance"""
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.token_counter = TokenCounter()
        self.example_selector = DynamicExampleSelector(embedding_service=embedding_service)
    
    async def optimize_prompt( # Made async to support async example selection
        self,
        template: PromptTemplate,
        context: Dict[str, Any],
        max_tokens: int = 2000,
        model: str = "gpt-4"
    ) -> str:
        """Optimize prompt for token limit and relevance"""
        
        # Start with base prompt
        prompt = template.build(context)
        
        # Add relevant examples within token budget
        # Assuming template.examples is a list of dicts like [{"input_text": "...", "output_text": "..."}]
        # And context might contain {"text_to_embed": "some query text"} for similarity
        selected_examples = await self.example_selector.select_examples(
            template.examples, # These are the few-shot examples stored in the PromptTemplate instance
            context,           # This is the current input context for which the prompt is being built
            max_examples=3     # Or some other configurable number
        )
        
        # TODO: Incorporate selected_examples into the prompt string.
        # This depends on how examples are formatted in the prompt (e.g., a specific section).
        # For now, 'prompt' variable does not include these dynamic examples.
        # Example of how it might be done (needs PromptTemplate to support example formatting):
        # prompt_with_examples = template.format_with_examples(context, selected_examples)
        # current_token_count = self.token_counter.count(prompt_with_examples, model)

        # For now, we'll just use the original prompt for token counting and compression.
        # The 'examples' variable here is just for demonstration of selection.
        
        # Compress if needed
        if self.token_counter.count(prompt, model) > max_tokens:
            prompt = self._compress_prompt(prompt, max_tokens, model)
        
        return prompt
    
    def _compress_prompt(
        self, prompt: str, max_tokens: int, model: str
    ) -> str:
        """Compress prompt to fit token limit"""
        # Implementation of smart compression
        pass