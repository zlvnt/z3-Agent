"""
Enhanced metrics collection for z3-Agent.

Tracks requests, errors, response times, channel stats, user activity,
RAG routing distribution, and alert conditions.
"""

import time
from collections import defaultdict
from typing import Dict, Any, Optional


class EnhancedMetrics:
    """Comprehensive in-memory metrics tracker."""

    WINDOW_SIZE = 1000
    MAX_USERS = 10000
    MAX_ERROR_CATEGORIES = 100

    def __init__(self):
        self._start_time = time.time()

        # Basic counters
        self._total_requests = 0
        self._total_errors = 0
        self._response_times: list[float] = []

        # Recent activity tracking (timestamps)
        self._recent_requests: list[float] = []
        self._recent_errors: list[float] = []

        # Channel stats
        self._channels: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "requests": 0,
                "errors": 0,
                "response_times": [],
                "recent_requests": [],
                "recent_errors": [],
            }
        )

        # User stats
        self._users_today: set = set()
        self._repeat_users_today: set = set()
        self._user_sessions: Dict[str, int] = defaultdict(int)

        # RAG stats
        self._routing_decisions: Dict[str, int] = defaultdict(int)
        self._rag_queries = 0
        self._rag_successes = 0

        # Error categories
        self._error_categories: Dict[str, int] = defaultdict(int)

    def record_request(self, duration: float, success: bool = True):
        """Record a basic request."""
        now = time.time()
        self._total_requests += 1
        self._response_times.append(duration)
        self._recent_requests.append(now)

        if not success:
            self._total_errors += 1
            self._recent_errors.append(now)

        # Trim to window
        if len(self._response_times) > self.WINDOW_SIZE:
            self._response_times = self._response_times[-self.WINDOW_SIZE:]
        self._recent_requests = [t for t in self._recent_requests if now - t < 3600]
        self._recent_errors = [t for t in self._recent_errors if now - t < 3600]

    def record_channel_request(
        self,
        channel: str,
        duration: float,
        success: bool = True,
        username: Optional[str] = None,
        error_category: Optional[str] = None,
    ):
        """Record a channel-specific request."""
        self.record_request(duration, success)
        now = time.time()

        ch = self._channels[channel]
        ch["requests"] += 1
        ch["response_times"].append(duration)
        ch["recent_requests"].append(now)

        if not success:
            ch["errors"] += 1
            ch["recent_errors"].append(now)

        # Trim
        if len(ch["response_times"]) > self.WINDOW_SIZE:
            ch["response_times"] = ch["response_times"][-self.WINDOW_SIZE:]
        ch["recent_requests"] = [t for t in ch["recent_requests"] if now - t < 3600]
        ch["recent_errors"] = [t for t in ch["recent_errors"] if now - t < 3600]

        # User tracking
        if username:
            if username in self._users_today:
                self._repeat_users_today.add(username)
            self._users_today.add(username)
            self._user_sessions[username] += 1

            # Cleanup if too many users
            if len(self._user_sessions) > self.MAX_USERS:
                self._user_sessions.clear()

        # Error category
        if error_category:
            self._error_categories[error_category] += 1
            if len(self._error_categories) > self.MAX_ERROR_CATEGORIES:
                self._error_categories.clear()

    def record_routing_decision(self, routing_mode: str, success: bool = True):
        """Record a RAG routing decision."""
        self._routing_decisions[routing_mode] += 1
        self._rag_queries += 1
        if success:
            self._rag_successes += 1

    def get_stats(self) -> Dict[str, Any]:
        """Basic metrics."""
        uptime = time.time() - self._start_time
        avg_rt = sum(self._response_times) / len(self._response_times) if self._response_times else 0.0
        error_rate = self._total_errors / self._total_requests if self._total_requests > 0 else 0.0

        return {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "error_rate": round(error_rate, 4),
            "avg_response_time": round(avg_rt, 4),
            "uptime_seconds": round(uptime, 1),
        }

    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Full enhanced metrics."""
        now = time.time()
        uptime = now - self._start_time
        avg_rt = sum(self._response_times) / len(self._response_times) if self._response_times else 0.0
        error_rate = self._total_errors / self._total_requests if self._total_requests > 0 else 0.0

        req_last_min = len([t for t in self._recent_requests if now - t < 60])
        req_last_hour = len([t for t in self._recent_requests if now - t < 3600])
        err_last_min = len([t for t in self._recent_errors if now - t < 60])
        err_last_hour = len([t for t in self._recent_errors if now - t < 3600])

        # Channel stats
        channels = {}
        for ch_name, ch_data in self._channels.items():
            ch_reqs = ch_data["requests"]
            ch_errs = ch_data["errors"]
            ch_rts = ch_data["response_times"]
            channels[ch_name] = {
                "requests": ch_reqs,
                "errors": ch_errs,
                "error_rate": round(ch_errs / ch_reqs, 4) if ch_reqs > 0 else 0.0,
                "avg_response_time": round(sum(ch_rts) / len(ch_rts), 4) if ch_rts else 0.0,
                "requests_last_hour": len([t for t in ch_data["recent_requests"] if now - t < 3600]),
                "errors_last_hour": len([t for t in ch_data["recent_errors"] if now - t < 3600]),
            }

        # RAG stats
        rag_success_rate = self._rag_successes / self._rag_queries if self._rag_queries > 0 else 0.0
        most_used = max(self._routing_decisions, key=self._routing_decisions.get) if self._routing_decisions else ""

        # User stats
        total_sessions = sum(self._user_sessions.values())
        unique_users = len(self._user_sessions)
        avg_per_user = total_sessions / unique_users if unique_users > 0 else 0.0

        # Alert conditions
        from app.config import settings
        high_error = error_rate > settings.ALERT_ERROR_RATE_THRESHOLD
        slow_resp = avg_rt > settings.ALERT_RESPONSE_TIME_THRESHOLD

        # Most common error
        most_common_error = max(self._error_categories, key=self._error_categories.get) if self._error_categories else None

        # Health status
        if high_error or slow_resp:
            health_status = "degraded"
        else:
            health_status = "healthy"

        return {
            "summary": {
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "error_rate": round(error_rate, 4),
                "avg_response_time": round(avg_rt, 4),
                "uptime_seconds": round(uptime, 1),
            },
            "recent_activity": {
                "requests_last_minute": req_last_min,
                "requests_last_hour": req_last_hour,
                "errors_last_minute": err_last_min,
                "errors_last_hour": err_last_hour,
            },
            "health_status": health_status,
            "channels": channels,
            "users": {
                "unique_users_today": len(self._users_today),
                "repeat_users_today": len(self._repeat_users_today),
                "total_user_sessions": total_sessions,
                "avg_requests_per_user": round(avg_per_user, 2),
            },
            "rag": {
                "total_queries": self._rag_queries,
                "success_rate": round(rag_success_rate, 4),
                "routing_distribution": dict(self._routing_decisions),
                "most_used_mode": most_used,
            },
            "errors": {
                "total_errors": self._total_errors,
                "categories": dict(self._error_categories),
                "most_common_error": most_common_error,
            },
            "alerts": {
                "high_error_rate": high_error,
                "slow_response": slow_resp,
                "error_rate_value": round(error_rate, 4),
                "avg_response_time_value": round(avg_rt, 4),
                "requests_last_hour": req_last_hour,
            },
        }


# Global instance
_enhanced_metrics = None


def get_enhanced_metrics_instance() -> EnhancedMetrics:
    """Get global EnhancedMetrics instance."""
    global _enhanced_metrics
    if _enhanced_metrics is None:
        _enhanced_metrics = EnhancedMetrics()
    return _enhanced_metrics


def get_metrics_instance() -> EnhancedMetrics:
    """Alias for backward compatibility."""
    return get_enhanced_metrics_instance()
