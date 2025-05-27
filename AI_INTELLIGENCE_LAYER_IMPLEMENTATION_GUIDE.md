# AI Intelligence Layer Implementation Guide for Damien Email Wrestler

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Prerequisites and Setup](#prerequisites-and-setup)
4. [Phase 1: Natural Language Rule Creation](#phase-1-natural-language-rule-creation)
5. [Phase 2: Smart Email Categorization](#phase-2-smart-email-categorization)
6. [Phase 3: Conversational Interface](#phase-3-conversational-interface)
7. [Integration Strategy](#integration-strategy)
8. [Testing Strategy](#testing-strategy)
9. [Implementation Timeline](#implementation-timeline)

## Overview

This guide provides a complete implementation roadmap for adding AI intelligence capabilities to Damien Email Wrestler. The three core features we'll implement are:

1. **Natural Language Rule Creation**: Convert human-readable instructions into Damien rules
2. **Smart Email Categorization**: Automatically categorize and suggest rules based on email patterns
3. **Conversational Interface**: Enable complex email queries and actions through natural language

### Design Principles

- **Local-First**: All AI processing happens locally for privacy and speed
- **Modular Integration**: AI features integrate cleanly with existing architecture
- **Progressive Enhancement**: Each feature builds on the previous one
- **Fallback Safety**: AI suggestions always require user confirmation

## Architecture Design

### Directory Structure

```
damien-cli/
└── damien_cli/
    └── features/
        └── ai_intelligence/            # NEW AI feature module
            ├── __init__.py
            ├── commands.py             # CLI commands for AI features
            ├── models.py               # Pydantic models for AI data
            ├── natural_language/       # Natural language processing
            │   ├── __init__.py
            │   ├── rule_parser.py      # NL to rule conversion
            │   ├── grammar.py          # Rule grammar definitions
            │   └── validators.py       # Rule validation logic
            ├── categorization/         # Email categorization
            │   ├── __init__.py
            │   ├── categorizer.py      # Main categorization logic
            │   ├── embeddings.py       # Email embedding generation
            │   └── patterns.py         # Pattern detection algorithms
            ├── conversation/           # Conversational interface
            │   ├── __init__.py
            │   ├── query_engine.py     # Natural language query processor
            │   ├── context_manager.py  # Conversation context tracking
            │   └── response_builder.py # Response formatting
            └── llm_providers/          # LLM integration layer
                ├── __init__.py
                ├── base.py             # Abstract LLM provider
                ├── openai_provider.py  # OpenAI implementation
                └── local_provider.py   # Local model implementation
```

### Core Components

```python
# damien_cli/features/ai_intelligence/models.py

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime

class NaturalLanguageRule(BaseModel):
    """Represents a rule expressed in natural language"""
    instruction: str = Field(..., description="Natural language rule instruction")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    
class ParsedRuleIntent(BaseModel):
    """Parsed intent from natural language"""
    action: Literal["archive", "label", "trash", "mark_read", "mark_unread", "forward"]
    conditions: List[Dict[str, str]]
    parameters: Dict[str, any] = Field(default_factory=dict)
    confidence: float
    alternative_interpretations: List[Dict] = Field(default_factory=list)

class EmailCategory(BaseModel):
    """Represents an email category"""
    name: str
    description: str
    confidence: float
    suggested_rules: List[Dict]
    example_emails: List[str] = Field(default_factory=list)
    
class ConversationContext(BaseModel):
    """Tracks conversation state"""
    session_id: str
    messages: List[Dict[str, str]]
    current_query_context: Optional[Dict] = None
    email_refs: List[str] = Field(default_factory=list)
```

## Prerequisites and Setup

### 1. Install Required Dependencies

Update `damien-cli/pyproject.toml`:

```toml
[tool.poetry.dependencies]
# Existing dependencies...

# AI Intelligence Layer dependencies
openai = "^1.35.0"  # For GPT integration
tiktoken = "^0.7.0"  # For token counting
numpy = "^1.26.0"  # For embeddings
scikit-learn = "^1.4.0"  # For similarity calculations
langchain = "^0.2.0"  # For LLM chains and prompts
chromadb = "^0.4.0"  # For local vector storage
transformers = "^4.40.0"  # For local models (optional)
sentence-transformers = "^2.6.0"  # For email embeddings
```

### 2. Environment Configuration

Add to `.env`:

```bash
# AI Configuration
DAMIEN_AI_PROVIDER=openai  # or "local" for offline mode
DAMIEN_OPENAI_API_KEY=your-api-key-here
DAMIEN_AI_MODEL=gpt-4-turbo-preview  # or gpt-3.5-turbo for cost savings
DAMIEN_EMBEDDING_MODEL=text-embedding-3-small
DAMIEN_LOCAL_MODEL_PATH=/path/to/local/model  # For offline mode
DAMIEN_AI_TEMPERATURE=0.3  # Lower = more deterministic
DAMIEN_AI_MAX_TOKENS=2000
```

### 3. Create Base AI Module

```python
# damien_cli/features/ai_intelligence/__init__.py

"""AI Intelligence Layer for Damien Email Wrestler

This module provides natural language processing capabilities for:
- Converting natural language to email rules
- Categorizing emails intelligently
- Processing conversational queries
"""

from .natural_language.rule_parser import NaturalLanguageRuleParser
from .categorization.categorizer import EmailCategorizer
from .conversation.query_engine import ConversationalQueryEngine

__all__ = [
    'NaturalLanguageRuleParser',
    'EmailCategorizer', 
    'ConversationalQueryEngine'
]
```

## Phase 1: Natural Language Rule Creation

### Implementation Overview

The natural language rule creation system converts human instructions like "Archive all newsletters older than 30 days" into Damien rule objects.

### Step 1: LLM Provider Interface

```python
# damien_cli/features/ai_intelligence/llm_providers/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion for a prompt"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass
```

### Step 2: OpenAI Provider Implementation

```python
# damien_cli/features/ai_intelligence/llm_providers/openai_provider.py

import openai
import tiktoken
from typing import List, Optional
import asyncio
from damien_cli.core.config import settings
from .base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider for LLM operations"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.ai_model
        self.embedding_model = settings.embedding_model
        self.encoding = tiktoken.encoding_for_model(self.model)
        
    async def complete(self, prompt: str, temperature: float = 0.3, 
                      max_tokens: int = 2000, **kwargs) -> str:
        """Generate completion using OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert email rule parser for the Damien Email Wrestler system."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"OpenAI Embedding error: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.encoding.encode(text))
```

### Step 3: Natural Language Rule Parser

```python
# damien_cli/features/ai_intelligence/natural_language/rule_parser.py

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from damien_cli.features.rule_management.models import RuleModel, ConditionModel, ActionModel
from ..models import NaturalLanguageRule, ParsedRuleIntent
from ..llm_providers.base import BaseLLMProvider
from .grammar import RULE_GRAMMAR_PROMPT
from .validators import RuleValidator

class NaturalLanguageRuleParser:
    """Converts natural language instructions to Damien rules"""
    
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.validator = RuleValidator()
        
    async def parse_instruction(self, instruction: str) -> Tuple[RuleModel, ParsedRuleIntent]:
        """Parse natural language instruction into a Damien rule"""
        
        # Step 1: Extract intent using LLM
        intent = await self._extract_intent(instruction)
        
        # Step 2: Validate and refine the intent
        validated_intent = self.validator.validate_intent(intent)
        
        # Step 3: Convert to Damien rule model
        rule = self._intent_to_rule(validated_intent, instruction)
        
        return rule, validated_intent
    
    async def _extract_intent(self, instruction: str) -> ParsedRuleIntent:
        """Extract structured intent from natural language"""
        
        prompt = f"""
{RULE_GRAMMAR_PROMPT}

Convert this instruction into a structured email rule:
"{instruction}"

Respond with a JSON object containing:
{{
    "action": "archive|label|trash|mark_read|mark_unread|forward",
    "conditions": [
        {{"field": "from|to|subject|body|label|age_days|has_attachment", 
          "operator": "contains|equals|greater_than|less_than|not_contains",
          "value": "string or number"}}
    ],
    "parameters": {{
        "label_name": "string (if action is label)",
        "forward_to": "email (if action is forward)"
    }},
    "confidence": 0.0-1.0,
    "reasoning": "explanation of interpretation"
}}

Examples:
1. "Archive emails from newsletters older than 30 days"
   -> action: "archive", conditions: [{{"field": "from", "operator": "contains", "value": "newsletter"}}, {{"field": "age_days", "operator": "greater_than", "value": 30}}]

2. "Label emails from my boss as Important"
   -> action: "label", conditions: [{{"field": "from", "operator": "contains", "value": "boss"}}], parameters: {{"label_name": "Important"}}
"""
        
        response = await self.llm.complete(prompt, temperature=0.2)
        
        try:
            # Parse JSON response
            parsed = json.loads(response)
            
            # Convert to ParsedRuleIntent
            return ParsedRuleIntent(
                action=parsed["action"],
                conditions=parsed["conditions"],
                parameters=parsed.get("parameters", {}),
                confidence=parsed.get("confidence", 0.8)
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback: Try to extract intent using regex
            return self._fallback_parse(instruction)
    
    def _fallback_parse(self, instruction: str) -> ParsedRuleIntent:
        """Fallback parser using regex patterns"""
        
        instruction_lower = instruction.lower()
        
        # Detect action
        action = "archive"  # default
        if "label" in instruction_lower:
            action = "label"
        elif "trash" in instruction_lower or "delete" in instruction_lower:
            action = "trash"
        elif "mark as read" in instruction_lower:
            action = "mark_read"
        elif "mark as unread" in instruction_lower:
            action = "mark_unread"
        
        # Extract conditions using patterns
        conditions = []
        
        # From condition
        from_match = re.search(r'from\s+(["\']?)([^"\']+)\1', instruction_lower)
        if from_match:
            conditions.append({
                "field": "from",
                "operator": "contains",
                "value": from_match.group(2)
            })
        
        # Age condition
        age_match = re.search(r'older than\s+(\d+)\s+(day|week|month)', instruction_lower)
        if age_match:
            days = int(age_match.group(1))
            unit = age_match.group(2)
            if unit == "week":
                days *= 7
            elif unit == "month":
                days *= 30
            conditions.append({
                "field": "age_days",
                "operator": "greater_than",
                "value": days
            })
        
        # Subject condition
        subject_match = re.search(r'subject\s+(["\']?)([^"\']+)\1', instruction_lower)
        if subject_match:
            conditions.append({
                "field": "subject",
                "operator": "contains",
                "value": subject_match.group(2)
            })
        
        return ParsedRuleIntent(
            action=action,
            conditions=conditions,
            parameters={},
            confidence=0.6  # Lower confidence for fallback
        )
    
    def _intent_to_rule(self, intent: ParsedRuleIntent, original_instruction: str) -> RuleModel:
        """Convert ParsedRuleIntent to Damien RuleModel"""
        
        # Generate rule name from instruction
        rule_name = self._generate_rule_name(original_instruction)
        
        # Convert conditions
        conditions = []
        for cond in intent.conditions:
            # Map to Damien's condition model
            condition = ConditionModel(
                field=cond["field"],
                operator=cond["operator"],
                value=cond["value"]
            )
            conditions.append(condition)
        
        # Convert action
        action_type = intent.action
        action_params = {}
        
        if action_type == "label" and "label_name" in intent.parameters:
            action_params["label_name"] = intent.parameters["label_name"]
        elif action_type == "forward" and "forward_to" in intent.parameters:
            action_params["forward_to"] = intent.parameters["forward_to"]
        
        actions = [ActionModel(type=action_type, **action_params)]
        
        # Create rule
        rule = RuleModel(
            name=rule_name,
            description=f"Generated from: {original_instruction}",
            conditions=conditions,
            condition_conjunction="AND",
            actions=actions,
            is_enabled=True,
            metadata={
                "generated_by": "ai",
                "original_instruction": original_instruction,
                "confidence": intent.confidence
            }
        )
        
        return rule
    
    def _generate_rule_name(self, instruction: str) -> str:
        """Generate a concise rule name from instruction"""
        # Simple approach: take first few significant words
        words = instruction.split()
        significant_words = [w for w in words if len(w) > 3 and w.lower() not in 
                           ["from", "with", "that", "this", "email", "emails"]]
        
        if significant_words:
            return " ".join(significant_words[:3])
        else:
            return f"Rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
```

### Step 4: Grammar Definition

```python
# damien_cli/features/ai_intelligence/natural_language/grammar.py

RULE_GRAMMAR_PROMPT = """
You are an expert at parsing email management instructions. Convert natural language into structured email rules.

SUPPORTED FIELDS:
- from: Email sender (supports partial matching)
- to: Email recipient
- subject: Email subject line
- body: Email body content
- label: Gmail labels (e.g., INBOX, SPAM, IMPORTANT)
- age_days: Email age in days
- has_attachment: Whether email has attachments (true/false)
- size_mb: Email size in megabytes

SUPPORTED OPERATORS:
- contains: Field contains the value (case-insensitive)
- equals: Exact match
- not_contains: Field does not contain value
- greater_than: Numeric comparison (for age_days, size_mb)
- less_than: Numeric comparison
- matches_regex: Regular expression matching

SUPPORTED ACTIONS:
- archive: Move to archive
- label: Apply a Gmail label
- trash: Move to trash
- mark_read: Mark as read
- mark_unread: Mark as unread
- forward: Forward to email address

TIME EXPRESSIONS:
- "older than X days/weeks/months" -> age_days > X
- "newer than X days" -> age_days < X
- "from last week" -> age_days < 7
- "from this month" -> age_days < 30

COMMON PATTERNS:
- "newsletters" -> from contains "newsletter" OR subject contains "newsletter"
- "from my team" -> from contains "@mycompany.com"
- "important emails" -> label equals "IMPORTANT"
- "large attachments" -> has_attachment equals true AND size_mb > 10
"""

# Common email patterns for recognition
EMAIL_PATTERNS = {
    "newsletters": {
        "patterns": ["newsletter", "digest", "weekly update", "monthly roundup"],
        "fields": ["from", "subject"]
    },
    "notifications": {
        "patterns": ["notification", "alert", "reminder", "automated"],
        "fields": ["from", "subject"]
    },
    "receipts": {
        "patterns": ["receipt", "order", "invoice", "payment", "purchase"],
        "fields": ["subject", "body"]
    },
    "social": {
        "patterns": ["facebook", "twitter", "linkedin", "instagram"],
        "fields": ["from"]
    },
    "work": {
        "patterns": ["@company.com", "meeting", "project", "deadline"],
        "fields": ["from", "subject"]
    }
}
```

### Step 5: Rule Validator

```python
# damien_cli/features/ai_intelligence/natural_language/validators.py

from typing import Dict, List, Optional
from ..models import ParsedRuleIntent
from damien_cli.core_api.exceptions import InvalidParameterError

class RuleValidator:
    """Validates and refines parsed rule intents"""
    
    # Valid field-operator combinations
    VALID_COMBINATIONS = {
        "from": ["contains", "equals", "not_contains", "matches_regex"],
        "to": ["contains", "equals", "not_contains"],
        "subject": ["contains", "equals", "not_contains", "matches_regex"],
        "body": ["contains", "not_contains", "matches_regex"],
        "label": ["equals", "not_equals"],
        "age_days": ["greater_than", "less_than", "equals"],
        "has_attachment": ["equals"],
        "size_mb": ["greater_than", "less_than"]
    }
    
    def validate_intent(self, intent: ParsedRuleIntent) -> ParsedRuleIntent:
        """Validate and potentially fix parsed intent"""
        
        # Validate action
        valid_actions = ["archive", "label", "trash", "mark_read", "mark_unread", "forward"]
        if intent.action not in valid_actions:
            raise InvalidParameterError(f"Invalid action: {intent.action}")
        
        # Validate and fix conditions
        validated_conditions = []
        for condition in intent.conditions:
            validated_condition = self._validate_condition(condition)
            if validated_condition:
                validated_conditions.append(validated_condition)
        
        intent.conditions = validated_conditions
        
        # Validate action-specific parameters
        if intent.action == "label" and "label_name" not in intent.parameters:
            raise InvalidParameterError("Label action requires 'label_name' parameter")
        
        if intent.action == "forward" and "forward_to" not in intent.parameters:
            raise InvalidParameterError("Forward action requires 'forward_to' parameter")
        
        return intent
    
    def _validate_condition(self, condition: Dict) -> Optional[Dict]:
        """Validate a single condition"""
        
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        # Check required fields
        if not all([field, operator, value is not None]):
            return None
        
        # Validate field-operator combination
        if field not in self.VALID_COMBINATIONS:
            return None
        
        if operator not in self.VALID_COMBINATIONS[field]:
            # Try to fix common mistakes
            if operator == "is" and field in ["has_attachment"]:
                operator = "equals"
            elif operator == ">" and field in ["age_days", "size_mb"]:
                operator = "greater_than"
            elif operator == "<" and field in ["age_days", "size_mb"]:
                operator = "less_than"
            else:
                return None
        
        # Type conversion
        if field in ["age_days", "size_mb"]:
            try:
                value = float(value)
            except (ValueError, TypeError):
                return None
        
        if field == "has_attachment":
            value = str(value).lower() in ["true", "yes", "1"]
        
        return {
            "field": field,
            "operator": operator,
            "value": value
        }
```

### Step 6: CLI Commands

```python
# damien_cli/features/ai_intelligence/commands.py

import click
import asyncio
from typing import Optional
from damien_cli.core.cli_utils import format_output
from damien_cli.features.rule_management.models import RuleModel
from .natural_language.rule_parser import NaturalLanguageRuleParser
from .llm_providers.openai_provider import OpenAIProvider
import json

@click.group(name="ai")
def ai_group():
    """AI-powered email management commands"""
    pass

@ai_group.command(name="create-rule")
@click.argument("instruction", type=str)
@click.option("--dry-run", is_flag=True, help="Preview rule without saving")
@click.option("--output-format", type=click.Choice(["human", "json"]), default="human")
@click.pass_context
def create_rule_from_nl(ctx, instruction: str, dry_run: bool, output_format: str):
    """Create an email rule from natural language instruction"""
    
    async def _create_rule():
        # Initialize components
        llm_provider = OpenAIProvider()
        parser = NaturalLanguageRuleParser(llm_provider)
        
        try:
            # Parse instruction
            click.echo(f"Parsing instruction: '{instruction}'...")
            rule, intent = await parser.parse_instruction(instruction)
            
            if output_format == "json":
                output = {
                    "success": True,
                    "rule": rule.dict(),
                    "intent": intent.dict(),
                    "instruction": instruction
                }
                click.echo(json.dumps(output, indent=2))
            else:
                # Human-readable output
                click.echo("\n✅ Successfully parsed instruction!")
                click.echo(f"\nRule Name: {rule.name}")
                click.echo(f"Description: {rule.description}")
                click.echo(f"Confidence: {intent.confidence:.0%}")
                
                click.echo("\nConditions:")
                for i, cond in enumerate(rule.conditions, 1):
                    click.echo(f"  {i}. {cond.field} {cond.operator} '{cond.value}'")
                
                click.echo(f"\nAction: {rule.actions[0].type}")
                if rule.actions[0].type == "label":
                    click.echo(f"  Label: {rule.actions[0].label_name}")
                
                if not dry_run:
                    # Save the rule
                    from damien_cli.core_api.rules_api_service import add_rule
                    saved_rule = add_rule(rule.dict())
                    click.echo(f"\n✅ Rule saved with ID: {saved_rule['id']}")
                else:
                    click.echo("\n🔍 Dry run mode - rule not saved")
                    
        except Exception as e:
            if output_format == "json":
                output = {
                    "success": False,
                    "error": str(e),
                    "instruction": instruction
                }
                click.echo(json.dumps(output, indent=2))
            else:
                click.secho(f"\n❌ Error: {str(e)}", fg="red")
    
    # Run async function
    asyncio.run(_create_rule())

@ai_group.command(name="suggest-rules")
@click.option("--limit", type=int, default=5, help="Number of suggestions")
@click.option("--min-confidence", type=float, default=0.7, help="Minimum confidence threshold")
@click.pass_context
def suggest_rules(ctx, limit: int, min_confidence: float):
    """Analyze emails and suggest rules"""
    
    # This will be implemented in Phase 2
    click.echo("Email analysis and rule suggestions coming in Phase 2!")
```

## Phase 2: Smart Email Categorization

### Implementation Overview

The smart email categorization system analyzes your emails to:
- Identify patterns and categories
- Suggest rules based on behavior
- Learn from user feedback

### Step 1: Email Embeddings

```python
# damien_cli/features/ai_intelligence/categorization/embeddings.py

import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import hashlib
import pickle
from pathlib import Path
from damien_cli.core.config import DATA_DIR

class EmailEmbeddingGenerator:
    """Generates and caches embeddings for emails"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.cache_dir = Path(DATA_DIR) / "embeddings_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
    def generate_embedding(self, email_data: Dict) -> np.ndarray:
        """Generate embedding for an email"""
        
        # Create cache key
        cache_key = self._get_cache_key(email_data)
        cached_embedding = self._load_from_cache(cache_key)
        
        if cached_embedding is not None:
            return cached_embedding
        
        # Prepare text for embedding
        text = self._prepare_email_text(email_data)
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Cache the result
        self._save_to_cache(cache_key, embedding)
        
        return embedding
    
    def generate_batch_embeddings(self, emails: List[Dict]) -> np.ndarray:
        """Generate embeddings for multiple emails efficiently"""
        
        texts = [self._prepare_email_text(email) for email in emails]
        embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
        
        return embeddings
    
    def _prepare_email_text(self, email_data: Dict) -> str:
        """Prepare email text for embedding"""
        
        # Extract relevant fields
        from_sender = email_data.get("from_sender", "")
        subject = email_data.get("subject", "")
        snippet = email_data.get("snippet", "")
        labels = " ".join(email_data.get("label_names", []))
        
        # Combine fields with weights
        text = f"FROM: {from_sender}\nSUBJECT: {subject}\nCONTENT: {snippet}\nLABELS: {labels}"
        
        return text
    
    def _get_cache_key(self, email_data: Dict) -> str:
        """Generate cache key for email"""
        email_id = email_data.get("id", "")
        return hashlib.md5(email_id.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """Load embedding from cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        return None
    
    def _save_to_cache(self, cache_key: str, embedding: np.ndarray):
        """Save embedding to cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        with open(cache_file, "wb") as f:
            pickle.dump(embedding, f)
```

### Step 2: Pattern Detection

```python
# damien_cli/features/ai_intelligence/categorization/patterns.py

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set
import re

class EmailPatternDetector:
    """Detects patterns in email collections"""
    
    def __init__(self):
        self.sender_patterns = defaultdict(list)
        self.subject_patterns = defaultdict(list)
        self.time_patterns = defaultdict(list)
        
    def detect_patterns(self, emails: List[Dict], embeddings: np.ndarray) -> List[Dict]:
        """Detect various patterns in emails"""
        
        patterns = []
        
        # 1. Clustering-based patterns
        cluster_patterns = self._detect_cluster_patterns(emails, embeddings)
        patterns.extend(cluster_patterns)
        
        # 2. Sender-based patterns
        sender_patterns = self._detect_sender_patterns(emails)
        patterns.extend(sender_patterns)
        
        # 3. Subject line patterns
        subject_patterns = self._detect_subject_patterns(emails)
        patterns.extend(subject_patterns)
        
        # 4. Time-based patterns
        time_patterns = self._detect_time_patterns(emails)
        patterns.extend(time_patterns)
        
        # 5. Label correlation patterns
        label_patterns = self._detect_label_patterns(emails)
        patterns.extend(label_patterns)
        
        return patterns
    
    def _detect_cluster_patterns(self, emails: List[Dict], embeddings: np.ndarray) -> List[Dict]:
        """Use DBSCAN clustering to find email groups"""
        
        if len(embeddings) < 5:
            return []
        
        # Normalize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)
        
        # Cluster emails
        clustering = DBSCAN(eps=0.3, min_samples=3).fit(embeddings_scaled)
        
        # Analyze clusters
        patterns = []
        unique_labels = set(clustering.labels_)
        
        for label in unique_labels:
            if label == -1:  # Skip noise
                continue
                
            # Get emails in this cluster
            cluster_indices = np.where(clustering.labels_ == label)[0]
            cluster_emails = [emails[i] for i in cluster_indices]
            
            # Find common characteristics
            pattern = self._analyze_cluster(cluster_emails)
            if pattern:
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_cluster(self, emails: List[Dict]) -> Optional[Dict]:
        """Analyze a cluster of emails to find patterns"""
        
        # Extract common features
        senders = [e.get("from_sender", "") for e in emails]
        subjects = [e.get("subject", "") for e in emails]
        labels = [label for e in emails for label in e.get("label_names", [])]
        
        # Find most common sender
        sender_counter = Counter(senders)
        most_common_sender = sender_counter.most_common(1)[0] if sender_counter else None
        
        # Find common subject words
        subject_words = []
        for subject in subjects:
            words = re.findall(r'\b\w+\b', subject.lower())
            subject_words.extend(words)
        
        word_counter = Counter(subject_words)
        common_words = [word for word, count in word_counter.most_common(5) 
                       if count >= len(emails) * 0.5]  # Word appears in 50% of emails
        
        # Find common labels
        label_counter = Counter(labels)
        common_labels = [label for label, count in label_counter.most_common(3)
                        if count >= len(emails) * 0.7]  # Label on 70% of emails
        
        if not any([most_common_sender, common_words, common_labels]):
            return None
        
        pattern = {
            "type": "cluster",
            "email_count": len(emails),
            "characteristics": {
                "common_sender": most_common_sender[0] if most_common_sender else None,
                "common_subject_words": common_words,
                "common_labels": common_labels
            },
            "example_emails": [e["id"] for e in emails[:3]],
            "suggested_rule": self._suggest_rule_from_cluster(
                most_common_sender, common_words, common_labels
            )
        }
        
        return pattern
    
    def _detect_sender_patterns(self, emails: List[Dict]) -> List[Dict]:
        """Detect patterns based on email senders"""
        
        sender_groups = defaultdict(list)
        for email in emails:
            sender = email.get("from_sender", "")
            if sender:
                sender_groups[sender].append(email)
        
        patterns = []
        for sender, sender_emails in sender_groups.items():
            if len(sender_emails) >= 5:  # Significant volume
                # Analyze this sender's emails
                pattern = {
                    "type": "high_volume_sender",
                    "sender": sender,
                    "email_count": len(sender_emails),
                    "characteristics": {
                        "average_per_day": self._calculate_email_frequency(sender_emails),
                        "common_subjects": self._get_common_subjects(sender_emails),
                        "usually_has_attachments": self._check_attachment_pattern(sender_emails)
                    },
                    "suggested_rule": {
                        "conditions": [{"field": "from", "operator": "equals", "value": sender}],
                        "suggested_actions": ["label", "archive"]
                    }
                }
                patterns.append(pattern)
        
        return patterns
    
    def _detect_subject_patterns(self, emails: List[Dict]) -> List[Dict]:
        """Detect patterns in subject lines"""
        
        patterns = []
        
        # Newsletter patterns
        newsletter_keywords = ["newsletter", "digest", "weekly", "monthly", "update"]
        newsletter_emails = []
        
        for email in emails:
            subject = email.get("subject", "").lower()
            if any(keyword in subject for keyword in newsletter_keywords):
                newsletter_emails.append(email)
        
        if len(newsletter_emails) >= 3:
            patterns.append({
                "type": "newsletter",
                "email_count": len(newsletter_emails),
                "characteristics": {
                    "senders": list(set(e.get("from_sender", "") for e in newsletter_emails))[:5]
                },
                "suggested_rule": {
                    "conditions": [
                        {"field": "subject", "operator": "contains", "value": "newsletter"},
                        {"field": "subject", "operator": "contains", "value": "digest"}
                    ],
                    "condition_conjunction": "OR",
                    "suggested_actions": ["label", "archive"]
                }
            })
        
        return patterns
    
    def _detect_time_patterns(self, emails: List[Dict]) -> List[Dict]:
        """Detect time-based patterns"""
        
        # This is a placeholder for time pattern detection
        # In a full implementation, you would analyze:
        # - Emails received at specific times
        # - Regular intervals (daily, weekly reports)
        # - Business hours vs after hours
        
        return []
    
    def _detect_label_patterns(self, emails: List[Dict]) -> List[Dict]:
        """Detect patterns in how emails are labeled"""
        
        # Analyze which types of emails tend to get certain labels
        label_associations = defaultdict(lambda: defaultdict(int))
        
        for email in emails:
            labels = email.get("label_names", [])
            sender_domain = self._extract_domain(email.get("from_sender", ""))
            
            for label in labels:
                if sender_domain:
                    label_associations[label]["domains"][sender_domain] += 1
                
                # Check for subject patterns
                subject = email.get("subject", "").lower()
                if "invoice" in subject or "receipt" in subject:
                    label_associations[label]["types"]["receipt"] += 1
                elif "meeting" in subject or "calendar" in subject:
                    label_associations[label]["types"]["meeting"] += 1
        
        patterns = []
        # Convert associations to patterns
        # This is simplified - you'd want more sophisticated analysis
        
        return patterns
    
    def _suggest_rule_from_cluster(self, sender_info, common_words, common_labels):
        """Generate rule suggestion from cluster analysis"""
        
        conditions = []
        
        if sender_info:
            conditions.append({
                "field": "from",
                "operator": "equals",
                "value": sender_info[0]
            })
        
        if common_words:
            # Use the most distinctive word
            conditions.append({
                "field": "subject",
                "operator": "contains", 
                "value": common_words[0]
            })
        
        # Suggest action based on current labels
        if "TRASH" in common_labels:
            suggested_action = "trash"
        elif "SPAM" in common_labels:
            suggested_action = "trash"
        elif any(label.startswith("Label_") for label in common_labels):
            suggested_action = "label"
        else:
            suggested_action = "archive"
        
        return {
            "conditions": conditions,
            "suggested_action": suggested_action,
            "confidence": 0.8
        }
    
    def _extract_domain(self, email_address: str) -> str:
        """Extract domain from email address"""
        if "@" in email_address:
            return email_address.split("@")[1].lower()
        return ""
    
    def _calculate_email_frequency(self, emails: List[Dict]) -> float:
        """Calculate average emails per day"""
        # Simplified - would need actual date parsing
        return len(emails) / 30  # Assume 30 day period
    
    def _get_common_subjects(self, emails: List[Dict]) -> List[str]:
        """Get most common subject patterns"""
        subjects = [e.get("subject", "") for e in emails]
        # Simplified - would use more sophisticated analysis
        return list(set(subjects))[:3]
    
    def _check_attachment_pattern(self, emails: List[Dict]) -> bool:
        """Check if sender usually includes attachments"""
        with_attachments = sum(1 for e in emails if e.get("has_attachments", False))
        return with_attachments / len(emails) > 0.5
```

### Step 3: Email Categorizer

```python
# damien_cli/features/ai_intelligence/categorization/categorizer.py

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from damien_cli.core_api.gmail_api_service import list_messages, get_message_details
from damien_cli.core.config import DATA_DIR
from .embeddings import EmailEmbeddingGenerator
from .patterns import EmailPatternDetector
from ..models import EmailCategory

class EmailCategorizer:
    """Main class for email categorization and rule suggestions"""
    
    def __init__(self):
        self.embedding_generator = EmailEmbeddingGenerator()
        self.pattern_detector = EmailPatternDetector()
        self.categories_file = Path(DATA_DIR) / "email_categories.json"
        self.learned_patterns_file = Path(DATA_DIR) / "learned_patterns.json"
        
    async def analyze_emails(self, 
                           query: Optional[str] = None,
                           max_emails: int = 500,
                           days_back: int = 30) -> Dict:
        """Analyze emails and generate categorization insights"""
        
        # Build query
        if not query:
            date_filter = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
            query = f"after:{date_filter}"
        
        # Fetch emails
        click.echo(f"Fetching emails with query: {query}")
        email_summaries = []
        page_token = None
        
        while len(email_summaries) < max_emails:
            batch_size = min(100, max_emails - len(email_summaries))
            result = list_messages(
                gmail_service=self._get_gmail_service(),
                query=query,
                max_results=batch_size,
                page_token=page_token
            )
            
            email_summaries.extend(result["messages"])
            page_token = result.get("next_page_token")
            
            if not page_token:
                break
        
        click.echo(f"Analyzing {len(email_summaries)} emails...")
        
        # Generate embeddings
        embeddings = self.embedding_generator.generate_batch_embeddings(email_summaries)
        
        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(email_summaries, embeddings)
        
        # Generate categories
        categories = self._patterns_to_categories(patterns)
        
        # Save results
        self._save_categories(categories)
        self._save_patterns(patterns)
        
        return {
            "emails_analyzed": len(email_summaries),
            "patterns_found": len(patterns),
            "categories_identified": len(categories),
            "categories": categories,
            "top_suggestions": self._generate_top_suggestions(patterns, categories)
        }
    
    def _patterns_to_categories(self, patterns: List[Dict]) -> List[EmailCategory]:
        """Convert detected patterns into email categories"""
        
        categories = []
        
        # Group patterns by type
        pattern_groups = {}
        for pattern in patterns:
            pattern_type = pattern["type"]
            if pattern_type not in pattern_groups:
                pattern_groups[pattern_type] = []
            pattern_groups[pattern_type].append(pattern)
        
        # Create categories from pattern groups
        for pattern_type, type_patterns in pattern_groups.items():
            if pattern_type == "newsletter":
                category = EmailCategory(
                    name="Newsletters & Digests",
                    description="Regular updates and newsletters",
                    confidence=0.9,
                    suggested_rules=[{
                        "name": "Auto-archive newsletters",
                        "conditions": [
                            {"field": "subject", "operator": "contains", "value": "newsletter"}
                        ],
                        "action": "archive"
                    }],
                    example_emails=[p["example_emails"][0] for p in type_patterns[:3] 
                                   if "example_emails" in p]
                )
                categories.append(category)
                
            elif pattern_type == "high_volume_sender":
                for pattern in type_patterns[:5]:  # Top 5 high volume senders
                    category = EmailCategory(
                        name=f"Emails from {pattern['sender']}",
                        description=f"High volume sender ({pattern['email_count']} emails)",
                        confidence=0.85,
                        suggested_rules=[{
                            "name": f"Manage {pattern['sender']}",
                            "conditions": pattern["suggested_rule"]["conditions"],
                            "action": "label",
                            "parameters": {"label_name": f"Sender/{pattern['sender'].split('@')[0]}"}
                        }]
                    )
                    categories.append(category)
                    
            elif pattern_type == "cluster":
                # Create category from cluster characteristics
                chars = pattern["characteristics"]
                if chars.get("common_subject_words"):
                    name = f"{chars['common_subject_words'][0].title()} Emails"
                elif chars.get("common_sender"):
                    name = f"Emails like {chars['common_sender']}"
                else:
                    name = f"Email Group {len(categories) + 1}"
                    
                category = EmailCategory(
                    name=name,
                    description=f"Group of {pattern['email_count']} similar emails",
                    confidence=0.75,
                    suggested_rules=[pattern["suggested_rule"]] if "suggested_rule" in pattern else []
                )
                categories.append(category)
        
        return categories
    
    def _generate_top_suggestions(self, patterns: List[Dict], 
                                categories: List[EmailCategory]) -> List[Dict]:
        """Generate top rule suggestions based on patterns and categories"""
        
        suggestions = []
        
        # High-impact suggestions (would affect many emails)
        for pattern in sorted(patterns, key=lambda p: p.get("email_count", 0), reverse=True)[:5]:
            if "suggested_rule" in pattern:
                suggestion = {
                    "impact": pattern["email_count"],
                    "type": pattern["type"],
                    "rule": pattern["suggested_rule"],
                    "description": self._describe_suggestion(pattern)
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _describe_suggestion(self, pattern: Dict) -> str:
        """Generate human-readable description of a suggestion"""
        
        if pattern["type"] == "newsletter":
            return f"Archive {pattern['email_count']} newsletter emails automatically"
        elif pattern["type"] == "high_volume_sender":
            return f"Organize {pattern['email_count']} emails from {pattern['sender']}"
        elif pattern["type"] == "cluster":
            chars = pattern["characteristics"]
            if chars.get("common_subject_words"):
                return f"Handle {pattern['email_count']} emails about {chars['common_subject_words'][0]}"
            else:
                return f"Manage group of {pattern['email_count']} similar emails"
        else:
            return f"Process {pattern['email_count']} emails"
    
    def _save_categories(self, categories: List[EmailCategory]):
        """Save categories to file"""
        data = [cat.dict() for cat in categories]
        with open(self.categories_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _save_patterns(self, patterns: List[Dict]):
        """Save learned patterns"""
        with open(self.learned_patterns_file, "w") as f:
            json.dump(patterns, f, indent=2, default=str)
    
    def _get_gmail_service(self):
        """Get Gmail service from context"""
        # This would come from Click context in real implementation
        from damien_cli.core_api.gmail_api_service import get_authenticated_service
        return get_authenticated_service()
```

### Step 4: Add Categorization Commands

```python
# Add to damien_cli/features/ai_intelligence/commands.py

@ai_group.command(name="analyze")
@click.option("--days", type=int, default=30, help="Number of days to analyze")
@click.option("--max-emails", type=int, default=500, help="Maximum emails to analyze")
@click.option("--query", type=str, help="Custom Gmail query")
@click.pass_context
def analyze_emails(ctx, days: int, max_emails: int, query: Optional[str]):
    """Analyze emails and suggest categorization rules"""
    
    async def _analyze():
        categorizer = EmailCategorizer()
        
        with click.progressbar(length=100, label="Analyzing emails") as bar:
            # Simulate progress
            bar.update(10)
            
            results = await categorizer.analyze_emails(
                query=query,
                max_emails=max_emails,
                days_back=days
            )
            
            bar.update(90)
        
        # Display results
        click.echo(f"\n📊 Analysis Complete!")
        click.echo(f"Emails analyzed: {results['emails_analyzed']}")
        click.echo(f"Patterns found: {results['patterns_found']}")
        click.echo(f"Categories identified: {results['categories_identified']}")
        
        # Show top categories
        click.echo("\n📁 Top Email Categories:")
        for i, category in enumerate(results['categories'][:5], 1):
            click.echo(f"\n{i}. {category['name']}")
            click.echo(f"   Description: {category['description']}")
            click.echo(f"   Confidence: {category['confidence']:.0%}")
            
            if category['suggested_rules']:
                click.echo("   Suggested rule:")
                rule = category['suggested_rules'][0]
                click.echo(f"     - {rule}")
        
        # Show top suggestions
        click.echo("\n💡 Top Rule Suggestions:")
        for i, suggestion in enumerate(results['top_suggestions'][:5], 1):
            click.echo(f"\n{i}. {suggestion['description']}")
            click.echo(f"   Impact: {suggestion['impact']} emails")
            click.echo(f"   Type: {suggestion['type']}")
        
        # Offer to create rules
        if results['top_suggestions']:
            if click.confirm("\nWould you like to create rules from these suggestions?"):
                # Implementation for rule creation workflow
                click.echo("Rule creation workflow to be implemented...")
    
    asyncio.run(_analyze())

@ai_group.command(name="learn")
@click.option("--feedback-file", type=click.Path(exists=True), help="File with user feedback")
@click.pass_context
def learn_from_feedback(ctx, feedback_file: Optional[str]):
    """Learn from user feedback to improve categorization"""
    
    # This would implement feedback learning
    click.echo("Feedback learning system - coming soon!")
```

## Phase 3: Conversational Interface

### Implementation Overview

The conversational interface enables natural language queries about emails and complex operations through conversation.

### Step 1: Query Engine

```python
# damien_cli/features/ai_intelligence/conversation/query_engine.py

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..llm_providers.base import BaseLLMProvider
from ..models import ConversationContext
from damien_cli.core_api import gmail_api_service

class ConversationalQueryEngine:
    """Processes natural language queries about emails"""
    
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.context_manager = ConversationContextManager()
        
    async def process_query(self, 
                          query: str, 
                          session_id: str,
                          context: Optional[ConversationContext] = None) -> Dict:
        """Process a natural language query"""
        
        # Load or create context
        if not context:
            context = self.context_manager.get_or_create_context(session_id)
        
        # Add query to context
        context.messages.append({"role": "user", "content": query})
        
        # Determine query intent
        intent = await self._analyze_query_intent(query, context)
        
        # Execute based on intent
        result = await self._execute_intent(intent, context)
        
        # Update context with result
        context.messages.append({"role": "assistant", "content": result["response"]})
        if "email_refs" in result:
            context.email_refs.extend(result["email_refs"])
        
        # Save context
        self.context_manager.save_context(context)
        
        return result
    
    async def _analyze_query_intent(self, query: str, context: ConversationContext) -> Dict:
        """Analyze what the user is asking for"""
        
        prompt = f"""
Analyze this email-related query and determine the intent.

Query: "{query}"

Previous context:
{self._format_context(context, last_n=3)}

Determine:
1. Intent type: search, summarize, action, or question
2. Email criteria (if searching)
3. Action to perform (if action)
4. Time range (if applicable)

Respond in JSON:
{{
    "intent_type": "search|summarize|action|question",
    "criteria": {{
        "from": "sender if specified",
        "to": "recipient if specified", 
        "subject": "subject keywords",
        "body": "body keywords",
        "time_range": "today|this_week|last_week|custom",
        "has_attachment": true/false,
        "is_unread": true/false,
        "labels": ["label1", "label2"]
    }},
    "action": "archive|trash|label|mark_read|forward|reply",
    "action_params": {{}},
    "limit": 10
}}

Examples:
- "Show me unread emails from John" -> intent_type: "search", criteria: {{from: "John", is_unread: true}}
- "Summarize emails from today" -> intent_type: "summarize", criteria: {{time_range: "today"}}
- "Archive all newsletters" -> intent_type: "action", action: "archive", criteria: {{subject: "newsletter"}}
"""
        
        response = await self.llm.complete(prompt, temperature=0.2)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to simple search
            return {
                "intent_type": "search",
                "criteria": {"body": query},
                "limit": 10
            }
    
    async def _execute_intent(self, intent: Dict, context: ConversationContext) -> Dict:
        """Execute the analyzed intent"""
        
        intent_type = intent.get("intent_type", "search")
        
        if intent_type == "search":
            return await self._execute_search(intent, context)
        elif intent_type == "summarize":
            return await self._execute_summarize(intent, context)
        elif intent_type == "action":
            return await self._execute_action(intent, context)
        elif intent_type == "question":
            return await self._execute_question(intent, context)
        else:
            return {
                "response": "I'm not sure how to help with that. Could you rephrase your request?",
                "success": False
            }
    
    async def _execute_search(self, intent: Dict, context: ConversationContext) -> Dict:
        """Execute email search based on intent"""
        
        # Build Gmail query from criteria
        gmail_query = self._build_gmail_query(intent.get("criteria", {}))
        
        # Search emails
        service = self._get_gmail_service()
        results = gmail_api_service.list_messages(
            gmail_service=service,
            query=gmail_query,
            max_results=intent.get("limit", 10)
        )
        
        emails = results.get("messages", [])
        
        if not emails:
            return {
                "response": "I couldn't find any emails matching your criteria.",
                "success": True,
                "emails": []
            }
        
        # Format response
        response_text = f"I found {len(emails)} email(s) matching your search:\n\n"
        
        email_refs = []
        for i, email in enumerate(emails[:5], 1):  # Show first 5
            response_text += f"{i}. From: {email['from_sender']}\n"
            response_text += f"   Subject: {email['subject']}\n"
            response_text += f"   Date: {email['date']}\n"
            response_text += f"   Preview: {email['snippet'][:100]}...\n\n"
            email_refs.append(email['id'])
        
        if len(emails) > 5:
            response_text += f"... and {len(emails) - 5} more email(s).\n"
        
        response_text += "\nWhat would you like to do with these emails?"
        
        return {
            "response": response_text,
            "success": True,
            "emails": emails,
            "email_refs": email_refs
        }
    
    async def _execute_summarize(self, intent: Dict, context: ConversationContext) -> Dict:
        """Summarize emails based on criteria"""
        
        # First search for emails
        search_result = await self._execute_search(intent, context)
        
        if not search_result["emails"]:
            return search_result
        
        # Get email details for summarization
        emails = search_result["emails"][:10]  # Limit to 10 for API costs
        
        email_contents = []
        for email in emails:
            details = gmail_api_service.get_message_details(
                gmail_service=self._get_gmail_service(),
                message_id=email['id'],
                format_option='metadata'
            )
            email_contents.append({
                "from": email['from_sender'],
                "subject": email['subject'],
                "snippet": email['snippet'],
                "date": email['date']
            })
        
        # Generate summary
        summary_prompt = f"""
Summarize these emails concisely:

{json.dumps(email_contents, indent=2)}

Provide:
1. Overall summary (2-3 sentences)
2. Key themes or topics
3. Any urgent items
4. Suggested actions
"""
        
        summary = await self.llm.complete(summary_prompt, temperature=0.3)
        
        return {
            "response": f"Summary of {len(emails)} email(s):\n\n{summary}",
            "success": True,
            "emails": emails,
            "email_refs": [e['id'] for e in emails]
        }
    
    async def _execute_action(self, intent: Dict, context: ConversationContext) -> Dict:
        """Execute an action on emails"""
        
        action = intent.get("action")
        criteria = intent.get("criteria", {})
        
        # First find the emails
        search_intent = {"criteria": criteria, "limit": 1000}  # Higher limit for actions
        search_result = await self._execute_search(search_intent, context)
        
        if not search_result["emails"]:
            return {
                "response": "I couldn't find any emails to perform that action on.",
                "success": False
            }
        
        email_ids = [e['id'] for e in search_result["emails"]]
        
        # Confirm action
        response = f"I found {len(email_ids)} email(s) to {action}. "
        
        # For destructive actions, list some examples
        if action in ["trash", "archive"] and len(email_ids) > 3:
            response += "Here are a few examples:\n"
            for email in search_result["emails"][:3]:
                response += f"- {email['subject']} (from {email['from_sender']})\n"
            response += f"... and {len(email_ids) - 3} more.\n\n"
        
        response += f"This action will be simulated (dry-run). In production, you would confirm before executing."
        
        # Simulate the action (in production, this would actually execute)
        action_result = {
            "action": action,
            "email_count": len(email_ids),
            "email_ids": email_ids[:10],  # First 10 for reference
            "dry_run": True
        }
        
        return {
            "response": response,
            "success": True,
            "action_result": action_result,
            "email_refs": email_ids
        }
    
    async def _execute_question(self, intent: Dict, context: ConversationContext) -> Dict:
        """Answer questions about emails or the system"""
        
        # This would handle questions like:
        # - "How many emails do I have from Amazon?"
        # - "What's my most frequent sender?"
        # - "When was the last email from John?"
        
        # For now, return a placeholder
        return {
            "response": "I can help you search, summarize, and manage your emails. Try asking me to find specific emails or summarize your inbox!",
            "success": True
        }
    
    def _build_gmail_query(self, criteria: Dict) -> str:
        """Convert criteria dict to Gmail query string"""
        
        query_parts = []
        
        if criteria.get("from"):
            query_parts.append(f'from:{criteria["from"]}')
        
        if criteria.get("to"):
            query_parts.append(f'to:{criteria["to"]}')
            
        if criteria.get("subject"):
            query_parts.append(f'subject:{criteria["subject"]}')
            
        if criteria.get("body"):
            query_parts.append(f'{criteria["body"]}')
            
        if criteria.get("is_unread"):
            query_parts.append("is:unread")
            
        if criteria.get("has_attachment"):
            query_parts.append("has:attachment")
            
        if criteria.get("labels"):
            for label in criteria["labels"]:
                query_parts.append(f'label:{label}')
        
        # Time range
        time_range = criteria.get("time_range")
        if time_range == "today":
            query_parts.append(f'after:{datetime.now().strftime("%Y/%m/%d")}')
        elif time_range == "this_week":
            week_ago = datetime.now() - timedelta(days=7)
            query_parts.append(f'after:{week_ago.strftime("%Y/%m/%d")}')
        elif time_range == "last_week":
            two_weeks = datetime.now() - timedelta(days=14)
            one_week = datetime.now() - timedelta(days=7)
            query_parts.append(f'after:{two_weeks.strftime("%Y/%m/%d")}')
            query_parts.append(f'before:{one_week.strftime("%Y/%m/%d")}')
        
        return " ".join(query_parts)
    
    def _format_context(self, context: ConversationContext, last_n: int = 5) -> str:
        """Format conversation context for prompt"""
        
        if not context.messages:
            return "No previous messages."
        
        formatted = []
        for msg in context.messages[-last_n:]:
            role = msg["role"].capitalize()
            content = msg["content"]
            if len(content) > 200:
                content = content[:200] + "..."
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _get_gmail_service(self):
        """Get Gmail service"""
        from damien_cli.core_api.gmail_api_service import get_authenticated_service
        return get_authenticated_service()
```

### Step 2: Context Manager

```python
# damien_cli/features/ai_intelligence/conversation/context_manager.py

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from ..models import ConversationContext
from damien_cli.core.config import DATA_DIR

class ConversationContextManager:
    """Manages conversation contexts across sessions"""
    
    def __init__(self):
        self.contexts_dir = Path(DATA_DIR) / "conversation_contexts"
        self.contexts_dir.mkdir(exist_ok=True)
        
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing context or create new one"""
        
        context_file = self.contexts_dir / f"{session_id}.json"
        
        if context_file.exists():
            with open(context_file, "r") as f:
                data = json.load(f)
                return ConversationContext(**data)
        else:
            return ConversationContext(session_id=session_id, messages=[])
    
    def save_context(self, context: ConversationContext):
        """Save context to disk"""
        
        context_file = self.contexts_dir / f"{context.session_id}.json"
        with open(context_file, "w") as f:
            json.dump(context.dict(), f, indent=2, default=str)
    
    def clear_context(self, session_id: str):
        """Clear a conversation context"""
        
        context_file = self.contexts_dir / f"{session_id}.json"
        if context_file.exists():
            context_file.unlink()
    
    def list_sessions(self) -> List[Dict]:
        """List all conversation sessions"""
        
        sessions = []
        for context_file in self.contexts_dir.glob("*.json"):
            with open(context_file, "r") as f:
                data = json.load(f)
                sessions.append({
                    "session_id": data["session_id"],
                    "message_count": len(data["messages"]),
                    "last_updated": context_file.stat().st_mtime
                })
        
        return sorted(sessions, key=lambda x: x["last_updated"], reverse=True)
```

### Step 3: Add Conversational Commands

```python
# Add to damien_cli/features/ai_intelligence/commands.py

@ai_group.command(name="chat")
@click.option("--session-id", type=str, help="Continue existing session")
@click.option("--new-session", is_flag=True, help="Start fresh session")
@click.pass_context
def chat_interface(ctx, session_id: Optional[str], new_session: bool):
    """Start an interactive chat session for email management"""
    
    # Generate session ID if needed
    if not session_id or new_session:
        session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    click.echo(f"Starting chat session: {session_id}")
    click.echo("Type 'exit' or 'quit' to end the session.\n")
    
    # Initialize components
    llm_provider = OpenAIProvider()
    query_engine = ConversationalQueryEngine(llm_provider)
    
    # Load context if continuing session
    context = None
    if not new_session:
        context = query_engine.context_manager.get_or_create_context(session_id)
        if context.messages:
            click.echo("Resuming previous conversation...\n")
    
    # Interactive loop
    while True:
        try:
            # Get user input
            user_input = click.prompt("You", type=str)
            
            if user_input.lower() in ["exit", "quit"]:
                click.echo("Ending chat session. Goodbye!")
                break
            
            # Process query
            click.echo("Assistant: Thinking...")
            
            # Run async query processing
            async def process():
                return await query_engine.process_query(user_input, session_id, context)
            
            result = asyncio.run(process())
            
            # Display response
            click.echo(f"\nAssistant: {result['response']}\n")
            
            # Update context for next iteration
            context = query_engine.context_manager.get_or_create_context(session_id)
            
        except KeyboardInterrupt:
            click.echo("\n\nChat interrupted. Goodbye!")
            break
        except Exception as e:
            click.echo(f"\nError: {str(e)}\n")
            continue

@ai_group.command(name="ask")
@click.argument("question", type=str)
@click.option("--session-id", type=str, help="Use specific session")
@click.pass_context
def ask_question(ctx, question: str, session_id: Optional[str]):
    """Ask a one-off question about your emails"""
    
    if not session_id:
        session_id = f"oneoff_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def process():
        llm_provider = OpenAIProvider()
        query_engine = ConversationalQueryEngine(llm_provider)
        return await query_engine.process_query(question, session_id)
    
    click.echo("Processing your question...")
    result = asyncio.run(process())
    
    click.echo(f"\n{result['response']}")
    
    if result.get("emails"):
        click.echo(f"\nFound {len(result['emails'])} relevant email(s).")

@ai_group.command(name="sessions")
@click.option("--clear", type=str, help="Clear specific session")
@click.option("--clear-all", is_flag=True, help="Clear all sessions")
@click.pass_context  
def manage_sessions(ctx, clear: Optional[str], clear_all: bool):
    """Manage chat sessions"""
    
    context_manager = ConversationContextManager()
    
    if clear_all:
        if click.confirm("Are you sure you want to clear all chat sessions?"):
            for session in context_manager.list_sessions():
                context_manager.clear_context(session["session_id"])
            click.echo("All sessions cleared.")
        return
    
    if clear:
        context_manager.clear_context(clear)
        click.echo(f"Session {clear} cleared.")
        return
    
    # List sessions
    sessions = context_manager.list_sessions()
    
    if not sessions:
        click.echo("No chat sessions found.")
        return
    
    click.echo("Chat Sessions:")
    for session in sessions:
        last_updated = datetime.fromtimestamp(session["last_updated"])
        click.echo(f"- {session['session_id']}: {session['message_count']} messages, "
                  f"last used {last_updated.strftime('%Y-%m-%d %H:%M')}")
```

## Integration Strategy

### 1. Update CLI Entry Point

```python
# Update damien_cli/cli_entry.py

from damien_cli.features.ai_intelligence.commands import ai_group

# Add to the main damien group
damien.add_command(ai_group)
```

### 2. Create Local Model Provider (Optional)

```python
# damien_cli/features/ai_intelligence/llm_providers/local_provider.py

from transformers import pipeline
import torch
from typing import List
from .base import BaseLLMProvider

class LocalModelProvider(BaseLLMProvider):
    """Local model provider for offline operation"""
    
    def __init__(self, model_path: Optional[str] = None):
        # Use a small model like Flan-T5 or GPT-J
        self.model_name = model_path or "google/flan-t5-base"
        self.generator = pipeline(
            "text2text-generation",
            model=self.model_name,
            device=0 if torch.cuda.is_available() else -1
        )
        
        # For embeddings
        self.embedder = pipeline(
            "feature-extraction",
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion using local model"""
        
        # Truncate prompt if needed
        max_length = kwargs.get("max_tokens", 512)
        
        result = self.generator(
            prompt,
            max_length=max_length,
            temperature=kwargs.get("temperature", 0.3),
            do_sample=True
        )
        
        return result[0]["generated_text"]
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using local model"""
        
        result = self.embedder(text)
        # Average pooling
        embeddings = torch.tensor(result[0]).mean(dim=0)
        return embeddings.tolist()
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count"""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
```

### 3. Provider Factory

```python
# damien_cli/features/ai_intelligence/llm_providers/__init__.py

from typing import Optional
from damien_cli.core.config import settings
from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .local_provider import LocalModelProvider

def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """Factory function to get appropriate LLM provider"""
    
    provider = provider_name or settings.ai_provider
    
    if provider == "openai":
        return OpenAIProvider()
    elif provider == "local":
        return LocalModelProvider(settings.local_model_path)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

__all__ = ["get_llm_provider", "BaseLLMProvider"]
```

## Testing Strategy

### Unit Tests

```python
# tests/features/ai_intelligence/test_rule_parser.py

import pytest
from unittest.mock import Mock, AsyncMock
from damien_cli.features.ai_intelligence.natural_language.rule_parser import NaturalLanguageRuleParser
from damien_cli.features.ai_intelligence.models import ParsedRuleIntent

@pytest.fixture
def mock_llm_provider():
    provider = Mock()
    provider.complete = AsyncMock()
    provider.embed = AsyncMock()
    provider.count_tokens = Mock(return_value=100)
    return provider

@pytest.mark.asyncio
async def test_parse_simple_archive_rule(mock_llm_provider):
    """Test parsing a simple archive rule"""
    
    # Mock LLM response
    mock_llm_provider.complete.return_value = '''
    {
        "action": "archive",
        "conditions": [
            {"field": "from", "operator": "contains", "value": "newsletter"}
        ],
        "parameters": {},
        "confidence": 0.9,
        "reasoning": "User wants to archive emails from newsletters"
    }
    '''
    
    parser = NaturalLanguageRuleParser(mock_llm_provider)
    rule, intent = await parser.parse_instruction("Archive emails from newsletters")
    
    assert rule.name
    assert len(rule.conditions) == 1
    assert rule.conditions[0].field == "from"
    assert rule.conditions[0].operator == "contains"
    assert rule.conditions[0].value == "newsletter"
    assert rule.actions[0].type == "archive"
    assert intent.confidence == 0.9

@pytest.mark.asyncio
async def test_parse_complex_rule_with_age(mock_llm_provider):
    """Test parsing rule with multiple conditions"""
    
    mock_llm_provider.complete.return_value = '''
    {
        "action": "trash",
        "conditions": [
            {"field": "label", "operator": "equals", "value": "SPAM"},
            {"field": "age_days", "operator": "greater_than", "value": 30}
        ],
        "parameters": {},
        "confidence": 0.85
    }
    '''
    
    parser = NaturalLanguageRuleParser(mock_llm_provider)
    rule, intent = await parser.parse_instruction("Delete spam emails older than 30 days")
    
    assert len(rule.conditions) == 2
    assert rule.actions[0].type == "trash"
    assert any(c.field == "age_days" for c in rule.conditions)

def test_fallback_parser():
    """Test fallback parser when LLM fails"""
    
    parser = NaturalLanguageRuleParser(Mock())
    intent = parser._fallback_parse("Archive emails from john@example.com older than 7 days")
    
    assert intent.action == "archive"
    assert len(intent.conditions) >= 1
    assert any(c["field"] == "from" for c in intent.conditions)
    assert intent.confidence < 1.0  # Lower confidence for fallback
```

### Integration Tests

```python
# tests/features/ai_intelligence/test_integration.py

import pytest
from click.testing import CliRunner
from damien_cli.cli_entry import damien

def test_create_rule_command():
    """Test the create-rule CLI command"""
    
    runner = CliRunner()
    result = runner.invoke(damien, [
        'ai', 'create-rule', 
        'Archive all newsletters', 
        '--dry-run'
    ])
    
    assert result.exit_code == 0
    assert "Successfully parsed instruction" in result.output
    assert "archive" in result.output.lower()

def test_analyze_command():
    """Test the analyze command"""
    
    runner = CliRunner()
    result = runner.invoke(damien, [
        'ai', 'analyze',
        '--days', '7',
        '--max-emails', '50'
    ])
    
    # This would need mocking of Gmail API calls
    assert result.exit_code == 0
```

## Implementation Timeline

### Week 1-2: Natural Language Rule Creation
- [x] Day 1-2: Set up AI module structure and dependencies
- [x] Day 3-4: Implement LLM providers (OpenAI + local) - OpenAI implemented, local blocked by dependencies
- [x] Day 5-6: Build rule parser and grammar
- [x] Day 7-8: Create validators and error handling - Validation error in fallback parser fixed
- [x] Day 9-10: Add CLI commands and testing - Commands added, unit tests passing (async tests enabled, validation errors fixed)

### Week 3-4: Smart Email Categorization  
- [ ] Day 1-2: Implement embedding generation
- [ ] Day 3-4: Build pattern detection algorithms
- [ ] Day 5-6: Create categorizer main logic
- [ ] Day 7-8: Add feedback learning system
- [ ] Day 9-10: CLI integration and testing

### Week 5-6: Conversational Interface
- [ ] Day 1-2: Build query intent analyzer
- [ ] Day 3-4: Implement search/action execution
- [ ] Day 5-6: Create context management
- [ ] Day 7-8: Build interactive chat interface
- [ ] Day 9-10: Integration testing and refinement

## Performance Considerations

1. **Caching**: Cache embeddings and LLM responses
2. **Batch Processing**: Process multiple emails in batches
3. **Async Operations**: Use async/await throughout
4. **Token Limits**: Monitor and manage API token usage
5. **Local Models**: Offer offline alternatives

## Security Considerations

1. **API Key Management**: Use environment variables
2. **Data Privacy**: Option to use local models
3. **Input Validation**: Sanitize all user inputs
4. **Rate Limiting**: Implement API rate limiting
5. **Audit Logging**: Log all AI-driven actions

## Deployment Notes

1. **Dependencies**: Large models may require significant disk space
2. **GPU Support**: Local models benefit from GPU acceleration
3. **API Costs**: Monitor OpenAI API usage
4. **Graceful Degradation**: Fallback when AI services unavailable

This implementation guide provides everything needed to add AI intelligence to Damien Email Wrestler. The modular design allows you to implement each phase independently while building toward a comprehensive AI-powered email management system.
