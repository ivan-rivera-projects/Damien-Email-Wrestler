# Privacy-First Security Design for Damien AI Rules Engine

## Overview
Enterprise-grade security architecture with zero-trust principles, end-to-end encryption, and GDPR/CCPA compliance for AI-powered email management.

## 1. Core Security Principles

### Privacy-First Architecture

```python
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import hashlib
import json
from datetime import datetime, timedelta

class DataClassification(Enum):
    """Data sensitivity classification levels"""
    PUBLIC = "public"                    # Non-sensitive data
    INTERNAL = "internal"               # Internal business data
    CONFIDENTIAL = "confidential"      # Sensitive business data
    RESTRICTED = "restricted"          # Highly sensitive/PII data

class ProcessingPurpose(Enum):
    """Lawful basis for data processing under GDPR"""
    CONSENT = "consent"                 # User explicit consent
    CONTRACT = "contract"              # Contract performance
    LEGAL_OBLIGATION = "legal_obligation"  # Legal requirement
    VITAL_INTERESTS = "vital_interests"    # Life/safety protection
    PUBLIC_TASK = "public_task"           # Public interest task
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Legitimate business interests

@dataclass
class DataElement:
    """Individual data element with privacy metadata"""
    field_name: str
    classification: DataClassification
    processing_purpose: ProcessingPurpose
    retention_period_days: int
    encryption_required: bool
    pii_detected: bool
    consent_required: bool
    can_be_anonymized: bool
    geographic_restrictions: List[str] = None
    
    def __post_init__(self):
        if self.geographic_restrictions is None:
            self.geographic_restrictions = []

# Privacy configuration for different data types
PRIVACY_SCHEMA = {
    "email_metadata": {
        "gmail_message_id": DataElement(
            field_name="gmail_message_id",
            classification=DataClassification.INTERNAL,
            processing_purpose=ProcessingPurpose.CONTRACT,
            retention_period_days=365,
            encryption_required=True,
            pii_detected=False,
            consent_required=False,
            can_be_anonymized=True
        ),
        "subject_hash": DataElement(
            field_name="subject_hash",
            classification=DataClassification.CONFIDENTIAL,
            processing_purpose=ProcessingPurpose.LEGITIMATE_INTERESTS,
            retention_period_days=90,
            encryption_required=True,
            pii_detected=False,
            consent_required=True,
            can_be_anonymized=False
        ),
        "sender_domain": DataElement(
            field_name="sender_domain",
            classification=DataClassification.INTERNAL,
            processing_purpose=ProcessingPurpose.LEGITIMATE_INTERESTS,
            retention_period_days=180,
            encryption_required=False,
            pii_detected=False,
            consent_required=False,
            can_be_anonymized=True
        ),
        "content_features": DataElement(
            field_name="content_features",
            classification=DataClassification.CONFIDENTIAL,
            processing_purpose=ProcessingPurpose.LEGITIMATE_INTERESTS,
            retention_period_days=30,
            encryption_required=True,
            pii_detected=False,
            consent_required=True,
            can_be_anonymized=True
        )
    },
    "user_profile": {
        "email": DataElement(
            field_name="email",
            classification=DataClassification.RESTRICTED,
            processing_purpose=ProcessingPurpose.CONTRACT,
            retention_period_days=2555,  # 7 years for business records
            encryption_required=True,
            pii_detected=True,
            consent_required=True,
            can_be_anonymized=False,
            geographic_restrictions=["EU", "UK", "CA"]
        ),
        "gmail_account": DataElement(
            field_name="gmail_account",
            classification=DataClassification.RESTRICTED,
            processing_purpose=ProcessingPurpose.CONTRACT,
            retention_period_days=2555,
            encryption_required=True,
            pii_detected=True,
            consent_required=True,
            can_be_anonymized=False
        ),
        "preferences": DataElement(
            field_name="preferences",
            classification=DataClassification.INTERNAL,
            processing_purpose=ProcessingPurpose.LEGITIMATE_INTERESTS,
            retention_period_days=365,
            encryption_required=False,
            pii_detected=False,
            consent_required=False,
            can_be_anonymized=True
        )
    }
}
```

