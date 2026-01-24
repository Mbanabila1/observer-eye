"""
BI Analytics Data Models

Defines the data models and enums for the BI analytics engine.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime
import uuid

class ReportFormat(Enum):
    """Report output formats"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    POWERPOINT = "powerpoint"

class ReportType(Enum):
    """Types of reports"""
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CUSTOM = "custom"

class KPIType(Enum):
    """Key Performance Indicator types"""
    AVAILABILITY = "availability"
    PERFORMANCE = "performance"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    RESOURCE_UTILIZATION = "resource_utilization"
    SECURITY_SCORE = "security_score"
    COMPLIANCE_SCORE = "compliance_score"
    CUSTOM = "custom"

class TrendType(Enum):
    """Trend analysis types"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"
    ANOMALY_DETECTION = "anomaly_detection"
    FORECAST = "forecast"

class AnalyticsMetric(Enum):
    """Analytics metrics"""
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    STANDARD_DEVIATION = "standard_deviation"
    VARIANCE = "variance"
    PERCENTILE_95 = "percentile_95"
    PERCENTILE_99 = "percentile_99"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    SUM = "sum"
    CORRELATION = "correlation"
    REGRESSION = "regression"

class ScheduleFrequency(Enum):
    """Report scheduling frequencies"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ON_DEMAND = "on_demand"

@dataclass
class TimeRange:
    """Time range for analytics queries"""
    start_time: datetime
    end_time: datetime
    timezone: Optional[str] = "UTC"
    
    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def duration_hours(self) -> float:
        return self.duration_seconds / 3600
    
    @property
    def duration_days(self) -> float:
        return self.duration_hours / 24

@dataclass
class DataFilter:
    """Data filtering criteria"""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, not_in, contains, regex
    value: Union[str, int, float, List[Any]]
    case_sensitive: bool = True

@dataclass
class AggregationConfig:
    """Configuration for data aggregation"""
    field: str
    function: AnalyticsMetric
    group_by: Optional[List[str]] = None
    having_filter: Optional[DataFilter] = None

@dataclass
class AnalyticsRequest:
    """Request for analytics processing"""
    time_range: TimeRange
    data_sources: List[str]  # pillar types or specific data sources
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filters: List[DataFilter] = field(default_factory=list)
    aggregations: List[AggregationConfig] = field(default_factory=list)
    metrics: List[AnalyticsMetric] = field(default_factory=list)
    group_by: Optional[List[str]] = None
    limit: Optional[int] = None
    include_metadata: bool = True

@dataclass
class ReportRequest:
    """Request for report generation"""
    report_type: ReportType
    report_format: ReportFormat
    title: str
    analytics_request: AnalyticsRequest
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    template_id: Optional[str] = None
    custom_sections: List[Dict[str, Any]] = field(default_factory=list)
    include_charts: bool = True
    include_tables: bool = True
    include_executive_summary: bool = True
    branding: Optional[Dict[str, Any]] = None

@dataclass
class KPIRequest:
    """Request for KPI calculation"""
    kpi_type: KPIType
    kpi_name: str
    time_range: TimeRange
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    calculation_formula: Optional[str] = None
    data_sources: List[str] = field(default_factory=list)
    filters: List[DataFilter] = field(default_factory=list)

@dataclass
class TrendAnalysisRequest:
    """Request for trend analysis"""
    trend_type: TrendType
    time_range: TimeRange
    metric_field: str
    data_sources: List[str]
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filters: List[DataFilter] = field(default_factory=list)
    forecast_periods: Optional[int] = None
    confidence_interval: float = 0.95
    seasonality_period: Optional[str] = None  # daily, weekly, monthly, yearly

@dataclass
class ScheduleConfig:
    """Configuration for scheduled reports"""
    frequency: ScheduleFrequency
    start_date: datetime
    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    end_date: Optional[datetime] = None
    time_of_day: Optional[str] = None  # HH:MM format
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    day_of_month: Optional[int] = None  # 1-31
    timezone: str = "UTC"
    is_active: bool = True
    recipients: List[str] = field(default_factory=list)
    delivery_method: str = "email"  # email, webhook, file_system

@dataclass
class AnalyticsResult:
    """Result of analytics processing"""
    request_id: str
    status: str  # success, error, partial
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_time_ms: float
    row_count: int
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ReportResult:
    """Result of report generation"""
    request_id: str
    report_id: str
    status: str  # success, error, partial
    report_format: ReportFormat
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    analytics_result: Optional[AnalyticsResult] = None
    generation_time_ms: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class KPIResult:
    """Result of KPI calculation"""
    request_id: str
    kpi_name: str
    kpi_type: KPIType
    current_value: float
    target_value: Optional[float] = None
    variance_from_target: Optional[float] = None
    status: str = "normal"  # normal, warning, critical
    trend_direction: Optional[str] = None  # up, down, stable
    trend_percentage: Optional[float] = None
    historical_values: List[Dict[str, Any]] = field(default_factory=list)
    calculation_details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TrendAnalysisResult:
    """Result of trend analysis"""
    request_id: str
    trend_type: TrendType
    trend_direction: str  # increasing, decreasing, stable, volatile
    trend_strength: float  # 0.0 to 1.0
    statistical_significance: float  # p-value
    correlation_coefficient: Optional[float] = None
    forecast_values: List[Dict[str, Any]] = field(default_factory=list)
    anomalies_detected: List[Dict[str, Any]] = field(default_factory=list)
    seasonal_patterns: Dict[str, Any] = field(default_factory=dict)
    model_accuracy: Optional[float] = None
    confidence_intervals: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class MLModelResult:
    """Result of machine learning model execution"""
    model_id: str
    model_type: str
    predictions: List[Dict[str, Any]]
    confidence_scores: List[float]
    feature_importance: Dict[str, float]
    model_accuracy: float
    training_data_size: int
    prediction_time_ms: float
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DataQualityMetrics:
    """Data quality assessment metrics"""
    completeness: float  # 0.0 to 1.0
    accuracy: float  # 0.0 to 1.0
    consistency: float  # 0.0 to 1.0
    timeliness: float  # 0.0 to 1.0
    validity: float  # 0.0 to 1.0
    uniqueness: float  # 0.0 to 1.0
    overall_score: float  # 0.0 to 1.0
    issues_detected: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)