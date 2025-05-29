from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass

@dataclass
class ContextItem:
    """Individual context item with priority"""
    content: str
    priority: float
    token_count: int
    category: str
    metadata: Dict[str, Any]

class ContextPrioritizer:
    """
    Determines the priority of a context item.
    This is a placeholder and should be expanded with more sophisticated logic.
    """
    def prioritize(self, item_content: str, item_metadata: Dict[str, Any]) -> float:
        """
        Assigns a priority score to a context item.
        Higher scores mean higher priority.

        Args:
            item_content: The textual content of the item.
            item_metadata: Metadata associated with the item, which might include
                           pre-assigned priority, source, type, etc.

        Returns:
            A float representing the priority score (e.g., 0.0 to 1.0).
        """
        # Placeholder logic:
        # - Check if metadata already contains a 'priority' field.
        # - Could analyze content for keywords (e.g., "urgent", "important").
        # - Could consider the source or type of the context item.
        # For now, just returns a pre-set priority if available, else a default.
        return item_metadata.get('priority', 0.5)

class ContextWindowOptimizer:
    """Optimizes context for LLM token limits"""
    
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.reserved_tokens = 2000  # For prompt and response
        self.prioritizer = ContextPrioritizer()
    
    def optimize_context(
        self,
        items: List[ContextItem],
        required_items: List[ContextItem] = None,
        target_tokens: Optional[int] = None
    ) -> List[ContextItem]:
        """Optimize context items to fit token limit"""
        
        if target_tokens is None:
            target_tokens = self.max_tokens - self.reserved_tokens
        
        # Always include required items
        selected = required_items or []
        used_tokens = sum(item.token_count for item in selected)
        
        # Sort remaining items by priority
        remaining = [i for i in items if i not in selected]
        remaining.sort(key=lambda x: x.priority, reverse=True)
        
        # Greedy selection with diversity
        categories_seen = set()
        for item in remaining:
            if used_tokens + item.token_count <= target_tokens:
                # Boost priority for category diversity
                if item.category not in categories_seen:
                    selected.append(item)
                    used_tokens += item.token_count
                    categories_seen.add(item.category)
                elif item.priority > 0.8:  # High priority items
                    selected.append(item)
                    used_tokens += item.token_count
        
        return selected
    
    def create_sliding_window(
        self,
        emails: List[Dict[str, Any]],
        window_size: int = 10,
        overlap: int = 2
    ) -> List[List[Dict[str, Any]]]:
        """Create overlapping windows for batch processing"""
        
        windows = []
        for i in range(0, len(emails), window_size - overlap):
            window = emails[i:i + window_size]
            if window:
                windows.append(window)
        
        return windows
    
    def compress_email_content(
        self,
        email: Dict[str, Any],
        target_length: int = 500
    ) -> str:
        """Intelligently compress email content"""
        
        content = email.get('content', '')
        
        # If already short enough, return as-is
        if len(content) <= target_length:
            return content
        
        # Smart truncation preserving important parts
        lines = content.split('\n')
        important_lines = []
        
        # Priority patterns
        priority_patterns = [
            'action required',
            'deadline',
            'urgent',
            'important',
            'please',
            'would you',
            'can you'
        ]
        
        # First pass: collect important lines
        for line in lines:
            line_lower = line.lower()
            if any(pattern in line_lower for pattern in priority_patterns):
                important_lines.append(line)
        
        # Build compressed version
        if important_lines:
            compressed = '\n'.join(important_lines)
        else:
            # If no important lines found, use the original content for potential truncation
            compressed = content

        # If the result (either from important lines or original content) is too long, truncate with ellipsis
        if len(compressed) > target_length:
            # Ensure target_length-3 is not negative if target_length is very small
            ellipsis_point = max(0, target_length - 3)
            compressed = compressed[:ellipsis_point] + '...'
        
        return compressed