"""Confidence scoring utilities for pattern detection and rule suggestions"""

from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta

class ConfidenceScorer:
    """Calculates confidence scores for patterns and suggestions"""
    
    def __init__(self):
        self.base_confidence = 0.5
        self.min_sample_size = 3
        
    def score_pattern_confidence(
        self, 
        pattern_type: str,
        email_count: int,
        total_emails: int,
        pattern_characteristics: Dict
    ) -> float:
        """Calculate confidence score for a detected pattern"""
        
        # Start with base confidence
        confidence = self.base_confidence
        
        # Sample size factor
        sample_ratio = email_count / max(total_emails, 1)
        if email_count >= self.min_sample_size:
            confidence += min(sample_ratio, 0.3)  # Max 0.3 boost
        
        # Pattern-specific adjustments
        if pattern_type == "sender":
            confidence += self._score_sender_pattern(pattern_characteristics)
        elif pattern_type == "subject":
            confidence += self._score_subject_pattern(pattern_characteristics)
        elif pattern_type == "cluster":
            confidence += self._score_cluster_pattern(pattern_characteristics)
        elif pattern_type == "time":
            confidence += self._score_time_pattern(pattern_characteristics)
        elif pattern_type == "label":
            confidence += self._score_label_pattern(pattern_characteristics)
        
        # Volume factor
        if email_count > 10:
            confidence += 0.1
        if email_count > 50:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _score_sender_pattern(self, characteristics: Dict) -> float:
        """Score sender-based patterns"""
        
        score_boost = 0.0
        
        # High frequency senders are more predictable
        avg_per_day = characteristics.get('average_per_day', 0)
        if avg_per_day > 1:
            score_boost += 0.2
        elif avg_per_day > 0.5:
            score_boost += 0.1
        
        # Known sender types are more reliable
        sender_type = characteristics.get('sender_type', '')
        reliable_types = ['Newsletter', 'Notification', 'Shopping']
        if sender_type in reliable_types:
            score_boost += 0.2
        
        # Consistent subjects increase confidence
        common_subjects = characteristics.get('common_subjects', [])
        if len(common_subjects) > 2:
            score_boost += 0.1
        
        return score_boost
    
    def _score_subject_pattern(self, characteristics: Dict) -> float:
        """Score subject-based patterns"""
        
        score_boost = 0.0
        
        # Strong keywords increase confidence
        keywords = characteristics.get('keywords', [])
        strong_keywords = ['newsletter', 'receipt', 'order', 'invoice', 'digest']
        
        if any(keyword in strong_keywords for keyword in keywords):
            score_boost += 0.3
        
        # Multiple keywords increase confidence
        if len(keywords) > 1:
            score_boost += 0.1
        
        return score_boost
    
    def _score_cluster_pattern(self, characteristics: Dict) -> float:
        """Score clustering-based patterns"""
        
        # Clusters are inherently less reliable than explicit patterns
        score_boost = -0.1
        
        # But strong characteristics can improve confidence
        if 'dominant_sender' in characteristics:
            score_boost += 0.2
        
        if characteristics.get('common_keywords'):
            score_boost += 0.1
        
        if characteristics.get('common_labels'):
            score_boost += 0.1
        
        return score_boost
    
    def _score_time_pattern(self, characteristics: Dict) -> float:
        """Score time-based patterns"""
        
        score_boost = 0.0
        
        # Weekly patterns are more reliable than hourly
        pattern_type = characteristics.get('pattern_type', '')
        if pattern_type == 'weekly':
            score_boost += 0.2
        elif pattern_type == 'hourly':
            score_boost += 0.1
        
        return score_boost
    
    def _score_label_pattern(self, characteristics: Dict) -> float:
        """Score label-based patterns"""
        
        # Label patterns are quite reliable since they're explicit
        return 0.2
    
    def score_rule_suggestion(
        self,
        pattern_confidence: float,
        email_count: int,
        rule_complexity: int,
        potential_impact: float
    ) -> float:
        """Score a rule suggestion based on multiple factors"""
        
        # Start with pattern confidence
        confidence = pattern_confidence
        
        # Adjust for rule complexity (simpler rules are more reliable)
        if rule_complexity == 1:  # Single condition
            confidence += 0.1
        elif rule_complexity > 3:  # Complex rules
            confidence -= 0.1
        
        # Factor in potential impact
        if potential_impact > 0.5:  # High impact
            confidence += 0.05
        
        # Email count factor
        if email_count > 20:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def calculate_business_confidence(
        self,
        technical_confidence: float,
        user_feedback_score: float = 0.5,
        historical_accuracy: float = 0.8,
        data_quality_score: float = 0.9
    ) -> Dict[str, float]:
        """Calculate comprehensive business confidence metrics"""
        
        # Weighted combination of different confidence factors
        weights = {
            'technical': 0.4,
            'user_feedback': 0.2,
            'historical': 0.3,
            'data_quality': 0.1
        }
        
        business_confidence = (
            technical_confidence * weights['technical'] +
            user_feedback_score * weights['user_feedback'] +
            historical_accuracy * weights['historical'] +
            data_quality_score * weights['data_quality']
        )
        
        # Calculate risk level
        if business_confidence >= 0.9:
            risk_level = "very_low"
        elif business_confidence >= 0.8:
            risk_level = "low" 
        elif business_confidence >= 0.6:
            risk_level = "medium"
        elif business_confidence >= 0.4:
            risk_level = "high"
        else:
            risk_level = "very_high"
        
        return {
            'business_confidence': business_confidence,
            'technical_confidence': technical_confidence,
            'user_feedback_score': user_feedback_score,
            'historical_accuracy': historical_accuracy,
            'data_quality_score': data_quality_score,
            'risk_level': risk_level,
            'recommended_action': self._get_recommended_action(business_confidence)
        }
    
    def _get_recommended_action(self, confidence: float) -> str:
        """Get recommended action based on confidence level"""
        
        if confidence >= 0.9:
            return "auto_implement"
        elif confidence >= 0.8:
            return "implement_with_monitoring"
        elif confidence >= 0.6:
            return "pilot_test_first"
        elif confidence >= 0.4:
            return "manual_review_required"
        else:
            return "do_not_implement"
    
    def track_prediction_accuracy(
        self,
        predictions: List[Dict],
        actual_outcomes: List[Dict]
    ) -> Dict[str, float]:
        """Track the accuracy of confidence predictions"""
        
        if len(predictions) != len(actual_outcomes):
            raise ValueError("Predictions and outcomes must have the same length")
        
        correct_predictions = 0
        confidence_errors = []
        
        for pred, actual in zip(predictions, actual_outcomes):
            predicted_confidence = pred.get('confidence', 0.5)
            actual_success = actual.get('success', False)
            
            # Calculate if prediction was directionally correct
            if (predicted_confidence >= 0.7 and actual_success) or \
               (predicted_confidence < 0.7 and not actual_success):
                correct_predictions += 1
            
            # Calculate confidence calibration error
            actual_confidence = 1.0 if actual_success else 0.0
            confidence_error = abs(predicted_confidence - actual_confidence)
            confidence_errors.append(confidence_error)
        
        accuracy = correct_predictions / len(predictions)
        mean_confidence_error = np.mean(confidence_errors)
        
        return {
            'accuracy': accuracy,
            'mean_confidence_error': mean_confidence_error,
            'total_predictions': len(predictions),
            'correct_predictions': correct_predictions,
            'calibration_quality': 1.0 - mean_confidence_error  # Higher is better
        }
    
    def adjust_confidence_based_on_feedback(
        self,
        original_confidence: float,
        feedback_type: str,
        feedback_strength: float = 1.0
    ) -> float:
        """Adjust confidence based on user feedback"""
        
        adjustment = 0.0
        
        if feedback_type == "positive":
            adjustment = 0.1 * feedback_strength
        elif feedback_type == "negative":
            adjustment = -0.15 * feedback_strength
        elif feedback_type == "neutral":
            adjustment = 0.0
        
        # Apply adjustment with bounds
        new_confidence = original_confidence + adjustment
        return max(0.0, min(1.0, new_confidence))
