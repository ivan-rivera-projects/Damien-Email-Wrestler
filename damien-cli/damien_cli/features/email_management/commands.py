import click
import json
from datetime import datetime, timezone
from typing import Optional, List
import sys
from damien_cli.core_api import gmail_api_service
from damien_cli.core.cli_utils import _confirm_action
from damien_cli.core_api.exceptions import GmailApiError, InvalidParameterError, DamienError
import logging

logger = logging.getLogger(__name__)

# Create emails command group
emails = click.Group(name="emails", help="Email management commands.")

@emails.command("list")
@click.option('--query', '-q', help="Gmail search query (e.g., 'is:unread', 'from:example.com')")
@click.option('--max-results', '-m', type=int, default=10, help="Maximum number of emails to retrieve (default: 10)")
@click.option('--page-token', '-p', help="Token for fetching the next page of results")
@click.option('--output-format', type=click.Choice(['human', 'json']), default='human', help="Output format")
@click.pass_context
def list_emails_cmd(ctx, query, max_results, page_token, output_format):
    """Lists email messages based on query with support for pagination."""
    gmail_service = ctx.obj.get('gmail_service')
    logger = ctx.obj.get('logger')
    cmd_name = "damien emails list"
    
    if not gmail_service:
        msg = "Damien is not connected to Gmail. Please run `damien login` first."
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "NO_GMAIL_SERVICE"}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
        return
    
    if logger:
        logger.info(f"Executing '{cmd_name}' with query: '{query}', max_results: {max_results}")
    
    try:
        # Get list of message stubs
        result = gmail_api_service.list_messages(
            gmail_service=gmail_service,
            query_string=query,
            max_results=max_results,
            page_token=page_token
        )
        
        messages = result.get('messages', [])
        next_page_token = result.get('nextPageToken')
        
        if not messages:
            if output_format == 'json':
                response_obj = {
                    "status": "success",
                    "command_executed": cmd_name,
                    "message": "No emails found.",
                    "data": {
                        "messages": [],
                        "next_page_token": next_page_token
                    },
                    "error_details": None
                }
                sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
            else:
                query_msg = f" matching '{query}'" if query else ""
                click.echo(f"No emails found{query_msg}.")
            return
        
        # Get details for each message stub
        email_details = []
        for msg in messages:
            message_id = msg.get('id')
            try:
                details = gmail_api_service.get_message_details(
                    gmail_service=gmail_service,
                    message_id=message_id,
                    format='metadata'  # For list, we just need basic info
                )
                email_details.append(details)
            except GmailApiError as e:
                # Log error but continue with other messages
                logger.warning(f"Could not get details for message {message_id}: {e}")
                continue
        
        if output_format == 'json':
            # Format for JSON output
            formatted_messages = []
            for msg in email_details:
                headers = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
                formatted_messages.append({
                    "id": msg.get('id'),
                    "thread_id": msg.get('threadId'),
                    "subject": headers.get('subject', 'No Subject'),
                    "from": headers.get('from', 'Unknown Sender'),
                    "date": headers.get('date', 'Unknown Date'),
                    "snippet": msg.get('snippet', '')
                })
            
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "message": f"Successfully listed {len(email_details)} emails.",
                "data": {
                    "messages": formatted_messages,
                    "next_page_token": next_page_token
                },
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else:
            # Human-readable output
            click.echo(f"\n📨 Emails{' matching query: ' + query if query else ''}")
            click.echo("=" * 70)
            
            for i, msg in enumerate(email_details):
                headers = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
                subject = headers.get('subject', 'No Subject')
                sender = headers.get('from', 'Unknown Sender')
                date = headers.get('date', 'Unknown Date')
                
                click.echo(f"\n{i+1}. ID: {msg.get('id')}")
                click.echo(f"   Subject: {subject}")
                click.echo(f"   From: {sender}")
                click.echo(f"   Date: {date}")
                click.echo(f"   Snippet: {msg.get('snippet', '')[:100]}...")
            
            click.echo("\n" + "=" * 70)
            if next_page_token:
                click.echo(f'To see more, use --page-token "{next_page_token}"')
            else:
                click.echo("No more results available.")
    
    except GmailApiError as e:
        msg = f"Error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "GMAIL_API_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)
    
    except Exception as e:
        msg = f"Unexpected error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)