## 2. Zero-Trust Security Framework

### Identity and Access Management

```python
class ZeroTrustAccessControl:
    """Zero-trust access control for all system components"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.access_policies = self._load_access_policies()
        
    def validate_access_request(self, 
                              principal: str,
                              resource: str, 
                              action: str,
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate access request using zero-trust principles"""
        
        validation_result = {
            "allowed": False,
            "reason": "",
            "conditions": [],
            "audit_required": True,
            "risk_score": 0.0
        }
        
        # 1. Verify principal identity
        identity_verification = self._verify_identity(principal, context)
        if not identity_verification["verified"]:
            validation_result["reason"] = "Identity verification failed"
            return validation_result
        
        # 2. Check device trust
        device_trust = self._assess_device_trust(context)
        if device_trust["risk_score"] > 0.7:
            validation_result["reason"] = "Device trust score too high"
            validation_result["risk_score"] = device_trust["risk_score"]
            return validation_result
        
        # 3. Evaluate location and network
        location_assessment = self._assess_location_risk(context)
        if location_assessment["blocked"]:
            validation_result["reason"] = "Location blocked"
            return validation_result
        
        # 4. Check resource permissions
        resource_permission = self._check_resource_permission(principal, resource, action)
        if not resource_permission["allowed"]:
            validation_result["reason"] = resource_permission["reason"]
            return validation_result
        
        # 5. Apply time-based restrictions
        time_restriction = self._check_time_restrictions(principal, action, context)
        if not time_restriction["allowed"]:
            validation_result["reason"] = time_restriction["reason"]
            return validation_result
        
        # 6. Calculate overall risk score
        overall_risk = self._calculate_risk_score(
            identity_verification, device_trust, location_assessment, context
        )
        
        # 7. Apply risk-based controls
        if overall_risk > 0.5:
            validation_result["conditions"].append("require_mfa")
        if overall_risk > 0.8:
            validation_result["conditions"].append("require_approval")
            
        validation_result.update({
            "allowed": True,
            "risk_score": overall_risk,
            "session_duration": self._calculate_session_duration(overall_risk),
            "required_validations": validation_result["conditions"]
        })
        
        return validation_result
    
    def _verify_identity(self, principal: str, context: Dict) -> Dict[str, Any]:
        """Verify principal identity using multiple factors"""
        
        verification_methods = []
        
        # JWT token validation
        jwt_valid = self._validate_jwt_token(context.get("jwt_token"))
        verification_methods.append(("jwt", jwt_valid))
        
        # API key validation
        api_key_valid = self._validate_api_key(context.get("api_key"))
        verification_methods.append(("api_key", api_key_valid))
        
        # Certificate validation for service-to-service
        cert_valid = self._validate_certificate(context.get("client_cert"))
        verification_methods.append(("certificate", cert_valid))
        
        # Require at least one valid authentication method
        verified = any(result for method, result in verification_methods if result)
        
        return {
            "verified": verified,
            "methods_used": [method for method, result in verification_methods if result],
            "confidence_score": 0.9 if verified else 0.0
        }
    
    def _assess_device_trust(self, context: Dict) -> Dict[str, Any]:
        """Assess device trustworthiness"""
        
        device_fingerprint = context.get("device_fingerprint", {})
        
        risk_factors = []
        risk_score = 0.0
        
        # Check if device is known
        device_known = self._is_device_known(device_fingerprint)
        if not device_known:
            risk_factors.append("unknown_device")
            risk_score += 0.3
        
        # Check device security posture
        security_posture = device_fingerprint.get("security_posture", {})
        
        if not security_posture.get("antivirus_enabled", True):
            risk_factors.append("no_antivirus")
            risk_score += 0.2
            
        if not security_posture.get("firewall_enabled", True):
            risk_factors.append("no_firewall") 
            risk_score += 0.1
            
        if security_posture.get("jailbroken", False):
            risk_factors.append("jailbroken_device")
            risk_score += 0.4
        
        # Check for suspicious patterns
        recent_activity = self._get_recent_device_activity(device_fingerprint.get("device_id"))
        if recent_activity.get("suspicious_patterns"):
            risk_factors.append("suspicious_activity")
            risk_score += 0.3
        
        return {
            "risk_score": min(1.0, risk_score),
            "risk_factors": risk_factors,
            "device_known": device_known,
            "security_posture": security_posture
        }
    
    def _assess_location_risk(self, context: Dict) -> Dict[str, Any]:
        """Assess location-based risks"""
        
        ip_address = context.get("source_ip")
        location_data = self._get_ip_geolocation(ip_address)
        
        risk_assessment = {
            "blocked": False,
            "risk_score": 0.0,
            "restrictions": []
        }
        
        # Check blocked countries
        blocked_countries = ["CN", "RU", "KP", "IR"]  # Example restricted countries
        if location_data.get("country_code") in blocked_countries:
            risk_assessment["blocked"] = True
            risk_assessment["restrictions"].append("blocked_country")
        
        # Check for VPN/Proxy usage
        if location_data.get("is_vpn") or location_data.get("is_proxy"):
            risk_assessment["risk_score"] += 0.2
            risk_assessment["restrictions"].append("vpn_proxy_detected")
        
        # Check for unusual location
        user_usual_locations = self._get_user_usual_locations(context.get("user_id"))
        if not self._is_usual_location(location_data, user_usual_locations):
            risk_assessment["risk_score"] += 0.3
            risk_assessment["restrictions"].append("unusual_location")
        
        return risk_assessment
    
    def _check_resource_permission(self, principal: str, resource: str, action: str) -> Dict[str, Any]:
        """Check if principal has permission for resource/action"""
        
        # Load principal's permissions
        permissions = self._get_principal_permissions(principal)
        
        # Check direct permissions
        direct_permission = self._check_direct_permission(permissions, resource, action)
        if direct_permission["allowed"]:
            return direct_permission
        
        # Check role-based permissions
        role_permission = self._check_role_permissions(principal, resource, action)
        if role_permission["allowed"]:
            return role_permission
        
        # Check attribute-based permissions
        abac_permission = self._check_abac_permissions(principal, resource, action)
        
        return abac_permission
    
    def _calculate_risk_score(self, *assessments) -> float:
        """Calculate overall risk score from multiple assessments"""
        
        risk_scores = []
        for assessment in assessments:
            if isinstance(assessment, dict):
                risk_scores.append(assessment.get("risk_score", 0.0))
        
        if not risk_scores:
            return 0.5  # Default medium risk
        
        # Use weighted average with max cap
        weighted_score = sum(risk_scores) / len(risk_scores)
        return min(1.0, weighted_score)
    
    def _calculate_session_duration(self, risk_score: float) -> int:
        """Calculate session duration based on risk score"""
        
        if risk_score < 0.2:
            return 8 * 3600  # 8 hours for low risk
        elif risk_score < 0.5:
            return 4 * 3600  # 4 hours for medium risk
        elif risk_score < 0.8:
            return 1 * 3600  # 1 hour for high risk
        else:
            return 15 * 60   # 15 minutes for very high risk
```

