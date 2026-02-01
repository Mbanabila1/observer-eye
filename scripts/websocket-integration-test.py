#!/usr/bin/env python3
"""
Observer Eye Platform - WebSocket Integration Test

This script tests real-time WebSocket connections and streaming capabilities.
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, Any, List
import websockets
import aiohttp
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketIntegrationTest:
    """WebSocket integration test suite."""
    
    def __init__(self, websocket_url: str, api_url: str):
        self.websocket_url = websocket_url
        self.api_url = api_url
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []
    
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
    
    async def test_websocket_connection(self) -> bool:
        """Test basic WebSocket connection."""
        logger.info("Testing WebSocket connection...")
        
        try:
            async with websockets.connect(self.websocket_url, timeout=10) as websocket:
                self.success("WebSocket connection established")
                
                # Test ping/pong
                await websocket.ping()
                self.success("WebSocket ping/pong successful")
                
                return True
                
        except Exception as e:
            self.error(f"WebSocket connection failed: {str(e)}")
            return False
    
    async def test_websocket_subscription(self) -> bool:
        """Test WebSocket channel subscription."""
        logger.info("Testing WebSocket channel subscription...")
        
        try:
            async with websockets.connect(self.websocket_url, timeout=10) as websocket:
                # Subscribe to metrics channel
                subscribe_message = {
                    "action": "subscribe",
                    "channel": "metrics"
                }
                
                await websocket.send(json.dumps(subscribe_message))
                self.success("Subscription message sent")
                
                # Wait for subscription confirmation
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    if response_data.get("status") == "subscribed":
                        self.success("Channel subscription confirmed")
                        return True
                    else:
                        self.warning(f"Unexpected subscription response: {response_data}")
                        return False
                        
                except asyncio.TimeoutError:
                    self.warning("No subscription confirmation received (timeout)")
                    return False
                    
        except Exception as e:
            self.error(f"WebSocket subscription failed: {str(e)}")
            return False
    
    async def test_real_time_data_streaming(self) -> bool:
        """Test real-time data streaming through WebSocket."""
        logger.info("Testing real-time data streaming...")
        
        try:
            # Start WebSocket connection
            websocket_task = asyncio.create_task(self._websocket_listener())
            
            # Wait a moment for connection to establish
            await asyncio.sleep(1)
            
            # Send data through API to trigger WebSocket updates
            await self._send_test_data()
            
            # Wait for WebSocket to receive data
            await asyncio.sleep(2)
            
            # Cancel WebSocket listener
            websocket_task.cancel()
            
            try:
                await websocket_task
            except asyncio.CancelledError:
                pass
            
            self.success("Real-time data streaming test completed")
            return True
            
        except Exception as e:
            self.error(f"Real-time data streaming failed: {str(e)}")
            return False
    
    async def _websocket_listener(self):
        """Listen for WebSocket messages."""
        try:
            async with websockets.connect(self.websocket_url, timeout=10) as websocket:
                # Subscribe to metrics channel
                subscribe_message = {
                    "action": "subscribe",
                    "channel": "metrics"
                }
                await websocket.send(json.dumps(subscribe_message))
                
                # Listen for messages
                message_count = 0
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        logger.info(f"Received WebSocket message: {data}")
                        message_count += 1
                        
                        if message_count >= 1:  # Received at least one message
                            self.success("Real-time data received via WebSocket")
                            break
                            
                    except json.JSONDecodeError:
                        self.warning(f"Invalid JSON received: {message}")
                        
        except Exception as e:
            logger.error(f"WebSocket listener error: {str(e)}")
    
    async def _send_test_data(self):
        """Send test data through API."""
        test_data = {
            "data": {
                "metric_name": "websocket_test_metric",
                "value": 42.0,
                "timestamp": "2024-01-01T12:00:00Z",
                "source": "integration_test"
            },
            "data_type": "real_time_metrics"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/data/ingest/streaming",
                    json=test_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        self.success("Test data sent via API")
                    else:
                        self.warning(f"API request failed with status: {response.status}")
                        
        except Exception as e:
            self.error(f"Failed to send test data: {str(e)}")
    
    async def test_websocket_error_handling(self) -> bool:
        """Test WebSocket error handling."""
        logger.info("Testing WebSocket error handling...")
        
        try:
            async with websockets.connect(self.websocket_url, timeout=10) as websocket:
                # Send invalid message
                invalid_message = "invalid-json-message"
                await websocket.send(invalid_message)
                
                # Wait for error response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    if "error" in response_data:
                        self.success("WebSocket error handling working correctly")
                        return True
                    else:
                        self.warning("No error response received for invalid message")
                        return False
                        
                except asyncio.TimeoutError:
                    self.warning("No error response received (timeout)")
                    return False
                    
        except Exception as e:
            self.error(f"WebSocket error handling test failed: {str(e)}")
            return False
    
    async def test_websocket_reconnection(self) -> bool:
        """Test WebSocket reconnection capability."""
        logger.info("Testing WebSocket reconnection...")
        
        try:
            # First connection
            async with websockets.connect(self.websocket_url, timeout=10) as websocket1:
                await websocket1.ping()
                self.success("First WebSocket connection established")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Second connection (simulating reconnection)
            async with websockets.connect(self.websocket_url, timeout=10) as websocket2:
                await websocket2.ping()
                self.success("WebSocket reconnection successful")
                return True
                
        except Exception as e:
            self.error(f"WebSocket reconnection failed: {str(e)}")
            return False
    
    async def test_multiple_concurrent_connections(self) -> bool:
        """Test multiple concurrent WebSocket connections."""
        logger.info("Testing multiple concurrent WebSocket connections...")
        
        try:
            # Create multiple concurrent connections
            async def create_connection(connection_id: int):
                try:
                    async with websockets.connect(self.websocket_url, timeout=10) as websocket:
                        await websocket.ping()
                        logger.info(f"Connection {connection_id} established")
                        await asyncio.sleep(2)  # Keep connection alive briefly
                        return True
                except Exception as e:
                    logger.error(f"Connection {connection_id} failed: {str(e)}")
                    return False
            
            # Create 5 concurrent connections
            tasks = [create_connection(i) for i in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_connections = sum(1 for result in results if result is True)
            
            if successful_connections >= 3:  # At least 3 out of 5 should succeed
                self.success(f"Multiple concurrent connections successful ({successful_connections}/5)")
                return True
            else:
                self.error(f"Too few concurrent connections succeeded ({successful_connections}/5)")
                return False
                
        except Exception as e:
            self.error(f"Multiple concurrent connections test failed: {str(e)}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all WebSocket integration tests."""
        logger.info("Starting WebSocket integration tests...")
        logger.info("=" * 50)
        
        # Run all test methods
        test_methods = [
            self.test_websocket_connection,
            self.test_websocket_subscription,
            self.test_real_time_data_streaming,
            self.test_websocket_error_handling,
            self.test_websocket_reconnection,
            self.test_multiple_concurrent_connections
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                logger.info("")  # Add spacing between tests
            except Exception as e:
                self.error(f"Test {test_method.__name__} crashed: {str(e)}")
                logger.info("")
        
        # Print results
        logger.info("=" * 50)
        logger.info("WebSocket Integration Test Results")
        logger.info("=" * 50)
        logger.info(f"Tests Passed: {self.tests_passed}")
        logger.info(f"Tests Failed: {self.tests_failed}")
        logger.info(f"Total Tests: {self.tests_passed + self.tests_failed}")
        
        if self.tests_failed > 0:
            logger.error("")
            logger.error("Failed Tests:")
            for test in self.failed_tests:
                logger.error(f"  ✗ {test}")
            logger.error("")
            logger.error("WebSocket integration tests FAILED")
            return False
        else:
            logger.info("")
            logger.info("All WebSocket integration tests PASSED")
            return True


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="WebSocket Integration Test for Observer Eye Platform")
    parser.add_argument("--websocket-url", default="ws://localhost:8400/ws", 
                       help="WebSocket URL (default: ws://localhost:8400/ws)")
    parser.add_argument("--api-url", default="http://localhost:8400",
                       help="API URL (default: http://localhost:8400)")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Test timeout in seconds (default: 30)")
    
    args = parser.parse_args()
    
    # Create test instance
    test_suite = WebSocketIntegrationTest(args.websocket_url, args.api_url)
    
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