@emails.command("get")
@click.option('--id', required=True, help="The ID of the email to retrieve")
@click.option('--format', 'email_format', type=click.Choice(['full', 'metadata', 'minimal', 'raw']), 
              default='full', help="Level of detail to retrieve")
@click.option('--output-format', type=click.Choice(['human', 'json']), default='human', help="Output format")
@click.pass_context
def get_email_cmd(ctx, id, email_format, output_format):
    """Retrieves and displays details of a specific email."""
    gmail_service = ctx.obj.get('gmail_service')
    logger = ctx.obj.get('logger')
    cmd_name = "damien emails get"
    
    if not gmail_service:
        msg = "Damien is not connected to Gmail. Please run `damien login` first."
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "NO_GMAIL_SERVICE"}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
        return
    
    if logger:
        logger.info(f"Executing '{cmd_name}' for email ID: {id}, format: {email_format}")
    
    try:
        # Get message details
        email_details = gmail_api_service.get_message_details(
            gmail_service=gmail_service,
            message_id=id,
            format=email_format
        )
        
        if output_format == 'json':
            # Return raw API response for JSON output
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "message": f"Successfully retrieved email {id}.",
                "data": email_details,
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else:
            # Human-readable output
            click.echo(f"\n📧 Details for Email ID: {id}")
            click.echo("=" * 70)
            
            # Process headers
            headers = {h['name'].lower(): h['value'] for h in email_details.get('payload', {}).get('headers', [])}
            subject = headers.get('subject', 'No Subject')
            sender = headers.get('from', 'Unknown Sender')
            recipient = headers.get('to', 'Unknown Recipient')
            date = headers.get('date', 'Unknown Date')
            cc = headers.get('cc', None)
            bcc = headers.get('bcc', None)
            
            click.echo(f"Subject: {subject}")
            click.echo(f"From: {sender}")
            click.echo(f"To: {recipient}")
            if cc:
                click.echo(f"CC: {cc}")
            if bcc:
                click.echo(f"BCC: {bcc}")
            click.echo(f"Date: {date}")
            
            # Show labels if present
            labels = email_details.get('labelIds', [])
            if labels:
                click.echo(f"Labels: {', '.join(labels)}")
            
            # Extract and show body content if full format
            if email_format == 'full':
                click.echo("\nBody:")
                click.echo("-" * 70)
                
                # Helper function to extract body content
                def extract_body(payload):
                    if not payload:
                        return "No content found."
                    
                    body_data = payload.get('body', {}).get('data')
                    if body_data:
                        import base64
                        return base64.urlsafe_b64decode(body_data).decode('utf-8')
                    
                    # Check for multipart message
                    parts = payload.get('parts', [])
                    if parts:
                        # Try to find text/plain part first
                        for part in parts:
                            if part.get('mimeType') == 'text/plain':
                                part_body = part.get('body', {}).get('data')
                                if part_body:
                                    import base64
                                    return base64.urlsafe_b64decode(part_body).decode('utf-8')
                        
                        # If no text/plain, try text/html
                        for part in parts:
                            if part.get('mimeType') == 'text/html':
                                part_body = part.get('body', {}).get('data')
                                if part_body:
                                    import base64
                                    html_content = base64.urlsafe_b64decode(part_body).decode('utf-8')
                                    return f"[HTML Content] {html_content[:500]}..."
                    
                    return "Could not extract body content."
                
                body_content = extract_body(email_details.get('payload', {}))
                click.echo(body_content)
            else:
                # For other formats, just show the snippet
                click.echo("\nSnippet:")
                click.echo("-" * 70)
                click.echo(email_details.get('snippet', 'No snippet available.'))
            
            click.echo("\n" + "=" * 70)
    
    except GmailApiError as e:
        msg = f"Error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "GMAIL_API_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)
    
    except Exception as e:
        msg = f"Unexpected error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)


