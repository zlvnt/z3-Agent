"""
Instagram channel handler - refactored from conditional_chain.py logic.
"""

from typing import Dict, Any
from app.channels.base import BaseChannel


class InstagramChannel(BaseChannel):
    """Instagram channel implementation using existing Instagram logic."""
    
    def __init__(self):
        """Initialize Instagram channel."""
        print("🤖 InstagramChannel initialized")
    
    async def process_message(self, raw_data: Dict[str, Any]) -> str:
        """Process Instagram comment through existing logic."""
        try:
            # Extract Instagram-specific data
            message_data = self.extract_message_data(raw_data)
            
            # Basic validation
            if not message_data or not isinstance(message_data, dict):
                return "Invalid Instagram comment data format"
            
            if not self.should_process_message(message_data):
                return "Instagram comment skipped (bot, empty, or filtered)"
            
            # Get session ID for Instagram
            session_id = self.get_session_id(message_data)
            
            # Process through Instagram core chain
            from .chain import process_instagram_message_with_core
            
            reply = await process_instagram_message_with_core(
                comment=message_data['comment'],
                post_id=message_data['post_id'],
                comment_id=message_data['comment_id'],
                username=message_data['username'],
                history=""  # Instagram doesn't use conversation history currently
            )
            
            # Send reply (reuse existing Instagram API)
            send_metadata = {
                'comment_id': message_data['comment_id'],
                'username': message_data['username']
            }
            
            success = await self.send_reply(reply, send_metadata)
            
            if success:
                print(f"✅ Instagram reply sent to @{message_data['username']}")
                return f"Instagram comment processed successfully for {session_id}"
            else:
                return "Failed to send Instagram reply"
                
        except Exception as e:
            print(f"❌ Error in Instagram process_message: {e}")
            return f"Error: {str(e)}"
    
    def get_session_id(self, message_data: Dict[str, Any]) -> str:
        """Generate session ID for Instagram comments."""
        post_id = message_data.get('post_id', 'unknown')
        comment_id = message_data.get('comment_id', 'unknown')
        return f"ig_post_{post_id}_comment_{comment_id}"
    
    async def send_reply(self, reply: str, metadata: Dict[str, Any]) -> bool:
        """Send reply to Instagram comment using existing API."""
        try:
            from app.services.instagram_api import upload_reply
            
            comment_id = metadata.get('comment_id')
            if not comment_id:
                return False
                
            result = upload_reply(comment_id, reply)
            success = not ("error" in result)
            return success
            
        except Exception as e:
            print(f"❌ Failed to send Instagram reply: {e}")
            return False
    
    def extract_message_data(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Instagram comment data from webhook format."""
        try:
            # Simple extraction - expecting existing webhook format
            return {
                'comment': raw_input.get('comment', ''),
                'post_id': raw_input.get('post_id', ''),
                'comment_id': raw_input.get('comment_id', ''),
                'username': raw_input.get('username', ''),
                'timestamp': raw_input.get('timestamp', 0)
            }
        except Exception as e:
            raise ValueError(f"Failed to extract Instagram comment data: {e}")
    
    def should_process_message(self, message_data: Dict[str, Any]) -> bool:
        """Check if Instagram comment should be processed."""
        # Basic validation
        if not message_data.get('comment', '').strip():
            return False
            
        # Skip if no required fields
        required_fields = ['comment', 'post_id', 'comment_id', 'username']
        for field in required_fields:
            if not message_data.get(field):
                return False
                
        # Skip bot comments (existing logic)
        username = message_data.get('username', '')
        if username == 'z3_agent':  # Bot username
            print(f"🔄 Skipping comment from bot itself: {username}")
            return False
            
        return True


# Global instance
_instagram_channel = None

def get_instagram_channel() -> InstagramChannel:
    """Get global InstagramChannel instance."""
    global _instagram_channel
    if _instagram_channel is None:
        _instagram_channel = InstagramChannel()
    return _instagram_channel