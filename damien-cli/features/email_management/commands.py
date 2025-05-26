import json
import click
from damien_cli.core_api import gmail_api_service

# Define the main 'emails' group
@click.group()
def emails():
    """Manage email related commands."""
    pass

# Define 'email_settings_commands' as a standalone group
@click.group(name="email-settings") # Set the desired command name here
def email_settings_commands():
    """Manage Gmail settings such as vacation responder, IMAP, and POP."""
    pass

@email_settings_commands.command("get-vacation-settings")
def get_vacation_settings_cmd():
    """Get Gmail vacation responder settings."""
    service = gmail_api_service.get_authenticated_service()
    if not service:
        click.echo("Failed to authenticate Gmail service.")
        return
    try:
        settings = gmail_api_service.get_vacation_settings(service)
        click.echo(json.dumps(settings, indent=2))
    except Exception as e:
        click.echo(f"Error getting vacation settings: {e}")

@email_settings_commands.command("update-vacation-settings")
@click.argument("vacation_settings_json", type=click.Path(exists=True))
def update_vacation_settings_cmd(vacation_settings_json):
    """Update Gmail vacation responder settings from a JSON file."""
    service = gmail_api_service.get_authenticated_service()
    if not service:
        click.echo("Failed to authenticate Gmail service.")
        return
    try:
        with open(vacation_settings_json, "r") as f:
            vacation_settings = json.load(f)
        updated = gmail_api_service.update_vacation_settings(service, vacation_settings)
        click.echo(json.dumps(updated, indent=2))
    except Exception as e:
        click.echo(f"Error updating vacation settings: {e}")

@email_settings_commands.command("enable-vacation-responder")
def enable_vacation_responder_cmd():
    """Enable Gmail vacation responder."""
    service = gmail_api_service.get_authenticated_service()
    if not service:
        click.echo("Failed to authenticate Gmail service.")
        return
    try:
        result = gmail_api_service.enable_vacation_responder(service)
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error enabling vacation responder: {e}")

@email_settings_commands.command("disable-vacation-responder")
def disable_vacation_responder_cmd():
    """Disable Gmail vacation responder."""
    service = gmail_api_service.get_authenticated_service()
    if not service:
        click.echo("Failed to authenticate Gmail service.")
        return
    try:
        result = gmail_api_service.disable_vacation_responder(service)
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error disabling vacation responder: {e}")

@email_settings_commands.command("get-imap-settings")
def get_imap_settings_cmd():
    """Get Gmail IMAP settings."""
    service = gmail_api_service.get_authenticated_service()
    if not service:
        click.echo("Failed to authenticate Gmail service.")
        return
    try:
        settings = gmail_api_service.get_imap_settings(service)
        click.echo(json.dumps(settings, indent=2))
    except Exception as e:
        click.echo(f"Error getting IMAP settings: {e}")

@email_settings_commands.command("update-imap-settings")
@click.argument("imap_settings_json", type=click.Path(exists=True))
def update_imap_settings_cmd(imap_settings_json):
    """Update Gmail IMAP settings from a JSON file."""
    service = gmail_api_service.get_authenticated_service()
    if not service:
        click.echo("Failed to authenticate Gmail service.")
        return
    try:
        with open(imap_settings_json, "r") as f:
            imap_settings = json.load(f)
        updated = gmail_api_service.update_imap_settings(service, imap_settings)
        click.echo(json.dumps(updated, indent=2))
    except Exception as e:
        click.echo(f"Error updating IMAP settings: {e}")

@email_settings_commands.command("get-pop-settings")
def get_pop_settings_cmd():
    """Get Gmail POP settings."""
    service = gmail_api_service.get_authenticated_service()
    if not service:
        click.echo("Failed to authenticate Gmail service.")
        return
    try:
        settings = gmail_api_service.get_pop_settings(service)
        click.echo(json.dumps(settings, indent=2))
    except Exception as e:
        click.echo(f"Error getting POP settings: {e}")

@email_settings_commands.command("update-pop-settings")
@click.argument("pop_settings_json", type=click.Path(exists=True))
def update_pop_settings_cmd(pop_settings_json):
    """Update Gmail POP settings from a JSON file."""
    service = gmail_api_service.get_authenticated_service()
    if not service:
        click.echo("Failed to authenticate Gmail service.")
        return
    try:
        with open(pop_settings_json, "r") as f:
            pop_settings = json.load(f)
        updated = gmail_api_service.update_pop_settings(service, pop_settings)
        click.echo(json.dumps(updated, indent=2))
    except Exception as e:
        click.echo(f"Error updating POP settings: {e}")

# Add the fully defined email_settings_commands group to the main emails group
emails.add_command(email_settings_commands)