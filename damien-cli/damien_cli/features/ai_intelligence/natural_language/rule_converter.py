"""
Natural Language Rule Converter - Converts user instructions to rule JSON.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from ..llm_integration.providers import get_llm_provider
from .rule_parser import NaturalLanguageRuleParser
from .grammar import RULE_GRAMMAR_PROMPT
from ....core_api.labels_api_service import get_labels_service
from ....core_api.gmail_api_service import GmailApiError

logger = logging.getLogger(__name__)


class NaturalLanguageRuleConverter:
    """Converts natural language instructions to rule JSON with label creation."""
    
    def __init__(self):
        """Initialize the converter."""
        self.parser = NaturalLanguageRuleParser()
        self.labels_service = get_labels_service()
        
    def parse_instruction(self, 
                         instruction: str,
                         create_labels: bool = True,
                         apply_immediately: bool = False) -> Dict[str, Any]:
        """
        Convert natural language instruction to rule JSON.
        
        Args:
            instruction: Natural language rule description
            create_labels: Whether to create labels if they don't exist
            apply_immediately: Whether to apply the rule to existing emails
            
        Returns:
            Dict containing:
                - rule: The rule definition
                - created_labels: List of labels that were created
                - suggestions: Additional suggestions for the user
        """
        try:
            # First, use the existing parser to get the base rule
            rule_dict = self.parser.parse(instruction)
            
            # Check if any labels need to be created
            created_labels = []
            if create_labels:
                created_labels = self._ensure_labels_exist(rule_dict)
            
            # Generate suggestions based on the instruction
            suggestions = self._generate_suggestions(instruction, rule_dict)
            
            return {
                "success": True,
                "rule": rule_dict,
                "created_labels": created_labels,
                "apply_immediately": apply_immediately,
                "suggestions": suggestions,
                "original_instruction": instruction
            }
            
        except Exception as e:
            logger.error(f"Failed to parse instruction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_instruction": instruction
            }
    
    def _ensure_labels_exist(self, rule_dict: Dict[str, Any]) -> List[str]:
        """
        Check if labels in the rule exist and create them if needed.
        
        Args:
            rule_dict: The parsed rule dictionary
            
        Returns:
            List of labels that were created
        """
        created_labels = []
        
        # Check actions for label operations
        for action in rule_dict.get("actions", []):
            if action["type"] == "add_label":
                label_name = action["label_name"]
                try:
                    result = self.labels_service.create_label(label_name)
                    if result.get("created"):
                        created_labels.append(label_name)
                        logger.info(f"Created label: {label_name}")
                except GmailApiError as e:
                    # Label might already exist, which is fine
                    logger.debug(f"Label '{label_name}' check: {str(e)}")
        
        return created_labels
    
    def _generate_suggestions(self, instruction: str, rule_dict: Dict[str, Any]) -> List[str]:
        """
        Generate helpful suggestions based on the instruction.
        
        Args:
            instruction: Original natural language instruction
            rule_dict: The parsed rule
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Check for common patterns
        instruction_lower = instruction.lower()
        
        # Archive suggestion
        if any(word in instruction_lower for word in ["archive", "remove from inbox"]):
            if not any(action["type"] == "archive" for action in rule_dict.get("actions", [])):
                suggestions.append("Consider adding 'archive' action to remove emails from inbox")
        
        # Label color suggestion
        if "label" in instruction_lower:
            suggestions.append("You can customize label colors in Gmail settings")
        
        # Notification suggestion
        if any(word in instruction_lower for word in ["important", "urgent", "boss", "client"]):
            suggestions.append("Consider using 'mark as important' for priority emails")
        
        # Bulk operations suggestion
        if any(word in instruction_lower for word in ["all", "every", "existing"]):
            suggestions.append("This rule will apply to new emails. Use 'apply to existing' to process current emails")
        
        return suggestions
    
    def create_smart_rule(self,
                         pattern: str,
                         action: str,
                         preview: bool = True) -> Dict[str, Any]:
        """
        Create a rule from simple pattern and action.
        
        Args:
            pattern: Email pattern (e.g., "from Amazon receipts")
            action: Action to take (e.g., "archive with label 'Receipts'")
            preview: Whether to preview before creating
            
        Returns:
            Dict containing rule creation result
        """
        # Combine pattern and action into instruction
        instruction = f"{action} emails {pattern}"
        
        # Parse the instruction
        result = self.parse_instruction(instruction, create_labels=True)
        
        if not result["success"]:
            return result
        
        # Add preview information
        if preview:
            result["preview_mode"] = True
            result["preview_query"] = self._build_gmail_query(result["rule"])
        
        return result
    
    def _build_gmail_query(self, rule_dict: Dict[str, Any]) -> str:
        """
        Build a Gmail search query from rule conditions.
        
        Args:
            rule_dict: The rule dictionary
            
        Returns:
            Gmail search query string
        """
        query_parts = []
        
        for condition in rule_dict.get("conditions", []):
            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]
            
            if field == "from":
                if operator == "contains":
                    query_parts.append(f"from:{value}")
                elif operator == "equals":
                    query_parts.append(f"from:\"{value}\"")
            
            elif field == "to":
                if operator == "contains":
                    query_parts.append(f"to:{value}")
                elif operator == "equals":
                    query_parts.append(f"to:\"{value}\"")
            
            elif field == "subject":
                if operator == "contains":
                    query_parts.append(f"subject:{value}")
                elif operator == "equals":
                    query_parts.append(f"subject:\"{value}\"")
            
            elif field == "body":
                if operator == "contains":
                    query_parts.append(f"\"{value}\"")
            
            elif field == "has_attachment":
                if value:
                    query_parts.append("has:attachment")
            
            elif field == "size":
                if operator == "greater_than":
                    query_parts.append(f"size:{value}")
                elif operator == "less_than":
                    query_parts.append(f"smaller:{value}")
        
        # Join with AND or OR based on conjunction
        conjunction = " OR " if rule_dict.get("condition_conjunction") == "OR" else " "
        return conjunction.join(query_parts)


# Enhanced rule parser that includes label creation
class EnhancedRuleParser(NaturalLanguageRuleParser):
    """Enhanced parser that understands label creation intent."""
    
    def __init__(self):
        """Initialize enhanced parser."""
        super().__init__()
        self.converter = NaturalLanguageRuleConverter()
    
    def parse_with_label_creation(self, instruction: str) -> Dict[str, Any]:
        """
        Parse instruction and handle label creation.
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            Complete rule with label creation handled
        """
        return self.converter.parse_instruction(
            instruction,
            create_labels=True,
            apply_immediately=True
        )