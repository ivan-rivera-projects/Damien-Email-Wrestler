import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
# from pydantic import ValidationError # Removed ValidationError

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
    rules_api_service.RULES_FILE_PATH = original_path


# --- Tests for load_rules ---
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
    assert result[0].id == "valid-rule"


# --- Tests for save_rules ---
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
            )


# --- Tests for add_rule ---
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
            rules_api_service.add_rule(sample_rule_model)


# --- Tests for delete_rule ---
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
        rules_api_service.delete_rule("")


# --- Tests for _email_field_matches_condition ---
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


# --- Tests for does_email_match_rule ---
def test_does_email_match_rule_all_conditions_match():
    """Test does_email_match_rule with all conditions matching (AND conjunction)"""
    # ARRANGE
    email_data = {
        "from": "sender@example.com",
        "subject": "Important Test",
        "body_snippet": "This is important content",
    }

    rule = RuleModel(
        name="Test Rule",
        conditions=[
            ConditionModel(field="from", operator="contains", value="sender"),
            ConditionModel(field="subject", operator="contains", value="Important"),
        ],
        condition_conjunction="AND",
        actions=[ActionModel(type="trash")],
    )

    # ACT
    result = rules_api_service.does_email_match_rule(email_data, rule)

    # ASSERT
    assert result is True


def test_does_email_match_rule_some_conditions_match_and():
    """Test does_email_match_rule with some conditions matching (AND conjunction)"""
    # ARRANGE
    email_data = {
        "from": "sender@example.com",
        "subject": "Regular Test",  # Doesn't contain "Important"
        "body_snippet": "This is important content",
    }

    rule = RuleModel(
        name="Test Rule",
        conditions=[
            ConditionModel(field="from", operator="contains", value="sender"),
            ConditionModel(field="subject", operator="contains", value="Important"),
        ],
        condition_conjunction="AND",
        actions=[ActionModel(type="trash")],
    )

    # ACT
    result = rules_api_service.does_email_match_rule(email_data, rule)

    # ASSERT
    assert result is False  # AND requires all conditions to match


def test_does_email_match_rule_some_conditions_match_or():
    """Test does_email_match_rule with some conditions matching (OR conjunction)"""
    # ARRANGE
    email_data = {
        "from": "sender@example.com",
        "subject": "Regular Test",  # Doesn't contain "Important"
        "body_snippet": "This is important content",
    }

    rule = RuleModel(
        name="Test Rule",
        conditions=[
            ConditionModel(field="from", operator="contains", value="sender"),
            ConditionModel(field="subject", operator="contains", value="Important"),
        ],
        condition_conjunction="OR",
        actions=[ActionModel(type="trash")],
    )

    # ACT
    result = rules_api_service.does_email_match_rule(email_data, rule)

    # ASSERT
    assert result is True  # OR requires at least one condition to match


def test_does_email_match_rule_disabled_rule():
    """Test does_email_match_rule with a disabled rule"""
    # ARRANGE
    email_data = {
        "from": "sender@example.com",
        "subject": "Important Test",
        "body_snippet": "This is important content",
    }

    rule = RuleModel(
        name="Test Rule",
        is_enabled=False,  # Rule is disabled
        conditions=[
            ConditionModel(field="from", operator="contains", value="sender"),
            ConditionModel(field="subject", operator="contains", value="Important"),
        ],
        condition_conjunction="AND",
        actions=[ActionModel(type="trash")],
    )

    # ACT
    result = rules_api_service.does_email_match_rule(email_data, rule)

    # ASSERT
    assert result is False  # Disabled rules never match


def test_does_email_match_rule_no_conditions():
    """Test does_email_match_rule with a rule that has no conditions"""
    # ARRANGE
    email_data = {
        "from": "sender@example.com",
        "subject": "Important Test",
        "body_snippet": "This is important content",
    }

    # Create a rule with empty conditions list
    rule = RuleModel(
        name="Test Rule",
        conditions=[],  # No conditions
        actions=[ActionModel(type="trash")],
    )

    # ACT
    result = rules_api_service.does_email_match_rule(email_data, rule)

    # ASSERT
    assert result is False  # Rules with no conditions never match


def test_does_email_match_rule_invalid_inputs():
    """Test does_email_match_rule with invalid inputs"""
    # Test with non-dict email_data
    rule = RuleModel(
        name="Test Rule",
        conditions=[ConditionModel(field="from", operator="contains", value="test")],
        actions=[ActionModel(type="trash")],
    )

    assert rules_api_service.does_email_match_rule("not a dict", rule) is False

    # Test with non-RuleModel rule
    email_data = {"from": "test@example.com"}
    assert rules_api_service.does_email_match_rule(email_data, "not a rule") is False

