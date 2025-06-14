# damien_cli/core_api/rules_api_service.py
import json
import logging
from typing import List, Dict, Any, Optional, Union  # Added Optional, Union
from pathlib import Path  # For consistency with gmail_api_service
from pydantic import ValidationError  # Keep this import
from collections import defaultdict  # For aggregating actions
from datetime import datetime, timezone  # For age calculations
from damien_cli.core import config as app_config

# Assuming models stay in features for now, adjust if you move them to core_api/models.py
from damien_cli.features.rule_management.models import RuleModel, ConditionModel
from damien_cli.core_api import gmail_api_service as gmail_api_helpers  # Import for helper functions
from .exceptions import (  # Added DamienError, GmailApiError
    RuleNotFoundError,
    RuleStorageError,
    InvalidParameterError,
    DamienError,
    GmailApiError,
)

logger = logging.getLogger(__name__)
RULES_FILE_PATH = Path(app_config.RULES_FILE)  # Ensure RULES_FILE is defined in config


# --- Rule Storage (CRUD) ---
def load_rules() -> List[RuleModel]:
    """Loads rules from the JSON rules file. Raises RuleStorageError on issues."""
    if not RULES_FILE_PATH.exists():
        logger.info(f"Rules file not found at {RULES_FILE_PATH}. Returning empty list.")
        return []
    try:
        with open(RULES_FILE_PATH, "r") as f:
            rules_data_from_file = json.load(f)

        valid_rules: List[RuleModel] = []
        invalid_rule_count = 0
        for i, rule_dict in enumerate(rules_data_from_file):
            try:
                valid_rules.append(RuleModel(**rule_dict))
            except ValidationError as e:
                invalid_rule_count += 1
                logger.warning(
                    f"Skipping invalid rule #{i+1} due to validation error: {e.errors()} in rule data: {rule_dict}"
                )

        if invalid_rule_count > 0:
            logger.warning(
                f"Loaded {len(valid_rules)} valid rules and skipped {invalid_rule_count} invalid rules."
            )
        else:
            logger.info(
                f"Successfully loaded {len(valid_rules)} rules from {RULES_FILE_PATH}."
            )
        return valid_rules

    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding JSON from rules file {RULES_FILE_PATH}: {e}", exc_info=True
        )
        raise RuleStorageError(
            f"Invalid JSON in rules file: {RULES_FILE_PATH}", original_exception=e
        )
    except IOError as e:
        logger.error(
            f"IOError reading rules file {RULES_FILE_PATH}: {e}", exc_info=True
        )
        raise RuleStorageError(
            f"Could not read rules file: {RULES_FILE_PATH}", original_exception=e
        )
    except Exception as e:  # Catch any other unexpected error during loading/validation
        logger.error(f"Unexpected error loading rules: {e}", exc_info=True)
        raise RuleStorageError(
            f"An unexpected error occurred while loading rules: {e}",
            original_exception=e,
        )


def save_rules(rules: List[RuleModel]) -> None:
    """Saves the list of rules to the JSON rules file. Raises RuleStorageError on issues."""
    try:
        logger.debug(f"Attempting to save {len(rules)} rules to {RULES_FILE_PATH}.")
        # Ensure parent directory exists
        RULES_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        rules_data_to_save = [rule.model_dump(mode="json") for rule in rules]

        with open(RULES_FILE_PATH, "w") as f:
            json.dump(rules_data_to_save, f, indent=2)
        logger.info(f"Successfully saved {len(rules)} rules to {RULES_FILE_PATH}.")
    except IOError as e:
        logger.error(f"IOError saving rules file {RULES_FILE_PATH}: {e}", exc_info=True)
        raise RuleStorageError(
            f"Could not write to rules file: {RULES_FILE_PATH}", original_exception=e
        )
    except (
        Exception
    ) as e:  # Catch other potential errors like Pydantic model issues if not properly handled before
        logger.error(
            f"An unexpected error occurred while saving rules: {e}", exc_info=True
        )
        raise RuleStorageError(
            f"An unexpected error occurred while saving rules: {e}",
            original_exception=e,
        )


def add_rule(new_rule_model: RuleModel) -> RuleModel:
    """Adds a new rule and saves. Raises RuleStorageError or InvalidParameterError."""
    if not isinstance(new_rule_model, RuleModel):
        raise InvalidParameterError("Invalid rule object provided to add_rule.")

    rules = load_rules()  # load_rules can raise RuleStorageError
    # Optional: Check for duplicate rule names (IDs are unique by factory)
    for existing_rule in rules:
        if existing_rule.name.lower() == new_rule_model.name.lower():
            err_msg = f"A rule with the name '{new_rule_model.name}' already exists (ID: {existing_rule.id})."
            logger.warning(err_msg)
            raise InvalidParameterError(err_msg)  # Or a specific DuplicateRuleError
    rules.append(new_rule_model)
    save_rules(rules)  # save_rules can raise RuleStorageError
    logger.info(f"Rule '{new_rule_model.name}' (ID: {new_rule_model.id}) added.")
    return new_rule_model


