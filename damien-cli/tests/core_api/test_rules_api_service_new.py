import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from damien_cli.core_api import rules_api_service
from damien_cli.core_api.exceptions import (
    RuleNotFoundError,
    RuleStorageError,
    InvalidParameterError,
)
from damien_cli.features.rule_management.models import (
    RuleModel,
    ConditionModel,
    ActionModel,
)
from damien_cli.core_api.rules_api_service import transform_gmail_message_to_matchable_data


# --- Test Data Fixtures ---
@pytest.fixture
def sample_rule_dict():
    """Sample rule as a dictionary"""
    return {
        "id": "test-rule-id-1",
        "name": "Test Rule 1",
        "description": "A test rule for unit tests",
        "is_enabled": True,
        "conditions": [
            {"field": "from", "operator": "contains", "value": "test@example.com"},
            {"field": "subject", "operator": "contains", "value": "test subject"},
        ],
        "condition_conjunction": "AND",
        "actions": [{"type": "add_label", "label_name": "TestLabel"}],
    }


@pytest.fixture
def sample_rule_model(sample_rule_dict):
    """Sample rule as a RuleModel object"""
    return RuleModel(**sample_rule_dict)


@pytest.fixture
def sample_rules_list(sample_rule_dict):
    """List with multiple sample rules for testing"""
    rule1 = sample_rule_dict
    rule2 = sample_rule_dict.copy()
    rule2["id"] = "test-rule-id-2"
    rule2["name"] = "Test Rule 2"

    return [rule1, rule2]


# --- Test Environment Setup ---
@pytest.fixture
def mock_rules_file_path(tmp_path):
    """Sets up a temporary rules file path and restores the original after the test"""
    original_path = rules_api_service.RULES_FILE_PATH
    test_path = tmp_path / "test_rules.json"

    # Override the path for testing
    rules_api_service.RULES_FILE_PATH = test_path

    yield test_path  # The test runs here

    # Restore the original path
    rules_api_service.RULES_FILE_PATH = original_path# --- Tests for load_rules ---
def test_load_rules_file_not_exists(mock_rules_file_path):
    """Test load_rules when the rules file doesn't exist"""
    # ARRANGE - ensure file doesn't exist
    if mock_rules_file_path.exists():
        mock_rules_file_path.unlink()

    # ACT
    result = rules_api_service.load_rules()

    # ASSERT
    assert isinstance(result, list)
    assert len(result) == 0  # Empty list returned when file doesn't exist


def test_load_rules_with_valid_data(mock_rules_file_path, sample_rules_list):
    """Test load_rules with a valid JSON file"""
    # ARRANGE - create a valid rules file
    mock_rules_file_path.parent.mkdir(exist_ok=True)
    with open(mock_rules_file_path, "w") as f:
        json.dump(sample_rules_list, f)

    # ACT
    result = rules_api_service.load_rules()

    # ASSERT
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(rule, RuleModel) for rule in result)
    assert result[0].id == "test-rule-id-1"
    assert result[0].name == "Test Rule 1"
    assert result[1].id == "test-rule-id-2"
    assert result[1].name == "Test Rule 2"


def test_load_rules_with_json_decode_error(mock_rules_file_path):
    """Test load_rules with invalid JSON data"""
    # ARRANGE - create an invalid JSON file
    mock_rules_file_path.parent.mkdir(exist_ok=True)
    with open(mock_rules_file_path, "w") as f:
        f.write("This is not valid JSON")

    # ACT & ASSERT
    with pytest.raises(RuleStorageError, match="Invalid JSON in rules file"):
        rules_api_service.load_rules()


def test_load_rules_with_io_error(mock_rules_file_path):
    """Test load_rules with IO error (can't open file)"""
    # ARRANGE
    # Make the (mocked path) file appear to exist so open() is attempted
    mock_rules_file_path.touch()  # Creates an empty file at the temp path

    with patch("builtins.open", side_effect=IOError("Mocked IO Error")):
        # ACT & ASSERT
        with pytest.raises(RuleStorageError, match="Could not read rules file"):
            rules_api_service.load_rules()


def test_load_rules_with_validation_errors(mock_rules_file_path):
    """Test load_rules when some rules have validation errors"""
    # ARRANGE - create a file with some invalid rules
    valid_rule = {
        "id": "valid-rule",
        "name": "Valid Rule",
        "conditions": [{"field": "from", "operator": "contains", "value": "test"}],
        "actions": [{"type": "trash"}],
    }

    invalid_rule = {
        "id": "invalid-rule",
        "name": "Invalid Rule",
        # Missing required fields: conditions and actions
    }

    mock_rules_file_path.parent.mkdir(exist_ok=True)
    with open(mock_rules_file_path, "w") as f:
        json.dump([valid_rule, invalid_rule], f)

    # ACT
    result = rules_api_service.load_rules()

    # ASSERT
    assert len(result) == 1  # Only the valid rule should be loaded
    assert result[0].id == "valid-rule"# --- Tests for save_rules ---
