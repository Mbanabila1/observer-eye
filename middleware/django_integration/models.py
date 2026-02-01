"""
Django integration models and data structures.
Defines configuration, endpoints, and result models for Django backend integration.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class DatabaseEngine(str, Enum):
    """Supported database engines"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class HTTPMethod(str, Enum):
    """HTTP methods for API endpoints"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class QueryType(str, Enum):
    """Types of database queries"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    AGGREGATE = "aggregate"
    RAW = "raw"


class ConnectionStatus(str, Enum):
    """Database connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


class DjangoAppConfig(BaseModel):
    """Configuration for Django app integration"""
    app_name: str = Field(..., description="Django app name")
    app_label: str = Field(..., description="Django app label")
    models: List[str] = Field(default_factory=list, description="Model names in the app")
    api_prefix: str = Field("/api", description="API prefix for endpoints")
    enable_crud: bool = Field(True, description="Enable CRUD operations")
    enable_bulk_operations: bool = Field(True, description="Enable bulk operations")
    enable_filtering: bool = Field(True, description="Enable filtering")
    enable_pagination: bool = Field(True, description="Enable pagination")
    max_page_size: int = Field(1000, description="Maximum page size")
    
    # Permissions and security
    require_authentication: bool = Field(True, description="Require authentication")
    allowed_operations: List[str] = Field(
        default_factory=lambda: ["create", "read", "update", "delete"],
        description="Allowed CRUD operations"
    )
    
    # Caching configuration
    enable_caching: bool = Field(True, description="Enable response caching")
    cache_ttl_seconds: int = Field(300, description="Cache TTL in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "app_name": "analytics",
                "app_label": "analytics",
                "models": ["AnalyticsData", "DataSource", "AnalyticsQuery"],
                "api_prefix": "/api",
                "enable_crud": True,
                "require_authentication": True,
                "allowed_operations": ["create", "read", "update", "delete"]
            }
        }


class APIEndpoint(BaseModel):
    """API endpoint configuration"""
    path: str = Field(..., description="Endpoint path")
    method: HTTPMethod = Field(..., description="HTTP method")
    app_name: str = Field(..., description="Django app name")
    model_name: Optional[str] = Field(None, description="Model name (for model-based endpoints)")
    view_name: str = Field(..., description="Django view name")
    
    # Request/Response configuration
    requires_body: bool = Field(False, description="Whether endpoint requires request body")
    supports_pagination: bool = Field(False, description="Whether endpoint supports pagination")
    supports_filtering: bool = Field(False, description="Whether endpoint supports filtering")
    supports_ordering: bool = Field(False, description="Whether endpoint supports ordering")
    
    # Authentication and permissions
    requires_auth: bool = Field(True, description="Whether endpoint requires authentication")
    required_permissions: List[str] = Field(default_factory=list, description="Required permissions")
    
    # Caching
    cacheable: bool = Field(False, description="Whether response can be cached")
    cache_ttl: int = Field(300, description="Cache TTL in seconds")
    
    # Rate limiting
    rate_limit: Optional[int] = Field(None, description="Rate limit per minute")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "/api/analytics/data/",
                "method": "GET",
                "app_name": "analytics",
                "model_name": "AnalyticsData",
                "view_name": "AnalyticsDataListView",
                "supports_pagination": True,
                "supports_filtering": True,
                "requires_auth": True
            }
        }


class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    engine: DatabaseEngine = Field(..., description="Database engine")
    name: str = Field(..., description="Database name")
    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port")
    user: str = Field(..., description="Database user")
    password: str = Field(..., description="Database password")
    
    # Connection pool settings
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Maximum pool overflow")
    pool_timeout: int = Field(30, description="Pool timeout in seconds")
    pool_recycle: int = Field(3600, description="Pool recycle time in seconds")
    
    # SSL settings
    use_ssl: bool = Field(False, description="Use SSL connection")
    ssl_cert_path: Optional[str] = Field(None, description="SSL certificate path")
    ssl_key_path: Optional[str] = Field(None, description="SSL key path")
    ssl_ca_path: Optional[str] = Field(None, description="SSL CA path")
    
    # Additional options
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional connection options")
    
    @validator('port')
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    class Config:
        # Don't include password in string representation
        fields = {"password": {"write_only": True}}


class QueryFilter(BaseModel):
    """Database query filter"""
    field: str = Field(..., description="Field name to filter on")
    operator: str = Field("exact", description="Filter operator")
    value: Any = Field(..., description="Filter value")
    lookup_type: str = Field("exact", description="Django lookup type")
    
    class Config:
        schema_extra = {
            "example": {
                "field": "created_at",
                "operator": "gte",
                "value": "2024-01-01T00:00:00Z",
                "lookup_type": "gte"
            }
        }


class QueryOrder(BaseModel):
    """Database query ordering"""
    field: str = Field(..., description="Field name to order by")
    direction: str = Field("asc", description="Order direction (asc/desc)")
    
    @validator('direction')
    def validate_direction(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("Direction must be 'asc' or 'desc'")
        return v.lower()


class QueryParams(BaseModel):
    """Database query parameters"""
    filters: List[QueryFilter] = Field(default_factory=list, description="Query filters")
    ordering: List[QueryOrder] = Field(default_factory=list, description="Query ordering")
    limit: Optional[int] = Field(None, description="Query limit")
    offset: Optional[int] = Field(None, description="Query offset")
    select_related: List[str] = Field(default_factory=list, description="Fields to select_related")
    prefetch_related: List[str] = Field(default_factory=list, description="Fields to prefetch_related")
    distinct: bool = Field(False, description="Use DISTINCT")
    
    @validator('limit')
    def validate_limit(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Limit must be positive")
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        if v is not None and v < 0:
            raise ValueError("Offset must be non-negative")
        return v


class QueryResult(BaseModel):
    """Database query result"""
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Query ID")
    query_type: QueryType = Field(..., description="Type of query executed")
    success: bool = Field(..., description="Whether query was successful")
    
    # Result data
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        None, description="Query result data"
    )
    count: Optional[int] = Field(None, description="Total count (for paginated queries)")
    affected_rows: Optional[int] = Field(None, description="Number of affected rows")
    
    # Query metadata
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if query failed")
    error_code: Optional[str] = Field(None, description="Error code")
    
    # Timestamps
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="Query execution timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BulkOperationResult(BaseModel):
    """Result of bulk database operation"""
    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Operation ID")
    operation_type: str = Field(..., description="Type of bulk operation")
    total_items: int = Field(..., description="Total items processed")
    successful_items: int = Field(..., description="Successfully processed items")
    failed_items: int = Field(..., description="Failed items")
    
    # Detailed results
    success_ids: List[str] = Field(default_factory=list, description="IDs of successful items")
    failed_items_details: List[Dict[str, Any]] = Field(
        default_factory=list, description="Details of failed items"
    )
    
    # Performance metrics
    execution_time_ms: float = Field(..., description="Total execution time")
    average_time_per_item_ms: float = Field(..., description="Average time per item")
    
    # Timestamps
    started_at: datetime = Field(..., description="Operation start time")
    completed_at: datetime = Field(..., description="Operation completion time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConnectionInfo(BaseModel):
    """Database connection information"""
    connection_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Connection ID")
    status: ConnectionStatus = Field(..., description="Connection status")
    database_name: str = Field(..., description="Database name")
    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port")
    
    # Connection metrics
    active_connections: int = Field(0, description="Number of active connections")
    idle_connections: int = Field(0, description="Number of idle connections")
    total_connections: int = Field(0, description="Total connections in pool")
    
    # Performance metrics
    avg_query_time_ms: float = Field(0.0, description="Average query time")
    total_queries: int = Field(0, description="Total queries executed")
    failed_queries: int = Field(0, description="Number of failed queries")
    
    # Timestamps
    connected_at: Optional[datetime] = Field(None, description="Connection established time")
    last_activity: Optional[datetime] = Field(None, description="Last activity time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class APIResponse(BaseModel):
    """Standardized API response"""
    success: bool = Field(..., description="Response success status")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    
    # Pagination (for list responses)
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination information")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheck(BaseModel):
    """Health check result"""
    status: str = Field(..., description="Overall health status")
    checks: Dict[str, Dict[str, Any]] = Field(..., description="Individual health checks")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "status": "healthy",
                "checks": {
                    "database": {
                        "status": "healthy",
                        "response_time_ms": 5.2,
                        "details": "Connection successful"
                    },
                    "django_api": {
                        "status": "healthy",
                        "response_time_ms": 12.8,
                        "details": "API responding normally"
                    }
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }