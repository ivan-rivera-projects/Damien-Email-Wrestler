import click
import json
import sys
import base64

# Imports for the new API service layer
from damien_cli.core_api import gmail_api_service
from damien_cli.core_api.exceptions import (
    GmailApiError,
    InvalidParameterError,
    DamienError,
)

# Import the shared confirmation utility
from damien_cli.core.cli_utils import _confirm_action

# (SCOPES import might not be needed here anymore if not directly used)
# from damien_cli.core.config import SCOPES


# --- Helper Functions (These can remain as they are CLI/presentation helpers) ---
def _extract_headers(message_payload: dict) -> dict:
    headers_list = message_payload.get("headers", [])
    subject = next(
        (h["value"] for h in headers_list if h["name"].lower() == "subject"), "N/A"
    )
    sender = next(
        (h["value"] for h in headers_list if h["name"].lower() == "from"), "N/A"
    )
    date = next(
        (h["value"] for h in headers_list if h["name"].lower() == "date"), "N/A"
    )
    return {"subject": subject, "from": sender, "date": date}


def _parse_ids(ids_str: str) -> list:
    if not ids_str:
        return []
    return [id_val.strip() for id_val in ids_str.split(",") if id_val.strip()]


# Removed local _confirm_action, will use the one from core.cli_utils


# --- Click Command Group ---
@click.group("emails")
@click.pass_context
def emails_group(ctx):
    """Manage emails in your Gmail account."""
    logger = ctx.obj.get("logger")
    if not ctx.obj.get(
        "gmail_service"
    ):  # This 'gmail_service' is the raw Google API client resource
        if logger:
            logger.error(
                "emails_group: Gmail service client not found in context. This should have been set by 'damien login'."
            )
        click.secho(
            "Damien is not connected to Gmail. Please run `damien login` first.",
            fg="yellow",
        )
        ctx.abort()  # Stops further execution of this command group
    elif logger:
        logger.debug("emails_group: Raw Gmail service client found in context.")


