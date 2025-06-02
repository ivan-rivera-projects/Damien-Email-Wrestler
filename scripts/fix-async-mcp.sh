# Quick MCP Registration Fix Script
# Run this to enable async tools in Claude Desktop

cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien_mcp_server/app/routers

# Create a clean working tools.py with async tools
cat > tools_async_fix.py << 'EOF'
# Add async tools to the get_tools() function before the closing ]
# Insert this block before the last } in the tools array:

        {
            "name": "damien_ai_analyze_emails_async",
            "description": "🚀 LARGE-SCALE BACKGROUND EMAIL ANALYSIS - No more timeouts! Processes 3,000+ emails in background with progress tracking.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30},
                    "target_count": {"type": "integer", "minimum": 1, "maximum": 10000, "default": 1000},
                    "min_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.85},
                    "query": {"type": "string", "default": "", "description": "Gmail search query (e.g., 'is:unread')"},
                    "use_statistical_validation": {"type": "boolean", "default": true}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "job_id": {"type": "string"},
                    "status": {"type": "string"},
                    "tracking": {"type": "object"},
                    "estimated_duration_minutes": {"type": "integer"}
                }
            }
        },
        {
            "name": "damien_job_get_status",
            "description": "📊 Track background job progress with real-time updates",
            "input_schema": {
                "type": "object",
                "properties": {"job_id": {"type": "string"}},
                "required": ["job_id"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "status": {"type": "string"},
                    "progress": {"type": "object"}
                }
            }
        },
        {
            "name": "damien_job_get_result",
            "description": "🎯 Get comprehensive analysis results when job completes",
            "input_schema": {
                "type": "object",
                "properties": {"job_id": {"type": "string"}},
                "required": ["job_id"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "result": {"type": "object"}
                }
            }
        }
EOF

echo "MCP registration fix created. Run this to enable async tools in Claude Desktop interface."
