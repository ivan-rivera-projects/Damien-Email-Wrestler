import logging
import sys
from damien_cli.core.config import settings

def get_logger(name: str, level: str = None) -> logging.Logger:
    """
    Configures and returns a logger instance.
    """
    if level is None:
        level = settings.LOG_LEVEL

    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers if logger already configured
    if not logger.handlers:
        # Ensure level is a valid attribute of logging module
        log_level_attr = getattr(logging, level.upper(), None)
        if log_level_attr is None:
            print(f"Warning: Invalid LOG_LEVEL '{level}' in app_logging.py. Defaulting to INFO.")
            log_level_attr = logging.INFO
        
        logger.setLevel(log_level_attr)
        
        # Create console handler and set level
        ch = logging.StreamHandler(sys.stdout)
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
