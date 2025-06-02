# Rule Creation API Parameter Mismatch - Complete Fix

## Issue Summary

Based on the analysis of the Damien Email Processing workflow, I've identified the exact root cause of the rule creation failures:

1. **CLIBridge.create_email_rule() got an unexpected keyword argument 'rule'**
2. **damien_cli.features.rule_management.models.RuleModel() argument after ** must be a mapping, not RuleDefinitionModel**

## Root Cause Analysis

### Issue 1: Keyword Argument Mismatch in AI Intelligence Tools

**Location**: `/damien-mcp-server/app/tools/ai_intelligence.py` around line 375

**Problem**: The method is being called with keyword arguments but expects positional arguments:

```python
# ❌ CURRENT (INCORRECT)
creation_result = await self.cli_bridge.create_email_rule(
    rule=parsing_result.get("rule", {})
)

# Also affects simulate_rule_creation:
creation_result = await self.cli_bridge.simulate_rule_creation(
    rule=parsing_result.get("rule", {})
)
```

**Expected Signature**: The CLIBridge methods expect positional arguments:
```python
async def create_email_rule(self, parsed_rule: Dict[str, Any]) -> Dict[str, Any]:
async def simulate_rule_creation(self, rule: Dict[str, Any]) -> Dict[str, Any]:
```

### Issue 2: Type Mismatch in Rule Model Constructor

**Location**: `/damien-mcp-server/app/services/damien_adapter.py` around line 685

**Problem**: The RuleModel constructor is receiving a non-dict object:

```python
# ❌ CURRENT (POTENTIALLY PROBLEMATIC)
new_rule_model = RuleModel(**rule_definition)
```

The issue occurs when `rule_definition` is not a proper dictionary or when it contains nested objects that can't be unpacked with `**`.

## Complete Fix Implementation

### Fix 1: Correct Method Calls in AI Intelligence Tools

**File**: `/damien-mcp-server/app/tools/ai_intelligence.py`

**Change around line 371-378**:

```python
# ✅ FIXED VERSION
# Create rule (or simulate if dry run)
if dry_run:
    creation_result = await self.cli_bridge.simulate_rule_creation(
        parsing_result.get("rule", {})
    )
    status = "dry_run_success"
else:
    creation_result = await self.cli_bridge.create_email_rule(
        parsing_result.get("rule", {})
    )
    status = "created"
```

**Key Changes**:
- Remove `rule=` keyword argument
- Pass the dictionary as a positional argument
- Apply same fix to both `simulate_rule_creation` and `create_email_rule` calls

### Fix 2: Enhance Rule Definition Validation in Adapter

**File**: `/damien-mcp-server/app/services/damien_adapter.py`

**Change around line 685 in `add_rule_tool` method**:

```python
# ✅ ENHANCED VERSION with proper validation
async def add_rule_tool(self, rule_definition: Dict[str, Any]) -> Dict[str, Any]:
    try:
        logger.debug(f"Adapter: Adding new rule: {rule_definition}")
        
        # Ensure rule_definition is a proper dictionary
        if not isinstance(rule_definition, dict):
            raise ValidationError(f"rule_definition must be a dictionary, got {type(rule_definition)}")
        
        # Convert any nested objects to dictionaries if needed
        cleaned_rule_definition = self._clean_rule_definition(rule_definition)
        
        # Create the RuleModel with validated data
        new_rule_model = RuleModel(**cleaned_rule_definition)
        added_rule = self.damien_rules_module.add_rule(new_rule_model)
        return {"success": True, "data": added_rule.model_dump(mode="json")}
        
    except ValidationError as e: 
        logger.error(f"Invalid rule definition for add_rule_tool: {e.errors()}", exc_info=True)
        return {"success": False, "error_message": f"Invalid rule definition: {e.errors()}", "error_code": "INVALID_RULE_DEFINITION"}
    except (RuleStorageError, InvalidParameterError) as e: 
        logger.error(f"Error adding rule in add_rule_tool: {e}", exc_info=True)
        return {"success": False, "error_message": str(e), "error_code": e.__class__.__name__}
    except Exception as e:
        logger.error(f"Unexpected error in add_rule_tool: {e}", exc_info=True)
        return {"success": False, "error_message": f"Unexpected error: {str(e)}", "error_code": "UNEXPECTED_ADAPTER_ERROR"}

def _clean_rule_definition(self, rule_definition: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and validate rule definition for RuleModel constructor."""
    cleaned = {}
    
    # Copy basic fields
    for field in ['name', 'description', 'is_enabled', 'condition_conjunction']:
        if field in rule_definition:
            cleaned[field] = rule_definition[field]
    
    # Handle conditions (ensure they're proper dictionaries)
    if 'conditions' in rule_definition:
        cleaned['conditions'] = []
        for condition in rule_definition['conditions']:
            if isinstance(condition, dict):
                cleaned['conditions'].append(condition)
            else:
                # Convert condition object to dict if needed
                cleaned['conditions'].append(condition.model_dump() if hasattr(condition, 'model_dump') else dict(condition))
    
    # Handle actions (ensure they're proper dictionaries)
    if 'actions' in rule_definition:
        cleaned['actions'] = []
        for action in rule_definition['actions']:
            if isinstance(action, dict):
                cleaned['actions'].append(action)
            else:
                # Convert action object to dict if needed
                cleaned['actions'].append(action.model_dump() if hasattr(action, 'model_dump') else dict(action))
    
    return cleaned
```

