import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set, Optional
import re

class EmailPatternDetector:
    """Detects patterns in email collections"""
    
    def __init__(self):
        self.sender_patterns = defaultdict(list)
        self.subject_patterns = defaultdict(list)
        self.time_patterns = defaultdict(list)
        
    def detect_patterns(self, emails: List[Dict], embeddings: np.ndarray) -> List[Dict]:
        """Detect various patterns in emails"""
        
        patterns = []
        
        # 1. Clustering-based patterns
        cluster_patterns = self._detect_cluster_patterns(emails, embeddings)
        patterns.extend(cluster_patterns)
        
        # 2. Sender-based patterns
        sender_patterns = self._detect_sender_patterns(emails)
        patterns.extend(sender_patterns)
        
        # 3. Subject line patterns
        subject_patterns = self._detect_subject_patterns(emails)
        patterns.extend(subject_patterns)
        
        # 4. Time-based patterns
        time_patterns = self._detect_time_patterns(emails)
        patterns.extend(time_patterns)
        
        # 5. Label correlation patterns
        label_patterns = self._detect_label_patterns(emails)
        patterns.extend(label_patterns)
        
        return patterns
    
    def _detect_cluster_patterns(self, emails: List[Dict], embeddings: np.ndarray) -> List[Dict]:
        """Use DBSCAN clustering to find email groups"""
        
        if len(embeddings) < 5:
            return []
        
        # Normalize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)
        
        # Cluster emails
        clustering = DBSCAN(eps=0.3, min_samples=3).fit(embeddings_scaled)
        
        # Analyze clusters
        patterns = []
        unique_labels = set(clustering.labels_)
        
        for label in unique_labels:
            if label == -1:  # Skip noise
                continue
                
            # Get emails in this cluster
            cluster_indices = np.where(clustering.labels_ == label)[0]
            cluster_emails = [emails[i] for i in cluster_indices]
            
            # Find common characteristics
            pattern = self._analyze_cluster(cluster_emails)
            if pattern:
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_cluster(self, emails: List[Dict]) -> Optional[Dict]:
        """Analyze a cluster of emails to find patterns"""
        
        # Extract common features
        senders = [e.get("from_sender", "") for e in emails]
        subjects = [e.get("subject", "") for e in emails]
        labels = [label for e in emails for label in e.get("label_names", [])]
        
        # Find most common sender
        sender_counter = Counter(senders)
        most_common_sender = sender_counter.most_common(1)[0] if sender_counter else None
        
        # Find common subject words
        subject_words = []
        for subject in subjects:
            words = re.findall(r'\b\w+\b', subject.lower())
            subject_words.extend(words)
        
        word_counter = Counter(subject_words)
        common_words = [word for word, count in word_counter.most_common(5) 
                       if count >= len(emails) * 0.5]  # Word appears in 50% of emails
        
        # Find common labels
        label_counter = Counter(labels)
        common_labels = [label for label, count in label_counter.most_common(3)
                        if count >= len(emails) * 0.7]  # Label on 70% of emails
        
        if not any([most_common_sender, common_words, common_labels]):
            return None
        
        pattern = {
            "type": "cluster",
            "email_count": len(emails),
            "characteristics": {
                "common_sender": most_common_sender[0] if most_common_sender else None,
                "common_subject_words": common_words,
                "common_labels": common_labels
            },
            "example_emails": [e["id"] for e in emails[:3]],
            "suggested_rule": self._suggest_rule_from_cluster(
                most_common_sender, common_words, common_labels
            )
        }
        
        return pattern
    
    def _detect_sender_patterns(self, emails: List[Dict]) -> List[Dict]:
        """Detect patterns based on email senders"""
        
        sender_groups = defaultdict(list)
        for email in emails:
            sender = email.get("from_sender", "")
            if sender:
                sender_groups[sender].append(email)
        
        patterns = []
        for sender, sender_emails in sender_groups.items():
            if len(sender_emails) >= 5:  # Significant volume
                # Analyze this sender's emails
                pattern = {
                    "type": "high_volume_sender",
                    "sender": sender,
                    "email_count": len(sender_emails),
                    "characteristics": {
                        "average_per_day": self._calculate_email_frequency(sender_emails),
                        "common_subjects": self._get_common_subjects(sender_emails),
                        "usually_has_attachments": self._check_attachment_pattern(sender_emails)
                    },
                    "suggested_rule": {
                        "conditions": [{"field": "from", "operator": "equals", "value": sender}],
                        "suggested_actions": ["label", "archive"]
                    }
                }
                patterns.append(pattern)
        
        return patterns
    
    def _detect_subject_patterns(self, emails: List[Dict]) -> List[Dict]:
        """Detect patterns in subject lines"""
        
        patterns = []
        
        # Newsletter patterns
        newsletter_keywords = ["newsletter", "digest", "weekly", "monthly", "update"]
        newsletter_emails = []
        
        for email in emails:
            subject = email.get("subject", "").lower()
            if any(keyword in subject for keyword in newsletter_keywords):
                newsletter_emails.append(email)
        
        if len(newsletter_emails) >= 3:
            patterns.append({
                "type": "newsletter",
                "email_count": len(newsletter_emails),
                "characteristics": {
                    "senders": list(set(e.get("from_sender", "") for e in newsletter_emails))[:5]
                },
                "suggested_rule": {
                    "conditions": [
                        {"field": "subject", "operator": "contains", "value": "newsletter"},
                        {"field": "subject", "operator": "contains", "value": "digest"}
                    ],
                    "condition_conjunction": "OR",
                    "suggested_actions": ["label", "archive"]
                }
            })
        
        return patterns
    
    def _detect_time_patterns(self, emails: List[Dict]) -> List[Dict]:
        """Detect time-based patterns"""
        
        # This is a placeholder for time pattern detection
        # In a full implementation, you would analyze:
        # - Emails received at specific times
        # - Regular intervals (daily, weekly reports)
        # - Business hours vs after hours
        
        return []
    
    def _detect_label_patterns(self, emails: List[Dict]) -> List[Dict]:
        """Detect patterns in how emails are labeled"""
        
        # Analyze which types of emails tend to get certain labels
        label_associations = defaultdict(lambda: defaultdict(int))
        
        for email in emails:
            labels = email.get("label_names", [])
            sender_domain = self._extract_domain(email.get("from_sender", ""))
            
            for label in labels:
                if sender_domain:
                    label_associations[label]["domains"][sender_domain] += 1
                
                # Check for subject patterns
                subject = email.get("subject", "").lower()
                if "invoice" in subject or "receipt" in subject:
                    label_associations[label]["types"]["receipt"] += 1
                elif "meeting" in subject or "calendar" in subject:
                    label_associations[label]["types"]["meeting"] += 1
        
        patterns = []
        # Convert associations to patterns
        # This is simplified - you'd want more sophisticated analysis
        
        return patterns
    
    def _suggest_rule_from_cluster(self, sender_info, common_words, common_labels):
        """Generate rule suggestion from cluster analysis"""
        
        conditions = []
        
        if sender_info:
            conditions.append({
                "field": "from",
                "operator": "equals",
                "value": sender_info[0]
            })
        
        if common_words:
            # Use the most distinctive word
            conditions.append({
                "field": "subject",
                "operator": "contains", 
                "value": common_words[0]
            })
        
        # Suggest action based on current labels
        if "TRASH" in common_labels:
            suggested_action = "trash"
        elif "SPAM" in common_labels:
            suggested_action = "trash"
        elif any(label.startswith("Label_") for label in common_labels):
            suggested_action = "label"
        else:
            suggested_action = "archive"
        
        return {
            "conditions": conditions,
            "suggested_action": suggested_action,
            "confidence": 0.8
        }
    
    def _extract_domain(self, email_address: str) -> str:
        """Extract domain from email address"""
        if "@" in email_address:
            return email_address.split("@")[1].lower()
        return ""
    
    def _calculate_email_frequency(self, emails: List[Dict]) -> float:
        """Calculate average emails per day"""
        # Simplified - would need actual date parsing
        return len(emails) / 30  # Assume 30 day period
    
    def _get_common_subjects(self, emails: List[Dict]) -> List[str]:
        """Get most common subject patterns"""
        subjects = [e.get("subject", "") for e in emails]
        # Simplified - would use more sophisticated analysis
        return list(set(subjects))[:3]
    
    def _check_attachment_pattern(self, emails: List[Dict]) -> bool:
        """Check if sender usually includes attachments"""
        with_attachments = sum(1 for e in emails if e.get("has_attachments", False))
        return with_attachments / len(emails) > 0.5