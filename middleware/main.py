"""
Observer-Eye FastAPI Middleware
Business Logic Layer with Four Pillars Data Processors and Real-Time Correlation

This middleware serves as the core processing layer for the Observer-Eye platform,
handling real-time data correlation across the four pillars of observability with
deep system integration, eBPF-based kernel monitoring, and payload inspection.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import psutil
import structlog

# Four Pillars Processors and Correlation Engine
from processors import (
    MetricsProcessor, EventsProcessor, LogsProcessor, TracesProcessor,
    RealTimeCorrelationEngine, DeepSystemIntegration
)
from processors.metrics_processor import MetricData, MetricType
from processors.events_processor import EventData, EventSeverity, EventCategory
from processors.logs_processor import LogData, LogLevel, LogFormat
from processors.traces_processor import SpanData, SpanKind, SpanStatus
from processors.deep_system_integration import SystemMonitoringLevel, PayloadInspectionMode

# BI Analytics Engine
from analytics import (
    BIAnalyticsEngine, ReportGenerator, MachineLearningPipeline,
    DataWarehouseManager, KPICalculator, TrendAnalyzer,
    AnalyticsRequest, ReportRequest, KPIRequest, TrendAnalysisRequest,
    AnalyticsResult, ReportResult, KPIResult, TrendAnalysisResult,
    ReportFormat, ReportType, KPIType, TrendType, AnalyticsMetric,
    TimeRange, DataFilter, AggregationConfig, ScheduleConfig
)

# eBPF and deep system monitoring imports
try:
    from bcc import BPF
    EBPF_AVAILABLE = True
except ImportError:
    EBPF_AVAILABLE = False
    BPF = None

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

# Configuration
class MiddlewareConfig:
    """Configuration for the FastAPI middleware"""
    
    def __init__(self):
        self.environment = os.getenv("FASTAPI_ENV", "development")
        self.host = os.getenv("FASTAPI_HOST", "0.0.0.0")
        self.port = int(os.getenv("FASTAPI_PORT", "8000"))
        self.workers = int(os.getenv("FASTAPI_WORKERS", "1"))
        
        # Four Pillars Processing Configuration
        self.enable_metrics_processing = os.getenv("ENABLE_METRICS_PROCESSING", "true").lower() == "true"
        self.enable_events_processing = os.getenv("ENABLE_EVENTS_PROCESSING", "true").lower() == "true"
        self.enable_logs_processing = os.getenv("ENABLE_LOGS_PROCESSING", "true").lower() == "true"
        self.enable_traces_processing = os.getenv("ENABLE_TRACES_PROCESSING", "true").lower() == "true"
        
        # Real-Time Correlation Configuration
        self.correlation_window_ms = float(os.getenv("CORRELATION_WINDOW_MS", "5000"))
        self.correlation_threshold = float(os.getenv("CORRELATION_THRESHOLD", "0.7"))
        self.max_candidates_per_window = int(os.getenv("MAX_CANDIDATES_PER_WINDOW", "1000"))
        
        # eBPF and monitoring configuration
        self.ebpf_enabled = os.getenv("EBPF_ENABLED", "false").lower() == "true"
        self.deep_monitoring_enabled = os.getenv("DEEP_MONITORING_ENABLED", "true").lower() == "true"
        self.kernel_monitoring_enabled = os.getenv("KERNEL_MONITORING_ENABLED", "false").lower() == "true"
        self.payload_inspection_enabled = os.getenv("PAYLOAD_INSPECTION_ENABLED", "false").lower() == "true"
        
        # Mock mode for development/testing
        self.ebpf_mock_mode = os.getenv("EBPF_MOCK_MODE", "true").lower() == "true"
        
        # Deep System Integration Configuration
        monitoring_level_str = os.getenv("SYSTEM_MONITORING_LEVEL", "enhanced").lower()
        self.system_monitoring_level = {
            "basic": SystemMonitoringLevel.BASIC,
            "enhanced": SystemMonitoringLevel.ENHANCED,
            "deep": SystemMonitoringLevel.DEEP,
            "kernel": SystemMonitoringLevel.KERNEL
        }.get(monitoring_level_str, SystemMonitoringLevel.ENHANCED)
        
        payload_mode_str = os.getenv("PAYLOAD_INSPECTION_MODE", "metadata_only").lower()
        self.payload_inspection_mode = {
            "disabled": PayloadInspectionMode.DISABLED,
            "metadata_only": PayloadInspectionMode.METADATA_ONLY,
            "header_inspection": PayloadInspectionMode.HEADER_INSPECTION,
            "deep_inspection": PayloadInspectionMode.DEEP_INSPECTION
        }.get(payload_mode_str, PayloadInspectionMode.METADATA_ONLY)
        
        # Database and external service URLs
        self.database_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/observability")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.analytics_url = os.getenv("ANALYTICS_URL", "http://localhost:8002")

config = MiddlewareConfig()

# Global processor instances
metrics_processor = None
events_processor = None
logs_processor = None
traces_processor = None
correlation_engine = None
deep_system_integration = None

# BI Analytics instances
bi_analytics_engine = None
report_generator = None
ml_pipeline = None
data_warehouse_manager = None

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global metrics_processor, events_processor, logs_processor, traces_processor
    global correlation_engine, deep_system_integration
    global bi_analytics_engine, report_generator, ml_pipeline, data_warehouse_manager
    
    # Startup
    logger.info("Starting Observer-Eye FastAPI Middleware with Four Pillars Processing and BI Analytics", 
               environment=config.environment,
               ebpf_enabled=config.ebpf_enabled,
               system_monitoring_level=config.system_monitoring_level.value,
               correlation_enabled=True,
               bi_analytics_enabled=True)
    
    try:
        # Initialize Data Warehouse Manager
        data_warehouse_manager = DataWarehouseManager(
            warehouse_url=config.analytics_url.replace('http://', 'sqlite:///') + '/warehouse.db',
            operational_db_url=config.database_url
        )
        await data_warehouse_manager.initialize()
        
        # Initialize BI Analytics Engine
        bi_analytics_engine = BIAnalyticsEngine(
            data_warehouse_manager=data_warehouse_manager,
            enable_ml_pipeline=True,
            cache_results=True
        )
        
        # Initialize Machine Learning Pipeline
        ml_pipeline = MachineLearningPipeline(models_directory="ml_models")
        
        # Initialize Report Generator
        report_generator = ReportGenerator(
            analytics_engine=bi_analytics_engine,
            reports_directory="reports",
            templates_directory="templates"
        )
        
        # Initialize Deep System Integration
        deep_system_integration = DeepSystemIntegration(
            monitoring_level=config.system_monitoring_level,
            payload_inspection_mode=config.payload_inspection_mode,
            enable_mock_mode=config.ebpf_mock_mode
        )
        await deep_system_integration.initialize()
        
        # Initialize Four Pillars Processors
        if config.enable_metrics_processing:
            metrics_processor = MetricsProcessor("metrics_processor_001")
            logger.info("Metrics processor initialized")
        
        if config.enable_events_processing:
            events_processor = EventsProcessor("events_processor_001")
            logger.info("Events processor initialized")
        
        if config.enable_logs_processing:
            logs_processor = LogsProcessor("logs_processor_001")
            logger.info("Logs processor initialized")
        
        if config.enable_traces_processing:
            traces_processor = TracesProcessor("traces_processor_001")
            logger.info("Traces processor initialized")
        
        # Initialize Real-Time Correlation Engine
        correlation_engine = RealTimeCorrelationEngine(
            correlation_window_ms=config.correlation_window_ms,
            max_candidates_per_window=config.max_candidates_per_window,
            correlation_threshold=config.correlation_threshold
        )
        await correlation_engine.start()
        logger.info("Real-time correlation engine started")
        
        # Start background monitoring tasks
        monitoring_task = asyncio.create_task(background_monitoring())
        
        logger.info("Four Pillars Processing System with BI Analytics initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize Four Pillars Processing System with BI Analytics", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Observer-Eye FastAPI Middleware")
    
    try:
        monitoring_task.cancel()
        
        if correlation_engine:
            await correlation_engine.stop()
        
        if deep_system_integration:
            await deep_system_integration.shutdown()
        
        if data_warehouse_manager:
            await data_warehouse_manager.shutdown()
        
        logger.info("Four Pillars Processing System with BI Analytics shutdown complete")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

# Pydantic models for API requests and responses
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment name")
    four_pillars_status: Dict[str, Any] = Field(..., description="Four pillars processors status")
    correlation_engine_status: Dict[str, Any] = Field(..., description="Correlation engine status")
    deep_monitoring: Dict[str, Any] = Field(..., description="Deep system monitoring status")
    system_metrics: Dict[str, Any] = Field(..., description="Current system metrics")

class SystemMetricsResponse(BaseModel):
    """System metrics response model"""
    metrics: Dict[str, Any] = Field(..., description="System performance metrics")
    deep_monitoring_active: bool = Field(..., description="Deep monitoring status")
    correlation_active: bool = Field(..., description="Correlation engine status")

class MetricsRequest(BaseModel):
    """Metrics processing request"""
    name: str = Field(..., description="Metric name")
    value: Union[float, int] = Field(..., description="Metric value")
    metric_type: str = Field(..., description="Metric type (counter, gauge, histogram, timer)")
    timestamp: Optional[float] = None
    labels: Optional[Dict[str, str]] = None
    unit: Optional[str] = None
    help_text: Optional[str] = None

class EventsRequest(BaseModel):
    """Events processing request"""
    event_type: str = Field(..., description="Event type")
    severity: str = Field(..., description="Event severity (critical, error, warning, info, debug)")
    message: str = Field(..., description="Event message")
    timestamp: Optional[float] = None
    source: Optional[str] = None
    category: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class LogsRequest(BaseModel):
    """Logs processing request"""
    message: str = Field(..., description="Log message")
    level: str = Field(..., description="Log level (trace, debug, info, warn, error, fatal)")
    timestamp: Optional[float] = None
    logger_name: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    thread_id: Optional[str] = None
    process_id: Optional[int] = None
    structured_data: Optional[Dict[str, Any]] = None
    raw_log: Optional[str] = None
    format_type: Optional[str] = None

class TracesRequest(BaseModel):
    """Traces processing request"""
    trace_id: str = Field(..., description="Trace ID")
    span_id: str = Field(..., description="Span ID")
    operation_name: str = Field(..., description="Operation name")
    start_time: float = Field(..., description="Span start time")
    end_time: Optional[float] = None
    parent_span_id: Optional[str] = None
    span_kind: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    logs: Optional[List[Dict[str, Any]]] = None
    process: Optional[Dict[str, Any]] = None
    duration_microseconds: Optional[int] = None

class ProcessingResponse(BaseModel):
    """Processing response model"""
    status: str = Field(..., description="Processing status")
    correlation_id: str = Field(..., description="Correlation ID")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    correlations_found: List[Dict[str, Any]] = Field(default_factory=list, description="Correlations found")
    message: str = Field(..., description="Processing message")

# BI Analytics Request Models
class AnalyticsRequestModel(BaseModel):
    """Analytics request model"""
    data_sources: List[str] = Field(..., description="Data sources to query")
    start_time: str = Field(..., description="Start time (ISO format)")
    end_time: str = Field(..., description="End time (ISO format)")
    filters: Optional[List[Dict[str, Any]]] = Field(None, description="Data filters")
    aggregations: Optional[List[Dict[str, Any]]] = Field(None, description="Aggregation configurations")
    metrics: Optional[List[str]] = Field(None, description="Metrics to calculate")
    group_by: Optional[List[str]] = Field(None, description="Group by fields")
    limit: Optional[int] = Field(None, description="Maximum rows to return")

class ReportRequestModel(BaseModel):
    """Report generation request model"""
    title: str = Field(..., description="Report title")
    report_type: str = Field(..., description="Report type (executive, operational, technical)")
    report_format: str = Field(..., description="Report format (pdf, excel, html, csv, json)")
    data_sources: List[str] = Field(..., description="Data sources for the report")
    start_time: str = Field(..., description="Start time (ISO format)")
    end_time: str = Field(..., description="End time (ISO format)")
    description: Optional[str] = Field(None, description="Report description")
    filters: Optional[List[Dict[str, Any]]] = Field(None, description="Data filters")
    include_charts: bool = Field(True, description="Include charts in report")
    include_tables: bool = Field(True, description="Include tables in report")
    include_executive_summary: bool = Field(True, description="Include executive summary")

class KPIRequestModel(BaseModel):
    """KPI calculation request model"""
    kpi_name: str = Field(..., description="KPI name")
    kpi_type: str = Field(..., description="KPI type")
    start_time: str = Field(..., description="Start time (ISO format)")
    end_time: str = Field(..., description="End time (ISO format)")
    data_sources: Optional[List[str]] = Field(None, description="Data sources")
    target_value: Optional[float] = Field(None, description="Target value")
    warning_threshold: Optional[float] = Field(None, description="Warning threshold")
    critical_threshold: Optional[float] = Field(None, description="Critical threshold")
    calculation_formula: Optional[str] = Field(None, description="Custom calculation formula")
    filters: Optional[List[Dict[str, Any]]] = Field(None, description="Data filters")

class TrendAnalysisRequestModel(BaseModel):
    """Trend analysis request model"""
    trend_type: str = Field(..., description="Trend analysis type")
    metric_field: str = Field(..., description="Metric field to analyze")
    data_sources: List[str] = Field(..., description="Data sources")
    start_time: str = Field(..., description="Start time (ISO format)")
    end_time: str = Field(..., description="End time (ISO format)")
    filters: Optional[List[Dict[str, Any]]] = Field(None, description="Data filters")
    forecast_periods: Optional[int] = Field(None, description="Number of forecast periods")
    confidence_interval: float = Field(0.95, description="Confidence interval for forecasting")
    seasonality_period: Optional[str] = Field(None, description="Seasonality period")

class MLTrainingRequestModel(BaseModel):
    """ML model training request model"""
    model_name: str = Field(..., description="Model name")
    data_sources: List[str] = Field(..., description="Training data sources")
    start_time: str = Field(..., description="Start time (ISO format)")
    end_time: str = Field(..., description="End time (ISO format)")
    filters: Optional[List[Dict[str, Any]]] = Field(None, description="Data filters")
    target_column: Optional[str] = Field(None, description="Target column for supervised learning")

class MLPredictionRequestModel(BaseModel):
    """ML prediction request model"""
    model_name: str = Field(..., description="Model name to use")
    data_sources: List[str] = Field(..., description="Prediction data sources")
    start_time: str = Field(..., description="Start time (ISO format)")
    end_time: str = Field(..., description="End time (ISO format)")
    filters: Optional[List[Dict[str, Any]]] = Field(None, description="Data filters")

# Create FastAPI application
mymiddleware = FastAPI(
    title="Observer-Eye FastAPI Middleware with BI Analytics",
    description="Business Logic Layer with Four Pillars Processing, Real-Time Correlation, and Advanced BI Analytics Engine",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if config.environment != "production" else None,
    redoc_url="/redoc" if config.environment != "production" else None
)

# Add middleware
mymiddleware.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.environment == "development" else ["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mymiddleware.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if config.environment == "development" else ["localhost", "127.0.0.1"]
)

# Background monitoring task
async def background_monitoring():
    """Background task for continuous system monitoring"""
    while True:
        try:
            # Get system context from deep system integration
            if deep_system_integration:
                system_context = await deep_system_integration.get_system_context()
                
                # Update processor health checks
                if metrics_processor:
                    await metrics_processor.health_check()
                if events_processor:
                    await events_processor.health_check()
                if logs_processor:
                    await logs_processor.health_check()
                if traces_processor:
                    await traces_processor.health_check()
            
            await asyncio.sleep(30)  # Update every 30 seconds
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Background monitoring error", error=str(e))
            await asyncio.sleep(60)  # Wait longer on error

# API Routes
@mymiddleware.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "Observer-Eye FastAPI Middleware",
        "status": "running",
        "version": "1.0.0",
        "environment": config.environment
    }

@mymiddleware.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check with four pillars processors and correlation engine"""
    try:
        # Get system metrics from deep system integration
        system_metrics = {}
        deep_monitoring_status = {}
        
        if deep_system_integration:
            system_context = await deep_system_integration.get_system_context()
            system_metrics = system_context
            monitoring_stats = await deep_system_integration.get_monitoring_statistics()
            deep_monitoring_status = monitoring_stats
        
        # Get four pillars processors status
        four_pillars_status = {}
        
        if metrics_processor:
            four_pillars_status['metrics'] = await metrics_processor.health_check()
        if events_processor:
            four_pillars_status['events'] = await events_processor.health_check()
        if logs_processor:
            four_pillars_status['logs'] = await logs_processor.health_check()
        if traces_processor:
            four_pillars_status['traces'] = await traces_processor.health_check()
        
        # Get correlation engine status
        correlation_engine_status = {}
        if correlation_engine:
            correlation_engine_status = await correlation_engine.get_correlation_statistics()
        
        return HealthResponse(
            status="healthy",
            timestamp=str(asyncio.get_event_loop().time()),
            version="1.0.0",
            environment=config.environment,
            four_pillars_status=four_pillars_status,
            correlation_engine_status=correlation_engine_status,
            deep_monitoring=deep_monitoring_status,
            system_metrics=system_metrics
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@mymiddleware.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics():
    """Get current system metrics and processing statistics"""
    try:
        # Get system metrics from deep system integration
        metrics = {}
        if deep_system_integration:
            metrics = await deep_system_integration.get_system_context()
        
        return SystemMetricsResponse(
            metrics=metrics,
            deep_monitoring_active=deep_system_integration is not None,
            correlation_active=correlation_engine is not None
        )
    except Exception as e:
        logger.error("Failed to get system metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# Four Pillars Processing Endpoints

@mymiddleware.post("/observability/metrics", response_model=ProcessingResponse)
async def process_metrics(request: MetricsRequest, background_tasks: BackgroundTasks):
    """Process metrics data through the metrics processor"""
    try:
        if not metrics_processor:
            raise HTTPException(status_code=503, detail="Metrics processor not available")
        
        # Convert request to MetricData
        metric_type_enum = {
            'counter': MetricType.COUNTER,
            'gauge': MetricType.GAUGE,
            'histogram': MetricType.HISTOGRAM,
            'timer': MetricType.TIMER
        }.get(request.metric_type.lower(), MetricType.GAUGE)
        
        metric_data = MetricData(
            name=request.name,
            value=request.value,
            metric_type=metric_type_enum,
            timestamp=request.timestamp,
            labels=request.labels,
            unit=request.unit,
            help_text=request.help_text
        )
        
        # Process through metrics processor
        processing_result = await metrics_processor.process(metric_data)
        
        # Add to correlation engine
        correlations = []
        if correlation_engine and processing_result.is_successful:
            correlations = await correlation_engine.add_candidate(processing_result)
        
        return ProcessingResponse(
            status=processing_result.status.value,
            correlation_id=processing_result.metadata.correlation_id,
            processing_time_ms=processing_result.processing_latency_ms,
            correlations_found=[{
                'correlation_id': corr.correlation_id,
                'correlation_type': corr.correlation_type.value,
                'strength': corr.strength.value,
                'confidence_score': corr.confidence_score
            } for corr in correlations],
            message="Metrics data processed successfully"
        )
        
    except Exception as e:
        logger.error("Metrics processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Metrics processing failed: {str(e)}")

@mymiddleware.post("/observability/events", response_model=ProcessingResponse)
async def process_events(request: EventsRequest, background_tasks: BackgroundTasks):
    """Process events data through the events processor"""
    try:
        if not events_processor:
            raise HTTPException(status_code=503, detail="Events processor not available")
        
        # Convert request to EventData
        severity_enum = {
            'critical': EventSeverity.CRITICAL,
            'error': EventSeverity.ERROR,
            'warning': EventSeverity.WARNING,
            'info': EventSeverity.INFO,
            'debug': EventSeverity.DEBUG
        }.get(request.severity.lower(), EventSeverity.INFO)
        
        category_enum = None
        if request.category:
            category_enum = {
                'system': EventCategory.SYSTEM,
                'application': EventCategory.APPLICATION,
                'security': EventCategory.SECURITY,
                'network': EventCategory.NETWORK,
                'user': EventCategory.USER,
                'infrastructure': EventCategory.INFRASTRUCTURE,
                'business': EventCategory.BUSINESS
            }.get(request.category.lower())
        
        event_data = EventData(
            event_type=request.event_type,
            severity=severity_enum,
            message=request.message,
            timestamp=request.timestamp,
            source=request.source,
            category=category_enum,
            attributes=request.attributes,
            tags=request.tags,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Process through events processor
        processing_result = await events_processor.process(event_data)
        
        # Add to correlation engine
        correlations = []
        if correlation_engine and processing_result.is_successful:
            correlations = await correlation_engine.add_candidate(processing_result)
        
        return ProcessingResponse(
            status=processing_result.status.value,
            correlation_id=processing_result.metadata.correlation_id,
            processing_time_ms=processing_result.processing_latency_ms,
            correlations_found=[{
                'correlation_id': corr.correlation_id,
                'correlation_type': corr.correlation_type.value,
                'strength': corr.strength.value,
                'confidence_score': corr.confidence_score
            } for corr in correlations],
            message="Events data processed successfully"
        )
        
    except Exception as e:
        logger.error("Events processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Events processing failed: {str(e)}")

@mymiddleware.post("/observability/logs", response_model=ProcessingResponse)
async def process_logs(request: LogsRequest, background_tasks: BackgroundTasks):
    """Process logs data through the logs processor"""
    try:
        if not logs_processor:
            raise HTTPException(status_code=503, detail="Logs processor not available")
        
        # Convert request to LogData
        level_enum = {
            'trace': LogLevel.TRACE,
            'debug': LogLevel.DEBUG,
            'info': LogLevel.INFO,
            'warn': LogLevel.WARN,
            'error': LogLevel.ERROR,
            'fatal': LogLevel.FATAL
        }.get(request.level.lower(), LogLevel.INFO)
        
        format_enum = None
        if request.format_type:
            format_enum = {
                'plain_text': LogFormat.PLAIN_TEXT,
                'json': LogFormat.JSON,
                'structured': LogFormat.STRUCTURED,
                'syslog': LogFormat.SYSLOG,
                'apache_combined': LogFormat.APACHE_COMBINED,
                'nginx': LogFormat.NGINX,
                'kernel': LogFormat.KERNEL
            }.get(request.format_type.lower())
        
        log_data = LogData(
            message=request.message,
            level=level_enum,
            timestamp=request.timestamp,
            logger_name=request.logger_name,
            source_file=request.source_file,
            line_number=request.line_number,
            function_name=request.function_name,
            thread_id=request.thread_id,
            process_id=request.process_id,
            structured_data=request.structured_data,
            raw_log=request.raw_log,
            format_type=format_enum
        )
        
        # Process through logs processor
        processing_result = await logs_processor.process(log_data)
        
        # Add to correlation engine
        correlations = []
        if correlation_engine and processing_result.is_successful:
            correlations = await correlation_engine.add_candidate(processing_result)
        
        return ProcessingResponse(
            status=processing_result.status.value,
            correlation_id=processing_result.metadata.correlation_id,
            processing_time_ms=processing_result.processing_latency_ms,
            correlations_found=[{
                'correlation_id': corr.correlation_id,
                'correlation_type': corr.correlation_type.value,
                'strength': corr.strength.value,
                'confidence_score': corr.confidence_score
            } for corr in correlations],
            message="Logs data processed successfully"
        )
        
    except Exception as e:
        logger.error("Logs processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Logs processing failed: {str(e)}")

@mymiddleware.post("/observability/traces", response_model=ProcessingResponse)
async def process_traces(request: TracesRequest, background_tasks: BackgroundTasks):
    """Process traces data through the traces processor"""
    try:
        if not traces_processor:
            raise HTTPException(status_code=503, detail="Traces processor not available")
        
        # Convert request to SpanData
        span_kind_enum = None
        if request.span_kind:
            span_kind_enum = {
                'internal': SpanKind.INTERNAL,
                'server': SpanKind.SERVER,
                'client': SpanKind.CLIENT,
                'producer': SpanKind.PRODUCER,
                'consumer': SpanKind.CONSUMER
            }.get(request.span_kind.lower())
        
        status_enum = None
        if request.status:
            status_enum = {
                'unset': SpanStatus.UNSET,
                'ok': SpanStatus.OK,
                'error': SpanStatus.ERROR
            }.get(request.status.lower())
        
        span_data = SpanData(
            trace_id=request.trace_id,
            span_id=request.span_id,
            operation_name=request.operation_name,
            start_time=request.start_time,
            end_time=request.end_time,
            parent_span_id=request.parent_span_id,
            span_kind=span_kind_enum,
            status=status_enum,
            tags=request.tags,
            logs=request.logs,
            process=request.process,
            duration_microseconds=request.duration_microseconds
        )
        
        # Process through traces processor
        processing_result = await traces_processor.process(span_data)
        
        # Add to correlation engine
        correlations = []
        if correlation_engine and processing_result.is_successful:
            correlations = await correlation_engine.add_candidate(processing_result)
        
        return ProcessingResponse(
            status=processing_result.status.value,
            correlation_id=processing_result.metadata.correlation_id,
            processing_time_ms=processing_result.processing_latency_ms,
            correlations_found=[{
                'correlation_id': corr.correlation_id,
                'correlation_type': corr.correlation_type.value,
                'strength': corr.strength.value,
                'confidence_score': corr.confidence_score
            } for corr in correlations],
            message="Traces data processed successfully"
        )
        
    except Exception as e:
        logger.error("Traces processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Traces processing failed: {str(e)}")

# Correlation and Analytics Endpoints

@mymiddleware.get("/correlation/statistics")
async def get_correlation_statistics():
    """Get correlation engine statistics"""
    try:
        if not correlation_engine:
            raise HTTPException(status_code=503, detail="Correlation engine not available")
        
        return await correlation_engine.get_correlation_statistics()
        
    except Exception as e:
        logger.error("Failed to get correlation statistics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get correlation statistics: {str(e)}")

@mymiddleware.get("/correlation/active")
async def get_active_correlations(limit: int = 50):
    """Get active correlations"""
    try:
        if not correlation_engine:
            raise HTTPException(status_code=503, detail="Correlation engine not available")
        
        return await correlation_engine.get_active_correlations(limit)
        
    except Exception as e:
        logger.error("Failed to get active correlations", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get active correlations: {str(e)}")

@mymiddleware.get("/processors/statistics")
async def get_processors_statistics():
    """Get statistics from all four pillars processors"""
    try:
        stats = {}
        
        if metrics_processor:
            stats['metrics'] = metrics_processor.get_processing_stats()
            stats['metrics']['aggregations'] = await metrics_processor.get_aggregation_summary()
        
        if events_processor:
            stats['events'] = events_processor.get_processing_stats()
            stats['events']['security_incidents'] = await events_processor.get_security_incidents_summary()
            stats['events']['event_patterns'] = await events_processor.get_event_patterns_summary()
        
        if logs_processor:
            stats['logs'] = logs_processor.get_processing_stats()
            stats['logs']['error_patterns'] = await logs_processor.get_error_patterns_summary()
        
        if traces_processor:
            stats['traces'] = traces_processor.get_processing_stats()
            stats['traces']['service_topology'] = await traces_processor.get_service_topology_summary()
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get processors statistics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get processors statistics: {str(e)}")

@mymiddleware.get("/deep-system/status")
async def deep_system_status():
    """Get deep system monitoring status"""
    try:
        if not deep_system_integration:
            raise HTTPException(status_code=503, detail="Deep system integration not available")
        
        return await deep_system_integration.get_monitoring_statistics()
        
    except Exception as e:
        logger.error("Failed to get deep system status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# BI Analytics Endpoints

@mymiddleware.post("/analytics/analyze", response_model=Dict[str, Any])
async def process_analytics_request(
    data_sources: List[str],
    start_time: str,
    end_time: str,
    filters: Optional[List[Dict[str, Any]]] = None,
    aggregations: Optional[List[Dict[str, Any]]] = None,
    metrics: Optional[List[str]] = None,
    group_by: Optional[List[str]] = None,
    limit: Optional[int] = None
):
    """Process analytics request and return comprehensive analysis"""
    try:
        if not bi_analytics_engine:
            raise HTTPException(status_code=503, detail="BI Analytics engine not available")
        
        # Parse datetime strings
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Create time range
        time_range = TimeRange(start_time=start_datetime, end_time=end_datetime)
        
        # Parse filters
        parsed_filters = []
        if filters:
            for f in filters:
                parsed_filters.append(DataFilter(
                    field=f['field'],
                    operator=f['operator'],
                    value=f['value'],
                    case_sensitive=f.get('case_sensitive', True)
                ))
        
        # Parse aggregations
        parsed_aggregations = []
        if aggregations:
            for agg in aggregations:
                parsed_aggregations.append(AggregationConfig(
                    field=agg['field'],
                    function=AnalyticsMetric(agg['function']),
                    group_by=agg.get('group_by'),
                    having_filter=None  # Simplified for now
                ))
        
        # Parse metrics
        parsed_metrics = []
        if metrics:
            for metric in metrics:
                try:
                    parsed_metrics.append(AnalyticsMetric(metric))
                except ValueError:
                    logger.warning("Unknown metric type", metric=metric)
        
        # Create analytics request
        analytics_request = AnalyticsRequest(
            time_range=time_range,
            data_sources=data_sources,
            filters=parsed_filters,
            aggregations=parsed_aggregations,
            metrics=parsed_metrics,
            group_by=group_by,
            limit=limit
        )
        
        # Process request
        result = await bi_analytics_engine.process_analytics_request(analytics_request)
        
        return {
            'status': result.status,
            'request_id': result.request_id,
            'data': result.data,
            'metadata': result.metadata,
            'processing_time_ms': result.processing_time_ms,
            'row_count': result.row_count,
            'error_message': result.error_message,
            'warnings': result.warnings
        }
        
    except Exception as e:
        logger.error("Analytics request processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analytics processing failed: {str(e)}")

@mymiddleware.post("/analytics/reports/generate")
async def generate_report(
    title: str,
    report_type: str,
    report_format: str,
    data_sources: List[str],
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    filters: Optional[List[Dict[str, Any]]] = None,
    include_charts: bool = True,
    include_tables: bool = True,
    include_executive_summary: bool = True
):
    """Generate a comprehensive report"""
    try:
        if not report_generator:
            raise HTTPException(status_code=503, detail="Report generator not available")
        
        # Parse datetime strings
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Create time range
        time_range = TimeRange(start_time=start_datetime, end_time=end_datetime)
        
        # Parse filters
        parsed_filters = []
        if filters:
            for f in filters:
                parsed_filters.append(DataFilter(
                    field=f['field'],
                    operator=f['operator'],
                    value=f['value']
                ))
        
        # Create analytics request for the report
        analytics_request = AnalyticsRequest(
            time_range=time_range,
            data_sources=data_sources,
            filters=parsed_filters,
            aggregations=[],  # Will be auto-generated based on report type
            metrics=[AnalyticsMetric.MEAN, AnalyticsMetric.COUNT, AnalyticsMetric.MAX, AnalyticsMetric.MIN]
        )
        
        # Create report request
        report_request = ReportRequest(
            report_type=ReportType(report_type),
            report_format=ReportFormat(report_format),
            title=title,
            description=description,
            analytics_request=analytics_request,
            include_charts=include_charts,
            include_tables=include_tables,
            include_executive_summary=include_executive_summary
        )
        
        # Generate report
        result = await report_generator.generate_report(report_request)
        
        return {
            'status': result.status,
            'request_id': result.request_id,
            'report_id': result.report_id,
            'report_format': result.report_format.value,
            'file_path': result.file_path,
            'file_size_bytes': result.file_size_bytes,
            'generation_time_ms': result.generation_time_ms,
            'error_message': result.error_message
        }
        
    except Exception as e:
        logger.error("Report generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@mymiddleware.post("/analytics/kpi/calculate")
async def calculate_kpi(
    kpi_name: str,
    kpi_type: str,
    start_time: str,
    end_time: str,
    data_sources: Optional[List[str]] = None,
    target_value: Optional[float] = None,
    warning_threshold: Optional[float] = None,
    critical_threshold: Optional[float] = None,
    calculation_formula: Optional[str] = None,
    filters: Optional[List[Dict[str, Any]]] = None
):
    """Calculate Key Performance Indicator"""
    try:
        if not bi_analytics_engine or not bi_analytics_engine.kpi_calculator:
            raise HTTPException(status_code=503, detail="KPI calculator not available")
        
        # Parse datetime strings
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Create time range
        time_range = TimeRange(start_time=start_datetime, end_time=end_datetime)
        
        # Parse filters
        parsed_filters = []
        if filters:
            for f in filters:
                parsed_filters.append(DataFilter(
                    field=f['field'],
                    operator=f['operator'],
                    value=f['value']
                ))
        
        # Create KPI request
        kpi_request = KPIRequest(
            kpi_type=KPIType(kpi_type),
            kpi_name=kpi_name,
            time_range=time_range,
            target_value=target_value,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            calculation_formula=calculation_formula,
            data_sources=data_sources or [],
            filters=parsed_filters
        )
        
        # Calculate KPI
        result = await bi_analytics_engine.kpi_calculator.calculate_kpi(kpi_request)
        
        return {
            'request_id': result.request_id,
            'kpi_name': result.kpi_name,
            'kpi_type': result.kpi_type.value,
            'current_value': result.current_value,
            'target_value': result.target_value,
            'variance_from_target': result.variance_from_target,
            'status': result.status,
            'trend_direction': result.trend_direction,
            'trend_percentage': result.trend_percentage,
            'historical_values': result.historical_values,
            'calculation_details': result.calculation_details
        }
        
    except Exception as e:
        logger.error("KPI calculation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")

@mymiddleware.post("/analytics/trends/analyze")
async def analyze_trend(
    trend_type: str,
    metric_field: str,
    data_sources: List[str],
    start_time: str,
    end_time: str,
    filters: Optional[List[Dict[str, Any]]] = None,
    forecast_periods: Optional[int] = None,
    confidence_interval: float = 0.95,
    seasonality_period: Optional[str] = None
):
    """Perform trend analysis on observability data"""
    try:
        if not bi_analytics_engine or not bi_analytics_engine.trend_analyzer:
            raise HTTPException(status_code=503, detail="Trend analyzer not available")
        
        # Parse datetime strings
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Create time range
        time_range = TimeRange(start_time=start_datetime, end_time=end_datetime)
        
        # Parse filters
        parsed_filters = []
        if filters:
            for f in filters:
                parsed_filters.append(DataFilter(
                    field=f['field'],
                    operator=f['operator'],
                    value=f['value']
                ))
        
        # Create trend analysis request
        trend_request = TrendAnalysisRequest(
            trend_type=TrendType(trend_type),
            time_range=time_range,
            metric_field=metric_field,
            data_sources=data_sources,
            filters=parsed_filters,
            forecast_periods=forecast_periods,
            confidence_interval=confidence_interval,
            seasonality_period=seasonality_period
        )
        
        # Analyze trend
        result = await bi_analytics_engine.trend_analyzer.analyze_trend(trend_request)
        
        return {
            'request_id': result.request_id,
            'trend_type': result.trend_type.value,
            'trend_direction': result.trend_direction,
            'trend_strength': result.trend_strength,
            'statistical_significance': result.statistical_significance,
            'correlation_coefficient': result.correlation_coefficient,
            'forecast_values': result.forecast_values,
            'anomalies_detected': result.anomalies_detected,
            'seasonal_patterns': result.seasonal_patterns,
            'model_accuracy': result.model_accuracy,
            'confidence_intervals': result.confidence_intervals
        }
        
    except Exception as e:
        logger.error("Trend analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

@mymiddleware.post("/analytics/ml/train/anomaly")
async def train_anomaly_model(
    model_name: str,
    data_sources: List[str],
    start_time: str,
    end_time: str,
    filters: Optional[List[Dict[str, Any]]] = None
):
    """Train an anomaly detection model"""
    try:
        if not ml_pipeline:
            raise HTTPException(status_code=503, detail="ML pipeline not available")
        
        # Parse datetime strings
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Get training data
        training_data = await data_warehouse_manager.query_observability_data(
            data_sources=data_sources,
            start_time=start_datetime,
            end_time=end_datetime,
            filters={f['field']: f['value'] for f in filters} if filters else None
        )
        
        # Train model
        result = await ml_pipeline.train_anomaly_detection_model(training_data, model_name)
        
        return result
        
    except Exception as e:
        logger.error("Anomaly model training failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

@mymiddleware.post("/analytics/ml/predict/anomaly")
async def predict_anomalies(
    model_name: str,
    data_sources: List[str],
    start_time: str,
    end_time: str,
    filters: Optional[List[Dict[str, Any]]] = None
):
    """Predict anomalies using trained model"""
    try:
        if not ml_pipeline:
            raise HTTPException(status_code=503, detail="ML pipeline not available")
        
        # Parse datetime strings
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Get prediction data
        prediction_data = await data_warehouse_manager.query_observability_data(
            data_sources=data_sources,
            start_time=start_datetime,
            end_time=end_datetime,
            filters={f['field']: f['value'] for f in filters} if filters else None
        )
        
        # Make predictions
        result = await ml_pipeline.predict_anomalies(prediction_data, model_name)
        
        return {
            'model_id': result.model_id,
            'model_type': result.model_type,
            'predictions': result.predictions,
            'confidence_scores': result.confidence_scores,
            'feature_importance': result.feature_importance,
            'model_accuracy': result.model_accuracy,
            'prediction_time_ms': result.prediction_time_ms
        }
        
    except Exception as e:
        logger.error("Anomaly prediction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Anomaly prediction failed: {str(e)}")

@mymiddleware.get("/analytics/statistics")
async def get_analytics_statistics():
    """Get comprehensive analytics statistics"""
    try:
        stats = {}
        
        if bi_analytics_engine:
            stats['analytics_engine'] = await bi_analytics_engine.get_analytics_statistics()
        
        if report_generator:
            stats['report_generator'] = await report_generator.get_report_statistics()
        
        if ml_pipeline:
            stats['ml_pipeline'] = await ml_pipeline.get_ml_statistics()
        
        if data_warehouse_manager:
            stats['data_warehouse'] = await data_warehouse_manager.get_warehouse_statistics()
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get analytics statistics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@mymiddleware.get("/analytics/health")
async def analytics_health_check():
    """Comprehensive health check for analytics components"""
    try:
        health_status = {}
        
        if bi_analytics_engine:
            health_status['analytics_engine'] = await bi_analytics_engine.health_check()
        
        if report_generator:
            health_status['report_generator'] = await report_generator.health_check()
        
        if ml_pipeline:
            health_status['ml_pipeline'] = await ml_pipeline.health_check()
        
        if data_warehouse_manager:
            health_status['data_warehouse'] = await data_warehouse_manager.health_check()
        
        # Overall status
        all_healthy = all(
            component.get('status') == 'healthy' 
            for component in health_status.values()
        )
        
        return {
            'overall_status': 'healthy' if all_healthy else 'degraded',
            'components': health_status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Analytics health check failed", error=str(e))
        return {
            'overall_status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

@mymiddleware.get("/deep-system/status")
async def deep_system_status():
    """Get deep system monitoring status"""
    try:
        if not deep_system_integration:
            raise HTTPException(status_code=503, detail="Deep system integration not available")
        
        return await deep_system_integration.get_monitoring_statistics()
        
    except Exception as e:
        logger.error("Failed to get deep system status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# Exception handlers
@mymiddleware.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", 
                path=request.url.path,
                method=request.method,
                error=str(exc))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if config.environment == "development" else "An error occurred"
        }
    )

if __name__ == '__main__':
    # Configure logging level
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level))
    
    # Run the application
    uvicorn.run(
        "main:mymiddleware",
        host=config.host,
        port=config.port,
        reload=config.environment == "development",
        log_level=log_level.lower(),
        workers=1 if config.environment == "development" else config.workers
    )