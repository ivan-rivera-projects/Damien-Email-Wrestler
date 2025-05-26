import click
import json
from datetime import datetime, timezone
from typing import Optional
from damien_cli.core_api import gmail_api_service
from damien_cli.core.cli_utils import _confirm_action
import logging

logger = logging.getLogger(__name__)

# Create emails command group
emails = click.Group(name="emails", help="Email management commands.")

# Add new command group for settings
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