# --- CLI Command Functions ---
@emails_group.command("list")
@click.option("--query", "-q", default=None, help="Gmail search query.")
@click.option(
    "--max-results", "-m", type=int, default=10, show_default=True, help="Max messages."
)
@click.option("--page-token", "-p", default=None, help="Page token for pagination.")
@click.option(
    "--output-format",
    type=click.Choice(["human", "json"]),
    default="human",
    show_default=True,
)
@click.pass_context
def list_cmd(ctx, query, max_results, page_token, output_format):
    """Lists emails matching criteria."""
    logger = ctx.obj.get("logger")
    g_service_client = ctx.obj.get("gmail_service")  # Raw Google API client
    cmd_name = "damien emails list"
    params_provided = {
        "query": query,
        "max_results": max_results,
        "page_token": page_token,
    }
    if logger:
        logger.info(f"Executing '{cmd_name}' with params: {params_provided}")
    try:
        api_result_data = gmail_api_service.list_messages(
            g_service_client,
            query_string=query,
            max_results=max_results,
            page_token=page_token,
        )
        # api_result_data = {'messages': [], 'nextPageToken': None}
        messages_stubs = api_result_data.get("messages", [])
        next_page = api_result_data.get("nextPageToken")

        human_msg = f"Successfully listed {len(messages_stubs)} email(s)."
        if not messages_stubs:
            human_msg = (
                "No emails found matching your criteria."
                if query
                else "No emails found."
            )
        if output_format == "json":
            detailed_messages_for_json = []
            if messages_stubs:
                # For JSON list, fetching details for each can be slow but more informative.
                # This matches previous behavior. Consider if stubs are enough for some use cases.
                for stub in messages_stubs:
                    try:
                        msg_detail = gmail_api_service.get_message_details(
                            g_service_client, stub["id"], email_format="metadata"
                        )
                        headers = _extract_headers(msg_detail.get("payload", {}))
                        detailed_messages_for_json.append(
                            {
                                "id": msg_detail["id"],
                                "threadId": msg_detail["threadId"],
                                "subject": headers["subject"],
                                "from": headers["from"],
                                "date": headers["date"],
                                "snippet": msg_detail.get("snippet", ""),
                            }
                        )
                    except (
                        GmailApiError
                    ) as detail_err:  # Catch error for individual detail fetch
                        if logger:
                            logger.warning(
                                f"Error fetching details for {stub['id']} for JSON list: {detail_err}"
                            )
                        detailed_messages_for_json.append(
                            {
                                "id": stub["id"],
                                "error": f"Could not fetch details: {detail_err.message}",
                            }
                        )

            data_payload = {
                "count_returned": len(messages_stubs),
                "next_page_token": next_page,
                "messages": detailed_messages_for_json,
            }
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_msg,
                "data": data_payload,
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:  # human format
            if not messages_stubs:
                click.echo(human_msg)
            else:
                click.echo(f"\nDamien found {len(messages_stubs)} email(s):")
                for stub in messages_stubs:
                    try:
                        msg_detail = gmail_api_service.get_message_details(
                            g_service_client, stub["id"], email_format="metadata"
                        )
                        headers = _extract_headers(msg_detail.get("payload", {}))
                        click.echo("-" * 30)
                        click.echo(f"  ID: {msg_detail['id']}")
                        click.echo(f"  From: {headers['from']}")
                        click.echo(f"  Subject: {headers['subject']}")
                        # ... (other human output)
                    except GmailApiError as detail_err:
                        click.echo("-" * 30)
                        click.echo(
                            f"  ID: {stub['id']} (Error fetching details: {detail_err.message})"
                        )
                if next_page:
                    click.echo(f'\nTo see more, use --page-token "{next_page}"')
        if logger:
            logger.info(f"'{cmd_name}' command finished successfully.")
    except (InvalidParameterError, GmailApiError, DamienError) as e:
        msg = f"Error during '{cmd_name}': {e}"
        error_code = e.__class__.__name__.upper().replace(
            "ERROR", "_ERROR"
        )  # e.g., GMAIL_API_ERROR
        if hasattr(e, "message") and e.message:
            msg = e.message  # Use custom exception message if available

        if logger:
            logger.error(f"{error_code} in '{cmd_name}': {e}", exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": error_code,
                    "details": str(
                        e.original_exception if hasattr(e, "original_exception") else e
                    ),
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
    except Exception as e:  # Catch-all
        msg = f"An unexpected error occurred in '{cmd_name}': {e}"
        if logger:
            logger.error(msg, exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)},
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)