def delete_rule(rule_id_or_name: str) -> bool:
    """Deletes a rule by its ID or name. Raises RuleNotFoundError or RuleStorageError."""
    if not rule_id_or_name:
        raise InvalidParameterError("Rule ID or name must be provided for deletion.")
    rules = load_rules()
    # initial_len = len(rules) # Removed unused variable

    rule_to_delete = None
    for rule in rules:
        if rule.id == rule_id_or_name or rule.name.lower() == rule_id_or_name.lower():
            rule_to_delete = rule
            break

    if not rule_to_delete:
        logger.warning(
            f"Rule with ID or name '{rule_id_or_name}' not found for deletion."
        )
        raise RuleNotFoundError(f"Rule '{rule_id_or_name}' not found.")

    rules.remove(rule_to_delete)  # Remove the found rule object
    save_rules(rules)  # save_rules can raise RuleStorageError
    logger.info(f"Rule '{rule_to_delete.name}' (ID: {rule_to_delete.id}) deleted.")
    return True  # Indicates deletion attempt was processed (save_rules would raise if failed)


# --- Rule Matching Logic (from features/rule_management/service.py) ---
def _email_field_matches_condition(
    email_data: Dict[str, Any], condition: ConditionModel
) -> bool:
    """Checks if a single email field matches a single condition.
    Helper function for internal use.
    """
    # Ensure field value is a string for string operations; handle list for 'label'
    field_name = condition.field
    condition_val = condition.value.lower()
    if field_name == "label":  # Special handling for labels (list of strings)
        email_field_value_list = email_data.get(field_name, [])
        if not isinstance(email_field_value_list, list):
            logger.warning(
                f"Expected list for email field '{field_name}', got {type(email_field_value_list)}. Treating as no match."
            )
            return False

        # For 'label', 'contains' means the label is present in the list
        # 'equals' could mean the list of labels is exactly this one label (less common)
        # Adjust logic based on desired behavior for label matching
        if condition.operator == "contains":
            return any(
                condition_val == label.lower() for label in email_field_value_list
            )
        elif condition.operator == "not_contains":
            return all(
                condition_val != label.lower() for label in email_field_value_list
            )
        else:
            logger.warning(
                f"Operator '{condition.operator}' not fully supported for 'label' field in this basic matcher. Treating as no match."
            )
            return False  # Or implement other operators for lists
    else:  # For other fields, assume string comparison
        email_field_value_str = str(
            email_data.get(field_name, "")
        ).lower()  # Convert to str just in case

        if condition.operator == "contains":
            return condition_val in email_field_value_str
        elif condition.operator == "not_contains":
            return condition_val not in email_field_value_str
        elif condition.operator == "equals":
            return condition_val == email_field_value_str
        elif condition.operator == "not_equals":
            return condition_val != email_field_value_str
        elif condition.operator == "starts_with":
            return email_field_value_str.startswith(condition_val)
        elif condition.operator == "ends_with":
            return email_field_value_str.endswith(condition_val)

        logger.warning(
            f"Unknown operator '{condition.operator}' for field '{field_name}'."
        )
        return False


def does_email_match_rule(email_data: Dict[str, Any], rule: RuleModel) -> bool:
    """
    Checks if the given email data matches a rule based on its conditions and conjunction.
    Assumes email_data keys correspond to ConditionModel.field values.
    """
    if not isinstance(email_data, dict):
        logger.error("email_data must be a dictionary for rule matching.")
        return False  # Or raise InvalidParameterError
    if not isinstance(rule, RuleModel):
        logger.error("rule must be a RuleModel instance for rule matching.")
        return False  # Or raise InvalidParameterError
    if not rule.is_enabled:
        logger.debug(f"Rule '{rule.name}' is disabled, skipping match.")
        return False
    if not rule.conditions:
        logger.debug(
            f"Rule '{rule.name}' has no conditions, evaluating as non-match by default."
        )
        return False
    condition_matches: List[bool] = []
    for cond in rule.conditions:
        match = _email_field_matches_condition(email_data, cond)
        condition_matches.append(match)
        logger.debug(
            f"Rule '{rule.name}', Condition '{cond.field} {cond.operator} {cond.value}', Email Value '{email_data.get(cond.field)}', Match: {match}"
        )
    if not condition_matches:  # Should not happen if rule.conditions is not empty
        return False
    final_match = False
    if rule.condition_conjunction == "AND":
        final_match = all(condition_matches)
    elif rule.condition_conjunction == "OR":
        final_match = any(condition_matches)

    logger.debug(
        f"Rule '{rule.name}' overall match for email: {final_match} (Conjunction: {rule.condition_conjunction}, Individual matches: {condition_matches})"
    )
    return final_match