@emails.command("trash")
@click.option('--ids', required=True, help="Comma-separated list of email IDs to trash")
@click.option('--dry-run', is_flag=True, help="Show what would be done without making changes")
@click.option('--yes', '-y', is_flag=True, help="Skip confirmation prompt")
@click.option('--output-format', type=click.Choice(['human', 'json']), default='human', help="Output format")
@click.pass_context
def trash_emails_cmd(ctx, ids, dry_run, yes, output_format):
    """Moves specified emails to the Trash folder."""
    gmail_service = ctx.obj.get('gmail_service')
    logger = ctx.obj.get('logger')
    cmd_name = "damien emails trash"
    
    if not gmail_service:
        msg = "Damien is not connected to Gmail. Please run `damien login` first."
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "NO_GMAIL_SERVICE"}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
        return
    
    # Split comma-separated IDs into a list
    id_list = [id.strip() for id in ids.split(',')]
    
    if logger:
        logger.info(f"Executing '{cmd_name}' for {len(id_list)} email(s), dry_run: {dry_run}")
    
    # Dry run mode - just show what would happen
    if dry_run:
        if output_format == 'json':
            response_obj = {
                "status": "dry_run",
                "command_executed": cmd_name,
                "message": f"DRY RUN: {len(id_list)} email(s) would be moved to Trash. No actual changes made.",
                "data": {
                    "action": "trash",
                    "affected_ids": id_list,
                    "count": len(id_list)
                },
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else:
            click.echo(click.style(f"DRY RUN: {len(id_list)} email(s) would be moved to Trash. No actual changes made.", fg="yellow"))
        return
    
    # Get confirmation before proceeding
    confirmed, message = _confirm_action(
        prompt_message=f"Are you sure you want to move these {len(id_list)} email(s) to Trash?",
        yes_flag=yes
    )
    
    if yes and confirmed:
        click.echo(click.style(message, fg="green"))
    
    if not confirmed:
        if output_format == 'human' and not yes:
            click.echo(message)
        elif output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "aborted_by_user",
                "command_executed": cmd_name,
                "message": message,
                "data": {"action_taken": False},
                "error_details": None
            }, indent=2) + '\n')
        return
    
    try:
        # Move emails to trash
        result = gmail_api_service.batch_trash_messages(
            gmail_service=gmail_service,
            message_ids=id_list
        )
        
        if output_format == 'json':
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "message": f"Successfully moved {len(id_list)} email(s) to Trash.",
                "data": result,
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else:
            click.echo(click.style(f"Successfully moved {len(id_list)} email(s) to Trash.", fg="green"))
    
    except GmailApiError as e:
        msg = f"Error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "GMAIL_API_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)
    
    except Exception as e:
        msg = f"Unexpected error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)


