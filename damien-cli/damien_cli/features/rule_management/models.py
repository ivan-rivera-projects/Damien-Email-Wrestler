from typing import List, Literal, Optional # Removed Dict, Union
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)  # Make sure model_validator is imported
import uuid


class ConditionModel(BaseModel):
    field: Literal["from", "subject", "body_snippet", "to", "label"]
    operator: Literal[
        "contains", "not_contains", "equals", "not_equals", "starts_with", "ends_with"
    ]
    value: str


class ActionModel(BaseModel):
    type: Literal["trash", "add_label", "remove_label", "mark_read", "mark_unread"]
    label_name: Optional[str] = None

    @model_validator(mode="after")
    def check_label_name_for_label_actions(
        cls, model_instance
    ):  # Parameter is the model instance
        # Access fields as attributes of the model_instance
        action_type = model_instance.type
        label_name_value = model_instance.label_name  # Defined here before use

        if action_type in ["add_label", "remove_label"]:
            if label_name_value is None or not str(label_name_value).strip():
                raise ValueError(
                    "label_name is required and cannot be empty for add_label or remove_label actions"
                )
        # Ensure label_name is None if not a label action (optional strict validation)
        elif (
            action_type not in ["add_label", "remove_label"]
            and label_name_value is not None
        ):
            raise ValueError(
                f"label_name ('{label_name_value}') should not be provided for action type '{action_type}'"
            )
        return model_instance  # Must return the model instance for @model_validator


class RuleModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    is_enabled: bool = True
    conditions: List[ConditionModel]
    condition_conjunction: Literal["AND", "OR"] = "AND"
    actions: List[ActionModel]