## 3. End-to-End Encryption

### Field-Level Encryption Implementation

```python
import boto3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class FieldLevelEncryption:
    """Field-level encryption for sensitive data"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.kms_client = boto3.client('kms')
        self.tenant_key_id = self._get_tenant_key_id()
        
    def encrypt_field(self, field_name: str, value: Any, data_classification: DataClassification) -> Dict[str, Any]:
        """Encrypt a field based on its classification"""
        
        if not self._requires_encryption(data_classification):
            return {"encrypted": False, "value": value}
        
        # Generate data encryption key
        dek_response = self.kms_client.generate_data_key(
            KeyId=self.tenant_key_id,
            KeySpec='AES_256'
        )
        
        # Encrypt the value
        fernet = Fernet(base64.urlsafe_b64encode(dek_response['Plaintext'][:32]))
        encrypted_value = fernet.encrypt(json.dumps(value).encode())
        
        # Return encrypted package
        return {
            "encrypted": True,
            "value": base64.b64encode(encrypted_value).decode(),
            "key_id": self.tenant_key_id,
            "encrypted_dek": base64.b64encode(dek_response['CiphertextBlob']).decode(),
            "algorithm": "AES-256-GCM",
            "field_name": field_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def decrypt_field(self, encrypted_package: Dict[str, Any]) -> Any:
        """Decrypt an encrypted field"""
        
        if not encrypted_package.get("encrypted", False):
            return encrypted_package.get("value")
        
        try:
            # Decrypt the data encryption key
            dek_response = self.kms_client.decrypt(
                CiphertextBlob=base64.b64decode(encrypted_package["encrypted_dek"])
            )
            
            # Decrypt the value
            fernet = Fernet(base64.urlsafe_b64encode(dek_response['Plaintext'][:32]))
            decrypted_bytes = fernet.decrypt(base64.b64decode(encrypted_package["value"]))
            
            return json.loads(decrypted_bytes.decode())
            
        except Exception as e:
            raise DecryptionError(f"Failed to decrypt field {encrypted_package.get('field_name')}: {str(e)}")
    
    def _requires_encryption(self, classification: DataClassification) -> bool:
        """Determine if data classification requires encryption"""
        
        encryption_required = {
            DataClassification.PUBLIC: False,
            DataClassification.INTERNAL: False,
            DataClassification.CONFIDENTIAL: True,
            DataClassification.RESTRICTED: True
        }
        
        return encryption_required.get(classification, True)
    
    def _get_tenant_key_id(self) -> str:
        """Get or create tenant-specific KMS key"""
        
        # In production, this would manage tenant-specific KMS keys
        key_alias = f"alias/damien-tenant-{self.tenant_id}"
        
        try:
            response = self.kms_client.describe_key(KeyId=key_alias)
            return response['KeyMetadata']['KeyId']
        except self.kms_client.exceptions.NotFoundException:
            # Create new key for tenant
            return self._create_tenant_key()
    
    def _create_tenant_key(self) -> str:
        """Create new KMS key for tenant"""
        
        key_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{boto3.Session().get_credentials().access_key}:root"},
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow use of the key for tenant",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{boto3.Session().get_credentials().access_key}:role/damien-tenant-{self.tenant_id}"},
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        response = self.kms_client.create_key(
            Policy=json.dumps(key_policy),
            Description=f"Damien tenant key for {self.tenant_id}",
            Usage='ENCRYPT_DECRYPT',
            Origin='AWS_KMS'
        )
        
        # Create alias
        self.kms_client.create_alias(
            AliasName=f"alias/damien-tenant-{self.tenant_id}",
            TargetKeyId=response['KeyMetadata']['KeyId']
        )
        
        return response['KeyMetadata']['KeyId']

class PIIDetectionAndMasking:
    """Detect and mask PII in data automatically"""
    
    def __init__(self):
        self.pii_patterns = self._load_pii_patterns()
        
    def detect_and_mask_pii(self, text: str, preserve_format: bool = True) -> Dict[str, Any]:
        """Detect PII and return masked version with detection metadata"""
        
        if not text or not isinstance(text, str):
            return {"masked_text": text, "pii_detected": [], "risk_score": 0.0}
        
        detected_pii = []
        masked_text = text
        risk_score = 0.0
        
        for pii_type, pattern_config in self.pii_patterns.items():
            pattern = pattern_config["pattern"]
            risk_weight = pattern_config["risk_weight"]
            
            import re
            matches = re.finditer(pattern, text)
            
            for match in matches:
                detected_pii.append({
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": pattern_config["confidence"]
                })
                
                # Mask the detected PII
                if preserve_format:
                    masked_value = self._preserve_format_mask(match.group(), pii_type)
                else:
                    masked_value = f"[{pii_type.upper()}_REDACTED]"
                
                masked_text = masked_text[:match.start()] + masked_value + masked_text[match.end():]
                risk_score += risk_weight
        
        return {
            "masked_text": masked_text,
            "pii_detected": detected_pii,
            "risk_score": min(1.0, risk_score),
            "requires_consent": any(d["type"] in ["email", "phone", "ssn", "credit_card"] for d in detected_pii)
        }
    
    def _load_pii_patterns(self) -> Dict[str, Dict]:
        """Load PII detection patterns"""
        
        return {
            "email": {
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "confidence": 0.95,
                "risk_weight": 0.3
            },
            "phone": {
                "pattern": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                "confidence": 0.90,
                "risk_weight": 0.2
            },
            "ssn": {
                "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
                "confidence": 0.99,
                "risk_weight": 0.8
            },
            "credit_card": {
                "pattern": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
                "confidence": 0.85,
                "risk_weight": 0.9
            },
            "ip_address": {
                "pattern": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                "confidence": 0.80,
                "risk_weight": 0.1
            }
        }
    
    def _preserve_format_mask(self, original: str, pii_type: str) -> str:
        """Create format-preserving mask"""
        
        if pii_type == "email":
            parts = original.split('@')
            if len(parts) == 2:
                return f"{'*' * len(parts[0])}@{parts[1]}"
        elif pii_type == "phone":
            return re.sub(r'\d', '*', original)
        elif pii_type == "credit_card":
            return original[:4] + '*' * (len(original) - 8) + original[-4:]
        
        return '*' * len(original)
```

