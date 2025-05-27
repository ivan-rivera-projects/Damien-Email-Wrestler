import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
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
                query=query,
                max_results=batch_size,
                page_token=page_token
            )
            
            email_summaries.extend(result["messages"])
            page_token = result.get("next_page_token")
            
            if not page_token:
                break
        
        click.echo(f"Analyzing {len(email_summaries)} emails...")
        
        # Generate embeddings
        embeddings = self.embedding_generator.generate_batch_embeddings(email_summaries)
        
        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(email_summaries, embeddings)
        
        # Generate categories
        categories = self._patterns_to_categories(patterns)
        
        # Save results
        self._save_categories(categories)
        self._save_patterns(patterns)
        
        return {
            "emails_analyzed": len(email_summaries),
            "patterns_found": len(patterns),
            "categories_identified": len(categories),
            "categories": categories,
            "top_suggestions": self._generate_top_suggestions(patterns, categories)
        }
    
    def _patterns_to_categories(self, patterns: List[Dict]) -> List[EmailCategory]:
        """Convert detected patterns into email categories"""
        
        categories = []
        
        # Group patterns by type
        pattern_groups = {}
        for pattern in patterns:
            pattern_type = pattern["type"]
            if pattern_type not in pattern_groups:
                pattern_groups[pattern_type] = []
            pattern_groups[pattern_type].append(pattern)
        
        # Create categories from pattern groups
        for pattern_type, type_patterns in pattern_groups.items():
            if pattern_type == "newsletter":
                category = EmailCategory(
                    name="Newsletters & Digests",
                    description="Regular updates and newsletters",
                    confidence=0.9,
                    suggested_rules=[{
                        "name": "Auto-archive newsletters",
                        "conditions": [
                            {"field": "subject", "operator": "contains", "value": "newsletter"}
                        ],
                        "action": "archive"
                    }],
                    example_emails=[p["example_emails"][0] for p in type_patterns[:3] 
                                   if "example_emails" in p]
                )
                categories.append(category)
                
            elif pattern_type == "high_volume_sender":
                for pattern in type_patterns[:5]:  # Top 5 high volume senders
                    category = EmailCategory(
                        name=f"Emails from {pattern['sender']}",
                        description=f"High volume sender ({pattern['email_count']} emails)",
                        confidence=0.85,
                        suggested_rules=[{
                            "name": f"Manage {pattern['sender']}",
                            "conditions": pattern["suggested_rule"]["conditions"],
                            "action": "label",
                            "parameters": {"label_name": f"Sender/{pattern['sender'].split('@')[0]}"}
                        }]
                    )
                    categories.append(category)
                    
            elif pattern_type == "cluster":
                # Create category from cluster characteristics
                chars = pattern["characteristics"]
                if chars.get("common_subject_words"):
                    name = f"{chars['common_subject_words'][0].title()} Emails"
                elif chars.get("common_sender"):
                    name = f"Emails like {chars['common_sender']}"
                else:
                    name = f"Email Group {len(categories) + 1}"
                    
                category = EmailCategory(
                    name=name,
                    description=f"Group of {pattern['email_count']} similar emails",
                    confidence=0.75,
                    suggested_rules=[pattern["suggested_rule"]] if "suggested_rule" in pattern else []
                )
                categories.append(category)
        
        return categories
    
    def _generate_top_suggestions(self, patterns: List[Dict], 
                                categories: List[EmailCategory]) -> List[Dict]:
        """Generate top rule suggestions based on patterns and categories"""
        
        suggestions = []
        
        # High-impact suggestions (would affect many emails)
        for pattern in sorted(patterns, key=lambda p: p.get("email_count", 0), reverse=True)[:5]:
            if "suggested_rule" in pattern:
                suggestion = {
                    "impact": pattern["email_count"],
                    "type": pattern["type"],
                    "rule": pattern["suggested_rule"],
                    "description": self._describe_suggestion(pattern)
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _describe_suggestion(self, pattern: Dict) -> str:
        """Generate human-readable description of a suggestion"""
        
        if pattern["type"] == "newsletter":
            return f"Archive {pattern['email_count']} newsletter emails automatically"
        elif pattern["type"] == "high_volume_sender":
            return f"Organize {pattern['email_count']} emails from {pattern['sender']}"
        elif pattern["type"] == "cluster":
            chars = pattern["characteristics"]
            if chars.get("common_subject_words"):
                return f"Handle {pattern['email_count']} emails about {chars['common_subject_words'][0]}"
            else:
                return f"Manage group of {pattern['email_count']} similar emails"
        else:
            return f"Process {pattern['email_count']} emails"
    
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