def translate_rule_to_gmail_query(rule: RuleModel) -> Optional[str]:
    """
    Translates a rule's conditions to a Gmail API query string.
    Only translates conditions that map directly to Gmail's search syntax.
    Returns None if no conditions can be translated.
    
    Gmail query syntax reference:
    - AND is implicit (space between terms)
    - OR needs explicit "OR" keyword
    - NOT is a minus sign (-)
    - Exact phrases use double quotes
    """
    if not rule.conditions:
        return None
    
    translatable_conditions = []
    for condition in rule.conditions:
        query_part = None
        value = condition.value # For convenience
        
        # Handle field-specific translations
        if condition.field == "from":
            if condition.operator == "contains":
                query_part = f"from:{value}"
            elif condition.operator == "equals":
                query_part = f"from:({value})"
            elif condition.operator == "not_contains" or condition.operator == "not_equals":
                query_part = f"-from:{value}"
                
        elif condition.field == "to":
            if condition.operator == "contains":
                query_part = f"to:{value}"
            elif condition.operator == "equals":
                query_part = f"to:({value})"
            elif condition.operator == "not_contains" or condition.operator == "not_equals":
                query_part = f"-to:{value}"
                
        elif condition.field == "subject":
            if condition.operator == "contains":
                if " " in value: query_part = f'subject:("{value}")'
                else: query_part = f"subject:{value}"
            elif condition.operator == "equals":
                query_part = f'subject:("{value}")'
            elif condition.operator == "not_contains" or condition.operator == "not_equals":
                if " " in value: query_part = f'-subject:("{value}")'
                else: query_part = f"-subject:{value}"
        
        elif condition.field == "label":
            if condition.operator == "contains":
                query_part = f"label:{value}"
            elif condition.operator == "not_contains":
                query_part = f"-label:{value}"

        elif condition.field == "date_age":
            # Expects value like "7d", "2m", "1y"
            # Basic validation: ensure value ends with d, m, or y and starts with a digit.
            if value and len(value) > 1 and value[:-1].isdigit() and value[-1] in ['d', 'm', 'y']:
                if condition.operator == "older_than":
                    query_part = f"older_than:{value}"
                elif condition.operator == "newer_than":
                    query_part = f"newer_than:{value}"
            else:
                logger.warning(f"Invalid value '{value}' for date_age condition. Expected format like '7d', '2m'. Skipping translation.")

        elif condition.field == "has_attachment":
            if condition.operator == "is":
                if value.lower() == "true":
                    query_part = "has:attachment"
                elif value.lower() == "false":
                    query_part = "-has:attachment" # Gmail uses minus for negation
            else:
                 logger.warning(f"Unsupported operator '{condition.operator}' for 'has_attachment'. Use 'is'. Skipping translation.")
        
        elif condition.field == "attachment_filename":
            # Gmail uses 'filename:' for this
            if condition.operator == "contains" or condition.operator == "equals":
                 # For multi-word filenames, Gmail often implies AND, quotes might be needed for exact phrase
                if " " in value: query_part = f'filename:("{value}")'
                else: query_part = f"filename:{value}"
            elif condition.operator == "not_contains" or condition.operator == "not_equals":
                if " " in value: query_part = f'-filename:("{value}")'
                else: query_part = f"-filename:{value}"
            # 'starts_with' and 'ends_with' are not directly supported by Gmail's filename search.
            # Could potentially use broader 'contains' or rely on client-side for these.

        elif condition.field == "message_size":
            # Expects value like "1M", "500K", "10000" (bytes)
            # Basic validation: ensure value ends with K, M, or is all digits.
            is_valid_size = False
            if value:
                if value.isdigit():
                    is_valid_size = True
                elif len(value) > 1 and value[:-1].isdigit() and value[-1].upper() in ['K', 'M']:
                    is_valid_size = True
            
            if is_valid_size:
                if condition.operator == "greater_than":
                    query_part = f"larger:{value}"
                elif condition.operator == "less_than":
                    query_part = f"smaller:{value}"
            else:
                logger.warning(f"Invalid value '{value}' for message_size condition. Expected format like '10M', '500K', or bytes. Skipping translation.")

        # Add the query part if translatable
        if query_part:
            translatable_conditions.append(query_part)
    
    # If no translatable conditions, return None
    if not translatable_conditions:
        return None
    
    # Handle conjunction
    if rule.condition_conjunction == "AND":
        # AND is implicit in Gmail query, just join with space
        return " ".join(translatable_conditions)
    elif rule.condition_conjunction == "OR":
        # OR needs explicit keyword
        return " OR ".join(translatable_conditions)
    
    # Default: if conjunction not recognized, return first condition only
    return translatable_conditions[0] if translatable_conditions else None


