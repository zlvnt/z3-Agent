"""
Centralized conversation history service for consistent history handling
across all agents (reply, supervisor, etc.)
"""

from typing import Optional


class ConversationHistoryService:
    """
    Centralized service for conversation history management.
    Provides consistent history formatting and limits across all agents.
    """
    
    DEFAULT_LIMIT = 5
    
    @staticmethod 
    def get_history_context(post_id: str, comment_id: str, limit: Optional[int] = None) -> str:
        """
        Get formatted conversation history for any agent.
        
        Args:
            post_id: Instagram post ID
            comment_id: Instagram comment ID  
            limit: Number of conversations to retrieve (default: 5)
            
        Returns:
            Formatted conversation history string
        """
        if limit is None:
            limit = ConversationHistoryService.DEFAULT_LIMIT
        
        try:
            # Reuse existing conversation loading logic
            from app.services.conversation import get_comment_history
            history = get_comment_history(post_id, comment_id)
            
            if not history:
                return ""
            
            # Get last N conversations
            slices = history[-limit:]
            ctx_lines = ["Riwayat Percakapan Sebelumnya:"]
            
            for h in slices:
                ctx_lines.append(f"{h['user']}: {h['comment']}")
                ctx_lines.append(f"z3: {h['reply']}")
                
            return "\n".join(ctx_lines)
            
        except Exception as e:
            print(f"WARNING: History service failed: {e}")
            return ""
    
    @staticmethod
    def get_optimized_history_for_reply(post_id: str, comment_id: str, limit: Optional[int] = None) -> str:
        """
        Get history formatted specifically for reply agent's optimized template.
        This maintains compatibility with the professional CS template format.
        """
        raw_history = ConversationHistoryService.get_history_context(post_id, comment_id, limit)
        
        if not raw_history:
            return "No previous interaction."
            
        return raw_history.strip()