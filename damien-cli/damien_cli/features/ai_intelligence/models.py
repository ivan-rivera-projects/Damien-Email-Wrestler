"""
Enterprise-Grade AI Intelligence Models

Designed with principles from top-tier system architecture:
- Comprehensive validation and type safety
- Performance optimization with __slots__
- Rich metadata and audit trails  
- Extensible design patterns
- Business logic integration
- Monitoring and observability hooks
"""

from __future__ import annotations
from typing import (
    List, Dict, Optional, Literal, Tuple, Union, Any, Set, 
    Callable, Generic, TypeVar, Protocol, runtime_checkable
)
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from enum import Enum, auto
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import hashlib
import logging
from contextlib import contextmanager

from pydantic import (
    BaseModel, Field, validator, root_validator, ConfigDict,
    computed_field, model_validator, field_validator
)
import numpy as np
from numpy.typing import NDArray

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class PatternType(str, Enum):
    """Email pattern classification types"""
    SENDER = "sender"
    SUBJECT = "subject" 
    TIME = "time"
    CLUSTER = "cluster"
    ATTACHMENT = "attachment"
    LABEL = "label"
    THREAD = "thread"
    SIZE = "size"
    FREQUENCY = "frequency"
    BEHAVIORAL = "behavioral"

class ConfidenceLevel(str, Enum):
    """Confidence level classifications"""
    VERY_HIGH = "very_high"  # 0.9+
    HIGH = "high"           # 0.8-0.89
    MEDIUM = "medium"       # 0.6-0.79  
    LOW = "low"            # 0.4-0.59
    VERY_LOW = "very_low"  # <0.4

class RuleComplexity(str, Enum):
    """Rule complexity levels"""
    SIMPLE = "simple"        # 1 condition
    MODERATE = "moderate"    # 2-3 conditions
    COMPLEX = "complex"      # 4+ conditions
    ADVANCED = "advanced"    # Complex logic with nested conditions

class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class ActionType(str, Enum):
    """Available email actions"""
    ARCHIVE = "archive"
    LABEL = "label"
    TRASH = "trash"
    MARK_READ = "mark_read"
    MARK_UNREAD = "mark_unread"
    FORWARD = "forward"
    STAR = "star"
    SNOOZE = "snooze"
    CATEGORIZE = "categorize"

# ============================================================================
# PROTOCOLS AND ABSTRACT CLASSES
# ============================================================================

@runtime_checkable
class Serializable(Protocol):
    """Protocol for serializable objects"""
    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Serializable: ...

@runtime_checkable
class Cacheable(Protocol):
    """Protocol for cacheable objects"""
    def cache_key(self) -> str: ...
    def is_cache_valid(self) -> bool: ...

@runtime_checkable
class Analyzable(Protocol):
    """Protocol for objects that can be analyzed"""
    def analyze(self) -> 'AnalysisResult': ...
    def get_features(self) -> Dict[str, Any]: ...

# ============================================================================
# BASE CLASSES AND MIXINS
# ============================================================================

class EnhancedBaseModel(BaseModel):
    """Enhanced base model with enterprise features"""
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        frozen=False,
        extra='forbid'
    )
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    version: str = Field(default="1.0.0")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Override to track updates"""
        super().__setattr__(name, value)
        if hasattr(self, 'created_at') and name != 'updated_at':
            object.__setattr__(self, 'updated_at', datetime.now(timezone.utc))
    
    @computed_field
    @property
    def age_seconds(self) -> float:
        """Age of the object in seconds"""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Enhanced serialization"""
        return self.model_dump(
            exclude_none=True,
            serialize_as_any=True
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Enhanced deserialization"""
        return cls.model_validate(data)
    
    def cache_key(self) -> str:
        """Generate cache key"""
        content = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def clone(self, **updates) -> 'EnhancedBaseModel':
        """Create a clone with optional updates"""
        data = self.to_dict()
        data.update(updates)
        return self.__class__(**data)

class PerformanceMetrics(BaseModel):
    """Performance tracking for operations"""
    
    model_config = ConfigDict(frozen=False, slots=True)
    
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    items_processed: int = 0
    throughput_per_second: Optional[float] = None
    errors_encountered: int = 0
    warnings_count: int = 0
    
    @model_validator(mode='after')
    def calculate_derived_metrics(self):
        """Calculate derived performance metrics"""
        if self.end_time and self.start_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
            
            if self.duration_ms > 0 and self.items_processed > 0:
                self.throughput_per_second = self.items_processed / (self.duration_ms / 1000)
        
        return self

# ============================================================================
# CORE EMAIL INTELLIGENCE MODELS
# ============================================================================

class EmailSignature(EnhancedBaseModel):
    """Unique signature/fingerprint for an email"""
    
    model_config = ConfigDict(frozen=True, slots=True)
    
    content_hash: str = Field(..., min_length=8, max_length=64)
    structural_hash: str = Field(..., min_length=8, max_length=64)
    sender_domain_hash: str = Field(..., min_length=8, max_length=64)
    subject_pattern_hash: str = Field(..., min_length=8, max_length=64)
    
    @classmethod
    def from_email(cls, email_data: Dict[str, Any]) -> 'EmailSignature':
        """Generate signature from email data"""
        
        def safe_hash(content: str) -> str:
            return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
        
        # Content hash (subject + snippet)
        content = f"{email_data.get('subject', '')}{email_data.get('snippet', '')}"
        content_hash = safe_hash(content)
        
        # Structural hash (headers, size, attachments)
        structure = f"{len(email_data.get('label_names', []))}{email_data.get('has_attachments', False)}{email_data.get('size_estimate', 0)}"
        structural_hash = safe_hash(structure)
        
        # Sender domain hash
        sender = email_data.get('from_sender', '')
        domain = sender.split('@')[-1] if '@' in sender else sender
        sender_domain_hash = safe_hash(domain)
        
        # Subject pattern hash (remove numbers, dates, IDs)
        import re
        subject = email_data.get('subject', '')
        pattern = re.sub(r'\d+|#\w+|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '', subject)
        subject_pattern_hash = safe_hash(pattern)
        
        return cls(
            content_hash=content_hash,
            structural_hash=structural_hash,
            sender_domain_hash=sender_domain_hash,
            subject_pattern_hash=subject_pattern_hash
        )

class EmailFeatures(EnhancedBaseModel):
    """Comprehensive email feature extraction"""
    
    # Basic features
    word_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    line_count: int = Field(ge=0)
    paragraph_count: int = Field(ge=0)
    
    # Linguistic features
    sentiment_score: float = Field(ge=-1.0, le=1.0, default=0.0)
    formality_score: float = Field(ge=0.0, le=1.0, default=0.5)
    urgency_score: float = Field(ge=0.0, le=1.0, default=0.0)
    readability_score: float = Field(ge=0.0, le=100.0, default=50.0)
    
    # Content features
    has_urls: bool = False
    url_count: int = Field(ge=0, default=0)
    has_phone_numbers: bool = False
    has_dates: bool = False
    has_currency: bool = False
    has_numbers: bool = False
    
    # Structural features
    html_content: bool = False
    has_images: bool = False
    image_count: int = Field(ge=0, default=0)
    attachment_types: Set[str] = Field(default_factory=set)
    
    # Sender features
    sender_is_automated: bool = False
    sender_trust_score: float = Field(ge=0.0, le=1.0, default=0.5)
    sender_frequency_score: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Temporal features
    sent_hour: int = Field(ge=0, le=23, default=12)
    sent_day_of_week: int = Field(ge=0, le=6, default=0)  # 0=Monday
    is_weekend: bool = False
    is_business_hours: bool = True
    
    @classmethod
    def extract_from_email(cls, email_data: Dict[str, Any]) -> 'EmailFeatures':
        """Extract comprehensive features from email data"""
        
        snippet = email_data.get('snippet', '')
        subject = email_data.get('subject', '')
        full_content = f"{subject} {snippet}"
        
        # Basic counts
        word_count = len(full_content.split())
        character_count = len(full_content)
        line_count = len(snippet.split('\n'))
        paragraph_count = len([p for p in snippet.split('\n\n') if p.strip()])
        
        # URL detection
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, full_content)
        
        # Phone number detection
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        has_phone_numbers = bool(re.search(phone_pattern, full_content))
        
        # Date detection
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\w+\s+\d{1,2},?\s+\d{4}\b'
        has_dates = bool(re.search(date_pattern, full_content))
        
        # Currency detection
        currency_pattern = r'\$[\d,]+\.?\d*|USD|EUR|GBP|\b\d+\.\d{2}\s*(dollars?|euros?|pounds?)\b'
        has_currency = bool(re.search(currency_pattern, full_content))
        
        # Time analysis
        try:
            internal_date = email_data.get('internal_date')
            if internal_date:
                timestamp = int(internal_date) / 1000
                dt = datetime.fromtimestamp(timestamp)
                sent_hour = dt.hour
                sent_day_of_week = dt.weekday()
                is_weekend = sent_day_of_week >= 5
                is_business_hours = 9 <= sent_hour <= 17
            else:
                sent_hour, sent_day_of_week = 12, 0
                is_weekend, is_business_hours = False, True
        except:
            sent_hour, sent_day_of_week = 12, 0
            is_weekend, is_business_hours = False, True
        
        # Sender analysis
        sender = email_data.get('from_sender', '').lower()
        sender_is_automated = any(keyword in sender for keyword in [
            'noreply', 'no-reply', 'automated', 'notification', 'system'
        ])
        
        return cls(
            word_count=word_count,
            character_count=character_count,
            line_count=line_count,
            paragraph_count=paragraph_count,
            has_urls=len(urls) > 0,
            url_count=len(urls),
            has_phone_numbers=has_phone_numbers,
            has_dates=has_dates,
            has_currency=has_currency,
            has_numbers=bool(re.search(r'\d+', full_content)),
            sender_is_automated=sender_is_automated,
            sent_hour=sent_hour,
            sent_day_of_week=sent_day_of_week,
            is_weekend=is_weekend,
            is_business_hours=is_business_hours,
            attachment_types=set(email_data.get('attachment_types', []))
        )

class EmailEmbedding(EnhancedBaseModel):
    """Advanced email embedding with metadata"""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    email_id: str = Field(..., min_length=1)
    embedding_vector: NDArray[np.float32] = Field(..., description="Numpy array of embeddings")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    embedding_dimension: int = Field(ge=1)
    
    # Email context
    subject: str = Field(default="")
    from_sender: str = Field(default="")
    snippet: str = Field(default="")
    
    # Features and signature
    features: EmailFeatures
    signature: EmailSignature
    
    # Quality metrics
    embedding_quality_score: float = Field(ge=0.0, le=1.0, default=1.0)
    text_preprocessing_applied: List[str] = Field(default_factory=list)
    
    @field_validator('embedding_vector', mode='before')
    def validate_embedding_vector(cls, v):
        """Validate and convert embedding vector"""
        if isinstance(v, list):
            v = np.array(v, dtype=np.float32)
        elif isinstance(v, np.ndarray):
            v = v.astype(np.float32)
        else:
            raise ValueError("Embedding vector must be a numpy array or list")
        
        if len(v.shape) != 1:
            raise ValueError("Embedding vector must be 1-dimensional")
        
        return v
    
    @model_validator(mode='after')
    def validate_embedding_dimension(self):
        """Ensure embedding dimension matches vector length"""
        if len(self.embedding_vector) != self.embedding_dimension:
            self.embedding_dimension = len(self.embedding_vector)
        return self
    
    def similarity(self, other: 'EmailEmbedding') -> float:
        """Calculate cosine similarity with another embedding"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        vec1 = self.embedding_vector.reshape(1, -1)
        vec2 = other.embedding_vector.reshape(1, -1)
        
        return float(cosine_similarity(vec1, vec2)[0, 0])
    
    def distance(self, other: 'EmailEmbedding', metric: str = 'euclidean') -> float:
        """Calculate distance to another embedding"""
        from sklearn.metrics.pairwise import euclidean_distances, manhattan_distances
        
        vec1 = self.embedding_vector.reshape(1, -1)
        vec2 = other.embedding_vector.reshape(1, -1)
        
        if metric == 'euclidean':
            return float(euclidean_distances(vec1, vec2)[0, 0])
        elif metric == 'manhattan':
            return float(manhattan_distances(vec1, vec2)[0, 0])
        else:
            raise ValueError(f"Unsupported distance metric: {metric}")

class PatternCharacteristics(EnhancedBaseModel):
    """Comprehensive pattern characteristics"""
    
    # Core characteristics
    primary_feature: str
    secondary_features: List[str] = Field(default_factory=list)
    statistical_measures: Dict[str, float] = Field(default_factory=dict)
    
    # Sender-specific
    sender_domain: Optional[str] = None
    sender_type: Optional[str] = None
    sender_frequency: Optional[float] = None
    sender_trust_level: Optional[str] = None
    
    # Content-specific
    common_keywords: List[str] = Field(default_factory=list)
    keyword_frequencies: Dict[str, int] = Field(default_factory=dict)
    content_themes: List[str] = Field(default_factory=list)
    language_patterns: Dict[str, Any] = Field(default_factory=dict)
    
    # Temporal-specific
    time_pattern_type: Optional[str] = None
    peak_hours: List[int] = Field(default_factory=list)
    peak_days: List[int] = Field(default_factory=list)
    frequency_pattern: Optional[str] = None
    
    # Structural-specific
    size_statistics: Dict[str, float] = Field(default_factory=dict)
    attachment_patterns: Dict[str, Any] = Field(default_factory=dict)
    label_distributions: Dict[str, int] = Field(default_factory=dict)
    
    # ML-specific (for clusters)
    cluster_centroid: Optional[List[float]] = None
    cluster_radius: Optional[float] = None
    silhouette_score: Optional[float] = None
    inertia: Optional[float] = None
    
    def add_statistical_measure(self, name: str, value: float):
        """Add a statistical measure"""
        self.statistical_measures[name] = value
    
    def get_strength_indicators(self) -> Dict[str, float]:
        """Get indicators of pattern strength"""
        indicators = {}
        
        # Frequency strength
        if self.sender_frequency:
            indicators['frequency_strength'] = min(self.sender_frequency / 10.0, 1.0)
        
        # Keyword consistency
        if self.keyword_frequencies:
            total_occurrences = sum(self.keyword_frequencies.values())
            max_frequency = max(self.keyword_frequencies.values())
            indicators['keyword_consistency'] = max_frequency / total_occurrences
        
        # Temporal consistency
        if self.peak_hours:
            indicators['temporal_consistency'] = len(self.peak_hours) / 24.0
        
        # Statistical significance
        if 'std_dev' in self.statistical_measures and 'mean' in self.statistical_measures:
            cv = self.statistical_measures['std_dev'] / max(self.statistical_measures['mean'], 1)
            indicators['statistical_stability'] = max(0, 1 - cv)
        
        return indicators

class EmailPattern(EnhancedBaseModel):
    """Enterprise-grade email pattern representation"""
    
    # Core identification
    pattern_id: UUID = Field(default_factory=uuid4)
    pattern_type: PatternType
    pattern_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    
    # Statistical properties
    email_count: int = Field(ge=1)
    total_email_universe: int = Field(ge=1)
    prevalence_rate: float = Field(ge=0.0, le=1.0)
    
    # Confidence and quality
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    quality_score: float = Field(ge=0.0, le=1.0, default=0.5)
    statistical_significance: float = Field(ge=0.0, le=1.0, default=0.5)
    
    @model_validator(mode='after')
    def set_confidence_level(self):
        """Automatically set confidence level based on confidence score"""
        if self.confidence >= 0.9:
            self.confidence_level = ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.8:
            self.confidence_level = ConfidenceLevel.HIGH
        elif self.confidence >= 0.6:
            self.confidence_level = ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.4:
            self.confidence_level = ConfidenceLevel.LOW
        else:
            self.confidence_level = ConfidenceLevel.VERY_LOW
        return self
    
    # Rich characteristics
    characteristics: PatternCharacteristics
    
    # Evidence and examples
    example_email_ids: List[str] = Field(default_factory=list, max_items=10)
    counter_example_ids: List[str] = Field(default_factory=list, max_items=5)
    representative_features: Dict[str, Any] = Field(default_factory=dict)
    
    # Business impact
    potential_automation_impact: float = Field(ge=0.0, le=1.0, default=0.0)
    estimated_time_savings_hours: float = Field(ge=0.0, default=0.0)
    business_value_score: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Relationships
    related_pattern_ids: Set[UUID] = Field(default_factory=set)
    parent_pattern_id: Optional[UUID] = None
    child_pattern_ids: Set[UUID] = Field(default_factory=set)
    
    # Suggested actions
    suggested_rule: Optional[Dict[str, Any]] = None
    alternative_actions: List[Dict[str, Any]] = Field(default_factory=list)
    
    @model_validator(mode='after')
    def validate_pattern_consistency(self):
        """Validate pattern internal consistency"""
        # Ensure prevalence rate matches counts
        if self.total_email_universe > 0:
            expected_prevalence = self.email_count / self.total_email_universe
            if abs(self.prevalence_rate - expected_prevalence) > 0.01:
                self.prevalence_rate = expected_prevalence
        
        return self
    
    def calculate_business_impact(self, avg_processing_time_seconds: float = 30.0) -> float:
        """Calculate business impact of automating this pattern"""
        time_saved_per_email = avg_processing_time_seconds
        total_time_saved = (self.email_count * time_saved_per_email) / 3600  # hours
        self.estimated_time_savings_hours = total_time_saved
        
        # Business value factors: impact, confidence, automation feasibility
        automation_feasibility = 1.0 if self.suggested_rule else 0.5
        impact_factor = min(total_time_saved / 10.0, 1.0)  # Normalize to max 10 hours
        
        business_value = (
            impact_factor * 0.4 +
            self.confidence * 0.4 +
            automation_feasibility * 0.2
        )
        
        self.business_value_score = business_value
        self.potential_automation_impact = min(self.prevalence_rate * self.confidence, 1.0)
        
        return business_value

class RuleCondition(EnhancedBaseModel):
    """Advanced rule condition with validation"""
    
    model_config = ConfigDict(frozen=True)
    
    field: str = Field(..., min_length=1)
    operator: str = Field(..., min_length=1)
    value: Union[str, int, float, bool, List[Any]]
    negated: bool = False
    case_sensitive: bool = False
    
    # Advanced features
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    @field_validator('operator')
    def validate_operator(cls, v):
        """Validate operator"""
        valid_operators = {
            'equals', 'not_equals', 'contains', 'not_contains',
            'starts_with', 'ends_with', 'matches_regex',
            'greater_than', 'less_than', 'greater_equal', 'less_equal',
            'in', 'not_in', 'between', 'is_empty', 'is_not_empty'
        }
        if v not in valid_operators:
            raise ValueError(f"Invalid operator: {v}. Must be one of {valid_operators}")
        return v
    
    def evaluate(self, email_data: Dict[str, Any]) -> bool:
        """Evaluate condition against email data"""
        field_value = email_data.get(self.field)
        
        if field_value is None:
            return self.operator in ['is_empty', 'is_not_empty']
        
        # Apply case sensitivity
        if isinstance(field_value, str) and not self.case_sensitive:
            field_value = field_value.lower()
            if isinstance(self.value, str):
                compare_value = self.value.lower()
            else:
                compare_value = self.value
        else:
            compare_value = self.value
        
        # Evaluate based on operator
        result = self._evaluate_operator(field_value, compare_value)
        
        # Apply negation
        return not result if self.negated else result
    
    def _evaluate_operator(self, field_value: Any, compare_value: Any) -> bool:
        """Internal operator evaluation"""
        if self.operator == 'equals':
            return field_value == compare_value
        elif self.operator == 'not_equals':
            return field_value != compare_value
        elif self.operator == 'contains':
            return str(compare_value) in str(field_value)
        elif self.operator == 'not_contains':
            return str(compare_value) not in str(field_value)
        elif self.operator == 'starts_with':
            return str(field_value).startswith(str(compare_value))
        elif self.operator == 'ends_with':
            return str(field_value).endswith(str(compare_value))
        elif self.operator == 'greater_than':
            return float(field_value) > float(compare_value)
        elif self.operator == 'less_than':
            return float(field_value) < float(compare_value)
        elif self.operator == 'in':
            return field_value in compare_value
        elif self.operator == 'not_in':
            return field_value not in compare_value
        elif self.operator == 'is_empty':
            return not field_value or (isinstance(field_value, (list, dict)) and len(field_value) == 0)
        elif self.operator == 'is_not_empty':
            return bool(field_value) and (not isinstance(field_value, (list, dict)) or len(field_value) > 0)
        elif self.operator == 'matches_regex':
            import re
            return bool(re.search(str(compare_value), str(field_value)))
        else:
            return False

class RuleAction(EnhancedBaseModel):
    """Advanced rule action with parameters"""
    
    model_config = ConfigDict(frozen=True)
    
    action_type: ActionType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution properties
    priority: int = Field(default=100, ge=1, le=1000)
    conditional: bool = False
    retry_on_failure: bool = True
    max_retries: int = Field(default=3, ge=0, le=10)
    
    # Impact estimation
    estimated_impact: Optional[str] = None
    reversible: bool = True
    requires_confirmation: bool = False
    
    @field_validator('parameters', mode='before')
    def validate_parameters(cls, v, info):
        """Validate parameters based on action type"""
        action_type = info.data.get('action_type')
        
        if action_type == ActionType.LABEL:
            if 'label_name' not in v:
                raise ValueError("Label action requires 'label_name' parameter")
        elif action_type == ActionType.FORWARD:
            if 'forward_to' not in v:
                raise ValueError("Forward action requires 'forward_to' parameter")
        elif action_type == ActionType.SNOOZE:
            if 'snooze_until' not in v:
                raise ValueError("Snooze action requires 'snooze_until' parameter")
        
        return v
    
    def estimate_impact(self, email_count: int) -> str:
        """Estimate the impact of this action"""
        if self.action_type in [ActionType.TRASH, ActionType.ARCHIVE]:
            impact = f"Will organize {email_count} emails"
        elif self.action_type == ActionType.LABEL:
            label_name = self.parameters.get('label_name', 'Unknown')
            impact = f"Will label {email_count} emails as '{label_name}'"
        elif self.action_type == ActionType.FORWARD:
            forward_to = self.parameters.get('forward_to', 'Unknown')
            impact = f"Will forward {email_count} emails to {forward_to}"
        else:
            impact = f"Will apply {self.action_type.value} to {email_count} emails"
        
        self.estimated_impact = impact
        return impact

class CategorySuggestion(EnhancedBaseModel):
    """Enterprise-grade category suggestion"""
    
    # Core identification
    suggestion_id: UUID = Field(default_factory=uuid4)
    category_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    
    # Impact metrics
    email_count: int = Field(ge=1)
    affected_email_percentage: float = Field(ge=0.0, le=100.0)
    estimated_time_savings_minutes: float = Field(ge=0.0)
    
    # Confidence and quality
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    quality_indicators: Dict[str, float] = Field(default_factory=dict)
    
    # Rule definition
    rule_conditions: List[RuleCondition] = Field(min_items=1)
    rule_actions: List[RuleAction] = Field(min_items=1)
    rule_complexity: RuleComplexity
    
    # Evidence and validation
    example_email_ids: List[str] = Field(default_factory=list, max_items=10)
    validation_sample_size: int = Field(default=0, ge=0)
    false_positive_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    false_negative_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Business context
    business_justification: str = Field(default="")
    risk_level: Literal["low", "medium", "high"] = Field(default="low")
    implementation_difficulty: Literal["easy", "moderate", "hard"] = Field(default="easy")
    
    # Source pattern
    source_pattern_id: Optional[UUID] = None
    supporting_patterns: List[UUID] = Field(default_factory=list)
    
    @model_validator(mode='after')
    def calculate_derived_fields(self):
        """Calculate derived fields"""
        # Set confidence level
        if self.confidence >= 0.9:
            self.confidence_level = ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.8:
            self.confidence_level = ConfidenceLevel.HIGH
        elif self.confidence >= 0.6:
            self.confidence_level = ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.4:
            self.confidence_level = ConfidenceLevel.LOW
        else:
            self.confidence_level = ConfidenceLevel.VERY_LOW
        
        # Determine rule complexity
        condition_count = len(self.rule_conditions)
        if condition_count == 1:
            self.rule_complexity = RuleComplexity.SIMPLE
        elif condition_count <= 3:
            self.rule_complexity = RuleComplexity.MODERATE
        elif condition_count <= 6:
            self.rule_complexity = RuleComplexity.COMPLEX
        else:
            self.rule_complexity = RuleComplexity.ADVANCED
        
        # Estimate time savings (average 30 seconds per email)
        if self.estimated_time_savings_minutes == 0:
            self.estimated_time_savings_minutes = (self.email_count * 30) / 60
        
        return self
    
    def calculate_roi(self, hourly_rate: float = 25.0) -> Dict[str, float]:
        """Calculate return on investment for implementing this suggestion"""
        
        time_saved_hours = self.estimated_time_savings_minutes / 60
        monetary_value = time_saved_hours * hourly_rate
        
        # Implementation cost (rough estimate)
        complexity_multiplier = {
            RuleComplexity.SIMPLE: 0.5,
            RuleComplexity.MODERATE: 1.0,
            RuleComplexity.COMPLEX: 2.0,
            RuleComplexity.ADVANCED: 4.0
        }
        
        implementation_cost = 30 * complexity_multiplier[self.rule_complexity]  # minutes
        implementation_cost_dollars = (implementation_cost / 60) * hourly_rate
        
        # ROI calculation
        net_benefit = monetary_value - implementation_cost_dollars
        roi_percentage = (net_benefit / max(implementation_cost_dollars, 1)) * 100
        
        return {
            'time_saved_hours': time_saved_hours,
            'monetary_value': monetary_value,
            'implementation_cost': implementation_cost_dollars,
            'net_benefit': net_benefit,
            'roi_percentage': roi_percentage,
            'payback_period_days': max(implementation_cost_dollars / max(monetary_value / 365, 0.01), 0)
        }

class BatchProcessingResult(EnhancedBaseModel):
    """Advanced batch processing results with comprehensive metrics"""
    
    # Core metrics
    total_items: int = Field(ge=0)
    processed_successfully: int = Field(ge=0)
    failed_items: int = Field(ge=0)
    skipped_items: int = Field(ge=0)
    
    # Performance metrics
    processing_time_seconds: float = Field(ge=0.0)
    throughput_per_second: float = Field(ge=0.0)
    peak_memory_usage_mb: float = Field(ge=0.0)
    average_cpu_usage_percent: float = Field(ge=0.0, le=100.0)
    
    # Quality metrics
    embeddings_generated: int = Field(ge=0)
    patterns_discovered: int = Field(ge=0)
    suggestions_created: int = Field(ge=0)
    
    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    error_categories: Dict[str, int] = Field(default_factory=dict)
    
    # Progress tracking
    status: ProcessingStatus = ProcessingStatus.COMPLETED
    progress_percentage: float = Field(ge=0.0, le=100.0, default=100.0)
    current_stage: str = Field(default="completed")
    
    # Batch configuration
    batch_size: int = Field(ge=1)
    parallel_workers: int = Field(ge=1)
    retry_attempts: int = Field(ge=0)
    
    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_items == 0:
            return 0.0
        return (self.processed_successfully / self.total_items) * 100
    
    @computed_field
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.total_items == 0:
            return 0.0
        return (self.failed_items / self.total_items) * 100
    
    def add_error(self, error_type: str, message: str, item_id: Optional[str] = None):
        """Add an error to the result"""
        error_entry = {
            'type': error_type,
            'message': message,
            'item_id': item_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.errors.append(error_entry)
        
        # Update error categories
        self.error_categories[error_type] = self.error_categories.get(error_type, 0) + 1
    
    def add_warning(self, warning_type: str, message: str, item_id: Optional[str] = None):
        """Add a warning to the result"""
        warning_entry = {
            'type': warning_type,
            'message': message,
            'item_id': item_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.warnings.append(warning_entry)

class EmailAnalysisResult(EnhancedBaseModel):
    """Comprehensive email analysis results"""
    
    # Core metrics
    total_emails_analyzed: int = Field(ge=0)
    analysis_scope: Dict[str, Any] = Field(default_factory=dict)  # date range, filters, etc.
    
    # Results
    patterns_detected: List[EmailPattern] = Field(default_factory=list)
    category_suggestions: List[CategorySuggestion] = Field(default_factory=list)
    email_embeddings: List[EmailEmbedding] = Field(default_factory=list)
    
    # Performance and quality
    processing_performance: PerformanceMetrics
    batch_results: List[BatchProcessingResult] = Field(default_factory=list)
    
    # Statistical summary
    summary_statistics: Dict[str, Any] = Field(default_factory=dict)
    confidence_distribution: Dict[ConfidenceLevel, int] = Field(default_factory=dict)
    pattern_type_distribution: Dict[PatternType, int] = Field(default_factory=dict)
    
    # Business insights
    automation_opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_total_time_savings: float = Field(ge=0.0, default=0.0)
    roi_projections: Dict[str, float] = Field(default_factory=dict)
    
    # Data provenance
    data_sources: List[str] = Field(default_factory=list)
    analysis_parameters: Dict[str, Any] = Field(default_factory=dict)
    model_versions: Dict[str, str] = Field(default_factory=dict)
    
    @computed_field
    @property
    def high_confidence_patterns(self) -> List[EmailPattern]:
        """Get high confidence patterns (>= 0.8)"""
        return [p for p in self.patterns_detected if p.confidence >= 0.8]
    
    @computed_field
    @property
    def actionable_suggestions(self) -> List[CategorySuggestion]:
        """Get actionable suggestions (>= 0.7 confidence)"""
        return [s for s in self.category_suggestions if s.confidence >= 0.7]
    
    def calculate_business_impact(self) -> Dict[str, Any]:
        """Calculate comprehensive business impact"""
        
        total_emails_automatable = sum(
            s.email_count for s in self.actionable_suggestions
        )
        
        total_time_savings = sum(
            s.estimated_time_savings_minutes for s in self.actionable_suggestions
        )
        
        # Calculate ROI for all suggestions
        total_roi_data = {'total_value': 0, 'total_cost': 0, 'net_benefit': 0}
        
        for suggestion in self.actionable_suggestions:
            roi_data = suggestion.calculate_roi()
            total_roi_data['total_value'] += roi_data['monetary_value']
            total_roi_data['total_cost'] += roi_data['implementation_cost']
            total_roi_data['net_benefit'] += roi_data['net_benefit']
        
        automation_rate = (
            total_emails_automatable / max(self.total_emails_analyzed, 1)
        ) * 100
        
        return {
            'emails_automatable': total_emails_automatable,
            'automation_rate_percent': automation_rate,
            'time_savings_hours': total_time_savings / 60,
            'monetary_value': total_roi_data['total_value'],
            'implementation_cost': total_roi_data['total_cost'],
            'net_benefit': total_roi_data['net_benefit'],
            'overall_roi_percent': (
                total_roi_data['net_benefit'] / max(total_roi_data['total_cost'], 1)
            ) * 100,
            'high_confidence_patterns': len(self.high_confidence_patterns),
            'actionable_suggestions': len(self.actionable_suggestions)
        }
    
    def generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary for business stakeholders"""
        
        business_impact = self.calculate_business_impact()
        
        # Top patterns by business value
        top_patterns = sorted(
            self.patterns_detected,
            key=lambda p: p.business_value_score,
            reverse=True
        )[:5]
        
        # Top suggestions by ROI
        top_suggestions = sorted(
            self.actionable_suggestions,
            key=lambda s: s.calculate_roi()['roi_percentage'],
            reverse=True
        )[:5]
        
        return {
            'analysis_overview': {
                'emails_analyzed': self.total_emails_analyzed,
                'patterns_found': len(self.patterns_detected),
                'suggestions_generated': len(self.category_suggestions),
                'processing_time': f"{self.processing_performance.duration_ms/1000:.1f}s"
            },
            'business_impact': business_impact,
            'top_opportunities': [
                {
                    'name': s.category_name,
                    'emails_affected': s.email_count,
                    'time_savings_hours': s.estimated_time_savings_minutes / 60,
                    'confidence': f"{s.confidence:.0%}",
                    'roi_percent': f"{s.calculate_roi()['roi_percentage']:.0f}%"
                }
                for s in top_suggestions
            ],
            'recommendations': self._generate_recommendations(business_impact),
            'next_steps': self._generate_next_steps()
        }
    
    def _generate_recommendations(self, business_impact: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if business_impact['automation_rate_percent'] > 50:
            recommendations.append("High automation potential - prioritize implementation")
        elif business_impact['automation_rate_percent'] > 25:
            recommendations.append("Moderate automation potential - selective implementation recommended")
        else:
            recommendations.append("Low automation potential - focus on highest ROI suggestions")
        
        if business_impact['time_savings_hours'] > 10:
            recommendations.append("Significant time savings opportunity - business case approved")
        
        if len(self.high_confidence_patterns) > 5:
            recommendations.append("Multiple reliable patterns detected - batch implementation possible")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generate next steps for implementation"""
        return [
            "Review and validate top suggestions",
            "Start with highest ROI, lowest risk suggestions",
            "Implement rules in test environment first",
            "Monitor and measure actual impact",
            "Iterate based on results and feedback"
        ]

# Legacy models for backward compatibility
class NaturalLanguageRule(EnhancedBaseModel):
    """Legacy model - use EmailPattern instead"""
    instruction: str = Field(..., description="Natural language rule instruction")
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class ParsedRuleIntent(EnhancedBaseModel):
    """Legacy model - use CategorySuggestion instead"""
    action: Literal["archive", "label", "trash", "mark_read", "mark_unread", "forward"]
    conditions: List[Dict[str, str]]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence: float
    alternative_interpretations: List[Dict] = Field(default_factory=list)

class EmailCategory(EnhancedBaseModel):
    """Legacy model - use EmailPattern instead"""
    name: str
    description: str
    confidence: float
    suggested_rules: List[Dict]
    example_emails: List[str] = Field(default_factory=list)

class ConversationContext(EnhancedBaseModel):
    """Tracks conversation state"""
    session_id: str
    messages: List[Dict[str, str]]
    current_query_context: Optional[Dict] = None
    email_refs: List[str] = Field(default_factory=list)
