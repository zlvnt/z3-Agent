"""
Enhanced metrics collection for multi-channel AI agent.
Extends BasicMetrics with channel-specific tracking, user activity, and RAG effectiveness.
"""

import time
from typing import Dict, Any, Optional, Set
from collections import defaultdict, deque
from datetime import datetime, timedelta

from .metrics import BasicMetrics


class EnhancedMetrics(BasicMetrics):
    """
    Enhanced metrics for early-stage monitoring (100 queries/day).
    Tracks channel-specific metrics, user activity, and RAG effectiveness.
    """
    
    def __init__(self, window_size: int = 1000):
        super().__init__(window_size)
        
        # Channel-specific metrics
        self.channel_requests = defaultdict(int)
        self.channel_errors = defaultdict(int) 
        self.channel_response_times = defaultdict(list)
        
        # User activity tracking
        self.unique_users_today = set()
        self.user_request_counts = defaultdict(int)
        self.repeat_users = set()
        
        # RAG effectiveness
        self.routing_decisions = defaultdict(int)  # direct, docs, web, all
        self.rag_success_count = 0
        self.rag_total_count = 0
        
        # Error categorization
        self.error_categories = defaultdict(int)  # api_failure, ai_error, timeout, etc
        
        # Recent activity for alerts
        self.recent_channel_requests = defaultdict(lambda: deque(maxlen=100))
        self.recent_channel_errors = defaultdict(lambda: deque(maxlen=100))
        
        # Daily reset tracking
        self.last_daily_reset = datetime.now().date()
    
    def record_channel_request(self, channel: str, duration: float, success: bool = True, 
                             username: Optional[str] = None, error_category: Optional[str] = None) -> None:
        """Record a channel-specific request"""
        # Call parent method for overall metrics
        self.record_request(duration, success)
        
        # Channel-specific tracking
        self.channel_requests[channel] += 1
        self.channel_response_times[channel].append(duration)
        
        timestamp = time.time()
        self.recent_channel_requests[channel].append(timestamp)
        
        if not success:
            self.channel_errors[channel] += 1
            self.recent_channel_errors[channel].append(timestamp)
            
            if error_category:
                self.error_categories[error_category] += 1
        
        # User activity tracking
        if username:
            if username in self.unique_users_today:
                self.repeat_users.add(username)
            else:
                self.unique_users_today.add(username)
            
            self.user_request_counts[username] += 1
        
        # Keep channel response times manageable
        if len(self.channel_response_times[channel]) > self.window_size:
            self.channel_response_times[channel] = self.channel_response_times[channel][-self.window_size:]
        
        # Check if we need daily reset
        self._check_daily_reset()
    
    def record_routing_decision(self, routing_mode: str, success: bool = True) -> None:
        """Record RAG routing decision"""
        self.routing_decisions[routing_mode] += 1
        self.rag_total_count += 1
        
        if success:
            self.rag_success_count += 1
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get comprehensive enhanced statistics"""
        # Get base stats
        base_stats = self.get_stats()
        
        # Add enhanced metrics
        enhanced_stats = {
            **base_stats,
            "channels": self._get_channel_stats(),
            "users": self._get_user_stats(), 
            "rag": self._get_rag_stats(),
            "errors": self._get_error_stats(),
            "alerts": self._get_alert_status()
        }
        
        return enhanced_stats
    
    def _get_channel_stats(self) -> Dict[str, Any]:
        """Get channel-specific statistics"""
        channel_stats = {}
        
        for channel in self.channel_requests.keys():
            total_requests = self.channel_requests[channel]
            total_errors = self.channel_errors[channel]
            response_times = self.channel_response_times[channel]
            
            if total_requests > 0:
                error_rate = total_errors / total_requests
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                channel_stats[channel] = {
                    "requests": total_requests,
                    "errors": total_errors,
                    "error_rate": round(error_rate, 4),
                    "avg_response_time": round(avg_response_time, 3),
                    "requests_last_hour": self._count_recent(self.recent_channel_requests[channel], 3600),
                    "errors_last_hour": self._count_recent(self.recent_channel_errors[channel], 3600)
                }
        
        return channel_stats
    
    def _get_user_stats(self) -> Dict[str, Any]:
        """Get user activity statistics"""
        return {
            "unique_users_today": len(self.unique_users_today),
            "repeat_users_today": len(self.repeat_users),
            "total_user_sessions": len(self.user_request_counts),
            "avg_requests_per_user": sum(self.user_request_counts.values()) / max(len(self.user_request_counts), 1),
            "most_active_users": dict(sorted(self.user_request_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def _get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG effectiveness statistics"""
        rag_success_rate = self.rag_success_count / max(self.rag_total_count, 1)
        
        return {
            "total_queries": self.rag_total_count,
            "success_rate": round(rag_success_rate, 4),
            "routing_distribution": dict(self.routing_decisions),
            "most_used_mode": max(self.routing_decisions.items(), key=lambda x: x[1])[0] if self.routing_decisions else "none"
        }
    
    def _get_error_stats(self) -> Dict[str, Any]:
        """Get error categorization statistics"""
        total_errors = sum(self.error_categories.values())
        
        error_stats = {
            "total_errors": total_errors,
            "categories": dict(self.error_categories)
        }
        
        if total_errors > 0:
            error_stats["most_common_error"] = max(self.error_categories.items(), key=lambda x: x[1])[0]
        
        return error_stats
    
    def _get_alert_status(self) -> Dict[str, Any]:
        """Get current alert status for monitoring"""
        # Check error rates in last hour
        recent_requests = self._count_recent(self.recent_requests, 3600)
        recent_errors = self._count_recent(self.recent_errors, 3600)
        
        hourly_error_rate = recent_errors / max(recent_requests, 1)
        
        # Check average response time in last hour
        recent_response_times = [
            duration for duration in list(self.recent_requests)[-100:] 
            if time.time() - duration < 3600
        ]
        avg_recent_response_time = sum(recent_response_times) / max(len(recent_response_times), 1)
        
        return {
            "high_error_rate": hourly_error_rate > 0.1,  # >10%
            "slow_response": avg_recent_response_time > 5.0,  # >5 seconds
            "error_rate_value": round(hourly_error_rate, 4),
            "avg_response_time_value": round(avg_recent_response_time, 3),
            "requests_last_hour": recent_requests
        }
    
    def _check_daily_reset(self) -> None:
        """Reset daily metrics if needed"""
        current_date = datetime.now().date()
        
        if current_date != self.last_daily_reset:
            self.unique_users_today.clear()
            self.repeat_users.clear()
            self.last_daily_reset = current_date


