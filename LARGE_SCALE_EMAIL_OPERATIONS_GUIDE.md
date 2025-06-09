# Large-Scale Email Operations Guide

## Overview

This guide explains how to handle large-scale email operations (150+ emails) in Damien Email Wrestler without hitting timeout issues.

## The Problem

When processing large numbers of emails (150+), synchronous operations timeout because:
1. Fetching hundreds of email IDs takes time
2. Processing them all at once exceeds the 30-60 second timeout limit
3. The operation fails and returns an error

## Solutions

### Solution 1: Use Async Tools (Existing Feature)

For operations involving 150+ emails, use the async workflow:

#### Step 1: Start Async Analysis
```
damien_ai_analyze_emails_async(
    days=30,
    target_count=500,
    query="is:unread",
    min_confidence=0.85,
    use_statistical_validation=true
)
```

This returns immediately with:
```json
{
    "success": true,
    "job_id": "task_abc123",
    "status": "started",
    "estimated_duration_minutes": 5
}
```

#### Step 2: Check Progress
```
damien_job_get_status(job_id="task_abc123")
```

Returns:
```json
{
    "success": true,
    "status": "running",
    "progress": {
        "percentage": 45,
        "message": "Processed 225/500 emails"
    }
}
```

#### Step 3: Get Results
```
damien_job_get_result(job_id="task_abc123")
```

Returns complete analysis results when done.

### Solution 2: Use Enhanced Query-Based Tools (New Feature)

The new enhanced tools avoid the ID generation bottleneck entirely:

#### For Trashing Marketing Emails
```
damien_trash_emails_by_query(
    query="is:unread (list:* OR unsubscribe OR promotional OR marketing)",
    max_results=1000,
    dry_run=false
)
```

This:
- Uses Gmail queries directly (no ID fetching)
- Automatically switches to async for >100 emails
- Processes in batches to avoid timeouts
- Provides progress tracking

#### Smart Marketing Detection and Removal
```
damien_smart_trash_marketing(
    days=7,
    max_emails=500,
    min_confidence=0.85,
    dry_run=false
)
```

This:
- Analyzes emails with AI first
- Identifies marketing patterns
- Builds smart queries
- Trashes in batches

## Best Practices

### 1. For Small Operations (< 50 emails)
- Use standard synchronous tools
- Direct ID-based operations work fine

### 2. For Medium Operations (50-500 emails)
- Use `damien_trash_emails_by_query` with queries
- Let the tool auto-detect async needs

### 3. For Large Operations (500+ emails)
- Always use async tools
- Monitor progress with job tracking
- Process in logical chunks

### 4. For Marketing Cleanup
- Use `damien_smart_trash_marketing` for intelligent detection
- Start with `dry_run=true` to preview
- Adjust `min_confidence` based on results

## Example Workflows

### Workflow 1: Clean 1000 Marketing Emails
```
1. damien_smart_trash_marketing(days=30, max_emails=1000)
   → Returns job_id

2. damien_job_get_status(job_id="...")
   → Monitor progress

3. damien_job_get_result(job_id="...")
   → Get final results
```

### Workflow 2: Query-Based Cleanup
```
1. Preview what would be deleted:
   damien_trash_emails_by_query(
       query="from:newsletter* OR from:*marketing*",
       dry_run=true
   )

2. Execute if satisfied:
   damien_trash_emails_by_query(
       query="from:newsletter* OR from:*marketing*",
       max_results=2000
   )
```

### Workflow 3: Time-Based Cleanup
```
damien_trash_emails_by_query(
    query="older_than:90d category:promotions",
    max_results=5000
)
```

## Query Examples

### Marketing Emails
```
is:unread (list:* OR unsubscribe OR promotional OR marketing OR deals OR sale)
```

### Old Promotional Emails
```
older_than:30d category:promotions
```

### Newsletter Cleanup
```
from:newsletter* OR subject:newsletter OR list:*
```

### Social Media Notifications
```
category:social older_than:7d
```

## Performance Guidelines

| Email Count | Recommended Approach | Expected Time |
|------------|---------------------|---------------|
| 1-50 | Synchronous tools | < 5 seconds |
| 50-200 | Query-based tools | 10-30 seconds |
| 200-1000 | Async tools | 1-10 minutes |
| 1000+ | Async with batching | 10-30 minutes |

## Troubleshooting

### Timeout Errors
- Switch to async tools
- Use query-based operations
- Reduce batch sizes

### Memory Issues
- Process in smaller batches
- Use query filters to narrow scope
- Enable progressive processing

### Rate Limiting
- Built-in delays prevent this
- Async tools handle automatically
- Monitor job progress

## Summary

For large-scale operations:
1. **Use async tools** for analysis
2. **Use query-based tools** for actions
3. **Monitor progress** with job tracking
4. **Process in batches** for efficiency

This approach handles 10-10,000+ emails efficiently without timeouts!