"""
Request logger for z3-Agent.

Logs user requests to JSONL file for analysis and debugging.
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.config import settings


class RequestLogger:
    """Logs user requests to a JSONL file."""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or settings.REQUEST_LOG_FILE
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        self._recent: List[Dict[str, Any]] = []

    def log_request(
        self,
        channel: str,
        username: str,
        query: str,
        routing_mode: str,
        duration: float,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """Log a request to file and in-memory buffer."""
        max_len = settings.REQUEST_LOG_MAX_QUERY_LENGTH
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "channel": channel,
            "username": username,
            "query": query[:max_len] if len(query) > max_len else query,
            "routing_mode": routing_mode,
            "duration": round(duration, 4),
            "success": success,
        }
        if error_message:
            entry["error"] = error_message

        # Write to file
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Failed to write request log: {e}")

        # Keep in memory
        self._recent.append(entry)
        if len(self._recent) > 100:
            self._recent = self._recent[-100:]

    def get_recent_requests(self, n: int = 20) -> List[Dict[str, Any]]:
        """Get the last N logged requests."""
        return self._recent[-n:]


# Global instance
_request_logger = None


def get_request_logger() -> RequestLogger:
    """Get global request logger instance."""
    global _request_logger
    if _request_logger is None:
        _request_logger = RequestLogger()
    return _request_logger


def log_user_request(
    channel: str,
    username: str,
    query: str,
    routing_mode: str,
    duration: float,
    success: bool,
    error_message: Optional[str] = None,
) -> None:
    """Convenience function to log user request."""
    logger = get_request_logger()
    logger.log_request(channel, username, query, routing_mode, duration, success, error_message)