def test_save_rules_success(mock_rules_file_path, sample_rule_model):
    """Test save_rules with valid rule models"""
    # ARRANGE
    rules_to_save = [sample_rule_model]

    # ACT
    rules_api_service.save_rules(rules_to_save)

    # ASSERT
    assert mock_rules_file_path.exists()
    with open(mock_rules_file_path, "r") as f:
        saved_data = json.load(f)

    assert len(saved_data) == 1
    assert saved_data[0]["id"] == sample_rule_model.id
    assert saved_data[0]["name"] == sample_rule_model.name


def test_save_rules_creates_parent_directories(tmp_path):
    """Test save_rules creates parent directories if they don't exist"""
    # ARRANGE
    nested_path = tmp_path / "nested" / "dir" / "structure" / "rules.json"
    rules_api_service.RULES_FILE_PATH = nested_path  # Override for this test

    rule = RuleModel(
        name="Test Rule",
        conditions=[ConditionModel(field="from", operator="contains", value="test")],
        actions=[ActionModel(type="trash")],
    )

    # ACT
    rules_api_service.save_rules([rule])

    # ASSERT
    assert nested_path.exists()

    # Clean up
    rules_api_service.RULES_FILE_PATH = Path(rules_api_service.app_config.RULES_FILE)


def test_save_rules_io_error():
    """Test save_rules with IO error"""
    # ARRANGE - mock open to raise IOError
    with patch("builtins.open", side_effect=IOError("Mocked IO Error")):
        # ACT & ASSERT
        with pytest.raises(RuleStorageError, match="Could not write to rules file"):
            rules_api_service.save_rules(
                [
                    RuleModel(
                        name="Test Rule",
                        conditions=[
                            ConditionModel(
                                field="from", operator="contains", value="test"
                            )
                        ],
                        actions=[ActionModel(type="trash")],
                    )
                ]
            )# --- Tests for add_rule ---
def test_add_rule_success(mock_rules_file_path, sample_rule_model):
    """Test add_rule with a valid rule model"""
    # ARRANGE - ensure rules file doesn't exist initially
    if mock_rules_file_path.exists():
        mock_rules_file_path.unlink()

    # Mock load_rules and save_rules to isolate test
    with patch(
        "damien_cli.core_api.rules_api_service.load_rules", return_value=[]
    ), patch("damien_cli.core_api.rules_api_service.save_rules") as mock_save:

        # ACT
        result = rules_api_service.add_rule(sample_rule_model)

        # ASSERT
        assert result is sample_rule_model  # Should return the added model
        mock_save.assert_called_once()
        # Verify the rule was passed to save_rules
        saved_rules = mock_save.call_args[0][0]
        assert len(saved_rules) == 1
        assert saved_rules[0] is sample_rule_model


def test_add_rule_invalid_parameter(mock_rules_file_path):
    """Test add_rule with an invalid parameter (not a RuleModel)"""
    # ARRANGE - Not necessary, just use a non-RuleModel value

    # ACT & ASSERT
    with pytest.raises(InvalidParameterError, match="Invalid rule object"):
        rules_api_service.add_rule("not a rule model")


def test_add_rule_duplicate_name(mock_rules_file_path, sample_rule_model):
    """Test add_rule with a duplicate rule name"""
    # ARRANGE - Mock load_rules to return a rule with the same name
    existing_rule = RuleModel(
        id="existing-id",
        name=sample_rule_model.name,  # Same name
        conditions=[ConditionModel(field="from", operator="contains", value="test")],
        actions=[ActionModel(type="trash")],
    )

    with patch(
        "damien_cli.core_api.rules_api_service.load_rules", return_value=[existing_rule]
    ):
        # ACT & ASSERT
        with pytest.raises(
            InvalidParameterError, match="rule with the name.*already exists"
        ):
            rules_api_service.add_rule(sample_rule_model)# --- Tests for delete_rule ---
def test_delete_rule_by_id_success(mock_rules_file_path, sample_rule_model):
    """Test delete_rule with a valid rule ID"""
    # ARRANGE
    rules = [sample_rule_model]

    # Mock load_rules and save_rules
    with patch(
        "damien_cli.core_api.rules_api_service.load_rules", return_value=rules
    ), patch("damien_cli.core_api.rules_api_service.save_rules") as mock_save:

        # ACT
        result = rules_api_service.delete_rule(sample_rule_model.id)

        # ASSERT
        assert result is True
        mock_save.assert_called_once()
        # Verify empty list passed to save_rules (rule was removed)
        saved_rules = mock_save.call_args[0][0]
        assert len(saved_rules) == 0