# --- Tests for transform_gmail_message_to_matchable_data ---
@pytest.fixture
def mock_g_service_client():
    """Provides a generic MagicMock for the raw Google API client resource."""
    return MagicMock(name="MockRawGServiceClient")

@pytest.fixture
def mock_gmail_api_module():
    """Provides a MagicMock for the gmail_api_service module/instance."""
    # We will configure specific methods like get_label_name_from_id per test
    return MagicMock(name="MockGmailApiServiceModule")

def test_transform_basic_extraction(mock_g_service_client, mock_gmail_api_module):
    """Test basic extraction of headers and data from a Gmail message."""
    gmail_message_obj = {
        'id': 'test_id_1', 
        'snippet': 'This is a test snippet.',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'Sender <sender@example.com>'},
                {'name': 'To', 'value': 'Receiver <receiver@example.com>'},
                {'name': 'SUBJECT', 'value': 'Test Subject Line'}, # Test case insensitivity of header name
                {'name': 'Date', 'value': 'Mon, 20 May 2024 10:00:00 -0700'}
            ]
        },
        'labelIds': ['INBOX', 'UNREAD']
    }
    
    # Mock get_label_name_from_id to just return the ID for system labels
    mock_gmail_api_module.get_label_name_from_id.side_effect = lambda svc, lid: lid.upper() if lid.upper() in ["INBOX", "UNREAD"] else lid
    
    expected_data = {
        'from': 'Sender <sender@example.com>', 
        'to': 'Receiver <receiver@example.com>',
        'subject': 'Test Subject Line', 
        'body_snippet': 'This is a test snippet.',
        'label': ['INBOX', 'UNREAD'] # Assuming get_label_name_from_id returns them as is for system ones
    }
    
    result = transform_gmail_message_to_matchable_data(
        gmail_message_obj, mock_g_service_client, mock_gmail_api_module
    )
    
    assert result.get('from') == expected_data['from']
    assert result.get('to') == expected_data['to']
    assert result.get('subject') == expected_data['subject']
    assert result.get('body_snippet') == expected_data['body_snippet']
    assert sorted(result.get('label', [])) == sorted(expected_data['label'])

def test_transform_missing_fields(mock_g_service_client, mock_gmail_api_module):
    """Test handling of missing fields in the Gmail message."""
    gmail_message_obj = {
        'id': 'test_id_2', 
        'snippet': '',
        'payload': {'headers': [{'name': 'From', 'value': 'onlysender@example.com'}]},
        'labelIds': []
    }
    
    mock_gmail_api_module.get_label_name_from_id.return_value = None # Should not be called if no labelIds
    
    expected_data = {
        'from': 'onlysender@example.com', 
        'to': '', 
        'subject': '', 
        'body_snippet': '', 
        'label': []
    }
    
    result = transform_gmail_message_to_matchable_data(
        gmail_message_obj, mock_g_service_client, mock_gmail_api_module
    )
    
    assert result.get('from') == expected_data['from']
    assert result.get('to', '') == expected_data['to'] # Check default for missing 'to'
    assert result.get('subject', '') == expected_data['subject'] # Check default for missing 'subject'
    assert result.get('body_snippet') == expected_data['body_snippet']
    assert result.get('label') == expected_data['label']
    
    mock_gmail_api_module.get_label_name_from_id.assert_not_called()

def test_transform_user_label_resolution(mock_g_service_client, mock_gmail_api_module):
    """Test resolution of user-defined label IDs to names."""
    gmail_message_obj = {
        'id': 'test_id_3', 
        'snippet': 'Labels test', 
        'payload': {'headers': []},
        'labelIds': ['INBOX', 'Label_123_UserA', 'Label_456_UserB', 'Label_Unknown_789']
    }
    
    def mock_get_name_side_effect(svc, lid): # svc is the g_service_client
        if lid == 'Label_123_UserA': return 'My Custom Label A'
        if lid == 'Label_456_UserB': return 'Project Zeta'
        if lid.upper() == 'INBOX': return 'INBOX'
        if lid == 'Label_Unknown_789': return None # Simulate this ID not resolving to a name
        return lid # Default pass-through for other system labels if any
    
    mock_gmail_api_module.get_label_name_from_id.side_effect = mock_get_name_side_effect
    
    expected_labels = sorted(['INBOX', 'My Custom Label A', 'Project Zeta', 'Label_Unknown_789']) # Assuming unresolved IDs are kept
    
    result = transform_gmail_message_to_matchable_data(
        gmail_message_obj, mock_g_service_client, mock_gmail_api_module
    )
    
    assert mock_gmail_api_module.get_label_name_from_id.call_count == 4
    assert sorted(result.get('label', [])) == expected_labels

