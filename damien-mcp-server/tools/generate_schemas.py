#!/usr/bin/env python
"""
Generate formal JSON schemas for Damien MCP tools.

This script creates well-defined JSON schemas for all Damien tools
that can be used to configure Claude or other MCP-compliant AI assistants.
"""

import json
import os
from typing import Dict, Any, List

# Create output directory if it doesn't exist
os.makedirs('tools/schemas', exist_ok=True)

def create_tool_schema(
    name: str,
    description: str,
    properties: Dict[str, Any],
    required: List[str] = None,
    examples: Dict[str, Any] = None,
    output_schema: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a standardized tool schema following MCP conventions."""
    if required is None:
        required = []
    
    if examples is None:
        examples = {}

    schema = {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }
    
    # Add examples if provided
    if examples:
        schema["input_schema"]["examples"] = examples
    
    # Add output schema if provided
    if output_schema:
        schema["output_schema"] = output_schema
    
    return schema

# Tool 1: damien_list_emails (OPTIMIZED)
list_emails_schema = create_tool_schema(
    name="damien_list_emails",
    description="""
    ⚡ OPTIMIZATION REQUIRED: Lists email messages with support for pagination. 
    ALWAYS use 'include_headers' parameter to fetch all needed data in ONE call 
    instead of making multiple get_email_details calls. This saves 10x time and tokens.
    
    Example: include_headers=["From", "Subject", "Date", "To", "List-Unsubscribe"]
    
    Token Efficiency Tips:
    - Use include_headers for common fields (saves 90% follow-up calls)
    - Set appropriate max_results (default 10, max 100)  
    - Use query filters to reduce irrelevant results
    - Gmail query examples: 'is:unread from:boss@example.com', 'subject:report older_than:7d'
    """,
    properties={
        "query": {
            "type": "string",
            "description": "Optional. Gmail search query string to filter emails. "
                          "Examples: 'is:unread from:boss@example.com', 'subject:report older_than:7d'. "
                          "If omitted, lists recent emails."
        },
        "max_results": {
            "type": "integer",
            "description": "Optional. Maximum number of email summaries to return (default: 10, max: 100). "
                          "Use lower values for faster responses and token efficiency.",
            "default": 10,
            "minimum": 1,
            "maximum": 100
        },
        "page_token": {
            "type": "string",
            "description": "Optional. Pagination token from a previous call to fetch next page."
        },
        "include_headers": {
            "type": "array",
            "items": {"type": "string"},
            "description": "🚀 PERFORMANCE OPTIMIZATION: List of header names to include in response. "
                          "This ELIMINATES the need for separate get_email_details calls, saving 10x tokens. "
                          "Common headers: ['From', 'Subject', 'Date', 'To', 'Cc', 'List-Unsubscribe']. "
                          "Use this for ANY operation that needs email details!",
            "examples": [
                ["From", "Subject", "Date"],
                ["From", "Subject", "Date", "To", "List-Unsubscribe"],
                ["From", "Subject", "Date", "To", "Cc", "Bcc", "Reply-To"]
            ]
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "email_summaries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "thread_id": {"type": "string"},
                        "subject": {"type": "string"},
                        "from": {"type": "string"},
                        "snippet": {"type": "string"},
                        "date": {"type": "string"},
                        "has_attachments": {"type": "boolean"},
                        "headers": {
                            "type": "object",
                            "description": "Requested headers (when include_headers used)"
                        }
                    }
                }
            },
            "next_page_token": {"type": "string"},
            "performance_info": {
                "type": "object",
                "properties": {
                    "tokens_saved": {"type": "number"},
                    "api_calls_avoided": {"type": "number"}
                }
            }
        }
    }
)

# Tool 2: damien_get_email_details
get_email_details_schema = create_tool_schema(
    name="damien_get_email_details",
    description="Retrieves detailed information for a specific email using its unique ID. "
               "Can fetch metadata, full content, or raw format.",
    properties={
        "message_id": {
            "type": "string",
            "description": "The unique ID of the email to retrieve. This ID is typically obtained from a 'damien_list_emails' call."
        },
        "format": {
            "type": "string",
            "enum": ["metadata", "full", "raw"],
            "description": "Optional. The level of detail to retrieve. 'metadata' for headers and snippet (fastest), "
                          "'full' for parsed content including body, 'raw' for the complete raw email. Defaults to 'full'."
        }
    },
    required=["message_id"]
)

# Tool 3: damien_trash_emails
trash_emails_schema = create_tool_schema(
    name="damien_trash_emails",
    description="Moves one or more specified emails (by their IDs) to the Gmail Trash folder. "
               "Emails in Trash are typically deleted permanently after 30 days.",
    properties={
        "message_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of unique email IDs to be moved to Trash."
        }
    },
    required=["message_ids"]
)

# Tool 4: damien_label_emails
label_emails_schema = create_tool_schema(
    name="damien_label_emails",
    description="Adds or removes specified labels from one or more emails. Provide label names as seen in Gmail.",
    properties={
        "message_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of unique email IDs to modify."
        },
        "add_label_names": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional. A list of label names to add to the emails (e.g., ['Important', 'ProjectX']). "
                         "System labels like 'STARRED' or 'IMPORTANT' can be used."
        },
        "remove_label_names": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional. A list of label names to remove from the emails (e.g., ['OldProject', 'UNREAD']). "
                         "System labels like 'UNREAD' or 'INBOX' can be used."
        }
    },
    required=["message_ids"]
)

# Tool 5: damien_mark_emails
mark_emails_schema = create_tool_schema(
    name="damien_mark_emails",
    description="Marks one or more specified emails as 'read' or 'unread'.",
    properties={
        "message_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of unique email IDs to mark."
        },
        "mark_as": {
            "type": "string",
            "enum": ["read", "unread"],
            "description": "The state to mark the emails: 'read' or 'unread'."
        }
    },
    required=["message_ids", "mark_as"]
)

# Tool 6: damien_delete_emails_permanently
delete_emails_permanently_schema = create_tool_schema(
    name="damien_delete_emails_permanently",
    description="CRITICAL WARNING: Permanently deletes one or more specified emails. "
               "This action is IRREVERSIBLE and emails CANNOT be recovered. "
               "Use with extreme caution. Emails are removed completely and do not go to Trash.",
    properties={
        "message_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of unique email IDs to be PERMANENTLY DELETED. Double-check these IDs carefully."
        }
    },
    required=["message_ids"]
)

# Tool 7: damien_apply_rules
apply_rules_schema = create_tool_schema(
    name="damien_apply_rules",
    description="Applies configured filtering rules to emails in the Gmail account. "
               "Can operate on all emails or a filtered subset. Reports a summary of actions taken or planned.",
    properties={
        "gmail_query_filter": {
            "type": "string",
            "description": "Optional. A Gmail search query to narrow down which emails are scanned for rule application "
                         "(e.g., 'in:inbox is:unread')."
        },
        "rule_ids_to_apply": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional. A list of specific rule IDs or rule names to apply. If omitted, all enabled rules are considered."
        },
        "dry_run": {
            "type": "boolean",
            "description": "Optional. If true, simulates rule application and reports what actions *would* be taken "
                         "without actually modifying any emails. Defaults to false (meaning actions will be executed). "
                         "Recommended to use dry_run:true first for verification."
        },
        "scan_limit": {
            "type": "integer",
            "description": "Optional. Limits the total number of recent emails (or emails matching the main query) to "
                         "fetch and consider for rule application. Useful for very large mailboxes or initial testing."
        },
        "date_after": {
            "type": "string",
            "format": "date",
            "description": "Optional. Process emails received after this date (YYYY/MM/DD or YYYY-MM-DD)."
        },
        "date_before": {
            "type": "string",
            "format": "date",
            "description": "Optional. Process emails received before this date (YYYY/MM/DD or YYYY-MM-DD)."
        },
        "all_mail": {
            "type": "boolean",
            "description": "Optional. If true, attempts to process all mail irrespective of date (unless other date filters are specified). "
                         "Use with caution on large mailboxes; combine with scan_limit or specific queries. "
                         "Defaults to processing recent mail (e.g., last 30 days if no other date filters)."
        }
    }
)

# Tool 8: damien_list_rules
list_rules_schema = create_tool_schema(
    name="damien_list_rules",
    description="Lists all currently configured filtering rules in Damien.",
    properties={}  # No input parameters needed
)

# Tool 9: damien_add_rule
add_rule_schema = create_tool_schema(
    name="damien_add_rule",
    description="Adds a new filtering rule to Damien. The rule definition must be a valid JSON object matching Damien's rule structure.",
    properties={
        "rule_definition": {
            "type": "object",
            "description": "A JSON object defining the rule. Must include 'name' (string), 'conditions' (array of condition objects), "
                          "and 'actions' (array of action objects). Optional fields: 'description' (string), 'is_enabled' (boolean, "
                          "defaults to true), 'condition_conjunction' (string 'AND' or 'OR', defaults to 'AND'). "
                          "Example condition: {'field': 'from', 'operator': 'contains', 'value': 'spam@example.com'}. "
                          "Example action: {'type': 'trash'}.",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "is_enabled": {"type": "boolean"},
                "conditions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "operator": {"type": "string"},
                            "value": {"type": "string"}
                        }
                    }
                },
                "condition_conjunction": {"type": "string", "enum": ["AND", "OR"]},
                "actions": {
                    "type": "array",
                    "items": {"type": "object"}
                }
            },
            "required": ["name", "conditions", "actions"]
        }
    },
    required=["rule_definition"]
)

# Tool 10: damien_delete_rule
delete_rule_schema = create_tool_schema(
    name="damien_delete_rule",
    description="Deletes an existing filtering rule from Damien, specified by its unique ID or name.",
    properties={
        "rule_identifier": {
            "type": "string",
            "description": "The unique ID or the name of the rule to be deleted."
        }
    },
    required=["rule_identifier"]
)

# Collect all schemas
all_schemas = [
    list_emails_schema,
    get_email_details_schema,
    trash_emails_schema,
    label_emails_schema,
    mark_emails_schema,
    delete_emails_permanently_schema,
    apply_rules_schema,
    list_rules_schema,
    add_rule_schema,
    delete_rule_schema
]

# Write individual schema files
for schema in all_schemas:
    filename = f"tools/schemas/{schema['name']}.json"
    with open(filename, 'w') as f:
        json.dump(schema, f, indent=2)
    print(f"Created schema: {filename}")

# Write the combined schema file
with open('tools/schemas/damien_all_tools.json', 'w') as f:
    json.dump(all_schemas, f, indent=2)
print("Created combined schema: tools/schemas/damien_all_tools.json")

print(f"Successfully generated {len(all_schemas)} tool schemas for Damien MCP Server")