@emails.command("delete")
@click.option('--ids', required=True, help="Comma-separated list of email IDs to delete permanently")
@click.option('--dry-run', is_flag=True, help="Show what would be done without making changes")
@click.option('--yes', '-y', is_flag=True, help="Skip confirmation prompts (USE WITH EXTREME CAUTION)")
@click.option('--output-format', type=click.Choice(['human', 'json']), default='human', help="Output format")
@click.pass_context
def delete_emails_cmd(ctx, ids, dry_run, yes, output_format):
    """PERMANENTLY deletes specified emails. This action is irreversible."""
    gmail_service = ctx.obj.get('gmail_service')
    logger = ctx.obj.get('logger')
    cmd_name = "damien emails delete"
    
    if not gmail_service:
        msg = "Damien is not connected to Gmail. Please run `damien login` first."
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "NO_GMAIL_SERVICE"}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
        return
    
    # Split comma-separated IDs into a list
    id_list = [id.strip() for id in ids.split(',')]
    
    if logger:
        logger.info(f"Executing '{cmd_name}' for {len(id_list)} email(s), dry_run: {dry_run}")
    
    # Dry run mode - just show what would happen
    if dry_run:
        if output_format == 'json':
            response_obj = {
                "status": "dry_run",
                "command_executed": cmd_name,
                "message": f"DRY RUN: {len(id_list)} email(s) would be PERMANENTLY DELETED. No actual changes made.",
                "data": {
                    "action": "delete_permanently",
                    "affected_ids": id_list,
                    "count": len(id_list)
                },
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else:
            click.echo(click.style(f"DRY RUN: {len(id_list)} email(s) would be PERMANENTLY DELETED. No actual changes made.", fg="yellow", bold=True))
            click.echo(click.style("⚠️  Warning: This action would be irreversible if not in dry-run mode.", fg="yellow"))
        return
    
    # First confirmation (generic)
    confirmed, message = _confirm_action(
        prompt_message=f"Are you absolutely sure you want to PERMANENTLY DELETE these {len(id_list)} email(s)? This is IRREVERSIBLE.",
        yes_flag=yes
    )
    
    if yes and confirmed:
        click.echo(click.style(message, fg="green"))
    
    if not confirmed:
        if output_format == 'human' and not yes:
            click.echo(message)
        elif output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "aborted_by_user",
                "command_executed": cmd_name,
                "message": message,
                "data": {"action_taken": False},
                "error_details": None
            }, indent=2) + '\n')
        return
    
    # Second confirmation (require typing YESIDO)
    if not yes:
        try:
            confirmation_text = click.prompt(
                click.style("Please type YESIDO (all caps) to confirm permanent deletion", fg="red", bold=True),
                type=str
            )
            if confirmation_text != "YESIDO":
                click.echo("Confirmation text did not match. Permanent deletion aborted.")
                return
        except click.Abort:
            click.echo("\nOperation aborted by user.")
            return
    else:
        click.echo(click.style("Confirmation 'YESIDO' bypassed by --yes flag.", fg="yellow", bold=True))
    
    # Final confirmation (last chance)
    confirmed, message = _confirm_action(
        prompt_message=click.style("FINAL WARNING: All checks passed. Confirm PERMANENT DELETION of these emails?", fg="red", bold=True),
        yes_flag=yes,
        default_abort_message="Permanent deletion aborted at final warning."
    )
    
    if yes and confirmed:
        click.echo(click.style(message, fg="green"))
    
    if not confirmed:
        if output_format == 'human' and not yes:
            click.echo(message)
        elif output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "aborted_by_user",
                "command_executed": cmd_name,
                "message": message,
                "data": {"action_taken": False},
                "error_details": None
            }, indent=2) + '\n')
        return
    
    try:
        # Permanently delete emails
        result = gmail_api_service.batch_delete_permanently(
            gmail_service=gmail_service,
            message_ids=id_list
        )
        
        if output_format == 'json':
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "message": f"Successfully PERMANENTLY DELETED {len(id_list)} email(s).",
                "data": result,
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else:
            click.echo(click.style(f"Successfully PERMANENTLY DELETED {len(id_list)} email(s).", fg="green"))
    
    except GmailApiError as e:
        msg = f"Error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "GMAIL_API_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)
    
    except Exception as e:
        msg = f"Unexpected error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)
    # The block from line 608 to 679 was incorrectly duplicated here from label_emails_cmd
    # It should be removed as delete_emails_cmd only deletes.
    # The try block for actual deletion starts after all confirmations.
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "GMAIL_API_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)
    
    except Exception as e:
        msg = f"Unexpected error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)
@emails.command("label")
@click.option('--ids', required=True, help="Comma-separated list of email IDs to label")
@click.option('--add-labels', help="Comma-separated list of labels to add")
@click.option('--remove-labels', help="Comma-separated list of labels to remove")
@click.option('--dry-run', is_flag=True, help="Show what would be done without making changes")
@click.option('--yes', '-y', is_flag=True, help="Skip confirmation prompt")
@click.option('--output-format', type=click.Choice(['human', 'json']), default='human', help="Output format")
@click.pass_context
def label_emails_cmd(ctx, ids, add_labels, remove_labels, dry_run, yes, output_format):
    """Add or remove labels on specified emails."""
    gmail_service = ctx.obj.get('gmail_service')
    logger = ctx.obj.get('logger')
    cmd_name = "damien emails label"

    if not gmail_service:
        msg = "Damien is not connected to Gmail. Please run `damien login` first."
        if output_format == 'json':
            import sys, json
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "NO_GMAIL_SERVICE"}
            }, indent=2) + '\n')
        else:
            import click
            click.secho(msg, fg="red")
        ctx.exit(1)
        return

    id_list = [id.strip() for id in ids.split(',')]
    add_label_list = [label.strip() for label in add_labels.split(',')] if add_labels else None
    remove_label_list = [label.strip() for label in remove_labels.split(',')] if remove_labels else None

    if logger:
        logger.info(f"Executing '{cmd_name}' for {len(id_list)} email(s), add_labels: {add_label_list}, remove_labels: {remove_label_list}, dry_run: {dry_run}")

    if dry_run:
        if output_format == 'json':
            import sys, json
            response_obj = {
                "status": "dry_run",
                "command_executed": cmd_name,
                "message": f"DRY RUN: Would modify labels on {len(id_list)} email(s). No actual changes made.",
                "data": {
                    "action": "label_modify",
                    "affected_ids": id_list,
                    "add_labels": add_label_list,
                    "remove_labels": remove_label_list,
                    "count": len(id_list)
                },
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else:
            import click
            click.echo(click.style(f"DRY RUN: Would modify labels on {len(id_list)} email(s). No actual changes made.", fg="yellow"))
        return

    confirmed, message = _confirm_action(
        prompt_message=f"Are you sure you want to modify labels on these {len(id_list)} email(s)?",
        yes_flag=yes
    )

    if yes and confirmed:
        import click
        click.echo(click.style(message, fg="green"))

    if not confirmed:
        if output_format == 'human' and not yes:
            import click
            click.echo(message)
        elif output_format == 'json':
            import sys, json
            sys.stdout.write(json.dumps({
                "status": "aborted_by_user",
                "command_executed": cmd_name,
                "message": message,
                "data": {"action_taken": False},
                "error_details": None
            }, indent=2) + '\n')
        return

    try:
        result = gmail_api_service.batch_modify_message_labels(
            gmail_service=gmail_service,
            message_ids=id_list,
            add_label_names=add_label_list,
            remove_label_names=remove_label_list
        )

        if output_format == 'json':
            import json
            click.echo(json.dumps(result, indent=2))
        else:
            changes = []
            if add_label_list:
                changes.append(f"added labels: {', '.join(add_label_list)}")
            if remove_label_list:
                changes.append(f"removed labels: {', '.join(remove_label_list)}")

            import click
            click.echo(click.style(f"Successfully applied label changes to {len(id_list)} email(s) ({', '.join(changes)}).", fg="green"))

    except Exception as e:
        msg = f"Error during '{cmd_name}': {e}"
        if output_format == 'json':
            import sys, json
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "GMAIL_API_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            import click
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)


