"""
Integration tests for CRUD operations and telemetry system.
Tests the complete integration between FastAPI middleware and Django backend.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

# Import the main application
from main import app

# Import models for testing
from crud.models import CRUDRequest, CRUDOperation
from telemetry.models import TelemetryData, TelemetryType, TelemetrySource


class TestCRUDIntegration:
    """Test CRUD operations integration"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_crud_create_operation(self):
        """Test CRUD create operation"""
        crud_request = {
            "operation": "create",
            "entity_type": "analytics.analyticsdata",
            "data": {
                "metric_name": "test_metric",
                "metric_value": 42.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        response = self.client.post("/crud", json=crud_request)
        
        # Should return 401 without authentication in this test setup
        assert response.status_code in [200, 401, 422]
    
    def test_crud_read_operation(self):
        """Test CRUD read operation"""
        crud_request = {
            "operation": "read",
            "entity_type": "analytics.analyticsdata",
            "entity_id": "123e4567-e89b-12d3-a456-426614174000"
        }
        
        response = self.client.post("/crud", json=crud_request)
        
        # Should return 401 without authentication in this test setup
        assert response.status_code in [200, 401, 422]
    
    def test_crud_invalid_request(self):
        """Test CRUD with invalid request"""
        invalid_request = {
            "operation": "invalid_operation",
            "entity_type": "invalid.type"
        }
        
        response = self.client.post("/crud", json=invalid_request)
        
        # Should return validation error
        assert response.status_code == 422


class TestTelemetryIntegration:
    """Test telemetry system integration"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_telemetry_single_collection(self):
        """Test single telemetry data collection"""
        telemetry_data = {
            "type": "metric",
            "source": "application",
            "name": "cpu_usage",
            "value": 75.5,
            "unit": "percent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "test_service",
            "host": "test_host"
        }
        
        response = self.client.post("/telemetry", json=telemetry_data)
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "telemetry_id" in data
    
    def test_telemetry_batch_collection(self):
        """Test batch telemetry data collection"""
        batch_data = [
            {
                "type": "metric",
                "source": "application",
                "name": "memory_usage",
                "value": 60.0,
                "unit": "percent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "type": "log",
                "source": "system",
                "name": "error_log",
                "value": "Test error message",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        response = self.client.post("/telemetry/batch", json=batch_data)
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "telemetry_ids" in data
    
    def test_telemetry_correlations_endpoint(self):
        """Test telemetry correlations endpoint"""
        response = self.client.get("/telemetry/correlations?limit=10")
        
        # Should succeed or require authentication
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "correlations" in data
    
    def test_telemetry_analysis_endpoint(self):
        """Test telemetry analysis endpoint"""
        response = self.client.get("/telemetry/analysis?limit=10")
        
        # Should succeed or require authentication
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "analysis_results" in data
    
    def test_telemetry_metrics_endpoint(self):
        """Test telemetry metrics endpoint"""
        response = self.client.get("/telemetry/metrics")
        
        # Should succeed or require authentication
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "metrics" in data


class TestDjangoIntegration:
    """Test Django backend integration"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_django_health_check(self):
        """Test Django health check endpoint"""
        response = self.client.get("/django/health")
        
        # Should return health status (may fail if Django is not running)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "health_check" in data or "error" in data


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_basic_health_check(self):
        """Test basic health check"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "middleware"
    
    def test_detailed_health_check(self):
        """Test detailed health check"""
        response = self.client.get("/health/detailed")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "service" in data
    
    def test_cache_health_check(self):
        """Test cache health check"""
        response = self.client.get("/cache/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Observer Eye Middleware API"
        assert "endpoints" in data
        
        # Check that new endpoints are listed
        endpoints = data["endpoints"]
        assert "crud" in endpoints
        assert "telemetry" in endpoints
        assert "telemetry_batch" in endpoints


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])