@emails_group.command("get")
@click.option(
    "--id", "message_id", required=True, help="The ID of the email to retrieve."
)
@click.option(
    "--format",
    "email_format_option",
    type=click.Choice(["metadata", "full", "raw"]),
    default="full",
    show_default=True,
    help="Format of email details.",
)  # Renamed to avoid clash
@click.option(
    "--output-format",
    type=click.Choice(["human", "json"]),
    default="human",
    show_default=True,
)
@click.pass_context
def get_cmd(
    ctx, message_id, email_format_option, output_format
):  # Renamed email_format to email_format_option
    """Gets and displays details of a specific email."""
    logger = ctx.obj.get("logger")
    g_service_client = ctx.obj.get("gmail_service")
    cmd_name = "damien emails get"
    params_provided = {"id": message_id, "format": email_format_option}
    if logger:
        logger.info(
            f"Executing '{cmd_name}' for ID='{message_id}', format='{email_format_option}'"
        )
    try:
        message_data = gmail_api_service.get_message_details(
            g_service_client, message_id, email_format=email_format_option
        )
        human_msg = f"Successfully retrieved details for email ID {message_id}."
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_msg,
                "data": message_data,
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:  # human format
            click.echo(f"\n--- Details for Email ID: {message_data['id']} ---")
            # ... (your existing detailed human output logic for message_data)
            click.echo(f"Thread ID: {message_data['threadId']}")
            click.echo(f"Snippet: {message_data['snippet']}")
            payload = message_data.get("payload", {})
            headers_data = _extract_headers(payload)
            click.echo(f"From: {headers_data['from']}")
            click.echo(f"Subject: {headers_data['subject']}")
            click.echo(f"Date: {headers_data['date']}")
            if email_format_option == "full" or email_format_option == "raw":
                # ... (body display logic using base64) ...
                parts = payload.get("parts", [])
                body_content = "Body content not easily displayed in this simple view. Try JSON output or a dedicated email viewer."
                if payload.get("body") and payload["body"].get("data"):
                    body_content = base64.urlsafe_b64decode(
                        payload["body"]["data"]
                    ).decode("utf-8", errors="replace")
                elif parts:
                    for part in parts:
                        if (
                            part.get("mimeType") == "text/plain"
                            and part.get("body")
                            and part["body"].get("data")
                        ):
                            body_content = base64.urlsafe_b64decode(
                                part["body"]["data"]
                            ).decode("utf-8", errors="replace")
                            break
                click.echo("\n--- Body (Plain Text Sample) ---")
                click.echo(
                    body_content[:500] + "..."
                    if len(body_content) > 500
                    else body_content
                )
            click.echo("-" * 30)
        if logger:
            logger.info(f"'{cmd_name}' for ID {message_id} finished.")
    except (InvalidParameterError, GmailApiError, DamienError) as e:
        msg = f"Error during '{cmd_name}': {e.message if hasattr(e, 'message') else str(e)}"
        error_code = e.__class__.__name__.upper().replace("ERROR", "_ERROR")
        if logger:
            logger.error(f"{error_code} in '{cmd_name}': {e}", exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": error_code,
                    "details": str(
                        e.original_exception if hasattr(e, "original_exception") else e
                    ),
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
    except Exception as e:  # Catch-all
        # Similar error handling as above for unexpected errors
        msg = f"An unexpected error in '{cmd_name}': {e}"
        if logger:
            logger.error(msg, exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)},
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)


