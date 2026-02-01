"""
Telemetry data models and structures.
Defines telemetry data types, processing results, and analysis models.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class TelemetryType(str, Enum):
    """Types of telemetry data"""
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    EVENT = "event"
    SPAN = "span"
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TelemetrySource(str, Enum):
    """Sources of telemetry data"""
    APPLICATION = "application"
    SYSTEM = "system"
    NETWORK = "network"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    USER = "user"
    EXTERNAL = "external"


class SeverityLevel(str, Enum):
    """Severity levels for telemetry data"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ProcessingStatus(str, Enum):
    """Processing status for telemetry data"""
    RECEIVED = "received"
    PROCESSING = "processing"
    ENRICHED = "enriched"
    CORRELATED = "correlated"
    ANALYZED = "analyzed"
    STORED = "stored"
    FAILED = "failed"


class TelemetryData(BaseModel):
    """Base telemetry data model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique telemetry ID")
    type: TelemetryType = Field(..., description="Type of telemetry data")
    source: TelemetrySource = Field(..., description="Source of telemetry data")
    timestamp: datetime = Field(..., description="Timestamp when data was generated")
    received_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when data was received")
    
    # Core data
    name: str = Field(..., description="Name or identifier of the telemetry")
    value: Union[str, int, float, Dict[str, Any], List[Any]] = Field(..., description="Telemetry value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    
    # Metadata
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value labels")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    
    # Context information
    service_name: Optional[str] = Field(None, description="Service that generated the telemetry")
    service_version: Optional[str] = Field(None, description="Version of the service")
    environment: Optional[str] = Field(None, description="Environment (dev, staging, prod)")
    host: Optional[str] = Field(None, description="Host that generated the telemetry")
    instance_id: Optional[str] = Field(None, description="Instance ID")
    
    # Tracing context
    trace_id: Optional[str] = Field(None, description="Trace ID for distributed tracing")
    span_id: Optional[str] = Field(None, description="Span ID")
    parent_span_id: Optional[str] = Field(None, description="Parent span ID")
    
    # User context
    user_id: Optional[str] = Field(None, description="User ID associated with the telemetry")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    # Quality indicators
    severity: SeverityLevel = Field(SeverityLevel.INFO, description="Severity level")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProcessedTelemetry(BaseModel):
    """Processed telemetry data with enrichment"""
    original_data: TelemetryData = Field(..., description="Original telemetry data")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    status: ProcessingStatus = Field(..., description="Processing status")
    
    # Enriched data
    enriched_attributes: Dict[str, Any] = Field(default_factory=dict, description="Enriched attributes")
    computed_metrics: Dict[str, float] = Field(default_factory=dict, description="Computed metrics")
    derived_labels: Dict[str, str] = Field(default_factory=dict, description="Derived labels")
    
    # Processing metadata
    processor_version: str = Field(..., description="Version of the processor")
    enrichment_sources: List[str] = Field(default_factory=list, description="Sources used for enrichment")
    processing_errors: List[str] = Field(default_factory=list, description="Processing errors")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    
    # Quality scores
    data_quality_score: float = Field(1.0, ge=0.0, le=1.0, description="Data quality score")
    completeness_score: float = Field(1.0, ge=0.0, le=1.0, description="Data completeness score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CorrelationRule(BaseModel):
    """Rule for correlating telemetry data"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Rule ID")
    name: str = Field(..., description="Rule name")
    description: str = Field("", description="Rule description")
    
    # Matching criteria
    source_types: List[TelemetryType] = Field(..., description="Source telemetry types to match")
    target_types: List[TelemetryType] = Field(..., description="Target telemetry types to correlate with")
    time_window_seconds: int = Field(300, description="Time window for correlation in seconds")
    
    # Correlation conditions
    match_fields: List[str] = Field(..., description="Fields that must match for correlation")
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Similarity threshold")
    
    # Rule configuration
    is_active: bool = Field(True, description="Whether the rule is active")
    priority: int = Field(1, description="Rule priority (higher number = higher priority)")
    max_correlations: int = Field(100, description="Maximum correlations per time window")


class CorrelationResult(BaseModel):
    """Result of telemetry correlation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Correlation ID")
    rule_id: str = Field(..., description="ID of the correlation rule used")
    primary_telemetry_id: str = Field(..., description="Primary telemetry data ID")
    correlated_telemetry_ids: List[str] = Field(..., description="Correlated telemetry data IDs")
    
    correlation_score: float = Field(..., ge=0.0, le=1.0, description="Correlation strength score")
    correlation_type: str = Field(..., description="Type of correlation found")
    correlation_reason: str = Field(..., description="Reason for correlation")
    
    # Timing information
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Correlation timestamp")
    time_span_seconds: float = Field(..., description="Time span of correlated events")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional correlation metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisPattern(BaseModel):
    """Pattern for telemetry analysis"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Pattern ID")
    name: str = Field(..., description="Pattern name")
    description: str = Field("", description="Pattern description")
    
    # Pattern definition
    pattern_type: str = Field(..., description="Type of pattern (anomaly, trend, threshold, etc.)")
    telemetry_types: List[TelemetryType] = Field(..., description="Telemetry types to analyze")
    analysis_window_seconds: int = Field(3600, description="Analysis time window in seconds")
    
    # Pattern parameters
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Pattern-specific parameters")
    thresholds: Dict[str, float] = Field(default_factory=dict, description="Threshold values")
    
    # Configuration
    is_active: bool = Field(True, description="Whether the pattern is active")
    sensitivity: float = Field(0.5, ge=0.0, le=1.0, description="Pattern sensitivity")
    min_data_points: int = Field(10, description="Minimum data points required for analysis")


