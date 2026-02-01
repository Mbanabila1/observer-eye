"""
Tests for error handling middleware and circuit breaker functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from error_handling.exceptions import (
    ObserverEyeException,
    ValidationError,
    AuthenticationError,
    ServiceUnavailableError,
    CircuitBreakerOpenError
)
from error_handling.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerConfig
from error_handling.middleware import ErrorHandlingMiddleware


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker for testing"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout=1,  # 1 second for faster testing
            success_threshold=2,
            monitoring_window=60
        )
        cb = CircuitBreaker(config)
        cb.initialize()
        return cb
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state allows calls"""
        async def successful_function():
            return "success"
        
        result = await circuit_breaker.call("test_service", successful_function)
        assert result == "success"
        
        status = await circuit_breaker.get_circuit_status("test_service")
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures"""
        async def failing_function():
            raise Exception("Service failure")
        
        # Cause failures to reach threshold
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call("test_service", failing_function)
        
        status = await circuit_breaker.get_circuit_status("test_service")
        assert status["state"] == "open"
        assert status["failure_count"] == 3
        
        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call("test_service", failing_function)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self, circuit_breaker):
        """Test circuit breaker transitions to half-open after timeout"""
        async def failing_function():
            raise Exception("Service failure")
        
        async def successful_function():
            return "success"
        
        # Cause failures to open circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call("test_service", failing_function)
        
        # Wait for timeout
        await asyncio.sleep(1.1)
        
        # Next call should transition to half-open and succeed
        result = await circuit_breaker.call("test_service", successful_function)
        assert result == "success"
        
        status = await circuit_breaker.get_circuit_status("test_service")
        assert status["state"] == "half_open"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_successes(self, circuit_breaker):
        """Test circuit breaker closes after successful calls in half-open state"""
        async def failing_function():
            raise Exception("Service failure")
        
        async def successful_function():
            return "success"
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call("test_service", failing_function)
        
        # Wait for timeout and transition to half-open
        await asyncio.sleep(1.1)
        
        # Make successful calls to close circuit
        for i in range(2):  # success_threshold = 2
            result = await circuit_breaker.call("test_service", successful_function)
            assert result == "success"
        
        status = await circuit_breaker.get_circuit_status("test_service")
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_reset(self, circuit_breaker):
        """Test manual circuit breaker reset"""
        async def failing_function():
            raise Exception("Service failure")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call("test_service", failing_function)
        
        status = await circuit_breaker.get_circuit_status("test_service")
        assert status["state"] == "open"
        
        # Reset the circuit
        await circuit_breaker.reset_circuit("test_service")
        
        status = await circuit_breaker.get_circuit_status("test_service")
        assert status["state"] == "closed"
        assert status["failure_count"] == 0


class TestErrorHandlingMiddleware:
    """Test error handling middleware"""
    
    def test_observer_eye_exception_handling(self):
        """Test handling of custom Observer Eye exceptions"""
        with patch('main.performance_monitor') as mock_perf, \
             patch('main.circuit_breaker') as mock_cb:
            
            # Mock dependencies
            mock_perf.initialize = AsyncMock()
            mock_perf.cleanup = AsyncMock()
            mock_perf.get_current_timestamp.return_value = "2024-01-01T00:00:00Z"
            mock_perf.start_request_tracking.return_value = 1234567890.0
            mock_perf.end_request_tracking.return_value = 100.0
            mock_cb.initialize.return_value = None
            
            from main import app
            
            # Add a test endpoint that raises ValidationError
            @app.get("/test/validation-error")
            async def test_validation_error():
                raise ValidationError("Test validation error", field="test_field")
            
            client = TestClient(app)
            response = client.get("/test/validation-error")
            
            assert response.status_code == 400
            data = response.json()
            assert data["error"]["code"] == "VALIDATION_ERROR"
            assert "validation" in data["error"]["message"].lower()
    
    def test_authentication_error_handling(self):
        """Test handling of authentication errors"""
        with patch('main.performance_monitor') as mock_perf, \
             patch('main.circuit_breaker') as mock_cb:
            
            # Mock dependencies
            mock_perf.initialize = AsyncMock()
            mock_perf.cleanup = AsyncMock()
            mock_perf.get_current_timestamp.return_value = "2024-01-01T00:00:00Z"
            mock_perf.start_request_tracking.return_value = 1234567890.0
            mock_perf.end_request_tracking.return_value = 100.0
            mock_cb.initialize.return_value = None
            
            from main import app
            
            # Add a test endpoint that raises AuthenticationError
            @app.get("/test/auth-error")
            async def test_auth_error():
                raise AuthenticationError("Test authentication error")
            
            client = TestClient(app)
            response = client.get("/test/auth-error")
            
            assert response.status_code == 401
            data = response.json()
            assert data["error"]["code"] == "AUTHENTICATION_ERROR"
            assert "authentication" in data["error"]["message"].lower()
    
    def test_service_unavailable_error_handling(self):
        """Test handling of service unavailable errors"""
        with patch('main.performance_monitor') as mock_perf, \
             patch('main.circuit_breaker') as mock_cb:
            
            # Mock dependencies
            mock_perf.initialize = AsyncMock()
            mock_perf.cleanup = AsyncMock()
            mock_perf.get_current_timestamp.return_value = "2024-01-01T00:00:00Z"
            mock_perf.start_request_tracking.return_value = 1234567890.0
            mock_perf.end_request_tracking.return_value = 100.0
            mock_cb.initialize.return_value = None
            
            from main import app
            
            # Add a test endpoint that raises ServiceUnavailableError
            @app.get("/test/service-error")
            async def test_service_error():
                raise ServiceUnavailableError("test_service", "Test service unavailable")
            
            client = TestClient(app)
            response = client.get("/test/service-error")
            
            assert response.status_code == 503
            data = response.json()
            assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
            assert "test_service" in data["error"]["message"]
    
    def test_circuit_breaker_error_handling(self):
        """Test handling of circuit breaker errors"""
        with patch('main.performance_monitor') as mock_perf, \
             patch('main.circuit_breaker') as mock_cb:
            
            # Mock dependencies
            mock_perf.initialize = AsyncMock()
            mock_perf.cleanup = AsyncMock()
            mock_perf.get_current_timestamp.return_value = "2024-01-01T00:00:00Z"
            mock_perf.start_request_tracking.return_value = 1234567890.0
            mock_perf.end_request_tracking.return_value = 100.0
            mock_cb.initialize.return_value = None
            
            from main import app
            
            # Add a test endpoint that raises CircuitBreakerOpenError
            @app.get("/test/circuit-breaker-error")
            async def test_circuit_breaker_error():
                raise CircuitBreakerOpenError("test_service")
            
            client = TestClient(app)
            response = client.get("/test/circuit-breaker-error")
            
            assert response.status_code == 503
            data = response.json()
            assert data["error"]["code"] == "CIRCUIT_BREAKER_OPEN"
            assert "temporarily unavailable" in data["error"]["message"].lower()
    
    def test_generic_exception_handling(self):
        """Test handling of generic exceptions"""
        with patch('main.performance_monitor') as mock_perf, \
             patch('main.circuit_breaker') as mock_cb:
            
            # Mock dependencies
            mock_perf.initialize = AsyncMock()
            mock_perf.cleanup = AsyncMock()
            mock_perf.get_current_timestamp.return_value = "2024-01-01T00:00:00Z"
            mock_perf.start_request_tracking.return_value = 1234567890.0
            mock_perf.end_request_tracking.return_value = 100.0
            mock_cb.initialize.return_value = None
            
            from main import app
            
            # Add a test endpoint that raises a generic exception
            @app.get("/test/generic-error")
            async def test_generic_error():
                raise ValueError("Test generic error")
            
            client = TestClient(app)
            response = client.get("/test/generic-error")
            
            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
            assert "internal server error" in data["error"]["message"].lower()


class TestGracefulDegradation:
    """Test graceful degradation patterns"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_health_check(self):
        """Test circuit breaker health check functionality"""
        circuit_breaker = CircuitBreaker()
        circuit_breaker.initialize()
        
        health = await circuit_breaker.health_check()
        assert health["total_circuits"] == 0
        assert health["open_circuits"] == 0
        assert health["health_status"] == "healthy"
        
        # Simulate a circuit
        async def failing_function():
            raise Exception("Service failure")
        
        # Open a circuit
        for i in range(5):  # Default threshold is 5
            with pytest.raises(Exception):
                await circuit_breaker.call("test_service", failing_function)
        
        health = await circuit_breaker.health_check()
        assert health["total_circuits"] == 1
        assert health["open_circuits"] == 1
        assert health["health_status"] == "degraded"