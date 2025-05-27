# MCP Tool Handler Fix Pattern

## Problem Identified

**Root Cause**: Tool handlers in the registry expect two parameters (`params` and `context`) but the router was only passing one parameter (`params_dict`).

**Error**: `create_draft_handler() missing 1 required positional argument: 'context'`

## Universal Fix Pattern

### Issue 1: Missing Context Parameter

**Problem**: Router calling handlers with only parameters:
```python
api_response = await handler_func(params_dict)
```

**Solution**: Router must pass both parameters and context:
```python
# Prepare context for the handler
context = {
    "session_id": session_id,
    "user_id": user_id,
    "tool_name": tool_name,
    "timestamp": mcp_response.tool_result_id
}

# Execute the handler with both parameters and context
api_response = await handler_func(params_dict, context)
```

### Issue 2: Tool Registration Not Executed

**Problem**: Tool definition exists but registration function not called:
```python
def register_tools():
    # Registration logic here
    pass

# Missing: Actually calling the function!
```

**Solution**: Call registration when module is imported:
```python
def register_tools():
    # Registration logic here
    pass

# Add this line at the end of the module:
register_tools()
```

### Issue 3: Missing Module Import

**Problem**: Tool modules not imported in router, so registration never happens.

**Solution**: Import tool modules in router:
```python
# At the end of tools.py router
from ..tools import settings_tools
from ..tools import draft_tools  # Add this line
```

### Issue 4: Handler Response Format

**Problem**: Handlers throwing exceptions instead of returning error responses.

**Solution**: Handlers should always return a standardized response:
```python
async def handler_function(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Tool logic here
        result = some_operation()
        
        return {
            "success": True,
            "data": {
                **result,
                "user_context": context
            }
        }
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": f"Error: {str(e)}",
            "data": None
        }
```

### Issue 5: Gmail Service Access

**Problem**: Handlers trying to create new adapters or call non-existent methods:
```python
damien_adapter = DamienAdapter()
gmail_service = await damien_adapter.get_gmail_service()  # Method doesn't exist
```

**Solution**: Use the Gmail integration directly:
```python
from damien_cli.integrations.gmail_integration import get_gmail_service
gmail_service = get_gmail_service()
```

## Files Modified for Draft Tools Fix

1. **`/app/routers/tools.py`**:
   - Added context parameter preparation
   - Fixed handler calling with both params and context
   - Added import for draft_tools module

2. **`/app/tools/draft_tools.py`**:
   - Fixed handler to use correct Gmail service access
   - Added standardized error handling with success/error response format
   - Added registration call at module end

3. **Fixed Response Format**:
   - Router expects `response.get("success")` to determine if operation succeeded
   - Handlers now return `{"success": True/False, "data": {...}, "error_message": "..."}` format

## Apply This Pattern to Any Tool

To fix any tool handler system:

1. **Check handler signature**: Must accept `(params, context)`
2. **Check router invocation**: Must pass both parameters
3. **Check registration**: Function must be called when module imported
4. **Check import**: Module must be imported in router
5. **Check response format**: Handlers return standardized success/error format
6. **Check service access**: Use correct authentication method

## Validation Test

After applying fixes:
```bash
# Test the tool directly
curl -H "X-API-Key: your-key" \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "damien_create_draft", 
       "input": {
         "to": ["test@example.com"], 
         "subject": "Test", 
         "body": "Test body"
       }, 
       "session_id": "test"
     }' \
     http://localhost:8892/mcp/execute_tool
```

Expected response:
```json
{
  "is_error": false,
  "output": {
    "success": true,
    "data": {
      "id": "draft_id",
      "created_at": "2025-05-25T...",
      ...
    }
  }
}
```

This pattern can be applied to **all** tool types (settings tools, future tools, etc.) to ensure consistent behavior.
