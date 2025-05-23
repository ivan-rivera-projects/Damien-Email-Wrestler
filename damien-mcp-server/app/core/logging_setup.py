import logging
import sys
from pythonjsonlogger import jsonlogger
from .config import settings # To potentially get log level or log file path if defined in settings

# Define service name for logs
SERVICE_NAME = "damien-mcp-server" 
LOG_FILE_PATH = settings.log_file_path if hasattr(settings, 'log_file_path') and settings.log_file_path else None # Example: get from settings

# Custom formatter to add more fields
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        # python-json-logger can automatically add timestamp, level, name if configured in the format string
        # or via reserved_attrs. For simplicity, let's rely on its defaults or format string.
        # If we want to force specific keys:
        log_record['timestamp_epoch'] = record.created
        log_record['level_name'] = record.levelname
        log_record['logger_name'] = record.name
        log_record['service_name'] = SERVICE_NAME # Already set this
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line_number'] = record.lineno
        # The main format string will determine which of these are rendered if not using default JsonFormatter output
        # The default JsonFormatter will include many of these if they are in log_record.
        # Let's simplify the format string and let JsonFormatter do more work.
        if not log_record.get('level'): # Ensure 'level' (standard key) is present
             log_record['level'] = record.levelname.upper()
        if not log_record.get('name'):
            log_record['name'] = record.name # Logger name
        log_record['service_name'] = SERVICE_NAME
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line_number'] = record.lineno
        # Could add request_id, session_id etc. here if passed via LogRecord's extra
        # For FastAPI, this might be better handled by middleware adding to context


def setup_logging(log_level_str: str = "INFO"):
    """Configures JSON logging for the Damien MCP Server application."""
    
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Configure root logger - FastAPI/Uvicorn might have their own handlers.
    # We are primarily configuring loggers obtained via logging.getLogger(__name__)
    # or logging.getLogger("damien_mcp_server")
    
    # Get a specific logger for the application to avoid interfering with uvicorn's root logger setup
    app_logger = logging.getLogger("damien_mcp_server_app") # Specific logger for app messages
    app_logger.setLevel(log_level)
    app_logger.propagate = False # Prevent messages from going to the root logger if uvicorn has its own formatting

    if app_logger.hasHandlers():
        app_logger.handlers.clear()

    # Simplified format string; python-json-logger will add standard fields.
    # We can add more required fields in add_fields or ensure they are in reserved_attrs.
    # For a typical JSON log, we often don't need a complex format string here,
    # as JsonFormatter structures the output.
    # Let's use the default formatter capabilities more.
    formatter = CustomJsonFormatter()
    # Example of a format string that python-json-logger understands for specific fields:
    # formatter = CustomJsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')


    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    if LOG_FILE_PATH:
        try:
            # Ensure log directory exists if LOG_FILE_PATH is complex
            from pathlib import Path # Make sure Path is imported
            log_path_obj = Path(LOG_FILE_PATH)
            log_path_obj.parent.mkdir(parents=True, exist_ok=True) # Create directory
            
            file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            app_logger.addHandler(file_handler)
            app_logger.info(f"MCP Server file logging configured at {LOG_FILE_PATH}.")
        except Exception as e:
            app_logger.error(f"Failed to set up file handler for MCP server logging: {e}", exc_info=True)
            print(f"CRITICAL MCP LOGGING ERROR during file_handler setup: {e}", file=sys.stderr)
            
    # To make uvicorn access logs use this format, its access logger needs to be configured.
    # This setup primarily affects logs made via logging.getLogger("damien_mcp_server_app")
    # or loggers that are children of it.

    # Example of how to get this logger elsewhere:
    # import logging
    # logger = logging.getLogger("damien_mcp_server_app")
    # logger.info("This is a test from another module")

    app_logger.info(f"Damien MCP Server application logging initialized with level {log_level_str.upper()}.")
    return app_logger

# If you want to try and configure uvicorn's loggers too (more complex):
# UVICORN_ACCESS_LOGGER_NAME = "uvicorn.access"
# UVICORN_ERROR_LOGGER_NAME = "uvicorn.error"

# def setup_uvicorn_logging(log_level_str: str = "INFO"):
#     log_level = getattr(logging, log_level_str.upper(), logging.INFO)
#     formatter = CustomJsonFormatter(...)
    
#     access_logger = logging.getLogger(UVICORN_ACCESS_LOGGER_NAME)
#     access_logger.handlers.clear()
#     access_logger.propagate = False
#     console_access_handler = logging.StreamHandler(sys.stdout)
#     console_access_handler.setFormatter(formatter)
#     access_logger.addHandler(console_access_handler)
#     access_logger.setLevel(log_level)

    # error_logger = logging.getLogger(UVICORN_ERROR_LOGGER_NAME)
    # ... similar setup for error logger if needed ...