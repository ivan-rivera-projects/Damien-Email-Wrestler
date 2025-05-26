# DAMIEN TOOL USAGE POLICY - MANDATORY

## PRIMARY RULE: MCP TOOLS FIRST
**ALWAYS use MCP tools directly before attempting any API calls**

### Tool Usage Priority:
1. **FIRST**: Use damien_[tool_name] MCP tools directly
2. **ONLY IF FAILED**: Fall back to curl/API calls

### Examples of CORRECT usage:
```
✅ CORRECT: damien_list_emails with parameters
❌ WRONG: curl -X POST http://localhost:8081/execute
```

### When to use fallback:
- Tool returns error
- Tool is unavailable 
- Tool times out
- MCP server is down

### Enforcement:
- Log all tool usage attempts
- Warn when using API fallback
- Always explain why fallback was needed
- Try MCP tool again after fallback if possible

This policy ensures optimal performance, token efficiency, and proper integration usage.
