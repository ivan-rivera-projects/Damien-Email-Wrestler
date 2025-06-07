# Damien AI Rules Engine - MVP+ Architecture

## Overview
Enterprise-grade AI rules engine with multi-tenant architecture, event-driven processing, and advanced rule conflict resolution.

## 1. Multi-Tenant DynamoDB Schema

### Table: `damien-ai-rules-prod`

#### Primary Access Patterns

```
1. Get all rules for a tenant: PK = TENANT#tenant_id, SK begins_with RULE#
2. Get user-specific rules: PK = TENANT#tenant_id, SK begins_with USER#user_id#RULE#
3. Get rule by ID: PK = TENANT#tenant_id, SK = RULE#rule_id
4. Get rules by performance: GSI1PK = TENANT#tenant_id#PERFORMANCE, GSI1SK = score#rule_id
5. Get rules by category: GSI2PK = TENANT#tenant_id#CATEGORY#category, GSI2SK = created_at
```

#### Core Schema

```json
{
  "TableName": "damien-ai-rules-prod",
  "BillingMode": "PAY_PER_REQUEST",
  "AttributeDefinitions": [
    {"AttributeName": "PK", "AttributeType": "S"},
    {"AttributeName": "SK", "AttributeType": "S"},
    {"AttributeName": "GSI1PK", "AttributeType": "S"},
    {"AttributeName": "GSI1SK", "AttributeType": "S"},
    {"AttributeName": "GSI2PK", "AttributeType": "S"},
    {"AttributeName": "GSI2SK", "AttributeType": "S"}
  ],
  "KeySchema": [
    {"AttributeName": "PK", "KeyType": "HASH"},
    {"AttributeName": "SK", "KeyType": "RANGE"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "PerformanceIndex",
      "KeySchema": [
        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
        {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
      ]
    },
    {
      "IndexName": "CategoryIndex", 
      "KeySchema": [
        {"AttributeName": "GSI2PK", "KeyType": "HASH"},
        {"AttributeName": "GSI2SK", "KeyType": "RANGE"}
      ]
    }
  ]
}
```

### Entity Types

#### 1. Tenant Configuration
```json
{
  "PK": "TENANT#org_12345",
  "SK": "CONFIG",
  "entity_type": "tenant_config",
  "tenant_id": "org_12345",
  "organization_name": "Acme Corp",
  "subscription_tier": "enterprise",
  "created_at": "2025-06-07T10:00:00Z",
  "settings": {
    "max_rules_per_user": 1000,
    "ai_confidence_threshold": 0.85,
    "rule_execution_timeout_ms": 5000,
    "privacy_mode": "strict",
    "audit_logging": true
  },
  "billing": {
    "plan": "enterprise",
    "monthly_rule_executions": 50000,
    "current_usage": 12450
  }
}
```

#### 2. User Profile
```json
{
  "PK": "TENANT#org_12345",
  "SK": "USER#user_67890",
  "entity_type": "user_profile",
  "tenant_id": "org_12345",
  "user_id": "user_67890",
  "email": "ivan@acmecorp.com",
  "gmail_account": "1shotmanagement@gmail.com",
  "created_at": "2025-06-07T10:00:00Z",
  "preferences": {
    "ai_aggressiveness": "moderate",
    "notification_frequency": "daily",
    "auto_apply_rules": true,
    "feedback_enabled": true
  },
  "stats": {
    "total_rules": 23,
    "active_rules": 18,
    "emails_processed": 5420,
    "time_saved_minutes": 340
  }
}
```