class AnalysisResult(BaseModel):
    """Result of telemetry analysis"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Analysis ID")
    pattern_id: str = Field(..., description="ID of the analysis pattern used")
    telemetry_ids: List[str] = Field(..., description="Telemetry data IDs analyzed")
    
    # Analysis results
    pattern_detected: bool = Field(..., description="Whether the pattern was detected")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the analysis")
    severity: SeverityLevel = Field(..., description="Severity of the finding")
    
    # Details
    finding_type: str = Field(..., description="Type of finding")
    description: str = Field(..., description="Description of the finding")
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")
    
    # Timing and context
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    time_range_start: datetime = Field(..., description="Start of analyzed time range")
    time_range_end: datetime = Field(..., description="End of analyzed time range")
    
    # Statistical data
    statistics: Dict[str, float] = Field(default_factory=dict, description="Statistical measures")
    data_points_analyzed: int = Field(..., description="Number of data points analyzed")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional analysis metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TelemetryMetrics(BaseModel):
    """Metrics about telemetry processing"""
    # Ingestion metrics
    total_received: int = Field(0, description="Total telemetry data received")
    total_processed: int = Field(0, description="Total telemetry data processed")
    total_failed: int = Field(0, description="Total processing failures")
    
    # Processing metrics
    average_processing_time_ms: float = Field(0.0, description="Average processing time")
    max_processing_time_ms: float = Field(0.0, description="Maximum processing time")
    processing_rate_per_second: float = Field(0.0, description="Processing rate")
    
    # Quality metrics
    average_data_quality_score: float = Field(1.0, description="Average data quality score")
    average_completeness_score: float = Field(1.0, description="Average completeness score")
    
    # Correlation metrics
    total_correlations: int = Field(0, description="Total correlations found")
    correlation_success_rate: float = Field(0.0, description="Correlation success rate")
    
    # Analysis metrics
    total_analyses: int = Field(0, description="Total analyses performed")
    patterns_detected: int = Field(0, description="Total patterns detected")
    anomalies_detected: int = Field(0, description="Total anomalies detected")
    
    # Storage metrics
    total_stored: int = Field(0, description="Total telemetry data stored")
    storage_size_bytes: int = Field(0, description="Total storage size in bytes")
    
    # Time range
    metrics_start_time: datetime = Field(default_factory=datetime.utcnow, description="Metrics collection start time")
    metrics_end_time: datetime = Field(default_factory=datetime.utcnow, description="Metrics collection end time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TelemetryBatch(BaseModel):
    """Batch of telemetry data for bulk processing"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Batch ID")
    telemetry_data: List[TelemetryData] = Field(..., description="Telemetry data in the batch")
    batch_size: int = Field(..., description="Number of items in the batch")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Batch creation timestamp")
    
    # Batch metadata
    source_system: Optional[str] = Field(None, description="Source system for the batch")
    batch_type: Optional[str] = Field(None, description="Type of batch")
    priority: int = Field(1, description="Batch processing priority")
    
    @validator('batch_size', always=True)
    def validate_batch_size(cls, v, values):
        """Validate batch size matches telemetry data length"""
        telemetry_data = values.get('telemetry_data', [])
        if v != len(telemetry_data):
            raise ValueError("Batch size must match telemetry data length")
        return v


class TelemetryQuery(BaseModel):
    """Query for retrieving telemetry data"""
    # Time range
    start_time: Optional[datetime] = Field(None, description="Query start time")
    end_time: Optional[datetime] = Field(None, description="Query end time")
    
    # Filters
    telemetry_types: Optional[List[TelemetryType]] = Field(None, description="Filter by telemetry types")
    sources: Optional[List[TelemetrySource]] = Field(None, description="Filter by sources")
    service_names: Optional[List[str]] = Field(None, description="Filter by service names")
    severities: Optional[List[SeverityLevel]] = Field(None, description="Filter by severity levels")
    
    # Text search
    search_text: Optional[str] = Field(None, description="Text search in telemetry data")
    
    # Labels and attributes
    label_filters: Dict[str, str] = Field(default_factory=dict, description="Filter by labels")
    attribute_filters: Dict[str, Any] = Field(default_factory=dict, description="Filter by attributes")
    
    # Pagination and sorting
    limit: int = Field(100, ge=1, le=10000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Result offset")
    sort_by: str = Field("timestamp", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    
    # Aggregation
    aggregate_by: Optional[str] = Field(None, description="Field to aggregate by")
    aggregate_function: Optional[str] = Field(None, description="Aggregation function")


class TelemetryAlert(BaseModel):
    """Alert based on telemetry analysis"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Alert ID")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    
    # Alert details
    severity: SeverityLevel = Field(..., description="Alert severity")
    alert_type: str = Field(..., description="Type of alert")
    source_analysis_id: str = Field(..., description="ID of the analysis that triggered the alert")
    
    # Affected entities
    affected_services: List[str] = Field(default_factory=list, description="Affected services")
    affected_hosts: List[str] = Field(default_factory=list, description="Affected hosts")
    
    # Timing
    triggered_at: datetime = Field(default_factory=datetime.utcnow, description="Alert trigger timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Alert resolution timestamp")
    
    # Status
    status: str = Field("active", description="Alert status")
    acknowledged: bool = Field(False, description="Whether alert is acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="User who acknowledged the alert")
    
    # Actions
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    escalation_policy: Optional[str] = Field(None, description="Escalation policy")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional alert metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }