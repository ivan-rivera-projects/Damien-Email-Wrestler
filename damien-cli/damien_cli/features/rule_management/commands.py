import click
import json
import sys
from typing import Optional, List
from pydantic import ValidationError

# Updated import to use the new API service layer
from damien_cli.core_api import rules_api_service
from damien_cli.core_api import gmail_api_service as gmail_api_service_module # To pass module
from damien_cli.core_api.exceptions import (
    RuleNotFoundError,
    RuleStorageError,
    InvalidParameterError,
    DamienError,
    GmailApiError,
)

# Import the shared confirmation utility
from damien_cli.core.cli_utils import _confirm_action

# Models are still used for creating new rules from JSON, if that's how add_rule_cmd works
from .models import RuleModel  # Assuming models.py is still in features/rule_management


@click.group("rules")
@click.pass_context
def rules_group(ctx):
    """Manage filtering rules for Damien."""
    logger = ctx.obj.get("logger")
    # No specific setup needed here for now, as API calls don't need a 'gmail_service' object passed
    # unlike email commands. If rule application needed it, that would be handled in 'apply' cmd.
    if logger:
        logger.debug("Rules command group invoked.")


@rules_group.command("list")
@click.option(
    "--output-format",
    type=click.Choice(["human", "json"]),
    default="human",
    show_default=True,
)
@click.pass_context
def list_rules_cmd(ctx, output_format):
    """Lists all configured rules."""
    logger = ctx.obj.get("logger")
    if logger:
        logger.info("Executing 'rules list'")

    try:
        rules = rules_api_service.load_rules()
    except RuleStorageError as e:
        click.secho(f"Error loading rules: {e}", fg="red")
        if logger:
            logger.error(f"Rule storage error during list: {e}", exc_info=True)
        if output_format == "json":
            sys.stdout.write(
                json.dumps(
                    {
                        "status": "error",
                        "command_executed": "damien rules list",
                        "message": str(e),
                        "data": None,
                        "error_details": {
                            "code": "RULE_STORAGE_ERROR",
                            "details": str(
                                e.original_exception
                                if hasattr(e, "original_exception")
                                else e
                            ),
                        },
                    },
                    indent=2,
                )
                + "\n"
            )
        ctx.exit(1)
        return
    if not rules:
        if output_format == "json":
            # Standard JSON response for success but no data
            response_obj = {
                "status": "success",
                "command_executed": "damien rules list",
                "message": "No rules configured yet.",
                "data": [],
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo("No rules configured yet.")
        return

    if output_format == "json":
        rules_data = [rule.model_dump(mode="json") for rule in rules]
        response_obj = {
            "status": "success",
            "command_executed": "damien rules list",
            "message": f"Successfully listed {len(rules_data)} rules.",
            "data": rules_data,
            "error_details": None,
        }
        sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
    else:  # human format
        click.echo("Configured Rules:")
        for i, rule in enumerate(rules):
            click.echo(
                f"\n--- Rule {i+1} ({'Enabled' if rule.is_enabled else 'Disabled'}) ---"
            )
            click.echo(f" ID: {rule.id}")
            click.echo(f" Name: {rule.name}")
            if rule.description:
                click.echo(f" Description: {rule.description}")
            click.echo(f" Condition Logic: {rule.condition_conjunction}")
            click.echo(" Conditions:") # Removed f-string
            for cond in rule.conditions:
                click.echo(
                    f" - Field: {cond.field}, Operator: {cond.operator}, Value: '{cond.value}'"
                )
            click.echo(" Actions:") # Removed f-string
            for action in rule.actions:
                click.echo(
                    f" - Type: {action.type}"
                    + (f", Label: {action.label_name}" if action.label_name else "")
                )
    if logger:
        logger.info(f"Listed {len(rules)} rules.")


@rules_group.command("add")
@click.option(
    "--rule-json", help="Rule definition as a JSON string or path to a JSON file."
)
@click.option(
    "--output-format",
    type=click.Choice(["human", "json"]),
    default="human",
    show_default=True,
    help="Output format for success/error messages.",
)  # Added for consistency
@click.pass_context
def add_rule_cmd(ctx, rule_json, output_format):
    """Adds a new rule from a JSON definition."""
    logger = ctx.obj.get("logger")
    cmd_name = "damien rules add"

    def _output_error(message: str, code: str, details: Optional[str] = None):
        if output_format == "json":
            err_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "message": message,
                "data": None,
                "error_details": {"code": code, "details": details or message},
            }
            sys.stdout.write(json.dumps(err_obj, indent=2) + "\n")
        else:
            click.secho(message, fg="red")
        ctx.exit(1)

    if not rule_json:
        msg = "Error: --rule-json option is required to define the rule."
        if output_format == "human":
            click.echo(msg)
            example_structure = {
                "name": "Sample Rule Name",
                "description": "Optional description",
                "is_enabled": True,
                "conditions": [
                    {
                        "field": "from",
                        "operator": "contains",
                        "value": "newsletter@example.com",
                    }
                ],
                "condition_conjunction": "AND",
                "actions": [{"type": "trash"}],
            }
            click.echo("\nExample JSON structure for a rule:")
            click.echo(json.dumps(example_structure, indent=2))
        else:  # JSON output
            _output_error(msg, "MISSING_PARAMETER", "--rule-json is required.")
        ctx.exit(1)  # Exit after printing help or JSON error
    try:
        rule_data_dict = json.loads(rule_json)
    except json.JSONDecodeError:
        try:
            with open(rule_json, "r") as f:
                rule_data_dict = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            msg = f"Error: Could not parse --rule-json. Not valid JSON or readable file: {e}"
            if logger:
                logger.error(f"Failed to parse rule_json: {e}", exc_info=True)
            _output_error(msg, "INVALID_INPUT_JSON", str(e))
            # ctx.exit(1) is handled by _output_error

    try:
        new_rule_model = RuleModel(**rule_data_dict)
        if logger:
            logger.info(f"Attempting to add rule: {new_rule_model.name}")

        added_rule = rules_api_service.add_rule(
            new_rule_model
        )  # API now returns the added rule or raises

        msg = f"Rule '{added_rule.name}' (ID: {added_rule.id}) added successfully."
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "message": msg,
                "data": added_rule.model_dump(mode="json"),
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(msg)
        if logger:
            logger.info(f"Rule '{added_rule.name}' added.")
    except ValidationError as e:
        msg = "Error: Rule data is invalid according to the expected schema."
        details_str = (
            json.dumps(e.errors(), indent=2) if hasattr(e, "errors") else str(e)
        )
        if logger:
            logger.error(f"Rule validation failed: {details_str}")
        if output_format == "human":
            click.secho(msg, fg="red")
            click.echo(f"Validation details:\n{details_str}")
        _output_error(msg, "VALIDATION_ERROR", details_str)
    except (RuleStorageError, InvalidParameterError) as e:
        msg = f"Error adding rule: {e}"
        if logger:
            logger.error(msg, exc_info=True)
        _output_error(
            msg,
            e.__class__.__name__.upper(),
            str(e.original_exception if hasattr(e, "original_exception") else e),
        )
    except Exception as e:  # Catch-all for other unexpected errors
        msg = f"An unexpected error occurred while adding the rule: {e}"
        if logger:
            logger.error(msg, exc_info=True)
        _output_error(msg, "UNEXPECTED_ERROR", str(e))


