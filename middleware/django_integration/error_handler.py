"""
Django error handler for Observer Eye Middleware.
Handles error propagation and translation between Django and FastAPI.
"""

import traceback
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import structlog
from fastapi import HTTPException, status

from .models import APIResponse
from crud.exceptions import (
    CRUDError, ValidationError, EntityNotFoundError, EntityAlreadyExistsError,
    OptimisticLockError, PermissionDeniedError, DatabaseConnectionError,
    DatabaseOperationError
)

logger = structlog.get_logger(__name__)


class DjangoErrorHandler:
    """
    Error handler for Django backend integration.
    Translates Django errors to FastAPI-compatible responses.
    """
    
    def __init__(self, include_traceback: bool = False):
        self.include_traceback = include_traceback
        
        # Django error code mappings
        self.django_error_mappings = {
            # Django validation errors
            "ValidationError": "VALIDATION_ERROR",
            "IntegrityError": "INTEGRITY_ERROR",
            "DoesNotExist": "NOT_FOUND",
            "MultipleObjectsReturned": "MULTIPLE_OBJECTS_FOUND",
            
            # Django permission errors
            "PermissionDenied": "PERMISSION_DENIED",
            "AuthenticationFailed": "AUTHENTICATION_FAILED",
            
            # Django database errors
            "DatabaseError": "DATABASE_ERROR",
            "OperationalError": "DATABASE_OPERATIONAL_ERROR",
            "ProgrammingError": "DATABASE_PROGRAMMING_ERROR",
            "DataError": "DATABASE_DATA_ERROR",
            
            # HTTP errors
            "Http404": "NOT_FOUND",
            "BadRequest": "BAD_REQUEST",
            "Forbidden": "FORBIDDEN",
            "MethodNotAllowed": "METHOD_NOT_ALLOWED",
        }
        
        # HTTP status code mappings
        self.status_code_mappings = {
            400: status.HTTP_400_BAD_REQUEST,
            401: status.HTTP_401_UNAUTHORIZED,
            403: status.HTTP_403_FORBIDDEN,
            404: status.HTTP_404_NOT_FOUND,
            405: status.HTTP_405_METHOD_NOT_ALLOWED,
            409: status.HTTP_409_CONFLICT,
            422: status.HTTP_422_UNPROCESSABLE_ENTITY,
            429: status.HTTP_429_TOO_MANY_REQUESTS,
            500: status.HTTP_500_INTERNAL_SERVER_ERROR,
            502: status.HTTP_502_BAD_GATEWAY,
            503: status.HTTP_503_SERVICE_UNAVAILABLE,
            504: status.HTTP_504_GATEWAY_TIMEOUT,
        }
    
    def handle_django_response_error(
        self,
        status_code: int,
        response_data: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """
        Handle Django API response errors.
        
        Args:
            status_code: HTTP status code
            response_data: Django response data
            request_context: Additional request context
        
        Returns:
            HTTPException: FastAPI-compatible exception
        """
        try:
            # Extract error information
            error_message = self._extract_error_message(response_data)
            error_details = self._extract_error_details(response_data)
            
            # Map status code
            fastapi_status = self.status_code_mappings.get(
                status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            # Create error response
            error_response = {
                "error": error_message,
                "status_code": status_code,
                "details": error_details,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add request context if available
            if request_context:
                error_response["request_context"] = request_context
            
            # Add traceback in development
            if self.include_traceback:
                error_response["traceback"] = traceback.format_exc()
            
            logger.error(
                "Django API error",
                status_code=status_code,
                error_message=error_message,
                error_details=error_details,
                request_context=request_context
            )
            
            return HTTPException(
                status_code=fastapi_status,
                detail=error_response
            )
            
        except Exception as e:
            logger.error(
                "Error handling Django response error",
                original_status_code=status_code,
                original_response=response_data,
                handler_error=str(e)
            )
            
            # Fallback error response
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Internal server error",
                    "message": "Error processing Django response",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def handle_crud_error(self, error: CRUDError) -> HTTPException:
        """
        Handle CRUD operation errors.
        
        Args:
            error: CRUD error to handle
        
        Returns:
            HTTPException: FastAPI-compatible exception
        """
        error_response = {
            "error": error.message,
            "error_code": error.error_code,
            "details": error.details,
            "timestamp": error.timestamp.isoformat()
        }
        
        # Add entity information if available
        if error.entity_type:
            error_response["entity_type"] = error.entity_type
        if error.entity_id:
            error_response["entity_id"] = error.entity_id
        
        # Determine HTTP status code based on error type
        if isinstance(error, ValidationError):
            http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
            error_response["field_errors"] = error.field_errors
        elif isinstance(error, EntityNotFoundError):
            http_status = status.HTTP_404_NOT_FOUND
        elif isinstance(error, EntityAlreadyExistsError):
            http_status = status.HTTP_409_CONFLICT
            error_response["conflicting_fields"] = error.conflicting_fields
        elif isinstance(error, OptimisticLockError):
            http_status = status.HTTP_409_CONFLICT
            error_response["expected_version"] = error.expected_version
            error_response["actual_version"] = error.actual_version
        elif isinstance(error, PermissionDeniedError):
            http_status = status.HTTP_403_FORBIDDEN
            error_response["operation"] = error.operation
            error_response["user_id"] = error.user_id
        elif isinstance(error, DatabaseConnectionError):
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        elif isinstance(error, DatabaseOperationError):
            http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_response["operation"] = error.operation
            error_response["sql_error"] = error.sql_error
        else:
            http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        logger.error(
            "CRUD operation error",
            error_type=type(error).__name__,
            error_code=error.error_code,
            error_message=error.message,
            entity_type=error.entity_type,
            entity_id=error.entity_id
        )
        
        return HTTPException(
            status_code=http_status,
            detail=error_response
        )
    
    def handle_generic_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """
        Handle generic errors.
        
        Args:
            error: Generic exception
            context: Additional context information
        
        Returns:
            HTTPException: FastAPI-compatible exception
        """
        error_response = {
            "error": "Internal server error",
            "message": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if context:
            error_response["context"] = context
        
        if self.include_traceback:
            error_response["traceback"] = traceback.format_exc()
        
        logger.error(
            "Generic error occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            traceback=traceback.format_exc()
        )
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response
        )
    
    def create_api_response_error(
        self,
        message: str,
        error_code: str = "API_ERROR",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> APIResponse:
        """
        Create standardized API error response.
        
        Args:
            message: Error message
            error_code: Error code
            details: Additional error details
            request_id: Request ID for tracing
        
        Returns:
            APIResponse: Standardized error response
        """
        return APIResponse(
            success=False,
            message=message,
            errors=[{
                "code": error_code,
                "message": message,
                "details": details or {}
            }],
            request_id=request_id
        )
    
    def _extract_error_message(self, response_data: Dict[str, Any]) -> str:
        """Extract error message from Django response"""
        # Try different Django error response formats
        if isinstance(response_data, dict):
            # DRF error format
            if "detail" in response_data:
                return str(response_data["detail"])
            
            # Form validation errors
            if "non_field_errors" in response_data:
                errors = response_data["non_field_errors"]
                if isinstance(errors, list) and errors:
                    return str(errors[0])
            
            # Field validation errors
            field_errors = []
            for field, errors in response_data.items():
                if isinstance(errors, list):
                    field_errors.extend([f"{field}: {error}" for error in errors])
                else:
                    field_errors.append(f"{field}: {errors}")
            
            if field_errors:
                return "; ".join(field_errors)
            
            # Generic message
            if "message" in response_data:
                return str(response_data["message"])
            
            # Fallback
            return "Django API error"
        
        return str(response_data)
    
    def _extract_error_details(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract error details from Django response"""
        details = {}
        
        if isinstance(response_data, dict):
            # Field validation errors
            field_errors = {}
            for field, errors in response_data.items():
                if field not in ["detail", "message", "non_field_errors"]:
                    if isinstance(errors, list):
                        field_errors[field] = errors
                    else:
                        field_errors[field] = [str(errors)]
            
            if field_errors:
                details["field_errors"] = field_errors
            
            # Non-field errors
            if "non_field_errors" in response_data:
                details["non_field_errors"] = response_data["non_field_errors"]
            
            # Additional details
            for key in ["code", "error_code", "type", "timestamp"]:
                if key in response_data:
                    details[key] = response_data[key]
        
        return details
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: str = "error"
    ) -> None:
        """
        Log error with structured logging.
        
        Args:
            error: Exception to log
            context: Additional context
            level: Log level
        """
        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if context:
            log_data.update(context)
        
        if self.include_traceback:
            log_data["traceback"] = traceback.format_exc()
        
        if level == "error":
            logger.error("Error occurred", **log_data)
        elif level == "warning":
            logger.warning("Warning occurred", **log_data)
        else:
            logger.info("Info logged", **log_data)
    
    def is_retryable_error(self, status_code: int) -> bool:
        """
        Determine if error is retryable.
        
        Args:
            status_code: HTTP status code
        
        Returns:
            bool: Whether error is retryable
        """
        # Retry on server errors and some client errors
        retryable_codes = {
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }
        
        return status_code in retryable_codes