@emails.command("mark")
@click.option('--ids', required=True, help="Comma-separated list of email IDs to mark")
@click.option('--action', type=click.Choice(['read', 'unread']), required=True, help="Action to perform")
@click.option('--dry-run', is_flag=True, help="Show what would be done without making changes")
@click.option('--yes', '-y', is_flag=True, help="Skip confirmation prompt")
@click.option('--output-format', type=click.Choice(['human', 'json']), default='human', help="Output format")
@click.pass_context
def mark_emails_cmd(ctx, ids, action, dry_run, yes, output_format):
    """Marks specified emails as read or unread."""
    gmail_service = ctx.obj.get('gmail_service')
    logger = ctx.obj.get('logger')
    cmd_name = "damien emails mark"
    
    if not gmail_service:
        msg = "Damien is not connected to Gmail. Please run `damien login` first."
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "NO_GMAIL_SERVICE"}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        ctx.exit(1)
        return
    
    # Split comma-separated IDs into a list
    id_list = [id.strip() for id in ids.split(',')]
    
    if logger:
        logger.info(f"Executing '{cmd_name}' for {len(id_list)} email(s), action: {action}, dry_run: {dry_run}")
    
    # Dry run mode - just show what would happen
    if dry_run:
        if output_format == 'json':
            response_obj = {
                "status": "dry_run",
                "command_executed": cmd_name,
                "message": f"DRY RUN: Would mark {len(id_list)} email(s) as {action}. No actual changes made.",
                "data": {
                    "action": f"mark_{action}",
                    "affected_ids": id_list,
                    "count": len(id_list)
                },
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else:
            click.echo(click.style(f"DRY RUN: Would mark {len(id_list)} email(s) as {action}. No actual changes made.", fg="yellow"))
        return
    
    # Get confirmation before proceeding
    confirmed, message = _confirm_action(
        prompt_message=f"Are you sure you want to mark these {len(id_list)} email(s) as {action}?",
        yes_flag=yes
    )
    
    if yes and confirmed:
        click.echo(click.style(message, fg="green"))
    
    if not confirmed:
        if output_format == 'human' and not yes:
            click.echo(message)
        elif output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "aborted_by_user",
                "command_executed": cmd_name,
                "message": message,
                "data": {"action_taken": False},
                "error_details": None
            }, indent=2) + '\n')
        return
    
    try:
        # Mark emails as read/unread
        result = gmail_api_service.batch_mark_messages(
            gmail_service=gmail_service,
            message_ids=id_list,
            action=action
        )
        
        if output_format == 'json':
            response_obj = {
                "status": "success",
                "command_executed": cmd_name,
                "message": f"Successfully marked {len(id_list)} email(s) as {action}.",
                "data": result,
                "error_details": None
            }
            sys.stdout.write(json.dumps(response_obj, indent=2) + '\n')
        else:
            click.echo(click.style(f"Successfully marked {len(id_list)} email(s) as {action}.", fg="green"))
    
    except GmailApiError as e:
        msg = f"Error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "GMAIL_API_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)
    
    except Exception as e:
        msg = f"Unexpected error during '{cmd_name}': {e}"
        if output_format == 'json':
            sys.stdout.write(json.dumps({
                "status": "error",
                "command_executed": cmd_name,
                "message": msg,
                "error_details": {"code": "UNEXPECTED_ERROR", "details": str(e)}
            }, indent=2) + '\n')
        else:
            click.secho(msg, fg="red")
        if logger:
            logger.error(msg, exc_info=True)
        ctx.exit(1)

