"""
CRUD operation models and data structures.
Defines request/response models, filters, and pagination for CRUD operations.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class CRUDOperation(str, Enum):
    """CRUD operation types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


class SortOrder(str, Enum):
    """Sort order options"""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Filter operators for queries"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class EntityFilter(BaseModel):
    """Filter specification for entity queries"""
    field: str = Field(..., description="Field name to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Optional[Union[str, int, float, bool, List[Any]]] = Field(
        None, description="Filter value (not required for null checks)"
    )
    
    @validator('value')
    def validate_value_for_operator(cls, v, values):
        """Validate that value is appropriate for the operator"""
        operator = values.get('operator')
        
        if operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            if v is not None:
                raise ValueError(f"Value should be None for {operator} operator")
        elif operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            if not isinstance(v, list):
                raise ValueError(f"Value should be a list for {operator} operator")
        else:
            if v is None:
                raise ValueError(f"Value is required for {operator} operator")
        
        return v


class SortField(BaseModel):
    """Sort field specification"""
    field: str = Field(..., description="Field name to sort by")
    order: SortOrder = Field(SortOrder.ASC, description="Sort order")


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=1000, description="Number of items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size


class CRUDRequest(BaseModel):
    """Base CRUD request model"""
    operation: CRUDOperation = Field(..., description="CRUD operation type")
    entity_type: str = Field(..., description="Entity type (Django app.model)")
    entity_id: Optional[str] = Field(None, description="Entity ID for single operations")
    data: Optional[Dict[str, Any]] = Field(None, description="Entity data for create/update")
    filters: Optional[List[EntityFilter]] = Field(None, description="Filters for list/read operations")
    sort_fields: Optional[List[SortField]] = Field(None, description="Sort fields for list operations")
    pagination: Optional[PaginationParams] = Field(None, description="Pagination for list operations")
    include_inactive: bool = Field(False, description="Include soft-deleted entities")
    version: Optional[int] = Field(None, description="Entity version for optimistic locking")
    
    @validator('entity_type')
    def validate_entity_type(cls, v):
        """Validate entity type format"""
        if '.' not in v:
            raise ValueError("Entity type must be in format 'app.model'")
        return v.lower()
    
    @validator('entity_id')
    def validate_entity_id(cls, v):
        """Validate entity ID format"""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("Entity ID must be a valid UUID")
        return v


class ValidationError(BaseModel):
    """Validation error details"""
    field: str = Field(..., description="Field name with error")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    value: Optional[Any] = Field(None, description="Invalid value")


class CRUDResponse(BaseModel):
    """CRUD operation response model"""
    success: bool = Field(..., description="Operation success status")
    operation: CRUDOperation = Field(..., description="CRUD operation performed")
    entity_type: str = Field(..., description="Entity type")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        None, description="Response data"
    )
    total_count: Optional[int] = Field(None, description="Total count for list operations")
    page_info: Optional[Dict[str, Any]] = Field(None, description="Pagination info")
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EntityMetadata(BaseModel):
    """Entity metadata for CRUD operations"""
    app_name: str = Field(..., description="Django app name")
    model_name: str = Field(..., description="Django model name")
    primary_key_field: str = Field("id", description="Primary key field name")
    version_field: Optional[str] = Field("updated_at", description="Version field for optimistic locking")
    soft_delete_field: Optional[str] = Field("is_active", description="Soft delete field name")
    audit_fields: List[str] = Field(
        default_factory=lambda: ["created_at", "updated_at", "created_by", "updated_by"],
        description="Fields to track for auditing"
    )
    readonly_fields: List[str] = Field(
        default_factory=lambda: ["id", "created_at", "updated_at"],
        description="Read-only fields that cannot be updated"
    )
    required_fields: List[str] = Field(default_factory=list, description="Required fields for creation")
    searchable_fields: List[str] = Field(default_factory=list, description="Fields that can be searched")
    filterable_fields: List[str] = Field(default_factory=list, description="Fields that can be filtered")
    sortable_fields: List[str] = Field(default_factory=list, description="Fields that can be sorted")


class BulkOperation(BaseModel):
    """Bulk operation request"""
    operation: CRUDOperation = Field(..., description="Bulk operation type")
    entity_type: str = Field(..., description="Entity type")
    items: List[Dict[str, Any]] = Field(..., description="Items for bulk operation")
    batch_size: int = Field(100, ge=1, le=1000, description="Batch size for processing")
    continue_on_error: bool = Field(False, description="Continue processing on individual errors")


class BulkOperationResult(BaseModel):
    """Bulk operation result"""
    total_items: int = Field(..., description="Total items processed")
    successful_items: int = Field(..., description="Successfully processed items")
    failed_items: int = Field(..., description="Failed items")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    processing_time_ms: float = Field(..., description="Total processing time")
    batch_results: List[CRUDResponse] = Field(default_factory=list, description="Individual batch results")


class AuditLogEntry(BaseModel):
    """Audit log entry for CRUD operations"""
    operation: CRUDOperation = Field(..., description="CRUD operation")
    entity_type: str = Field(..., description="Entity type")
    entity_id: str = Field(..., description="Entity ID")
    user_id: Optional[str] = Field(None, description="User performing the operation")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    changes: Dict[str, Any] = Field(default_factory=dict, description="Changes made")
    old_values: Dict[str, Any] = Field(default_factory=dict, description="Previous values")
    new_values: Dict[str, Any] = Field(default_factory=dict, description="New values")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Operation timestamp")
    success: bool = Field(..., description="Operation success status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CacheKey(BaseModel):
    """Cache key specification for CRUD operations"""
    entity_type: str = Field(..., description="Entity type")
    operation: CRUDOperation = Field(..., description="Operation type")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    filters_hash: Optional[str] = Field(None, description="Hash of filters")
    user_id: Optional[str] = Field(None, description="User ID for user-specific caching")
    
    def generate_key(self) -> str:
        """Generate cache key string"""
        parts = [f"crud:{self.entity_type}:{self.operation.value}"]
        
        if self.entity_id:
            parts.append(f"id:{self.entity_id}")
        
        if self.filters_hash:
            parts.append(f"filters:{self.filters_hash}")
        
        if self.user_id:
            parts.append(f"user:{self.user_id}")
        
        return ":".join(parts)


class DatabaseConnection(BaseModel):
    """Database connection configuration"""
    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    engine: str = Field("postgresql", description="Database engine")
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Maximum pool overflow")
    pool_timeout: int = Field(30, description="Pool timeout in seconds")
    
    class Config:
        # Don't include password in string representation
        fields = {"password": {"write_only": True}}