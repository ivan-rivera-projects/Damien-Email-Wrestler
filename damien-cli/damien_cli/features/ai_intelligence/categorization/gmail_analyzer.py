"""Gmail-specific email analyzer that fetches and processes real email data"""

import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from tqdm import tqdm
import time

from damien_cli.core_api import gmail_api_service
from damien_cli.features.ai_intelligence.models import (
    EmailAnalysisResult, EmailPattern, CategorySuggestion, 
    EmailFeatures, EmailSignature, PerformanceMetrics,
    ProcessingStatus, PatternCharacteristics, PatternType
)
from .embeddings import EmailEmbeddingGenerator
from .patterns import EmailPatternDetector
from ..utils.batch_processor import BatchEmailProcessor
from ..utils.confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)

class GmailEmailAnalyzer:
    """Analyzes Gmail emails to detect patterns and suggest rules"""
    
    def __init__(self, gmail_service=None):
        self.gmail_service = gmail_service
        self.embedding_generator = EmailEmbeddingGenerator()
        self.pattern_detector = EmailPatternDetector()
        self.batch_processor = BatchEmailProcessor()
        self.confidence_scorer = ConfidenceScorer()
        
        # Performance tracking
        self.performance_metrics = None
        
    async def analyze_inbox(
        self,
        max_emails: int = 1000,
        days_back: int = 30,
        min_confidence: float = 0.7,
        query_filter: Optional[str] = None
    ) -> EmailAnalysisResult:
        """Analyze Gmail inbox and return comprehensive results"""
        
        # Start performance tracking
        start_time = datetime.now()
        operation_name = f"Gmail Analysis ({max_emails} emails, {days_back} days)"
        
        logger.info(f"🚀 Starting Gmail inbox analysis")
        logger.info(f"   📧 Max emails: {max_emails}")
        logger.info(f"   📅 Days back: {days_back}")
        logger.info(f"   🎯 Min confidence: {min_confidence:.0%}")
        
        try:
            # Step 1: Fetch emails from Gmail
            print("📥 Fetching emails from Gmail...")
            emails = await self._fetch_emails(max_emails, days_back, query_filter)
            logger.info(f"✅ Fetched {len(emails)} emails from Gmail")
            
            if not emails:
                logger.warning("No emails found matching criteria")
                return self._create_empty_result(start_time, operation_name)
            
            # Step 2: Extract features and signatures
            print("🔍 Extracting email features...")
            enriched_emails = self._enrich_emails_with_features(emails)
            
            # Step 3: Generate embeddings in batches
            print("🧠 Generating email embeddings...")
            embeddings_result, embeddings_array = await self.batch_processor.process_embeddings(
                enriched_emails, self.embedding_generator
            )
            logger.info(f"✅ Generated {embeddings_result.embeddings_generated} embeddings")
            
            # Step 4: Detect patterns
            print("🔍 Detecting email patterns...")
            patterns = self.pattern_detector.detect_patterns(
                enriched_emails, embeddings_array
            )
            logger.info(f"✅ Detected {len(patterns)} patterns")
            
            # Step 5: Filter patterns by confidence
            high_confidence_patterns = [
                p for p in patterns if p.confidence >= min_confidence
            ]
            logger.info(f"✅ {len(high_confidence_patterns)} high-confidence patterns")
            
            # Step 6: Generate category suggestions
            print("💡 Generating rule suggestions...")
            suggestions = self._generate_category_suggestions(
                high_confidence_patterns, enriched_emails
            )
            logger.info(f"✅ Generated {len(suggestions)} suggestions")
            
            # Step 7: Create comprehensive summary
            print("📊 Creating analysis summary...")
            summary = self._create_analysis_summary(enriched_emails, patterns, suggestions)
            
            # Step 8: Calculate performance metrics
            end_time = datetime.now()
            performance_metrics = PerformanceMetrics(
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                items_processed=len(emails),
                errors_encountered=embeddings_result.failed_items,
                warnings_count=len(embeddings_result.warnings)
            )
            
            # Create final result
            result = EmailAnalysisResult(
                total_emails_analyzed=len(emails),
                analysis_scope={
                    'max_emails': max_emails,
                    'days_back': days_back,
                    'query_filter': query_filter,
                    'date_range': {
                        'start': (datetime.now() - timedelta(days=days_back)).isoformat(),
                        'end': datetime.now().isoformat()
                    }
                },
                patterns_detected=high_confidence_patterns,
                category_suggestions=suggestions,
                processing_performance=performance_metrics,
                batch_results=[embeddings_result],
                summary_statistics=summary,
                data_sources=['gmail_api'],
                analysis_parameters={
                    'min_confidence': min_confidence,
                    'embedding_model': self.embedding_generator.model_name,
                    'batch_size': self.batch_processor.batch_size
                },
                model_versions={
                    'sentence_transformer': 'all-MiniLM-L6-v2',
                    'analyzer_version': '2.0.0'
                }
            )
            
            logger.info(f"🎉 Analysis complete in {performance_metrics.duration_ms/1000:.1f}s")
            print(f"✅ Analysis complete! Found {len(suggestions)} actionable suggestions")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error during inbox analysis: {str(e)}")
            raise
    
    async def _fetch_emails(
        self, 
        max_emails: int, 
        days_back: int, 
        query_filter: Optional[str] = None
    ) -> List[Dict]:
        """Fetch emails from Gmail API with enhanced error handling"""
        
        if not self.gmail_service:
            from damien_cli.core_api.gmail_api_service import get_authenticated_service
            self.gmail_service = get_authenticated_service()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Build Gmail query
        query_parts = [f"after:{start_date.strftime('%Y/%m/%d')}"]
        
        if query_filter:
            query_parts.append(query_filter)
        
        query = " ".join(query_parts)
        logger.debug(f"Gmail query: {query}")
        
        try:
            # Fetch email list with progress tracking
            print(f"🔍 Searching Gmail with query: {query}")
            response = gmail_api_service.list_messages(
                self.gmail_service,
                query_string=query,
                max_results=max_emails
            )
            
            message_ids = [msg['id'] for msg in response.get('messages', [])]
            logger.info(f"📋 Found {len(message_ids)} email IDs")
            
            if not message_ids:
                logger.warning("No emails found matching criteria")
                return []
            
            # Fetch detailed information for each email with progress bar
            emails = []
            failed_count = 0
            
            for i, msg_id in enumerate(tqdm(message_ids, desc="📧 Fetching email details")):
                try:
                    email_details = gmail_api_service.get_message_details(
                        self.gmail_service,
                        message_id=msg_id,
                        format='metadata'
                    )
                    
                    # Process email response
                    processed_email = self._process_email_response(email_details)
                    if processed_email:
                        emails.append(processed_email)
                    else:
                        failed_count += 1
                        
                    # Rate limiting - small delay every 10 emails
                    if (i + 1) % 10 == 0:
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching email {msg_id}: {str(e)}")
                    failed_count += 1
                    continue
            
            if failed_count > 0:
                logger.warning(f"⚠️ Failed to process {failed_count} emails")
            
            logger.info(f"✅ Successfully processed {len(emails)} emails")
            return emails
            
        except Exception as e:
            logger.error(f"❌ Error fetching emails from Gmail: {str(e)}")
            raise
    
    def _process_email_response(self, email_details: Dict) -> Optional[Dict]:
        """Process Gmail API response into standardized format with error handling"""
        
        try:
            headers = email_details.get('payload', {}).get('headers', [])
            
            # Extract headers safely
            header_dict = {}
            for header in headers:
                name = header.get('name', '').lower()
                value = header.get('value', '')
                if name and value:
                    header_dict[name] = value
            
            # Parse internal date
            internal_date = email_details.get('internalDate', '0')
            try:
                timestamp = int(internal_date) / 1000
                parsed_date = datetime.fromtimestamp(timestamp)
            except (ValueError, OSError):
                parsed_date = datetime.now()
            
            # Extract size estimate
            size_estimate = email_details.get('sizeEstimate', 0)
            
            # Process labels
            label_names = email_details.get('labelIds', [])
            
            # Check for attachments
            has_attachments = self._check_has_attachments(email_details)
            
            processed_email = {
                'id': email_details.get('id', ''),
                'thread_id': email_details.get('threadId', ''),
                'from_sender': header_dict.get('from', 'Unknown'),
                'to': header_dict.get('to', ''),
                'subject': header_dict.get('subject', 'No Subject'),
                'date': header_dict.get('date', ''),
                'snippet': email_details.get('snippet', ''),
                'label_names': label_names,
                'size_estimate': size_estimate,
                'has_attachments': has_attachments,
                'internal_date': internal_date,
                'message_id': header_dict.get('message-id', ''),
                'parsed_date': parsed_date,
                
                # Additional metadata
                'received_timestamp': timestamp if internal_date != '0' else time.time(),
                'header_count': len(headers),
                'is_unread': 'UNREAD' in label_names,
                'is_important': 'IMPORTANT' in label_names,
                'in_inbox': 'INBOX' in label_names,
            }
            
            return processed_email
            
        except Exception as e:
            logger.warning(f"⚠️ Error processing email response: {str(e)}")
            return None
    
    def _check_has_attachments(self, email_details: Dict) -> bool:
        """Check if email has attachments"""
        
        try:
            payload = email_details.get('payload', {})
            
            # Check main payload
            if payload.get('filename'):
                return True
            
            # Check parts for attachments
            parts = payload.get('parts', [])
            for part in parts:
                if part.get('filename'):
                    return True
                
                # Check headers for content-disposition
                headers = part.get('headers', [])
                for header in headers:
                    if header.get('name', '').lower() == 'content-disposition':
                        if 'attachment' in header.get('value', '').lower():
                            return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking attachments: {str(e)}")
            return False
    
    def _enrich_emails_with_features(self, emails: List[Dict]) -> List[Dict]:
        """Enrich emails with extracted features and signatures"""
        
        enriched_emails = []
        
        for email in tqdm(emails, desc="🔍 Extracting features"):
            try:
                # Extract comprehensive features
                features = EmailFeatures.extract_from_email(email)
                
                # Generate email signature
                signature = EmailSignature.from_email(email)
                
                # Add features and signature to email
                enriched_email = email.copy()
                enriched_email['features'] = features
                enriched_email['signature'] = signature
                
                enriched_emails.append(enriched_email)
                
            except Exception as e:
                logger.warning(f"⚠️ Error enriching email {email.get('id', 'unknown')}: {str(e)}")
                # Add email without enrichment
                enriched_emails.append(email)
        
        return enriched_emails
    
    def _generate_category_suggestions(
        self, 
        patterns: List[EmailPattern], 
        emails: List[Dict]
    ) -> List[CategorySuggestion]:
        """Generate actionable category suggestions from patterns"""
        
        suggestions = []
        
        for pattern in patterns:
            try:
                # Convert pattern to category suggestion
                suggestion = self._pattern_to_suggestion(pattern, emails)
                if suggestion:
                    suggestions.append(suggestion)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error creating suggestion from pattern: {str(e)}")
                continue
        
        # Sort by business value and confidence
        suggestions.sort(
            key=lambda x: (x.confidence * 0.7 + (x.email_count / len(emails)) * 0.3), 
            reverse=True
        )
        
        return suggestions[:15]  # Return top 15 suggestions
    
    def _pattern_to_suggestion(
        self, 
        pattern: EmailPattern, 
        emails: List[Dict]
    ) -> Optional[CategorySuggestion]:
        """Convert a pattern into an actionable rule suggestion"""
        
        try:
            if pattern.pattern_type == PatternType.SENDER:
                return self._create_sender_suggestion(pattern, emails)
            elif pattern.pattern_type == PatternType.SUBJECT:
                return self._create_subject_suggestion(pattern, emails)
            elif pattern.pattern_type == PatternType.CLUSTER:
                return self._create_cluster_suggestion(pattern, emails)
            elif pattern.pattern_type == PatternType.TIME:
                return self._create_time_suggestion(pattern, emails)
            elif pattern.pattern_type == PatternType.LABEL:
                return self._create_label_suggestion(pattern, emails)
            else:
                return self._create_generic_suggestion(pattern, emails)
                
        except Exception as e:
            logger.warning(f"⚠️ Error creating suggestion from pattern: {str(e)}")
            return None
    
    def _create_sender_suggestion(
        self, 
        pattern: EmailPattern, 
        emails: List[Dict]
    ) -> CategorySuggestion:
        """Create suggestion for sender-based pattern"""
        
        from damien_cli.features.ai_intelligence.models import RuleCondition, RuleAction, ActionType
        
        sender = pattern.characteristics.primary_feature
        
        # Determine appropriate action based on email volume and characteristics
        if pattern.email_count > 20:
            action_type = ActionType.ARCHIVE
            category_name = f"Auto-archive {sender}"
            description = f"Automatically archive emails from {sender} (high volume sender)"
        else:
            action_type = ActionType.LABEL
            category_name = f"Label {sender}"
            description = f"Label emails from {sender} for better organization"
        
        # Create rule conditions
        conditions = [
            RuleCondition(
                field="from_sender",
                operator="contains", 
                value=sender,
                confidence=pattern.confidence
            )
        ]
        
        # Create rule actions
        actions = [
            RuleAction(
                action_type=action_type,
                parameters={"label_name": f"From_{sender}"} if action_type == ActionType.LABEL else {}
            )
        ]
        
        return CategorySuggestion(
            category_name=category_name,
            description=description,
            email_count=pattern.email_count,
            affected_email_percentage=(pattern.email_count / len(emails)) * 100,
            confidence=pattern.confidence,
            rule_conditions=conditions,
            rule_actions=actions,
            example_email_ids=pattern.example_email_ids[:3],
            source_pattern_id=pattern.pattern_id,
            business_justification=f"Pattern shows consistent behavior with {pattern.confidence:.0%} confidence"
        )
    
    def _create_subject_suggestion(
        self, 
        pattern: EmailPattern, 
        emails: List[Dict]
    ) -> CategorySuggestion:
        """Create suggestion for subject-based pattern"""
        
        from damien_cli.features.ai_intelligence.models import RuleCondition, RuleAction, ActionType
        
        keywords = pattern.characteristics.common_keywords[:3]  # Top 3 keywords
        primary_keyword = keywords[0] if keywords else "Unknown"
        
        conditions = [
            RuleCondition(
                field="subject",
                operator="contains",
                value=primary_keyword,
                confidence=pattern.confidence
            )
        ]
        
        actions = [
            RuleAction(
                action_type=ActionType.LABEL,
                parameters={"label_name": f"Category_{primary_keyword.title()}"}
            )
        ]
        
        return CategorySuggestion(
            category_name=f"Auto-organize {primary_keyword.title()}",
            description=f"Organize emails with '{primary_keyword}' in subject",
            email_count=pattern.email_count,
            affected_email_percentage=(pattern.email_count / len(emails)) * 100,
            confidence=pattern.confidence,
            rule_conditions=conditions,
            rule_actions=actions,
            example_email_ids=pattern.example_email_ids[:3],
            source_pattern_id=pattern.pattern_id
        )
    
    def _create_cluster_suggestion(
        self, 
        pattern: EmailPattern, 
        emails: List[Dict]
    ) -> CategorySuggestion:
        """Create suggestion for cluster-based pattern"""
        
        from damien_cli.features.ai_intelligence.models import RuleCondition, RuleAction, ActionType
        
        theme = pattern.characteristics.primary_feature
        
        conditions = [
            RuleCondition(
                field="snippet",
                operator="contains",
                value=theme,
                confidence=pattern.confidence * 0.8  # Lower confidence for clusters
            )
        ]
        
        actions = [
            RuleAction(
                action_type=ActionType.LABEL,
                parameters={"label_name": f"Cluster_{theme.replace(' ', '_')}"}
            )
        ]
        
        return CategorySuggestion(
            category_name=f"Group: {theme}",
            description=f"Group similar emails about {theme}",
            email_count=pattern.email_count,
            affected_email_percentage=(pattern.email_count / len(emails)) * 100,
            confidence=pattern.confidence * 0.8,
            rule_conditions=conditions,
            rule_actions=actions,
            example_email_ids=pattern.example_email_ids[:3],
            source_pattern_id=pattern.pattern_id
        )
    
    def _create_time_suggestion(
        self, 
        pattern: EmailPattern, 
        emails: List[Dict]
    ) -> CategorySuggestion:
        """Create suggestion for time-based pattern"""
        
        from damien_cli.features.ai_intelligence.models import RuleCondition, RuleAction, ActionType
        
        time_pattern = pattern.characteristics.primary_feature
        
        conditions = [
            RuleCondition(
                field="age_days",
                operator="greater_than",
                value=7,
                confidence=pattern.confidence * 0.9
            )
        ]
        
        actions = [
            RuleAction(action_type=ActionType.ARCHIVE)
        ]
        
        return CategorySuggestion(
            category_name=f"Scheduled: {time_pattern}",
            description=f"Handle {time_pattern} emails automatically",
            email_count=pattern.email_count,
            affected_email_percentage=(pattern.email_count / len(emails)) * 100,
            confidence=pattern.confidence * 0.9,
            rule_conditions=conditions,
            rule_actions=actions,
            example_email_ids=pattern.example_email_ids[:3],
            source_pattern_id=pattern.pattern_id
        )
    
    def _create_label_suggestion(
        self, 
        pattern: EmailPattern, 
        emails: List[Dict]
    ) -> CategorySuggestion:
        """Create suggestion for label-based pattern"""
        
        from damien_cli.features.ai_intelligence.models import RuleCondition, RuleAction, ActionType
        
        label = pattern.characteristics.primary_feature
        
        conditions = [
            RuleCondition(
                field="label_names",
                operator="in",
                value=label,
                confidence=pattern.confidence
            )
        ]
        
        actions = [
            RuleAction(
                action_type=ActionType.LABEL,
                parameters={"label_name": f"Organized_{label}"}
            )
        ]
        
        return CategorySuggestion(
            category_name=f"Organize {label}",
            description=f"Better organize emails with {label} label",
            email_count=pattern.email_count,
            affected_email_percentage=(pattern.email_count / len(emails)) * 100,
            confidence=pattern.confidence,
            rule_conditions=conditions,
            rule_actions=actions,
            example_email_ids=pattern.example_email_ids[:3],
            source_pattern_id=pattern.pattern_id
        )
    
    def _create_generic_suggestion(
        self, 
        pattern: EmailPattern, 
        emails: List[Dict]
    ) -> CategorySuggestion:
        """Create generic suggestion for unknown pattern types"""
        
        from damien_cli.features.ai_intelligence.models import RuleCondition, RuleAction, ActionType
        
        conditions = [
            RuleCondition(
                field="snippet",
                operator="contains",
                value=pattern.characteristics.primary_feature,
                confidence=pattern.confidence * 0.7
            )
        ]
        
        actions = [
            RuleAction(
                action_type=ActionType.LABEL,
                parameters={"label_name": "AI_Detected_Pattern"}
            )
        ]
        
        return CategorySuggestion(
            category_name=f"Pattern: {pattern.pattern_name}",
            description=f"Detected pattern: {pattern.description}",
            email_count=pattern.email_count,
            affected_email_percentage=(pattern.email_count / len(emails)) * 100,
            confidence=pattern.confidence * 0.7,
            rule_conditions=conditions,
            rule_actions=actions,
            example_email_ids=pattern.example_email_ids[:3],
            source_pattern_id=pattern.pattern_id
        )
    
    def _create_analysis_summary(
        self, 
        emails: List[Dict], 
        patterns: List[EmailPattern], 
        suggestions: List[CategorySuggestion]
    ) -> Dict[str, Any]:
        """Create comprehensive analysis summary"""
        
        # Calculate basic statistics
        total_emails = len(emails)
        unique_senders = len(set(email['from_sender'] for email in emails))
        
        # Categorize by labels
        label_distribution = {}
        for email in emails:
            labels = email.get('label_names', [])
            for label in labels:
                label_distribution[label] = label_distribution.get(label, 0) + 1
        
        # Top senders
        sender_counts = {}
        for email in emails:
            sender = email['from_sender']
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Pattern type distribution
        pattern_type_dist = {}
        for pattern in patterns:
            ptype = pattern.pattern_type.value
            pattern_type_dist[ptype] = pattern_type_dist.get(ptype, 0) + 1
        
        # Business metrics
        potential_automation = sum(s.email_count for s in suggestions if s.confidence >= 0.7)
        time_savings = sum(s.estimated_time_savings_minutes for s in suggestions) / 60  # hours
        
        return {
            'total_emails': total_emails,
            'unique_senders': unique_senders,
            'patterns_found': len(patterns),
            'high_confidence_patterns': len([p for p in patterns if p.confidence >= 0.8]),
            'suggestions_generated': len(suggestions),
            'actionable_suggestions': len([s for s in suggestions if s.confidence >= 0.7]),
            'label_distribution': dict(sorted(label_distribution.items(), key=lambda x: x[1], reverse=True)[:10]),
            'top_senders': top_senders,
            'pattern_type_distribution': pattern_type_dist,
            'potential_automation_emails': potential_automation,
            'estimated_time_savings_hours': time_savings,
            'automation_rate_percent': (potential_automation / max(total_emails, 1)) * 100,
            'analysis_date': datetime.now().isoformat(),
            'data_quality_score': min(1.0, len(emails) / 100),  # Based on sample size
        }
    
    def _create_empty_result(self, start_time: datetime, operation_name: str) -> EmailAnalysisResult:
        """Create empty result when no emails found"""
        
        end_time = datetime.now()
        performance_metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            items_processed=0
        )
        
        return EmailAnalysisResult(
            total_emails_analyzed=0,
            patterns_detected=[],
            category_suggestions=[],
            processing_performance=performance_metrics,
            summary_statistics={'total_emails': 0, 'message': 'No emails found'},
            data_sources=['gmail_api'],
            analysis_parameters={}
        )
    
    async def quick_pattern_check(
        self,
        sample_size: int = 100,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Quick pattern check for testing and validation"""
        
        logger.info(f"🔍 Running quick pattern check (sample: {sample_size}, days: {days_back})")
        
        try:
            # Fetch small sample
            emails = await self._fetch_emails(sample_size, days_back)
            
            if not emails:
                return {"status": "no_emails", "message": "No emails found"}
            
            # Quick analysis without embeddings
            senders = {}
            subjects = []
            
            for email in emails:
                sender = email.get('from_sender', 'Unknown')
                senders[sender] = senders.get(sender, 0) + 1
                subjects.append(email.get('subject', ''))
            
            # Find top senders
            top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Simple keyword analysis
            all_subjects = ' '.join(subjects).lower()
            common_words = []
            for word in ['newsletter', 'receipt', 'order', 'notification', 'update']:
                if word in all_subjects:
                    common_words.append(word)
            
            result = {
                "status": "success",
                "emails_analyzed": len(emails),
                "unique_senders": len(senders),
                "top_senders": top_senders,
                "common_keywords": common_words,
                "potential_patterns": len(top_senders) + len(common_words),
                "recommendation": "Run full analysis" if len(emails) > 50 else "Increase sample size"
            }
            
            logger.info(f"✅ Quick check complete: {result['potential_patterns']} potential patterns")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in quick pattern check: {str(e)}")
            return {"status": "error", "message": str(e)}
