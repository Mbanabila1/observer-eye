"""
BI Analytics Engine

Advanced business intelligence and analytics capabilities for the Observer-Eye platform.
Provides statistical analysis, automated report generation, machine learning pipelines,
and predictive analytics for comprehensive observability insights.
"""

from .analytics_engine import BIAnalyticsEngine
from .report_generator import ReportGenerator
from .ml_pipeline import MachineLearningPipeline
from .data_warehouse import DataWarehouseManager
from .kpi_calculator import KPICalculator
from .trend_analyzer import TrendAnalyzer
from .models import (
    AnalyticsRequest, ReportRequest, KPIRequest, TrendAnalysisRequest,
    AnalyticsResult, ReportResult, KPIResult, TrendAnalysisResult,
    ReportFormat, ReportType, KPIType, TrendType, AnalyticsMetric,
    TimeRange, DataFilter, AggregationConfig, ScheduleConfig
)

__all__ = [
    'BIAnalyticsEngine',
    'ReportGenerator', 
    'MachineLearningPipeline',
    'DataWarehouseManager',
    'KPICalculator',
    'TrendAnalyzer',
    'AnalyticsRequest',
    'ReportRequest',
    'KPIRequest', 
    'TrendAnalysisRequest',
    'AnalyticsResult',
    'ReportResult',
    'KPIResult',
    'TrendAnalysisResult',
    'ReportFormat',
    'ReportType',
    'KPIType',
    'TrendType',
    'AnalyticsMetric',
    'TimeRange',
    'DataFilter',
    'AggregationConfig',
    'ScheduleConfig'
]