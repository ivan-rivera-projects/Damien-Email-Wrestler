"""
Module docstring explaining purpose and usage.

This module implements the ConsentManager, responsible for managing user
consent for various data processing activities within the Damien AI
Email Intelligence Layer. It ensures that data is processed in
accordance with user permissions and regulatory requirements (e.g., GDPR).

Example:
    >>> from damien_cli.features.ai_intelligence.llm_integration.privacy.consent import ConsentManager, DataProcessingPurpose
    >>> consent_manager = ConsentManager()
    >>> user_id = "user_abc_123"
    >>> # Grant consent
    >>> consent_manager.grant_consent(user_id, DataProcessingPurpose.EMAIL_ANALYSIS)
    >>> consent_manager.grant_consent(user_id, DataProcessingPurpose.PII_DETECTION, {"duration_days": 30})
    >>> # Check consent
    >>> can_analyze = consent_manager.check_consent(user_id, DataProcessingPurpose.EMAIL_ANALYSIS)
    >>> print(f"Can analyze email for {user_id}: {can_analyze}")
    >>> # Revoke consent
    >>> consent_manager.revoke_consent(user_id, DataProcessingPurpose.EMAIL_ANALYSIS)
    >>> can_analyze_after_revoke = consent_manager.check_consent(user_id, DataProcessingPurpose.EMAIL_ANALYSIS)
    >>> print(f"Can analyze email for {user_id} after revoke: {can_analyze_after_revoke}")

Note:
    This is a simplified in-memory implementation for demonstration.
    A production ConsentManager would integrate with a persistent database
    to store consent records, manage expiration, and handle versioning
    of consent policies. It would also need to integrate with the
    ComplianceAuditLogger for all consent changes.
"""
import datetime
from typing import Dict, Any, Optional, Set
from enum import Enum

# Assuming ComplianceAuditLogger might be used here.
from .audit import ComplianceAuditLogger 

class DataProcessingPurpose(Enum):
    """
    Defines common purposes for which user consent might be required.
    These should be granular and clearly explained to the user.
    """
    EMAIL_ANALYSIS = "EMAIL_ANALYSIS" # General analysis of email content
    PII_DETECTION = "PII_DETECTION"   # Specifically detecting PII
    LLM_ENHANCEMENT = "LLM_ENHANCEMENT" # Using LLMs to enhance email data
    DATA_RETENTION_RAW = "DATA_RETENTION_RAW" # Retaining raw email data
    DATA_RETENTION_PROCESSED = "DATA_RETENTION_PROCESSED" # Retaining processed/derived data
    THIRD_PARTY_SHARING_ANONYMIZED = "THIRD_PARTY_SHARING_ANONYMIZED" # Sharing anonymized data
    # Add more specific purposes as needed

class ConsentRecord(Dict[DataProcessingPurpose, Dict[str, Any]]):
    """
    Represents the consent status for a user for various processing purposes.
    The inner dictionary stores metadata like grant date, expiry date, etc.
    Example:
    {
        DataProcessingPurpose.EMAIL_ANALYSIS: {"granted_at": "...", "expires_at": "...", "status": True},
        DataProcessingPurpose.PII_DETECTION: {"granted_at": "...", "status": False}
    }
    """
    pass