# --- Email Write Commands (Trash, Delete, Label, Mark) ---
# These will follow a similar refactoring pattern:
# 1. Get g_service_client from ctx.obj.
# 2. Perform CLI-specific logic (parse IDs, dry-run check, confirmations).
# 3. Call the corresponding gmail_api_service function.
# 4. Wrap API call in try/except to handle custom exceptions.
# 5. Format human or JSON output based on success/failure from API.
@emails_group.command("trash")
@click.option(
    "--ids",
    "message_ids_str",
    required=True,
    help="Comma-separated list of email IDs to trash.",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without actually doing it."
)
@click.option('--yes', '-y', is_flag=True, help="Automatically answer yes to confirmation prompts.")
@click.option(
    "--output-format",
    type=click.Choice(["human", "json"]),
    default="human",
    show_default=True,
)
@click.pass_context
def trash_cmd(ctx, message_ids_str, dry_run, yes, output_format): # Added 'yes'
    logger = ctx.obj.get("logger")
    g_service_client = ctx.obj.get("gmail_service")
    cmd_name = "damien emails trash"
    message_ids = _parse_ids(message_ids_str)
    params_provided = {"ids": message_ids, "dry_run": dry_run, "yes": yes} # Added 'yes' to params
    if not message_ids:
        msg = "No message IDs provided to trash."
        if logger:
            logger.warning("Trash command called with no message IDs.")
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": "MISSING_PARAMETER",
                    "details": "--ids option requires at least one valid message ID.",
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(msg)
        ctx.exit(1)
        return

    if logger:
        logger.info(
            f"Executing '{cmd_name}' for IDs: {message_ids} (Dry run: {dry_run})"
        )

    human_dry_run_msg = f"DRY RUN: {len(message_ids)} email(s) would be moved to Trash. No actual changes made."
    human_success_msg = f"Successfully moved {len(message_ids)} email(s) to Trash."
    if dry_run:
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_dry_run_msg,
                "data": {
                    "action_taken": False,
                    "processed_ids_count": len(message_ids),
                },
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(human_dry_run_msg)
        if logger:
            logger.info("Dry run: Trash operation completed.")
        return

    confirmed, confirm_msg = _confirm_action(
        prompt_message=f"Are you sure you want to move these {len(message_ids)} email(s) to Trash?",
        yes_flag=yes
    )
    if yes and confirmed : # Changed yes_flag to yes
        click.echo(click.style(confirm_msg, fg="green"))

    if not confirmed:
        if output_format == "human" and not yes: # Changed yes_flag to yes
            click.echo(confirm_msg)
        elif output_format == "json": # Always provide JSON abort message if not confirmed
            response_obj = {
                "status": "aborted_by_user",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": {"action_taken": False},
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(msg)
        if logger:
            logger.info("User aborted trash operation.")
        return

    try:
        gmail_api_service.batch_trash_messages(g_service_client, message_ids)
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_success_msg,
                "data": {"action_taken": True, "processed_ids_count": len(message_ids)},
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(human_success_msg)
        if logger:
            logger.info(f"Successfully trashed {len(message_ids)} emails.")
    except (InvalidParameterError, GmailApiError, DamienError) as e:
        msg = f"Error during '{cmd_name}': {e.message if hasattr(e, 'message') else str(e)}"
        error_code = e.__class__.__name__.upper().replace("ERROR", "_ERROR")
        if logger:
            logger.error(f"{error_code} in '{cmd_name}': {e}", exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": error_code,
                    "details": str(
                        e.original_exception if hasattr(e, "original_exception") else e
                    ),
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
    except Exception as e:
        msg = f"Unexpected error in '{cmd_name}': {e}"
        if logger:
            logger.error(msg, exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)},
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)


