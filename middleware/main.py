import os
import logging
import json
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import uvicorn
import structlog
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from performance.monitor import PerformanceMonitor
from error_handling.middleware import ErrorHandlingMiddleware
from error_handling.circuit_breaker import CircuitBreaker
from data_processing.pipeline import DataProcessingPipeline, PipelineConfig, ProcessingMode
from data_processing.validation import ValidationMiddleware
from caching.cache_manager import CacheManager, CacheConfig, CacheBackend
from caching.cache_middleware import CacheMiddleware
from caching.invalidation import CacheInvalidationStrategy

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global instances
performance_monitor = PerformanceMonitor()
circuit_breaker = CircuitBreaker()
security = HTTPBearer(auto_error=False)

# Import CRUD and telemetry components
from crud.handlers import CRUDHandler
from telemetry.collector import TelemetryCollector
from telemetry.processor import TelemetryProcessor
from telemetry.enricher import TelemetryEnricher
from telemetry.correlator import TelemetryCorrelator
from telemetry.analyzer import TelemetryAnalyzer
from django_integration.api_client import DjangoAPIClient
from django_integration.models import DjangoAppConfig

# Initialize cache manager first
cache_config = CacheConfig(
    backend=CacheBackend.REDIS,
    default_ttl=3600,  # 1 hour
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    enable_compression=True,
    enable_metrics=True
)
cache_manager = CacheManager(cache_config)

# Initialize CRUD handler
crud_handler = CRUDHandler(
    django_base_url=os.getenv("DJANGO_URL", "http://localhost:8000"),
    cache_manager=cache_manager,
    enable_audit=True,
    enable_caching=True
)

# Initialize telemetry components
telemetry_collector = TelemetryCollector(
    cache_manager=cache_manager,
    max_batch_size=1000,
    rate_limit_per_second=10000
)

telemetry_processor = TelemetryProcessor(
    processor_version="1.0.0",
    enable_enrichment=True
)

telemetry_enricher = TelemetryEnricher(
    django_base_url=os.getenv("DJANGO_URL", "http://localhost:8000"),
    enable_service_lookup=True
)

telemetry_correlator = TelemetryCorrelator(
    max_correlation_window_seconds=3600,
    enable_automatic_rules=True
)

telemetry_analyzer = TelemetryAnalyzer(
    max_analysis_window_seconds=3600,
    enable_anomaly_detection=True,
    enable_trend_analysis=True
)

# Initialize Django API client
django_client = DjangoAPIClient(
    base_url=os.getenv("DJANGO_URL", "http://localhost:8000"),
    timeout_seconds=30.0,
    max_retries=3
)

# Initialize data processing pipeline
pipeline_config = PipelineConfig(
    mode=ProcessingMode.PERMISSIVE,
    enable_logging=True,
    enable_metrics=True,
    batch_size=1000
)
data_pipeline = DataProcessingPipeline(pipeline_config)

