"""
Comprehensive metrics collection for multi-channel AI agent.
Includes basic metrics + channel-specific tracking, user activity, and RAG effectiveness.
"""

import time
from typing import Dict, Any, Optional, Set
from collections import defaultdict, deque
from datetime import datetime, timedelta


class EnhancedMetrics:
    """
    Enhanced metrics for early-stage monitoring (100 queries/day).
    Tracks channel-specific metrics, user activity, and RAG effectiveness.
    """
    
    def __init__(self, window_size: int = 1000):
        """Initialize comprehensive metrics collector"""
        self.window_size = window_size
        
        # Basic counters (from BasicMetrics)
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        
        # Step-specific metrics (from BasicMetrics)
        self.step_timings = defaultdict(list)
        self.step_counts = defaultdict(int)
        
        # Recent requests for rate calculation (from BasicMetrics)
        self.recent_requests = deque(maxlen=window_size)
        self.recent_errors = deque(maxlen=window_size)
        
        # Start time for uptime calculation (from BasicMetrics)
        self.start_time = time.time()
        
        # Channel-specific metrics (enhanced)
        self.channel_requests = defaultdict(int)
        self.channel_errors = defaultdict(int) 
        self.channel_response_times = defaultdict(list)
        
        # User activity tracking (bounded)
        self.unique_users_today = set()
        self.user_request_counts = defaultdict(int)
        self.repeat_users = set()
        
        # Memory management limits
        self.max_users_tracked = 10000  # Reasonable limit for user tracking
        self.max_error_categories = 100  # Limit error categories
        
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
    
    def record_request(self, duration: float, success: bool = True) -> None:
        """Record a completed request (from BasicMetrics)"""
        self.request_count += 1
        self.total_response_time += duration
        
        timestamp = time.time()
        self.recent_requests.append(timestamp)
        
        if not success:
            self.error_count += 1
            self.recent_errors.append(timestamp)
    
    def record_step_duration(self, step_name: str, duration: float) -> None:
        """Record timing for specific processing step (from BasicMetrics)"""
        self.step_timings[step_name].append(duration)
        self.step_counts[step_name] += 1
        
        # Keep only recent timings for memory efficiency
        if len(self.step_timings[step_name]) > self.window_size:
            self.step_timings[step_name] = self.step_timings[step_name][-self.window_size:]

    def record_channel_request(self, channel: str, duration: float, success: bool = True, 
                             username: Optional[str] = None, error_category: Optional[str] = None) -> None:
        """Record a channel-specific request"""
        # Record basic metrics
        self.record_request(duration, success)
        
        # Channel-specific tracking
        self.channel_requests[channel] += 1
        self.channel_response_times[channel].append(duration)
        
        # Bound channel response times to prevent memory growth
        if len(self.channel_response_times[channel]) > self.window_size:
            self.channel_response_times[channel] = self.channel_response_times[channel][-self.window_size:]
        
        timestamp = time.time()
        self.recent_channel_requests[channel].append(timestamp)
        
        if not success:
            self.channel_errors[channel] += 1
            self.recent_channel_errors[channel].append(timestamp)
            
            if error_category:
                self.error_categories[error_category] += 1
                
                # Prevent unlimited error categories
                if len(self.error_categories) > self.max_error_categories:
                    self._cleanup_error_categories()
        
        # User activity tracking (with bounds)
        if username:
            if username in self.unique_users_today:
                self.repeat_users.add(username)
            else:
                self.unique_users_today.add(username)
            
            self.user_request_counts[username] += 1
            
            # Prevent unlimited user growth
            if len(self.user_request_counts) > self.max_users_tracked:
                self._cleanup_old_users()
        
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic metrics statistics (from BasicMetrics)"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        return {
            "summary": {
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "error_rate": self.error_count / max(self.request_count, 1),
                "avg_response_time": self.total_response_time / max(self.request_count, 1),
                "uptime_seconds": round(uptime, 2)
            },
            "recent_activity": {
                "requests_last_minute": self._count_recent(self.recent_requests, 60),
                "requests_last_hour": self._count_recent(self.recent_requests, 3600),
                "errors_last_minute": self._count_recent(self.recent_errors, 60),
                "errors_last_hour": self._count_recent(self.recent_errors, 3600)
            },
            "step_performance": self._get_step_stats(),
            "health_status": self._get_health_status()
        }

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
        # Get recent response times for actual durations, not timestamps
        recent_durations = []
        for channel in self.channel_response_times.values():
            recent_durations.extend(channel[-100:])  # Last 100 requests
        
        avg_recent_response_time = sum(recent_durations) / max(len(recent_durations), 1)
        
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
    
    def _cleanup_old_users(self) -> None:
        """Remove least active users to prevent memory growth"""
        if len(self.user_request_counts) <= self.max_users_tracked:
            return
        
        # Keep top 80% most active users
        target_size = int(self.max_users_tracked * 0.8)
        
        # Sort by request count and keep most active users
        sorted_users = sorted(
            self.user_request_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Keep only top users
        self.user_request_counts = defaultdict(int)
        for username, count in sorted_users[:target_size]:
            self.user_request_counts[username] = count
        
        print(f"🧹 Cleaned up user tracking: {len(sorted_users)} → {target_size} users")
    
    def _cleanup_error_categories(self) -> None:
        """Remove least common error categories to prevent memory growth"""
        if len(self.error_categories) <= self.max_error_categories:
            return
        
        # Keep top 80% most common error categories
        target_size = int(self.max_error_categories * 0.8)
        
        # Sort by count and keep most common errors
        sorted_errors = sorted(
            self.error_categories.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Keep only top error categories
        self.error_categories = defaultdict(int)
        for error_type, count in sorted_errors[:target_size]:
            self.error_categories[error_type] = count
        
        print(f"🧹 Cleaned up error categories: {len(sorted_errors)} → {target_size} categories")
    
    def _count_recent(self, deque_data, window_seconds: int) -> int:
        """Count recent events within time window"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        return sum(1 for timestamp in deque_data if timestamp >= cutoff_time)
    
    def _get_step_stats(self) -> Dict[str, Any]:
        """Get step performance statistics"""
        step_stats = {}
        for step_name in self.step_timings.keys():
            timings = self.step_timings[step_name]
            if timings:
                step_stats[step_name] = {
                    "count": self.step_counts[step_name],
                    "avg_duration": sum(timings) / len(timings),
                    "min_duration": min(timings),
                    "max_duration": max(timings)
                }
        return step_stats
    
    def _get_health_status(self) -> str:
        """Get basic health status"""
        error_rate = self.error_count / max(self.request_count, 1)
        avg_response_time = self.total_response_time / max(self.request_count, 1)
        
        if error_rate > 0.1:
            return "unhealthy"
        elif error_rate > 0.05 or avg_response_time > 3.0:
            return "degraded"
        else:
            return "healthy"


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


# Backward compatibility aliases for BasicMetrics
def get_metrics_instance() -> EnhancedMetrics:
    """Get global metrics instance (backward compatibility)"""
    return get_enhanced_metrics_instance()


def reset_metrics() -> None:
    """Reset global metrics instance (backward compatibility)"""
    reset_enhanced_metrics()


# Backward compatibility class alias
BasicMetrics = EnhancedMetrics


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