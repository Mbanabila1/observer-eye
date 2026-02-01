"""
Custom exceptions for Observer Eye Middleware
"""


class ObserverEyeException(Exception):
    """Base exception for Observer Eye Middleware"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "OBSERVER_EYE_ERROR"
        self.details = details or {}


class ValidationError(ObserverEyeException):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value


class AuthenticationError(ObserverEyeException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(ObserverEyeException):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class ServiceUnavailableError(ObserverEyeException):
    """Raised when a service is unavailable"""
    
    def __init__(self, service_name: str, message: str = None):
        message = message or f"Service {service_name} is unavailable"
        super().__init__(message, "SERVICE_UNAVAILABLE")
        self.service_name = service_name


class CircuitBreakerOpenError(ObserverEyeException):
    """Raised when circuit breaker is open"""
    
    def __init__(self, service_name: str):
        message = f"Circuit breaker is open for service {service_name}"
        super().__init__(message, "CIRCUIT_BREAKER_OPEN")
        self.service_name = service_name


class DataProcessingError(ObserverEyeException):
    """Raised when data processing fails"""
    
    def __init__(self, message: str, stage: str = None):
        super().__init__(message, "DATA_PROCESSING_ERROR")
        self.stage = stage


class CacheError(ObserverEyeException):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(message, "CACHE_ERROR")
        self.operation = operation


class StreamingError(ObserverEyeException):
    """Raised when streaming operations fail"""
    
    def __init__(self, message: str, stream_id: str = None):
        super().__init__(message, "STREAMING_ERROR")
        self.stream_id = stream_id