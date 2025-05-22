# damien_cli/core_api/exceptions.py
class DamienError(Exception):
    """Base exception for Damien application errors."""

    def __init__(self, message, original_exception=None):  # Add original_exception here
        super().__init__(message)
        self.original_exception = original_exception


class GmailApiError(DamienError):
    """Indicates an error interacting with the Gmail API."""

    # Inherits __init__ from DamienError, so it can also take original_exception
    pass


class RuleNotFoundError(DamienError):
    """Indicates a rule was not found."""

    # Inherits __init__
    pass


class RuleStorageError(DamienError):
    """Indicates an error during rule storage operations."""

    # Inherits __init__
    pass


class InvalidParameterError(DamienError):
    """Indicates an invalid parameter was provided to an API function."""

    # Inherits __init__
    pass