@rules_group.command("apply")
@click.option('--query', '-q', default=None, help="Optional Gmail query to filter emails for rule application.")
@click.option('--rule-ids', default=None, help="Comma-separated list of specific rule IDs or Names to apply. Applies all enabled if not set.")
@click.option('--scan-limit', type=int, default=None, help="Maximum number of emails to scan. Default is no limit.")
@click.option('--date-after', type=str, default=None, help="Process emails after this date (YYYY/MM/DD format).")
@click.option('--date-before', type=str, default=None, help="Process emails before this date (YYYY/MM/DD format).")
@click.option('--all-mail', is_flag=True, help="Process all mail without date restrictions. By default, only processes last 30 days.")
@click.option('--dry-run', is_flag=True, help="Simulate rule application without making actual changes.")
@click.option('--confirm', 'user_must_confirm_apply', is_flag=True, help="Require explicit confirmation before applying actions (if not dry-run).") # Renamed for clarity
@click.option('--yes', '-y', is_flag=True, help="Automatically answer yes to an apply confirmation prompt.") # NEW
@click.option('--output-format', type=click.Choice(['human', 'json']), default='human', show_default=True)
@click.pass_context
def apply_rules_cmd(ctx, query, rule_ids, scan_limit, date_after, date_before, all_mail, dry_run, user_must_confirm_apply, yes, output_format): # Added 'yes', renamed 'confirm'
    """Applies configured (or specified) active rules to emails.
    
    By default, only processes emails from the last 30 days unless --all-mail, --date-after, 
    or --date-before options are provided.
    """
    logger = ctx.obj.get('logger')
    g_service_client = ctx.obj.get('gmail_service') # Raw Google API client from context
    cmd_name = "damien rules apply"
    
    # Build the Gmail query with date filtering if needed
    gmail_query = query or ""
    
    # Apply date restrictions
    if not all_mail:
        # Calculate dates for filtering
        if date_after:
            gmail_query = f"{gmail_query} after:{date_after}" if gmail_query else f"after:{date_after}"
        elif date_before:
            # If only date_before is specified, don't apply default date_after
            pass
        else:
            # Default to last 30 days if no date restrictions specified
            from datetime import datetime, timedelta
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y/%m/%d")
            gmail_query = f"{gmail_query} after:{thirty_days_ago}" if gmail_query else f"after:{thirty_days_ago}"
            
        if date_before:
            gmail_query = f"{gmail_query} before:{date_before}" if gmail_query else f"before:{date_before}"
    
    # Log the final query
    if gmail_query:
        logger.info(f"Using Gmail query: {gmail_query}")
    
    params_provided = {
        "query": query, 
        "rule_ids": rule_ids, 
        "scan_limit": scan_limit, 
        "date_after": date_after,
        "date_before": date_before,
        "all_mail": all_mail,
        "dry_run": dry_run,
        "confirm": user_must_confirm_apply, # Use new name
        "yes": yes # Added yes
    }
    
    if not g_service_client:
        msg = "Damien is not connected to Gmail. Please run `damien login` first."
        if output_format == 'json': 
            sys.stdout.write(json.dumps({"status":"error", "message":msg, "error_details":{"code":"NO_GMAIL_SERVICE"}}, indent=2)+'\n')
        else: 
            click.secho(msg, fg="red")
        ctx.exit(1)
        return
    
    if logger: 
        logger.info(f"Executing '{cmd_name}' with params: {params_provided}")
    
    # If no query/scan limit and processing all mail, warn about large operation
    if not gmail_query and not scan_limit and all_mail:
        warning_msg = "Warning: You are about to apply rules to your entire mailbox with no filtering or limits. This could process a large number of emails."
        click.secho(warning_msg, fg="yellow")
        if not click.confirm("Are you sure you want to continue?", default=False):
            click.echo("Operation aborted.")
            return
    
    if not dry_run and user_must_confirm_apply:
        confirmed, confirm_msg = _confirm_action(
            prompt_message="Are you sure you want to apply rules and potentially modify emails?",
            yes_flag=yes
        )
        if yes and confirmed: # Changed yes_flag to yes
            click.echo(click.style(confirm_msg, fg="green")) # Echo the bypass message from _confirm_action

        if not confirmed:
            if output_format == 'human' and not yes: # Changed yes_flag to yes
                click.echo(confirm_msg) # Echo the abort message from _confirm_action
            elif output_format == 'json': # Always provide JSON abort message if not confirmed
                 sys.stdout.write(json.dumps({
                    "status":"aborted_by_user",
                    "command_executed": cmd_name,
                    "message": confirm_msg, # Use message from _confirm_action
                    "data": {"action_taken": False},
                    "error_details": None
                }, indent=2)+'\n')
            return # Abort the command
    
    rule_ids_list = [rid.strip() for rid in rule_ids.split(',')] if rule_ids else None
    
    try:
        # Call the core API function
        # Pass the actual modules/instances as dependencies
        application_summary = rules_api_service.apply_rules_to_mailbox(
            g_service_client=g_service_client,
            gmail_api_service=gmail_api_service_module, # Pass the imported module
            gmail_query_filter=gmail_query, # Now includes date filtering
            rule_ids_to_apply=rule_ids_list,
            scan_limit=scan_limit,
            dry_run=dry_run
        )
        
        # --- Format Output ---
        if output_format == 'json':
            response_obj = {
                "status": "success", 
                "command_executed": cmd_name, 
                "parameters_provided": params_provided,
                "message": "Rule application process completed.", 
                "data": application_summary, 
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else: # Human output
            click.echo("\n--- Rule Application Summary ---")
            click.echo(f"Dry Run: {'Yes' if application_summary['dry_run'] else 'No'}")
            click.echo(f"Total Emails Scanned: {application_summary['total_emails_scanned']}")
            click.echo(f"Emails Matching Any Rule: {application_summary['emails_matching_any_rule']}")
            
            click.echo("\nActions Planned/Taken:")
            if not application_summary['actions_planned_or_taken']:
                click.echo(" No actions were planned or taken.")
            else:
                for action, items in application_summary['actions_planned_or_taken'].items():
                    count = items if isinstance(items, int) else len(items) # Dry run might have counts, actual run list of IDs
                    click.echo(f" - {action}: {count} email(s)")
            
            click.echo("\nRules Applied Counts (how many times each rule's actions were triggered):")
            if not application_summary['rules_applied_counts']:
                click.echo(" No rules were triggered.")
            else:
                for rule_id_val, count in application_summary['rules_applied_counts'].items():
                    # Try to get rule name for better display
                    # This is a bit inefficient here, ideally summary would include names
                    try:
                        all_loaded_rules = rules_api_service.load_rules() # Could be cached from earlier call
                        rule_name_display = next((r.name for r in all_loaded_rules if r.id == rule_id_val), rule_id_val)
                    except Exception:
                        rule_name_display = rule_id_val
                    click.echo(f" - Rule '{rule_name_display}' (ID: {rule_id_val}): {count} time(s)")
            
            if application_summary['errors']:
                click.secho("\nErrors Encountered During Application:", fg="red")
                for err_item in application_summary['errors']:
                    click.echo(f" - {err_item}")
            
            click.echo("--- End of Summary ---")
        
        if logger: 
            logger.info(f"'{cmd_name}' completed. Summary: {application_summary}")
    
    except (RuleStorageError, GmailApiError, InvalidParameterError, DamienError) as e:
        msg = f"Error during '{cmd_name}': {e.message if hasattr(e, 'message') else str(e)}"
        if output_format == 'json': 
            sys.stdout.write(json.dumps({
                "status":"error", 
                "message":msg, 
                "error_details":{"code":e.__class__.__name__.upper(), "details":str(e)}
            }, indent=2)+'\n')
        else: 
            click.secho(msg, fg="red")
        if logger: 
            logger.error(msg, exc_info=True)
        ctx.exit(1)
    
    except Exception as e:
        msg = f"An unexpected error occurred in '{cmd_name}': {e}"
        if output_format == 'json': 
            sys.stdout.write(json.dumps({
                "status":"error", 
                "message":msg, 
                "error_details":{"code":"UNEXPECTED_ERROR", "details":str(e)}
            }, indent=2)+'\n')
        else: 
            click.secho(msg, fg="red")
        if logger: 
            logger.error(msg, exc_info=True)
        ctx.exit(1)


@rules_group.command("delete")
@click.option(
    "--id", "rule_identifier", required=True, help="ID or Name of the rule to delete."
)
@click.option('--yes', '-y', is_flag=True, help="Automatically answer yes to confirmation prompts.") # NEW
@click.option(
    "--output-format",
    type=click.Choice(["human", "json"]),
    default="human",
    show_default=True,
    help="Output format.",
)
@click.pass_context
def delete_rule_cmd(ctx, rule_identifier, yes, output_format): # Added 'yes'
    """Deletes a rule by its ID or Name."""
    logger = ctx.obj.get("logger")
    cmd_name = "damien rules delete"

    def _output_error(
        message: str, code: str, details: Optional[str] = None
    ):  # Local helper for this command
        if output_format == "json":
            err_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "message": message,
                "data": None,
                "error_details": {"code": code, "details": details or message},
            }
            sys.stdout.write(json.dumps(err_obj, indent=2) + "\n")
        else:
            click.secho(message, fg="red")
        ctx.exit(1)

    if logger:
        logger.info(f"Attempting to delete rule: {rule_identifier}")

    confirmed, confirm_msg = _confirm_action(
        prompt_message=f"Are you sure you want to delete the rule '{rule_identifier}'?",
        yes_flag=yes
    )
    if yes and confirmed: # Changed yes_flag to yes
        click.echo(click.style(confirm_msg, fg="green"))

    if not confirmed:
        if output_format == 'human' and not yes: # Changed yes_flag to yes
            click.echo(confirm_msg)
        elif output_format == "json":
            response_obj = {
                "status": "aborted_by_user",
                "command_executed": cmd_name,
                "message": confirm_msg, # Use message from _confirm_action
                "data": None,
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        return # Abort the command

    try:
        rules_api_service.delete_rule(rule_identifier)  # Returns True or raises
        msg = f"Rule '{rule_identifier}' deleted successfully."
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "message": msg,
                "data": {"deleted_identifier": rule_identifier},
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(msg)
        if logger:
            logger.info(f"Rule '{rule_identifier}' deleted.")
    except RuleNotFoundError as e:
        msg = str(e)  # API service already provides a good message
        if logger:
            logger.warning(msg)  # It's a warning if not found
        if output_format == "json":
            # Technically, command was valid but resource not found. Could be error or specific success.
            # Let's call it an error for the CLI user trying to delete something specific.
            _output_error(msg, "RULE_NOT_FOUND", str(e))
        else:
            click.secho(msg, fg="yellow")  # Yellow for not found
    except RuleStorageError as e:
        msg = f"Error deleting rule: {e}"
        if logger:
            logger.error(msg, exc_info=True)
        _output_error(
            msg,
            "RULE_STORAGE_ERROR",
            str(e.original_exception if hasattr(e, "original_exception") else e),
        )
    except Exception as e:  # Catch-all
        msg = f"An unexpected error occurred: {e}"
        if logger:
            logger.error(msg, exc_info=True)
        _output_error(msg, "UNEXPECTED_ERROR", str(e))