# Initialize cache invalidation strategy
cache_invalidation = CacheInvalidationStrategy(cache_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Observer Eye Middleware")
    
    # Initialize performance monitoring
    await performance_monitor.initialize()
    
    # Initialize circuit breaker
    circuit_breaker.initialize()
    
    # Configure data pipeline for different data types
    data_pipeline.configure_for_telemetry()
    
    # Create default cache invalidation rules
    cache_invalidation.create_default_rules()
    
    # Start background cache cleanup
    await cache_invalidation.start_background_cleanup(interval_seconds=300)
    
    # Start telemetry collector
    await telemetry_collector.start()
    
    # Initialize data ingestion service
    from data_ingestion import get_ingestion_service
    await get_ingestion_service()  # This will start the service
    
    # Register Django apps with API client
    await _register_django_apps()
    
    yield
    
    # Cleanup
    logger.info("Shutting down Observer Eye Middleware")
    await performance_monitor.cleanup()
    await cache_invalidation.stop_background_cleanup()
    
    # Stop telemetry collector
    await telemetry_collector.stop()
    
    # Shutdown data ingestion service
    from data_ingestion import shutdown_ingestion_service
    await shutdown_ingestion_service()
    
    # Close connections
    await crud_handler.close()
    await telemetry_enricher.close()
    await django_client.close()
    
    # Close cache manager
    if hasattr(cache_manager, '__aexit__'):
        await cache_manager.__aexit__(None, None, None)

async def _register_django_apps():
    """Register Django apps with the API client"""
    # Define Django app configurations
    django_apps = [
        DjangoAppConfig(
            app_name="analytics",
            app_label="analytics",
            models=["AnalyticsData", "DataSource", "AnalyticsQuery", "AnalyticsReport"],
            enable_crud=True,
            require_authentication=True
        ),
        DjangoAppConfig(
            app_name="appmetrics",
            app_label="appmetrics", 
            models=["ApplicationInstance", "ApplicationMetricData", "ApplicationCounter"],
            enable_crud=True,
            require_authentication=True
        ),
        DjangoAppConfig(
            app_name="core",
            app_label="core",
            models=["User", "UserSession", "AuditLog"],
            enable_crud=True,
            require_authentication=True,
            allowed_operations=["read", "update"]  # Restrict operations for core models
        ),
        DjangoAppConfig(
            app_name="notification",
            app_label="notification",
            models=["NotificationChannel", "Alert", "AlertRule"],
            enable_crud=True,
            require_authentication=True
        ),
        DjangoAppConfig(
            app_name="template_dashboards",
            app_label="template_dashboards",
            models=["DashboardTemplate", "Dashboard"],
            enable_crud=True,
            require_authentication=True
        )
    ]
    
    # Register each app
    for app_config in django_apps:
        django_client.register_app_config(app_config)
        logger.info(f"Registered Django app: {app_config.app_name}")

# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="Observer Eye Middleware",
    description="FastAPI middleware layer for the Observer Eye Platform - Logic Layer for data processing, performance monitoring, and API orchestration",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "development") == "development" else None,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:80",  # Angular frontend
        "http://localhost:4200",  # Angular dev server
        "http://localhost:3000",  # Alternative frontend port
        os.getenv("FRONTEND_URL", "http://localhost:80")
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"]
)

# Add trusted host middleware for security
trusted_hosts = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "testserver",  # Add testserver for FastAPI TestClient
    os.getenv("ALLOWED_HOST", "localhost")
]

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=trusted_hosts
)

# Add custom error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Add data validation middleware
validation_middleware = ValidationMiddleware(app)
app.add_middleware(ValidationMiddleware)

# Add cache middleware
cache_middleware = CacheMiddleware(
    app,
    cache_manager,
    default_ttl=300,  # 5 minutes for HTTP responses
    cache_get_requests=True,
    cache_post_requests=False,
    excluded_paths=['/health', '/docs', '/redoc', '/openapi.json', '/data/process']
)
app.add_middleware(CacheMiddleware, 
                  cache_manager=cache_manager,
                  default_ttl=300,
                  excluded_paths=['/health', '/docs', '/redoc', '/openapi.json', '/data/process'])

# Add OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)

# Dependency injection functions
async def get_performance_monitor() -> PerformanceMonitor:
    """Dependency injection for performance monitor"""
    return performance_monitor

async def get_circuit_breaker() -> CircuitBreaker:
    """Dependency injection for circuit breaker"""
    return circuit_breaker

async def get_data_pipeline() -> DataProcessingPipeline:
    """Dependency injection for data processing pipeline"""
    return data_pipeline

async def get_cache_manager() -> CacheManager:
    """Dependency injection for cache manager"""
    return cache_manager