def needs_full_message_details(rule: RuleModel) -> bool:
    """
    Determines if a rule requires full message details for evaluation.
    Some rules can be evaluated using only server-side queries, without fetching details.
    
    Args:
        rule: The rule to check
        
    Returns:
        True if the rule needs message details, False if it can be evaluated server-side only
    """
    # Check if the rule has any conditions that can't be perfectly translated to Gmail queries
    if not rule.conditions:
        return False
    
    for condition in rule.conditions:
        # If the field isn't one we can translate perfectly, we need details
        translatable_fields = ["from", "to", "subject", "label", "date_age", "has_attachment", "attachment_filename", "message_size"]
        if condition.field not in translatable_fields:
            logger.debug(f"Rule needs details because field '{condition.field}' is not directly translatable to Gmail query.")
            return True
            
        # If the field is one we can translate, but the operator isn't perfectly matched, we might need details.
        # This logic checks if the specific field-operator combo was translated.
        # A more robust way is to check if translate_rule_to_gmail_query for this single condition would yield a result.
        # For now, let's refine based on known supported translations.
        
        if condition.field in ["from", "to", "subject", "attachment_filename"]:
            if condition.operator not in ["contains", "not_contains", "equals", "not_equals"]:
                logger.debug(f"Rule needs details due to operator '{condition.operator}' on field '{condition.field}'.")
                return True
        elif condition.field == "label":
            if condition.operator not in ["contains", "not_contains"]:
                logger.debug(f"Rule needs details due to operator '{condition.operator}' on field 'label'.")
                return True
        elif condition.field == "date_age":
            if condition.operator not in ["older_than", "newer_than"]:
                logger.debug(f"Rule needs details due to operator '{condition.operator}' on field 'date_age'.")
                return True
        elif condition.field == "has_attachment":
            if condition.operator not in ["is"]:
                logger.debug(f"Rule needs details due to operator '{condition.operator}' on field 'has_attachment'.")
                return True
        elif condition.field == "message_size":
            if condition.operator not in ["greater_than", "less_than"]:
                logger.debug(f"Rule needs details due to operator '{condition.operator}' on field 'message_size'.")
                return True
        
        # If a condition like 'body_snippet' is used, it always needs details.
        if condition.field == "body_snippet": # body_snippet was already in ConditionModel
             logger.debug(f"Rule needs details because field 'body_snippet' is used.")
             return True
                
    # If we have multiple conditions with OR conjunction, and any of them are not perfectly translatable
    # individually, or if the OR itself isn't perfectly handled by a combined query, we might need details.
    # Gmail's OR is explicit. If translate_rule_to_gmail_query produces a valid OR query, it's server-side.
    # The current translate_rule_to_gmail_query handles OR by joining parts with " OR ".
    # So, if all individual parts are translatable, the OR query is server-side.
    # The main reason for needing details with OR would be if one of the sub-conditions isn't translatable.
    # The loop above should catch non-translatable sub-conditions.
    if len(rule.conditions) > 1 and rule.condition_conjunction == "OR":
        return True
        
    # If we got here, the rule can be perfectly handled by Gmail's server-side filtering
    return False


def rule_requires_body_content(rule: RuleModel) -> bool:
    """
    Checks if a rule needs body content to be evaluated.
    This determines if we need 'full' format instead of just 'metadata'.
    
    Args:
        rule: The rule to check
        
    Returns:
        True if the rule needs body content, False if 'metadata' format is sufficient
    """
    if not rule.conditions:
        return False
        
    for condition in rule.conditions:
        if condition.field == "body_snippet" or condition.field == "body":
            return True
            
    return False


