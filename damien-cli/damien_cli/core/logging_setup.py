import logging
import sys
from pythonjsonlogger import jsonlogger # Added
from . import config  # To get DATA_DIR

LOG_FILE_PATH = config.DATA_DIR / "damien_session.log"
SERVICE_NAME = "damien-cli" # Define service name for logs

# Custom formatter to add more fields
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = record.created # Use record.created for epoch timestamp
        if not log_record.get('level'):
            log_record['level'] = record.levelname
        if not log_record.get('name'):
            log_record['name'] = record.name
        log_record['service_name'] = SERVICE_NAME
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line_number'] = record.lineno


def setup_logging(
    log_level=logging.INFO, testing_mode=False
):  # Added testing_mode back for flexibility
    """Configures JSON logging for the application."""

    logger = logging.getLogger("damien_cli")
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    # JSON Formatter
    # Standard fields: asctime, created, filename, funcName, levelname, levelno, lineno, message, module, msecs, name, pathname, process, processName, relativeCreated, thread, threadName
    # We will use a more structured format.
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(service_name)s %(module)s %(function)s %(line_number)d %(message)s'
    )
    # For a simpler default JSON structure, one could use:
    # formatter = jsonlogger.JsonFormatter()

    if not testing_mode:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    try:
        # DATA_DIR is already created in config.py
        file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Successfully added FileHandler for {LOG_FILE_PATH}") # Explicit success log
    except Exception as e:
        # If logger itself is having issues, print directly as a fallback
        error_message = f"CRITICAL DAMIEN-CLI LOGGING ERROR: Failed to set up FileHandler for {LOG_FILE_PATH}. Error: {e}"
        print(error_message, file=sys.stderr)
        # Still try to log with the logger if parts of it are working, this will go to console if console_handler is up.
        if logger and logger.hasHandlers(): # Check if any handlers (like console) are already there
            logger.critical(error_message, exc_info=True)
        else: # Fallback if logger has no handlers at all yet
            # Basic config to ensure print works if logger is completely unconfigured
            logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
            logging.critical(error_message, exc_info=True)


    # Only log initialization if not in testing mode or if specifically desired
    if not testing_mode or log_level <= logging.DEBUG:  # e.g. log if debug is on
        logger.info(
            f"Logging initialized. Log file: {LOG_FILE_PATH if not testing_mode or logger.hasHandlers() else 'No file handler in this mode'}"
        )

    return logger
