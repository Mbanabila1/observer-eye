#!/usr/bin/env python3
"""
Observer Eye Platform - Performance and Load Testing Script

This script tests system performance under normal and high load conditions.
"""

import asyncio
import aiohttp
import json
import time
import statistics
import logging
import sys
import argparse
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import psutil
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceLoadTest:
    """Performance and load testing suite."""
    
    def __init__(self, frontend_url: str, middleware_url: str, backend_url: str):
        self.frontend_url = frontend_url
        self.middleware_url = middleware_url
        self.backend_url = backend_url
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []
        self.performance_metrics = {}
    
    def success(self, message: str):
        """Log successful test."""
        logger.info(f"✓ {message}")
        self.tests_passed += 1
    
    def error(self, message: str):
        """Log failed test."""
        logger.error(f"✗ {message}")
        self.tests_failed += 1
        self.failed_tests.append(message)
    
    def warning(self, message: str):
        """Log warning."""
        logger.warning(f"⚠ {message}")
    
    async def measure_response_time(self, session: aiohttp.ClientSession, 
                                  url: str, method: str = 'GET', 
                                  data: Dict = None) -> Tuple[float, int]:
        """Measure response time for a single request."""
        start_time = time.time()
        
        try:
            if method.upper() == 'POST' and data:
                async with session.post(url, json=data) as response:
                    await response.read()
                    return time.time() - start_time, response.status
            else:
                async with session.get(url) as response:
                    await response.read()
                    return time.time() - start_time, response.status
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return time.time() - start_time, 0
    
    async def load_test_endpoint(self, url: str, concurrent_requests: int, 
                               total_requests: int, method: str = 'GET',
                               data: Dict = None) -> Dict[str, Any]:
        """Perform load test on a specific endpoint."""
        logger.info(f"Load testing {url} with {concurrent_requests} concurrent requests...")
        
        connector = aiohttp.TCPConnector(limit=concurrent_requests * 2)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            async def make_request():
                async with semaphore:
                    return await self.measure_response_time(session, url, method, data)
            
            # Execute requests
            start_time = time.time()
            tasks = [make_request() for _ in range(total_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Process results
            response_times = []
            status_codes = {}
            errors = 0
            
            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                else:
                    response_time, status_code = result
                    response_times.append(response_time)
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1
            
            # Calculate metrics
            if response_times:
                metrics = {
                    'total_requests': total_requests,
                    'successful_requests': len(response_times),
                    'failed_requests': errors,
                    'requests_per_second': total_requests / total_time,
                    'avg_response_time': statistics.mean(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'median_response_time': statistics.median(response_times),
                    'p95_response_time': self._percentile(response_times, 95),
                    'p99_response_time': self._percentile(response_times, 99),
                    'status_codes': status_codes,
                    'total_time': total_time
                }
            else:
                metrics = {
                    'total_requests': total_requests,
                    'successful_requests': 0,
                    'failed_requests': total_requests,
                    'requests_per_second': 0,
                    'total_time': total_time
                }
            
            return metrics
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict(),
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    
    async def test_docker_build_time(self) -> bool:
        """Test Docker build time requirements."""
        logger.info("Testing Docker build time requirements...")
        
        build_times = {}
        layers = ['backend', 'middleware', 'dashboard']
        
        for layer in layers:
            logger.info(f"Testing build time for {layer}...")
            
            start_time = time.time()
            
            try:
                # Run docker build command
                process = await asyncio.create_subprocess_exec(
                    'docker', 'build', '-t', f'observer-eye-{layer}-test', f'observer-eye/{layer}',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                build_time = time.time() - start_time
                build_times[layer] = build_time
                
                if process.returncode == 0:
                    if build_time < 300:  # 5 minutes
                        self.success(f"{layer} build completed in {build_time:.1f}s (requirement: <300s)")
                    else:
                        self.error(f"{layer} build took {build_time:.1f}s (exceeds 300s requirement)")
                else:
                    self.error(f"{layer} build failed: {stderr.decode()}")
                    
                # Cleanup test image
                try:
                    cleanup_process = await asyncio.create_subprocess_exec(
                        'docker', 'rmi', f'observer-eye-{layer}-test',
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    await cleanup_process.communicate()
                except:
                    pass
                    
            except Exception as e:
                self.error(f"Docker build test for {layer} failed: {str(e)}")
                build_times[layer] = float('inf')
        
        self.performance_metrics['build_times'] = build_times
        
        # Overall assessment
        max_build_time = max(build_times.values())
        if max_build_time < 300:
            self.success(f"All Docker builds meet time requirements (max: {max_build_time:.1f}s)")
            return True
        else:
            self.error(f"Docker build time requirement not met (max: {max_build_time:.1f}s)")
            return False
    
    async def test_api_performance(self) -> bool:
        """Test API performance under normal load."""
        logger.info("Testing API performance under normal load...")
        
        endpoints = [
            {'url': f'{self.middleware_url}/health', 'name': 'Middleware Health'},
            {'url': f'{self.backend_url}/health/', 'name': 'Backend Health'},
            {'url': f'{self.middleware_url}/metrics', 'name': 'Middleware Metrics'},
            {'url': f'{self.middleware_url}/cache/stats', 'name': 'Cache Stats'},
        ]
        
        performance_results = {}
        all_passed = True
        
        for endpoint in endpoints:
            metrics = await self.load_test_endpoint(
                endpoint['url'], 
                concurrent_requests=10, 
                total_requests=100
            )
            
            performance_results[endpoint['name']] = metrics
            
            # Evaluate performance
            if metrics['successful_requests'] >= 95:  # 95% success rate
                if metrics['avg_response_time'] < 1.0:  # < 1 second average
                    self.success(f"{endpoint['name']}: {metrics['avg_response_time']:.3f}s avg, {metrics['requests_per_second']:.1f} RPS")
                else:
                    self.warning(f"{endpoint['name']}: {metrics['avg_response_time']:.3f}s avg (slow)")
                    all_passed = False
            else:
                self.error(f"{endpoint['name']}: {metrics['successful_requests']}/{metrics['total_requests']} success rate")
                all_passed = False
        
        self.performance_metrics['api_performance'] = performance_results
        return all_passed
    
    async def test_data_ingestion_performance(self) -> bool:
        """Test data ingestion performance."""
        logger.info("Testing data ingestion performance...")
        
        # Test streaming data ingestion
        streaming_data = {
            "data": {
                "metric_name": "performance_test_metric",
                "value": 75.5,
                "timestamp": "2024-01-01T12:00:00Z"
            },
            "data_type": "real_time_metrics"
        }
        
        streaming_metrics = await self.load_test_endpoint(
            f'{self.middleware_url}/data/ingest/streaming',
            concurrent_requests=20,
            total_requests=200,
            method='POST',
            data=streaming_data
        )
        
        # Test batch data ingestion
        batch_data = {
            "data": [
                {
                    "metric_name": "batch_test_metric",
                    "value": 67.8,
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            ] * 10,  # 10 records per batch
            "data_type": "real_time_metrics"
        }
        
        batch_metrics = await self.load_test_endpoint(
            f'{self.middleware_url}/data/ingest/batch',
            concurrent_requests=10,
            total_requests=50,
            method='POST',
            data=batch_data
        )
        
        self.performance_metrics['data_ingestion'] = {
            'streaming': streaming_metrics,
            'batch': batch_metrics
        }
        
        # Evaluate performance
        streaming_passed = (
            streaming_metrics['successful_requests'] >= 180 and  # 90% success rate
            streaming_metrics['avg_response_time'] < 2.0  # < 2 seconds
        )
        
        batch_passed = (
            batch_metrics['successful_requests'] >= 45 and  # 90% success rate
            batch_metrics['avg_response_time'] < 5.0  # < 5 seconds for batch
        )
        
        if streaming_passed:
            self.success(f"Streaming ingestion: {streaming_metrics['avg_response_time']:.3f}s avg, {streaming_metrics['requests_per_second']:.1f} RPS")
        else:
            self.error(f"Streaming ingestion performance inadequate")
        
        if batch_passed:
            self.success(f"Batch ingestion: {batch_metrics['avg_response_time']:.3f}s avg, {batch_metrics['requests_per_second']:.1f} RPS")
        else:
            self.error(f"Batch ingestion performance inadequate")
        
        return streaming_passed and batch_passed
    
    async def test_concurrent_user_simulation(self) -> bool:
        """Simulate concurrent users accessing the system."""
        logger.info("Testing concurrent user simulation...")
        
        # Simulate different user workflows
        workflows = [
            # Workflow 1: Dashboard user
            [
                {'url': f'{self.frontend_url}/', 'method': 'GET'},
                {'url': f'{self.middleware_url}/metrics', 'method': 'GET'},
                {'url': f'{self.middleware_url}/cache/stats', 'method': 'GET'},
            ],
            # Workflow 2: API user
            [
                {'url': f'{self.middleware_url}/health', 'method': 'GET'},
                {'url': f'{self.middleware_url}/data/pipeline/stats', 'method': 'GET'},
                {'url': f'{self.middleware_url}/telemetry/metrics', 'method': 'GET'},
            ],
            # Workflow 3: Data ingestion user
            [
                {'url': f'{self.middleware_url}/data/ingest/stats', 'method': 'GET'},
                {'url': f'{self.middleware_url}/data/ingest/streaming', 'method': 'POST', 
                 'data': {"data": {"metric_name": "test", "value": 1}, "data_type": "real_time_metrics"}},
            ]
        ]
        
        async def simulate_user_workflow(workflow_id: int, workflow: List[Dict]):
            """Simulate a single user workflow."""
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                workflow_times = []
                
                for step in workflow:
                    start_time = time.time()
                    try:
                        if step['method'] == 'POST':
                            async with session.post(step['url'], json=step.get('data')) as response:
                                await response.read()
                        else:
                            async with session.get(step['url']) as response:
                                await response.read()
                        
                        workflow_times.append(time.time() - start_time)
                    except Exception as e:
                        logger.error(f"Workflow {workflow_id} step failed: {str(e)}")
                        workflow_times.append(float('inf'))
                
                return workflow_times
        
        # Run concurrent user simulations
        concurrent_users = 25
        tasks = []
        
        for user_id in range(concurrent_users):
            workflow = workflows[user_id % len(workflows)]
            tasks.append(simulate_user_workflow(user_id, workflow))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_workflows = 0
        total_response_times = []
        
        for result in results:
            if isinstance(result, Exception):
                continue
            
            if all(t < 10.0 for t in result):  # All steps completed within 10 seconds
                successful_workflows += 1
                total_response_times.extend(result)
        
        success_rate = successful_workflows / concurrent_users
        avg_response_time = statistics.mean(total_response_times) if total_response_times else float('inf')
        
        self.performance_metrics['concurrent_users'] = {
            'concurrent_users': concurrent_users,
            'successful_workflows': successful_workflows,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'total_time': total_time
        }
        
        if success_rate >= 0.8 and avg_response_time < 5.0:
            self.success(f"Concurrent user test: {success_rate:.1%} success rate, {avg_response_time:.3f}s avg response")
            return True
        else:
            self.error(f"Concurrent user test failed: {success_rate:.1%} success rate, {avg_response_time:.3f}s avg response")
            return False
    
    async def test_system_resource_usage(self) -> bool:
        """Test system resource usage under load."""
        logger.info("Testing system resource usage under load...")
        
        # Get baseline metrics
        baseline_metrics = self.get_system_metrics()
        
        # Run load test while monitoring resources
        load_task = asyncio.create_task(
            self.load_test_endpoint(
                f'{self.middleware_url}/health',
                concurrent_requests=50,
                total_requests=500
            )
        )
        
        # Monitor resources during load test
        resource_samples = []
        for _ in range(10):  # Sample 10 times during the test
            await asyncio.sleep(1)
            resource_samples.append(self.get_system_metrics())
        
        # Wait for load test to complete
        load_metrics = await load_task
        
        # Analyze resource usage
        avg_cpu = statistics.mean([sample['cpu_percent'] for sample in resource_samples])
        avg_memory = statistics.mean([sample['memory_percent'] for sample in resource_samples])
        max_cpu = max([sample['cpu_percent'] for sample in resource_samples])
        max_memory = max([sample['memory_percent'] for sample in resource_samples])
        
        self.performance_metrics['resource_usage'] = {
            'baseline': baseline_metrics,
            'under_load': {
                'avg_cpu_percent': avg_cpu,
                'avg_memory_percent': avg_memory,
                'max_cpu_percent': max_cpu,
                'max_memory_percent': max_memory
            },
            'load_test_results': load_metrics
        }
        
        # Evaluate resource usage
        resource_passed = True
        
        if max_cpu < 80:
            self.success(f"CPU usage under control: {max_cpu:.1f}% max")
        else:
            self.warning(f"High CPU usage: {max_cpu:.1f}% max")
            resource_passed = False
        
        if max_memory < 80:
            self.success(f"Memory usage under control: {max_memory:.1f}% max")
        else:
            self.warning(f"High memory usage: {max_memory:.1f}% max")
            resource_passed = False
        
        return resource_passed
    
    async def test_real_time_streaming_performance(self) -> bool:
        """Test real-time streaming performance."""
        logger.info("Testing real-time streaming performance...")
        
        # This would require WebSocket testing
        # For now, we'll test the HTTP endpoints that support streaming
        
        streaming_endpoints = [
            f'{self.middleware_url}/data/ingest/streaming',
            f'{self.middleware_url}/telemetry'
        ]
        
        streaming_data = {
            "trace_id": "perf_test_123",
            "span_id": "span_456",
            "operation": "performance_test",
            "duration_ms": 45.2
        }
        
        all_passed = True
        
        for endpoint in streaming_endpoints:
            metrics = await self.load_test_endpoint(
                endpoint,
                concurrent_requests=30,
                total_requests=300,
                method='POST',
                data=streaming_data
            )
            
            # Streaming should handle high throughput with low latency
            if metrics['avg_response_time'] < 0.5 and metrics['requests_per_second'] > 100:
                self.success(f"Streaming endpoint {endpoint}: {metrics['avg_response_time']:.3f}s avg, {metrics['requests_per_second']:.1f} RPS")
            else:
                self.error(f"Streaming endpoint {endpoint} performance inadequate")
                all_passed = False
        
        return all_passed
    
    async def run_all_tests(self) -> bool:
        """Run all performance and load tests."""
        logger.info("Starting Performance and Load Tests...")
        logger.info("=" * 60)
        
        # Record initial system state
        initial_metrics = self.get_system_metrics()
        logger.info(f"Initial system state: CPU {initial_metrics['cpu_percent']:.1f}%, Memory {initial_metrics['memory_percent']:.1f}%")
        logger.info("")
        
        # Run all test methods
        test_methods = [
            self.test_docker_build_time,
            self.test_api_performance,
            self.test_data_ingestion_performance,
            self.test_concurrent_user_simulation,
            self.test_system_resource_usage,
            self.test_real_time_streaming_performance
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                logger.info("")  # Add spacing between tests
            except Exception as e:
                self.error(f"Test {test_method.__name__} crashed: {str(e)}")
                logger.info("")
        
        # Print results
        logger.info("=" * 60)
        logger.info("Performance and Load Test Results")
        logger.info("=" * 60)
        logger.info(f"Tests Passed: {self.tests_passed}")
        logger.info(f"Tests Failed: {self.tests_failed}")
        logger.info(f"Total Tests: {self.tests_passed + self.tests_failed}")
        
        # Print performance summary
        if self.performance_metrics:
            logger.info("")
            logger.info("Performance Summary:")
            logger.info("-" * 40)
            
            if 'api_performance' in self.performance_metrics:
                for endpoint, metrics in self.performance_metrics['api_performance'].items():
                    logger.info(f"{endpoint}: {metrics['avg_response_time']:.3f}s avg, {metrics['requests_per_second']:.1f} RPS")
            
            if 'build_times' in self.performance_metrics:
                logger.info("")
                logger.info("Docker Build Times:")
                for layer, build_time in self.performance_metrics['build_times'].items():
                    logger.info(f"  {layer}: {build_time:.1f}s")
        
        if self.tests_failed > 0:
            logger.error("")
            logger.error("Failed Tests:")
            for test in self.failed_tests:
                logger.error(f"  ✗ {test}")
            logger.error("")
            logger.error("Performance and load tests FAILED")
            return False
        else:
            logger.info("")
            logger.info("All performance and load tests PASSED")
            return True


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Performance and Load Test for Observer Eye Platform")
    parser.add_argument("--frontend-url", default="http://localhost:80",
                       help="Frontend URL (default: http://localhost:80)")
    parser.add_argument("--middleware-url", default="http://localhost:8400",
                       help="Middleware URL (default: http://localhost:8400)")
    parser.add_argument("--backend-url", default="http://localhost:8000",
                       help="Backend URL (default: http://localhost:8000)")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Test timeout in seconds (default: 300)")
    
    args = parser.parse_args()
    
    # Check if required tools are available
    if not psutil:
        logger.error("psutil is required but not installed. Install with: pip install psutil")
        sys.exit(1)
    
    # Create test instance
    test_suite = PerformanceLoadTest(
        args.frontend_url,
        args.middleware_url,
        args.backend_url
    )
    
    try:
        # Run tests with timeout
        success = await asyncio.wait_for(
            test_suite.run_all_tests(),
            timeout=args.timeout
        )
        
        sys.exit(0 if success else 1)
        
    except asyncio.TimeoutError:
        logger.error(f"Tests timed out after {args.timeout} seconds")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite crashed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())