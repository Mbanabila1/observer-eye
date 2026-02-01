"""
Metrics collection system for performance monitoring
"""

import asyncio
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """
    Collects and stores performance metrics with time-series capabilities
    """
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics_store: deque = deque(maxlen=max_metrics)
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the metrics collector"""
        logger.info("Initializing metrics collector")
    
    async def cleanup(self):
        """Cleanup metrics collector resources"""
        logger.info("Cleaning up metrics collector")
        async with self._lock:
            self.metrics_store.clear()
    
    async def store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in the time-series store"""
        async with self._lock:
            self.metrics_store.append({
                **metrics,
                "stored_at": datetime.utcnow().isoformat()
            })
    
    async def get_metrics(self, 
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve metrics within a time range"""
        async with self._lock:
            metrics = list(self.metrics_store)
        
        # Filter by time range if specified
        if start_time or end_time:
            filtered_metrics = []
            for metric in metrics:
                metric_time = datetime.fromisoformat(metric["timestamp"].replace("Z", "+00:00"))
                
                if start_time and metric_time < start_time:
                    continue
                if end_time and metric_time > end_time:
                    continue
                
                filtered_metrics.append(metric)
            
            metrics = filtered_metrics
        
        # Apply limit if specified
        if limit:
            metrics = metrics[-limit:]
        
        return metrics
    
    async def get_latest_metrics(self, count: int = 1) -> List[Dict[str, Any]]:
        """Get the latest N metrics"""
        async with self._lock:
            return list(self.metrics_store)[-count:] if self.metrics_store else []
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of stored metrics"""
        async with self._lock:
            total_count = len(self.metrics_store)
            
            if total_count == 0:
                return {
                    "total_count": 0,
                    "oldest_timestamp": None,
                    "newest_timestamp": None
                }
            
            oldest = self.metrics_store[0]
            newest = self.metrics_store[-1]
            
            return {
                "total_count": total_count,
                "oldest_timestamp": oldest["timestamp"],
                "newest_timestamp": newest["timestamp"],
                "storage_utilization": (total_count / self.max_metrics) * 100
            }