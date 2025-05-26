"""Tests for tool-specific models."""

import pytest
from pydantic import ValidationError
from app.models.tools import (
    ListDraftsParams,
    GetDraftDetailsParams, # Changed from GetDraftDetailsParams
    TrashEmailsParams,
    LabelEmailsParams,
    MarkEmailsParams,
    ApplyRulesParams,
    AddRuleParams,
    DeleteRuleParams,
    DeleteEmailsPermanentlyParams
)


def test_list_emails_params():
    """Test ListDraftsParams model."""
    # Default values
    params = ListDraftsParams()
    assert params.query is None
    assert params.max_results == 10
    assert params.page_token is None
    
    # Custom values
    params = ListDraftsParams(query="is:unread", max_results=20, page_token="next_page")
    assert params.query == "is:unread"
    assert params.max_results == 20
    assert params.page_token == "next_page"
    
    # Validation: max_results must be > 0
    with pytest.raises(ValidationError):
        ListDraftsParams(max_results=0)
    
    # Validation: max_results must be <= 100
    with pytest.raises(ValidationError):
        ListDraftsParams(max_results=101)


def test_get_email_details_params():
    """Test GetDraftDetailsParams model."""
    # Required field
    with pytest.raises(ValidationError):
        GetDraftDetailsParams()  # message_id is required
    
    # Default format
    params = GetDraftDetailsParams(message_id="test_id")
    assert params.message_id == "test_id"
    assert params.format == "full"
    
    # Custom format
    params = GetDraftDetailsParams(message_id="test_id", format="metadata")
    assert params.format == "metadata"


def test_trash_emails_params():
    """Test TrashEmailsParams model."""
    # Required field
    with pytest.raises(ValidationError):
        TrashEmailsParams()  # message_ids is required
    
    # Valid params
    params = TrashEmailsParams(message_ids=["id1", "id2"])
    assert params.message_ids == ["id1", "id2"]
    
    # Empty list should be valid but might not be useful
    params = TrashEmailsParams(message_ids=[])
    assert params.message_ids == []


def test_label_emails_params():
    """Test LabelEmailsParams model."""
    # Required field
    with pytest.raises(ValidationError):
        LabelEmailsParams()  # message_ids is required
    
    # Both add and remove can be None, but this isn't useful in practice
    params = LabelEmailsParams(message_ids=["id1", "id2"])
    assert params.message_ids == ["id1", "id2"]
    assert params.add_label_names is None
    assert params.remove_label_names is None
    
    # Add labels
    params = LabelEmailsParams(message_ids=["id1"], add_label_names=["Label1", "Label2"])
    assert params.add_label_names == ["Label1", "Label2"]
    
    # Remove labels
    params = LabelEmailsParams(message_ids=["id1"], remove_label_names=["Label3"])
    assert params.remove_label_names == ["Label3"]
    
    # Both add and remove
    params = LabelEmailsParams(
        message_ids=["id1"], 
        add_label_names=["Label1"], 
        remove_label_names=["Label2"]
    )
    assert params.add_label_names == ["Label1"]
    assert params.remove_label_names == ["Label2"]


def test_mark_emails_params():
    """Test MarkEmailsParams model."""
    # Required fields
    with pytest.raises(ValidationError):
        MarkEmailsParams()  # Both message_ids and mark_as are required
    
    with pytest.raises(ValidationError):
        MarkEmailsParams(message_ids=["id1"])  # mark_as is required
    
    # Valid values for mark_as
    params = MarkEmailsParams(message_ids=["id1"], mark_as="read")
    assert params.mark_as == "read"
    
    params = MarkEmailsParams(message_ids=["id1"], mark_as="unread")
    assert params.mark_as == "unread"
    
    # Invalid value for mark_as
    with pytest.raises(ValidationError):
        MarkEmailsParams(message_ids=["id1"], mark_as="invalid")


def test_apply_rules_params():
    """Test ApplyRulesParams model."""
    # All fields optional
    params = ApplyRulesParams()
    assert params.gmail_query_filter is None
    assert params.rule_ids_to_apply is None
    assert params.dry_run is False
    assert params.scan_limit is None
    assert params.date_after is None
    assert params.date_before is None
    assert params.all_mail is False
    
    # Custom values
    params = ApplyRulesParams(
        gmail_query_filter="is:unread",
        rule_ids_to_apply=["rule1", "rule2"],
        dry_run=True,
        scan_limit=100,
        date_after="2023/01/01",
        date_before="2023/12/31",
        all_mail=True
    )
    assert params.gmail_query_filter == "is:unread"
    assert params.rule_ids_to_apply == ["rule1", "rule2"]
    assert params.dry_run is True
    assert params.scan_limit == 100
    assert params.date_after == "2023/01/01"
    assert params.date_before == "2023/12/31"
    assert params.all_mail is True


def test_add_rule_params():
    """Test AddRuleParams model."""
    # Required field
    with pytest.raises(ValidationError):
        AddRuleParams()  # rule_definition is required
    
    # Valid params
    rule_def = {
        "name": "Test Rule",
        "description": "A test rule",
        "is_enabled": True,
        "conditions": [{"field": "subject", "operator": "contains", "value": "Test"}],
        "condition_conjunction": "AND",
        "actions": [{"type": "add_label", "parameters": {"label_name": "TestLabel"}}]
    }
    params = AddRuleParams(rule_definition=rule_def)
    # Compare the dictionary representation of the Pydantic model
    assert params.rule_definition.model_dump() == rule_def


def test_delete_rule_params():
    """Test DeleteRuleParams model."""
    # Required field
    with pytest.raises(ValidationError):
        DeleteRuleParams()  # rule_identifier is required
    
    # Valid params
    params = DeleteRuleParams(rule_identifier="rule_id_123")
    assert params.rule_identifier == "rule_id_123"
    
    # Rule identifier can also be a name
    params = DeleteRuleParams(rule_identifier="My Rule Name")
    assert params.rule_identifier == "My Rule Name"


def test_delete_emails_permanently_params():
    """Test DeleteEmailsPermanentlyParams model."""
    # Required field
    with pytest.raises(ValidationError):
        DeleteEmailsPermanentlyParams()  # message_ids is required
    
    # Valid params
    params = DeleteEmailsPermanentlyParams(message_ids=["id1", "id2"])
    assert params.message_ids == ["id1", "id2"]
    
    # Empty list is valid but not useful
    params = DeleteEmailsPermanentlyParams(message_ids=[])
    assert params.message_ids == []