class ConsentManager:
    """
    Manages user consent for data processing activities.

    This class provides functionalities to:
    - Record user consent for specific data processing purposes.
    - Check if consent has been given for a particular purpose.
    - Allow users to revoke their consent.
    - Manage consent lifecycle (e.g., expiration).

    In a production system, this would be backed by a persistent database.
    """

    def __init__(self, audit_logger: Optional[ComplianceAuditLogger] = None):
        """
        Initializes the ConsentManager.

        Args:
            audit_logger (Optional[ComplianceAuditLogger]): An instance of the audit logger
                                                            to record consent changes.
        """
        # In-memory store for consents: {user_id: ConsentRecord}
        self._consents: Dict[str, ConsentRecord] = {}
        self.audit_logger = audit_logger

    def _log_consent_change(self, user_id: str, purpose: DataProcessingPurpose, action: str, details: Optional[Dict[str, Any]] = None):
        """Helper to log consent changes if an audit_logger is available."""
        if self.audit_logger:
            log_details = {
                "purpose": purpose.value,
                "action": action,
                **(details if details else {})
            }
            self.audit_logger.log_event(
                event_type="CONSENT_CHANGE",
                user_id=user_id,
                details=log_details,
                status="SUCCESS",
                component="ConsentManager"
            )

    def grant_consent(
        self,
        user_id: str,
        purpose: DataProcessingPurpose,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Records that a user has granted consent for a specific purpose.

        Args:
            user_id (str): The unique identifier for the user.
            purpose (DataProcessingPurpose): The purpose for which consent is granted.
            metadata (Optional[Dict[str, Any]]): Additional metadata, e.g.,
                                                 consent duration, version of policy.
                                                 Example: {"duration_days": 365, "policy_version": "1.2"}

        Returns:
            bool: True if consent was successfully recorded, False otherwise.
        """
        if user_id not in self._consents:
            self._consents[user_id] = ConsentRecord()

        grant_time = datetime.datetime.utcnow()
        consent_details = {
            "status": True,
            "granted_at": grant_time.isoformat() + "Z",
            **(metadata if metadata else {})
        }

        if "duration_days" in consent_details:
            duration = datetime.timedelta(days=consent_details["duration_days"])
            consent_details["expires_at"] = (grant_time + duration).isoformat() + "Z"

        self._consents[user_id][purpose] = consent_details
        self._log_consent_change(user_id, purpose, "GRANT", consent_details)
        return True

    def revoke_consent(self, user_id: str, purpose: DataProcessingPurpose) -> bool:
        """
        Records that a user has revoked consent for a specific purpose.

        Args:
            user_id (str): The unique identifier for the user.
            purpose (DataProcessingPurpose): The purpose for which consent is revoked.

        Returns:
            bool: True if consent was successfully revoked or was not granted, False otherwise.
        """
        if user_id in self._consents and purpose in self._consents[user_id]:
            self._consents[user_id][purpose]["status"] = False
            self._consents[user_id][purpose]["revoked_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            self._log_consent_change(user_id, purpose, "REVOKE", {"revoked_at": self._consents[user_id][purpose]["revoked_at"]})
            return True
        # If consent was never granted, or user not found, consider it "revoked" in effect.
        self._log_consent_change(user_id, purpose, "REVOKE_NO_PRIOR_GRANT")
        return True

    def check_consent(self, user_id: str, purpose: DataProcessingPurpose) -> bool:
        """
        Checks if a user has given active consent for a specific purpose.

        Args:
            user_id (str): The unique identifier for the user.
            purpose (DataProcessingPurpose): The purpose to check consent for.

        Returns:
            bool: True if active consent is found, False otherwise.
        """
        user_consent_record = self._consents.get(user_id)
        if not user_consent_record:
            return False

        purpose_consent = user_consent_record.get(purpose)
        if not purpose_consent or not purpose_consent.get("status", False):
            return False

        # Check for expiration
        expires_at_str = purpose_consent.get("expires_at")
        if expires_at_str:
            try:
                # Ensure correct parsing of ISO format string, potentially with 'Z'
                if expires_at_str.endswith('Z'):
                    expires_at = datetime.datetime.fromisoformat(expires_at_str[:-1] + '+00:00')
                else:
                    expires_at = datetime.datetime.fromisoformat(expires_at_str)
                
                if datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) > expires_at:
                    return False # Expired
            except ValueError:
                self._log_consent_change(user_id, purpose, "EXPIRY_DATE_INVALID_FORMAT")
                return False


        return True # Active consent found

    def get_user_consents(self, user_id: str) -> Optional[ConsentRecord]:
        """
        Retrieves all consent records for a given user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            Optional[ConsentRecord]: The user's consent records, or None if user not found.
        """
        return self._consents.get(user_id)

    def clear_all_consents(self):
        """
        Clears all consent records from the manager.
        USE WITH CAUTION. Primarily for testing or specific data lifecycle events.
        """
        self._consents.clear()
        if self.audit_logger:
             self.audit_logger.log_event(event_type="ALL_CONSENTS_CLEARED", status="WARNING", component="ConsentManager")
        print("WARNING: All consent records have been cleared.")


if __name__ == '__main__':
    # Example Usage
    audit_logger_instance = ComplianceAuditLogger(log_to_console=True)
    consent_manager = ConsentManager(audit_logger=audit_logger_instance)

    user1 = "user_001"
    user2 = "user_002"

    # Granting consents
    consent_manager.grant_consent(user1, DataProcessingPurpose.EMAIL_ANALYSIS)
    consent_manager.grant_consent(user1, DataProcessingPurpose.PII_DETECTION, {"duration_days": 1})
    consent_manager.grant_consent(user2, DataProcessingPurpose.LLM_ENHANCEMENT, {"policy_version": "2.0"})

    print(f"User1 EMAIL_ANALYSIS consent: {consent_manager.check_consent(user1, DataProcessingPurpose.EMAIL_ANALYSIS)}")
    print(f"User1 PII_DETECTION consent: {consent_manager.check_consent(user1, DataProcessingPurpose.PII_DETECTION)}")
    print(f"User1 LLM_ENHANCEMENT consent: {consent_manager.check_consent(user1, DataProcessingPurpose.LLM_ENHANCEMENT)}") 
    print(f"User2 LLM_ENHANCEMENT consent: {consent_manager.check_consent(user2, DataProcessingPurpose.LLM_ENHANCEMENT)}")

    # Revoking consent
    consent_manager.revoke_consent(user1, DataProcessingPurpose.EMAIL_ANALYSIS)
    print(f"\nUser1 EMAIL_ANALYSIS consent after revoke: {consent_manager.check_consent(user1, DataProcessingPurpose.EMAIL_ANALYSIS)}")
    
    if user1 in consent_manager._consents and DataProcessingPurpose.PII_DETECTION in consent_manager._consents[user1]:
        two_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        consent_manager._consents[user1][DataProcessingPurpose.PII_DETECTION]["expires_at"] = two_days_ago.isoformat() + "Z"
        print(f"User1 PII_DETECTION consent (after manually expiring): {consent_manager.check_consent(user1, DataProcessingPurpose.PII_DETECTION)}")


    print(f"\nAll consents for {user1}: {consent_manager.get_user_consents(user1)}")
    
    consent_manager.clear_all_consents()
    print(f"\nUser1 consents after clear all: {consent_manager.get_user_consents(user1)}")