#!/usr/bin/env python3
"""
Container Integration Test for FastAPI Middleware
Tests the containerized middleware functionality including eBPF integration
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any

import httpx
import pytest


class MiddlewareContainerTest:
    """Test suite for containerized FastAPI middleware"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_container_health(self) -> Dict[str, Any]:
        """Test container health endpoint"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert "deep_monitoring" in health_data
            assert "system_metrics" in health_data
            
            print("✅ Container health check passed")
            return health_data
            
        except Exception as e:
            print(f"❌ Container health check failed: {e}")
            raise
    
    async def test_deep_system_monitoring(self) -> Dict[str, Any]:
        """Test deep system monitoring functionality"""
        try:
            response = await self.client.get(f"{self.base_url}/deep-system/status")
            assert response.status_code == 200
            
            status_data = response.json()
            assert "monitoring_active" in status_data
            assert "ebpf_enabled" in status_data
            
            print("✅ Deep system monitoring test passed")
            return status_data
            
        except Exception as e:
            print(f"❌ Deep system monitoring test failed: {e}")
            raise
    
    async def test_system_metrics(self) -> Dict[str, Any]:
        """Test system metrics collection"""
        try:
            response = await self.client.get(f"{self.base_url}/metrics")
            assert response.status_code == 200
            
            metrics_data = response.json()
            assert "metrics" in metrics_data
            assert "ebpf_enabled" in metrics_data
            
            # Validate metric structure
            metrics = metrics_data["metrics"]
            assert "cpu" in metrics
            assert "memory" in metrics
            assert "disk" in metrics
            assert "network" in metrics
            
            print("✅ System metrics test passed")
            return metrics_data
            
        except Exception as e:
            print(f"❌ System metrics test failed: {e}")
            raise
    
    async def test_four_pillars_correlation(self) -> Dict[str, Any]:
        """Test four pillars data correlation"""
        try:
            test_data = {
                "correlation_id": "test-correlation-123",
                "timestamp": time.time(),
                "metrics": {"cpu_usage": 45.2, "memory_usage": 67.8},
                "events": {"event_type": "system_alert", "severity": "warning"},
                "logs": {"level": "INFO", "message": "Test log entry"},
                "traces": {"trace_id": "trace-456", "span_id": "span-789"}
            }
            
            response = await self.client.post(
                f"{self.base_url}/observability/correlate",
                json=test_data
            )
            assert response.status_code == 200
            
            correlation_result = response.json()
            assert correlation_result["status"] == "accepted"
            assert correlation_result["correlation_id"] == test_data["correlation_id"]
            
            print("✅ Four pillars correlation test passed")
            return correlation_result
            
        except Exception as e:
            print(f"❌ Four pillars correlation test failed: {e}")
            raise
    
    async def test_container_performance(self) -> Dict[str, Any]:
        """Test container performance under load"""
        try:
            # Test multiple concurrent requests
            tasks = []
            for i in range(10):
                task = self.client.get(f"{self.base_url}/metrics")
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # Validate all responses
            for response in responses:
                assert response.status_code == 200
            
            total_time = end_time - start_time
            avg_response_time = total_time / len(responses)
            
            performance_data = {
                "concurrent_requests": len(responses),
                "total_time": total_time,
                "average_response_time": avg_response_time,
                "requests_per_second": len(responses) / total_time
            }
            
            print(f"✅ Performance test passed - {performance_data['requests_per_second']:.2f} req/s")
            return performance_data
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            raise
    
    async def test_ebpf_integration(self) -> Dict[str, Any]:
        """Test eBPF integration (mock mode)"""
        try:
            # Get health data which includes eBPF status
            health_response = await self.client.get(f"{self.base_url}/health")
            health_data = health_response.json()
            
            deep_monitoring = health_data["deep_monitoring"]
            system_metrics = health_data["system_metrics"]
            
            # Validate eBPF configuration
            assert deep_monitoring["ebpf_enabled"] is True
            
            # Check for eBPF metrics in system data
            if "ebpf" in system_metrics:
                ebpf_metrics = system_metrics["ebpf"]
                assert "syscalls_per_second" in ebpf_metrics
                assert "kernel_events" in ebpf_metrics
                assert "deep_monitoring_active" in ebpf_metrics
            
            print("✅ eBPF integration test passed")
            return deep_monitoring
            
        except Exception as e:
            print(f"❌ eBPF integration test failed: {e}")
            raise
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all container tests"""
        print("🚀 Starting FastAPI Middleware Container Tests")
        print(f"Testing endpoint: {self.base_url}")
        print("-" * 60)
        
        results = {}
        
        try:
            # Wait for container to be ready
            print("⏳ Waiting for container to be ready...")
            await asyncio.sleep(5)
            
            # Run tests
            results["health"] = await self.test_container_health()
            results["deep_monitoring"] = await self.test_deep_system_monitoring()
            results["metrics"] = await self.test_system_metrics()
            results["correlation"] = await self.test_four_pillars_correlation()
            results["performance"] = await self.test_container_performance()
            results["ebpf"] = await self.test_ebpf_integration()
            
            print("-" * 60)
            print("🎉 All tests passed successfully!")
            
            return results
            
        except Exception as e:
            print(f"💥 Test suite failed: {e}")
            raise
        
        finally:
            await self.client.aclose()


async def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FastAPI Middleware Container")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Middleware URL (default: http://localhost:8000)")
    parser.add_argument("--wait", type=int, default=10,
                       help="Wait time for container startup (default: 10s)")
    
    args = parser.parse_args()
    
    # Wait for container startup
    if args.wait > 0:
        print(f"⏳ Waiting {args.wait} seconds for container startup...")
        await asyncio.sleep(args.wait)
    
    # Run tests
    tester = MiddlewareContainerTest(args.url)
    
    try:
        results = await tester.run_all_tests()
        
        # Print summary
        print("\n📊 Test Results Summary:")
        print(f"Health Status: {results['health']['status']}")
        print(f"Deep Monitoring: {'Active' if results['deep_monitoring']['monitoring_active'] else 'Inactive'}")
        print(f"eBPF Enabled: {results['ebpf']['ebpf_enabled']}")
        print(f"Performance: {results['performance']['requests_per_second']:.2f} req/s")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 Tests failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))