#### 3. AI Rule (Core Entity)
```json
{
  "PK": "TENANT#org_12345",
  "SK": "USER#user_67890#RULE#rule_uuid_12345",
  "GSI1PK": "TENANT#org_12345#PERFORMANCE",
  "GSI1SK": "0.92#rule_uuid_12345",
  "GSI2PK": "TENANT#org_12345#CATEGORY#promotional",
  "GSI2SK": "2025-06-07T10:30:00Z",
  
  "entity_type": "ai_rule",
  "tenant_id": "org_12345",
  "user_id": "user_67890",
  "rule_id": "rule_uuid_12345",
  
  "metadata": {
    "name": "Smart Promotional Email Handler",
    "description": "AI-generated rule for promotional emails with high confidence",
    "version": "1.2",
    "created_by": "ai_analyze_emails_async",
    "created_at": "2025-06-07T10:30:00Z",
    "last_modified": "2025-06-07T15:45:00Z",
    "status": "active",
    "category": "promotional",
    "tags": ["ai-generated", "high-performance", "promotional"]
  },
  
  "rule_definition": {
    "conditions": {
      "sender_patterns": {
        "domains": ["*@amazon.com", "*@deals.walmart.com"],
        "keywords": ["deals", "sale", "offer", "discount"],
        "exclude_patterns": ["receipt", "order confirmation"]
      },
      "subject_patterns": {
        "required_keywords": ["offer", "discount", "limited time"],
        "negative_keywords": ["receipt", "refund"],
        "regex_patterns": ["\\d+% off", "save \\$\\d+"]
      },
      "content_analysis": {
        "ai_classification": "promotional",
        "confidence_threshold": 0.85,
        "sentiment": "positive",
        "urgency_indicators": ["limited time", "expires", "while supplies last"]
      },
      "contextual": {
        "time_filters": {
          "business_hours_only": false,
          "exclude_weekends": false
        },
        "frequency_limits": {
          "max_per_day": 10,
          "cooldown_hours": 2
        }
      }
    },
    "actions": {
      "primary_actions": {
        "add_labels": ["AI_PROMOTIONAL", "AUTO_SORTED"],
        "remove_labels": ["INBOX", "UNREAD"],
        "mark_read": false,
        "priority": "low"
      },
      "advanced_actions": {
        "forward_to": null,
        "create_calendar_event": false,
        "notify_user": false,
        "archive_after_days": 30
      }
    },
    "execution_config": {
      "priority": 100,
      "timeout_ms": 3000,
      "retry_count": 2,
      "rollback_on_error": true
    }
  },
  
  "ai_metadata": {
    "model_version": "damien-classifier-v2.1",
    "training_data_size": 15420,
    "feature_importance": {
      "sender_domain": 0.45,
      "subject_keywords": 0.32,
      "content_sentiment": 0.23
    },
    "confidence_score": 0.92,
    "generated_from": {
      "analysis_job_id": "job_98765",
      "source_emails": 234,
      "pattern_strength": 0.89
    }
  },
  
  "performance_metrics": {
    "execution_stats": {
      "total_executions": 234,
      "successful_executions": 228,
      "failed_executions": 6,
      "avg_execution_time_ms": 145
    },
    "accuracy_metrics": {
      "correct_classifications": 208,
      "false_positives": 12,
      "false_negatives": 8,
      "precision": 0.945,
      "recall": 0.963,
      "f1_score": 0.954
    },
    "user_feedback": {
      "thumbs_up": 23,
      "thumbs_down": 2,
      "corrections_applied": 3,
      "last_feedback": "2025-06-07T14:20:00Z"
    },
    "impact_metrics": {
      "emails_processed": 234,
      "time_saved_minutes": 47,
      "user_satisfaction": 0.92,
      "automation_rate": 0.89
    }
  },
  
  "conflict_resolution": {
    "priority_weight": 100,
    "dependency_rules": ["rule_uuid_11111"],
    "conflict_strategy": "highest_confidence",
    "parallel_execution": true,
    "result_merge_strategy": "union"
  },
  
  "audit_trail": {
    "created_by": "system:ai_analyzer",
    "modified_by": ["user_67890", "system:optimizer"],
    "approval_status": "auto_approved",
    "compliance_tags": ["gdpr_compliant", "pii_safe"],
    "change_log": [
      {
        "timestamp": "2025-06-07T15:45:00Z",
        "action": "confidence_threshold_updated",
        "old_value": 0.80,
        "new_value": 0.85,
        "reason": "improved_accuracy"
      }
    ]
  }
}
```

#### 4. Rule Execution Log
```json
{
  "PK": "TENANT#org_12345",
  "SK": "EXECUTION#2025-06-07#rule_uuid_12345#exec_54321",
  "entity_type": "execution_log",
  "tenant_id": "org_12345",
  "user_id": "user_67890",
  "rule_id": "rule_uuid_12345",
  "execution_id": "exec_54321",
  "email_id": "gmail_msg_98765",
  "executed_at": "2025-06-07T16:30:00Z",
  "execution_result": {
    "status": "success",
    "confidence": 0.94,
    "actions_taken": ["add_label:AI_PROMOTIONAL", "remove_label:INBOX"],
    "execution_time_ms": 142,
    "ai_reasoning": "High confidence promotional email based on sender domain and subject keywords"
  },
  "email_metadata": {
    "subject": "50% Off Everything - Limited Time!",
    "sender": "deals@amazon.com",
    "received_at": "2025-06-07T16:29:45Z",
    "size_bytes": 12450
  },
  "ttl": 1704153600  // Auto-delete after 30 days
}
```