# --- Tests for apply_rules_to_mailbox ---
@pytest.fixture
def sample_rule_models(sample_rule_model):
    """Generate multiple rule models for testing."""
    rule1 = sample_rule_model
    rule2 = RuleModel(
        id="test-rule-id-2",
        name="Trash Rule",
        is_enabled=True,
        conditions=[
            ConditionModel(field="from", operator="contains", value="spam@example.com"),
        ],
        condition_conjunction="AND",
        actions=[ActionModel(type="trash")]
    )
    rule3 = RuleModel(
        id="test-rule-id-3",
        name="Disabled Rule",
        is_enabled=False,  # This rule is disabled
        conditions=[
            ConditionModel(field="subject", operator="contains", value="urgent"),
        ],
        condition_conjunction="AND",
        actions=[ActionModel(type="mark_read")]
    )
    return [rule1, rule2, rule3]

@pytest.fixture
def mock_email_data():
    """Sample email data for testing."""
    return {
        'messages': [
            {'id': 'email_1', 'threadId': 'thread_1'},
            {'id': 'email_2', 'threadId': 'thread_2'},
            {'id': 'email_3', 'threadId': 'thread_3'}
        ],
        'nextPageToken': None
    }

@pytest.fixture
def mock_email_details():
    """Sample email details for testing."""
    email1 = {
        'id': 'email_1',
        'threadId': 'thread_1',
        'snippet': 'Test email content',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'test@example.com'},
                {'name': 'To', 'value': 'user@example.com'},
                {'name': 'Subject', 'value': 'Test Subject'}
            ]
        },
        'labelIds': ['INBOX']
    }
    email2 = {
        'id': 'email_2',
        'threadId': 'thread_2',
        'snippet': 'Spam content',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'spam@example.com'},
                {'name': 'To', 'value': 'user@example.com'},
                {'name': 'Subject', 'value': 'Win Money'}
            ]
        },
        'labelIds': ['INBOX']
    }
    email3 = {
        'id': 'email_3',
        'threadId': 'thread_3',
        'snippet': 'Urgent content',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'important@example.com'},
                {'name': 'To', 'value': 'user@example.com'},
                {'name': 'Subject', 'value': 'URGENT: Action Required'}
            ]
        },
        'labelIds': ['INBOX']
    }
    return {
        'email_1': email1,
        'email_2': email2,
        'email_3': email3
    }

def test_apply_rules_to_mailbox_no_rules(mock_g_service_client, mock_gmail_api_module):
    """Test apply_rules_to_mailbox with no active rules."""
    with patch('damien_cli.core_api.rules_api_service.load_rules', return_value=[]) as mock_load_rules:
        result = rules_api_service.apply_rules_to_mailbox(
            mock_g_service_client,
            mock_gmail_api_module
        )
        
        mock_load_rules.assert_called_once()
        assert result["total_emails_scanned"] == 0
        assert result["emails_matching_any_rule"] == 0
        assert not result["actions_planned_or_taken"]
        assert "message" in result and "No active rules to apply" in result["message"]

