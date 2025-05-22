import logging
import sys
from . import config  # To get DATA_DIR

LOG_FILE_PATH = config.DATA_DIR / "damien_session.log"


def setup_logging(
    log_level=logging.INFO, testing_mode=False
):  # Added testing_mode back for flexibility
    """Configures basic logging for the application."""

    # Create a logger
    logger = logging.getLogger("damien_cli")  # Get the root logger for our app
    logger.setLevel(log_level)  # Set the minimum level of messages to handle

    # Prevent multiple handlers if setup_logging is called more than once
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter - defines how log messages will look
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    )

    # Console Handler - to print logs to the screen
    # Conditionally add console handler based on testing_mode
    if not testing_mode:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File Handler - to write logs to a file
    try:
        file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a")  # 'a' for append
        file_handler.setLevel(
            log_level
        )  # Log everything at this level and above to file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If logger itself is having issues, print directly as a fallback
        print(f"CRITICAL LOGGING ERROR during file_handler setup: {e}", file=sys.stderr)
        # Still try to log with the logger if parts of it are working
        if logger:
            logger.error(
                f"Failed to set up file handler for logging: {e}", exc_info=True
            )

    # Only log initialization if not in testing mode or if specifically desired
    if not testing_mode or log_level <= logging.DEBUG:  # e.g. log if debug is on
        logger.info(
            f"Logging initialized. Log file: {LOG_FILE_PATH if not testing_mode or logger.hasHandlers() else 'No file handler in this mode'}"
        )

    return logger
