"""
Simple alerting system for early-stage monitoring.
Sends Telegram notifications when thresholds are breached.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime

from app.config import settings

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    print("WARNING: aiohttp not available. Telegram alerts disabled.")

from .enhanced_metrics import get_enhanced_metrics_instance


class SimpleAlerts:
    """
    Lightweight alerting system for 100 queries/day scale.
    """
    
    def __init__(self):
        # Alert thresholds (from centralized config)
        self.error_rate_threshold = settings.ALERT_ERROR_RATE_THRESHOLD
        self.response_time_threshold = settings.ALERT_RESPONSE_TIME_THRESHOLD
        
        # Alert throttling (prevent spam)
        self.alert_cooldown_seconds = settings.ALERT_COOLDOWN_MINUTES * 60
        self.last_alert_time = 0
        
        # Telegram configuration (from centralized config)
        self.telegram_bot_token = settings.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = settings.TELEGRAM_ALERT_CHAT_ID
    
    async def check_and_alert(self) -> None:
        """Check metrics and send alerts if needed (with throttling)"""
        if not self._can_send_alerts():
            return
            
        metrics = get_enhanced_metrics_instance()
        alert_status = metrics._get_alert_status()
        
        # Send alert if issues detected and not throttled
        if alert_status["high_error_rate"] or alert_status["slow_response"]:
            if self._should_send_alert():
                await self._send_alert(alert_status)
                self.last_alert_time = time.time()  # Update throttling
            else:
                minutes_ago = (time.time() - self.last_alert_time) / 60
                print(f"⏸️ Alert throttled (last sent {minutes_ago:.0f}m ago, cooldown: {self.alert_cooldown_seconds/60:.0f}m)")
    
    async def _send_alert(self, alert_status: Dict[str, Any]) -> None:
        """Send single alert for any detected issues"""
        error_rate_pct = alert_status["error_rate_value"] * 100
        avg_time = alert_status["avg_response_time_value"]
        requests_count = alert_status["requests_last_hour"]
        
        # Build alert message
        issues = []
        if alert_status["high_error_rate"]:
            issues.append(f"🚨 Error Rate: {error_rate_pct:.1f}% (threshold: {self.error_rate_threshold*100:.0f}%)")
        
        if alert_status["slow_response"]:
            issues.append(f"⏰ Response Time: {avg_time:.2f}s (threshold: {self.response_time_threshold:.1f}s)")
        
        message = f"""🤖 *SYSTEM ALERT*

{chr(10).join(issues)}

Requests Last Hour: {requests_count}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the system! 🔧"""
        
        await self._send_telegram_alert(message)
    
    async def _send_telegram_alert(self, message: str) -> bool:
        """Send alert via Telegram"""
        if not HAS_AIOHTTP:
            print(f"WARNING: Cannot send alert - aiohttp not available")
            print(f"Alert: {message}")
            return False
            
        if not self.telegram_bot_token or not self.telegram_chat_id:
            print(f"WARNING: Telegram not configured. Alert: {message[:100]}...")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        print(f"✅ Alert sent via Telegram")
                        return True
                    else:
                        print(f"❌ Telegram alert failed: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"ERROR: Failed to send Telegram alert: {e}")
            return False
    
    def _can_send_alerts(self) -> bool:
        """Check if alerts are configured"""
        return bool(self.telegram_bot_token and self.telegram_chat_id and HAS_AIOHTTP)
    
    def _should_send_alert(self) -> bool:
        """Check if enough time has passed since last alert (throttling)"""
        return (time.time() - self.last_alert_time) >= self.alert_cooldown_seconds
    
    def get_alert_status(self) -> Dict[str, Any]:
        """Get alert configuration and throttling status"""
        return {
            "configured": self._can_send_alerts(),
            "error_rate_threshold": self.error_rate_threshold,
            "response_time_threshold": self.response_time_threshold,
            "alert_cooldown_minutes": self.alert_cooldown_seconds / 60,
            "last_alert_minutes_ago": (time.time() - self.last_alert_time) / 60 if self.last_alert_time > 0 else None
        }


# Global instance
_alerts_instance: Optional[SimpleAlerts] = None


def get_alerts_instance() -> SimpleAlerts:
    """Get global alerts instance"""
    global _alerts_instance
    if _alerts_instance is None:
        _alerts_instance = SimpleAlerts()
    return _alerts_instance


async def check_alerts_now() -> None:
    """Check alerts immediately"""
    alerts = get_alerts_instance()
    await alerts.check_and_alert()


async def send_test_alert() -> None:
    """Send test alert"""
    alerts = get_alerts_instance()
    
    if not alerts._can_send_alerts():
        print("❌ Cannot send test alert: Check TELEGRAM_BOT_TOKEN and TELEGRAM_ALERT_CHAT_ID")
        return
    
    test_message = f"""🧪 *TEST ALERT*

Instagram AI Agent monitoring test.
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Alert system working! ✅"""
    
    success = await alerts._send_telegram_alert(test_message)
    if success:
        print("✅ Test alert sent!")
    else:
        print("❌ Test alert failed")


def test_alert() -> None:
    """Test function for alerts"""
    asyncio.run(send_test_alert())


if __name__ == "__main__":
    test_alert()