# Add settings commands (vacation, imap, pop) below this line
@emails.group()
def settings():
    """Gmail settings management commands."""
    pass

# Vacation responder commands
@settings.group()
def vacation():
    """Vacation responder management."""
    pass

@vacation.command()
@click.option('--output-format', type=click.Choice(['human', 'json']), 
              default='human', help='Output format')
@click.pass_context
def get(ctx, output_format):
    """Get current vacation responder settings."""
    try:
        gmail_service = ctx.obj['gmail_service']
        logger = ctx.obj['logger']
        
        logger.debug("Getting vacation responder settings")
        
        result = gmail_api_service.get_vacation_settings(gmail_service=gmail_service)
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            # Human-readable output
            enabled = result.get('enableAutoReply', False)
            
            click.echo(f"\n🏖️  Vacation Responder Status")
            click.echo("=" * 40)
            click.echo(f"Enabled: {'Yes' if enabled else 'No'}")
            
            if enabled:
                subject = result.get('responseSubject', 'No subject')
                body = result.get('responseBodyPlainText', 'No message')
                start_time = result.get('startTime')
                end_time = result.get('endTime')
                restrict_contacts = result.get('restrictToContacts', False)
                restrict_domain = result.get('restrictToDomain', False)
                
                click.echo(f"Subject: {subject}")
                click.echo(f"Restrict to contacts: {'Yes' if restrict_contacts else 'No'}")
                click.echo(f"Restrict to domain: {'Yes' if restrict_domain else 'No'}")
                
                if start_time:
                    start_dt = datetime.fromtimestamp(int(start_time) / 1000, tz=timezone.utc)
                    click.echo(f"Start time: {start_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                if end_time:
                    end_dt = datetime.fromtimestamp(int(end_time) / 1000, tz=timezone.utc)
                    click.echo(f"End time: {end_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                click.echo(f"\nMessage:")
                click.echo("-" * 20)
                click.echo(body[:300] + "..." if len(body) > 300 else body)
            else:
                click.echo("Vacation responder is currently disabled.")
                
    except Exception as e:
        logger.error(f"Error getting vacation settings: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        ctx.exit(1)

@vacation.command()
@click.option('--subject', required=True, help='Auto-reply subject line')
@click.option('--body', required=True, help='Auto-reply message body')
@click.option('--start-time', help='Start time (ISO format: 2024-01-15T09:00:00Z)')
@click.option('--end-time', help='End time (ISO format: 2024-01-20T17:00:00Z)')
@click.option('--restrict-to-contacts', is_flag=True, 
              help='Only send auto-replies to people in contacts')
@click.option('--restrict-to-domain', is_flag=True,
              help='Only send auto-replies to people in the same domain')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.option('--output-format', type=click.Choice(['human', 'json']), 
              default='human', help='Output format')
@click.pass_context
def enable(ctx, subject, body, start_time, end_time, restrict_to_contacts, 
           restrict_to_domain, yes, output_format):
    """Enable vacation responder with specified message."""
    try:
        gmail_service = ctx.obj['gmail_service']
        logger = ctx.obj['logger']
        
        # Parse datetime strings if provided
        start_timestamp = None
        end_timestamp = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_timestamp = int(start_dt.timestamp() * 1000)
            except ValueError:
                click.echo("Error: Invalid start time format. Use ISO format like '2024-01-15T09:00:00Z'", err=True)
                ctx.exit(1)
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                end_timestamp = int(end_dt.timestamp() * 1000)
            except ValueError:
                click.echo("Error: Invalid end time format. Use ISO format like '2024-01-20T17:00:00Z'", err=True)
                ctx.exit(1)
        
        # Validate time range
        if start_timestamp and end_timestamp and start_timestamp >= end_timestamp:
            click.echo("Error: Start time must be before end time", err=True)
            ctx.exit(1)
        
        # Show preview and get confirmation
        if not yes:
            click.echo("\n📋 Vacation Responder Configuration:")
            click.echo(f"Subject: {subject}")
            click.echo(f"Message: {body[:100]}{'...' if len(body) > 100 else ''}")
            if start_time:
                click.echo(f"Start: {start_time}")
            if end_time:
                click.echo(f"End: {end_time}")
            click.echo(f"Restrict to contacts: {'Yes' if restrict_to_contacts else 'No'}")
            click.echo(f"Restrict to domain: {'Yes' if restrict_to_domain else 'No'}")
            
            confirmed, message = _confirm_action(
                "Enable vacation responder with these settings?",
                yes_flag=False
            )
            if not confirmed:
                click.echo(message)
                ctx.exit(0)
        
        logger.debug("Enabling vacation responder")
        
        result = gmail_api_service.update_vacation_settings(
            gmail_service=gmail_service,
            enabled=True,
            subject=subject,
            body=body,
            start_time=start_timestamp,
            end_time=end_timestamp,
            restrict_to_contacts=restrict_to_contacts,
            restrict_to_domain=restrict_to_domain
        )
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo("✅ Vacation responder enabled successfully!")
            click.echo(f"Subject: {subject}")
            if start_time or end_time:
                click.echo("Schedule:")
                if start_time:
                    click.echo(f"  Start: {start_time}")
                if end_time:
                    click.echo(f"  End: {end_time}")
            click.echo("\nYour vacation responder is now active.")
                
    except Exception as e:
        logger.error(f"Error enabling vacation responder: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        ctx.exit(1)

@vacation.command()
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.option('--output-format', type=click.Choice(['human', 'json']), 
              default='human', help='Output format')
@click.pass_context
def disable(ctx, yes, output_format):
    """Disable vacation responder."""
    try:
        gmail_service = ctx.obj['gmail_service']
        logger = ctx.obj['logger']
        
        # Get confirmation
        if not yes:
            confirmed, message = _confirm_action(
                "Disable vacation responder?",
                yes_flag=False
            )
            if not confirmed:
                click.echo(message)
                ctx.exit(0)
        
        logger.debug("Disabling vacation responder")
        
        result = gmail_api_service.disable_vacation_responder(gmail_service=gmail_service)
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo("✅ Vacation responder disabled successfully!")
                
    except Exception as e:
        logger.error(f"Error disabling vacation responder: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        ctx.exit(1)
# IMAP settings commands
@settings.group()
def imap():
    """IMAP access management."""
    pass

@imap.command()
@click.option('--output-format', type=click.Choice(['human', 'json']), 
              default='human', help='Output format')
@click.pass_context
def get(ctx, output_format):
    """Get current IMAP settings."""
    try:
        gmail_service = ctx.obj['gmail_service']
        logger = ctx.obj['logger']
        
        logger.debug("Getting IMAP settings")
        
        result = gmail_api_service.get_imap_settings(gmail_service=gmail_service)
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            # Human-readable output
            enabled = result.get('enabled', False)
            auto_expunge = result.get('autoExpunge', False)
            expunge_behavior = result.get('expungeBehavior', 'ARCHIVE')
            max_folder_size = result.get('maxFolderSize', 'Not set')
            
            click.echo(f"\n📨 IMAP Settings")
            click.echo("=" * 30)
            click.echo(f"Enabled: {'Yes' if enabled else 'No'}")
            click.echo(f"Auto-expunge: {'Yes' if auto_expunge else 'No'}")
            click.echo(f"Expunge behavior: {expunge_behavior.lower()}")
            click.echo(f"Max folder size: {max_folder_size}")
                
    except Exception as e:
        logger.error(f"Error getting IMAP settings: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        ctx.exit(1)

@imap.command()
@click.option('--enable/--disable', default=True, help='Enable or disable IMAP access')
@click.option('--auto-expunge/--no-auto-expunge', default=False, 
              help='Auto-expunge deleted messages')
@click.option('--expunge-behavior', type=click.Choice(['archive', 'trash', 'delete']), 
              default='archive', help='What to do with expunged messages')
@click.option('--max-folder-size', type=int, help='Maximum folder size in MB')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.option('--output-format', type=click.Choice(['human', 'json']), 
              default='human', help='Output format')
@click.pass_context
def update(ctx, enable, auto_expunge, expunge_behavior, max_folder_size, yes, output_format):
    """Update IMAP settings."""
    try:
        gmail_service = ctx.obj['gmail_service']
        logger = ctx.obj['logger']
        
        # Show preview and get confirmation
        if not yes:
            click.echo("\n📋 IMAP Settings Update:")
            click.echo(f"Enabled: {'Yes' if enable else 'No'}")
            click.echo(f"Auto-expunge: {'Yes' if auto_expunge else 'No'}")
            click.echo(f"Expunge behavior: {expunge_behavior}")
            if max_folder_size:
                click.echo(f"Max folder size: {max_folder_size} MB")
            
            confirmed, message = _confirm_action(
                "Update IMAP settings?",
                yes_flag=False
            )
            if not confirmed:
                click.echo(message)
                ctx.exit(0)
        
        logger.debug(f"Updating IMAP settings: enabled={enable}")
        
        result = gmail_api_service.update_imap_settings(
            gmail_service=gmail_service,
            enabled=enable,
            auto_expunge=auto_expunge,
            expunge_behavior=expunge_behavior,
            max_folder_size=max_folder_size
        )
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo("✅ IMAP settings updated successfully!")
            click.echo(f"IMAP access: {'Enabled' if enable else 'Disabled'}")
                
    except Exception as e:
        logger.error(f"Error updating IMAP settings: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        ctx.exit(1)

# POP settings commands
@settings.group()
def pop():
    """POP access management."""
    pass

@pop.command()
@click.option('--output-format', type=click.Choice(['human', 'json']), 
              default='human', help='Output format')
@click.pass_context
def get(ctx, output_format):
    """Get current POP settings."""
    try:
        gmail_service = ctx.obj['gmail_service']
        logger = ctx.obj['logger']
        
        logger.debug("Getting POP settings")
        
        result = gmail_api_service.get_pop_settings(gmail_service=gmail_service)
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            # Human-readable output
            access_window = result.get('accessWindow', 'disabled')
            disposition = result.get('disposition', 'leaveInInbox')
            
            click.echo(f"\n📥 POP Settings")
            click.echo("=" * 30)
            click.echo(f"Access window: {access_window}")
            click.echo(f"Message disposition: {disposition}")
            
            # Explain what these settings mean
            if access_window == 'disabled':
                click.echo("\nPOP access is currently disabled.")
            elif access_window == 'allMail':
                click.echo("\nPOP clients can access all mail.")
            elif access_window == 'fromNowOn':
                click.echo("\nPOP clients can access mail from now on.")
                
    except Exception as e:
        logger.error(f"Error getting POP settings: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        ctx.exit(1)

@pop.command()
@click.option('--access-window', 
              type=click.Choice(['allMail', 'fromNowOn', 'disabled']), 
              required=True,
              help='When POP clients can access mail')
@click.option('--disposition', 
              type=click.Choice(['leaveInInbox', 'archive', 'trash', 'delete']), 
              required=True,
              help='What happens to mail after POP access')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.option('--output-format', type=click.Choice(['human', 'json']), 
              default='human', help='Output format')
@click.pass_context
def update(ctx, access_window, disposition, yes, output_format):
    """Update POP settings."""
    try:
        gmail_service = ctx.obj['gmail_service']
        logger = ctx.obj['logger']
        
        # Show preview and get confirmation
        if not yes:
            click.echo("\n📋 POP Settings Update:")
            click.echo(f"Access window: {access_window}")
            click.echo(f"Message disposition: {disposition}")
            
            if disposition in ['trash', 'delete']:
                click.echo("\n⚠️  WARNING: This will affect how messages are handled after POP access!")
            
            confirmed, message = _confirm_action(
                "Update POP settings?",
                yes_flag=False
            )
            if not confirmed:
                click.echo(message)
                ctx.exit(0)
        
        logger.debug(f"Updating POP settings: access={access_window}, disposition={disposition}")
        
        result = gmail_api_service.update_pop_settings(
            gmail_service=gmail_service,
            access_window=access_window,
            disposition=disposition
        )
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo("✅ POP settings updated successfully!")
            click.echo(f"Access window: {access_window}")
            click.echo(f"Message disposition: {disposition}")
                
    except Exception as e:
        logger.error(f"Error updating POP settings: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        ctx.exit(1)
