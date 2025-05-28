"""AI Intelligence Layer for Damien Email Wrestler

This module provides natural language processing capabilities for:
- Converting natural language to email rules
- Categorizing emails intelligently
- Processing conversational queries
"""

from .natural_language.rule_parser import NaturalLanguageRuleParser
from .categorization.categorizer import EmailCategorizer
from .conversation.query_engine import ConversationalQueryEngine
from .conversation.context_manager import ConversationContextManager

__all__ = [
    'NaturalLanguageRuleParser',
    'EmailCategorizer', 
    'ConversationalQueryEngine',
    'ConversationContextManager'
]