def test_apply_rules_to_mailbox_dry_run(mock_g_service_client, mock_gmail_api_module, sample_rule_models, mock_email_data, mock_email_details):
    """Test apply_rules_to_mailbox in dry_run mode."""
    # Setup mocks
    with patch('damien_cli.core_api.rules_api_service.load_rules', return_value=sample_rule_models) as mock_load_rules:
        # Mock Gmail API calls
        # mock_gmail_api_module.list_messages.return_value = mock_email_data # Replaced by side_effect
        mock_gmail_api_module.get_message_details.side_effect = lambda svc, email_id, **kwargs: mock_email_details.get(email_id)

        def list_messages_side_effect(svc, query_string, page_token, max_results):
            potential_messages = []
            # Rule 1: id='test-rule-id-1', conditions: from contains test@example.com AND subject contains test subject
            # translate_rule_to_gmail_query for rule1: from:test@example.com subject:("test subject")
            if query_string and "from:test@example.com" in query_string and 'subject:("test subject")' in query_string.lower():
                potential_messages = [me for me in mock_email_data['messages'] if me['id'] == 'email_1']
            # Rule 2: id='test-rule-id-2', conditions: from contains spam@example.com
            # translate_rule_to_gmail_query for rule2: from:spam@example.com
            elif query_string and "from:spam@example.com" in query_string:
                potential_messages = [me for me in mock_email_data['messages'] if me['id'] == 'email_2']
            # Fallback for other queries or default if query_string is None (though not expected for specific rules)
            elif query_string is None: # Should not happen if rules are processed
                 potential_messages = mock_email_data['messages']


            return {'messages': potential_messages[:max_results], 'nextPageToken': None}
        mock_gmail_api_module.list_messages.side_effect = list_messages_side_effect
        
        # Mock transform and does_email_match
        with patch('damien_cli.core_api.rules_api_service.transform_gmail_message_to_matchable_data') as mock_transform:
            with patch('damien_cli.core_api.rules_api_service.does_email_match_rule') as mock_does_match:
                
                # Setup mock behaviors
                def transform_side_effect(msg_obj, *args):
                    msg_id = msg_obj.get('id')
                    if msg_id == 'email_1':
                        return {'from': 'test@example.com', 'to': 'user@example.com', 'subject': 'Test Subject', 'body_snippet': 'Test email content', 'label': ['INBOX']}
                    elif msg_id == 'email_2':
                        return {'from': 'spam@example.com', 'to': 'user@example.com', 'subject': 'Win Money', 'body_snippet': 'Spam content', 'label': ['INBOX']}
                    elif msg_id == 'email_3':
                        return {'from': 'important@example.com', 'to': 'user@example.com', 'subject': 'URGENT: Action Required', 'body_snippet': 'Urgent content', 'label': ['INBOX']}
                    return {}
                
                mock_transform.side_effect = transform_side_effect
                
                # This mock is primarily for rules where needs_details is True.
                # For rules where needs_details is False, the smart list_messages_side_effect is key.
                def does_match_side_effect(email_data, rule):
                    if rule.id == "test-rule-id-1" and email_data.get('from') == 'test@example.com' and "test subject" in email_data.get('subject','').lower():
                        return True
                    elif rule.id == "test-rule-id-2" and email_data.get('from') == 'spam@example.com':
                        return True
                    return False
                
                mock_does_match.side_effect = does_match_side_effect
                
                # Run the function in dry_run mode
                result = rules_api_service.apply_rules_to_mailbox(
                    mock_g_service_client,
                    mock_gmail_api_module,
                    dry_run=True
                )
                
                # Verify batch actions were NOT called
                mock_gmail_api_module.batch_trash_messages.assert_not_called()
                mock_gmail_api_module.batch_modify_message_labels.assert_not_called()
                mock_gmail_api_module.batch_mark_messages.assert_not_called()
                
                # Verify the summary 
                assert result["dry_run"] is True
                assert result["total_emails_scanned"] >= 2 # email_1 for rule1, email_2 for rule2
                assert result["emails_matching_any_rule"] == 2 # email_1 and email_2
                assert result["rules_applied_counts"]["test-rule-id-1"] == 1
                assert result["rules_applied_counts"]["test-rule-id-2"] == 1
                assert "test-rule-id-3" not in result["rules_applied_counts"]  # Disabled rule
                
                # Verify actions_planned_or_taken contains expected actions
                assert result["actions_planned_or_taken"].get("add_label:TestLabel") == 1
                assert result["actions_planned_or_taken"].get("trash") == 1