@emails_group.command("delete")
@click.option(
    "--ids",
    "message_ids_str",
    required=True,
    help="Comma-separated IDs to PERMANENTLY DELETE.",
)
@click.option("--dry-run", is_flag=True, help="Show what would be done.")
@click.option('--yes', '-y', is_flag=True, help="Automatically answer yes to ALL confirmation prompts.")
@click.option(
    "--output-format",
    type=click.Choice(["human", "json"]),
    default="human",
    show_default=True,
)
@click.pass_context
def delete_permanently_cmd(ctx, message_ids_str, dry_run, yes, output_format): # Added 'yes'
    """PERMANENTLY deletes specified emails. This action is IRREVERSIBLE."""
    logger = ctx.obj.get("logger")
    g_service_client = ctx.obj.get("gmail_service")
    cmd_name = "damien emails delete"
    message_ids = _parse_ids(message_ids_str)
    params_provided = {"ids": message_ids, "dry_run": dry_run, "yes": yes} # Added 'yes' to params

    if not message_ids:
        msg = "No message IDs provided to delete permanently."
        if logger:
            logger.warning("Delete command called with no message IDs.")
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": "MISSING_PARAMETER",
                    "details": "--ids option requires at least one valid message ID.",
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(msg)
        ctx.exit(1)
        return

    if logger:
        logger.info(
            f"Executing '{cmd_name}' for IDs: {message_ids} (Dry run: {dry_run})"
        )

    human_dry_run_msg = f"DRY RUN: {len(message_ids)} email(s) would be PERMANENTLY DELETED. No actual changes made."
    human_success_msg = f"Successfully PERMANENTLY DELETED {len(message_ids)} email(s)."

    if dry_run:
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_dry_run_msg,
                "data": {
                    "action_taken": False,
                    "processed_ids_count": len(message_ids),
                },
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(
                "WARNING: This would PERMANENTLY DELETE emails. No actual changes in dry run.",
                fg="yellow",
            )
            click.echo(human_dry_run_msg)
        if logger:
            logger.info("Dry run: Permanent delete operation completed.")
        return

    # First confirmation
    # First confirmation
    confirmed, confirm_msg = _confirm_action(
        prompt_message=f"Are you absolutely sure you want to PERMANENTLY DELETE these {len(message_ids)} email(s)? This is IRREVERSIBLE.",
        yes_flag=yes
    )
    if yes and confirmed: # Changed yes_flag to yes
        click.echo(click.style(confirm_msg, fg="green"))

    if not confirmed:
        if output_format == "human" and not yes: # Changed yes_flag to yes
            click.echo(confirm_msg)
        elif output_format == "json":
            response_obj = {
                "status": "aborted_by_user",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": {"action_taken": False},
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(msg)
        if logger:
            logger.info("User aborted permanent delete operation.")
        return

    # Second "YESIDO" confirmation (only if not bypassed by --yes and first confirm passed)
    if confirmed and not yes: # Only prompt if --yes was NOT given and first confirm passed
        # Only prompt for YESIDO if in human output mode, JSON mode would skip this specific interactive prompt
        if output_format == "human":
            confirmation_text = click.prompt(
                click.style(
                    "This action is IRREVERSIBLE. To proceed, type 'YESIDO' and press Enter",
                fg="yellow",
                bold=True,
            ),
            type=str,
            default="",
            show_default=False,
            prompt_suffix=": ",
        )
            if confirmation_text.strip().upper() != "YESIDO":
                click.echo("Confirmation text did not match. Permanent deletion aborted.")
                if logger: logger.info("User failed second confirmation (did not type YESIDO).")
                # Handle JSON abort for this specific failure if desired, or let it fall through
                if output_format == "json":
                     sys.stdout.write(json.dumps({
                        "status": "aborted_by_user",
                        "command_executed": cmd_name,
                        "message": "Confirmation text 'YESIDO' did not match. Permanent deletion aborted.",
                        "data": {"action_taken": False},
                        "error_details": None
                    }, indent=2)+'\n')
                return
    elif confirmed and yes: # If --yes was given and previous confirm passed
        click.echo(click.style("Confirmation 'YESIDO' bypassed by --yes flag.", fg="green"))
        if logger: logger.info("'YESIDO' confirmation bypassed by --yes flag.")
    # If first confirm failed, 'confirmed' is False, so these YESIDO blocks are skipped.

    # Third "FINAL WARNING" confirmation (only if all previous steps passed or were bypassed by --yes)
    if confirmed: # 'confirmed' here means all prior checks passed or were bypassed by --yes
        final_confirmed, final_confirm_msg = _confirm_action(
            prompt_message=click.style("FINAL WARNING: All checks passed. Confirm PERMANENT DELETION of these emails?", fg="red", bold=True),
            yes_flag=yes,
            default_abort_message="Permanent deletion aborted at final warning."
        )
        if yes and final_confirmed: # Changed yes_flag to yes
            click.echo(click.style(final_confirm_msg, fg="green"))
        
        if not final_confirmed:
            if output_format == "human" and not yes: # Changed yes_flag to yes
                click.echo(final_confirm_msg)
            elif output_format == "json":
                 sys.stdout.write(json.dumps({
                    "status": "aborted_by_user",
                    "command_executed": cmd_name,
                    "message": final_confirm_msg, # Use message from _confirm_action
                    "data": {"action_taken": False},
                    "error_details": None
                }, indent=2)+'\n')
            return
    elif not confirmed: # If first confirmation failed, we should have already returned. This is a safeguard.
        return


    try:
        gmail_api_service.batch_delete_permanently(g_service_client, message_ids)
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_success_msg,
                "data": {"action_taken": True, "processed_ids_count": len(message_ids)},
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(human_success_msg)
        if logger:
            logger.info(f"Successfully permanently deleted {len(message_ids)} emails.")
    except (InvalidParameterError, GmailApiError, DamienError) as e:
        msg = f"Error during '{cmd_name}': {e.message if hasattr(e, 'message') else str(e)}"
        error_code = e.__class__.__name__.upper().replace("ERROR", "_ERROR")
        if logger:
            logger.error(f"{error_code} in '{cmd_name}': {e}", exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": error_code,
                    "details": str(
                        e.original_exception if hasattr(e, "original_exception") else e
                    ),
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
    except Exception as e:
        msg = f"Unexpected error in '{cmd_name}': {e}"
        if logger:
            logger.error(msg, exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)},
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)


