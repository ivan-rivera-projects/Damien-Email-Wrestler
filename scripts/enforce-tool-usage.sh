#!/bin/bash

# Damien Tool Usage Enforcement Script
# Ensures AI engines use MCP tools directly first

TOOL_USAGE_LOG="/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/logs/tool-usage.log"

log_usage() {
    echo "$(date): $1" >> "$TOOL_USAGE_LOG"
}

# Function to check if MCP tools are available
check_mcp_availability() {
    if curl -s http://localhost:8081/health | grep -q "ok"; then
        return 0
    else
        return 1
    fi
}

# Function to enforce MCP tool usage
enforce_mcp_usage() {
    local tool_name="$1"
    
    log_usage "ATTEMPT: Direct MCP tool call for $tool_name"
    
    if check_mcp_availability; then
        log_usage "SUCCESS: MCP tools available, using direct interface"
        return 0
    else
        log_usage "FALLBACK: MCP tools unavailable, allowing API fallback"
        return 1
    fi
}

# Export function for use in other scripts
export -f enforce_mcp_usage
export -f check_mcp_availability
export -f log_usage

echo "✅ Damien Tool Usage Enforcement Active"
echo "📊 Logs: $TOOL_USAGE_LOG"
echo "🎯 Policy: MCP tools first, API fallback only on failure"
