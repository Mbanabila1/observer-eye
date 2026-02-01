"""
CRUD operation handlers for Observer Eye Middleware.
Provides comprehensive Create, Read, Update, Delete operations with validation,
optimistic locking, audit trails, and Django backend integration.
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone
import uuid

import httpx
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .models import (
    CRUDRequest, CRUDResponse, CRUDOperation, EntityFilter, FilterOperator,
    PaginationParams, SortField, SortOrder, EntityMetadata, BulkOperation,
    BulkOperationResult, CacheKey, ValidationError as ValidationErrorModel
)
from .exceptions import (
    CRUDError, ValidationError, EntityNotFoundError, EntityAlreadyExistsError,
    OptimisticLockError, PermissionDeniedError, DatabaseConnectionError,
    DatabaseOperationError, BulkOperationError
)
from .audit import AuditTrail
from caching.cache_manager import CacheManager

logger = structlog.get_logger(__name__)


class CRUDHandler:
    """
    Main CRUD handler for Observer Eye Platform.
    Integrates with Django backend and provides comprehensive CRUD operations.
    """
    
    def __init__(
        self,
        django_base_url: str = "http://localhost:8000",
        cache_manager: Optional[CacheManager] = None,
        enable_audit: bool = True,
        enable_caching: bool = True,
        default_page_size: int = 20,
        max_page_size: int = 1000
    ):
        self.django_base_url = django_base_url.rstrip('/')
        self.cache_manager = cache_manager
        self.enable_audit = enable_audit
        self.enable_caching = enable_caching
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
        
        # Initialize audit trail
        self.audit_trail = AuditTrail(enable_detailed_logging=True) if enable_audit else None
        
        # HTTP client for Django backend communication
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # Entity metadata cache
        self._entity_metadata_cache: Dict[str, EntityMetadata] = {}
        
        logger.info(
            "CRUD handler initialized",
            django_base_url=django_base_url,
            enable_audit=enable_audit,
            enable_caching=enable_caching
        )
    
    async def handle_request(
        self,
        request: CRUDRequest,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> CRUDResponse:
        """
        Handle a CRUD request.
        
        Args:
            request: CRUD request to handle
            user_id: ID of user making the request
            ip_address: IP address of the request
            user_agent: User agent string
        
        Returns:
            CRUDResponse: Response with operation results
        """
        start_time = time.time()
        
        try:
            # Validate request
            await self._validate_request(request, user_id)
            
            # Get entity metadata
            metadata = await self._get_entity_metadata(request.entity_type)
            
            # Route to appropriate handler
            if request.operation == CRUDOperation.CREATE:
                response = await self._handle_create(request, metadata, user_id, ip_address, user_agent)
            elif request.operation == CRUDOperation.READ:
                response = await self._handle_read(request, metadata, user_id)
            elif request.operation == CRUDOperation.UPDATE:
                response = await self._handle_update(request, metadata, user_id, ip_address, user_agent)
            elif request.operation == CRUDOperation.DELETE:
                response = await self._handle_delete(request, metadata, user_id, ip_address, user_agent)
            elif request.operation == CRUDOperation.LIST:
                response = await self._handle_list(request, metadata, user_id)
            else:
                raise CRUDError(f"Unsupported operation: {request.operation}")
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            response.processing_time_ms = processing_time
            
            logger.info(
                "CRUD request completed",
                operation=request.operation.value,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                success=response.success,
                processing_time_ms=processing_time
            )
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            
            logger.error(
                "CRUD request failed",
                operation=request.operation.value,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                error=str(e),
                processing_time_ms=processing_time
            )
            
            # Create error response
            if isinstance(e, CRUDError):
                return CRUDResponse(
                    success=False,
                    operation=request.operation,
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    errors=[ValidationErrorModel(
                        field="general",
                        message=e.message,
                        code=e.error_code,
                        value=None
                    )],
                    processing_time_ms=processing_time
                )
            else:
                return CRUDResponse(
                    success=False,
                    operation=request.operation,
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    errors=[ValidationErrorModel(
                        field="general",
                        message=str(e),
                        code="INTERNAL_ERROR",
                        value=None
                    )],
                    processing_time_ms=processing_time
                )
    
    async def _handle_create(
        self,
        request: CRUDRequest,
        metadata: EntityMetadata,
        user_id: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> CRUDResponse:
        """Handle CREATE operation"""
        if not request.data:
            raise ValidationError("Data is required for create operation")
        
        # Validate required fields
        await self._validate_required_fields(request.data, metadata)
        
        # Remove readonly fields
        create_data = {k: v for k, v in request.data.items() 
                      if k not in metadata.readonly_fields}
        
        # Add audit fields
        if user_id and 'created_by' in metadata.audit_fields:
            create_data['created_by'] = user_id
        
        try:
            # Call Django backend
            url = f"{self.django_base_url}/api/{metadata.app_name}/{metadata.model_name}/"
            response = await self.http_client.post(url, json=create_data)
            
            if response.status_code == 201:
                created_entity = response.json()
                entity_id = str(created_entity.get(metadata.primary_key_field))
                
                # Log audit trail
                if self.audit_trail:
                    await self.audit_trail.log_operation(
                        operation=CRUDOperation.CREATE,
                        entity_type=request.entity_type,
                        entity_id=entity_id,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        new_data=created_entity,
                        success=True
                    )
                
                # Invalidate related cache entries
                if self.enable_caching and self.cache_manager:
                    await self._invalidate_entity_cache(request.entity_type, entity_id)
                
                return CRUDResponse(
                    success=True,
                    operation=CRUDOperation.CREATE,
                    entity_type=request.entity_type,
                    entity_id=entity_id,
                    data=created_entity
                )
            
            elif response.status_code == 400:
                # Validation errors from Django
                error_data = response.json()
                errors = self._parse_django_errors(error_data)
                
                return CRUDResponse(
                    success=False,
                    operation=CRUDOperation.CREATE,
                    entity_type=request.entity_type,
                    errors=errors
                )
            
            elif response.status_code == 409:
                # Conflict - entity already exists
                raise EntityAlreadyExistsError(
                    entity_type=request.entity_type,
                    conflicting_fields=create_data
                )
            
            else:
                raise DatabaseOperationError(
                    message=f"Create operation failed with status {response.status_code}",
                    operation="create",
                    entity_type=request.entity_type
                )
                
        except httpx.RequestError as e:
            raise DatabaseConnectionError(f"Failed to connect to Django backend: {str(e)}")
    
    async def _handle_read(
        self,
        request: CRUDRequest,
        metadata: EntityMetadata,
        user_id: Optional[str]
    ) -> CRUDResponse:
        """Handle READ operation"""
        if not request.entity_id:
            raise ValidationError("Entity ID is required for read operation")
        
        # Check cache first
        if self.enable_caching and self.cache_manager:
            cache_key = CacheKey(
                entity_type=request.entity_type,
                operation=CRUDOperation.READ,
                entity_id=request.entity_id,
                user_id=user_id
            ).generate_key()
            
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                return CRUDResponse(
                    success=True,
                    operation=CRUDOperation.READ,
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    data=cached_data,
                    metadata={"from_cache": True}
                )
        
        try:
            # Call Django backend
            url = f"{self.django_base_url}/api/{metadata.app_name}/{metadata.model_name}/{request.entity_id}/"
            
            params = {}
            if request.include_inactive:
                params['include_inactive'] = 'true'
            
            response = await self.http_client.get(url, params=params)
            
            if response.status_code == 200:
                entity_data = response.json()
                
                # Cache the result
                if self.enable_caching and self.cache_manager:
                    await self.cache_manager.set(cache_key, entity_data, ttl=300)  # 5 minutes
                
                return CRUDResponse(
                    success=True,
                    operation=CRUDOperation.READ,
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    data=entity_data
                )
            
            elif response.status_code == 404:
                raise EntityNotFoundError(
                    entity_type=request.entity_type,
                    entity_id=request.entity_id
                )
            
            else:
                raise DatabaseOperationError(
                    message=f"Read operation failed with status {response.status_code}",
                    operation="read",
                    entity_type=request.entity_type,
                    entity_id=request.entity_id
                )
                
        except httpx.RequestError as e:
            raise DatabaseConnectionError(f"Failed to connect to Django backend: {str(e)}")
    
    async def _handle_update(
        self,
        request: CRUDRequest,
        metadata: EntityMetadata,
        user_id: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> CRUDResponse:
        """Handle UPDATE operation"""
        if not request.entity_id:
            raise ValidationError("Entity ID is required for update operation")
        
        if not request.data:
            raise ValidationError("Data is required for update operation")
        
        # Get current entity for optimistic locking and audit
        current_entity = await self._get_current_entity(request.entity_type, request.entity_id, metadata)
        
        # Check optimistic locking
        if request.version is not None and metadata.version_field:
            current_version = current_entity.get(metadata.version_field)
            if current_version != request.version:
                raise OptimisticLockError(
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    expected_version=request.version,
                    actual_version=current_version
                )
        
        # Remove readonly fields
        update_data = {k: v for k, v in request.data.items() 
                      if k not in metadata.readonly_fields}
        
        # Add audit fields
        if user_id and 'updated_by' in metadata.audit_fields:
            update_data['updated_by'] = user_id
        
        try:
            # Call Django backend
            url = f"{self.django_base_url}/api/{metadata.app_name}/{metadata.model_name}/{request.entity_id}/"
            response = await self.http_client.patch(url, json=update_data)
            
            if response.status_code == 200:
                updated_entity = response.json()
                
                # Log audit trail
                if self.audit_trail:
                    await self.audit_trail.log_operation(
                        operation=CRUDOperation.UPDATE,
                        entity_type=request.entity_type,
                        entity_id=request.entity_id,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        old_data=current_entity,
                        new_data=updated_entity,
                        success=True
                    )
                
                # Invalidate cache
                if self.enable_caching and self.cache_manager:
                    await self._invalidate_entity_cache(request.entity_type, request.entity_id)
                
                return CRUDResponse(
                    success=True,
                    operation=CRUDOperation.UPDATE,
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    data=updated_entity
                )
            
            elif response.status_code == 400:
                error_data = response.json()
                errors = self._parse_django_errors(error_data)
                
                return CRUDResponse(
                    success=False,
                    operation=CRUDOperation.UPDATE,
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    errors=errors
                )
            
            elif response.status_code == 404:
                raise EntityNotFoundError(
                    entity_type=request.entity_type,
                    entity_id=request.entity_id
                )
            
            elif response.status_code == 409:
                # Optimistic lock conflict
                raise OptimisticLockError(
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    expected_version=request.version,
                    actual_version="unknown"
                )
            
            else:
                raise DatabaseOperationError(
                    message=f"Update operation failed with status {response.status_code}",
                    operation="update",
                    entity_type=request.entity_type,
                    entity_id=request.entity_id
                )
                
        except httpx.RequestError as e:
            raise DatabaseConnectionError(f"Failed to connect to Django backend: {str(e)}")
    
    async def _handle_delete(
        self,
        request: CRUDRequest,
        metadata: EntityMetadata,
        user_id: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> CRUDResponse:
        """Handle DELETE operation"""
        if not request.entity_id:
            raise ValidationError("Entity ID is required for delete operation")
        
        # Get current entity for audit
        current_entity = await self._get_current_entity(request.entity_type, request.entity_id, metadata)
        
        try:
            # Call Django backend
            url = f"{self.django_base_url}/api/{metadata.app_name}/{metadata.model_name}/{request.entity_id}/"
            response = await self.http_client.delete(url)
            
            if response.status_code == 204:
                # Log audit trail
                if self.audit_trail:
                    await self.audit_trail.log_operation(
                        operation=CRUDOperation.DELETE,
                        entity_type=request.entity_type,
                        entity_id=request.entity_id,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        old_data=current_entity,
                        success=True
                    )
                
                # Invalidate cache
                if self.enable_caching and self.cache_manager:
                    await self._invalidate_entity_cache(request.entity_type, request.entity_id)
                
                return CRUDResponse(
                    success=True,
                    operation=CRUDOperation.DELETE,
                    entity_type=request.entity_type,
                    entity_id=request.entity_id
                )
            
            elif response.status_code == 404:
                raise EntityNotFoundError(
                    entity_type=request.entity_type,
                    entity_id=request.entity_id
                )
            
            else:
                raise DatabaseOperationError(
                    message=f"Delete operation failed with status {response.status_code}",
                    operation="delete",
                    entity_type=request.entity_type,
                    entity_id=request.entity_id
                )
                
        except httpx.RequestError as e:
            raise DatabaseConnectionError(f"Failed to connect to Django backend: {str(e)}")
    
    async def _handle_list(
        self,
        request: CRUDRequest,
        metadata: EntityMetadata,
        user_id: Optional[str]
    ) -> CRUDResponse:
        """Handle LIST operation"""
        # Set default pagination
        pagination = request.pagination or PaginationParams()
        if pagination.page_size > self.max_page_size:
            pagination.page_size = self.max_page_size
        
        # Check cache for list operations
        cache_key = None
        if self.enable_caching and self.cache_manager:
            filters_hash = self._hash_filters(request.filters or [])
            cache_key = CacheKey(
                entity_type=request.entity_type,
                operation=CRUDOperation.LIST,
                filters_hash=filters_hash,
                user_id=user_id
            ).generate_key()
            
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                return CRUDResponse(
                    success=True,
                    operation=CRUDOperation.LIST,
                    entity_type=request.entity_type,
                    data=cached_data.get("items", []),
                    total_count=cached_data.get("total_count", 0),
                    page_info=cached_data.get("page_info", {}),
                    metadata={"from_cache": True}
                )
        
        try:
            # Build query parameters
            params = {
                'page': pagination.page,
                'page_size': pagination.page_size
            }
            
            if request.include_inactive:
                params['include_inactive'] = 'true'
            
            # Add filters
            if request.filters:
                for i, filter_item in enumerate(request.filters):
                    params[f'filter_{i}_field'] = filter_item.field
                    params[f'filter_{i}_operator'] = filter_item.operator.value
                    if filter_item.value is not None:
                        params[f'filter_{i}_value'] = filter_item.value
            
            # Add sorting
            if request.sort_fields:
                sort_params = []
                for sort_field in request.sort_fields:
                    prefix = '-' if sort_field.order == SortOrder.DESC else ''
                    sort_params.append(f"{prefix}{sort_field.field}")
                params['ordering'] = ','.join(sort_params)
            
            # Call Django backend
            url = f"{self.django_base_url}/api/{metadata.app_name}/{metadata.model_name}/"
            response = await self.http_client.get(url, params=params)
            
            if response.status_code == 200:
                response_data = response.json()
                
                items = response_data.get('results', [])
                total_count = response_data.get('count', len(items))
                
                # Calculate page info
                total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
                page_info = {
                    'current_page': pagination.page,
                    'page_size': pagination.page_size,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'has_next': pagination.page < total_pages,
                    'has_previous': pagination.page > 1
                }
                
                # Cache the result
                if self.enable_caching and self.cache_manager and cache_key:
                    cache_data = {
                        'items': items,
                        'total_count': total_count,
                        'page_info': page_info
                    }
                    await self.cache_manager.set(cache_key, cache_data, ttl=60)  # 1 minute
                
                return CRUDResponse(
                    success=True,
                    operation=CRUDOperation.LIST,
                    entity_type=request.entity_type,
                    data=items,
                    total_count=total_count,
                    page_info=page_info
                )
            
            else:
                raise DatabaseOperationError(
                    message=f"List operation failed with status {response.status_code}",
                    operation="list",
                    entity_type=request.entity_type
                )
                
        except httpx.RequestError as e:
            raise DatabaseConnectionError(f"Failed to connect to Django backend: {str(e)}")
    
    async def _validate_request(self, request: CRUDRequest, user_id: Optional[str]) -> None:
        """Validate CRUD request"""
        # Basic validation is handled by Pydantic models
        # Add custom business logic validation here
        
        # Check permissions (placeholder - implement actual permission checking)
        if not user_id and request.operation in [CRUDOperation.CREATE, CRUDOperation.UPDATE, CRUDOperation.DELETE]:
            raise PermissionDeniedError(
                entity_type=request.entity_type,
                operation=request.operation.value,
                message="Authentication required for write operations"
            )
    
    async def _get_entity_metadata(self, entity_type: str) -> EntityMetadata:
        """Get entity metadata from cache or Django backend"""
        if entity_type in self._entity_metadata_cache:
            return self._entity_metadata_cache[entity_type]
        
        # Parse entity type
        app_name, model_name = entity_type.split('.')
        
        # Create default metadata (in real implementation, fetch from Django)
        metadata = EntityMetadata(
            app_name=app_name,
            model_name=model_name,
            primary_key_field="id",
            version_field="updated_at",
            soft_delete_field="is_active",
            audit_fields=["created_at", "updated_at", "created_by", "updated_by"],
            readonly_fields=["id", "created_at", "updated_at"],
            required_fields=[],
            searchable_fields=[],
            filterable_fields=[],
            sortable_fields=[]
        )
        
        # Cache metadata
        self._entity_metadata_cache[entity_type] = metadata
        
        return metadata
    
    async def _get_current_entity(
        self,
        entity_type: str,
        entity_id: str,
        metadata: EntityMetadata
    ) -> Dict[str, Any]:
        """Get current entity data"""
        try:
            url = f"{self.django_base_url}/api/{metadata.app_name}/{metadata.model_name}/{entity_id}/"
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise EntityNotFoundError(entity_type=entity_type, entity_id=entity_id)
            else:
                raise DatabaseOperationError(
                    message=f"Failed to get current entity: {response.status_code}",
                    operation="read",
                    entity_type=entity_type,
                    entity_id=entity_id
                )
        except httpx.RequestError as e:
            raise DatabaseConnectionError(f"Failed to connect to Django backend: {str(e)}")
    
    async def _validate_required_fields(
        self,
        data: Dict[str, Any],
        metadata: EntityMetadata
    ) -> None:
        """Validate required fields"""
        missing_fields = []
        for field in metadata.required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                message=f"Missing required fields: {', '.join(missing_fields)}",
                field_errors=[
                    {"field": field, "message": "This field is required", "code": "required"}
                    for field in missing_fields
                ]
            )
    
    def _parse_django_errors(self, error_data: Dict[str, Any]) -> List[ValidationErrorModel]:
        """Parse Django validation errors"""
        errors = []
        
        if isinstance(error_data, dict):
            for field, messages in error_data.items():
                if isinstance(messages, list):
                    for message in messages:
                        errors.append(ValidationErrorModel(
                            field=field,
                            message=str(message),
                            code="validation_error",
                            value=None
                        ))
                else:
                    errors.append(ValidationErrorModel(
                        field=field,
                        message=str(messages),
                        code="validation_error",
                        value=None
                    ))
        else:
            errors.append(ValidationErrorModel(
                field="general",
                message=str(error_data),
                code="validation_error",
                value=None
            ))
        
        return errors
    
    def _hash_filters(self, filters: List[EntityFilter]) -> str:
        """Generate hash for filters"""
        filter_data = []
        for f in filters:
            filter_data.append({
                'field': f.field,
                'operator': f.operator.value,
                'value': f.value
            })
        
        filter_json = json.dumps(filter_data, sort_keys=True)
        return hashlib.md5(filter_json.encode()).hexdigest()
    
    async def _invalidate_entity_cache(self, entity_type: str, entity_id: str) -> None:
        """Invalidate cache entries for an entity"""
        if not self.cache_manager:
            return
        
        # Invalidate specific entity cache
        patterns = [
            f"crud:{entity_type}:read:id:{entity_id}*",
            f"crud:{entity_type}:list:*",
        ]
        
        for pattern in patterns:
            try:
                await self.cache_manager.delete_pattern(pattern)
            except Exception as e:
                logger.warning(f"Failed to invalidate cache pattern {pattern}: {e}")
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources"""
        await self.http_client.aclose()
        logger.info("CRUD handler closed")