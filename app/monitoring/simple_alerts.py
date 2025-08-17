"""
Simple alerting system for early-stage monitoring.
Sends Telegram notifications when thresholds are breached.
"""

import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

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
        # Alert thresholds
        self.error_rate_threshold = 0.10  # 10%
        self.response_time_threshold = 5.0  # 5 seconds
        
        # Telegram configuration
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_ALERT_CHAT_ID")
    
    async def check_and_alert(self) -> None:
        """Check metrics and send alerts if needed"""
        if not self._can_send_alerts():
            return
            
        metrics = get_enhanced_metrics_instance()
        alert_status = metrics._get_alert_status()
        
        # Send combined alert if issues detected
        if alert_status["high_error_rate"] or alert_status["slow_response"]:
            await self._send_alert(alert_status)
    
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
    
    def get_alert_status(self) -> Dict[str, Any]:
        """Get simple alert configuration status"""
        return {
            "configured": self._can_send_alerts(),
            "error_rate_threshold": self.error_rate_threshold,
            "response_time_threshold": self.response_time_threshold
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