@emails_group.command("label")
@click.option(
    "--ids", "message_ids_str", required=True, help="Comma-separated IDs to label."
)
@click.option("--add-labels", help="Comma-separated Label names to add.")
@click.option("--remove-labels", help="Comma-separated Label names to remove.")
@click.option("--dry-run", is_flag=True, help="Show what would be done.")
@click.option(
    "--output-format",
    type=click.Choice(["human", "json"]),
    default="human",
    show_default=True,
)
@click.pass_context
def label_cmd(ctx, message_ids_str, add_labels, remove_labels, dry_run, output_format):
    """Adds or removes labels from specified emails."""
    logger = ctx.obj.get("logger")
    g_service_client = ctx.obj.get("gmail_service")
    cmd_name = "damien emails label"
    message_ids = _parse_ids(message_ids_str)
    add_label_names_list = _parse_ids(add_labels) if add_labels else []
    remove_label_names_list = _parse_ids(remove_labels) if remove_labels else []
    params_provided = {
        "ids": message_ids,
        "add_labels": add_label_names_list,
        "remove_labels": remove_label_names_list,
        "dry_run": dry_run,
    }

    if not message_ids:
        msg = "No message IDs provided to label."
        if logger:
            logger.warning("Label command called with no message IDs.")
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": "MISSING_PARAMETER",
                    "details": "--ids option requires at least one valid message ID.",
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(msg)
        ctx.exit(1)
        return

    if not add_label_names_list and not remove_label_names_list:
        msg = "No labels specified to add or remove."
        if logger:
            logger.warning("Label command called with no labels to change.")
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": "MISSING_PARAMETER",
                    "details": "Either --add-labels or --remove-labels must be specified.",
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(msg)
        ctx.exit(1)
        return

    if logger:
        logger.info(
            f"Executing '{cmd_name}' for IDs: {message_ids} (Add: {add_label_names_list}, Remove: {remove_label_names_list}, Dry run: {dry_run})"
        )

    action_summary = []
    if add_label_names_list:
        action_summary.append(f"add {add_label_names_list}")
    if remove_label_names_list:
        action_summary.append(f"remove {remove_label_names_list}")
    human_dry_run_msg = f"DRY RUN: Would {' and '.join(action_summary)} for {len(message_ids)} email(s). No actual changes made."
    human_success_msg = (
        f"Successfully applied label changes to {len(message_ids)} email(s)."
    )

    if dry_run:
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_dry_run_msg,
                "data": {
                    "processed_ids": message_ids,
                    "add_labels": add_label_names_list,
                    "remove_labels": remove_label_names_list,
                    "action_taken": False,
                },
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(human_dry_run_msg)
        if logger:
            logger.info("Dry run: Label operation completed.")
        return

    try:
        gmail_api_service.batch_modify_message_labels(
            g_service_client,
            message_ids,
            add_label_names=add_label_names_list,
            remove_label_names=remove_label_names_list,
        )
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_success_msg,
                "data": {
                    "processed_ids": message_ids,
                    "add_labels": add_label_names_list,
                    "remove_labels": remove_label_names_list,
                    "action_taken": True,
                },
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(human_success_msg)
        if logger:
            logger.info(f"Successfully labeled {len(message_ids)} emails.")
    except (InvalidParameterError, GmailApiError, DamienError) as e:
        msg = f"Error during '{cmd_name}': {e.message if hasattr(e, 'message') else str(e)}"
        error_code = e.__class__.__name__.upper().replace("ERROR", "_ERROR")
        if logger:
            logger.error(f"{error_code} in '{cmd_name}': {e}", exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": error_code,
                    "details": str(
                        e.original_exception if hasattr(e, "original_exception") else e
                    ),
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
    except Exception as e:
        msg = f"Unexpected error in '{cmd_name}': {e}"
        if logger:
            logger.error(msg, exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)},
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)