async def get_cache_invalidation() -> CacheInvalidationStrategy:
    """Dependency injection for cache invalidation strategy"""
    return cache_invalidation

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency injection for authentication (placeholder for now)"""
    if not credentials:
        return None
    # TODO: Implement actual JWT token validation
    return {"user_id": "anonymous", "token": credentials.credentials}

# Middleware for request/response logging and performance tracking
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log requests and track performance"""
    request_id = request.headers.get("X-Request-ID", f"req_{id(request)}")
    
    # Start performance tracking
    start_time = performance_monitor.start_request_tracking(request_id)
    
    # Add request ID to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    # Calculate response time
    response_time = performance_monitor.end_request_tracking(request_id, start_time)
    response.headers["X-Response-Time"] = f"{response_time:.3f}ms"
    
    # Log request details
    logger.info(
        "Request processed",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        response_time_ms=response_time
    )
    
    return response

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "middleware",
        "version": "1.0.0",
        "timestamp": performance_monitor.get_current_timestamp()
    }

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check(
    monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """Detailed health check with system metrics"""
    try:
        health_data = await monitor.get_health_metrics()
        return {
            "status": "healthy",
            "service": "middleware",
            "version": "1.0.0",
            "metrics": health_data,
            "timestamp": monitor.get_current_timestamp()
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Observer Eye Middleware API",
        "status": "running",
        "version": "1.0.0",
        "description": "FastAPI Logic Layer for Observer Eye Platform",
        "endpoints": {
            "health": "/health",
            "detailed_health": "/health/detailed",
            "docs": "/docs" if os.getenv("ENVIRONMENT", "development") == "development" else "disabled",
            "metrics": "/metrics",
            "data_processing": "/data/process",
            "data_validation": "/data/validate",
            "pipeline_stats": "/data/pipeline/stats",
            "data_ingestion_streaming": "/data/ingest/streaming",
            "data_ingestion_batch": "/data/ingest/batch",
            "data_ingestion_stats": "/data/ingest/stats",
            "cache_stats": "/cache/stats",
            "cache_invalidate": "/cache/invalidate",
            "crud": "/crud",
            "telemetry": "/telemetry",
            "telemetry_batch": "/telemetry/batch",
            "telemetry_correlations": "/telemetry/correlations",
            "telemetry_analysis": "/telemetry/analysis"
        }
    }

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics(
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
    current_user = Depends(get_current_user)
):
    """Get performance metrics (requires authentication in production)"""
    try:
        metrics = await monitor.collect_metrics()
        return {
            "metrics": metrics,
            "timestamp": monitor.get_current_timestamp(),
            "collected_by": current_user.get("user_id", "anonymous") if current_user else "anonymous"
        }
    except Exception as e:
        logger.error("Failed to collect metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect metrics"
        )

# Data Processing Endpoints
@app.post("/data/process", tags=["Data Processing"])
async def process_data(
    request: Request,
    pipeline: DataProcessingPipeline = Depends(get_data_pipeline),
    current_user = Depends(get_current_user)
):
    """Process data through the complete pipeline"""
    try:
        # Get request body
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required"
            )
        
        # Parse JSON data
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format"
            )
        
        # Extract processing parameters
        input_data = data.get("data")
        schema_name = data.get("schema_name")
        
        if input_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'data' field is required"
            )
        
        # Process data through pipeline
        result = pipeline.process_data(input_data, schema_name)
        
        return {
            "success": result.success,
            "processed_data": result.processed_data,
            "errors": result.errors,
            "warnings": result.warnings,
            "processing_time_ms": result.processing_time_ms,
            "stages_completed": [stage.value for stage in result.stages_completed],
            "metadata": result.metadata,
            "timestamp": result.timestamp.isoformat(),
            "processed_by": current_user.get("user_id", "anonymous") if current_user else "anonymous"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Data processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data processing failed"
        )

@app.post("/data/validate", tags=["Data Processing"])
async def validate_data(
    request: Request,
    pipeline: DataProcessingPipeline = Depends(get_data_pipeline)
):
    """Validate data without full processing"""
    try:
        # Get request body
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required"
            )
        
        # Parse JSON data
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format"
            )
        
        # Extract validation parameters
        input_data = data.get("data")
        schema_name = data.get("schema_name")
        
        if input_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'data' field is required"
            )
        
        # Validate data
        validation_result = pipeline.validator.validate_data(input_data, schema_name)
        
        return {
            "is_valid": validation_result.is_valid,
            "status": validation_result.status.value,
            "errors": [
                {
                    "field": error.field,
                    "message": error.message,
                    "code": error.code,
                    "value": error.value
                }
                for error in validation_result.errors
            ],
            "warnings": [
                {
                    "field": warning.field,
                    "message": warning.message,
                    "code": warning.code,
                    "value": warning.value
                }
                for warning in validation_result.warnings
            ],
            "validated_data": validation_result.validated_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Data validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data validation failed"
        )

@app.get("/data/pipeline/stats", tags=["Data Processing"])
async def get_pipeline_stats(
    pipeline: DataProcessingPipeline = Depends(get_data_pipeline),
    current_user = Depends(get_current_user)
):
    """Get data processing pipeline statistics"""
    try:
        stats = pipeline.get_pipeline_stats()
        return {
            "pipeline_stats": stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requested_by": current_user.get("user_id", "anonymous") if current_user else "anonymous"
        }
    except Exception as e:
        logger.error("Failed to get pipeline stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pipeline statistics"
        )

