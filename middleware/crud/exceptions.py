"""
CRUD operation exceptions.
Custom exceptions for CRUD operations with detailed error information.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


class CRUDError(Exception):
    """Base exception for CRUD operations"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "CRUD_ERROR",
        details: Optional[Dict[str, Any]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat()
        }


class ValidationError(CRUDError):
    """Validation error for CRUD operations"""
    
    def __init__(
        self,
        message: str,
        field_errors: Optional[List[Dict[str, Any]]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors or []},
            entity_type=entity_type,
            entity_id=entity_id
        )
        self.field_errors = field_errors or []


class EntityNotFoundError(CRUDError):
    """Entity not found error"""
    
    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        message: Optional[str] = None
    ):
        message = message or f"{entity_type} with ID {entity_id} not found"
        super().__init__(
            message=message,
            error_code="ENTITY_NOT_FOUND",
            entity_type=entity_type,
            entity_id=entity_id
        )


class EntityAlreadyExistsError(CRUDError):
    """Entity already exists error"""
    
    def __init__(
        self,
        entity_type: str,
        conflicting_fields: Dict[str, Any],
        message: Optional[str] = None
    ):
        message = message or f"{entity_type} already exists with the given values"
        super().__init__(
            message=message,
            error_code="ENTITY_ALREADY_EXISTS",
            details={"conflicting_fields": conflicting_fields},
            entity_type=entity_type
        )
        self.conflicting_fields = conflicting_fields


class OptimisticLockError(CRUDError):
    """Optimistic locking error"""
    
    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        expected_version: Any,
        actual_version: Any,
        message: Optional[str] = None
    ):
        message = message or (
            f"Optimistic lock failed for {entity_type} {entity_id}. "
            f"Expected version {expected_version}, but found {actual_version}"
        )
        super().__init__(
            message=message,
            error_code="OPTIMISTIC_LOCK_ERROR",
            details={
                "expected_version": expected_version,
                "actual_version": actual_version
            },
            entity_type=entity_type,
            entity_id=entity_id
        )
        self.expected_version = expected_version
        self.actual_version = actual_version


class PermissionDeniedError(CRUDError):
    """Permission denied error"""
    
    def __init__(
        self,
        entity_type: str,
        operation: str,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        message: Optional[str] = None
    ):
        message = message or f"Permission denied for {operation} operation on {entity_type}"
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            details={
                "operation": operation,
                "user_id": user_id
            },
            entity_type=entity_type,
            entity_id=entity_id
        )
        self.operation = operation
        self.user_id = user_id


class DatabaseConnectionError(CRUDError):
    """Database connection error"""
    
    def __init__(
        self,
        message: str,
        connection_details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR",
            details=connection_details or {}
        )


class DatabaseOperationError(CRUDError):
    """Database operation error"""
    
    def __init__(
        self,
        message: str,
        operation: str,
        sql_error: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_OPERATION_ERROR",
            details={
                "operation": operation,
                "sql_error": sql_error
            },
            entity_type=entity_type,
            entity_id=entity_id
        )
        self.operation = operation
        self.sql_error = sql_error


class BulkOperationError(CRUDError):
    """Bulk operation error"""
    
    def __init__(
        self,
        message: str,
        failed_items: List[Dict[str, Any]],
        successful_items: int = 0,
        total_items: int = 0
    ):
        super().__init__(
            message=message,
            error_code="BULK_OPERATION_ERROR",
            details={
                "failed_items": failed_items,
                "successful_items": successful_items,
                "total_items": total_items
            }
        )
        self.failed_items = failed_items
        self.successful_items = successful_items
        self.total_items = total_items


class CacheError(CRUDError):
    """Cache operation error"""
    
    def __init__(
        self,
        message: str,
        cache_operation: str,
        cache_key: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details={
                "cache_operation": cache_operation,
                "cache_key": cache_key
            }
        )
        self.cache_operation = cache_operation
        self.cache_key = cache_key


class SerializationError(CRUDError):
    """Data serialization error"""
    
    def __init__(
        self,
        message: str,
        data: Optional[Any] = None,
        serialization_type: str = "json"
    ):
        super().__init__(
            message=message,
            error_code="SERIALIZATION_ERROR",
            details={
                "serialization_type": serialization_type,
                "data_type": type(data).__name__ if data is not None else None
            }
        )
        self.serialization_type = serialization_type


class ConfigurationError(CRUDError):
    """Configuration error"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={
                "config_key": config_key,
                "config_value": config_value
            }
        )
        self.config_key = config_key
        self.config_value = config_value


class RateLimitError(CRUDError):
    """Rate limit exceeded error"""
    
    def __init__(
        self,
        message: str,
        limit: int,
        window_seconds: int,
        retry_after_seconds: Optional[int] = None
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={
                "limit": limit,
                "window_seconds": window_seconds,
                "retry_after_seconds": retry_after_seconds
            }
        )
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after_seconds = retry_after_seconds


class TransactionError(CRUDError):
    """Database transaction error"""
    
    def __init__(
        self,
        message: str,
        transaction_id: Optional[str] = None,
        rollback_successful: bool = False
    ):
        super().__init__(
            message=message,
            error_code="TRANSACTION_ERROR",
            details={
                "transaction_id": transaction_id,
                "rollback_successful": rollback_successful
            }
        )
        self.transaction_id = transaction_id
        self.rollback_successful = rollback_successful


class NetworkError(CRUDError):
    """Network communication error"""
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details={
                "url": url,
                "status_code": status_code,
                "response_body": response_body
            }
        )
        self.url = url
        self.status_code = status_code
        self.response_body = response_body