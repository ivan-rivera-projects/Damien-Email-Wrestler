# API Routing Fix for Thread Tools

## Problem
1. Thread tools were correctly registered with the tool_registry but not properly processed when executing them through the API endpoint. The `execute_tool_endpoint` in `tools.py` was missing the thread tools in the list of tools that should be routed to the registry-based handlers.

2. The thread tool handlers were expecting a Pydantic model instance as the first parameter, but were receiving a dictionary of parameters from the API endpoint.

## Solution
### Part 1: Add thread tools to the API router
1. Added the thread tool names to the list of registry-based tools in the execute_tool_endpoint condition:
   ```python
   # Added thread tools to the registry-based tools section
   elif tool_name in ["damien_create_draft", ..., 
                      # Thread tools added here
                      "damien_list_threads", "damien_get_thread_details",
                      "damien_modify_thread_labels", "damien_trash_thread",
                      "damien_delete_thread_permanently"]:
   ```

2. Imported the thread_tools module at the bottom of the file to ensure it's loaded:
   ```python
   # Import the tool modules to register their tools
   from ..tools import settings_tools
   from ..tools import draft_tools
   from ..tools import thread_tools  # Added thread_tools import
   ```

3. Added more debug logging to help troubleshoot any registry lookup issues.

### Part 2: Update thread tool handlers to accept dictionaries
Fixed all thread tool handlers to properly handle parameter dictionaries:

1. Modified the function signatures to accept a dictionary:
   ```python
   # Old signature
   async def list_threads_handler(params: ListThreadsParams, context: Dict[str, Any])
   
   # New signature
   async def list_threads_handler(params_dict: Dict[str, Any], context: Dict[str, Any])
   ```

2. Added code to convert the dictionary to a Pydantic model instance:
   ```python
   # Parse parameters from dict
   params = ListThreadsParams(**params_dict) if isinstance(params_dict, dict) else params_dict
   ```

3. Added logging to help with debugging:
   ```python
   logger.info(f"Processing list_threads with params: {params}")
   ```

4. Updated all five thread tool handlers:
   - list_threads_handler
   - get_thread_details_handler
   - modify_thread_labels_handler
   - trash_thread_handler
   - delete_thread_permanently_handler

## Testing
- Created test scripts to verify the fix:
  - `test_thread_tools.py`: Python script to test API functionality
  - `restart_server.sh`: Script to restart the server with our changes
  - `check_fix.sh`: Shell script to verify the fix with curl commands

## Verification
After applying the fix, all 28 tools (including the 5 thread tools) should be accessible via the MCP API.

## Next Steps
1. Run full test suite to verify all tools are working correctly
2. Address the 'emails' not defined issue in CLI tests as a separate task
3. Update test expectations for enhanced response structure

