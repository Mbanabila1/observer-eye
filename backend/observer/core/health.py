"""
Health check utilities for the Observer Eye platform.
"""

from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint for container orchestration.
    
    Returns:
        JsonResponse: Health status with basic system information
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Basic health information
    health_data = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "version": "1.0.0",
        "environment": getattr(settings, 'ENVIRONMENT', 'development')
    }
    
    status_code = 200 if health_data["status"] == "healthy" else 503
    
    return JsonResponse(health_data, status=status_code)


def readiness_check(request):
    """
    Readiness check endpoint for container orchestration.
    
    Returns:
        JsonResponse: Readiness status
    """
    try:
        # Check if all critical services are ready
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            migration_count = cursor.fetchone()[0]
        
        ready = migration_count > 0
        
        readiness_data = {
            "ready": ready,
            "migrations": migration_count,
            "timestamp": "2024-01-01T00:00:00Z"  # Would be actual timestamp in production
        }
        
        status_code = 200 if ready else 503
        
        return JsonResponse(readiness_data, status=status_code)
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({
            "ready": False,
            "error": str(e)
        }, status=503)