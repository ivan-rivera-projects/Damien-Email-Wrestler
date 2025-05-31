"""
AI Intelligence MCP Tools Registration

This module registers the 6 AI intelligence MCP tools with the tool registry,
making them available through the MCP server for AI assistant integration.
"""

from ..services.tool_registry import tool_registry, ToolDefinition
from ..tools.ai_intelligence import ai_intelligence_tools
import logging

logger = logging.getLogger(__name__)

# Define AI Intelligence tool schemas
AI_INTELLIGENCE_TOOLS = {
    "damien_ai_analyze_emails": ToolDefinition(
        name="damien_ai_analyze_emails",
        description="Perform comprehensive AI analysis of Gmail emails with pattern detection, business impact analysis, and intelligent insights generation.",
        input_schema={
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 30)",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 365
                },
                "max_emails": {
                    "type": "integer", 
                    "description": "Maximum number of emails to process (default: 500)",
                    "default": 500,
                    "minimum": 1,
                    "maximum": 2000
                },
                "min_confidence": {
                    "type": "number",
                    "description": "Minimum confidence threshold for patterns (default: 0.7)",
                    "default": 0.7,
                    "minimum": 0.1,
                    "maximum": 1.0
                },
                "output_format": {
                    "type": "string",
                    "enum": ["summary", "detailed", "json"],
                    "description": "Output format (default: summary)",
                    "default": "summary"
                },
                "query": {
                    "type": "string",
                    "description": "Optional Gmail search query to filter emails"
                },
                "patterns_only": {
                    "type": "boolean",
                    "description": "Return only pattern detection results (default: false)",
                    "default": False
                }
            }
        },
        handler="analyze_emails_handler",
        requires_scopes=["gmail_read"],
        rate_limit_group="ai_analysis"
    ),
    
    "damien_ai_suggest_rules": ToolDefinition(
        name="damien_ai_suggest_rules",
        description="Generate intelligent email management rules based on ML pattern analysis with business impact assessment and confidence scoring.",
        input_schema={
            "type": "object", 
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rule suggestions (default: 5)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "min_confidence": {
                    "type": "number",
                    "description": "Minimum confidence for suggestions (default: 0.8)",
                    "default": 0.8,
                    "minimum": 0.5,
                    "maximum": 1.0
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific categories to analyze (optional)"
                },
                "include_business_impact": {
                    "type": "boolean",
                    "description": "Include business impact analysis (default: true)",
                    "default": True
                },
                "auto_validate": {
                    "type": "boolean", 
                    "description": "Automatically validate suggestions (default: true)",
                    "default": True
                }
            }
        },
        handler="suggest_rules_handler",
        requires_scopes=["gmail_read"],
        rate_limit_group="ai_analysis"
    ),
    
    "damien_ai_quick_test": ToolDefinition(
        name="damien_ai_quick_test",
        description="Quick validation of AI integration and performance with component health checking and system readiness assessment.",
        input_schema={
            "type": "object",
            "properties": {
                "sample_size": {
                    "type": "integer",
                    "description": "Number of emails for testing (default: 50)",
                    "default": 50,
                    "minimum": 5,
                    "maximum": 200
                },
                "days": {
                    "type": "integer",
                    "description": "Days of recent emails to test (default: 7)",
                    "default": 7,
                    "minimum": 1,
                    "maximum": 30
                },
                "include_performance": {
                    "type": "boolean",
                    "description": "Include performance benchmarking (default: true)",
                    "default": True
                },
                "validate_components": {
                    "type": "boolean",
                    "description": "Validate component health (default: true)",
                    "default": True
                }
            }
        },
        handler="quick_test_handler",
        requires_scopes=["gmail_read"],
        rate_limit_group="ai_testing"
    ),
    
    "damien_ai_create_rule": ToolDefinition(
        name="damien_ai_create_rule",
        description="Create email rules using natural language descriptions with GPT-powered intent recognition and validation.",
        input_schema={
            "type": "object",
            "properties": {
                "rule_description": {
                    "type": "string",
                    "description": "Natural language description of the rule",
                    "minLength": 10,
                    "maxLength": 500
                },
                "validate_before_create": {
                    "type": "boolean",
                    "description": "Validate rule before creation (default: true)",
                    "default": True
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview only, don't create (default: false)",
                    "default": False
                },
                "confidence_threshold": {
                    "type": "number",
                    "description": "Minimum confidence for creation (default: 0.8)",
                    "default": 0.8,
                    "minimum": 0.5,
                    "maximum": 1.0
                }
            },
            "required": ["rule_description"]
        },
        handler="create_rule_handler",
        requires_scopes=["gmail_modify"],
        rate_limit_group="ai_modifications"
    ),
    
    "damien_ai_get_insights": ToolDefinition(
        name="damien_ai_get_insights",
        description="Get comprehensive email intelligence and insights with trend analysis, efficiency metrics, and predictive modeling.",
        input_schema={
            "type": "object",
            "properties": {
                "insight_type": {
                    "type": "string",
                    "enum": ["trends", "patterns", "efficiency", "summary"],
                    "description": "Type of insights to generate (default: summary)",
                    "default": "summary"
                },
                "time_range": {
                    "type": "integer",
                    "description": "Time range in days (default: 30)",
                    "default": 30,
                    "minimum": 7,
                    "maximum": 365
                },
                "include_predictions": {
                    "type": "boolean",
                    "description": "Include predictive analysis (default: false)",
                    "default": False
                },
                "format": {
                    "type": "string",
                    "enum": ["text", "json", "chart_data"],
                    "description": "Output format (default: text)",
                    "default": "text"
                }
            }
        },
        handler="get_insights_handler",
        requires_scopes=["gmail_read"],
        rate_limit_group="ai_analysis"
    ),
    
    "damien_ai_optimize_inbox": ToolDefinition(
        name="damien_ai_optimize_inbox",
        description="AI-powered inbox optimization with multi-strategy algorithms, risk assessment, and rollback capabilities.",
        input_schema={
            "type": "object",
            "properties": {
                "optimization_type": {
                    "type": "string",
                    "enum": ["declutter", "organize", "automate", "all"],
                    "description": "Type of optimization (default: all)",
                    "default": "all"
                },
                "aggressiveness": {
                    "type": "string",
                    "enum": ["conservative", "moderate", "aggressive"],
                    "description": "Optimization aggressiveness (default: moderate)",
                    "default": "moderate"
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Simulate only, don't execute (default: true)",
                    "default": True
                },
                "max_actions": {
                    "type": "integer",
                    "description": "Maximum number of actions (default: 100)",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 500
                }
            }
        },
        handler="optimize_inbox_handler",
        requires_scopes=["gmail_modify"],
        rate_limit_group="ai_modifications"
    )
}