def test_apply_rules_to_mailbox_with_execution(mock_g_service_client, mock_gmail_api_module, sample_rule_models, mock_email_data, mock_email_details):
    """Test apply_rules_to_mailbox with actual execution (not dry run)."""
    # Setup mocks
    with patch('damien_cli.core_api.rules_api_service.load_rules', return_value=sample_rule_models) as mock_load_rules:
        # Mock Gmail API calls
        # mock_gmail_api_module.list_messages.return_value = mock_email_data # Replaced by side_effect
        mock_gmail_api_module.get_message_details.side_effect = lambda svc, email_id, **kwargs: mock_email_details.get(email_id)

        def list_messages_side_effect(svc, query_string, page_token, max_results):
            potential_messages = []
            if query_string and "from:test@example.com" in query_string and 'subject:("test subject")' in query_string.lower():
                potential_messages = [me for me in mock_email_data['messages'] if me['id'] == 'email_1']
            elif query_string and "from:spam@example.com" in query_string:
                potential_messages = [me for me in mock_email_data['messages'] if me['id'] == 'email_2']
            elif query_string is None:
                 potential_messages = mock_email_data['messages']
            return {'messages': potential_messages[:max_results], 'nextPageToken': None}
        mock_gmail_api_module.list_messages.side_effect = list_messages_side_effect
        
        # Mock batch operations to return True (success)
        mock_gmail_api_module.batch_trash_messages.return_value = True
        mock_gmail_api_module.batch_modify_message_labels.return_value = True
        
        # Mock transform and does_email_match
        with patch('damien_cli.core_api.rules_api_service.transform_gmail_message_to_matchable_data') as mock_transform:
            with patch('damien_cli.core_api.rules_api_service.does_email_match_rule') as mock_does_match:
                
                # Setup mock behaviors (same as dry run test)
                def transform_side_effect(msg_obj, *args):
                    msg_id = msg_obj.get('id')
                    if msg_id == 'email_1':
                        return {'from': 'test@example.com', 'to': 'user@example.com', 'subject': 'Test Subject', 'body_snippet': 'Test email content', 'label': ['INBOX']}
                    elif msg_id == 'email_2':
                        return {'from': 'spam@example.com', 'to': 'user@example.com', 'subject': 'Win Money', 'body_snippet': 'Spam content', 'label': ['INBOX']}
                    elif msg_id == 'email_3':
                        return {'from': 'important@example.com', 'to': 'user@example.com', 'subject': 'URGENT: Action Required', 'body_snippet': 'Urgent content', 'label': ['INBOX']}
                    return {}
                
                mock_transform.side_effect = transform_side_effect
                
                def does_match_side_effect(email_data, rule):
                    if rule.id == "test-rule-id-1" and email_data.get('from') == 'test@example.com' and "test subject" in email_data.get('subject','').lower():
                        return True
                    elif rule.id == "test-rule-id-2" and email_data.get('from') == 'spam@example.com':
                        return True
                    return False
                
                mock_does_match.side_effect = does_match_side_effect
                
                # Run the function with actual execution (not dry_run)
                result = rules_api_service.apply_rules_to_mailbox(
                    mock_g_service_client,
                    mock_gmail_api_module,
                    dry_run=False
                )
                
                # Verify batch actions WERE called
                mock_gmail_api_module.batch_trash_messages.assert_called()
                mock_gmail_api_module.batch_modify_message_labels.assert_called()
                
                # Verify the summary
                assert result["dry_run"] is False
                assert result["total_emails_scanned"] >= 2
                assert result["emails_matching_any_rule"] == 2
                assert result["actions_planned_or_taken"].get("add_label:TestLabel") == 1
                assert result["actions_planned_or_taken"].get("trash") == 1

def test_apply_rules_to_mailbox_with_specific_rules(mock_g_service_client, mock_gmail_api_module, sample_rule_models, mock_email_data, mock_email_details):
    """Test apply_rules_to_mailbox with specific rule_ids_to_apply."""
    # Setup mocks
    with patch('damien_cli.core_api.rules_api_service.load_rules', return_value=sample_rule_models) as mock_load_rules:
        # Mock Gmail API calls
        mock_gmail_api_module.get_message_details.side_effect = lambda svc, email_id, **kwargs: mock_email_details.get(email_id)

        def list_messages_side_effect(svc, query_string, page_token, max_results):
            potential_messages = []
            # Only rule2 (test-rule-id-2) should be processed, its query is "from:spam@example.com"
            if query_string and "from:spam@example.com" in query_string:
                potential_messages = [me for me in mock_email_data['messages'] if me['id'] == 'email_2']
            return {'messages': potential_messages[:max_results], 'nextPageToken': None}
        mock_gmail_api_module.list_messages.side_effect = list_messages_side_effect
        
        # Mock transform and does_email_match (simplified for this test, though may not be hit if needs_details is false)
        with patch('damien_cli.core_api.rules_api_service.transform_gmail_message_to_matchable_data', return_value={'from': 'spam@example.com'}) as mock_transform: # Ensure it can match
            with patch('damien_cli.core_api.rules_api_service.does_email_match_rule', return_value=True) as mock_does_match: # Ensure it can match if called
                
                # Run the function with specific rule_ids_to_apply
                result = rules_api_service.apply_rules_to_mailbox(
                    mock_g_service_client,
                    mock_gmail_api_module,
                    rule_ids_to_apply=["test-rule-id-2"],  # Only apply the trash rule
                    dry_run=True
                )
                
                # Verify only rule2 was used
                mock_load_rules.assert_called_once()
                
                # Check that only test-rule-id-2 was processed and applied
                assert "test-rule-id-2" in result["rules_applied_counts"]
                assert result["rules_applied_counts"]["test-rule-id-2"] == 1 # Should match email_2
                assert "test-rule-id-1" not in result["rules_applied_counts"]
                assert "test-rule-id-3" not in result["rules_applied_counts"]
                assert result["actions_planned_or_taken"].get("trash") == 1

