"""
Tests for performance monitoring functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from performance.monitor import PerformanceMonitor, PerformanceMetrics, Alert
from performance.metrics import MetricsCollector
from performance.analyzer import PerformanceAnalyzer


class TestPerformanceMonitor:
    """Test performance monitoring functionality"""
    
    @pytest.fixture
    async def performance_monitor(self):
        """Create a performance monitor for testing"""
        monitor = PerformanceMonitor()
        await monitor.initialize()
        yield monitor
        await monitor.cleanup()
    
    @pytest.mark.asyncio
    async def test_performance_monitor_initialization(self):
        """Test performance monitor initialization"""
        monitor = PerformanceMonitor()
        await monitor.initialize()
        
        assert monitor._is_monitoring is True
        assert monitor._monitoring_task is not None
        
        await monitor.cleanup()
        assert monitor._is_monitoring is False
    
    @pytest.mark.asyncio
    async def test_request_tracking(self, performance_monitor):
        """Test request tracking functionality"""
        request_id = "test_request_123"
        
        # Start tracking
        start_time = performance_monitor.start_request_tracking(request_id)
        assert request_id in performance_monitor.active_requests
        assert performance_monitor.active_requests[request_id] == start_time
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # End tracking
        response_time = performance_monitor.end_request_tracking(request_id, start_time)
        assert request_id not in performance_monitor.active_requests
        assert response_time > 0
        assert len(performance_monitor.response_times) > 0
    
    @pytest.mark.asyncio
    async def test_error_recording(self, performance_monitor):
        """Test error recording functionality"""
        initial_error_count = performance_monitor.error_count
        
        performance_monitor.record_error()
        
        assert performance_monitor.error_count == initial_error_count + 1
    
    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    async def test_metrics_collection(self, mock_net, mock_disk, mock_memory, mock_cpu, performance_monitor):
        """Test comprehensive metrics collection"""
        # Mock system metrics
        mock_cpu.return_value = 45.0
        mock_memory.return_value = MagicMock(percent=60.0)
        mock_disk.return_value = MagicMock(used=1000, total=2000)
        mock_net.return_value = MagicMock(
            bytes_sent=1000000,
            bytes_recv=2000000,
            packets_sent=5000,
            packets_recv=10000
        )
        
        metrics = await performance_monitor.collect_metrics()
        
        assert "timestamp" in metrics
        assert metrics["cpu_usage"] == 45.0
        assert metrics["memory_usage"] == 60.0
        assert metrics["disk_usage"] == 50.0  # 1000/2000 * 100
        assert "network_io" in metrics
        assert metrics["network_io"]["bytes_sent"] == 1000000
        assert "active_requests" in metrics
        assert "response_times" in metrics
        assert "error_rate" in metrics
    
    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    async def test_health_metrics(self, mock_memory, mock_cpu, performance_monitor):
        """Test health metrics collection"""
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=40.0)
        
        health_metrics = await performance_monitor.get_health_metrics()
        
        assert health_metrics["cpu_usage"] == 30.0
        assert health_metrics["memory_usage"] == 40.0
        assert "active_requests" in health_metrics
        assert "total_requests" in health_metrics
        assert "error_count" in health_metrics
        assert "uptime" in health_metrics
    
    @pytest.mark.asyncio
    async def test_alert_generation(self, performance_monitor):
        """Test alert generation on threshold breach"""
        # Set low thresholds for testing
        performance_monitor.thresholds["response_time"] = 50.0  # 50ms
        
        request_id = "test_request"
        start_time = performance_monitor.start_request_tracking(request_id)
        
        # Simulate slow response
        await asyncio.sleep(0.1)  # 100ms
        
        performance_monitor.end_request_tracking(request_id, start_time)
        
        # Check if alert was generated
        assert len(performance_monitor.alerts) > 0
        alert = performance_monitor.alerts[0]
        assert alert.metric_name == "response_time"
        assert alert.severity == "warning"
        assert alert.current_value > 50.0


class TestMetricsCollector:
    """Test metrics collection and storage"""
    
    @pytest.fixture
    async def metrics_collector(self):
        """Create a metrics collector for testing"""
        collector = MetricsCollector(max_metrics=100)
        await collector.initialize()
        yield collector
        await collector.cleanup()
    
    @pytest.mark.asyncio
    async def test_metrics_storage(self, metrics_collector):
        """Test storing metrics"""
        test_metrics = {
            "timestamp": "2024-01-01T00:00:00Z",
            "cpu_usage": 50.0,
            "memory_usage": 60.0
        }
        
        await metrics_collector.store_metrics(test_metrics)
        
        latest_metrics = await metrics_collector.get_latest_metrics(1)
        assert len(latest_metrics) == 1
        assert latest_metrics[0]["cpu_usage"] == 50.0
        assert "stored_at" in latest_metrics[0]
    
    @pytest.mark.asyncio
    async def test_metrics_retrieval_with_time_range(self, metrics_collector):
        """Test retrieving metrics within a time range"""
        # Store multiple metrics with different timestamps
        base_time = datetime.utcnow()
        
        for i in range(5):
            test_metrics = {
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                "cpu_usage": 50.0 + i,
                "memory_usage": 60.0 + i
            }
            await metrics_collector.store_metrics(test_metrics)
        
        # Retrieve metrics within a specific range
        start_time = base_time + timedelta(minutes=1)
        end_time = base_time + timedelta(minutes=3)
        
        filtered_metrics = await metrics_collector.get_metrics(start_time, end_time)
        
        # Should get metrics for minutes 1, 2, and 3
        assert len(filtered_metrics) == 3
        assert filtered_metrics[0]["cpu_usage"] == 51.0
        assert filtered_metrics[-1]["cpu_usage"] == 53.0
    
    @pytest.mark.asyncio
    async def test_metrics_summary(self, metrics_collector):
        """Test metrics summary functionality"""
        # Initially empty
        summary = await metrics_collector.get_metrics_summary()
        assert summary["total_count"] == 0
        assert summary["oldest_timestamp"] is None
        
        # Add some metrics
        for i in range(3):
            test_metrics = {
                "timestamp": f"2024-01-01T00:0{i}:00Z",
                "cpu_usage": 50.0 + i
            }
            await metrics_collector.store_metrics(test_metrics)
        
        summary = await metrics_collector.get_metrics_summary()
        assert summary["total_count"] == 3
        assert summary["oldest_timestamp"] == "2024-01-01T00:00:00Z"
        assert summary["newest_timestamp"] == "2024-01-01T00:02:00Z"
        assert summary["storage_utilization"] == 3.0  # 3/100 * 100


class TestPerformanceAnalyzer:
    """Test performance analysis functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a performance analyzer for testing"""
        return PerformanceAnalyzer()
    
    @pytest.mark.asyncio
    async def test_cpu_analysis(self, analyzer):
        """Test CPU usage analysis"""
        # Test optimal CPU usage
        metrics = {"cpu_usage": 30.0}
        analysis = await analyzer.analyze(metrics)
        
        cpu_analysis = analysis["cpu_analysis"]
        assert cpu_analysis["status"] == "optimal"
        assert cpu_analysis["threshold_breached"] is False
        
        # Test high CPU usage
        metrics = {"cpu_usage": 85.0}
        analysis = await analyzer.analyze(metrics)
        
        cpu_analysis = analysis["cpu_analysis"]
        assert cpu_analysis["status"] == "critical"
        assert cpu_analysis["threshold_breached"] is True
    
    @pytest.mark.asyncio
    async def test_memory_analysis(self, analyzer):
        """Test memory usage analysis"""
        # Test optimal memory usage
        metrics = {"memory_usage": 50.0}
        analysis = await analyzer.analyze(metrics)
        
        memory_analysis = analysis["memory_analysis"]
        assert memory_analysis["status"] == "optimal"
        assert memory_analysis["threshold_breached"] is False
        
        # Test high memory usage
        metrics = {"memory_usage": 95.0}
        analysis = await analyzer.analyze(metrics)
        
        memory_analysis = analysis["memory_analysis"]
        assert memory_analysis["status"] == "critical"
        assert memory_analysis["threshold_breached"] is True
    
    @pytest.mark.asyncio
    async def test_response_time_analysis(self, analyzer):
        """Test response time analysis"""
        # Test excellent response times
        metrics = {"response_times": [50.0, 60.0, 70.0, 80.0, 90.0]}
        analysis = await analyzer.analyze(metrics)
        
        rt_analysis = analysis["response_time_analysis"]
        assert rt_analysis["status"] == "excellent"
        assert rt_analysis["p95"] < 200
        assert rt_analysis["threshold_breached"] is False
        
        # Test poor response times
        metrics = {"response_times": [1500.0, 1600.0, 1700.0, 1800.0, 1900.0]}
        analysis = await analyzer.analyze(metrics)
        
        rt_analysis = analysis["response_time_analysis"]
        assert rt_analysis["status"] == "poor"
        assert rt_analysis["p95"] > 1000
        assert rt_analysis["threshold_breached"] is True
    
    @pytest.mark.asyncio
    async def test_error_rate_analysis(self, analyzer):
        """Test error rate analysis"""
        # Test excellent error rate
        metrics = {"error_rate": 0.5}
        analysis = await analyzer.analyze(metrics)
        
        error_analysis = analysis["error_rate_analysis"]
        assert error_analysis["status"] == "excellent"
        assert error_analysis["threshold_breached"] is False
        
        # Test high error rate
        metrics = {"error_rate": 8.0}
        analysis = await analyzer.analyze(metrics)
        
        error_analysis = analysis["error_rate_analysis"]
        assert error_analysis["status"] == "high"
        assert error_analysis["threshold_breached"] is True
    
    @pytest.mark.asyncio
    async def test_overall_health_calculation(self, analyzer):
        """Test overall health calculation"""
        # Test healthy system
        metrics = {
            "cpu_usage": 30.0,
            "memory_usage": 50.0,
            "response_times": [100.0, 120.0, 110.0],
            "error_rate": 1.0
        }
        analysis = await analyzer.analyze(metrics)
        assert analysis["overall_health"] == "healthy"
        
        # Test critical system
        metrics = {
            "cpu_usage": 95.0,  # Critical
            "memory_usage": 95.0,  # Critical
            "response_times": [2000.0, 2100.0, 2200.0],  # Poor
            "error_rate": 10.0  # High
        }
        analysis = await analyzer.analyze(metrics)
        assert analysis["overall_health"] == "critical"