import click
import logging
import os  # Often useful for CLI apps, e.g. checking env vars

# Import core utilities
from damien_cli.core.logging_setup import setup_logging

# Service acquisition and error handling will be managed in the login command.

# Import feature command groups
from damien_cli.features.email_management.commands import emails_group
from damien_cli.features.rule_management.commands import rules_group


@click.group()
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose (DEBUG level) logging."
)
@click.option(
    "--config-dir",
    envvar="DAMIEN_CONFIG_DIR",
    type=click.Path(),
    default=None,
    help="Path to an alternative config/data directory.",
)  # Example for future config
@click.pass_context
def damien(ctx, verbose, config_dir):
    """
    Damien-CLI: Your Pythonic Gmail Assistant.
    Damien helps you manage your Gmail inbox with smarts and power.
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Determine if running in a test environment (simplistic check for now)
    # A more robust way might be a dedicated environment variable for testing.
    # For now, assume regular CLI runs are not 'testing_mode=True' for logging.
    running_tests = (
        "pytest" in os.environ.get("PYTEST_CURRENT_TEST", "")
        or os.environ.get("DAMIEN_TEST_MODE") == "1"
    )

    logger = setup_logging(log_level=log_level, testing_mode=running_tests)

    # Ensure ctx.obj is a dictionary, creating it if it's None.
    # This preserves obj passed from runner.invoke in tests.
    ctx.ensure_object(dict)

    ctx.obj["logger"] = logger
    ctx.obj["config_dir"] = config_dir  # Store custom config dir if provided

    # Attempt to non-interactively load gmail_service if not already set (e.g., by tests)
    if "gmail_service" not in ctx.obj:
        try:
            from damien_cli.core_api.gmail_api_service import (
                get_authenticated_service,
                DamienError,
            )

            # Try to get service non-interactively
            service = get_authenticated_service(interactive_auth_ok=False)
            if service:
                ctx.obj["gmail_service"] = service
                logger.info("Successfully pre-loaded Gmail service non-interactively.")
            else:
                logger.info(
                    "Non-interactive Gmail service pre-load did not return a service. Login may be required."
                )
        except DamienError as e:
            logger.warning(
                f"DamienError during non-interactive service pre-load: {e}. Login may be required."
            )
        except Exception as e:
            logger.warning(
                f"Unexpected error during non-interactive service pre-load: {e}. Login may be required.",
                exc_info=True,
            )
    else:
        logger.debug(
            "gmail_service already present in context (e.g. from test runner). Skipping non-interactive pre-load."
        )

    logger.debug(
        f"Damien CLI started. Verbose: {verbose}, Config Dir: {config_dir}, Testing Mode: {running_tests}, Initial ctx.obj keys: {list(ctx.obj.keys())}"
    )
    logger.debug(
        f"Effective log level: {logging.getLevelName(logger.getEffectiveLevel())}"
    )


# Register command groups from feature slices
damien.add_command(emails_group)
damien.add_command(rules_group)


@damien.command()
@click.pass_context
def hello(ctx):
    """Greets the user."""
    logger = ctx.obj.get(
        "logger", logging.getLogger("damien_cli_fallback")
    )  # Get logger, provide fallback
    logger.info("Executing hello command.")
    click.echo("Damien says: Hello! I'm ready to assist with your Gmail.")
    logger.debug("Hello command finished successfully.")


@damien.command()
@click.pass_context
def login(ctx):
    """Logs into Gmail and ensures authentication token is valid."""
    logger = ctx.obj.get("logger", logging.getLogger("damien_cli_fallback"))
    # Import the core API function for authentication and its specific errors
    from damien_cli.core_api.gmail_api_service import get_authenticated_service
    from damien_cli.core_api.exceptions import DamienError

    if logger:
        logger.info("Attempting Gmail login and service initialization...")
    try:
        service = get_authenticated_service()  # Call the core API function
        if service:
            if logger:
                logger.info("Login successful! Damien is connected to Gmail.")
            click.echo("Login successful! Damien is connected to Gmail.")
            ctx.obj["gmail_service"] = service  # Store the raw Google client here
        else:
            # This path should ideally not be hit if get_authenticated_service raises an error on failure
            if logger:
                logger.error(
                    "Login failed. get_authenticated_service returned None unexpectedly."
                )
            click.secho("Login failed. Could not establish Gmail service.", fg="red")
            # ctx.exit(1) # Consider if exit is appropriate
    except DamienError as e:  # Catch custom errors from your API layer
        if logger:
            logger.error(f"Login failed: {e}", exc_info=True)
        click.secho(
            f"Login failed: {e.message if hasattr(e, 'message') else str(e)}", fg="red"
        )
        # ctx.exit(1)
    except Exception as e:  # Catch any other unexpected error during login
        if logger:
            logger.error(f"Unexpected error during login: {e}", exc_info=True)
        click.secho(f"An unexpected error occurred during login: {e}", fg="red")
        # ctx.exit(1)


# This block is useful if you were to run this script directly (e.g., python cli_entry.py)
# However, with Poetry scripts (`poetry run damien`), this __main__ block isn't the primary entry point.
# It's good practice to keep it for direct script execution testing.
if __name__ == "__main__":
    # When running directly, ctx.obj won't be pre-populated by Click in the same way.
    # We pass an empty dict for obj to avoid errors if subcommands expect ctx.obj.
    damien(obj={})
