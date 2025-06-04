"""Basic email pattern detection algorithms"""

import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set, Optional
import re
from datetime import datetime, timedelta
import logging

from ..models import EmailPattern, PatternType, PatternCharacteristics

logger = logging.getLogger(__name__)

class EmailPatternDetector:
    """Detects various patterns in email collections using basic algorithms"""
    
    def __init__(self):
        self.min_pattern_size = 3  # Minimum emails to form a pattern
        self.min_confidence = 0.6  # Minimum confidence threshold
        
    def detect_patterns(self, emails: List[Dict], embeddings: np.ndarray) -> List[EmailPattern]:
        """Detect comprehensive patterns in email data"""
        
        if len(emails) < self.min_pattern_size:
            logger.warning(f"Not enough emails ({len(emails)}) to detect patterns")
            return []
        
        patterns = []
        
        try:
            # 1. Sender-based patterns (most reliable)
            try:
                sender_patterns = self._detect_sender_patterns(emails)
                patterns.extend(sender_patterns)
                logger.debug(f"Detected {len(sender_patterns)} sender patterns")
            except Exception as e:
                logger.warning(f"Error in sender pattern detection: {str(e)}")
            
            # 2. Subject line patterns  
            try:
                subject_patterns = self._detect_subject_patterns(emails)
                patterns.extend(subject_patterns)
                logger.debug(f"Detected {len(subject_patterns)} subject patterns")
            except Exception as e:
                logger.warning(f"Error in subject pattern detection: {str(e)}")
            
            # 3. Label patterns
            try:
                label_patterns = self._detect_label_patterns(emails)
                patterns.extend(label_patterns)
                logger.debug(f"Detected {len(label_patterns)} label patterns")
            except Exception as e:
                logger.warning(f"Error in label pattern detection: {str(e)}")
            
            # 4. Time-based patterns (basic)
            try:
                time_patterns = self._detect_time_patterns(emails)
                patterns.extend(time_patterns)
                logger.debug(f"Detected {len(time_patterns)} time patterns")
            except Exception as e:
                logger.warning(f"Error in time pattern detection: {str(e)}")
            
            # 5. Size/attachment patterns
            try:
                attachment_patterns = self._detect_attachment_patterns(emails)
                patterns.extend(attachment_patterns)
                logger.debug(f"Detected {len(attachment_patterns)} attachment patterns")
            except Exception as e:
                logger.warning(f"Error in attachment pattern detection: {str(e)}")
            
            # Filter by confidence and remove duplicates
            try:
                patterns = self._filter_and_dedupe_patterns(patterns)
            except Exception as e:
                logger.warning(f"Error in pattern filtering: {str(e)}")
                # Return unfiltered patterns if filtering fails
                pass
            
            logger.info(f"Detected {len(patterns)} email patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {str(e)}", exc_info=True)
            return []
    
    def _detect_sender_patterns(self, emails: List[Dict]) -> List[EmailPattern]:
        """Detect patterns based on email senders"""
        
        patterns = []
        sender_groups = defaultdict(list)
        
        # Group emails by sender
        for email in emails:
            sender = email.get('from_sender', '')
            if sender:
                sender_groups[sender].append(email)
        
        # Analyze each sender group
        for sender, sender_emails in sender_groups.items():
            if len(sender_emails) >= self.min_pattern_size:
                pattern = self._analyze_sender_group(sender, sender_emails, len(emails))
                if pattern:
                    patterns.append(pattern)
        
        return patterns
    
    def _analyze_sender_group(self, sender: str, emails: List[Dict], total_emails: int) -> Optional[EmailPattern]:
        """Analyze emails from a specific sender"""
        
        try:
            email_count = len(emails)
            
            # Calculate basic statistics
            subjects = [email.get('subject', '') for email in emails]
            common_subject_words = self._extract_common_words(subjects)
            
            # Check for attachments
            has_attachments = sum(1 for email in emails if email.get('has_attachments', False))
            attachment_rate = has_attachments / email_count if email_count > 0 else 0
            
            # Determine sender type and confidence
            sender_type, confidence = self._classify_sender(sender, subjects)
            
            # Create pattern characteristics with minimal complexity to avoid recursion
            try:
                characteristics = PatternCharacteristics(
                    primary_feature=sender,
                    secondary_features=common_subject_words[:3],
                    statistical_measures={
                        'email_count': email_count,
                        'attachment_rate': attachment_rate,
                        'prevalence': email_count / total_emails
                    },
                    sender_domain=sender.split('@')[-1] if '@' in sender else sender,
                    sender_type=sender_type,
                    common_keywords=common_subject_words
                )
            except Exception as char_error:
                logger.warning(f"Error creating characteristics for {sender}: {char_error}")
                # Create minimal characteristics if complex creation fails
                characteristics = PatternCharacteristics(
                    primary_feature=sender,
                    statistical_measures={'email_count': email_count}
                )
            
            # Create EmailPattern with error handling
            try:
                return EmailPattern(
                    pattern_type=PatternType.SENDER,
                    pattern_name=f"High Volume Sender: {sender}",
                    description=f"{sender_type} sender with {email_count} emails",
                    email_count=email_count,
                    total_email_universe=total_emails,
                    prevalence_rate=email_count / total_emails,
                    confidence=confidence,
                    characteristics=characteristics,
                    example_email_ids=[email.get('id', '') for email in emails[:3] if email.get('id')]
                )
            except Exception as pattern_error:
                logger.warning(f"Error creating EmailPattern for {sender}: {pattern_error}")
                return None
            
        except Exception as e:
            logger.warning(f"Error analyzing sender {sender}: {str(e)}")
            return None
    
    def _classify_sender(self, sender: str, subjects: List[str]) -> Tuple[str, float]:
        """Classify sender type and determine confidence"""
        
        sender_lower = sender.lower()
        all_subjects = ' '.join(subjects).lower()
        
        # Newsletter patterns
        if any(keyword in sender_lower for keyword in ['newsletter', 'digest', 'weekly', 'monthly']):
            return "Newsletter", 0.9
        
        # Notification patterns  
        if any(keyword in sender_lower for keyword in ['noreply', 'notification', 'alert', 'automated']):
            return "Notification", 0.85
        
        # Shopping patterns
        if any(keyword in all_subjects for keyword in ['order', 'receipt', 'purchase', 'shipped']):
            return "Shopping", 0.8
        
        # Social media patterns
        if any(keyword in sender_lower for keyword in ['facebook', 'twitter', 'linkedin', 'instagram']):
            return "Social Media", 0.85
        
        # Default
        return "Regular Sender", 0.7
    
    def _detect_subject_patterns(self, emails: List[Dict]) -> List[EmailPattern]:
        """Detect patterns in email subject lines"""
        
        patterns = []
        
        # Newsletter pattern
        newsletter_emails = []
        for email in emails:
            subject = email.get('subject', '').lower()
            if any(keyword in subject for keyword in ['newsletter', 'digest', 'weekly', 'monthly', 'update']):
                newsletter_emails.append(email)
        
        if len(newsletter_emails) >= self.min_pattern_size:
            characteristics = PatternCharacteristics(
                primary_feature="newsletter",
                common_keywords=['newsletter', 'digest', 'weekly', 'monthly'],
                statistical_measures={'pattern_strength': len(newsletter_emails) / len(emails)}
            )
            
            patterns.append(EmailPattern(
                pattern_type=PatternType.SUBJECT,
                pattern_name="Newsletter Emails",
                description=f"Emails with newsletter-like subjects ({len(newsletter_emails)} found)",
                email_count=len(newsletter_emails),
                total_email_universe=len(emails),
                prevalence_rate=len(newsletter_emails) / len(emails),
                confidence=0.85,
                characteristics=characteristics,
                example_email_ids=[email.get('id', '') for email in newsletter_emails[:3]]
            ))
        
        # Receipt/Order pattern
        receipt_emails = []
        for email in emails:
            subject = email.get('subject', '').lower()
            if any(keyword in subject for keyword in ['receipt', 'order', 'invoice', 'purchase', 'payment']):
                receipt_emails.append(email)
        
        if len(receipt_emails) >= self.min_pattern_size:
            characteristics = PatternCharacteristics(
                primary_feature="receipt",
                common_keywords=['receipt', 'order', 'invoice', 'purchase'],
                statistical_measures={'pattern_strength': len(receipt_emails) / len(emails)}
            )
            
            patterns.append(EmailPattern(
                pattern_type=PatternType.SUBJECT,
                pattern_name="Receipt/Order Emails", 
                description=f"Emails about purchases and orders ({len(receipt_emails)} found)",
                email_count=len(receipt_emails),
                total_email_universe=len(emails),
                prevalence_rate=len(receipt_emails) / len(emails),
                confidence=0.8,
                characteristics=characteristics,
                example_email_ids=[email.get('id', '') for email in receipt_emails[:3]]
            ))
        
        return patterns
    
    def _detect_label_patterns(self, emails: List[Dict]) -> List[EmailPattern]:
        """Detect patterns based on Gmail labels"""
        
        patterns = []
        label_groups = defaultdict(list)
        
        # Group emails by labels
        for email in emails:
            labels = email.get('label_names', [])
            for label in labels:
                if label not in ['INBOX', 'UNREAD']:  # Skip common labels
                    label_groups[label].append(email)
        
        # Analyze significant label groups
        for label, label_emails in label_groups.items():
            if len(label_emails) >= self.min_pattern_size:
                characteristics = PatternCharacteristics(
                    primary_feature=label,
                    statistical_measures={'prevalence': len(label_emails) / len(emails)}
                )
                
                patterns.append(EmailPattern(
                    pattern_type=PatternType.LABEL,
                    pattern_name=f"Label: {label}",
                    description=f"Emails with {label} label ({len(label_emails)} emails)",
                    email_count=len(label_emails),
                    total_email_universe=len(emails),
                    prevalence_rate=len(label_emails) / len(emails),
                    confidence=0.8,
                    characteristics=characteristics,
                    example_email_ids=[email.get('id', '') for email in label_emails[:3]]
                ))
        
        return patterns
    
    def _detect_time_patterns(self, emails: List[Dict]) -> List[EmailPattern]:
        """Detect basic time-based email patterns"""
        
        patterns = []
        
        try:
            # Parse email timestamps
            timestamps = []
            valid_emails = []
            
            for email in emails:
                try:
                    received_timestamp = email.get('received_timestamp')
                    if received_timestamp:
                        dt = datetime.fromtimestamp(received_timestamp)
                        timestamps.append(dt)
                        valid_emails.append(email)
                except:
                    continue
            
            if len(timestamps) < self.min_pattern_size:
                return patterns
            
            # Analyze day of week patterns
            weekday_counts = defaultdict(list)
            for i, dt in enumerate(timestamps):
                weekday_counts[dt.weekday()].append(valid_emails[i])
            
            # Find dominant days (>30% of emails)
            for weekday, day_emails in weekday_counts.items():
                if len(day_emails) >= len(valid_emails) * 0.3:
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    
                    characteristics = PatternCharacteristics(
                        primary_feature=day_names[weekday],
                        time_pattern_type='weekly',
                        peak_days=[weekday],
                        statistical_measures={'day_concentration': len(day_emails) / len(valid_emails)}
                    )
                    
                    patterns.append(EmailPattern(
                        pattern_type=PatternType.TIME,
                        pattern_name=f"{day_names[weekday]} Pattern",
                        description=f"Many emails received on {day_names[weekday]} ({len(day_emails)} emails)",
                        email_count=len(day_emails),
                        total_email_universe=len(emails),
                        prevalence_rate=len(day_emails) / len(emails),
                        confidence=0.7,
                        characteristics=characteristics,
                        example_email_ids=[email.get('id', '') for email in day_emails[:3]]
                    ))
            
            return patterns
            
        except Exception as e:
            logger.warning(f"Error detecting time patterns: {str(e)}")
            return []
    
    def _detect_attachment_patterns(self, emails: List[Dict]) -> List[EmailPattern]:
        """Detect patterns related to attachments and email size"""
        
        patterns = []
        
        # Emails with attachments
        attachment_emails = [email for email in emails if email.get('has_attachments', False)]
        
        if len(attachment_emails) >= self.min_pattern_size:
            characteristics = PatternCharacteristics(
                primary_feature="has_attachments",
                statistical_measures={'attachment_rate': len(attachment_emails) / len(emails)}
            )
            
            patterns.append(EmailPattern(
                pattern_type=PatternType.ATTACHMENT,
                pattern_name="Emails with Attachments",
                description=f"Emails containing attachments ({len(attachment_emails)} found)",
                email_count=len(attachment_emails),
                total_email_universe=len(emails),
                prevalence_rate=len(attachment_emails) / len(emails),
                confidence=0.75,
                characteristics=characteristics,
                example_email_ids=[email.get('id', '') for email in attachment_emails[:3]]
            ))
        
        # Large emails (>100KB)
        large_emails = []
        for email in emails:
            size = email.get('size_estimate', 0)
            if size > 100000:  # > 100KB
                large_emails.append(email)
        
        if len(large_emails) >= self.min_pattern_size:
            characteristics = PatternCharacteristics(
                primary_feature="large_size",
                statistical_measures={'large_email_rate': len(large_emails) / len(emails)}
            )
            
            patterns.append(EmailPattern(
                pattern_type=PatternType.SIZE,
                pattern_name="Large Emails",
                description=f"Large emails (>100KB) - {len(large_emails)} found",
                email_count=len(large_emails),
                total_email_universe=len(emails),
                prevalence_rate=len(large_emails) / len(emails),
                confidence=0.7,
                characteristics=characteristics,
                example_email_ids=[email.get('id', '') for email in large_emails[:3]]
            ))
        
        return patterns
    
    def _extract_common_words(self, texts: List[str], min_frequency: int = 2) -> List[str]:
        """Extract common words from a list of texts"""
        
        all_words = []
        for text in texts:
            # Clean and extract words
            words = re.findall(r'\b\w{3,}\b', text.lower())
            all_words.extend(words)
        
        word_counter = Counter(all_words)
        return [word for word, count in word_counter.most_common(10) if count >= min_frequency]
    
    def _filter_and_dedupe_patterns(self, patterns: List[EmailPattern]) -> List[EmailPattern]:
        """Filter patterns by confidence and remove duplicates"""
        
        # Filter by minimum confidence
        filtered = [p for p in patterns if p.confidence >= self.min_confidence]
        
        # Sort by confidence and email count
        filtered.sort(key=lambda x: (x.confidence, x.email_count), reverse=True)
        
        # Remove near-duplicates (same type and similar email count)
        deduped = []
        seen_combinations = set()
        
        for pattern in filtered:
            # Create a signature for the pattern
            signature = (
                pattern.pattern_type,
                pattern.email_count,
                pattern.characteristics.primary_feature
            )
            
            if signature not in seen_combinations:
                seen_combinations.add(signature)
                deduped.append(pattern)
        
        return deduped[:15]  # Return top 15 patterns
