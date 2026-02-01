"""
CRUD operations module for Observer Eye Middleware.
Provides comprehensive Create, Read, Update, Delete operations with validation,
optimistic locking, audit trails, and Django backend integration.
"""

from .handlers import CRUDHandler
from .models import CRUDRequest, CRUDResponse, EntityFilter, PaginationParams
from .exceptions import CRUDError, ValidationError, OptimisticLockError
from .audit import AuditTrail

__all__ = [
    'CRUDHandler',
    'CRUDRequest',
    'CRUDResponse', 
    'EntityFilter',
    'PaginationParams',
    'CRUDError',
    'ValidationError',
    'OptimisticLockError',
    'AuditTrail'
]