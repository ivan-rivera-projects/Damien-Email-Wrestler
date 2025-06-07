#!/usr/bin/env python3
"""
Damien Email Processor Lambda Function
Processes incoming Gmail webhook events and stores email metadata
"""

import json
import boto3
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
eventbridge = boto3.client('events', region_name='us-east-1')

# Table references
rules_table = dynamodb.Table('damien-ai-rules-table')
audit_table = dynamodb.Table('damien-audit-logs-table')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Process incoming Gmail webhook events
    - Validate email data
    - Extract metadata 
    - Store in DynamoDB
    - Trigger AI analysis
    """
    
    try:
        logger.info(f"Processing email event: {json.dumps(event, default=str)}")
        
        # Parse EventBridge event or direct invocation
        if 'detail' in event:
            # EventBridge event
            detail = event['detail']
            user_id = detail.get('user_id', 'default_user')
            email_data = detail.get('email_data', {})
        else:
            # Direct invocation for testing
            user_id = event.get('user_id', 'default_user')
            email_data = event.get('email_data', {})
        
        # Validate required fields
        if not email_data:
            raise ValueError("No email data provided")
        
        # Extract email metadata (privacy-safe)
        email_metadata = extract_email_metadata(email_data)
        
        # Generate unique email record ID
        email_record_id = str(uuid.uuid4())
        
        # Create email record
        email_record = {
            'PK': f'USER#{user_id}',
            'SK': f'EMAIL#{datetime.utcnow().strftime("%Y-%m-%d")}#{email_record_id}',
            'email_id': email_record_id,
            'gmail_message_id': email_metadata.get('gmail_message_id'),
            'thread_id': email_metadata.get('thread_id'),
            'received_at': email_metadata.get('received_at'),
            'processed_at': datetime.utcnow().isoformat(),
            'size_bytes': email_metadata.get('size_bytes', 0),
            'labels': email_metadata.get('labels', []),
            'headers': email_metadata.get('headers', {}),
            'has_attachments': email_metadata.get('has_attachments', False),
            'content_features': email_metadata.get('content_features', {}),
            'processing_version': '1.0',
            'ttl': int((datetime.utcnow().timestamp()) + (90 * 24 * 3600))  # 90 days retention
        }
        
        # Store email record
        store_email_record(email_record)
        
        # Trigger AI analysis
        trigger_ai_analysis(user_id, email_record_id, email_metadata)
        
        # Log audit record
        log_audit_event('email_processed', user_id, {
            'email_id': email_record_id,
            'gmail_message_id': email_metadata.get('gmail_message_id'),
            'processing_time_ms': (datetime.utcnow().timestamp() * 1000)
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'email_id': email_record_id,
                'processed_at': email_record['processed_at']
            })
        }
        
    except Exception as e:
        logger.error(f"Email processing failed: {str(e)}")
        
        # Log error to audit table
        log_audit_event('email_processing_error', user_id if 'user_id' in locals() else 'unknown', {
            'error': str(e),
            'event_data': json.dumps(event, default=str)
        })
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def extract_email_metadata(email_data: Dict) -> Dict:
    """Extract safe metadata from email without storing PII content"""
    
    metadata = {
        'gmail_message_id': email_data.get('id'),
        'thread_id': email_data.get('threadId'),
        'received_at': email_data.get('internalDate'),
        'size_bytes': len(str(email_data)),
        'labels': email_data.get('labelIds', []),
        'has_attachments': has_attachments(email_data),
        'headers': extract_safe_headers(email_data.get('payload', {}).get('headers', [])),
        'content_features': extract_content_features(email_data)
    }
    
    return metadata

def extract_safe_headers(headers: list) -> Dict:
    """Extract only safe, non-PII headers"""
    
    safe_headers = {}
    allowed_headers = ['Date', 'Message-ID', 'Content-Type', 'X-Gmail-Labels']
    
    for header in headers:
        name = header.get('name', '')
        value = header.get('value', '')
        
        if name in allowed_headers:
            safe_headers[name] = value
        elif name == 'Subject':
            # Hash subject for privacy while allowing pattern matching
            safe_headers['subject_hash'] = hashlib.sha256(value.encode()).hexdigest()[:16]
            safe_headers['subject_length'] = len(value)
        elif name == 'From':
            # Extract only domain for sender analysis
            safe_headers['sender_domain'] = extract_domain(value)
    
    return safe_headers

def extract_domain(email_address: str) -> str:
    """Extract domain from email address"""
    try:
        if '@' in email_address:
            # Handle cases like "Name <email@domain.com>"
            if '<' in email_address and '>' in email_address:
                email_part = email_address.split('<')[1].split('>')[0]
            else:
                email_part = email_address
            return email_part.split('@')[1].strip()
    except:
        return 'unknown'
    return 'unknown'

def has_attachments(email_data: Dict) -> bool:
    """Check if email has attachments"""
    try:
        payload = email_data.get('payload', {})
        parts = payload.get('parts', [])
        
        for part in parts:
            if part.get('filename') and part.get('body', {}).get('attachmentId'):
                return True
        
        return False
    except:
        return False

def extract_content_features(email_data: Dict) -> Dict:
    """Extract content features without storing actual content"""
    
    features = {
        'has_html': False,
        'has_text': False,
        'estimated_word_count': 0,
        'has_links': False,
        'has_images': False,
        'language': 'unknown'
    }
    
    try:
        payload = email_data.get('payload', {})
        
        # Check MIME type
        mime_type = payload.get('mimeType', '')
        if 'text/html' in mime_type:
            features['has_html'] = True
        if 'text/plain' in mime_type:
            features['has_text'] = True
        
        # Estimate content size (without storing content)
        body = payload.get('body', {})
        if body.get('size'):
            # Rough word count estimation
            features['estimated_word_count'] = max(1, body['size'] // 6)
        
        # Check parts for content types
        parts = payload.get('parts', [])
        for part in parts:
            part_mime = part.get('mimeType', '')
            if 'text/html' in part_mime:
                features['has_html'] = True
            if 'text/plain' in part_mime:
                features['has_text'] = True
        
    except Exception as e:
        logger.warning(f"Error extracting content features: {e}")
    
    return features

def store_email_record(email_record: Dict):
    """Store email record in DynamoDB"""
    
    try:
        rules_table.put_item(Item=email_record)
        logger.info(f"Stored email record: {email_record['email_id']}")
    except Exception as e:
        logger.error(f"Failed to store email record: {e}")
        raise

def trigger_ai_analysis(user_id: str, email_id: str, email_metadata: Dict):
    """Trigger AI analysis via EventBridge"""
    
    try:
        event_detail = {
            'user_id': user_id,
            'email_id': email_id,
            'metadata': email_metadata,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'damien.email.processor',
                    'DetailType': 'Email Analysis Request',
                    'Detail': json.dumps(event_detail, default=str),
                    'EventBusName': 'default'  # Using default bus for simplicity
                }
            ]
        )
        
        logger.info(f"Triggered AI analysis for email {email_id}")
        
    except Exception as e:
        logger.warning(f"Failed to trigger AI analysis: {e}")
        # Don't fail the whole function for this

def log_audit_event(event_type: str, user_id: str, details: Dict):
    """Log audit event"""
    
    try:
        audit_record = {
            'PK': f'USER#{user_id}',
            'SK': f'AUDIT#{datetime.utcnow().strftime("%Y-%m-%d")}#{str(uuid.uuid4())}',
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details,
            'ttl': int((datetime.utcnow().timestamp()) + (365 * 24 * 3600))  # 1 year retention
        }
        
        audit_table.put_item(Item=audit_record)
        
    except Exception as e:
        logger.warning(f"Failed to log audit event: {e}")
        # Don't fail for audit logging issues