#!/usr/bin/env python3
"""
Damien Rule Engine Lambda Function  
Executes matched rules with conflict resolution
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, List
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
gmail_api = None  # Will be initialized when needed

# Table references
rules_table = dynamodb.Table('damien-ai-rules-table')
audit_table = dynamodb.Table('damien-audit-logs-table')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Execute matched rules with conflict resolution
    - Load rule definitions
    - Resolve rule conflicts  
    - Execute actions
    - Update performance metrics
    """
    
    try:
        logger.info(f"Processing rule execution event: {json.dumps(event, default=str)}")
        
        # Parse EventBridge event or direct invocation
        if 'detail' in event:
            detail = event['detail']
            user_id = detail.get('user_id')
            email_id = detail.get('email_id')
            matching_rules = detail.get('matching_rules', [])
        else:
            # Direct invocation for testing
            user_id = event.get('user_id')
            email_id = event.get('email_id')
            matching_rules = event.get('matching_rules', [])
        
        if not all([user_id, email_id]):
            raise ValueError("Missing required fields: user_id, email_id")
        
        if not matching_rules:
            logger.info("No matching rules to execute")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'rules_executed': 0,
                    'message': 'No rules to execute'
                })
            }
        
        # Resolve rule conflicts
        resolved_rules = resolve_rule_conflicts(matching_rules)
        
        # Execute rules in priority order
        execution_results = []
        for rule in resolved_rules:
            result = execute_rule(user_id, email_id, rule)
            execution_results.append(result)
            
            # Update rule performance metrics
            update_rule_performance(user_id, rule['rule_id'], result)
        
        # Store execution log
        store_execution_log(user_id, email_id, execution_results)
        
        successful_executions = len([r for r in execution_results if r['success']])
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'rules_executed': len(execution_results),
                'successful_executions': successful_executions,
                'execution_results': execution_results
            })
        }
        
    except Exception as e:
        logger.error(f"Rule execution failed: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def resolve_rule_conflicts(rules: List[Dict]) -> List[Dict]:
    """Simplified conflict resolution for single user"""
    
    if len(rules) <= 1:
        return rules
    
    # For single user, simple strategy: sort by confidence and limit to top 3
    sorted_rules = sorted(rules, key=lambda r: r.get('confidence', 0), reverse=True)
    
    # Take top 3 rules to avoid overwhelming execution
    resolved_rules = sorted_rules[:3]
    
    logger.info(f"Resolved {len(rules)} rules to {len(resolved_rules)} for execution")
    
    return resolved_rules

def execute_rule(user_id: str, email_id: str, rule: Dict) -> Dict:
    """Execute a single rule and return results"""
    
    start_time = datetime.utcnow()
    
    try:
        rule_id = rule.get('rule_id')
        actions = rule.get('actions', {})
        primary_actions = actions.get('primary_actions', {})
        
        execution_log = {
            'rule_id': rule_id,
            'rule_name': rule.get('rule_name', 'Unknown'),
            'started_at': start_time.isoformat(),
            'success': True,
            'actions_executed': [],
            'errors': []
        }
        
        # Execute primary actions
        if 'add_labels' in primary_actions:
            labels_to_add = primary_actions['add_labels']
            if labels_to_add:
                result = add_labels_to_email(user_id, email_id, labels_to_add)
                execution_log['actions_executed'].append({
                    'action': 'add_labels',
                    'labels': labels_to_add,
                    'success': result['success']
                })
                if not result['success']:
                    execution_log['errors'].append(result.get('error', 'Unknown error'))
        
        if 'remove_labels' in primary_actions:
            labels_to_remove = primary_actions['remove_labels']
            if labels_to_remove:
                result = remove_labels_from_email(user_id, email_id, labels_to_remove)
                execution_log['actions_executed'].append({
                    'action': 'remove_labels',
                    'labels': labels_to_remove,
                    'success': result['success']
                })
                if not result['success']:
                    execution_log['errors'].append(result.get('error', 'Unknown error'))
        
        if primary_actions.get('mark_read'):
            result = mark_email_read(user_id, email_id)
            execution_log['actions_executed'].append({
                'action': 'mark_read',
                'success': result['success']
            })
            if not result['success']:
                execution_log['errors'].append(result.get('error', 'Unknown error'))
        
        # Execute advanced actions
        advanced_actions = actions.get('advanced_actions', {})
        
        if advanced_actions.get('archive_after_days'):
            # For now, just log this action (would implement delayed execution)
            execution_log['actions_executed'].append({
                'action': 'archive_scheduled',
                'days': advanced_actions['archive_after_days'],
                'success': True
            })
        
        end_time = datetime.utcnow()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        execution_log.update({
            'completed_at': end_time.isoformat(),
            'execution_time_ms': execution_time_ms,
            'success': len(execution_log['errors']) == 0
        })
        
        logger.info(f"Executed rule {rule_id} with {len(execution_log['actions_executed'])} actions")
        
        return execution_log
        
    except Exception as e:
        end_time = datetime.utcnow()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        error_log = {
            'rule_id': rule.get('rule_id', 'unknown'),
            'rule_name': rule.get('rule_name', 'Unknown'),
            'started_at': start_time.isoformat(),
            'completed_at': end_time.isoformat(),
            'execution_time_ms': execution_time_ms,
            'success': False,
            'error': str(e),
            'actions_executed': []
        }
        
        logger.error(f"Rule execution failed: {e}")
        return error_log

def add_labels_to_email(user_id: str, email_id: str, labels: List[str]) -> Dict:
    """Add labels to email (simulated for now)"""
    
    try:
        # In production, this would call Gmail API to add labels
        # For now, just simulate success
        
        logger.info(f"Simulating adding labels {labels} to email {email_id}")
        
        # Store label action in DynamoDB for tracking
        store_label_action(user_id, email_id, 'add_labels', labels)
        
        return {
            'success': True,
            'labels_added': labels
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def remove_labels_from_email(user_id: str, email_id: str, labels: List[str]) -> Dict:
    """Remove labels from email (simulated for now)"""
    
    try:
        # In production, this would call Gmail API to remove labels
        logger.info(f"Simulating removing labels {labels} from email {email_id}")
        
        store_label_action(user_id, email_id, 'remove_labels', labels)
        
        return {
            'success': True,
            'labels_removed': labels
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def mark_email_read(user_id: str, email_id: str) -> Dict:
    """Mark email as read (simulated for now)"""
    
    try:
        # In production, this would call Gmail API
        logger.info(f"Simulating marking email {email_id} as read")
        
        store_label_action(user_id, email_id, 'mark_read', [])
        
        return {
            'success': True,
            'action': 'marked_read'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def store_label_action(user_id: str, email_id: str, action: str, labels: List[str]):
    """Store label action for tracking and potential rollback"""
    
    try:
        action_record = {
            'PK': f'USER#{user_id}',
            'SK': f'LABELACTION#{datetime.utcnow().strftime("%Y-%m-%d")}#{str(uuid.uuid4())}',
            'email_id': email_id,
            'action': action,
            'labels': labels,
            'timestamp': datetime.utcnow().isoformat(),
            'ttl': int((datetime.utcnow().timestamp()) + (90 * 24 * 3600))  # 90 days
        }
        
        rules_table.put_item(Item=action_record)
        
    except Exception as e:
        logger.warning(f"Failed to store label action: {e}")

def update_rule_performance(user_id: str, rule_id: str, execution_result: Dict):
    """Update rule performance metrics"""
    
    try:
        # Get existing rule
        response = rules_table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'RULE#{rule_id}'
            }
        )
        
        if 'Item' not in response:
            logger.warning(f"Rule {rule_id} not found for performance update")
            return
        
        rule = response['Item']
        
        # Update performance metrics
        performance_metrics = rule.get('performance_metrics', {
            'execution_stats': {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'avg_execution_time_ms': 0
            }
        })
        
        stats = performance_metrics['execution_stats']
        stats['total_executions'] += 1
        
        if execution_result['success']:
            stats['successful_executions'] += 1
        else:
            stats['failed_executions'] += 1
        
        # Update average execution time
        current_time = execution_result.get('execution_time_ms', 0)
        if stats['total_executions'] == 1:
            stats['avg_execution_time_ms'] = current_time
        else:
            # Calculate running average
            stats['avg_execution_time_ms'] = (
                (stats['avg_execution_time_ms'] * (stats['total_executions'] - 1) + current_time) 
                / stats['total_executions']
            )
        
        # Update last execution
        performance_metrics['last_execution'] = {
            'timestamp': datetime.utcnow().isoformat(),
            'success': execution_result['success'],
            'execution_time_ms': current_time
        }
        
        # Save updated rule
        rule['performance_metrics'] = performance_metrics
        rule['last_modified'] = datetime.utcnow().isoformat()
        
        rules_table.put_item(Item=rule)
        
    except Exception as e:
        logger.warning(f"Failed to update rule performance: {e}")

def store_execution_log(user_id: str, email_id: str, execution_results: List[Dict]):
    """Store execution log for audit and analysis"""
    
    try:
        execution_log = {
            'PK': f'USER#{user_id}',
            'SK': f'EXECUTION#{datetime.utcnow().strftime("%Y-%m-%d")}#{str(uuid.uuid4())}',
            'email_id': email_id,
            'execution_timestamp': datetime.utcnow().isoformat(),
            'rules_executed': len(execution_results),
            'successful_executions': len([r for r in execution_results if r['success']]),
            'execution_results': execution_results,
            'total_execution_time_ms': sum(r.get('execution_time_ms', 0) for r in execution_results),
            'ttl': int((datetime.utcnow().timestamp()) + (90 * 24 * 3600))  # 90 days
        }
        
        rules_table.put_item(Item=execution_log)
        
        # Also log to audit table
        audit_record = {
            'PK': f'USER#{user_id}',
            'SK': f'AUDIT#{datetime.utcnow().strftime("%Y-%m-%d")}#{str(uuid.uuid4())}',
            'event_type': 'rule_execution',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'email_id': email_id,
                'rules_executed': len(execution_results),
                'successful_executions': len([r for r in execution_results if r['success']])
            },
            'ttl': int((datetime.utcnow().timestamp()) + (365 * 24 * 3600))  # 1 year
        }
        
        audit_table.put_item(Item=audit_record)
        
    except Exception as e:
        logger.warning(f"Failed to store execution log: {e}")