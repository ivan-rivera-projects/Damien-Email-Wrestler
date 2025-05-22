import click
import logging

# Get a logger instance for this utility module
logger = logging.getLogger(__name__)

from typing import Tuple

def _confirm_action(
    prompt_message: str,
    yes_flag: bool,
    default_abort_message: str = "Action aborted by user.",
    log_confirmation_bypass: bool = True
) -> Tuple[bool, str]:
    """
    Prompts user for confirmation or bypasses if yes_flag is True.
    Returns a tuple: (bool_confirmed_or_bypassed, message_to_display_or_log).
    """
    if yes_flag:
        bypass_message = f"Confirmation bypassed by --yes flag for: {prompt_message}"
        if log_confirmation_bypass and logger:
             logger.info(f"Confirmation bypassed by --yes flag for prompt: '{prompt_message}'")
        return True, bypass_message  # Confirmed by bypass, return bypass message

    # Original interactive confirmation
    if not click.confirm(prompt_message, default=False, abort=False):
        if logger:
            logger.info(f"User aborted action for prompt: '{prompt_message}'")
        return False, default_abort_message # Not confirmed, return abort message
    
    if logger:
        logger.info(f"User confirmed action for prompt: '{prompt_message}'")
    return True, "" # Confirmed by user, no specific message needed from here