### Fix 3: Add Proper Error Handling in CLIBridge

**File**: `/damien-mcp-server/app/services/cli_bridge.py`

**Enhance the `create_email_rule` method around line 980**:

```python
async def create_email_rule(self, parsed_rule: Dict[str, Any]) -> Dict[str, Any]:
    """Create an email rule from parsed rule definition."""
    async with self._performance_context("create_email_rule"):
        try:
            # Validate input
            if not isinstance(parsed_rule, dict):
                raise ValueError(f"parsed_rule must be a dictionary, got {type(parsed_rule)}")
            
            # Ensure required fields are present
            required_fields = ['name', 'conditions', 'actions']
            missing_fields = [field for field in required_fields if field not in parsed_rule]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Use the existing damien_add_rule tool through call_damien_tool
            creation_result = await self.call_damien_tool(
                "damien_add_rule",
                {"rule_definition": parsed_rule}
            )
            
            if creation_result.get("success"):
                rule_data = creation_result.get("data", {})
                return {
                    "created": True,
                    "rule_id": rule_data.get("id"),
                    "status": "active",
                    "rule_definition": rule_data,
                    "creation_timestamp": time.time()
                }
            else:
                error_msg = creation_result.get("error_message", "Unknown error")
                raise Exception(f"Rule creation failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Failed to create email rule: {e}")
            return {
                "created": False,
                "error": str(e),
                "rule_definition": parsed_rule,
                "creation_timestamp": time.time()
            }
```

## Testing the Fix

### Test Case 1: Direct Rule Creation
```python
# This should now work without errors
rule_data = {
    "name": "Test Marketing Rule",
    "description": "Auto-archive marketing emails",
    "conditions": [
        {"field": "from", "operator": "contains", "value": "marketing"}
    ],
    "actions": [
        {"type": "archive"}
    ]
}

result = await ai_intelligence_tools.damien_ai_create_rule(
    rule_description="Archive emails from marketing senders",
    dry_run=False
)
```

### Test Case 2: Bulk Email Processing
```python
# This workflow should now complete without 30+ API calls
result = await ai_intelligence_tools.damien_ai_analyze_emails(days=30, max_emails=300)
if result.get("status") == "success":
    # Rule creation should work
    rule_result = await ai_intelligence_tools.damien_ai_create_rule(
        rule_description="Auto-archive newsletter emails based on analysis"
    )
```

## Verification Steps

1. **Fix Implementation**: Apply all three fixes above
2. **Service Restart**: Restart the MCP server to load the changes
3. **Test Rule Creation**: Run the test cases to verify the fixes work
4. **Monitor Logs**: Check for any remaining parameter mismatch errors

## Implementation Priority

### High Priority (Fix Immediately)
1. **Fix 1**: Method call parameter mismatch in `ai_intelligence.py`
   - This is the direct cause of "unexpected keyword argument 'rule'" error
   - Simple fix that removes keyword arguments

