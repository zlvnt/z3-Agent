"""
Conversation management for Instagram channel (JSON-based).

Note: This is used by the Instagram channel which is currently disabled.
Telegram uses its own SQLite/PostgreSQL memory system.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings


class ConversationManager:
    """JSON file-based conversation manager for Instagram."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or settings.CONVERSATIONS_PATH
        Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)
        self._conversations: Dict[str, List[Dict]] = self._load()

    def _load(self) -> Dict[str, List[Dict]]:
        """Load conversations from JSON file."""
        try:
            if Path(self.file_path).exists():
                with open(self.file_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load conversations: {e}")
        return {}

    def _save(self):
        """Save conversations to JSON file."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(self._conversations, f, indent=2)
        except Exception as e:
            print(f"Failed to save conversations: {e}")

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to a conversation."""
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        self._conversations[session_id].append({
            "role": role,
            "content": content,
        })
        self._save()

    def get_history(self, session_id: str, last_n: int = 10) -> str:
        """Get formatted conversation history."""
        messages = self._conversations.get(session_id, [])
        if not messages:
            return ""
        recent = messages[-last_n:]
        return "\n".join(f"{m['role']}: {m['content']}" for m in recent)

    def clear(self, session_id: str):
        """Clear conversation history for a session."""
        self._conversations.pop(session_id, None)
        self._save()


# Global instance
_manager = None


def _get_manager() -> ConversationManager:
    global _manager
    if _manager is None:
        _manager = ConversationManager()
    return _manager


def add(post_id: str, comment_id: str, data: Dict) -> None:
    """
    Save a conversation entry (used by reply.py for Instagram replies).

    Args:
        post_id: Instagram post ID
        comment_id: Instagram comment ID
        data: Dict with user, comment, reply
    """
    manager = _get_manager()
    session_id = f"{post_id}_{comment_id}"
    manager.add_message(session_id, "user", data.get("comment", ""))
    manager.add_message(session_id, "bot", data.get("reply", ""))