def test_apply_rules_to_mailbox_with_scan_limit(mock_g_service_client, mock_gmail_api_module, sample_rule_models, mock_email_data):
    """Test apply_rules_to_mailbox with scan_limit."""
    # Setup mocks
    with patch('damien_cli.core_api.rules_api_service.load_rules', return_value=sample_rule_models) as mock_load_rules:
        # Mock Gmail API calls
        def list_messages_side_effect(svc, query_string, page_token, max_results):
            potential_messages = []
            # Rule 1 query
            if query_string and "from:test@example.com" in query_string and "subject:\"test subject\"" in query_string.lower():
                potential_messages = [me for me in mock_email_data['messages'] if me['id'] == 'email_1']
            # Rule 2 query
            elif query_string and "from:spam@example.com" in query_string:
                potential_messages = [me for me in mock_email_data['messages'] if me['id'] == 'email_2']
            elif query_string is None: # Default if no query
                 potential_messages = mock_email_data['messages']

            # IMPORTANT: Respect max_results for scan_limit
            return {'messages': potential_messages[:max_results], 'nextPageToken': None}
        mock_gmail_api_module.list_messages.side_effect = list_messages_side_effect
        
        # Run the function with a scan_limit
        result = rules_api_service.apply_rules_to_mailbox(
            mock_g_service_client,
            mock_gmail_api_module,
            scan_limit=1,  # Only scan 1 email
            dry_run=True
        )
        
        # Verify the scan_limit was respected
        assert result["total_emails_scanned"] == 1 # Exactly 1 due to scan_limit

def test_apply_rules_to_mailbox_with_error_handling(mock_g_service_client, mock_gmail_api_module, sample_rule_models):
    """Test error handling in apply_rules_to_mailbox."""
    # Setup mocks
    with patch('damien_cli.core_api.rules_api_service.load_rules', return_value=sample_rule_models) as mock_load_rules:
        # Mock Gmail API calls to raise errors
        from damien_cli.core_api.exceptions import GmailApiError
        mock_gmail_api_module.list_messages.side_effect = GmailApiError("API error")
        
        # Run the function and expect errors to be handled
        result = rules_api_service.apply_rules_to_mailbox(
            mock_g_service_client,
            mock_gmail_api_module,
            dry_run=True
        )
        
        # Verify errors were captured in the result
        assert len(result["errors"]) > 0
        assert any("API error" in str(error) for error in result["errors"])

def test_apply_rules_with_rule_specific_query(mock_g_service_client, mock_gmail_api_module, sample_rule_models):
    """Test apply_rules_to_mailbox with rule-specific queries."""
    # Setup mocks
    with patch('damien_cli.core_api.rules_api_service.load_rules', return_value=sample_rule_models) as mock_load_rules:
        # Mock translate_rule_to_gmail_query
        with patch('damien_cli.core_api.rules_api_service.translate_rule_to_gmail_query') as mock_translate:
            mock_translate.return_value = "from:test@example.com"  # Simulate a translated query
            
            # Mock Gmail API calls
            mock_gmail_api_module.list_messages.return_value = {'messages': [], 'nextPageToken': None}
            
            # Run the function
            result = rules_api_service.apply_rules_to_mailbox(
                mock_g_service_client,
                mock_gmail_api_module,
                gmail_query_filter="is:unread",  # User provided query
                dry_run=True
            )
            
            # Verify the Gmail query was combined with rule-specific query
            mock_translate.assert_called()
            assert mock_gmail_api_module.list_messages.called
            
            # Check that the combined query contains both the user query and rule query
            combined_query = mock_gmail_api_module.list_messages.call_args[1]['query_string']
            assert 'is:unread' in combined_query
            assert 'from:test@example.com' in combined_query