### Medium Priority (Implement for Robustness)
2. **Fix 2**: Enhanced validation in `damien_adapter.py`
   - Prevents the "mapping" vs "RuleDefinitionModel" error
   - Adds proper type checking and conversion

### Low Priority (Add for Complete Solution)
3. **Fix 3**: Improved error handling in `cli_bridge.py`
   - Makes the system more robust
   - Provides better error messages for debugging

## Expected Results After Fix

### Before Fix (Current State)
```
❌ Error executing code: MCP error -32603: CLIBridge.create_email_rule() got an unexpected keyword argument 'rule'
❌ Error executing code: MCP error -32603: damien_cli.features.rule_management.models.RuleModel() argument after ** must be a mapping, not RuleDefinitionModel
❌ Required 30+ API calls to process 300 emails
❌ No verification mechanism for changes
```

### After Fix (Expected State)
```
✅ Rule creation succeeds with single API call
✅ Bulk email processing works efficiently
✅ Complete workflow requires 3-5 API calls total
✅ Clear success/failure reporting
✅ Proper error handling and logging
```

## Additional Recommendations

### 1. Add Integration Tests
Create tests that verify the complete email processing workflow:

```python
async def test_complete_workflow():
    """Test the complete email processing workflow end-to-end."""
    # Step 1: Analyze emails
    analysis_result = await ai_intelligence_tools.damien_ai_analyze_emails(
        days=7, max_emails=50
    )
    assert analysis_result["status"] == "success"
    
    # Step 2: Create rule based on analysis
    rule_result = await ai_intelligence_tools.damien_ai_create_rule(
        rule_description="Archive newsletter emails",
        dry_run=True
    )
    assert rule_result["status"] in ["created", "dry_run_success"]
    
    # Step 3: Verify no parameter errors
    assert "unexpected keyword argument" not in str(rule_result)
    assert "must be a mapping" not in str(rule_result)
```

### 2. Add Performance Monitoring
Track the number of API calls required for common workflows:

```python
class WorkflowMetrics:
    def __init__(self):
        self.api_call_count = 0
        self.start_time = time.time()
    
    def track_call(self, tool_name: str):
        self.api_call_count += 1
        logger.info(f"API Call #{self.api_call_count}: {tool_name}")
    
    def get_efficiency_report(self):
        duration = time.time() - self.start_time
        return {
            "total_api_calls": self.api_call_count,
            "duration_seconds": duration,
            "efficiency_score": "excellent" if self.api_call_count <= 5 else "needs_improvement"
        }
```

### 3. Implement Batch Operations
Add true bulk operations that process multiple emails efficiently:

```python
async def bulk_process_emails(
    self,
    email_query: str,
    operations: List[Dict[str, Any]],
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Process multiple emails with multiple operations in optimized batches.
    
    Args:
        email_query: Gmail query to find emails
        operations: List of operations like [{"type": "label", "value": "Marketing"}]
        batch_size: Number of emails to process per batch
    
    Returns:
        Dict with results and performance metrics
    """
    # Implementation would batch multiple operations efficiently
    pass
```

## Long-term Architecture Improvements

### 1. Standardize Parameter Passing
Implement a consistent parameter schema across all MCP tools:

```python
class ToolParameters(BaseModel):
    """Standard parameter structure for all MCP tools."""
    operation_type: str
    parameters: Dict[str, Any]
    options: Optional[Dict[str, Any]] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for method calls."""
        return self.parameters
```

### 2. Add Parameter Validation Middleware
Create middleware that validates parameters before they reach the tools:

```python
def validate_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean parameters for a specific tool."""
    schema = get_tool_schema(tool_name)
    validated_params = schema.validate(parameters)
    return validated_params
```

### 3. Implement Circuit Breaker Pattern
Add circuit breakers to prevent cascade failures:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

## Conclusion

The rule creation parameter mismatch issue is now clearly identified and can be resolved with the three fixes outlined above. The primary fix (removing keyword arguments from method calls) will immediately resolve the "unexpected keyword argument 'rule'" error. The additional fixes will make the system more robust and prevent similar issues in the future.

After implementing these fixes, the email processing workflow should work efficiently with minimal API calls, and rule creation should succeed consistently without parameter mismatch errors.