"""
Email Organization Tools - Unified tools for smart email organization.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Add CLI module to Python path for direct imports
CLI_PATH = Path(__file__).parent.parent.parent.parent / "damien-cli"
sys.path.insert(0, str(CLI_PATH))


async def damien_create_label_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new Gmail label.
    
    Args:
        params: Dict containing:
            - name: Label name to create
            - color: Optional dict with "background" and "text" hex colors
            - visibility: Optional visibility setting ("show", "showIfUnread", "hide")
    
    Returns:
        Dict containing label creation result
    """
    try:
        name = params.get("name")
        if not name:
            return {
                "error": "Label name is required",
                "success": False
            }
        
        # Import Gmail API service directly
        from damien_cli.core_api.gmail_api_service import get_authenticated_service, create_label
        
        # Get authenticated Gmail service
        service = get_authenticated_service()
        
        # Extract color parameters
        color_bg = None
        color_text = None
        if params.get("color"):
            color_bg = params["color"].get("background")
            color_text = params["color"].get("text")
        
        # Create the label
        result = create_label(
            service,
            name,
            "labelShow",  # Default visibility
            "show",       # Default message visibility
            color_bg,
            color_text
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating label: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


async def damien_delete_label_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete a Gmail label.
    
    Args:
        params: Dict containing:
            - name: Label name or ID to delete
    
    Returns:
        Dict containing deletion result
    """
    try:
        name = params.get("name")
        if not name:
            return {
                "error": "Label name is required",
                "success": False
            }
        
        # Import Gmail API service directly
        from damien_cli.core_api.gmail_api_service import get_authenticated_service, delete_label
        
        # Get authenticated Gmail service
        service = get_authenticated_service()
        
        # Delete the label
        result = delete_label(service, name)
        
        return result
        
    except Exception as e:
        logger.error(f"Error deleting label: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


async def damien_smart_rule_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a rule from natural language instruction.
    
    Args:
        params: Dict containing:
            - instruction: Natural language rule description
            - preview: Whether to preview affected emails first (default: True)
            - apply_to_existing: Whether to apply to existing emails (default: False)
    
    Returns:
        Dict containing rule creation result with any created labels
    """
    try:
        instruction = params.get("instruction")
        if not instruction:
            return {
                "error": "Instruction is required",
                "success": False
            }
        
        preview = params.get("preview", True)
        apply_to_existing = params.get("apply_to_existing", False)
        
        # Simple natural language parsing for demo
        instruction_lower = instruction.lower()
        
        # Extract components from instruction
        name = f"Smart Rule: {instruction[:50]}..."
        conditions = []
        actions = []
        
        # Parse sender patterns
        if "from " in instruction_lower:
            # Extract sender (simple pattern matching)
            start = instruction_lower.find("from ") + 5
            end = instruction_lower.find(" ", start)
            if end == -1:
                end = len(instruction)
            sender = instruction[start:end].strip()
            conditions.append({
                "field": "from",
                "operator": "contains",
                "value": sender
            })
        
        # Parse actions
        if "archive" in instruction_lower:
            actions.append({"type": "archive"})
        
        if "label" in instruction_lower and "with" in instruction_lower:
            # Extract label name (simple pattern)
            if "label " in instruction_lower:
                start = instruction_lower.find("label ") + 6
                # Look for common label patterns
                label_end_words = [" and", " to", " then", " also"]
                end = len(instruction)
                for end_word in label_end_words:
                    if end_word in instruction_lower[start:]:
                        end = start + instruction_lower[start:].find(end_word)
                        break
                
                label_name = instruction[start:end].strip(' "\'"')
                if label_name:
                    actions.append({
                        "type": "add_label",
                        "label_name": label_name
                    })
        
        # Create rule definition
        rule_def = {
            "name": name,
            "conditions": conditions,
            "actions": actions,
            "is_enabled": True,
            "condition_conjunction": "AND",
            "description": f"Auto-generated from: {instruction}"
        }
        
        if preview:
            return {
                "success": True,
                "preview": True,
                "rule": rule_def,
                "message": f"Preview: Would create rule with {len(conditions)} conditions and {len(actions)} actions"
            }
        
        # Import and use existing rule creation
        from ..services.damien_adapter import DamienAdapter
        adapter = DamienAdapter()
        
        # Create the rule
        result = await adapter.add_rule_tool(rule_definition=rule_def)
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating smart rule: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


async def damien_organize_emails_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    One-stop email organization - creates labels, rules, and applies them.
    
    Args:
        params: Dict containing:
            - pattern: Email pattern in natural language (e.g., "from Shopify about customers")
            - action: Action to take (e.g., "archive with label 'Shopify Support'")
            - apply_to_existing: Whether to apply to existing emails (default: True)
            - dry_run: Preview mode without making changes (default: False)
    
    Returns:
        Dict containing:
            - created_labels: List of labels created
            - rule_created: The rule that was created
            - emails_processed: Number of existing emails processed
            - preview: List of emails that would be affected (if dry_run)
    """
    try:
        pattern = params.get("pattern")
        action = params.get("action")
        
        if not pattern or not action:
            return {
                "error": "Both pattern and action are required",
                "success": False
            }
        
        apply_to_existing = params.get("apply_to_existing", True)
        dry_run = params.get("dry_run", False)
        
        # Combine pattern and action into a full instruction
        instruction = f"{action} emails {pattern}"
        
        # Step 1: Parse the instruction and extract label name
        created_labels = []
        action_lower = action.lower()
        
        # Extract label name from action
        label_name = None
        if "label" in action_lower:
            # Find label name in quotes or after "label"
            import re
            # Look for quoted label names
            quote_match = re.search(r'["\']([^"\']+)["\']', action)
            if quote_match:
                label_name = quote_match.group(1)
            else:
                # Look for "label X" pattern
                label_match = re.search(r'label\s+([^"\'\s]+(?:\s+[^"\'\s]+)*)', action_lower)
                if label_match:
                    # Extract from original action to preserve case
                    start = action_lower.find(label_match.group(0))
                    end = start + len(label_match.group(0))
                    label_part = action[start:end]
                    label_name = label_part.split('label')[1].strip()
        
        # Step 2: Create label if needed and not in dry run mode
        if label_name and not dry_run:
            try:
                label_result = await damien_create_label_handler(
                    {"name": label_name}, context
                )
                if label_result.get("success") and label_result.get("created"):
                    created_labels.append(label_name)
            except Exception as e:
                logger.warning(f"Could not create label '{label_name}': {e}")
        
        # Step 3: Parse pattern for rule conditions
        conditions = []
        pattern_lower = pattern.lower()
        
        # Extract sender
        if "from " in pattern_lower:
            sender_start = pattern_lower.find("from ") + 5
            sender_end = len(pattern)
            for end_word in [" with", " about", " subject", " and"]:
                if end_word in pattern_lower[sender_start:]:
                    sender_end = sender_start + pattern_lower[sender_start:].find(end_word)
                    break
            sender = pattern[sender_start:sender_end].strip()
            conditions.append({
                "field": "from",
                "operator": "contains", 
                "value": sender
            })
        
        # Extract subject patterns
        if "subject" in pattern_lower or "about" in pattern_lower:
            for keyword in ["subject", "about"]:
                if keyword in pattern_lower:
                    start = pattern_lower.find(keyword) + len(keyword)
                    # Skip " with", " containing", etc.
                    while start < len(pattern) and pattern[start] in " :":
                        start += 1
                    
                    end = len(pattern)
                    subject_text = pattern[start:end].strip(' "\'"')
                    if subject_text:
                        conditions.append({
                            "field": "subject",
                            "operator": "contains",
                            "value": subject_text
                        })
                    break
        
        # Step 4: Parse actions
        actions = []
        if "archive" in action_lower:
            actions.append({"type": "archive"})
        
        if label_name:
            actions.append({
                "type": "add_label",
                "label_name": label_name
            })
        
        # Step 5: Create rule definition
        rule_def = {
            "name": f"Auto-organize: {instruction[:50]}...",
            "conditions": conditions,
            "actions": actions,
            "is_enabled": True,
            "condition_conjunction": "AND",
            "description": f"Auto-generated from: {instruction}"
        }
        
        result = {
            "success": True,
            "created_labels": created_labels,
            "rule": rule_def,
            "instruction": instruction
        }
        
        # Step 6: If dry run, show preview
        if dry_run:
            result["preview"] = True
            result["dry_run"] = True
            result["message"] = f"Preview: Would create rule with {len(conditions)} conditions and {len(actions)} actions"
            if label_name:
                result["message"] += f", including label '{label_name}'"
            return result
        
        # Step 7: Create the rule using existing infrastructure
        try:
            from ..services.damien_adapter import DamienAdapter
            adapter = DamienAdapter()
            rule_result = await adapter.add_rule_tool(rule_definition=rule_def)
            
            if rule_result.get("success"):
                result["rule_id"] = rule_result.get("rule_id")
                result["rule_created"] = True
            else:
                result["error"] = f"Failed to create rule: {rule_result.get('error', 'Unknown error')}"
                result["success"] = False
                return result
        except Exception as e:
            result["error"] = f"Failed to create rule: {str(e)}"
            result["success"] = False
            return result
        
        # Step 8: Generate summary
        summary_parts = []
        if created_labels:
            summary_parts.append(f"Created {len(created_labels)} label(s)")
        summary_parts.append("Created rule")
        result["summary"] = ". ".join(summary_parts) + "."
        
        return result
        
    except Exception as e:
        logger.error(f"Error organizing emails: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


async def damien_list_labels_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all Gmail labels.
    
    Args:
        params: Dict (no parameters required)
    
    Returns:
        Dict containing list of labels
    """
    try:
        # Import Gmail API service directly
        from damien_cli.core_api.gmail_api_service import get_authenticated_service
        
        # Get authenticated Gmail service
        service = get_authenticated_service()
        
        # List all labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        # Sort labels: system labels first, then user labels alphabetically
        system_labels = ["INBOX", "SPAM", "TRASH", "UNREAD", "IMPORTANT", "STARRED", 
                        "SENT", "DRAFT", "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", 
                        "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS"]
        
        system = []
        user = []
        
        for label in labels:
            if label['id'] in system_labels:
                system.append(label)
            else:
                user.append(label)
        
        # Sort each group
        system.sort(key=lambda x: x['name'])
        user.sort(key=lambda x: x['name'].lower())
        
        all_labels = system + user
        
        return {
            "success": True,
            "labels": all_labels,
            "count": len(all_labels),
            "system_count": len(system),
            "user_count": len(user)
        }
        
    except Exception as e:
        logger.error(f"Error listing labels: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


def register_organization_tools():
    """Register all organization tools."""
    from ..services.tool_registry import tool_registry, ToolDefinition
    
    logger.info("📁 Registering organization tools...")
    
    # Organization tool handlers
    handlers = {
        "damien_create_label": damien_create_label_handler,
        "damien_delete_label": damien_delete_label_handler,
        "damien_smart_rule": damien_smart_rule_handler,
        "damien_organize_emails": damien_organize_emails_handler,
        "damien_list_labels": damien_list_labels_handler
    }
    
    tools = {
        "damien_create_label": ToolDefinition(
            name="damien_create_label",
            description="Create a new Gmail label",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the label to create"
                    },
                    "color": {
                        "type": "object",
                        "description": "Optional label colors",
                        "properties": {
                            "background": {
                                "type": "string",
                                "description": "Background color hex (e.g., '#42d692')"
                            },
                            "text": {
                                "type": "string",
                                "description": "Text color hex (e.g., '#094228')"
                            }
                        }
                    },
                    "visibility": {
                        "type": "string",
                        "enum": ["show", "showIfUnread", "hide"],
                        "description": "Label visibility setting",
                        "default": "show"
                    }
                },
                "required": ["name"]
            },
            handler="damien_create_label"
        ),
        "damien_delete_label": ToolDefinition(
            name="damien_delete_label",
            description="Delete a Gmail label",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name or ID of the label to delete"
                    }
                },
                "required": ["name"]
            },
            handler="damien_delete_label"
        ),
        "damien_smart_rule": ToolDefinition(
            name="damien_smart_rule",
            description="Create an email rule from natural language instruction",
            input_schema={
                "type": "object",
                "properties": {
                    "instruction": {
                        "type": "string",
                        "description": "Natural language rule description (e.g., 'Archive all receipts from Amazon')"
                    },
                    "preview": {
                        "type": "boolean",
                        "description": "Preview affected emails before creating rule",
                        "default": True
                    },
                    "apply_to_existing": {
                        "type": "boolean",
                        "description": "Apply rule to existing emails",
                        "default": False
                    }
                },
                "required": ["instruction"]
            },
            handler="damien_smart_rule"
        ),
        "damien_organize_emails": ToolDefinition(
            name="damien_organize_emails",
            description="One-stop email organization - creates labels, rules, and applies them",
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Email pattern in natural language (e.g., 'from Shopify about customers')"
                    },
                    "action": {
                        "type": "string",
                        "description": "Action to take (e.g., 'archive with label Shopify Support')"
                    },
                    "apply_to_existing": {
                        "type": "boolean",
                        "description": "Apply to existing emails",
                        "default": True
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Preview mode without making changes",
                        "default": False
                    }
                },
                "required": ["pattern", "action"]
            },
            handler="damien_organize_emails"
        ),
        "damien_list_labels": ToolDefinition(
            name="damien_list_labels",
            description="List all Gmail labels",
            input_schema={
                "type": "object",
                "properties": {}
            },
            handler="damien_list_labels"
        )
    }
    
    for tool_name, tool_def in tools.items():
        try:
            handler = handlers[tool_def.handler_name]
            tool_registry.register_tool(tool_def, handler)
            logger.info(f"Registered organization tool: {tool_name}")
        except Exception as e:
            logger.error(f"Failed to register {tool_name}: {e}")
    
    logger.info(f"✅ Successfully registered {len(tools)} organization tools")