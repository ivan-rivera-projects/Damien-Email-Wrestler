# Damien Email Wrestler - AI Tool Usage Guide

## Overview
This guide documents optimal usage patterns for Damien's 43 AI-powered email management tools. Based on real-world Claude Desktop usage, these patterns ensure maximum effectiveness and accuracy.

## Core Principles

### 1. Use High-Confidence Parameters
- Always set `min_confidence: 0.85` or higher for production use
- Enable `use_statistical_validation: true` for better accuracy
- Use specific target counts rather than vague limits

### 2. Follow Async Patterns for Large Datasets
- Use async tools for > 50 emails
- Always check job status before retrieving results
- Implement proper error handling for long-running operations

### 3. Leverage AI Intelligence for Decision Making
- Focus on pattern detection and automation opportunities
- Use confidence scores to prioritize actions
- Target specific, actionable outcomes

## Tool Categories and Optimal Usage

### AI Analysis Tools

#### `damien_ai_analyze_emails_async` - PRIMARY TOOL for large datasets
**Optimal Parameters:**
```json
{
  "days": 30,
  "target_count": 100,
  "min_confidence": 0.85,
  "use_statistical_validation": true
}
```

**Usage Pattern:**
1. Start async job with optimal parameters
2. Check status with `damien_job_get_status`
3. Retrieve results with `damien_job_get_result`
4. Process automation opportunities

**Real Example (Claude Desktop Success):**
- Analyzed 100 emails
- Found 78% automation opportunities
- 92% confidence in newsletter pattern detection
- Estimated 78 minutes/week time savings

#### `damien_ai_analyze_emails` - For small datasets (< 50 emails)
**Optimal Parameters:**
```json
{
  "query": "specific search criteria",
  "max_results": 20,
  "analysis_type": "comprehensive",
  "min_confidence": 0.85
}
```

#### `damien_ai_analyze_emails_large_scale` - For 500+ emails
**Optimal Parameters:**
```json
{
  "query": "is:unread OR from:specific-domain",
  "max_results": 1000,
  "analysis_type": "comprehensive",
  "use_statistical_validation": true
}
```

### Email Management Tools

#### `damien_list_emails` - Email Discovery
**CRITICAL: Always include headers for meaningful results**
```json
{
  "query": "specific search criteria",
  "max_results": 50,
  "include_headers": ["Subject", "Date", "From"]
}
```

#### `damien_label_emails` - Smart Labeling
**Pattern: Apply AI-suggested labels**
```json
{
  "message_ids": ["id1", "id2", "id3"],
  "labels": ["AI_PROMOTIONAL", "AI_NEWSLETTER", "AI_BULK_DELETE_CANDIDATE"]
}
```

#### `damien_trash_emails` - Bulk Operations
**Pattern: Use after labeling**
```json
{
  "message_ids": ["array of email IDs"],
  // OR use query for label-based operations
  "query": "label:AI_BULK_DELETE_CANDIDATE"
}
```

### Job Management Tools

#### Async Job Workflow
1. **Start Job:** Use async tool with proper parameters
2. **Monitor Progress:** `damien_job_get_status(job_id)`
3. **Retrieve Results:** `damien_job_get_result(job_id)`
4. **Handle Completion:** Process automation opportunities

## Proven Workflows

### Workflow 1: AI-Powered Email Analysis
```
1. damien_ai_analyze_emails_async(target_count=100, min_confidence=0.85)
2. damien_job_get_status(job_id) - wait for completion
3. damien_job_get_result(job_id) - get insights
4. Process automation opportunities and patterns
```

### Workflow 2: Smart Email Categorization
```
1. damien_list_emails(include_headers=["Subject", "Date", "From"])
2. damien_ai_analyze_emails(emails, min_confidence=0.85)
3. damien_label_emails(message_ids, AI_suggested_labels)
4. damien_list_emails(query="label:AI_CATEGORY")
```

### Workflow 3: Bulk Management Based on AI Analysis
```
1. AI Analysis → Identify patterns (newsletters, promotions, etc.)
2. Label emails based on AI insights
3. Use label-based queries for bulk operations
4. damien_trash_emails(query="label:AI_BULK_DELETE_CANDIDATE")
```

## Parameter Reference

### Essential Parameters for Quality Results

#### AI Analysis Parameters
- `min_confidence`: 0.85+ (ensures high-quality patterns)
- `use_statistical_validation`: true (improves accuracy)
- `target_count`: Specific number vs vague limits
- `analysis_type`: "comprehensive" for full insights

#### Email Query Parameters
- `include_headers`: ["Subject", "Date", "From"] (ALWAYS include)
- `max_results`: Reasonable limits (50-100 for interactive, 500+ for async)
- `query`: Specific search criteria vs broad wildcards

#### Job Management
- Always check `job_id` in responses
- Poll status before retrieving results
- Handle completion and error states

## Common Mistakes to Avoid

### 1. Poor Parameter Selection
❌ `max_results: 5` with no headers
✅ `max_results: 50, include_headers: ["Subject", "Date", "From"]`

### 2. Ignoring Confidence Thresholds
❌ No confidence parameters
✅ `min_confidence: 0.85, use_statistical_validation: true`

### 3. Manual Script Approaches
❌ Complex Python scripts with cURL calls
✅ Direct tool usage with optimal parameters

### 4. Not Following Async Patterns
❌ Using sync tools for large datasets
✅ async_tool → check_status → get_result

## Real-World Success Metrics

Based on Claude Desktop usage:
- **Pattern Detection**: 78% coverage with 92% confidence
- **Time Savings**: 78 minutes/week through automation
- **Processing Speed**: 100 emails analyzed in ~13 seconds
- **Reliability**: 0.8+ reliability scores with proper parameters

## Tool Selection Guidelines

### For Small Operations (< 50 emails)
- `damien_ai_analyze_emails`
- `damien_list_emails` with headers
- Direct labeling and operations

### For Medium Operations (50-500 emails)
- `damien_ai_analyze_emails_large_scale`
- Batch operations with confidence thresholds
- Monitor for timeout issues

### For Large Operations (500+ emails)
- `damien_ai_analyze_emails_async` (MANDATORY)
- Job management pattern
- Statistical validation enabled
- Background processing

## Integration with 66k Email Dataset

For your large email dataset:
1. **Start with sampling**: Analyze 500-1000 emails first
2. **Use async processing**: Essential for large volumes
3. **Focus on patterns**: Let AI identify automation opportunities
4. **Implement gradually**: Test with small batches first
5. **Monitor performance**: Use job tracking for progress

This approach will efficiently process your 66k emails while maintaining high accuracy and providing actionable automation insights.