def transform_gmail_message_to_matchable_data(
    gmail_message_obj: Dict[str, Any], 
    g_service_client: Any, # Raw Google API client
    # Pass the module directly, or specific functions if preferred and manage imports
    gmail_api_service: Any = gmail_api_helpers # Default to imported module
) -> Dict[str, Union[str, List[str], Optional[int]]]:
    """Transforms a raw Gmail message object into a simplified dict for rule matching."""
    if not gmail_message_obj:
        return {}
    
    matchable_data: Dict[str, Union[str, List[str], Optional[int]]] = {}
    payload = gmail_message_obj.get('payload', {})
    headers = payload.get('headers', [])
    
    for header in headers:
        name = header.get('name', '').lower()
        value = header.get('value', '')
        if name == 'from':
            matchable_data['from'] = value
        elif name == 'to':
            matchable_data['to'] = value # Could be comma-separated, might need parsing for multi-value rules
        elif name == 'subject':
            matchable_data['subject'] = value
        # Add Cc, Bcc, Reply-To if needed for rules
        # elif name == 'date':
        #    try:
        #        # Parsing date needs a robust library like 'python-dateutil'
        #        # For now, let's skip age_days, or pass raw date string if rules can handle it.
        #        # from dateutil.parser import parse
        #        # parsed_date = parse(value).astimezone(timezone.utc)
        #        # matchable_data['received_datetime'] = parsed_date
        #        # matchable_data['age_days'] = (datetime.now(timezone.utc) - parsed_date).days
        #        matchable_data['date_string'] = value # Store raw date string
        #    except Exception as e:
        #        logger.warning(f"Could not parse date string '{value}': {e}")
        #        matchable_data['date_string'] = value
    
    matchable_data['body_snippet'] = gmail_message_obj.get('snippet', "")
    
    label_ids_from_api = gmail_message_obj.get('labelIds', [])
    label_names_for_matching: List[str] = []
    if label_ids_from_api:
        for lid in label_ids_from_api:
            # Use the passed gmail_api_service module/instance to call get_label_name_from_id
            name = gmail_api_service.get_label_name_from_id(g_service_client, lid)
            if name:
                label_names_for_matching.append(name)
            else: # If name not found, maybe include the ID itself if rules might use IDs?
                logger.debug(f"Could not resolve label name for ID '{lid}', using ID itself for matching if needed.")
                label_names_for_matching.append(lid) # Or skip
    
    matchable_data['label'] = label_names_for_matching # List of label names (and unresolved IDs)
    # Placeholder for future fields, requiring format='full' and more parsing
    # matchable_data['has_attachment'] = ...
    # matchable_data['attachment_names'] = ...
    
    logger.debug(f"Transformed email ID {gmail_message_obj.get('id')} to matchable data: {matchable_data}")
    return matchable_data