@emails_group.command("mark")
@click.option(
    "--ids", "message_ids_str", required=True, help="Comma-separated IDs to mark."
)
@click.option(
    "--action",
    "mark_action",
    type=click.Choice(["read", "unread"], case_sensitive=False),
    required=True,
)
@click.option("--dry-run", is_flag=True, help="Show what would be done.")
@click.option(
    "--output-format",
    type=click.Choice(["human", "json"]),
    default="human",
    show_default=True,
)
@click.pass_context
def mark_cmd(ctx, message_ids_str, mark_action, dry_run, output_format):
    """Marks specified emails as read or unread."""
    logger = ctx.obj.get("logger")
    g_service_client = ctx.obj.get("gmail_service")
    cmd_name = "damien emails mark"
    message_ids = _parse_ids(message_ids_str)
    params_provided = {"ids": message_ids, "action": mark_action, "dry_run": dry_run}

    if not message_ids:
        msg = "No message IDs provided to mark."
        if logger:
            logger.warning("Mark command called with no message IDs.")
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": "MISSING_PARAMETER",
                    "details": "--ids option requires at least one valid message ID.",
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(msg)
        ctx.exit(1)
        return

    if logger:
        logger.info(
            f"Executing '{cmd_name}' for IDs: {message_ids} (action: {mark_action}, Dry run: {dry_run})"
        )

    human_dry_run_msg = f"DRY RUN: {len(message_ids)} email(s) would be marked as {mark_action}. No actual changes made."
    human_success_msg = (
        f"Successfully marked {len(message_ids)} email(s) as {mark_action}."
    )

    if dry_run:
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_dry_run_msg,
                "data": {
                    "processed_ids": message_ids,
                    "mark_action": mark_action,
                    "action_taken": False,
                },
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(human_dry_run_msg)
        if logger:
            logger.info("Dry run: Mark operation completed.")
        return

    try:
        gmail_api_service.batch_mark_messages(
            g_service_client, message_ids, mark_as=mark_action
        )
        if output_format == "json":
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": human_success_msg,
                "data": {
                    "processed_ids": message_ids,
                    "mark_action": mark_action,
                    "action_taken": True,
                },
                "error_details": None,
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.echo(human_success_msg)
        if logger:
            logger.info(
                f"Successfully marked {len(message_ids)} emails as {mark_action}."
            )
    except (InvalidParameterError, GmailApiError, DamienError) as e:
        msg = f"Error during '{cmd_name}': {e.message if hasattr(e, 'message') else str(e)}"
        error_code = e.__class__.__name__.upper().replace("ERROR", "_ERROR")
        if logger:
            logger.error(f"{error_code} in '{cmd_name}': {e}", exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {
                    "code": error_code,
                    "details": str(
                        e.original_exception if hasattr(e, "original_exception") else e
                    ),
                },
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
    except Exception as e:
        msg = f"Unexpected error in '{cmd_name}': {e}"
        if logger:
            logger.error(msg, exc_info=True)
        if output_format == "json":
            response_obj = {
                "status": "error",
                "command_executed": cmd_name,
                "parameters_provided": params_provided,
                "message": msg,
                "data": None,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)},
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + "\n")
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
