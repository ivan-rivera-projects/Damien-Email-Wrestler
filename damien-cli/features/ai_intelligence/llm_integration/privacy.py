from typing import Dict, List, Any, Tuple, Optional
import re
import hashlib
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PIIEntity:
    """Represents a PII entity found in text"""
    entity_type: str
    value: str
    start_pos: int
    end_pos: int
    confidence: float
    replacement_token: str

class PrivacyGuardian:
    """Comprehensive privacy protection for LLM processing"""
    
    def __init__(self):
        self.pii_patterns = self._compile_patterns()
        self.tokenizer = PIITokenizer()
        self.audit_logger = AuditLogger()
    
    def process_email_privately(
        self,
        email: Dict[str, Any],
        protection_level: str = "standard"  # minimal, standard, maximum
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process email with privacy protection
        
        Returns:
            - Sanitized email safe for LLM
            - Privacy metadata for restoration
        """
        
        # Start privacy audit trail
        audit_id = self.audit_logger.start_audit(email['id'])
        
        # Deep copy to avoid modifying original
        import copy
        sanitized = copy.deepcopy(email)
        
        # Detect all PII
        pii_report = self.detect_pii_comprehensive(email)
        
        # Apply protection based on level
        if protection_level == "minimal":
            sanitized, mappings = self._apply_minimal_protection(sanitized, pii_report)
        elif protection_level == "standard":
            sanitized, mappings = self._apply_standard_protection(sanitized, pii_report)
        else:  # maximum
            sanitized, mappings = self._apply_maximum_protection(sanitized, pii_report)
        
        # Create privacy metadata
        privacy_metadata = {
            'audit_id': audit_id,
            'protection_level': protection_level,
            'pii_detected': len(pii_report['entities']),
            'pii_types': list(set(e.entity_type for e in pii_report['entities'])),
            'token_mappings': mappings,
            'processing_timestamp': datetime.utcnow().isoformat(),
            'original_hash': hashlib.sha256(str(email).encode()).hexdigest()
        }
        
        # Log privacy action
        self.audit_logger.log_action(
            audit_id,
            'sanitization_complete',
            privacy_metadata
        )
        
        return sanitized, privacy_metadata
    
    def detect_pii_comprehensive(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive PII detection across all email fields"""
        
        entities = []
        
        # Check all text fields
        text_fields = ['subject', 'content', 'snippet', 'from_sender', 'to_recipients']
        
        for field in text_fields:
            if field in email and email[field]:
                field_entities = self._detect_pii_in_text(
                    email[field],
                    field_name=field
                )
                entities.extend(field_entities)
        
        # Check structured data
        if 'attachments' in email:
            for attachment in email['attachments']:
                if 'filename' in attachment:
                    filename_entities = self._detect_pii_in_text(
                        attachment['filename'],
                        field_name='attachment_filename'
                    )
                    entities.extend(filename_entities)
        
        return {
            'has_pii': len(entities) > 0,
            'entity_count': len(entities),
            'entities': entities,
            'risk_score': self._calculate_privacy_risk(entities)
        }
    
    def _detect_pii_in_text(
        self,
        text: str,
        field_name: str
    ) -> List[PIIEntity]:
        """Detect PII entities in a text field"""
        
        entities = []
        
        for pii_type, pattern in self.pii_patterns.items():
            for match in pattern.finditer(text):
                # Generate unique token for this PII
                token = self.tokenizer.generate_token(
                    pii_type,
                    match.group(),
                    field_name
                )
                
                entity = PIIEntity(
                    entity_type=pii_type,
                    value=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=self._get_confidence(pii_type, match.group()),
                    replacement_token=token
                )
                
                entities.append(entity)
        
        # Additional detection using NER (if available)
        if hasattr(self, 'ner_model'):
            ner_entities = self._detect_pii_with_ner(text, field_name)
            entities.extend(ner_entities)
        
        return entities
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for PII detection"""
        
        patterns = {
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            'phone': re.compile(
                r'(\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                re.IGNORECASE
            ),
            'ssn': re.compile(
                r'\b\d{3}-?\d{2}-?\d{4}\b'
            ),
            'credit_card': re.compile(
                r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
            ),
            'ip_address': re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),
            'date_of_birth': re.compile(
                r'\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12][0-9]|3[01])[/-](?:19|20)\d{2}\b'
            ),
            'passport': re.compile(
                r'\b[A-Z]{1,2}\d{6,9}\b'
            ),
            'bank_account': re.compile(
                r'\b\d{8,17}\b'  # Simplified - needs context
            ),
            'medical_record': re.compile(
                r'\b(?:MRN|Medical Record Number)[:\s]*\w+\b',
                re.IGNORECASE
            )
        }
        
        return patterns
    
    def _apply_standard_protection(
        self,
        email: Dict[str, Any],
        pii_report: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Apply standard privacy protection"""
        
        mappings = {}
        
        # Sort entities by position (reverse) to maintain positions
        entities = sorted(
            pii_report['entities'],
            key=lambda e: (e.start_pos, e.end_pos),
            reverse=True
        )
        
        # Process each field
        for field in ['subject', 'content', 'snippet']:
            if field not in email:
                continue
            
            field_text = email[field]
            field_entities = [e for e in entities if field in str(e)]
            
            # Replace PII with tokens
            for entity in field_entities:
                # Store mapping
                mappings[entity.replacement_token] = entity.value
                
                # Replace in text
                field_text = (
                    field_text[:entity.start_pos] +
                    entity.replacement_token +
                    field_text[entity.end_pos:]
                )
            
            email[field] = field_text
        
        # Sanitize sender/recipient fields
        if 'from_sender' in email:
            sender_token = f"[SENDER_{hashlib.md5(email['from_sender'].encode()).hexdigest()[:8]}]"
            mappings[sender_token] = email['from_sender']
            email['from_sender'] = sender_token
        
        return email, mappings
    
    def restore_pii(
        self,
        processed_content: str,
        mappings: Dict[str, str]
    ) -> str:
        """Restore PII tokens to original values"""
        
        restored = processed_content
        
        # Sort by token length (descending) to avoid partial replacements
        sorted_mappings = sorted(
            mappings.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for token, original in sorted_mappings:
            restored = restored.replace(token, original)
        
        return restored

class PIITokenizer:
    """Generate consistent tokens for PII replacement"""
    
    def __init__(self):
        self.token_cache = {}
    
    def generate_token(
        self,
        pii_type: str,
        value: str,
        context: str
    ) -> str:
        """Generate a consistent token for PII value"""
        
        # Create cache key
        cache_key = f"{pii_type}:{value}:{context}"
        
        if cache_key in self.token_cache:
            return self.token_cache[cache_key]
        
        # Generate token
        value_hash = hashlib.md5(value.encode()).hexdigest()[:8]
        token = f"[{pii_type.upper()}_{value_hash}]"
        
        self.token_cache[cache_key] = token
        return token

class AuditLogger:
    """Audit trail for privacy operations"""
    
    def __init__(self):
        self.audit_store = {}
    
    def start_audit(self, email_id: str) -> str:
        """Start a new audit trail"""
        
        audit_id = f"audit_{email_id}_{datetime.utcnow().timestamp()}"
        
        self.audit_store[audit_id] = {
            'email_id': email_id,
            'start_time': datetime.utcnow(),
            'actions': []
        }
        
        return audit_id
    
    def log_action(
        self,
        audit_id: str,
        action: str,
        details: Dict[str, Any]
    ):
        """Log a privacy action"""
        
        if audit_id in self.audit_store:
            self.audit_store[audit_id]['actions'].append({
                'timestamp': datetime.utcnow(),
                'action': action,
                'details': details
            })
    
    def get_audit_trail(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve audit trail"""
        return self.audit_store.get(audit_id)