def apply_rules_to_mailbox(
    g_service_client: Any,
    gmail_api_service: Any, # Pass the module/instance
    gmail_query_filter: Optional[str] = None,
    rule_ids_to_apply: Optional[List[str]] = None,
    scan_limit: Optional[int] = None,
    dry_run: bool = False,
    include_detailed_ids: bool = False # New parameter
) -> Dict[str, Any]:
    """
    Applies configured rules to emails in the mailbox.
    Fetches emails, matches against rules, and executes actions (or simulates for dry_run).
    
    Args:
        g_service_client: The authenticated Gmail API service client.
        gmail_api_service: The gmail_api_service module with helper functions.
        gmail_query_filter: Optional Gmail query string to filter emails.
        rule_ids_to_apply: Optional list of rule IDs to apply.
        scan_limit: Optional maximum number of emails to scan.
        dry_run: If True, actions are only simulated.
        include_detailed_ids: If True, the 'actions_planned_or_taken' in the summary
                              will include lists of affected email IDs. Otherwise, it will
                              contain counts. Defaults to False for concise summaries.
        
    Returns:
        A summary dictionary with results and statistics.
    """
    logger.info(
        f"Starting rule application. Dry run: {dry_run}. Query: '{gmail_query_filter}'. "
        f"Specific rules: {rule_ids_to_apply}. Detailed IDs: {include_detailed_ids}"
    )
    
    # --- Initialization of trackers ---
    # _internal_actions_on_ids will always store lists of IDs for potential execution.
    _internal_actions_on_ids: Dict[str, List[str]] = defaultdict(list)
    
    summary: Dict[str, Any] = {
        "total_emails_scanned": 0,
        "emails_matching_any_rule": 0,
        "actions_planned_or_taken": defaultdict(list),  # Will be converted to dict at end
        "rules_applied_counts": defaultdict(int),
        "dry_run": dry_run,
        "include_detailed_ids_in_summary": include_detailed_ids, # For clarity in output
        "errors": [] # List of error dicts
    }
    
    # Track unique emails that matched any rule
    processed_email_ids = set()
    
    # --- 1. Load and Filter Rules ---
    try:
        all_rules = load_rules()
    except RuleStorageError as e:
        logger.error(f"Cannot apply rules: Failed to load rules: {e}", exc_info=True)
        summary["errors"].append({"error_type": "RULE_LOADING_FAILURE", "details": str(e)})
        return summary # Cannot proceed without rules
    
    active_rules_to_process: List[RuleModel] = [r for r in all_rules if r.is_enabled]
    if rule_ids_to_apply:
        specified_rule_names_or_ids_lower = {rid.lower() for rid in rule_ids_to_apply}
        active_rules_to_process = [
            r for r in active_rules_to_process 
            if r.id in rule_ids_to_apply or r.name.lower() in specified_rule_names_or_ids_lower
        ]
        logger.info(f"Applying a subset of {len(active_rules_to_process)} rules based on provided IDs/names.")
    
    if not active_rules_to_process:
        logger.info("No active rules to apply (either none defined, none enabled, or specified rules not found).")
        summary["message"] = "No active rules to apply."
        # Convert defaultdict to regular dict for consistent output
        summary["actions_planned_or_taken"] = dict(summary["actions_planned_or_taken"])
        summary["rules_applied_counts"] = dict(summary["rules_applied_counts"])
        return summary
    
    # --- 2. Process each rule separately with server-side filtering ---
    emails_scanned_count = 0
    MAX_EMAILS_PER_RULE = scan_limit if scan_limit else 1000000  # Use scan_limit if provided, otherwise a large number
    
    for rule in active_rules_to_process:
        # Skip processing more emails if we've hit the scan limit
        if scan_limit and emails_scanned_count >= scan_limit:
            logger.info(f"Reached scan limit of {scan_limit} emails. Stopping rule processing.")
            break
        
        # Try to convert rule conditions to Gmail query for server-side filtering
        rule_query = translate_rule_to_gmail_query(rule)
        
        # Combine with user-provided filter if available
        combined_query = rule_query
        if gmail_query_filter:
            if rule_query:
                combined_query = f"({gmail_query_filter}) AND ({rule_query})"
            else:
                combined_query = gmail_query_filter
        
        logger.info(f"Processing rule '{rule.name}' (ID: {rule.id}) with query: {combined_query}")
        
        # Calculate how many more emails we can process for this rule
        remaining_quota = MAX_EMAILS_PER_RULE - emails_scanned_count
        if remaining_quota <= 0:
            break
        
        # Get candidate emails using server-side filtering
        candidates_for_rule = []
        next_page_token = None
        rule_emails_count = 0
        
        while True:
            # Stop if we've reached the limit for this rule
            if rule_emails_count >= remaining_quota:
                break
                
            batch_size = min(50, remaining_quota - rule_emails_count)  # Use smaller of API batch size or remaining quota
            
            try:
                page = gmail_api_service.list_messages(
                    g_service_client, 
                    query_string=combined_query, 
                    page_token=next_page_token, 
                    max_results=batch_size
                )
            except GmailApiError as e:
                logger.error(f"API error fetching emails for rule '{rule.name}': {e}", exc_info=True)
                summary["errors"].append({
                    "rule_id": rule.id, 
                    "error_type": "EMAIL_FETCH_FAILURE", 
                    "details": str(e)
                })
                break
            
            stubs_on_page = page.get('messages', [])
            if not stubs_on_page:
                break
                
            candidates_for_rule.extend(stubs_on_page)
            rule_emails_count += len(stubs_on_page)
            
            next_page_token = page.get('nextPageToken')
            if not next_page_token:
                break
        
        # Update overall counter
        emails_scanned_count += rule_emails_count
        summary["total_emails_scanned"] = emails_scanned_count
        
        logger.info(f"Found {len(candidates_for_rule)} candidate emails for rule '{rule.name}'")
        
        # Process candidate emails for this rule
        for stub in candidates_for_rule:
            email_id = stub['id']
            
            # Skip if we've already processed this email for this rule (shouldn't happen, but just in case)
            if email_id in processed_email_ids:
                continue
                
            try:
                # Check if we actually need to fetch message details
                needs_details = needs_full_message_details(rule)
                
                # Some rules might be perfectly handled by Gmail's server-side filtering
                # In that case, we can skip fetching details and assume it's a match
                if not needs_details:
                    logger.debug(f"Rule '{rule.name}' can be evaluated purely server-side, assuming match for email ID {email_id}")
                    # Mark as processed
                    processed_email_ids.add(email_id)
                    
                    # Update rule count
                    summary["rules_applied_counts"][rule.id] += 1
                    
                    # Aggregate actions
                    for action_model in rule.actions:
                        action_key = action_model.type
                        if action_model.type in ["add_label", "remove_label"]:
                            if not action_model.label_name:
                                logger.warning(f"Rule '{rule.name}' has action '{action_model.type}' without label_name. Skipping action.")
                                continue
                            action_key = f"{action_model.type}:{action_model.label_name}"
                        
                        _internal_actions_on_ids[action_key].append(email_id) # Always store IDs internally
                        logger.debug(f"Planned action '{action_key}' for email ID {email_id} due to rule '{rule.name}'.")
                    
                    continue  # Skip to next email
                
                # For rules requiring content checks, determine the format needed
                email_format = 'metadata'  # Default format
                if rule_requires_body_content(rule):
                    email_format = 'full'  # Need full content for body matching
                
                # Fetch email details
                try:
                    message_obj = gmail_api_service.get_message_details(
                        g_service_client, 
                        email_id, 
                        format=email_format
                    )
                    
                    if not message_obj:
                        logger.warning(f"Could not retrieve details for email ID {email_id}. Skipping.")
                        summary["errors"].append({
                            "email_id": email_id, 
                            "rule_id": rule.id, 
                            "error_type": "DETAIL_FETCH_NONE", 
                            "details": "API returned no data."
                        })
                        continue
                    
                    # Transform to matchable data
                    matchable_data = transform_gmail_message_to_matchable_data(
                        message_obj,
                        g_service_client,
                        gmail_api_service # Pass the correct module, which is a parameter to apply_rules_to_mailbox
                    )
                    
                    # Double-check with client-side matching (for conditions that couldn't be translated to query)
                    if does_email_match_rule(matchable_data, rule):
                        logger.info(f"Email ID {email_id} MATCHED rule '{rule.name}' (ID: {rule.id})")
                        
                        # Mark as processed
                        processed_email_ids.add(email_id)
                        
                        # Update rule count
                        summary["rules_applied_counts"][rule.id] += 1
                        
                        # Aggregate actions
                        for action_model in rule.actions:
                            action_key = action_model.type
                            if action_model.type in ["add_label", "remove_label"]:
                                if not action_model.label_name:
                                    logger.warning(f"Rule '{rule.name}' has action '{action_model.type}' without label_name. Skipping action.")
                                    continue
                                action_key = f"{action_model.type}:{action_model.label_name}"
                            
                            _internal_actions_on_ids[action_key].append(email_id) # Always store IDs internally
                            logger.debug(f"Planned action '{action_key}' for email ID {email_id} due to rule '{rule.name}'.")
                except GmailApiError as e:
                    logger.error(f"Gmail API error fetching details for email ID {email_id}: {e}", exc_info=True)
                    summary["errors"].append({
                        "email_id": email_id, 
                        "rule_id": rule.id, 
                        "error_type": "DETAIL_FETCH_API_ERROR", 
                        "details": str(e)
                    })
                    continue
            except GmailApiError as e:
                logger.error(f"Gmail API error processing email ID {email_id} for rule '{rule.name}': {e}", exc_info=True)
                summary["errors"].append({
                    "email_id": email_id,
                    "rule_id": rule.id,
                    "error_type": "GMAIL_API_ERROR_PROCESSING", 
                    "details": str(e)
                })
            except Exception as e:
                logger.error(f"Unexpected error processing email ID {email_id} for rule '{rule.name}': {e}", exc_info=True)
                summary["errors"].append({
                    "email_id": email_id,
                    "rule_id": rule.id,
                    "error_type": "UNEXPECTED_EMAIL_PROCESSING_ERROR", 
                    "details": str(e)
                })
    
    # Update summary count of matched emails
    summary["emails_matching_any_rule"] = len(processed_email_ids)
    
    # --- 3. Execute Aggregated Actions ---
    if not dry_run:
        logger.info("Executing aggregated actions...")
        executed_actions_counts: Dict[str, int] = defaultdict(int) # Stores counts of successfully executed actions
        
        for action_key, email_ids_for_action in _internal_actions_on_ids.items():
            if not email_ids_for_action: continue
            
            unique_email_ids_full_list = sorted(list(set(email_ids_for_action)))
            total_ids_for_action = len(unique_email_ids_full_list)
            
            # Gmail API batch operations typically have a limit (e.g., 1000 IDs). Chunking is necessary.
            # Let's use a conservative chunk size, e.g., 500, as batchModify can take multiple label changes.
            # The Gmail API docs state 1000 for batchDelete and batchModify, but individual message.modify is 100/sec.
            # For batchModify, the number of label changes also matters.
            # Let's stick to a safer limit like 500 for batchModify. Trash might also be similar.
            CHUNK_SIZE = 500
            
            action_fully_successful = True # Track if all chunks for this action succeeded
            
            for i in range(0, total_ids_for_action, CHUNK_SIZE):
                chunk_of_ids = unique_email_ids_full_list[i:i + CHUNK_SIZE]
                if not chunk_of_ids: continue

                logger.info(f"Executing action '{action_key}' for chunk {i//CHUNK_SIZE + 1} with {len(chunk_of_ids)} email(s) (total for action: {total_ids_for_action}).")
            
                try:
                    action_type_main = action_key.split(":")[0]
                    chunk_action_result = None # Stores the dict from gmail_api_service calls
                    
                    if action_type_main == "trash":
                        chunk_action_result = gmail_api_service.batch_trash_messages(g_service_client, chunk_of_ids)
                    elif action_type_main == "mark_read":
                        chunk_action_result = gmail_api_service.batch_mark_messages(g_service_client, chunk_of_ids, mark_as='read')
                    elif action_type_main == "mark_unread":
                        chunk_action_result = gmail_api_service.batch_mark_messages(g_service_client, chunk_of_ids, mark_as='unread')
                    elif action_type_main == "add_label":
                        label_name_to_add = action_key.split(":")[1]
                        chunk_action_result = gmail_api_service.batch_modify_message_labels(
                            g_service_client, chunk_of_ids, add_label_names=[label_name_to_add]
                        )
                    elif action_type_main == "remove_label":
                        label_name_to_remove = action_key.split(":")[1]
                        chunk_action_result = gmail_api_service.batch_modify_message_labels(
                            g_service_client, chunk_of_ids, remove_label_names=[label_name_to_remove]
                        )
                    
                    # Check success from the result dict (assuming it has a 'success' key)
                    if chunk_action_result and chunk_action_result.get("success"):
                        executed_actions_counts[action_key] += len(chunk_of_ids) # Increment by chunk size
                        logger.info(f"Successfully executed action '{action_key}' for chunk of {len(chunk_of_ids)} email(s).")
                    else:
                        action_fully_successful = False
                        msg = f"Action '{action_key}' reported failure for chunk of {len(chunk_of_ids)} email(s). Result: {chunk_action_result}"
                        logger.error(msg)
                        summary["errors"].append({"error_type": "ACTION_CHUNK_FAILURE", "action": action_key, "details": msg, "chunk_ids_sample": chunk_of_ids[:5]})
                        # Decide if we should break from processing further chunks for this action_key
                        # For now, let's continue with other chunks but mark the action as not fully successful.
                
                except (GmailApiError, InvalidParameterError, DamienError) as e: # Catch specific errors from gmail_api_service
                    action_fully_successful = False
                    logger.error(f"Error executing action '{action_key}' on chunk: {e}", exc_info=True)
                    summary["errors"].append({"error_type": "ACTION_CHUNK_API_ERROR", "action": action_key, "details": str(e), "chunk_ids_sample": chunk_of_ids[:5]})
                    # Continue to next chunk or next action? For now, continue to next chunk.
                except Exception as e: # Catch any other unexpected error during chunk processing
                    action_fully_successful = False
                    logger.error(f"Unexpected error executing action '{action_key}' on chunk: {e}", exc_info=True)
                    summary["errors"].append({"error_type": "ACTION_CHUNK_UNEXPECTED_ERROR", "action": action_key, "details": str(e), "chunk_ids_sample": chunk_of_ids[:5]})

            # After processing all chunks for an action_key
            if action_fully_successful and total_ids_for_action > 0 :
                 logger.info(f"Action '{action_key}' fully completed for all {total_ids_for_action} email(s).")
            elif not action_fully_successful and total_ids_for_action > 0:
                 logger.warning(f"Action '{action_key}' had errors for some chunks. Total processed for this action: {executed_actions_counts.get(action_key, 0)} out of {total_ids_for_action}.")

        # This block is now part of the loop above, checking chunk_action_result.get("success")
        # if action_success:
        #    executed_actions_counts[action_key] = len(unique_email_ids)
        #    logger.info(f"Successfully executed action '{action_key}' for {len(unique_email_ids)} email(s).")
        
        summary["actions_planned_or_taken"] = executed_actions_counts # For non-dry_run, this shows counts of what was done.
    
    else: # This is the dry_run=True case
        logger.info("Dry run: No actions were executed.")
        if include_detailed_ids:
            summary["actions_planned_or_taken"] = {k: sorted(list(set(v))) for k, v in _internal_actions_on_ids.items()}
        else:
            summary["actions_planned_or_taken"] = {k: len(set(v)) for k, v in _internal_actions_on_ids.items()}
    
    logger.info(f"Rule application finished. Results: {summary}")
    
    # Convert defaultdicts to regular dicts for consistent output
    if isinstance(summary["actions_planned_or_taken"], defaultdict):
        summary["actions_planned_or_taken"] = dict(summary["actions_planned_or_taken"])
    if isinstance(summary["rules_applied_counts"], defaultdict):
        summary["rules_applied_counts"] = dict(summary["rules_applied_counts"])
    
    return summary