# Timeout Analysis and Intelligent Tool Routing Solution

## Problem Statement
Large-scale email analysis (800+ emails) is timing out due to:
- 30-second MCP client timeout
- Gmail API rate limiting  
- Synchronous processing of large datasets
- No automatic tool routing based on volume

## Current Timeout Points
1. `damien_ai_analyze_emails_large_scale`: 30s timeout processing 800 emails
2. `damien_ai_analyze_emails_async`: Also timing out (architectural issue)
3. `damien_list_emails`: Timing out on large queries

## Proposed Solution: Intelligent Volume-Based Tool Routing

### Routing Logic
```javascript
function selectOptimalTool(emailCount, userRequest) {
    if (emailCount <= 300) {
        return "damien_ai_analyze_emails"; // Fast synchronous
    } else if (emailCount <= 1000) {
        return "damien_ai_analyze_emails_async"; // Background job
    } else {
        return "damien_ai_analyze_emails_large_scale"; // Statistical sampling
    }
}
```

### Implementation Points

#### 1. Pre-Analysis Volume Detection
```javascript
// Before analysis, estimate email count
const estimatedCount = await getEmailCount(query, days);
const selectedTool = selectOptimalTool(estimatedCount);
```

#### 2. Timeout Configuration Updates
- **Sync tools**: 30s timeout (adequate for ≤300 emails)
- **Async tools**: 5s response + background processing
- **Large-scale**: 60s timeout with chunked processing

#### 3. Async Tool Fixes
- Return job ID immediately (no 30s wait)
- Process in background chunks
- Provide status/progress endpoints

#### 4. Automatic Fallback Logic
```javascript
if (syncToolTimeout && emailCount > 200) {
    console.log("Auto-switching to async processing...");
    return await processAsync(parameters);
}
```

## Implementation Plan

### Phase 1: Fix Async Tool (Immediate)
1. Fix `damien_ai_analyze_emails_async` to return job ID immediately
2. Implement proper background processing
3. Add job status checking

### Phase 2: Smart Routing (Next)
1. Add email count estimation to all analysis tools
2. Implement automatic tool selection logic
3. Add user notification of tool switching

### Phase 3: Timeout Optimization (Future)
1. Increase timeouts for appropriate tools
2. Add chunked processing for large datasets
3. Implement progress tracking

## Benefits
- **User Experience**: No manual tool selection needed
- **Reliability**: Automatic handling of large datasets
- **Performance**: Optimal tool for each use case
- **Scalability**: Supports 100k+ email processing

## Immediate Workaround
For now, users should:
- Use `damien_ai_analyze_emails` for ≤300 emails
- Use `damien_ai_analyze_emails_async` for 300+ emails (once fixed)
- Manually chunk large requests until automatic routing is implemented

## Test Cases Needed
1. 50 emails → sync tool
2. 300 emails → sync tool (boundary)
3. 500 emails → async tool
4. 1000+ emails → large-scale tool
5. Timeout simulation and recovery