## 4. Compliance and Audit Framework

### GDPR/CCPA Compliance Engine

```python
class ComplianceEngine:
    """Handle GDPR, CCPA, and other privacy regulation compliance"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.compliance_rules = self._load_compliance_rules()
        
    def process_data_subject_request(self, request_type: str, user_id: str, details: Dict) -> Dict[str, Any]:
        """Process data subject rights requests (GDPR Article 15-22)"""
        
        handlers = {
            "access": self._handle_data_access_request,
            "rectification": self._handle_data_rectification,
            "erasure": self._handle_data_erasure,
            "portability": self._handle_data_portability,
            "restriction": self._handle_processing_restriction,
            "objection": self._handle_processing_objection
        }
        
        handler = handlers.get(request_type)
        if not handler:
            return {"success": False, "error": f"Unknown request type: {request_type}"}
        
        # Verify user identity
        identity_verified = self._verify_data_subject_identity(user_id, details)
        if not identity_verified:
            return {"success": False, "error": "Identity verification failed"}
        
        # Execute request
        result = handler(user_id, details)
        
        # Log compliance action
        self._log_compliance_action(request_type, user_id, result)
        
        return result
    
    def _handle_data_access_request(self, user_id: str, details: Dict) -> Dict[str, Any]:
        """Handle GDPR Article 15 - Right of access"""
        
        try:
            # Collect all data for the user
            user_data = self._collect_user_data(user_id)
            
            # Decrypt sensitive fields for export
            decrypted_data = self._decrypt_for_export(user_data)
            
            # Generate human-readable report
            report = self._generate_access_report(decrypted_data)
            
            # Create secure download link
            download_link = self._create_secure_download(report, user_id)
            
            return {
                "success": True,
                "report_generated": True,
                "download_link": download_link,
                "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "data_categories": list(decrypted_data.keys())
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_data_erasure(self, user_id: str, details: Dict) -> Dict[str, Any]:
        """Handle GDPR Article 17 - Right to erasure"""
        
        try:
            # Check if erasure is legally permissible
            erasure_check = self._check_erasure_legitimacy(user_id, details)
            if not erasure_check["allowed"]:
                return {
                    "success": False,
                    "error": "Erasure not permitted",
                    "reason": erasure_check["reason"]
                }
            
            # Identify data to be erased
            erasure_scope = self._determine_erasure_scope(user_id, details)
            
            # Perform soft delete first (30-day grace period)
            soft_delete_result = self._perform_soft_delete(user_id, erasure_scope)
            
            # Schedule permanent deletion
            permanent_deletion_job = self._schedule_permanent_deletion(user_id, erasure_scope)
            
            return {
                "success": True,
                "soft_deleted": True,
                "permanent_deletion_scheduled": permanent_deletion_job["job_id"],
                "deletion_date": permanent_deletion_job["execution_date"],
                "data_categories_affected": erasure_scope["categories"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _check_erasure_legitimacy(self, user_id: str, details: Dict) -> Dict[str, Any]:
        """Check if data erasure is legally permissible"""
        
        # Check for legal obligations to retain data
        retention_obligations = self._get_legal_retention_requirements(user_id)
        
        if retention_obligations:
            return {
                "allowed": False,
                "reason": "Legal retention requirements apply",
                "obligations": retention_obligations
            }
        
        # Check for ongoing legal proceedings
        legal_holds = self._check_legal_holds(user_id)
        
        if legal_holds:
            return {
                "allowed": False,
                "reason": "Data subject to legal hold",
                "holds": legal_holds
            }
        
        # Check for legitimate interests that override erasure
        legitimate_interests = self._assess_legitimate_interests(user_id)
        
        if legitimate_interests["override_erasure"]:
            return {
                "allowed": False,
                "reason": "Legitimate interests override erasure request",
                "interests": legitimate_interests["reasons"]
            }
        
        return {"allowed": True}
    
    def generate_privacy_impact_assessment(self, processing_activity: Dict) -> Dict[str, Any]:
        """Generate GDPR Article 35 Privacy Impact Assessment"""
        
        pia = {
            "assessment_id": f"PIA-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "created_at": datetime.utcnow().isoformat(),
            "processing_activity": processing_activity,
            "data_flows": [],
            "risks_identified": [],
            "mitigation_measures": [],
            "residual_risks": [],
            "recommendations": []
        }
        
        # Analyze data flows
        pia["data_flows"] = self._analyze_data_flows(processing_activity)
        
        # Identify privacy risks
        pia["risks_identified"] = self._identify_privacy_risks(processing_activity)
        
        # Assess existing mitigation measures
        pia["mitigation_measures"] = self._assess_mitigation_measures(processing_activity)
        
        # Calculate residual risks
        pia["residual_risks"] = self._calculate_residual_risks(
            pia["risks_identified"],
            pia["mitigation_measures"]
        )
        
        # Generate recommendations
        pia["recommendations"] = self._generate_pia_recommendations(pia["residual_risks"])
        
        # Determine if DPA consultation required
        pia["dpa_consultation_required"] = any(
            risk["severity"] == "high" for risk in pia["residual_risks"]
        )
        
        return pia
    
    def _identify_privacy_risks(self, processing_activity: Dict) -> List[Dict]:
        """Identify privacy risks in processing activity"""
        
        risks = []
        
        # Risk categories based on GDPR guidelines
        risk_categories = {
            "data_minimization": self._assess_data_minimization_risk,
            "purpose_limitation": self._assess_purpose_limitation_risk,
            "accuracy": self._assess_accuracy_risk,
            "storage_limitation": self._assess_storage_limitation_risk,
            "security": self._assess_security_risk,
            "lawfulness": self._assess_lawfulness_risk,
            "transparency": self._assess_transparency_risk,
            "individual_rights": self._assess_individual_rights_risk
        }
        
        for category, assessment_func in risk_categories.items():
            risk_assessment = assessment_func(processing_activity)
            if risk_assessment["risk_level"] > 0:
                risks.append({
                    "category": category,
                    "description": risk_assessment["description"],
                    "severity": risk_assessment["severity"],
                    "likelihood": risk_assessment["likelihood"],
                    "impact": risk_assessment["impact"],
                    "risk_score": risk_assessment["risk_level"]
                })
        
        return sorted(risks, key=lambda x: x["risk_score"], reverse=True)

class AuditLogger:
    """Comprehensive audit logging for compliance"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        
    def log_data_access(self, 
                       user_id: str,
                       data_type: str,
                       action: str,
                       result: Dict,
                       context: Dict) -> str:
        """Log data access for audit trail"""
        
        audit_record = {
            "audit_id": self._generate_audit_id(),
            "tenant_id": self.tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "data_access",
            "user_id": user_id,
            "data_type": data_type,
            "action": action,
            "result_code": result.get("status_code", "unknown"),
            "success": result.get("success", False),
            "data_volume": result.get("records_accessed", 0),
            "legal_basis": context.get("legal_basis"),
            "purpose": context.get("processing_purpose"),
            "source_ip": context.get("source_ip"),
            "user_agent": context.get("user_agent"),
            "session_id": context.get("session_id")
        }
        
        # Store in immutable audit log
        self._store_audit_record(audit_record)
        
        return audit_record["audit_id"]
    
    def log_consent_change(self,
                          user_id: str,
                          consent_type: str,
                          previous_state: bool,
                          new_state: bool,
                          context: Dict) -> str:
        """Log consent changes for GDPR compliance"""
        
        audit_record = {
            "audit_id": self._generate_audit_id(),
            "tenant_id": self.tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "consent_change",
            "user_id": user_id,
            "consent_type": consent_type,
            "previous_state": previous_state,
            "new_state": new_state,
            "change_method": context.get("change_method", "unknown"),
            "source_ip": context.get("source_ip"),
            "evidence": context.get("evidence", {}),
            "withdrawal_reason": context.get("withdrawal_reason") if not new_state else None
        }
        
        self._store_audit_record(audit_record)
        
        return audit_record["audit_id"]
    
    def generate_audit_report(self, 
                            start_date: datetime,
                            end_date: datetime,
                            report_type: str = "comprehensive") -> Dict[str, Any]:
        """Generate audit reports for compliance reviews"""
        
        # Query audit records in date range
        audit_records = self._query_audit_records(start_date, end_date)
        
        report = {
            "report_id": f"AUDIT-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "tenant_id": self.tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "total_events": len(audit_records),
            "event_summary": {},
            "compliance_metrics": {},
            "anomalies": [],
            "recommendations": []
        }
        
        # Analyze events by type
        report["event_summary"] = self._analyze_events_by_type(audit_records)
        
        # Calculate compliance metrics
        report["compliance_metrics"] = self._calculate_compliance_metrics(audit_records)
        
        # Detect anomalies
        report["anomalies"] = self._detect_audit_anomalies(audit_records)
        
        # Generate recommendations
        report["recommendations"] = self._generate_audit_recommendations(
            report["compliance_metrics"],
            report["anomalies"]
        )
        
        return report
```

