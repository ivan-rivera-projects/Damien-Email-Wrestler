import pytest
from pydantic import ValidationError
from damien_cli.features.rule_management.models import (
    RuleModel,
    ConditionModel,
    ActionModel,
)


def test_condition_model_valid():
    data = {"field": "from", "operator": "contains", "value": "test@example.com"}
    condition = ConditionModel(**data)
    assert condition.field == "from"
    assert condition.value == "test@example.com"


def test_condition_model_invalid_field():
    with pytest.raises(ValidationError):
        ConditionModel(field="unknown", operator="contains", value="test")


def test_action_model_valid_trash():
    action = ActionModel(type="trash")
    assert action.type == "trash"
    assert action.label_name is None


def test_action_model_valid_add_label():
    action = ActionModel(type="add_label", label_name="MyLabel")
    assert action.type == "add_label"
    assert action.label_name == "MyLabel"


def test_action_model_add_label_missing_label_name():
    with pytest.raises(ValidationError) as excinfo:
        ActionModel(type="add_label")
    assert "label_name is required and cannot be empty" in str(excinfo.value).lower()


def test_rule_model_valid_simple():
    data = {
        "name": "Test Rule",
        "conditions": [{"field": "subject", "operator": "equals", "value": "Hello"}],
        "actions": [{"type": "mark_read"}],
    }
    rule = RuleModel(**data)
    assert rule.name == "Test Rule"
    assert rule.is_enabled is True  # Default
    assert rule.condition_conjunction == "AND"  # Default
    assert rule.id is not None  # Default factory for ID
    assert len(rule.conditions) == 1
    assert len(rule.actions) == 1


def test_rule_model_complex():
    data = {
        "id": "fixed_id_123",
        "name": "Complex Rule",
        "description": "A more complex rule",
        "is_enabled": False,
        "conditions": [
            {"field": "from", "operator": "contains", "value": "spam"},
            {"field": "body_snippet", "operator": "not_contains", "value": "important"},
        ],
        "condition_conjunction": "OR",
        "actions": [
            {"type": "add_label", "label_name": "PossiblySpam"},
            {"type": "trash"},
        ],
    }
    rule = RuleModel(**data)
    assert rule.id == "fixed_id_123"
    assert rule.is_enabled is False
    assert rule.condition_conjunction == "OR"
    assert len(rule.conditions) == 2
    assert len(rule.actions) == 2