def test_delete_rule_by_name_success(mock_rules_file_path, sample_rule_model):
    """Test delete_rule with a valid rule name"""
    # ARRANGE
    rules = [sample_rule_model]

    # Mock load_rules and save_rules
    with patch(
        "damien_cli.core_api.rules_api_service.load_rules", return_value=rules
    ), patch("damien_cli.core_api.rules_api_service.save_rules") as mock_save:

        # ACT
        result = rules_api_service.delete_rule(sample_rule_model.name)

        # ASSERT
        assert result is True
        mock_save.assert_called_once()
        # Verify empty list passed to save_rules (rule was removed)
        saved_rules = mock_save.call_args[0][0]
        assert len(saved_rules) == 0


def test_delete_rule_not_found(mock_rules_file_path):
    """Test delete_rule with a non-existent rule ID/name"""
    # ARRANGE
    with patch("damien_cli.core_api.rules_api_service.load_rules", return_value=[]):
        # ACT & ASSERT
        with pytest.raises(RuleNotFoundError, match="not found"):
            rules_api_service.delete_rule("non-existent-id")


def test_delete_rule_empty_id():
    """Test delete_rule with an empty ID"""
    # ACT & ASSERT
    with pytest.raises(InvalidParameterError, match="Rule ID or name must be provided"):
        rules_api_service.delete_rule("")# --- Tests for _email_field_matches_condition ---
def test_email_field_matches_condition_string_fields():
    """Test _email_field_matches_condition with string field comparisons"""
    # Create test data for various operators
    email_data = {
        "from": "sender@example.com",
        "subject": "Test Subject Line",
        "body_snippet": "This is a test email content",
    }

    # Test 'contains' operator
    condition = ConditionModel(field="from", operator="contains", value="sender")
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is True
    )

    # Test 'not_contains' operator
    condition = ConditionModel(field="from", operator="not_contains", value="unknown")
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is True
    )

    # Test 'equals' operator
    condition = ConditionModel(
        field="from", operator="equals", value="sender@example.com"
    )
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is True
    )

    # Test 'not_equals' operator
    condition = ConditionModel(
        field="from", operator="not_equals", value="other@example.com"
    )
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is True
    )

    # Test 'starts_with' operator
    condition = ConditionModel(field="subject", operator="starts_with", value="test")
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is True
    )

    # Test 'ends_with' operator
    condition = ConditionModel(
        field="body_snippet", operator="ends_with", value="content"
    )
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is True
    )

    # Test non-matches
    condition = ConditionModel(field="from", operator="contains", value="nonexistent")
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is False
    )
def test_email_field_matches_condition_label_field():
    """Test _email_field_matches_condition with the special 'label' field"""
    # Create test data for label field
    email_data = {"label": ["INBOX", "IMPORTANT", "CustomLabel"]}

    # Test 'contains' operator with labels
    condition = ConditionModel(field="label", operator="contains", value="important")
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is True
    )

    # Test 'not_contains' operator with labels
    condition = ConditionModel(field="label", operator="not_contains", value="SPAM")
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is True
    )

    # Test non-matches with labels
    condition = ConditionModel(field="label", operator="contains", value="SPAM")
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is False
    )

    # Test with non-list label data (which is an error case)
    email_data_invalid = {"label": "not a list"}
    condition = ConditionModel(field="label", operator="contains", value="not")
    assert (
        rules_api_service._email_field_matches_condition(email_data_invalid, condition)
        is False
    )

    # Test with unsupported operator for label field
    condition = ConditionModel(field="label", operator="equals", value="INBOX")
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is False
    )


def test_email_field_matches_condition_field_not_present():
    """Test _email_field_matches_condition when field is not in email_data"""
    # Empty email data
    email_data = {}

    # Test with a field that doesn't exist in the data
    condition = ConditionModel(field="from", operator="contains", value="test")
    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is False
    )


def test_email_field_matches_condition_unknown_operator():
    """Test _email_field_matches_condition with an unknown operator (should never happen due to Pydantic validation)"""
    # This is testing an edge case that shouldn't occur in production due to Pydantic validation
    email_data = {"subject": "Test Subject"}

    # Create a ConditionModel with a broken operator (for test purposes only)
    condition = ConditionModel(field="subject", operator="contains", value="Test")
    # Hack the operator to an invalid value (bypassing Pydantic validation)
    condition.__dict__["operator"] = "unknown_operator"

    assert (
        rules_api_service._email_field_matches_condition(email_data, condition) is False
    )