"""
HITL Escalation notifier for Telegram CS group.

Sends formatted notification to a Telegram group when
the AI system escalates a conversation to human CS.
"""

from typing import Dict, Any
from datetime import datetime

from app.config import settings


async def notify_cs_group(
    user_info: Dict[str, Any],
    escalation_result: Dict[str, Any],
    history_snippet: str = ""
) -> bool:
    """
    Send escalation notification to CS group chat.

    Non-blocking: failure is logged but never raises.

    Args:
        user_info: dict with keys: username, user_id, chat_id, message_id, session_id
        escalation_result: full result dict from CoreChain
        history_snippet: recent conversation history

    Returns:
        bool: True if notification sent successfully
    """
    cs_chat_id = getattr(settings, 'TELEGRAM_CS_GROUP_CHAT_ID', None)
    if not cs_chat_id:
        print("WARNING: TELEGRAM_CS_GROUP_CHAT_ID not configured, skipping CS notification")
        return False

    message = _format_escalation_message(user_info, escalation_result, history_snippet)

    try:
        from app.channels.telegram.client import get_telegram_client
        client = get_telegram_client()
        success = await client.send_message(
            chat_id=int(cs_chat_id),
            text=message
        )
        if success:
            print(f"ESCALATION: CS group notified for user @{user_info.get('username', 'unknown')}")
        else:
            print(f"ERROR: Failed to send CS group notification")
        return success
    except Exception as e:
        print(f"ERROR: CS group notification failed: {e}")
        return False


def _format_escalation_message(
    user_info: Dict[str, Any],
    escalation_result: Dict[str, Any],
    history_snippet: str = ""
) -> str:
    """Format the escalation notification for CS group."""
    username = user_info.get('username', 'unknown')
    user_id = user_info.get('user_id', 'unknown')
    chat_id = user_info.get('chat_id', 'unknown')
    reason = escalation_result.get('escalation_reason', 'Unknown reason')
    stage = escalation_result.get('escalation_stage', 'unknown')
    original_query = escalation_result.get('original_query', '')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    parts = [
        "--- ESCALATION ALERT ---",
        "",
        f"User: @{username} (ID: {user_id})",
        f"Chat ID: {chat_id}",
        f"Time: {timestamp}",
        f"Stage: {stage}",
        f"Reason: {reason}",
        "",
        f"Query: {original_query}",
    ]

    if history_snippet:
        truncated = history_snippet[:500]
        if len(history_snippet) > 500:
            truncated += "..."
        parts.extend(["", "Recent History:", truncated])

    parts.extend(["", "Please respond to this user directly in their chat."])

    return "\n".join(parts)
