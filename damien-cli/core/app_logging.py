import logging # This will now correctly import the standard library logging
import sys
from damien_cli.core.config import settings # Import settings to use LOG_LEVEL

def get_logger(name: str, level: str = None) -> logging.Logger:
    """
    Configures and returns a logger instance.
    """
    if level is None:
        level = settings.LOG_LEVEL

    logger = logging.getLogger(name) # Uses standard library logging.getLogger
    
    # Prevent adding multiple handlers if logger already configured
    if not logger.handlers:
        # Ensure level is a valid attribute of logging module
        log_level_attr = getattr(logging, level.upper(), None)
        if log_level_attr is None:
            print(f"Warning: Invalid LOG_LEVEL '{level}' in app_logging.py. Defaulting to INFO.")
            log_level_attr = logging.INFO
        
        logger.setLevel(log_level_attr)
        
        # Create console handler and set level
        ch = logging.StreamHandler(sys.stdout) # Output to stdout
        ch.setLevel(log_level_attr)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add formatter to ch
        ch.setFormatter(formatter)
        
        # Add ch to logger
        logger.addHandler(ch)
        
    return logger

# Example of a default application logger (optional)
# app_logger = get_logger("damien_cli_app")

if __name__ == '__main__':
    # Example usage:
    # Note: config import might cause issues if run directly due to its own imports,
    # but this block is for direct execution testing of app_logging.py itself.
    # For this to run standalone, config.py must be runnable standalone.
    try:
        from damien_cli.core.config import settings as s_test
        print(f"Configured LOG_LEVEL from settings: {s_test.LOG_LEVEL}")
        
        logger1 = get_logger("my_module_test", level="DEBUG")
        logger1.debug("This is a debug message from my_module_test.")
        logger1.info("This is an info message from my_module_test.")

        logger2 = get_logger("another_module_test") # Uses LOG_LEVEL from settings
        logger2.info("This is an info message from another_module_test.")
        logger2.warning("This is a warning message from another_module_test.")
    except ImportError:
        print("Could not import settings for __main__ block in app_logging.py. Run config.py directly to test settings.")
    except Exception as e:
        print(f"Error in app_logging.py __main__: {e}")