#### 5. Performance Analytics
```json
{
  "PK": "TENANT#org_12345",
  "SK": "ANALYTICS#DAILY#2025-06-07",
  "GSI1PK": "TENANT#org_12345#ANALYTICS",
  "GSI1SK": "2025-06-07",
  "entity_type": "performance_analytics",
  "tenant_id": "org_12345",
  "date": "2025-06-07",
  "metrics": {
    "total_rules": 156,
    "active_rules": 134,
    "total_executions": 2340,
    "successful_executions": 2298,
    "avg_confidence": 0.89,
    "top_performing_rules": ["rule_uuid_12345", "rule_uuid_67890"],
    "categories": {
      "promotional": {"executions": 1200, "accuracy": 0.94},
      "newsletter": {"executions": 800, "accuracy": 0.91},
      "personal": {"executions": 340, "accuracy": 0.97}
    }
  }
}
```

## 2. Access Patterns and Queries

### Query Examples

```python
# Get all rules for a user
{
  "KeyConditionExpression": "PK = :tenant AND begins_with(SK, :user_prefix)",
  "ExpressionAttributeValues": {
    ":tenant": "TENANT#org_12345",
    ":user_prefix": "USER#user_67890#RULE#"
  }
}

# Get top performing rules
{
  "IndexName": "PerformanceIndex",
  "KeyConditionExpression": "GSI1PK = :tenant_perf",
  "ScanIndexForward": False,  # Descending order
  "Limit": 10,
  "ExpressionAttributeValues": {
    ":tenant_perf": "TENANT#org_12345#PERFORMANCE"
  }
}

# Get rules by category
{
  "IndexName": "CategoryIndex", 
  "KeyConditionExpression": "GSI2PK = :tenant_category",
  "ExpressionAttributeValues": {
    ":tenant_category": "TENANT#org_12345#CATEGORY#promotional"
  }
}
```

## 3. Data Privacy and Security

### Encryption Strategy
```json
{
  "at_rest": {
    "encryption": "AWS KMS Customer Managed Keys",
    "key_rotation": "automatic_annual",
    "per_tenant_keys": true
  },
  "in_transit": {
    "encryption": "TLS 1.3",
    "certificate_pinning": true
  },
  "field_level": {
    "pii_fields": ["email_content", "sender_names"],
    "encryption_algorithm": "AES-256-GCM",
    "key_derivation": "tenant_specific"
  }
}
```

### PII Handling
```python
# Automatically detect and mask PII in email content
pii_patterns = {
    "email_addresses": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone_numbers": r'\b\d{3}-\d{3}-\d{4}\b',
    "credit_cards": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b'
}

# Store only metadata, not actual email content
rule_conditions = {
    "content_features": {
        "word_count": 245,
        "sentiment_score": 0.7,
        "has_links": true,
        "link_count": 3,
        "has_images": true,
        "language": "en"
    },
    "pii_detected": ["email_address"],  # Types only, not values
    "content_hash": "sha256_hash_here"  # For deduplication
}
```

## 4. Cost Optimization

### DynamoDB Optimization
```json
{
  "billing_mode": "PAY_PER_REQUEST",
  "backup_strategy": {
    "point_in_time_recovery": true,
    "on_demand_backups": "weekly",
    "cross_region_backup": "monthly"
  },
  "ttl_configuration": {
    "execution_logs": "30_days",
    "analytics_data": "365_days",
    "archived_rules": "2555_days"  // 7 years
  },
  "compression": {
    "large_fields": ["rule_definition", "execution_result"],
    "algorithm": "gzip",
    "size_threshold_bytes": 1024
  }
}
```

### Item Size Optimization
```python
# Keep items under 400KB for optimal performance
optimization_strategies = [
    "Compress large JSON fields",
    "Reference external S3 objects for large data",
    "Use abbreviated field names for frequently accessed data",
    "Implement data archival for old execution logs"
]
```

## 5. Monitoring and Observability

### CloudWatch Metrics
```json
{
  "custom_metrics": [
    "RuleExecutionLatency",
    "RuleAccuracyScore", 
    "TenantUsage",
    "AIConfidenceDistribution",
    "UserSatisfactionScore"
  ],
  "alarms": [
    {
      "metric": "RuleExecutionLatency",
      "threshold": "5000ms",
      "action": "scale_lambda_concurrency"
    },
    {
      "metric": "RuleAccuracyScore", 
      "threshold": "0.85",
      "action": "trigger_model_retraining"
    }
  ]
}
```

This schema provides enterprise-grade multi-tenancy, privacy protection, and performance optimization while maintaining simplicity for the MVP+ implementation.

Next: Event-driven Lambda architecture design.