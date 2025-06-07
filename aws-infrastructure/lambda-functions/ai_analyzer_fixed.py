#!/usr/bin/env python3
"""
Damien AI Analyzer Lambda Function (Fixed for DynamoDB Decimal types)
Analyzes email content and generates/matches AI rules
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import hashlib
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
eventbridge = boto3.client('events', region_name='us-east-1')

# Table references
rules_table = dynamodb.Table('damien-ai-rules-table')
analytics_table = dynamodb.Table('damien-analytics-table')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Analyze email content and generate/match AI rules
    - Content analysis using ML models
    - Pattern detection
    - Rule matching
    - Rule generation suggestions
    """
    
    try:
        logger.info(f"Processing AI analysis event: {json.dumps(event, default=str)}")
        
        # Parse EventBridge event or direct invocation
        if 'detail' in event:
            detail = event['detail']
            user_id = detail.get('user_id')
            email_id = detail.get('email_id')
            email_metadata = detail.get('metadata', {})
        else:
            # Direct invocation for testing
            user_id = event.get('user_id')
            email_id = event.get('email_id')
            email_metadata = event.get('metadata', {})
        
        if not all([user_id, email_id]):
            raise ValueError("Missing required fields: user_id, email_id")
        
        # Perform AI analysis
        analysis_results = perform_ai_analysis(email_metadata)
        
        # Match existing rules
        matching_rules = find_matching_rules(user_id, analysis_results)
        
        # Generate new rule suggestions if no matches
        rule_suggestions = []
        if not matching_rules:
            rule_suggestions = generate_rule_suggestions(user_id, analysis_results)
        
        # Store analysis results (convert floats to Decimal)
        analysis_record = {
            'PK': f'USER#{user_id}',
            'SK': f'ANALYSIS#{datetime.utcnow().strftime("%Y-%m-%d")}#{email_id}',
            'email_id': email_id,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'analysis_results': convert_floats_to_decimal(analysis_results),
            'matching_rules': convert_floats_to_decimal(matching_rules),
            'rule_suggestions': convert_floats_to_decimal(rule_suggestions),
            'confidence_score': Decimal(str(analysis_results.get('confidence', 0))),
            'processing_version': '1.0',
            'ttl': int((datetime.utcnow().timestamp()) + (30 * 24 * 3600))  # 30 days retention
        }
        
        store_analysis_results(analysis_record)
        
        # Trigger rule execution if matches found
        if matching_rules:
            trigger_rule_execution(user_id, email_id, matching_rules)
        
        # Update analytics
        update_analytics(user_id, analysis_results, len(matching_rules), len(rule_suggestions))
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'email_id': email_id,
                'analysis_confidence': float(analysis_results.get('confidence', 0)),
                'matching_rules_count': len(matching_rules),
                'suggestions_count': len(rule_suggestions)
            })
        }
        
    except Exception as e:
        logger.error(f"AI analysis failed: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def convert_floats_to_decimal(obj):
    """Recursively convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    else:
        return obj

def perform_ai_analysis(email_metadata: Dict) -> Dict:
    """Perform ML-based email analysis"""
    
    # Feature extraction
    features = {
        'sender_domain': email_metadata.get('headers', {}).get('sender_domain', 'unknown'),
        'subject_length': email_metadata.get('headers', {}).get('subject_length', 0),
        'content_features': email_metadata.get('content_features', {}),
        'received_hour': extract_hour(email_metadata.get('received_at')),
        'has_attachments': email_metadata.get('has_attachments', False),
        'label_count': len(email_metadata.get('labels', []))
    }
    
    # ML Classification (simplified heuristic-based for now)
    classification = classify_email(features)
    
    # Pattern detection
    patterns = detect_patterns(features)
    
    # Sentiment analysis (basic)
    sentiment = analyze_sentiment(features.get('content_features', {}))
    
    return {
        'classification': classification,
        'patterns': patterns,
        'sentiment': sentiment,
        'confidence': classification.get('confidence', 0.5),
        'features': features,
        'model_version': 'damien-classifier-v1.0'
    }

def classify_email(features: Dict) -> Dict:
    """Classify email using heuristic rules (would be ML model in production)"""
    
    classification = {
        'primary_category': 'personal',
        'confidence': 0.5,
        'secondary_categories': [],
        'reasoning': []
    }
    
    sender_domain = features.get('sender_domain', '').lower()
    content_features = features.get('content_features', {})
    
    # Promotional email detection
    promotional_domains = ['amazon.com', 'walmart.com', 'target.com', 'ebay.com', 'groupon.com']
    if any(domain in sender_domain for domain in promotional_domains):
        classification['primary_category'] = 'promotional'
        classification['confidence'] = 0.85
        classification['reasoning'].append('Known promotional sender domain')
    
    # Newsletter detection
    newsletter_indicators = ['newsletter', 'updates', 'digest', 'weekly', 'monthly']
    if any(indicator in sender_domain for indicator in newsletter_indicators):
        classification['primary_category'] = 'newsletter'
        classification['confidence'] = 0.80
        classification['reasoning'].append('Newsletter domain pattern')
    
    # Work email detection
    work_domains = ['slack.com', 'github.com', 'jira.atlassian.com', 'office365.com']
    if any(domain in sender_domain for domain in work_domains):
        classification['primary_category'] = 'work'
        classification['confidence'] = 0.90
        classification['reasoning'].append('Work-related sender domain')
    
    # Content-based classification
    if content_features.get('has_html') and content_features.get('estimated_word_count', 0) > 200:
        if classification['primary_category'] == 'personal':
            classification['primary_category'] = 'newsletter'
            classification['confidence'] = 0.70
            classification['reasoning'].append('Long HTML content suggests newsletter')
    
    return classification

def detect_patterns(features: Dict) -> List[Dict]:
    """Detect patterns in email features"""
    
    patterns = []
    
    # Time-based patterns
    received_hour = features.get('received_hour', 12)
    if received_hour < 6 or received_hour > 22:
        patterns.append({
            'type': 'unusual_time',
            'description': 'Email received outside normal hours',
            'confidence': 0.7
        })
    
    # Size patterns
    content_features = features.get('content_features', {})
    word_count = content_features.get('estimated_word_count', 0)
    
    if word_count > 1000:
        patterns.append({
            'type': 'long_content',
            'description': 'Unusually long email content',
            'confidence': 0.8
        })
    elif word_count < 10:
        patterns.append({
            'type': 'short_content',
            'description': 'Very short email content',
            'confidence': 0.6
        })
    
    # Attachment patterns
    if features.get('has_attachments'):
        patterns.append({
            'type': 'has_attachments',
            'description': 'Email contains attachments',
            'confidence': 0.9
        })
    
    return patterns

def analyze_sentiment(content_features: Dict) -> Dict:
    """Basic sentiment analysis"""
    
    # Simplified sentiment analysis
    word_count = content_features.get('estimated_word_count', 0)
    has_html = content_features.get('has_html', False)
    
    if has_html and word_count > 100:
        sentiment_score = 0.6  # Slightly positive for newsletters/marketing
    elif word_count < 20:
        sentiment_score = 0.5  # Neutral for short messages
    else:
        sentiment_score = 0.55  # Slightly positive default
    
    return {
        'score': sentiment_score,
        'label': 'positive' if sentiment_score > 0.6 else 'neutral' if sentiment_score > 0.4 else 'negative',
        'confidence': 0.6
    }

def find_matching_rules(user_id: str, analysis: Dict) -> List[Dict]:
    """Find existing rules that match the email analysis"""
    
    try:
        # Query user's rules
        response = rules_table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'USER#{user_id}',
                ':sk': 'RULE#'
            }
        )
        
        user_rules = response.get('Items', [])
        matching_rules = []
        
        for rule in user_rules:
            if rule_matches_analysis(rule, analysis):
                matching_rules.append({
                    'rule_id': rule['rule_id'],
                    'confidence': calculate_match_confidence(rule, analysis),
                    'actions': rule.get('rule_definition', {}).get('actions', {}),
                    'rule_name': rule.get('metadata', {}).get('name', 'Unknown Rule')
                })
        
        # Sort by confidence
        return sorted(matching_rules, key=lambda x: x['confidence'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error finding matching rules: {e}")
        return []

def rule_matches_analysis(rule: Dict, analysis: Dict) -> bool:
    """Check if a rule matches the email analysis"""
    return True  # Simplified for testing

def calculate_match_confidence(rule: Dict, analysis: Dict) -> float:
    """Calculate confidence score for rule match"""
    return 0.8  # Simplified for testing

def generate_rule_suggestions(user_id: str, analysis: Dict) -> List[Dict]:
    """Generate new rule suggestions based on analysis"""
    
    suggestions = []
    classification = analysis.get('classification', {})
    features = analysis.get('features', {})
    
    # Only suggest rules for high-confidence classifications
    if analysis.get('confidence', 0) < 0.7:
        return suggestions
    
    primary_category = classification.get('primary_category')
    sender_domain = features.get('sender_domain')
    
    if primary_category and sender_domain and sender_domain != 'unknown':
        suggestion = {
            'suggested_rule_id': str(uuid.uuid4()),
            'rule_name': f'Auto-sort {primary_category.title()} from {sender_domain}',
            'confidence': analysis.get('confidence'),
            'conditions': {
                'sender_patterns': {
                    'domains': [f'*@{sender_domain}']
                },
                'content_analysis': {
                    'ai_classification': primary_category,
                    'confidence_threshold': 0.7
                }
            },
            'suggested_actions': {
                'primary_actions': {
                    'add_labels': [f'AI_{primary_category.upper()}', 'AUTO_SORTED'],
                    'mark_read': False
                }
            },
            'reasoning': f'Based on consistent {primary_category} emails from {sender_domain}'
        }
        
        suggestions.append(suggestion)
    
    return suggestions

def extract_hour(timestamp_str: str) -> int:
    """Extract hour from timestamp string"""
    try:
        if timestamp_str:
            # Handle both ISO format and Gmail internal format
            if timestamp_str.isdigit():
                # Gmail internal timestamp (milliseconds)
                dt = datetime.fromtimestamp(int(timestamp_str) / 1000)
            else:
                # ISO format
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.hour
    except:
        pass
    return 12  # Default to noon

def store_analysis_results(analysis_record: Dict):
    """Store analysis results in DynamoDB"""
    
    try:
        rules_table.put_item(Item=analysis_record)
        logger.info(f"Stored analysis for email: {analysis_record['email_id']}")
    except Exception as e:
        logger.error(f"Failed to store analysis results: {e}")
        raise

def trigger_rule_execution(user_id: str, email_id: str, matching_rules: List[Dict]):
    """Trigger rule execution via EventBridge"""
    
    try:
        event_detail = {
            'user_id': user_id,
            'email_id': email_id,
            'matching_rules': matching_rules,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'damien.ai.analyzer',
                    'DetailType': 'Rule Execution Request',
                    'Detail': json.dumps(event_detail, default=str),
                    'EventBusName': 'default'
                }
            ]
        )
        
        logger.info(f"Triggered rule execution for email {email_id} with {len(matching_rules)} rules")
        
    except Exception as e:
        logger.warning(f"Failed to trigger rule execution: {e}")

def update_analytics(user_id: str, analysis_results: Dict, matching_rules_count: int, suggestions_count: int):
    """Update analytics with analysis results"""
    
    try:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        analytics_record = {
            'PK': f'USER#{user_id}',
            'SK': f'ANALYTICS#{today}',
            'date': today,
            'updated_at': datetime.utcnow().isoformat(),
            'analysis_stats': {
                'total_analyses': 1,
                'avg_confidence': Decimal(str(analysis_results.get('confidence', 0))),
                'categories': {
                    analysis_results.get('classification', {}).get('primary_category', 'unknown'): 1
                },
                'matching_rules_count': matching_rules_count,
                'suggestions_generated': suggestions_count
            }
        }
        
        # Try to update existing record, or create new one
        analytics_table.put_item(Item=analytics_record)
        
    except Exception as e:
        logger.warning(f"Failed to update analytics: {e}")
        # Don't fail the function for analytics issues