def register_ai_intelligence_tools():
    """Register all AI intelligence tools with the tool registry."""
    logger.info("🚀 Starting registration of AI intelligence tools...")
    
    # Import the handler functions (CRITICAL FIX)
    from .ai_intelligence import (
        analyze_emails_handler,
        suggest_rules_handler,
        quick_test_handler,
        create_rule_handler,
        get_insights_handler,
        optimize_inbox_handler
    )
    
    # Map handler names to actual handler functions
    handlers = {
        "analyze_emails_handler": analyze_emails_handler,
        "suggest_rules_handler": suggest_rules_handler,
        "quick_test_handler": quick_test_handler,
        "create_rule_handler": create_rule_handler,
        "get_insights_handler": get_insights_handler,
        "optimize_inbox_handler": optimize_inbox_handler
    }
    
    # Register each AI intelligence tool with proper handlers
    for tool_name, tool_def in AI_INTELLIGENCE_TOOLS.items():
        handler = handlers[tool_def.handler_name]
        tool_registry.register_tool(tool_def, handler)
        logger.info(f"✅ Registered {tool_name} with handler {tool_def.handler_name}")
    
    logger.info(f"✅ Successfully registered {len(AI_INTELLIGENCE_TOOLS)} AI intelligence tools with MCP handlers")


# Export for import in main.py
__all__ = ["register_ai_intelligence_tools"]
