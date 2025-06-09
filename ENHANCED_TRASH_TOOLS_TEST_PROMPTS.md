# Enhanced Trash Tools - Test Prompts & Usage Examples

## Overview
This document contains test prompts and usage examples for Damien's enhanced trash tools introduced to handle large-scale email operations without timeouts.

## New Tools
- `damien_trash_emails_by_query` - Query-based trash operations (handles 1000+ emails)
- `damien_smart_trash_marketing` - AI-powered marketing email detection and removal

## Basic Enhanced Trash Tool Tests

### 1. Dry Run Test (Safe to start with)
```
I want to see what promotional emails I could delete. Can you show me a preview of promotional emails from the last 7 days without actually deleting them? Use the new enhanced trash tool with dry_run mode.
```

### 2. Small Query-Based Trash Test
```
I have too many unread marketing emails. Can you trash unread emails that contain "unsubscribe" or "promotional" in them? Limit it to 25 emails for this test.
```

### 3. Smart Marketing Detection Test
```
Can you use AI to automatically identify and preview what marketing emails I have from the last 14 days? I want to see what patterns it finds before deciding to delete anything.
```

## Progressive Testing (After basic tests work)

### 4. Medium-Scale Operation
```
I want to clean up newsletter emails. Can you trash emails from the last 30 days that are newsletters or mailing lists? Limit to 100 emails and show me the progress.
```

### 5. Large-Scale Async Test
```
I have way too many promotional emails. Can you start an async job to analyze and trash promotional emails from the last 60 days? I want to process up to 500 emails.
```

### 6. Advanced Query Test
```
Can you help me delete old social media notifications? I want to trash emails from social media platforms that are older than 14 days. Use a smart query approach.
```

## Advanced Testing

### 7. Job Tracking Test
```
Start a large cleanup job for marketing emails from the last 90 days, then show me how to track its progress and get the results when it's done.
```

### 8. Custom Query Test
```
I want to delete emails from specific senders. Can you trash emails from addresses containing "noreply" or "no-reply" from the last 21 days? Show me what would be deleted first.
```

## Query Categories for Common Use Cases

### Marketing & Promotional Emails
```
Query: "is:unread (list:* OR unsubscribe OR promotional OR marketing OR deals OR sale)"
Use Case: General marketing cleanup
Expected Results: Newsletters, promotional emails, sales notifications
```

### Newsletter Management
```
Query: "from:newsletter* OR subject:newsletter OR list:*"
Use Case: Newsletter subscription cleanup
Expected Results: Mailing lists, newsletters, automated subscriptions
```

### Social Media Notifications
```
Query: "category:social older_than:7d"
Use Case: Clear old social media notifications
Expected Results: Facebook, LinkedIn, Twitter notifications
```

### No-Reply Senders
```
Query: "from:noreply* OR from:no-reply* OR from:*noreply*"
Use Case: Automated system emails cleanup
Expected Results: System notifications, automated emails
```

### Time-Based Cleanup
```
Query: "older_than:90d category:promotions"
Use Case: Archive old promotional content
Expected Results: Old marketing emails, expired promotions
```

### Unsubscribe Pattern Detection
```
Query: "unsubscribe OR 'click here to unsubscribe' OR 'update preferences'"
Use Case: Marketing emails with unsubscribe links
Expected Results: Commercial emails, newsletters, marketing
```

## Expected Behaviors to Verify

✅ **For small operations (< 50 emails)**: Should complete synchronously in seconds  
✅ **For medium operations (50-500 emails)**: Should auto-detect and use async processing  
✅ **Dry run mode**: Should show previews without deleting anything  
✅ **Progress tracking**: Async jobs should return job_id for monitoring  
✅ **Smart detection**: AI should identify marketing patterns accurately  

## Performance Guidelines

| Email Count | Recommended Tool | Expected Time | Notes |
|------------|------------------|---------------|--------|
| 1-50 | Standard sync tools | < 5 seconds | Direct operation |
| 50-200 | Query-based tools | 10-30 seconds | Auto-async detection |
| 200-1000 | Async tools | 1-10 minutes | Background processing |
| 1000+ | Async with batching | 10-30 minutes | Progress tracking |

## Safety Notes for Testing

- Always start with `dry_run: true` to preview results
- Begin with small numbers (25-50 emails) 
- The new tools should handle timeouts that the old tools couldn't
- Monitor job progress for large operations
- Test queries with small datasets first
- Verify results before scaling up operations

## Troubleshooting Common Issues

### Tool Not Found Error
- Ensure MCP server is running with latest tools
- Check that enhanced trash tools are registered
- Verify service status with `./scripts/status.sh`

### Timeout Issues
- Switch from sync to async tools for large datasets
- Use query-based operations instead of ID-based
- Reduce batch sizes and enable progressive processing

### Low Match Results
- Adjust query specificity
- Use broader patterns for initial discovery
- Combine multiple query patterns with OR operators

## Future Usage Guide Structure

This document serves as the foundation for a comprehensive usage guide organized by:

1. **Email Categories**: Marketing, Newsletters, Social, Notifications
2. **Operation Types**: Cleanup, Archive, Organize, Analyze
3. **Scale Levels**: Small (1-50), Medium (50-500), Large (500+)
4. **Use Cases**: Daily maintenance, Bulk cleanup, Pattern analysis
5. **Advanced Patterns**: Complex queries, Multi-step operations, Automation

These prompts and examples will help users understand the capabilities and proper usage patterns for the enhanced trash tools in various real-world scenarios.