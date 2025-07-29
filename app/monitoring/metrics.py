"""
Basic metrics collection.
Simple in-memory metrics.
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta


class BasicMetrics:
    """
    monitoring chain performance.
    Thread-safe & memory-efficient.
    """
    
    def __init__(self, window_size: int = 1000):
        """Initialize metrics collector"""
        self.window_size = window_size
        
        # Basic counters
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        
        # Step-specific metrics
        self.step_timings = defaultdict(list)
        self.step_counts = defaultdict(int)
        
        # Recent requests for rate calculation
        self.recent_requests = deque(maxlen=window_size)
        self.recent_errors = deque(maxlen=window_size)
        
        # Start time for uptime calculation
        self.start_time = time.time()
        
    def record_request(self, duration: float, success: bool = True) -> None:
        """Record a completed request"""
        self.request_count += 1
        self.total_response_time += duration
        
        timestamp = time.time()
        self.recent_requests.append(timestamp)
        
        if not success:
            self.error_count += 1
            self.recent_errors.append(timestamp)
    
    def record_step_duration(self, step_name: str, duration: float) -> None:
        """Record timing for specific processing step"""
        self.step_timings[step_name].append(duration)
        self.step_counts[step_name] += 1
        
        # Keep only recent timings for memory efficiency
        if len(self.step_timings[step_name]) > self.window_size:
            self.step_timings[step_name] = self.step_timings[step_name][-self.window_size:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive metrics statistics"""
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
    
    def _count_recent(self, timestamps: deque, seconds: int) -> int:
        """Count events in the last N seconds"""
        cutoff = time.time() - seconds
        return sum(1 for ts in timestamps if ts > cutoff)
    
    def _get_step_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for each processing step"""
        stats = {}
        
        for step, timings in self.step_timings.items():
            if timings:
                stats[step] = {
                    "count": self.step_counts[step],
                    "avg_duration": sum(timings) / len(timings),
                    "min_duration": min(timings),
                    "max_duration": max(timings),
                    "p95_duration": self._percentile(timings, 0.95),
                    "recent_avg": sum(timings[-10:]) / min(len(timings), 10)
                }
        
        return stats
    
    def _percentile(self, data: list, p: float) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_health_status(self) -> str:
        """Determine overall health status"""
        recent_error_rate = self._count_recent(self.recent_errors, 300) / max(self._count_recent(self.recent_requests, 300), 1)
        
        if recent_error_rate > 0.1:  # >10% error rate
            return "unhealthy"
        elif recent_error_rate > 0.05:  # >5% error rate
            return "degraded"
        else:
            return "healthy"
    
    def reset(self) -> None:
        """Reset all metrics (for testing)"""
        self.__init__(self.window_size)


# Global metrics instance (singleton pattern)
_metrics_instance: Optional[BasicMetrics] = None


def get_metrics_instance() -> BasicMetrics:
    """Get or create global metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = BasicMetrics()
    return _metrics_instance


def reset_metrics() -> None:
    """Reset global metrics instance (for testing)"""
    global _metrics_instance
    if _metrics_instance:
        _metrics_instance.reset()