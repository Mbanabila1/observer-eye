"""
Basic test to validate FastAPI testing setup
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

def test_create_app():
    """Test that the app can be created without errors"""
    with patch('main.performance_monitor') as mock_perf, \
         patch('main.circuit_breaker') as mock_cb:
        
        # Mock the performance monitor methods
        mock_perf.initialize = AsyncMock()
        mock_perf.cleanup = AsyncMock()
        mock_perf.get_current_timestamp.return_value = "2024-01-01T00:00:00Z"
        mock_perf.start_request_tracking.return_value = 1234567890.0
        mock_perf.end_request_tracking.return_value = 100.0
        
        # Mock circuit breaker
        mock_cb.initialize.return_value = None
        
        from main import app
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Observer Eye Middleware API"
        assert data["status"] == "running"
        assert "version" in data
        assert "endpoints" in data


def test_health_endpoint():
    """Test the health check endpoint"""
    with patch('main.performance_monitor') as mock_perf, \
         patch('main.circuit_breaker') as mock_cb:
        
        # Mock the performance monitor methods
        mock_perf.initialize = AsyncMock()
        mock_perf.cleanup = AsyncMock()
        mock_perf.get_current_timestamp.return_value = "2024-01-01T00:00:00Z"
        mock_perf.start_request_tracking.return_value = 1234567890.0
        mock_perf.end_request_tracking.return_value = 100.0
        
        # Mock circuit breaker
        mock_cb.initialize.return_value = None
        
        from main import app
        client = TestClient(app)
        
        response = client.get("/health")
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "middleware"
        assert "version" in data
        assert "timestamp" in data


def test_detailed_health_endpoint():
    """Test the detailed health check endpoint"""
    with patch('main.performance_monitor') as mock_perf, \
         patch('main.circuit_breaker') as mock_cb:
        
        # Mock the performance monitor methods
        mock_perf.initialize = AsyncMock()
        mock_perf.cleanup = AsyncMock()
        mock_perf.get_current_timestamp.return_value = "2024-01-01T00:00:00Z"
        mock_perf.start_request_tracking.return_value = 1234567890.0
        mock_perf.end_request_tracking.return_value = 100.0
        mock_perf.get_health_metrics = AsyncMock(return_value={
            "cpu_usage": 25.0,
            "memory_usage": 45.0,
            "active_requests": 0,
            "total_requests": 1,
            "error_count": 0,
            "uptime": 3600
        })
        
        # Mock circuit breaker
        mock_cb.initialize.return_value = None
        
        from main import app
        client = TestClient(app)
        
        response = client.get("/health/detailed")
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "middleware"
        assert "metrics" in data
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality works"""
    async def async_test():
        return "async_works"
    
    result = await async_test()
    assert result == "async_works"