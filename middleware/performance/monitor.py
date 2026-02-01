"""
Performance monitoring system for Observer Eye Middleware
"""

import asyncio
import time
import psutil
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

from .metrics import MetricsCollector
from .analyzer import PerformanceAnalyzer

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_requests: int
    response_times: List[float]
    error_rate: float


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    severity: str
    message: str
    timestamp: str
    metric_name: str
    threshold: float
    current_value: float


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system that collects metrics
    from all platform layers and generates alerts when thresholds are exceeded.
    
    Validates Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.analyzer = PerformanceAnalyzer()
        self.active_requests: Dict[str, float] = {}
        self.response_times: List[float] = []
        self.error_count = 0
        self.request_count = 0
        self.alerts: List[Alert] = []
        
        # Performance thresholds
        self.thresholds = {
            "cpu_usage": 80.0,  # 80% CPU usage
            "memory_usage": 85.0,  # 85% memory usage
            "response_time": 1000.0,  # 1 second response time
            "error_rate": 5.0,  # 5% error rate
        }
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
    
    async def initialize(self):
        """Initialize the performance monitoring system"""
        logger.info("Initializing performance monitor")
        await self.metrics_collector.initialize()
        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def cleanup(self):
        """Cleanup monitoring resources"""
        logger.info("Cleaning up performance monitor")
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        await self.metrics_collector.cleanup()
    
    def start_request_tracking(self, request_id: str) -> float:
        """Start tracking a request's performance"""
        start_time = time.time()
        self.active_requests[request_id] = start_time
        return start_time
    
    def end_request_tracking(self, request_id: str, start_time: float) -> float:
        """End tracking a request and calculate response time"""
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Remove from active requests
        self.active_requests.pop(request_id, None)
        
        # Store response time for analysis
        self.response_times.append(response_time)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        self.request_count += 1
        
        # Check response time threshold
        if response_time > self.thresholds["response_time"]:
            self._generate_alert(
                "response_time",
                f"High response time detected: {response_time:.2f}ms",
                "warning",
                self.thresholds["response_time"],
                response_time
            )
        
        return response_time
    
    def record_error(self):
        """Record an error occurrence"""
        self.error_count += 1
        
        # Check error rate threshold
        if self.request_count > 0:
            error_rate = (self.error_count / self.request_count) * 100
            if error_rate > self.thresholds["error_rate"]:
                self._generate_alert(
                    "error_rate",
                    f"High error rate detected: {error_rate:.2f}%",
                    "critical",
                    self.thresholds["error_rate"],
                    error_rate
                )
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect comprehensive performance metrics from all layers
        Validates Requirement 4.1: Performance monitoring across all layers
        """
        try:
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Calculate error rate
            error_rate = (self.error_count / max(self.request_count, 1)) * 100
            
            # Calculate average response time
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            
            metrics = PerformanceMetrics(
                timestamp=self.get_current_timestamp(),
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=(disk.used / disk.total) * 100,
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                active_requests=len(self.active_requests),
                response_times=self.response_times[-10:],  # Last 10 response times
                error_rate=error_rate
            )
            
            # Check thresholds and generate alerts
            await self._check_thresholds(metrics)
            
            # Store metrics for analysis
            await self.metrics_collector.store_metrics(asdict(metrics))
            
            return asdict(metrics)
            
        except Exception as e:
            logger.error("Failed to collect metrics", error=str(e))
            raise
    
    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get basic health metrics for health checks"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "active_requests": len(self.active_requests),
                "total_requests": self.request_count,
                "error_count": self.error_count,
                "uptime": time.time() - getattr(self, '_start_time', time.time())
            }
        except Exception as e:
            logger.error("Failed to get health metrics", error=str(e))
            raise
    
    async def analyze_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze performance data and identify issues
        Validates Requirement 4.3: BI analytics for trend analysis
        """
        return await self.analyzer.analyze(metrics)
    
    async def generate_alerts(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate alerts based on performance analysis
        Validates Requirement 4.2: Alert generation on threshold breach
        """
        alerts = []
        
        # Convert Alert objects to dictionaries
        for alert in self.alerts:
            alerts.append(asdict(alert))
        
        # Clear processed alerts
        self.alerts.clear()
        
        return alerts
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        self._start_time = time.time()
        
        while self._is_monitoring:
            try:
                # Collect metrics every 30 seconds
                await asyncio.sleep(30)
                if self._is_monitoring:
                    await self.collect_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _check_thresholds(self, metrics: PerformanceMetrics):
        """Check metrics against thresholds and generate alerts"""
        # Check CPU usage
        if metrics.cpu_usage > self.thresholds["cpu_usage"]:
            self._generate_alert(
                "cpu_usage",
                f"High CPU usage: {metrics.cpu_usage:.2f}%",
                "warning",
                self.thresholds["cpu_usage"],
                metrics.cpu_usage
            )
        
        # Check memory usage
        if metrics.memory_usage > self.thresholds["memory_usage"]:
            self._generate_alert(
                "memory_usage",
                f"High memory usage: {metrics.memory_usage:.2f}%",
                "critical",
                self.thresholds["memory_usage"],
                metrics.memory_usage
            )
    
    def _generate_alert(self, metric_name: str, message: str, severity: str, threshold: float, current_value: float):
        """Generate an alert"""
        alert = Alert(
            id=f"alert_{int(time.time())}_{metric_name}",
            severity=severity,
            message=message,
            timestamp=self.get_current_timestamp(),
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value
        )
        
        self.alerts.append(alert)
        logger.warning(
            "Performance alert generated",
            alert_id=alert.id,
            severity=severity,
            metric=metric_name,
            threshold=threshold,
            current_value=current_value
        )