import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path

from damien_cli.core_api.gmail_api_service import list_messages, get_message_details
from damien_cli.core.config import DATA_DIR
from .embeddings import EmailEmbeddingGenerator
from .patterns import EmailPatternDetector
from ..models import EmailCategory

class EmailCategorizer:
    """Main class for email categorization and rule suggestions"""
    
    def __init__(self):
        self.embedding_generator = EmailEmbeddingGenerator()
        self.pattern_detector = EmailPatternDetector()
        self.categories_file = Path(DATA_DIR) / "email_categories.json"
        self.learned_patterns_file = Path(DATA_DIR) / "learned_patterns.json"
        
    async def analyze_emails(self, 
                           query: Optional[str] = None,
                           max_emails: int = 500,
                           days_back: int = 30) -> Dict:
        """Analyze emails and generate categorization insights"""
        
        # Build query
        if not query:
            date_filter = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
            query = f"after:{date_filter}"
        
        # Fetch emails
        import click
        click.echo(f"Fetching emails with query: {query}")
        email_summaries = []
        page_token = None
        
        while len(email_summaries) < max_emails:
            batch_size = min(100, max_emails - len(email_summaries))
            result = list_messages(
                gmail_service=self._get_gmail_service(),
                query_string=query,
                max_results=batch_size,
                page_token=page_token
            )
            
            if not result.get("messages"):
                break
                
            email_summaries.extend(result["messages"])
            page_token = result.get("next_page_token")
            
            if not page_token:
                break
        
        click.echo(f"Analyzing {len(email_summaries)} emails...")
        
        # Generate embeddings - make this robust by providing a fallback
        try:
            embeddings = self.embedding_generator.generate_batch_embeddings(email_summaries)
        except Exception as e:
            click.echo(f"Warning: Could not generate embeddings: {e}")
            embeddings = []
        
        # Detect patterns - handle potential exceptions
        try:
            patterns = self.pattern_detector.detect_patterns(email_summaries, embeddings)
        except Exception as e:
            click.echo(f"Warning: Error in pattern detection: {e}")
            patterns = []
        
        # Generate categories - handle exceptions
        try:
            categories = self._patterns_to_categories(patterns)
        except Exception as e:
            click.echo(f"Warning: Error generating categories: {e}")
            categories = []
        
        # Save results - handle exceptions
        try:
            self._save_categories(categories)
            self._save_patterns(patterns)
        except Exception as e:
            click.echo(f"Warning: Could not save results: {e}")
        
        return {
            "emails_analyzed": len(email_summaries),
            "patterns_found": len(patterns),
            "categories_identified": len(categories),
            "categories": categories,
            "top_suggestions": self._generate_top_suggestions(patterns, categories)
        }
    
    def _patterns_to_categories(self, patterns: List[Dict]) -> List[EmailCategory]:
        """Convert detected patterns into email categories"""

        from collections import defaultdict
        categories = []

        # Group patterns by type for better category organization
        pattern_groups = defaultdict(list)
        for pattern in patterns:
            pattern_groups[pattern["type"]].append(pattern)

        # Process each pattern type
        if "newsletter" in pattern_groups:
            newsletter_patterns = pattern_groups["newsletter"]
            if newsletter_patterns:
                # Combine similar newsletter patterns into one category
                total_emails = sum(p["email_count"] for p in newsletter_patterns)
                example_emails = [e for p in newsletter_patterns for e in p.get("example_emails", [])][:3]
                categories.append(EmailCategory(
                    name="Newsletters & Digests",
                    description=f"Recurring updates and newsletters ({total_emails} emails)",
                    confidence=0.9,
                    suggested_rules=[{
                        "name": "Auto-archive newsletters",
                        "conditions": [{"field": "subject", "operator": "contains", "value": "newsletter"}],
                        "action": "archive"
                    }],
                    example_emails=example_emails
                ))

        if "high_volume_sender" in pattern_groups:
            # Create a category for each high volume sender (top 5)
            for pattern in sorted(pattern_groups["high_volume_sender"], key=lambda p: p["email_count"], reverse=True)[:5]:
                categories.append(EmailCategory(
                    name=f"Emails from {pattern['sender']}",
                    description=f"High volume sender ({pattern['email_count']} emails)",
                    confidence=0.85,
                    suggested_rules=[{
                        "name": f"Manage {pattern['sender']}",
                        "conditions": pattern["suggested_rule"]["conditions"],
                        "action": "label",
                        "parameters": {"label_name": f"Sender/{pattern['sender'].split('@')[0]}"}
                    }]
                ))

        if "cluster" in pattern_groups:
            # Create categories from significant clusters
            for pattern in sorted(pattern_groups["cluster"], key=lambda p: p["email_count"], reverse=True)[:10]: # Top 10 clusters
                 chars = pattern["characteristics"]
                 name = "Email Group"
                 description_parts = []

                 if chars.get("common_subject_words"):
                     name = f"{chars['common_subject_words'][0].title()} Emails"
                     description_parts.append(f"about {', '.join(chars['common_subject_words'])}")
                 if chars.get("common_sender"):
                     if name == "Email Group": name = f"Emails like {chars['common_sender']}"
                     description_parts.append(f"from {chars['common_sender']}")
                 if chars.get("common_labels"):
                     description_parts.append(f"with labels {', '.join(chars['common_labels'])}")
                 if chars.get("common_phrases"):
                      description_parts.append(f"containing '{chars['common_phrases'][0]}'")


                 description = f"Group of {pattern['email_count']} similar emails"
                 if description_parts:
                     description += " " + " and ".join(description_parts)


                 categories.append(EmailCategory(
                     name=name,
                     description=description,
                     confidence=pattern.get("suggested_rule", {}).get("confidence", 0.75), # Use rule confidence if available
                     suggested_rules=[pattern["suggested_rule"]] if "suggested_rule" in pattern else []
                 ))

        if "label_association" in pattern_groups:
             # Create categories based on label associations
             for pattern in pattern_groups["label_association"][:5]: # Top 5 label associations
                 chars = pattern["characteristics"]
                 description_parts = []
                 if chars.get("common_domains"):
                     description_parts.append(f"often from {', '.join(chars['common_domains'])}")
                 if chars.get("common_subject_keywords"):
                     description_parts.append(f"often about {', '.join(chars['common_subject_keywords'])}")

                 description = f"Emails typically labeled '{pattern['label']}'"
                 if description_parts:
                     description += " " + " and ".join(description_parts)

                 categories.append(EmailCategory(
                     name=f"Emails labeled '{pattern['label']}'",
                     description=description,
                     confidence=pattern.get("suggested_rule", {}).get("confidence", 0.7),
                     suggested_rules=[pattern["suggested_rule"]] if "suggested_rule" in pattern else []
                 ))

        if "time_based" in pattern_groups:
             # Create categories for significant time-based patterns
             for pattern in sorted(pattern_groups["time_based"], key=lambda p: p["email_count"], reverse=True)[:5]: # Top 5 time patterns
                 chars = pattern["characteristics"]
                 categories.append(EmailCategory(
                     name=f"Emails received around {chars['hour']}:00 on {chars['day_of_week']}",
                     description=f"Recurring emails received at a specific time ({pattern['email_count']} emails)",
                     confidence=pattern.get("suggested_rule", {}).get("confidence", 0.6),
                     suggested_rules=[pattern["suggested_rule"]] if "suggested_rule" in pattern else []
                 ))


        return categories

    def _generate_top_suggestions(self, patterns: List[Dict],
                                categories: List[EmailCategory]) -> List[Dict]:
        """Generate top rule suggestions based on patterns and categories"""

        suggestions = []

        # Collect all suggested rules from patterns
        for pattern in patterns:
            if "suggested_rule" in pattern and pattern["suggested_rule"]:
                suggestions.append({
                    "impact": pattern.get("email_count", 0), # Use email count as impact metric
                    "type": pattern["type"],
                    "rule": pattern["suggested_rule"],
                    "description": self._describe_suggestion(pattern)
                })

        # Sort suggestions by confidence and impact (higher confidence and impact first)
        suggestions.sort(key=lambda s: (s["rule"].get("confidence", 0), s["impact"]), reverse=True)

        # Return top N suggestions (e.g., top 10)
        return suggestions[:10]


    def _describe_suggestion(self, pattern: Dict) -> str:
        """Generate human-readable description of a suggestion"""

        rule = pattern.get("suggested_rule", {})
        if not rule:
            return "No rule suggested"

        description = f"Suggesting a rule to {rule['actions'][0]['type']}"

        conditions = rule.get("conditions", [])
        if conditions:
            condition_descriptions = []
            for cond in conditions:
                if cond["field"] == "from":
                    condition_descriptions.append(f"from '{cond['value']}'")
                elif cond["field"] == "subject":
                    condition_descriptions.append(f"with subject containing '{cond['value']}'")
                elif cond["field"] == "label":
                     condition_descriptions.append(f"with label '{cond['value']}'")
                elif cond["field"] == "age_days":
                     condition_descriptions.append(f"older than {cond['value']} days")
                # Add descriptions for other fields as needed

            if condition_descriptions:
                description += " for emails " + rule.get("condition_conjunction", "AND") + " ".join(condition_descriptions)

        if rule["actions"][0]["type"] == "label" and "label_name" in rule["actions"][0]:
            description += f" with label '{rule['actions'][0]['label_name']}'"

        description += f" (Confidence: {rule.get('confidence', 0):.0%})"

        return description
    
    def _save_categories(self, categories: List[EmailCategory]):
        """Save categories to file"""
        data = [cat.dict() for cat in categories]
        with open(self.categories_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _save_patterns(self, patterns: List[Dict]):
        """Save learned patterns"""
        with open(self.learned_patterns_file, "w") as f:
            json.dump(patterns, f, indent=2, default=str)
    
    def _get_gmail_service(self):
        """Get Gmail service from context"""
        # This would come from Click context in real implementation
        from damien_cli.core_api.gmail_api_service import get_authenticated_service
        return get_authenticated_service()