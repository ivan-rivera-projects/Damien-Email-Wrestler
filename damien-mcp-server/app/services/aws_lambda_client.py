"""AWS Lambda client wrapper for Damien MCP server integration.

This module provides the LambdaClient class for calling the deployed
AWS Lambda functions from the Damien MCP server.
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LambdaClient:
    """Client for calling Damien AI Lambda functions."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize Lambda client.
        
        Args:
            region_name: AWS region where Lambda functions are deployed
        """
        self.region_name = region_name
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        
        # Lambda function names
        self.functions = {
            'email_processor': 'damien-email-processor',
            'ai_analyzer': 'damien-ai-analyzer', 
            'rule_engine': 'damien-rule-engine'
        }
        
    def call_email_processor(self, user_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the email processor Lambda function.
        
        Args:
            user_id: User identifier
            email_data: Gmail email data
            
        Returns:
            Processing results with email_id and metadata
        """
        payload = {
            'user_id': user_id,
            'email_data': email_data
        }
        
        return self._invoke_function('email_processor', payload)
    
    def call_ai_analyzer(self, user_id: str, email_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Call the AI analyzer Lambda function.
        
        Args:
            user_id: User identifier
            email_id: Email identifier
            metadata: Email metadata for analysis
            
        Returns:
            AI analysis results including classification and suggestions
        """
        payload = {
            'user_id': user_id,
            'email_id': email_id,
            'metadata': metadata
        }
        
        return self._invoke_function('ai_analyzer', payload)
    
    def call_rule_engine(self, user_id: str, email_id: str, matching_rules: list) -> Dict[str, Any]:
        """Call the rule engine Lambda function.
        
        Args:
            user_id: User identifier
            email_id: Email identifier
            matching_rules: List of matched rules to execute
            
        Returns:
            Rule execution results
        """
        payload = {
            'user_id': user_id,
            'email_id': email_id,
            'matching_rules': matching_rules
        }
        
        return self._invoke_function('rule_engine', payload)
    
    def process_email_with_ai(self, user_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an email through the complete AI pipeline.
        
        This is a convenience method that calls all three Lambda functions
        in sequence for complete email processing.
        
        Args:
            user_id: User identifier
            email_data: Gmail email data
            
        Returns:
            Complete processing results including AI analysis and rule execution
        """
        try:
            # Step 1: Process email metadata
            logger.info(f"Processing email {email_data.get('id', 'unknown')} for user {user_id}")
            
            processor_result = self.call_email_processor(user_id, email_data)
            if not processor_result.get('success'):
                return {
                    'success': False,
                    'error': 'Email processing failed',
                    'details': processor_result
                }
            
            email_id = processor_result['body']['email_id']
            
            # Step 2: AI analysis
            # Extract metadata for analysis (simplified for now)
            metadata = {
                'headers': {
                    'sender_domain': self._extract_domain(email_data.get('payload', {}).get('headers', [])),
                    'subject_length': len(email_data.get('snippet', ''))
                },
                'content_features': {
                    'has_html': 'text/html' in str(email_data.get('payload', {})),
                    'estimated_word_count': len(email_data.get('snippet', '').split())
                }
            }
            
            analyzer_result = self.call_ai_analyzer(user_id, email_id, metadata)
            if not analyzer_result.get('success'):
                return {
                    'success': False,
                    'error': 'AI analysis failed',
                    'details': analyzer_result
                }
            
            # Step 3: Rule execution (if rules matched)
            # Note: In real implementation, matching rules would come from AI analyzer
            # For now, we'll skip rule execution unless there are specific matches
            
            return {
                'success': True,
                'email_id': email_id,
                'processor_result': processor_result,
                'analysis_result': analyzer_result,
                'message': 'Email processed successfully through AI pipeline'
            }
            
        except Exception as e:
            logger.error(f"Error in AI pipeline processing: {str(e)}")
            return {
                'success': False,
                'error': f'Pipeline processing failed: {str(e)}'
            }
    
    def _invoke_function(self, function_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a Lambda function with error handling.
        
        Args:
            function_key: Key in self.functions dict
            payload: Function payload
            
        Returns:
            Function response or error information
        """
        function_name = self.functions.get(function_key)
        if not function_name:
            return {
                'success': False,
                'error': f'Unknown function: {function_key}'
            }
        
        try:
            logger.info(f"Invoking Lambda function: {function_name}")
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            
            if response.get('StatusCode') == 200:
                # Parse the body if it's a string (API Gateway format)
                if isinstance(response_payload.get('body'), str):
                    response_payload['body'] = json.loads(response_payload['body'])
                
                return response_payload
            else:
                return {
                    'success': False,
                    'error': f'Lambda invocation failed with status: {response.get("StatusCode")}',
                    'details': response_payload
                }
                
        except Exception as e:
            logger.error(f"Error invoking Lambda function {function_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Lambda invocation error: {str(e)}'
            }
    
    def _extract_domain(self, headers: list) -> str:
        """Extract sender domain from email headers.
        
        Args:
            headers: List of email headers
            
        Returns:
            Sender domain or 'unknown'
        """
        for header in headers:
            if header.get('name', '').lower() == 'from':
                value = header.get('value', '')
                if '@' in value:
                    # Extract domain from email address
                    # Handle format like "Name <email@domain.com>" or "email@domain.com"
                    if '<' in value and '>' in value:
                        email = value.split('<')[1].split('>')[0]
                    else:
                        email = value.strip()
                    
                    if '@' in email:
                        return email.split('@')[1].strip()
        
        return 'unknown'
    
    def health_check(self) -> Dict[str, Any]:
        """Check if all Lambda functions are accessible.
        
        Returns:
            Health status of all functions
        """
        results = {}
        
        for key, function_name in self.functions.items():
            try:
                # Simple test payload
                test_payload = {
                    'user_id': 'health_check',
                    'test': True
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_payload)
                )
                
                results[key] = {
                    'status': 'healthy' if response.get('StatusCode') == 200 else 'unhealthy',
                    'function_name': function_name,
                    'last_check': datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                results[key] = {
                    'status': 'error',
                    'function_name': function_name,
                    'error': str(e),
                    'last_check': datetime.utcnow().isoformat()
                }
        
        return results