"""
Simple request logging for user interactions.
Logs user requests with timestamps for monitoring dashboard.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from app.config import settings

class RequestLogger:
    """Simple request logger for early-stage monitoring"""
    
    def __init__(self, log_file: str = None):
        self.log_file = Path(log_file or settings.REQUEST_LOG_FILE)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.max_query_length = settings.REQUEST_LOG_MAX_QUERY_LENGTH
    
    def log_request(
        self, 
        channel: str,
        username: str,
        query: str,
        routing_mode: str,
        duration: float,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Log a complete user request"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "channel": channel,
            "username": username,
            "query": query[:self.max_query_length] + "..." if len(query) > self.max_query_length else query,  # Truncate long queries
            "routing_mode": routing_mode,
            "duration": round(duration, 3),
            "success": success,
            "error": error_message if error_message else None
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"WARNING: Failed to write request log: {e}")
    
    def get_recent_requests(self, limit: int = 20) -> list:
        """Get recent request logs"""
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            recent_logs = []
            for line in lines[-limit:]:
                try:
                    entry = json.loads(line.strip())
                    recent_logs.append(entry)
                except json.JSONDecodeError:
                    continue
            
            return recent_logs
        except Exception as e:
            print(f"WARNING: Failed to read request logs: {e}")
            return []


# Global request logger instance
_request_logger: Optional[RequestLogger] = None

def get_request_logger() -> RequestLogger:
    """Get global request logger instance"""
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
    error_message: Optional[str] = None
) -> None:
    """Convenience function to log user request"""
    logger = get_request_logger()
    logger.log_request(channel, username, query, routing_mode, duration, success, error_message)