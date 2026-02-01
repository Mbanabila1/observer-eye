"""
Django backend integration for Observer Eye Middleware.
Provides database connection, ORM integration, and API endpoints
for all Django apps with proper error propagation and handling.
"""

from .connection import DjangoConnectionManager
from .orm_adapter import DjangoORMAdapter
from .api_client import DjangoAPIClient
from .error_handler import DjangoErrorHandler
from .models import DjangoAppConfig, APIEndpoint, QueryResult

__all__ = [
    'DjangoConnectionManager',
    'DjangoORMAdapter', 
    'DjangoAPIClient',
    'DjangoErrorHandler',
    'DjangoAppConfig',
    'APIEndpoint',
    'QueryResult'
]