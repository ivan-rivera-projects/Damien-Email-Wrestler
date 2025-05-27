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
    parameters: Dict[str, object] = Field(default_factory=dict)
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