# Global enhanced metrics instance
_enhanced_metrics_instance: Optional[EnhancedMetrics] = None


def get_enhanced_metrics_instance() -> EnhancedMetrics:
    """Get or create global enhanced metrics instance"""
    global _enhanced_metrics_instance
    if _enhanced_metrics_instance is None:
        _enhanced_metrics_instance = EnhancedMetrics()
    return _enhanced_metrics_instance


def reset_enhanced_metrics() -> None:
    """Reset global enhanced metrics instance (for testing)"""
    global _enhanced_metrics_instance
    if _enhanced_metrics_instance:
        _enhanced_metrics_instance = EnhancedMetrics()


def test_metrics() -> None:
    """Simple test function for enhanced metrics"""
    print("🧪 Testing Enhanced Metrics...")
    
    # Reset for clean test
    reset_enhanced_metrics()
    metrics = get_enhanced_metrics_instance()
    
    # Simulate some requests
    test_data = [
        ("instagram", "user1", 1.2, True, None),
        ("telegram", "user2", 0.8, True, None),
        ("instagram", "user1", 2.5, False, "api_failure"),  # repeat user
        ("telegram", "user3", 1.1, True, None),
        ("instagram", "user2", 0.9, True, None),  # cross-channel user
    ]
    
    for channel, username, duration, success, error_cat in test_data:
        metrics.record_channel_request(channel, duration, success, username, error_cat)
        
        # Simulate routing decisions
        routing_mode = "direct" if duration < 1.0 else "docs"
        metrics.record_routing_decision(routing_mode, success)
    
    # Get and display stats
    stats = metrics.get_enhanced_stats()
    
    print(f"✅ Total requests: {stats['summary']['total_requests']}")
    print(f"✅ Channels: {list(stats['channels'].keys())}")
    print(f"✅ Unique users: {stats['users']['unique_users_today']}")
    print(f"✅ Repeat users: {stats['users']['repeat_users_today']}")
    print(f"✅ RAG success rate: {stats['rag']['success_rate']:.2%}")
    print(f"✅ Alert status: Error rate high = {stats['alerts']['high_error_rate']}")
    
    print("✨ Enhanced metrics test completed!")


if __name__ == "__main__":
    test_metrics()