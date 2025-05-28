"""AI Intelligence Layer for Damien Email Wrestler

This module provides natural language processing capabilities for:
- Converting natural language to email rules
- Categorizing emails intelligently
- Processing conversational queries

Note: Components are imported on-demand to avoid circular imports and heavy loading times.
"""

# Lazy imports to avoid circular dependencies and heavy ML library loading
# Import these directly when needed:
# - from .categorization.gmail_analyzer import GmailEmailAnalyzer  
# - from .natural_language.rule_parser import NaturalLanguageRuleParser
# - from .conversation.query_engine import ConversationalQueryEngine

__all__ = [
    # Components available for direct import
    # 'GmailEmailAnalyzer',  # Use direct import: from .categorization.gmail_analyzer import GmailEmailAnalyzer
    # 'NaturalLanguageRuleParser',  # Use direct import when needed
    # 'ConversationalQueryEngine',  # Use direct import when needed
]