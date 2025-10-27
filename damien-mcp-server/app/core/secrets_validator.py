"""
Secrets validation module for Damien MCP Server.

This module ensures all required secrets are present before the application starts,
preventing runtime failures due to missing configuration.
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SecretsValidationError(Exception):
    """Raised when required secrets are missing or invalid."""
    pass


class SecretsValidator:
    """Validates that all required secrets are present and valid."""

    # Required secrets for core functionality
    REQUIRED_SECRETS = [
        'DAMIEN_MCP_SERVER_API_KEY',
        'DAMIEN_GMAIL_TOKEN_JSON_PATH',
        'DAMIEN_GMAIL_CREDENTIALS_JSON_PATH',
    ]

    # Optional secrets (warn if missing, but don't fail)
    OPTIONAL_SECRETS = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'GEMINI_API_KEY',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
    ]

    # Minimum length requirements for API keys
    MIN_KEY_LENGTHS = {
        'DAMIEN_MCP_SERVER_API_KEY': 32,
        'OPENAI_API_KEY': 20,
        'ANTHROPIC_API_KEY': 20,
        'GEMINI_API_KEY': 20,
    }

    @classmethod
    def validate_all(cls, strict: bool = True) -> Dict[str, str]:
        """
        Validate all required secrets are present.

        Args:
            strict: If True, raise exception for missing required secrets.
                   If False, only log warnings.

        Returns:
            Dictionary of validated secrets

        Raises:
            SecretsValidationError: If required secrets are missing (when strict=True)
        """
        missing_required = []
        missing_optional = []
        invalid_secrets = []
        validated_secrets = {}

        # Check required secrets
        for secret_name in cls.REQUIRED_SECRETS:
            value = os.getenv(secret_name)

            if not value:
                missing_required.append(secret_name)
                continue

            # Validate length if requirement exists
            min_length = cls.MIN_KEY_LENGTHS.get(secret_name)
            if min_length and len(value) < min_length:
                invalid_secrets.append(
                    f"{secret_name} (length: {len(value)}, required: >={min_length})"
                )
                continue

            validated_secrets[secret_name] = value

        # Check optional secrets
        for secret_name in cls.OPTIONAL_SECRETS:
            value = os.getenv(secret_name)

            if not value:
                missing_optional.append(secret_name)
            else:
                # Validate length if requirement exists
                min_length = cls.MIN_KEY_LENGTHS.get(secret_name)
                if min_length and len(value) < min_length:
                    logger.warning(
                        f"Optional secret {secret_name} is present but too short "
                        f"(length: {len(value)}, expected: >={min_length})"
                    )
                else:
                    validated_secrets[secret_name] = value

        # Report findings
        if missing_required:
            error_msg = (
                f"❌ CRITICAL: Missing required secrets:\n"
                f"   {', '.join(missing_required)}\n"
                f"   Please set these in your .env file or environment"
            )
            if strict:
                logger.error(error_msg)
                raise SecretsValidationError(error_msg)
            else:
                logger.warning(error_msg)

        if invalid_secrets:
            error_msg = (
                f"❌ CRITICAL: Invalid secrets (too short):\n"
                f"   {', '.join(invalid_secrets)}"
            )
            if strict:
                logger.error(error_msg)
                raise SecretsValidationError(error_msg)
            else:
                logger.warning(error_msg)

        if missing_optional:
            logger.warning(
                f"⚠️  Optional secrets not configured: {', '.join(missing_optional)}\n"
                f"   Some features may be unavailable"
            )

        # Log success
        logger.info(
            f"✅ Secrets validation passed: "
            f"{len(validated_secrets)}/{len(cls.REQUIRED_SECRETS) + len(cls.OPTIONAL_SECRETS)} configured"
        )

        return validated_secrets

    @classmethod
    def validate_file_paths(cls) -> Dict[str, Path]:
        """
        Validate that all file paths exist and are accessible.

        Returns:
            Dictionary of validated file paths

        Raises:
            SecretsValidationError: If required files are missing or not accessible
        """
        file_paths = {
            'gmail_token': os.getenv('DAMIEN_GMAIL_TOKEN_JSON_PATH'),
            'gmail_credentials': os.getenv('DAMIEN_GMAIL_CREDENTIALS_JSON_PATH'),
        }

        missing_files = []
        validated_paths = {}

        for name, path_str in file_paths.items():
            if not path_str:
                missing_files.append(f"{name} (environment variable not set)")
                continue

            path = Path(path_str)

            # For token file, it might not exist yet (created on first auth)
            if name == 'gmail_token' and not path.exists():
                logger.warning(
                    f"⚠️  Gmail token file not found at {path}\n"
                    f"   This is normal on first run - will be created after authentication"
                )
                validated_paths[name] = path
                continue

            # For credentials file, it must exist
            if not path.exists():
                missing_files.append(f"{name} at {path}")
                continue

            if not path.is_file():
                missing_files.append(f"{name} at {path} (not a file)")
                continue

            validated_paths[name] = path

        if missing_files:
            error_msg = (
                f"❌ CRITICAL: Missing or invalid files:\n"
                f"   {', '.join(missing_files)}"
            )
            logger.error(error_msg)
            raise SecretsValidationError(error_msg)

        logger.info(f"✅ File paths validation passed: {len(validated_paths)} files validated")
        return validated_paths

    @classmethod
    def mask_secret(cls, secret: str, visible_chars: int = 4) -> str:
        """
        Mask a secret for logging purposes.

        Args:
            secret: The secret to mask
            visible_chars: Number of characters to show at start

        Returns:
            Masked secret string
        """
        if not secret or len(secret) <= visible_chars:
            return '***'
        return f"{secret[:visible_chars]}{'*' * (len(secret) - visible_chars)}"

    @classmethod
    def log_secret_status(cls) -> None:
        """Log the status of all secrets (masked) for debugging."""
        logger.info("🔐 Secrets Status:")

        for secret_name in cls.REQUIRED_SECRETS:
            value = os.getenv(secret_name)
            if value:
                masked = cls.mask_secret(value)
                logger.info(f"   ✅ {secret_name}: {masked} (length: {len(value)})")
            else:
                logger.warning(f"   ❌ {secret_name}: NOT SET")

        for secret_name in cls.OPTIONAL_SECRETS:
            value = os.getenv(secret_name)
            if value:
                masked = cls.mask_secret(value)
                logger.info(f"   ✅ {secret_name}: {masked} (length: {len(value)})")
            else:
                logger.debug(f"   ⚪ {secret_name}: not configured (optional)")


def validate_secrets_on_startup(strict: bool = True, settings_obj=None) -> Dict[str, str]:
    """
    Convenience function to validate secrets on application startup.

    This should be called early in the application lifecycle, before
    any services are initialized.

    Args:
        strict: If True, raise exception for missing secrets
        settings_obj: Optional Pydantic Settings object to validate against.
                     If not provided, falls back to os.getenv()

    Returns:
        Dictionary of validated secrets

    Raises:
        SecretsValidationError: If validation fails
    """
    logger.info("=" * 80)
    logger.info("🔐 SECRETS VALIDATION STARTING")
    logger.info("=" * 80)

    try:
        # If settings object provided, validate directly from it
        if settings_obj:
            logger.info("✅ Using Pydantic Settings for validation")
            validated_secrets = {
                'DAMIEN_MCP_SERVER_API_KEY': settings_obj.api_key,
                'DAMIEN_GMAIL_TOKEN_JSON_PATH': settings_obj.gmail_token_path,
                'DAMIEN_GMAIL_CREDENTIALS_JSON_PATH': settings_obj.gmail_credentials_path,
            }

            # Check for empty values
            missing = [k for k, v in validated_secrets.items() if not v]
            if missing and strict:
                error_msg = (
                    f"❌ CRITICAL: Missing or empty required settings:\n"
                    f"   {', '.join(missing)}\n"
                    f"   Please set these in your .env file"
                )
                logger.error(error_msg)
                raise SecretsValidationError(error_msg)

            # Validate file paths using settings
            import os
            from pathlib import Path
            if settings_obj.gmail_credentials_path:
                cred_path = Path(settings_obj.gmail_credentials_path)
                if not cred_path.exists():
                    error_msg = f"❌ CRITICAL: Gmail credentials file not found at {cred_path}"
                    logger.error(error_msg)
                    if strict:
                        raise SecretsValidationError(error_msg)

            logger.info(f"✅ Settings validation passed: {len([v for v in validated_secrets.values() if v])}/{len(validated_secrets)} configured")

        else:
            # Fall back to os.getenv() validation
            secrets = SecretsValidator.validate_all(strict=strict)
            file_paths = SecretsValidator.validate_file_paths()
            SecretsValidator.log_secret_status()
            validated_secrets = secrets

        logger.info("=" * 80)
        logger.info("✅ SECRETS VALIDATION PASSED")
        logger.info("=" * 80)

        return validated_secrets

    except SecretsValidationError as e:
        logger.error("=" * 80)
        logger.error("❌ SECRETS VALIDATION FAILED")
        logger.error("=" * 80)
        raise


# Convenience export
__all__ = ['SecretsValidator', 'SecretsValidationError', 'validate_secrets_on_startup']
