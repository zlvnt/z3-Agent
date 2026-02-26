"""
Simple alert system for z3-Agent.

Monitors error rates and response times, sends alerts via Telegram
when thresholds are exceeded.
"""

import time
from typing import Dict, Any, Optional

from app.config import settings


class SimpleAlerts:
    """Threshold-based alert system."""

    def __init__(self):
        self._last_alert_time: float = 0
        self._cooldown = settings.ALERT_COOLDOWN_MINUTES * 60
        self._error_threshold = settings.ALERT_ERROR_RATE_THRESHOLD
        self._response_time_threshold = settings.ALERT_RESPONSE_TIME_THRESHOLD

    def get_alert_status(self) -> Dict[str, Any]:
        """Get current alert configuration and status."""
        from app.monitoring.enhanced_metrics import get_enhanced_metrics_instance

        metrics = get_enhanced_metrics_instance()
        stats = metrics.get_stats()

        error_rate = stats["error_rate"]
        avg_rt = stats["avg_response_time"]

        now = time.time()
        cooldown_remaining = max(0, self._cooldown - (now - self._last_alert_time))

        return {
            "thresholds": {
                "error_rate": self._error_threshold,
                "response_time": self._response_time_threshold,
            },
            "current": {
                "error_rate": error_rate,
                "avg_response_time": avg_rt,
            },
            "alerts_active": {
                "high_error_rate": error_rate > self._error_threshold,
                "slow_response": avg_rt > self._response_time_threshold,
            },
            "cooldown": {
                "active": cooldown_remaining > 0,
                "remaining_seconds": round(cooldown_remaining),
            },
            "alert_chat_id_configured": bool(settings.TELEGRAM_ALERT_CHAT_ID),
        }

    async def check_and_alert(self) -> Optional[str]:
        """Check thresholds and send alert if needed."""
        from app.monitoring.enhanced_metrics import get_enhanced_metrics_instance

        metrics = get_enhanced_metrics_instance()
        stats = metrics.get_stats()

        now = time.time()
        if now - self._last_alert_time < self._cooldown:
            return None

        alerts = []
        if stats["error_rate"] > self._error_threshold:
            alerts.append(f"High error rate: {stats['error_rate']:.1%}")
        if stats["avg_response_time"] > self._response_time_threshold:
            alerts.append(f"Slow response: {stats['avg_response_time']:.2f}s")

        if not alerts:
            return None

        message = "ALERT: " + ", ".join(alerts)
        self._last_alert_time = now

        # Send alert via Telegram if configured
        alert_chat_id = settings.TELEGRAM_ALERT_CHAT_ID
        if alert_chat_id:
            try:
                from app.channels.telegram.client import send_telegram_message
                await send_telegram_message(int(alert_chat_id), message)
            except Exception as e:
                print(f"Failed to send alert: {e}")

        return message


# Global instance
_alerts = None


def get_alerts_instance() -> SimpleAlerts:
    """Get global SimpleAlerts instance."""
    global _alerts
    if _alerts is None:
        _alerts = SimpleAlerts()
    return _alerts
