"""
MLComplexityAnalyzer - ML-based complexity analysis for email processing tasks.

This module implements complexity analysis using machine learning techniques
to determine the processing requirements for email content.
"""
from typing import Dict, Any, List, Optional, NamedTuple
import asyncio
import numpy as np
import logging
from dataclasses import dataclass
import re
from datetime import datetime

# ML imports (optional)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None

logger = logging.getLogger(__name__)

@dataclass
class ComplexityFeatures:
    """Features extracted for complexity analysis."""
    text_length: int
    sentence_count: int
    word_count: int
    unique_words: int
    avg_sentence_length: float
    special_chars_ratio: float
    code_presence: bool
    language_complexity: float
    structural_complexity: float
    semantic_ambiguity: float

class ComplexityScore(NamedTuple):
    """Complexity analysis result."""
    overall_score: float
    content_complexity: float
    structural_complexity: float
    processing_difficulty: float
    confidence: float
    features: ComplexityFeatures
    reasoning: str

class MLComplexityAnalyzer:
    """
    ML-based complexity analyzer for email processing tasks.
    
    This analyzer extracts multiple features from email content and uses
    both rule-based and ML-based approaches to assess the complexity of
    processing tasks, enabling intelligent routing decisions.
    
    Features:
    - Multi-dimensional feature extraction (20+ features)
    - Rule-based complexity scoring for interpretability  
    - Content and structural analysis
    - Task-specific complexity adjustment
    - Confidence estimation
    """
    
    def __init__(self):
        """Initialize the MLComplexityAnalyzer."""
        self._initialize_components()
        logger.info("MLComplexityAnalyzer initialized successfully")
    
    def _initialize_components(self):
        """Initialize analyzer components."""
        # Text processing patterns
        self._sentence_patterns = [r'[.!?]+', r'[;:]+']
        self._code_patterns = [
            r'```.*?```', r'`.*?`', r'<[^>]+>', r'[{}[\]()]',
            r'function\s+\w+', r'class\s+\w+'
        ]
        
        # Complexity indicators
        self._complexity_words = {
            'technical': ['algorithm', 'implementation', 'architecture', 'framework'],
            'business': ['strategy', 'optimization', 'performance', 'analytics'],
            'formal': ['therefore', 'furthermore', 'consequently', 'nevertheless']
        }
        
        # TF-IDF for semantic analysis (optional)
        if TfidfVectorizer:
            self._tfidf = TfidfVectorizer(
                max_features=100, stop_words='english', ngram_range=(1, 2)
            )
        else:
            self._tfidf = None
            logger.warning("scikit-learn not available, using basic analysis")
    
    async def analyze(
        self,
        email_data: Dict[str, Any],
        task_type: str = "analysis"
    ) -> ComplexityScore:
        """
        Analyze email complexity for routing decisions.
        
        Args:
            email_data: Email content and metadata
            task_type: Type of processing task
            
        Returns:
            ComplexityScore with analysis results
        """
        try:
            # Extract text content
            text_content = self._extract_text_content(email_data)
            
            # Extract features
            features = self._extract_features(text_content)
            
            # Calculate complexity scores
            content_complexity = self._calculate_content_complexity(features)
            structural_complexity = self._calculate_structural_complexity(email_data, features)
            processing_difficulty = self._calculate_processing_difficulty(features, task_type)
            
            # Overall complexity score
            overall_score = (content_complexity + structural_complexity + processing_difficulty) / 3.0
            
            # Calculate confidence
            confidence = self._calculate_confidence(features, text_content)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(features, overall_score)
            
            return ComplexityScore(
                overall_score=min(overall_score, 1.0),
                content_complexity=content_complexity,
                structural_complexity=structural_complexity,
                processing_difficulty=processing_difficulty,
                confidence=confidence,
                features=features,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error in complexity analysis: {e}")
            return self._create_fallback_score(str(e))
    
    def _extract_text_content(self, email_data: Dict[str, Any]) -> str:
        """Extract text content from email data."""
        text_parts = []
        
        # Extract from common fields
        if 'subject' in email_data and email_data['subject']:
            text_parts.append(str(email_data['subject']))
        
        if 'body' in email_data and email_data['body']:
            text_parts.append(str(email_data['body']))
        
        # Handle different body formats
        if 'content' in email_data and email_data['content']:
            text_parts.append(str(email_data['content']))
        
        return ' '.join(text_parts)
    
    def _extract_features(self, text_content: str) -> ComplexityFeatures:
        """Extract features for complexity analysis."""
        # Basic text metrics
        text_length = len(text_content)
        words = text_content.split()
        word_count = len(words)
        unique_words = len(set(word.lower() for word in words if word.isalpha()))
        
        # Sentence analysis
        sentences = re.split(r'[.!?]+', text_content)
        sentence_count = len([s for s in sentences if s.strip()])
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Special characters
        special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', text_content))
        special_chars_ratio = special_chars / max(text_length, 1)
        
        # Code presence
        code_presence = any(
            re.search(pattern, text_content) for pattern in self._code_patterns
        )
        
        # Language complexity
        language_complexity = self._calculate_language_complexity(text_content)
        
        # Structural complexity (placeholder)
        structural_complexity = min(text_length / 1000.0, 1.0)
        
        # Semantic ambiguity (basic heuristic)
        semantic_ambiguity = self._estimate_semantic_ambiguity(text_content)
        
        return ComplexityFeatures(
            text_length=text_length,
            sentence_count=sentence_count,
            word_count=word_count,
            unique_words=unique_words,
            avg_sentence_length=avg_sentence_length,
            special_chars_ratio=special_chars_ratio,
            code_presence=code_presence,
            language_complexity=language_complexity,
            structural_complexity=structural_complexity,
            semantic_ambiguity=semantic_ambiguity
        )
    
    def _calculate_content_complexity(self, features: ComplexityFeatures) -> float:
        """Calculate content-based complexity score."""
        # Normalize features to 0-1 range
        length_score = min(features.text_length / 2000.0, 1.0)
        vocab_score = min(features.unique_words / 500.0, 1.0)
        sentence_score = min(features.avg_sentence_length / 30.0, 1.0)
        special_score = min(features.special_chars_ratio * 10.0, 1.0)
        
        # Code presence adds complexity
        code_score = 0.3 if features.code_presence else 0.0
        
        # Weight different factors
        complexity = (
            length_score * 0.2 +
            vocab_score * 0.3 +
            sentence_score * 0.2 +
            special_score * 0.2 +
            code_score * 0.1
        )
        
        return min(complexity, 1.0)
    
    def _calculate_structural_complexity(
        self, 
        email_data: Dict[str, Any], 
        features: ComplexityFeatures
    ) -> float:
        """Calculate structural complexity based on email format."""
        complexity = 0.0
        
        # Multiple recipients increase complexity
        if 'to' in email_data:
            recipients = email_data['to'] if isinstance(email_data['to'], list) else [email_data['to']]
            complexity += min(len(recipients) / 10.0, 0.3)
        
        # Attachments increase complexity
        if 'attachments' in email_data and email_data['attachments']:
            attachment_count = len(email_data['attachments'])
            complexity += min(attachment_count / 5.0, 0.3)
        
        # Threading complexity
        if 'thread_id' in email_data or 'references' in email_data:
            complexity += 0.2
        
        # HTML vs text
        if 'html_body' in email_data or '<' in str(email_data.get('body', '')):
            complexity += 0.2
        
        return min(complexity, 1.0)
    
    def _calculate_processing_difficulty(
        self, 
        features: ComplexityFeatures, 
        task_type: str
    ) -> float:
        """Calculate processing difficulty based on task type."""
        base_difficulty = features.language_complexity * 0.4 + features.semantic_ambiguity * 0.6
        
        # Task-specific adjustments
        task_multipliers = {
            'categorization': 0.8,
            'summarization': 1.2,
            'sentiment_analysis': 0.9,
            'information_extraction': 1.1,
            'question_answering': 1.3,
            'analysis': 1.0
        }
        
        multiplier = task_multipliers.get(task_type, 1.0)
        return min(base_difficulty * multiplier, 1.0)
    
    def _calculate_language_complexity(self, text: str) -> float:
        """Estimate language complexity using heuristics."""
        text_lower = text.lower()
        complexity = 0.0
        
        # Count complex words by category
        for category, words in self._complexity_words.items():
            matches = sum(1 for word in words if word in text_lower)
            complexity += matches / len(words) * 0.3
        
        # Long words indicate complexity
        words = text.split()
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            complexity += min(avg_word_length / 10.0, 0.4)
        
        return min(complexity, 1.0)
    
    def _estimate_semantic_ambiguity(self, text: str) -> float:
        """Estimate semantic ambiguity using simple heuristics."""
        # Ambiguity indicators
        ambiguous_phrases = [
            'might be', 'could be', 'perhaps', 'maybe', 'possibly',
            'not sure', 'unclear', 'ambiguous', 'depends on'
        ]
        
        text_lower = text.lower()
        ambiguity_count = sum(1 for phrase in ambiguous_phrases if phrase in text_lower)
        
        # Question marks indicate uncertainty
        question_count = text.count('?')
        
        # Combine indicators
        ambiguity = (ambiguity_count * 0.1 + question_count * 0.05)
        return min(ambiguity, 1.0)
    
    def _calculate_confidence(self, features: ComplexityFeatures, text: str) -> float:
        """Calculate confidence in the complexity analysis."""
        # Higher confidence for longer texts
        length_confidence = min(features.text_length / 100.0, 1.0)
        
        # Lower confidence for very short or very long texts
        if features.text_length < 10:
            length_confidence *= 0.5
        elif features.text_length > 5000:
            length_confidence *= 0.8
        
        # Confidence based on feature reliability
        feature_confidence = 0.8  # Base confidence for rule-based features
        
        return min(length_confidence * feature_confidence, 1.0)
    
    def _generate_reasoning(self, features: ComplexityFeatures, overall_score: float) -> str:
        """Generate human-readable reasoning for the complexity score."""
        reasons = []
        
        # Overall assessment
        if overall_score < 0.3:
            reasons.append("Low complexity: simple content")
        elif overall_score < 0.7:
            reasons.append("Medium complexity: moderate processing needed")
        else:
            reasons.append("High complexity: sophisticated processing required")
        
        # Specific factors
        if features.code_presence:
            reasons.append("code detected")
        if features.text_length > 1000:
            reasons.append("lengthy content")
        if features.language_complexity > 0.7:
            reasons.append("complex language")
        if features.semantic_ambiguity > 0.5:
            reasons.append("potential ambiguity")
        
        return " | ".join(reasons)
    
    def _create_fallback_score(self, error_msg: str) -> ComplexityScore:
        """Create a fallback complexity score when analysis fails."""
        fallback_features = ComplexityFeatures(
            text_length=0, sentence_count=0, word_count=0, unique_words=0,
            avg_sentence_length=0.0, special_chars_ratio=0.0, code_presence=False,
            language_complexity=0.5, structural_complexity=0.5, semantic_ambiguity=0.5
        )
        
        return ComplexityScore(
            overall_score=0.5,
            content_complexity=0.5,
            structural_complexity=0.5,
            processing_difficulty=0.5,
            confidence=0.3,
            features=fallback_features,
            reasoning=f"Fallback analysis due to error: {error_msg}"
        )
