"""Rate limiting decorator for Gmail API calls."""

import time
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

# Default rate limiting settings
DEFAULT_RATE_LIMIT_DELAY = 0.1  # 100ms delay between API calls
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 2


def with_rate_limiting(func: Callable = None, *, 
                      delay: float = DEFAULT_RATE_LIMIT_DELAY,
                      max_retries: int = DEFAULT_MAX_RETRIES,
                      backoff_factor: float = DEFAULT_BACKOFF_FACTOR) -> Callable:
    """
    Decorator to add rate limiting and retry logic to Gmail API calls.
    
    Can be used as @with_rate_limiting or @with_rate_limiting(delay=0.5)
    
    Args:
        func: Function to decorate (when used without parentheses)
        delay: Base delay between API calls in seconds
        max_retries: Maximum number of retries on rate limit errors
        backoff_factor: Exponential backoff multiplier
        
    Returns:
        Decorated function with rate limiting
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Add delay before API call (except first attempt)
                    if attempt > 0:
                        sleep_time = delay * (backoff_factor ** (attempt - 1))
                        logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s before retry {attempt}")
                        time.sleep(sleep_time)
                    
                    # Execute the function
                    result = f(*args, **kwargs)
                    
                    # Add delay after successful call to prevent rate limiting
                    if delay > 0:
                        time.sleep(delay)
                    
                    return result
                    
                except Exception as e: # Catch all exceptions first
                    last_exception = e
                    
                    # Import HttpError and DamienError locally to avoid circular dependency if this file is imported early
                    from googleapiclient.errors import HttpError
                    from .exceptions import DamienError # Assuming exceptions.py is in the same directory or accessible

                    # If it's a DamienError subclass (like InvalidParameterError) but NOT an HttpError,
                    # re-raise it immediately as it's not an API communication issue for retrying.
                    if isinstance(e, DamienError) and not isinstance(e, HttpError):
                        logger.debug(f"Propagating DamienError: {type(e).__name__}('{str(e)}')")
                        raise

                    # Check if this is a retryable HttpError (rate limit or server error)
                    if isinstance(e, HttpError) and hasattr(e, 'resp') and hasattr(e.resp, 'status'):
                        if e.resp.status == 429:  # Too Many Requests
                            logger.warning(f"Rate limit hit (429) on attempt {attempt + 1} for {f.__name__}, retrying...")
                            if attempt < max_retries:
                                continue # Go to next attempt
                            else:
                                logger.error(f"Max retries for rate limit exceeded for {f.__name__}.")
                                # Fall through to raise last_exception
                        elif e.resp.status >= 500:  # Server errors
                            logger.warning(f"Server error ({e.resp.status}) on attempt {attempt + 1} for {f.__name__}, retrying...")
                            if attempt < max_retries:
                                continue # Go to next attempt
                            else:
                                logger.error(f"Max retries for server error exceeded for {f.__name__}.")
                                # Fall through to raise last_exception
                    
                    # For any other exceptions, or if retries are exhausted for HttpErrors, re-raise.
                    # This ensures non-HttpErrors or non-retryable HttpErrors are raised immediately on first attempt,
                    # or after all retries for retryable HttpErrors.
                    logger.debug(f"Non-retryable/exhausted retry for {type(e).__name__} in {f.__name__} on attempt {attempt + 1}. Raising.")
                    raise
            
            # If we've exhausted all retries, raise the last exception
            logger.error(f"Max retries ({max_retries}) exceeded for {f.__name__}")
            raise last_exception
            
        return wrapper
    
    # Handle both @with_rate_limiting and @with_rate_limiting(...) usage
    if func is None:
        # Called with arguments: @with_rate_limiting(delay=0.5)
        return decorator
    else:
        # Called without arguments: @with_rate_limiting
        return decorator(func)
