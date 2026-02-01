"""
Performance analysis algorithms for Observer Eye Middleware
"""

import structlog
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)


class PerformanceAnalyzer:
    """
    Analyzes performance data to identify trends, anomalies, and optimization opportunities
    """
    
    def __init__(self):
        self.analysis_cache: Dict[str, Any] = {}
    
    async def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive performance analysis
        """
        try:
            analysis = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_analysis": self._analyze_cpu(metrics.get("cpu_usage", 0)),
                "memory_analysis": self._analyze_memory(metrics.get("memory_usage", 0)),
                "response_time_analysis": self._analyze_response_times(metrics.get("response_times", [])),
                "error_rate_analysis": self._analyze_error_rate(metrics.get("error_rate", 0)),
                "network_analysis": self._analyze_network(metrics.get("network_io", {})),
                "overall_health": "unknown"
            }
            
            # Calculate overall health score
            analysis["overall_health"] = self._calculate_overall_health(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error("Failed to analyze performance metrics", error=str(e))
            return {"error": "Analysis failed", "timestamp": datetime.utcnow().isoformat()}
    
    def _analyze_cpu(self, cpu_usage: float) -> Dict[str, Any]:
        """Analyze CPU usage patterns"""
        if cpu_usage < 50:
            status = "optimal"
            recommendation = "CPU usage is within optimal range"
        elif cpu_usage < 70:
            status = "moderate"
            recommendation = "CPU usage is moderate, monitor for trends"
        elif cpu_usage < 85:
            status = "high"
            recommendation = "CPU usage is high, consider scaling or optimization"
        else:
            status = "critical"
            recommendation = "CPU usage is critical, immediate action required"
        
        return {
            "current_usage": cpu_usage,
            "status": status,
            "recommendation": recommendation,
            "threshold_breached": cpu_usage > 80
        }
    
    def _analyze_memory(self, memory_usage: float) -> Dict[str, Any]:
        """Analyze memory usage patterns"""
        if memory_usage < 60:
            status = "optimal"
            recommendation = "Memory usage is within optimal range"
        elif memory_usage < 75:
            status = "moderate"
            recommendation = "Memory usage is moderate, monitor for leaks"
        elif memory_usage < 90:
            status = "high"
            recommendation = "Memory usage is high, check for memory leaks"
        else:
            status = "critical"
            recommendation = "Memory usage is critical, immediate action required"
        
        return {
            "current_usage": memory_usage,
            "status": status,
            "recommendation": recommendation,
            "threshold_breached": memory_usage > 85
        }
    
    def _analyze_response_times(self, response_times: List[float]) -> Dict[str, Any]:
        """Analyze response time patterns"""
        if not response_times:
            return {
                "average": 0,
                "median": 0,
                "p95": 0,
                "p99": 0,
                "status": "no_data",
                "recommendation": "No response time data available"
            }
        
        times_array = np.array(response_times)
        average = float(np.mean(times_array))
        median = float(np.median(times_array))
        p95 = float(np.percentile(times_array, 95))
        p99 = float(np.percentile(times_array, 99))
        
        if p95 < 200:
            status = "excellent"
            recommendation = "Response times are excellent"
        elif p95 < 500:
            status = "good"
            recommendation = "Response times are good"
        elif p95 < 1000:
            status = "moderate"
            recommendation = "Response times are moderate, consider optimization"
        else:
            status = "poor"
            recommendation = "Response times are poor, optimization required"
        
        return {
            "average": average,
            "median": median,
            "p95": p95,
            "p99": p99,
            "status": status,
            "recommendation": recommendation,
            "threshold_breached": p95 > 1000
        }
    
    def _analyze_error_rate(self, error_rate: float) -> Dict[str, Any]:
        """Analyze error rate patterns"""
        if error_rate < 1:
            status = "excellent"
            recommendation = "Error rate is excellent"
        elif error_rate < 3:
            status = "good"
            recommendation = "Error rate is acceptable"
        elif error_rate < 5:
            status = "moderate"
            recommendation = "Error rate is moderate, investigate causes"
        else:
            status = "high"
            recommendation = "Error rate is high, immediate investigation required"
        
        return {
            "current_rate": error_rate,
            "status": status,
            "recommendation": recommendation,
            "threshold_breached": error_rate > 5
        }
    
    def _analyze_network(self, network_io: Dict[str, int]) -> Dict[str, Any]:
        """Analyze network I/O patterns"""
        if not network_io:
            return {
                "status": "no_data",
                "recommendation": "No network data available"
            }
        
        bytes_sent = network_io.get("bytes_sent", 0)
        bytes_recv = network_io.get("bytes_recv", 0)
        total_bytes = bytes_sent + bytes_recv
        
        # Convert to MB for easier analysis
        total_mb = total_bytes / (1024 * 1024)
        
        if total_mb < 100:
            status = "low"
            recommendation = "Network usage is low"
        elif total_mb < 1000:
            status = "moderate"
            recommendation = "Network usage is moderate"
        else:
            status = "high"
            recommendation = "Network usage is high, monitor bandwidth"
        
        return {
            "bytes_sent": bytes_sent,
            "bytes_received": bytes_recv,
            "total_bytes": total_bytes,
            "total_mb": total_mb,
            "status": status,
            "recommendation": recommendation
        }
    
    def _calculate_overall_health(self, analysis: Dict[str, Any]) -> str:
        """Calculate overall system health based on all metrics"""
        critical_issues = 0
        high_issues = 0
        moderate_issues = 0
        
        # Check each analysis component
        components = ["cpu_analysis", "memory_analysis", "response_time_analysis", "error_rate_analysis"]
        
        for component in components:
            if component in analysis:
                status = analysis[component].get("status", "unknown")
                threshold_breached = analysis[component].get("threshold_breached", False)
                
                if status in ["critical", "poor"] or threshold_breached:
                    critical_issues += 1
                elif status in ["high"]:
                    high_issues += 1
                elif status in ["moderate"]:
                    moderate_issues += 1
        
        # Determine overall health
        if critical_issues > 0:
            return "critical"
        elif high_issues > 1:
            return "degraded"
        elif high_issues > 0 or moderate_issues > 2:
            return "warning"
        else:
            return "healthy"