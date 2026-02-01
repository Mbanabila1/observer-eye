"""
Error handling middleware for comprehensive error management
"""

import traceback
import structlog
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

from .exceptions import (
    ObserverEyeException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ServiceUnavailableError,
    CircuitBreakerOpenError,
    DataProcessingError,
    CacheError,
    StreamingError
)

logger = structlog.get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive error handling middleware that provides structured error responses
    and logging for all types of exceptions.
    
    Validates Requirements 5.1, 5.3: Error logging and user-friendly error messages
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any exceptions"""
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as exc:
            # FastAPI HTTP exceptions - let them pass through
            raise exc
            
        except ObserverEyeException as exc:
            # Custom application exceptions
            return await self._handle_observer_eye_exception(request, exc)
            
        except Exception as exc:
            # Unhandled exceptions
            return await self._handle_generic_exception(request, exc)
    
    async def _handle_observer_eye_exception(self, request: Request, exc: ObserverEyeException) -> JSONResponse:
        """Handle custom Observer Eye exceptions"""
        
        # Log the exception with context
        logger.error(
            "Observer Eye exception occurred",
            error_code=exc.error_code,
            error_message=exc.message,
            error_details=exc.details,
            url=str(request.url),
            method=request.method,
            user_agent=request.headers.get("user-agent"),
            request_id=request.headers.get("X-Request-ID")
        )
        
        # Determine status code based on exception type
        status_code = self._get_status_code_for_exception(exc)
        
        # Create user-friendly error response
        error_response = {
            "error": {
                "code": exc.error_code,
                "message": self._get_user_friendly_message(exc),
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request.headers.get("X-Request-ID")
            }
        }
        
        # Add details for development environment
        if self._is_development_environment():
            error_response["error"]["details"] = exc.details
            error_response["error"]["original_message"] = exc.message
        
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    async def _handle_generic_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle generic unhandled exceptions"""
        
        # Log the full exception with traceback
        logger.error(
            "Unhandled exception occurred",
            error_type=type(exc).__name__,
            error_message=str(exc),
            traceback=traceback.format_exc(),
            url=str(request.url),
            method=request.method,
            user_agent=request.headers.get("user-agent"),
            request_id=request.headers.get("X-Request-ID")
        )
        
        # Create generic error response (don't expose internal details)
        error_response = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please try again later.",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request.headers.get("X-Request-ID")
            }
        }
        
        # Add details for development environment
        if self._is_development_environment():
            error_response["error"]["details"] = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc().split('\n')
            }
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )
    
    def _get_status_code_for_exception(self, exc: ObserverEyeException) -> int:
        """Map exception types to HTTP status codes"""
        status_code_map = {
            ValidationError: 400,
            AuthenticationError: 401,
            AuthorizationError: 403,
            ServiceUnavailableError: 503,
            CircuitBreakerOpenError: 503,
            DataProcessingError: 422,
            CacheError: 500,
            StreamingError: 500
        }
        
        return status_code_map.get(type(exc), 500)
    
    def _get_user_friendly_message(self, exc: ObserverEyeException) -> str:
        """Generate user-friendly error messages"""
        
        if isinstance(exc, ValidationError):
            if exc.field:
                return f"Validation failed for field '{exc.field}': {exc.message}"
            return f"Validation failed: {exc.message}"
        
        elif isinstance(exc, AuthenticationError):
            return "Authentication is required to access this resource."
        
        elif isinstance(exc, AuthorizationError):
            return "You don't have permission to access this resource."
        
        elif isinstance(exc, ServiceUnavailableError):
            return f"The {exc.service_name} service is currently unavailable. Please try again later."
        
        elif isinstance(exc, CircuitBreakerOpenError):
            return f"The {exc.service_name} service is temporarily unavailable due to recent failures. Please try again later."
        
        elif isinstance(exc, DataProcessingError):
            if exc.stage:
                return f"Data processing failed at {exc.stage} stage. Please check your input data."
            return "Data processing failed. Please check your input data."
        
        elif isinstance(exc, CacheError):
            return "A caching error occurred. The request may take longer than usual."
        
        elif isinstance(exc, StreamingError):
            return "A streaming error occurred. Please refresh your connection."
        
        else:
            return exc.message
    
    def _is_development_environment(self) -> bool:
        """Check if we're in development environment"""
        import os
        return os.getenv("ENVIRONMENT", "development").lower() == "development"