This privacy-first security design provides enterprise-grade protection with GDPR/CCPA compliance, zero-trust architecture, and comprehensive audit capabilities. The system automatically detects and protects PII while maintaining transparency and user control over their data.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Create test harness framework with result collector and performance tracking", "status": "completed", "priority": "high", "id": "1"}, {"content": "Build universal smoke test runner for all 43 tools", "status": "completed", "priority": "high", "id": "2"}, {"content": "Create controlled test data approach for live account", "status": "completed", "priority": "high", "id": "3"}, {"content": "Run Phase 1 read-only tests on live Gmail account", "status": "completed", "priority": "high", "id": "4"}, {"content": "Fix failing test functions to match actual Gmail API signatures", "status": "completed", "priority": "high", "id": "5"}, {"content": "Design read-only test suite for initial validation", "status": "completed", "priority": "high", "id": "6"}, {"content": "Examine Gmail API module to understand correct function signatures", "status": "completed", "priority": "high", "id": "7"}, {"content": "Update test implementations for all failing tools", "status": "completed", "priority": "high", "id": "8"}, {"content": "Create comprehensive test report for all 43 tools", "status": "completed", "priority": "high", "id": "9"}, {"content": "Test write operations with minimal test data", "status": "completed", "priority": "medium", "id": "10"}, {"content": "Create minimal test data for write operations", "status": "completed", "priority": "high", "id": "11"}, {"content": "Implement write operation tests", "status": "completed", "priority": "high", "id": "12"}, {"content": "Clean up test data after testing", "status": "completed", "priority": "high", "id": "13"}, {"content": "Design multi-tenant DynamoDB schema for AI rules", "status": "completed", "priority": "high", "id": "14"}, {"content": "Create event-driven Lambda architecture", "status": "completed", "priority": "high", "id": "15"}, {"content": "Implement advanced rule conflict resolution", "status": "completed", "priority": "high", "id": "16"}, {"content": "Build privacy-first security design", "status": "completed", "priority": "high", "id": "17"}]