# Cache Management Endpoints
@app.get("/cache/stats", tags=["Cache Management"])
async def get_cache_stats(
    cache_mgr: CacheManager = Depends(get_cache_manager),
    cache_inv: CacheInvalidationStrategy = Depends(get_cache_invalidation),
    current_user = Depends(get_current_user)
):
    """Get cache performance statistics"""
    try:
        cache_stats = await cache_mgr.get_stats()
        invalidation_stats = cache_inv.get_invalidation_stats()
        
        return {
            "cache_stats": cache_stats.__dict__,
            "invalidation_stats": invalidation_stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requested_by": current_user.get("user_id", "anonymous") if current_user else "anonymous"
        }
    except Exception as e:
        logger.error("Failed to get cache stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache statistics"
        )

@app.post("/cache/invalidate", tags=["Cache Management"])
async def invalidate_cache(
    request: Request,
    cache_inv: CacheInvalidationStrategy = Depends(get_cache_invalidation),
    current_user = Depends(get_current_user)
):
    """Invalidate cache entries by pattern or key"""
    try:
        # Get request body
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required"
            )
        
        # Parse JSON data
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format"
            )
        
        invalidated_count = 0
        
        # Invalidate by key
        if 'key' in data:
            invalidated_count = await cache_inv.invalidate_by_key(data['key'])
        
        # Invalidate by pattern
        elif 'pattern' in data:
            invalidated_count = await cache_inv.invalidate_by_pattern(data['pattern'])
        
        # Invalidate by event
        elif 'event_type' in data:
            event_data = data.get('event_data', {})
            invalidated_count = await cache_inv.invalidate_by_event(data['event_type'], event_data)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must specify 'key', 'pattern', or 'event_type'"
            )
        
        return {
            "success": True,
            "invalidated_count": invalidated_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "invalidated_by": current_user.get("user_id", "anonymous") if current_user else "anonymous"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Cache invalidation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache invalidation failed"
        )

@app.get("/cache/health", tags=["Cache Management"])
async def get_cache_health(
    cache_mgr: CacheManager = Depends(get_cache_manager)
):
    """Get cache system health status"""
    try:
        # Check if cache manager is working
        test_key = "health_check_test"
        test_value = {"timestamp": datetime.now(timezone.utc).isoformat()}
        
        # Test set operation
        set_success = await cache_mgr.set(test_key, test_value, 60)
        
        # Test get operation
        retrieved_value = await cache_mgr.get(test_key)
        
        # Test delete operation
        delete_success = await cache_mgr.delete(test_key)
        
        # Get cache stats
        cache_stats = await cache_mgr.get_stats()
        
        health_status = {
            "status": "healthy" if (set_success and retrieved_value and delete_success) else "unhealthy",
            "operations": {
                "set": set_success,
                "get": retrieved_value is not None,
                "delete": delete_success
            },
            "cache_stats": {
                "total_keys": cache_stats.total_keys,
                "memory_usage_bytes": cache_stats.memory_usage_bytes,
                "hit_rate": cache_stats.hit_rate
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error("Cache health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging"""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": performance_monitor.get_current_timestamp()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured logging"""
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url),
        method=request.method
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": performance_monitor.get_current_timestamp()
        }
    )

# CRUD Operations Endpoints
@app.post("/crud", tags=["CRUD Operations"])
async def handle_crud_operation(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Handle CRUD operations"""
    try:
        # Get request body
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required"
            )
        
        # Parse CRUD request
        try:
            from crud.models import CRUDRequest
            crud_request_data = json.loads(body)
            crud_request = CRUDRequest(**crud_request_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid CRUD request format: {str(e)}"
            )
        
        # Get client info
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        user_id = current_user.get("user_id") if current_user else None
        
        # Handle CRUD request
        response = await crud_handler.handle_request(
            request=crud_request,
            user_id=user_id,
            ip_address=client_host,
            user_agent=user_agent
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("CRUD operation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRUD operation failed"
        )

# Telemetry Collection Endpoints
@app.post("/telemetry", tags=["Telemetry"])
async def collect_telemetry(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Collect single telemetry data point"""
    try:
        # Get request body
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required"
            )
        
        # Parse telemetry data
        try:
            telemetry_data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format"
            )
        
        # Get client info
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Collect telemetry
        telemetry_id = await telemetry_collector.collect_single(
            telemetry_data=telemetry_data,
            source_ip=client_host,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "telemetry_id": telemetry_id,
            "message": "Telemetry data collected successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Telemetry collection failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telemetry collection failed"
        )

