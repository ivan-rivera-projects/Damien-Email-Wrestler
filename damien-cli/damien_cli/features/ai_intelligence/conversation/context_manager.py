import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from ..models import ConversationContext
from damien_cli.core.config import DATA_DIR

class ConversationContextManager:
    """Manages conversation contexts across sessions"""
    
    def __init__(self):
        self.contexts_dir = Path(DATA_DIR) / "conversation_contexts"
        self.contexts_dir.mkdir(exist_ok=True)
        
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing context or create new one"""
        
        context_file = self.contexts_dir / f"{session_id}.json"
        
        if context_file.exists():
            with open(context_file, "r") as f:
                data = json.load(f)
                return ConversationContext(**data)
        else:
            return ConversationContext(session_id=session_id, messages=[])
    
    def save_context(self, context: ConversationContext):
        """Save context to disk"""
        
        context_file = self.contexts_dir / f"{context.session_id}.json"
        with open(context_file, "w") as f:
            json.dump(context.dict(), f, indent=2, default=str)
    
    def clear_context(self, session_id: str):
        """Clear a conversation context"""
        
        context_file = self.contexts_dir / f"{session_id}.json"
        if context_file.exists():
            context_file.unlink()
    
    def list_sessions(self) -> List[Dict]:
        """List all conversation sessions"""
        
        sessions = []
        for context_file in self.contexts_dir.glob("*.json"):
            with open(context_file, "r") as f:
                data = json.load(f)
                sessions.append({
                    "session_id": data["session_id"],
                    "message_count": len(data["messages"]),
                    "last_updated": context_file.stat().st_mtime
                })
        
        return sorted(sessions, key=lambda x: x["last_updated"], reverse=True)