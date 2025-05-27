from typing import Dict, List, Optional
from ..models import ParsedRuleIntent
from damien_cli.core_api.exceptions import InvalidParameterError

class RuleValidator:
    """Validates and refines parsed rule intents"""
    
    # Valid field-operator combinations
    VALID_COMBINATIONS = {
        "from": ["contains", "equals", "not_contains", "matches_regex"],
        "to": ["contains", "equals", "not_contains"],
        "subject": ["contains", "equals", "not_contains", "matches_regex"],
        "body": ["contains", "not_contains", "matches_regex"],
        "label": ["equals", "not_equals"],
        "age_days": ["greater_than", "less_than", "equals"],
        "has_attachment": ["equals"],
        "size_mb": ["greater_than", "less_than"]
    }
    
    def validate_intent(self, intent: ParsedRuleIntent) -> ParsedRuleIntent:
        """Validate and potentially fix parsed intent"""
        
        # Validate action
        valid_actions = ["archive", "label", "trash", "mark_read", "mark_unread", "forward"]
        if intent.action not in valid_actions:
            raise InvalidParameterError(f"Invalid action: {intent.action}")
        
        # Validate and fix conditions
        validated_conditions = []
        for condition in intent.conditions:
            validated_condition = self._validate_condition(condition)
            if validated_condition:
                validated_conditions.append(validated_condition)
        
        intent.conditions = validated_conditions
        
        # Validate action-specific parameters
        if intent.action == "label" and "label_name" not in intent.parameters:
            raise InvalidParameterError("Label action requires 'label_name' parameter")
        
        if intent.action == "forward" and "forward_to" not in intent.parameters:
            raise InvalidParameterError("Forward action requires 'forward_to' parameter")
        
        return intent
    
    def _validate_condition(self, condition: Dict) -> Optional[Dict]:
        """Validate a single condition"""
        
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        print(f"Validating condition: field={field}, operator={operator}, value={value}") # Debug print
        
        # Check required fields
        if not all([field, operator, value is not None]):
            print(f"Validation failed: Missing required field, operator, or value is None") # Debug print
            return None
        
        # Validate field-operator combination
        if field not in self.VALID_COMBINATIONS:
            return None
        
        if operator not in self.VALID_COMBINATIONS[field]:
            # Try to fix common mistakes
            if operator == "is" and field in ["has_attachment"]:
                operator = "equals"
            elif operator == ">" and field in ["age_days", "size_mb"]:
                operator = "greater_than"
            elif operator == "<" and field in ["age_days", "size_mb"]:
                operator = "less_than"
            else:
                return None
        
        # Type conversion
        if field in ["age_days", "size_mb"]:
            try:
                value = float(value)
            except (ValueError, TypeError):
                return None
        
        if field == "has_attachment":
            value = str(value).lower() in ["true", "yes", "1"]
        
        return {
            "field": field,
            "operator": operator,
            "value": value
        }