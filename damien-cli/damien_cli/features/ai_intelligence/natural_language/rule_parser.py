import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from damien_cli.features.rule_management.models import RuleModel, ConditionModel, ActionModel
from ..models import NaturalLanguageRule, ParsedRuleIntent
from ..llm_providers.base import BaseLLMProvider
from .grammar import RULE_GRAMMAR_PROMPT
from .validators import RuleValidator

class NaturalLanguageRuleParser:
    """Converts natural language instructions to Damien rules"""
    
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.validator = RuleValidator()
        
    async def parse_instruction(self, instruction: str) -> Tuple[RuleModel, ParsedRuleIntent]:
        """Parse natural language instruction into a Damien rule"""
        
        # Step 1: Extract intent using LLM
        intent = await self._extract_intent(instruction)
        
        # Step 2: Validate and refine the intent
        validated_intent = self.validator.validate_intent(intent)
        
        # Step 3: Convert to Damien rule model
        rule = self._intent_to_rule(validated_intent, instruction)
        
        return rule, validated_intent
    
    async def _extract_intent(self, instruction: str) -> ParsedRuleIntent:
        """Extract structured intent from natural language"""
        
        prompt = f"""
{RULE_GRAMMAR_PROMPT}

Convert this instruction into a structured email rule:
"{instruction}"

Respond with a JSON object containing:
{{
    "action": "archive|label|trash|mark_read|mark_unread|forward",
    "conditions": [
        {{"field": "from|to|subject|body|label|age_days|has_attachment", 
          "operator": "contains|equals|greater_than|less_than|not_contains",
          "value": "string or number"}}
    ],
    "parameters": {{
        "label_name": "string (if action is label)",
        "forward_to": "email (if action is forward)"
    }},
    "confidence": 0.0-1.0,
    "reasoning": "explanation of interpretation"
}}

Examples:
1. "Archive emails from newsletters older than 30 days"
   -> action: "archive", conditions: [{{"field": "from", "operator": "contains", "value": "newsletter"}}, {{"field": "age_days", "operator": "greater_than", "value": 30}}]

2. "Label emails from my boss as Important"
   -> action: "label", conditions: [{{"field": "from", "operator": "contains", "value": "boss"}}], parameters: {{"label_name": "Important"}}
"""
        
        response = await self.llm.complete(prompt, temperature=0.2)
        
        print(f"Raw LLM response: {response}") # Debug print
        
        try:
            # Parse JSON response
            parsed = json.loads(response)

            print(f"Parsed LLM response: {parsed}") # Debug print

            # Ensure numeric values in conditions are strings for Pydantic model
            processed_conditions = []
            for cond in parsed.get("conditions", []):
                print(f"Processing condition in loop: {cond}") # Debug print
                if cond.get("field") in ["age_days", "size_mb"] and not isinstance(cond.get("value"), str):
                    cond["value"] = str(cond["value"])
                processed_conditions.append(cond)

            # Convert to ParsedRuleIntent
            return ParsedRuleIntent(
                action=parsed["action"],
                conditions=processed_conditions,
                parameters=parsed.get("parameters", {}),
                confidence=parsed.get("confidence", 0.8)
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback: Try to extract intent using regex
            return self._fallback_parse(instruction)
    
    def _fallback_parse(self, instruction: str) -> ParsedRuleIntent:
        """Fallback parser using regex patterns"""
        
        instruction_lower = instruction.lower()
        
        # Detect action
        action = "archive"  # default
        if "label" in instruction_lower:
            action = "label"
        elif "trash" in instruction_lower or "delete" in instruction_lower:
            action = "trash"
        elif "mark as read" in instruction_lower:
            action = "mark_read"
        elif "mark as unread" in instruction_lower:
            action = "mark_unread"
        
        # Extract conditions using patterns
        
        conditions = []
        
        # From condition
        from_match = re.search(r'from\s+(["\']?)([^"\']+)\1', instruction_lower)
        if from_match:
            conditions.append({
                "field": "from",
                "operator": "contains",
                "value": from_match.group(2)
            })
        
        # Age condition
        age_match = re.search(r'older than\s+(\d+)\s+(day|week|month)', instruction_lower)
        if age_match:
            days = int(age_match.group(1))
            unit = age_match.group(2)
            if unit == "week":
                days *= 7
            elif unit == "month":
                days *= 30
            conditions.append({
                "field": "age_days",
                "operator": "greater_than",
                "value": str(days)  # Convert integer to string for Pydantic model
            })
        
        # Subject condition
        subject_match = re.search(r'subject\s+(["\']?)([^"\']+)\1', instruction_lower)
        if subject_match:
            conditions.append({
                "field": "subject",
                "operator": "contains",
                "value": subject_match.group(2)
            })
        
        return ParsedRuleIntent(
            action=action,
            conditions=conditions,
            parameters={},
            confidence=0.6  # Lower confidence for fallback
        )
    
    def _intent_to_rule(self, intent: ParsedRuleIntent, original_instruction: str) -> RuleModel:
        """Convert ParsedRuleIntent to Damien RuleModel"""
        
        # Generate rule name from instruction
        rule_name = self._generate_rule_name(original_instruction)
        
        # Convert conditions
        conditions = []
        for cond in intent.conditions:
            # Map to Damien's condition model, ensuring value is a string
            condition = ConditionModel(
                field=cond["field"],
                operator=cond["operator"],
                value=str(cond["value"]) # Explicitly convert value to string
            )
            conditions.append(condition)
        
        # Convert action
        action_type = intent.action
        action_params = {}
        
        if action_type == "label" and "label_name" in intent.parameters:
            action_params["label_name"] = intent.parameters["label_name"]
        elif action_type == "forward" and "forward_to" in intent.parameters:
            action_params["forward_to"] = intent.parameters["forward_to"]
        
        actions = [ActionModel(type=action_type, **action_params)]
        
        # Create rule
        rule = RuleModel(
            name=rule_name,
            description=f"Generated from: {original_instruction}",
            conditions=conditions,
            condition_conjunction="AND",
            actions=actions,
            is_enabled=True,
            metadata={
                "generated_by": "ai",
                "original_instruction": original_instruction,
                "confidence": intent.confidence
            }
        )
        
        return rule
    
    def _generate_rule_name(self, instruction: str) -> str:
        """Generate a concise rule name from instruction"""
        # Simple approach: take first few significant words
        words = instruction.split()
        significant_words = [w for w in words if len(w) > 3 and w.lower() not in 
                           ["from", "with", "that", "this", "email", "emails"]]
        
        if significant_words:
            return " ".join(significant_words[:3])
        else:
            return f"Rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"