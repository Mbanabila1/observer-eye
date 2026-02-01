"""
Error handling and resilience patterns for Observer Eye Middleware
"""

from .middleware import ErrorHandlingMiddleware
from .circuit_breaker import CircuitBreaker, CircuitState
from .exceptions import (
    ObserverEyeException,
    ValidationError,
    AuthenticationError,
    ServiceUnavailableError,
    CircuitBreakerOpenError
)

__all__ = [
    "ErrorHandlingMiddleware",
    "CircuitBreaker",
    "CircuitState",
    "ObserverEyeException",
    "ValidationError",
    "AuthenticationError",
    "ServiceUnavailableError",
    "CircuitBreakerOpenError"
]