@app.post("/telemetry/batch", tags=["Telemetry"])
async def collect_telemetry_batch(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Collect batch of telemetry data"""
    try:
        # Get request body
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required"
            )
        
        # Parse telemetry batch
        try:
            batch_data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format"
            )
        
        # Get client info
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Collect telemetry batch
        telemetry_ids = await telemetry_collector.collect_batch(
            telemetry_batch=batch_data,
            source_ip=client_host,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "telemetry_ids": telemetry_ids,
            "collected_count": len(telemetry_ids),
            "message": "Telemetry batch collected successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Telemetry batch collection failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telemetry batch collection failed"
        )

@app.get("/telemetry/correlations", tags=["Telemetry"])
async def get_telemetry_correlations(
    limit: int = 100,
    rule_id: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get telemetry correlations"""
    try:
        correlations = telemetry_correlator.get_correlation_results(
            limit=limit,
            rule_id=rule_id
        )
        
        return {
            "success": True,
            "correlations": [correlation.dict() for correlation in correlations],
            "count": len(correlations),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get telemetry correlations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get telemetry correlations"
        )

@app.get("/telemetry/analysis", tags=["Telemetry"])
async def get_telemetry_analysis(
    limit: int = 100,
    pattern_id: Optional[str] = None,
    severity: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get telemetry analysis results"""
    try:
        from telemetry.models import SeverityLevel
        
        severity_filter = None
        if severity:
            try:
                severity_filter = SeverityLevel(severity.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity level: {severity}"
                )
        
        analysis_results = telemetry_analyzer.get_analysis_results(
            limit=limit,
            pattern_id=pattern_id,
            severity=severity_filter
        )
        
        return {
            "success": True,
            "analysis_results": [result.dict() for result in analysis_results],
            "count": len(analysis_results),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get telemetry analysis", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get telemetry analysis"
        )

@app.get("/telemetry/metrics", tags=["Telemetry"])
async def get_telemetry_metrics(
    current_user = Depends(get_current_user)
):
    """Get telemetry collection metrics"""
    try:
        metrics = telemetry_collector.get_metrics()
        
        return {
            "success": True,
            "metrics": metrics.dict(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get telemetry metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get telemetry metrics"
        )

# Data Ingestion Endpoints
@app.post("/data/ingest/streaming", tags=["Data Ingestion"])
async def ingest_streaming_data(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Ingest real-time streaming data"""
    try:
        from data_ingestion import get_ingestion_service, StreamingDataType
        
        # Get request body
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required"
            )
        
        # Parse JSON data
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format"
            )
        
        # Extract data and type
        streaming_data = data.get("data")
        data_type_str = data.get("data_type", "real_time_metrics")
        
        if streaming_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'data' field is required"
            )
        
        # Convert string to enum
        try:
            data_type = StreamingDataType(data_type_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid data_type: {data_type_str}"
            )
        
        # Get ingestion service
        ingestion_service = await get_ingestion_service()
        
        # Ingest data
        result = await ingestion_service.ingest_streaming_data(streaming_data, data_type)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Streaming data ingestion failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Streaming data ingestion failed"
        )

@app.post("/data/ingest/batch", tags=["Data Ingestion"])
async def ingest_batch_data(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Ingest batch of real data"""
    try:
        from data_ingestion import get_ingestion_service, StreamingDataType
        
        # Get request body
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required"
            )
        
        # Parse JSON data
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format"
            )
        
        # Extract data and type
        batch_data = data.get("data")
        data_type_str = data.get("data_type", "real_time_metrics")
        
        if batch_data is None or not isinstance(batch_data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'data' field is required and must be a list"
            )
        
        # Convert string to enum
        try:
            data_type = StreamingDataType(data_type_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid data_type: {data_type_str}"
            )
        
        # Get ingestion service
        ingestion_service = await get_ingestion_service()
        
        # Ingest batch
        result = await ingestion_service.ingest_batch_data(batch_data, data_type)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Batch data ingestion failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch data ingestion failed"
        )

@app.get("/data/ingest/stats", tags=["Data Ingestion"])
async def get_ingestion_stats(
    current_user = Depends(get_current_user)
):
    """Get data ingestion statistics"""
    try:
        from data_ingestion import get_ingestion_service
        
        # Get ingestion service
        ingestion_service = await get_ingestion_service()
        
        # Get stats
        stats = await ingestion_service.get_ingestion_stats()
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get ingestion stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ingestion statistics"
        )

# Django Integration Health Check
@app.get("/django/health", tags=["Django Integration"])
async def django_health_check():
    """Check Django backend health"""
    try:
        health_check = await django_client.health_check()
        
        return {
            "success": True,
            "health_check": health_check.dict(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Django health check failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8400,
        reload=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )