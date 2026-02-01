"""
Analytics Performance Monitoring models for the Observer Eye Platform.
Monitors and tracks performance metrics related to analytics operations.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

from core.models import BaseModel, User


class AnalyticsPerformanceMetric(BaseModel):
    """
    Performance metrics for analytics operations.
    Tracks query execution times, data processing performance, etc.
    """
    operation_type = models.CharField(
        max_length=50,
        choices=[
            ('query_execution', 'Query Execution'),
            ('data_ingestion', 'Data Ingestion'),
            ('aggregation', 'Data Aggregation'),
            ('insight_generation', 'Insight Generation'),
            ('report_generation', 'Report Generation'),
            ('dashboard_rendering', 'Dashboard Rendering'),
        ]
    )
    operation_name = models.CharField(max_length=255, db_index=True)
    execution_time_ms = models.PositiveIntegerField(help_text="Execution time in milliseconds")
    memory_usage_mb = models.FloatField(null=True, blank=True, help_text="Memory usage in MB")
    cpu_usage_percent = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="CPU usage percentage"
    )
    data_volume_mb = models.FloatField(null=True, blank=True, help_text="Data volume processed in MB")
    record_count = models.PositiveIntegerField(null=True, blank=True, help_text="Number of records processed")
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, help_text="Additional performance metadata")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'analytics_performance_metric'
        indexes = [
            models.Index(fields=['operation_type', 'timestamp']),
            models.Index(fields=['operation_name', 'success']),
            models.Index(fields=['execution_time_ms']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.operation_name} ({self.execution_time_ms}ms)"


class AnalyticsQueryPerformance(BaseModel):
    """
    Detailed performance tracking for analytics queries.
    """
    query_id = models.CharField(max_length=255, db_index=True, help_text="Query identifier or hash")
    query_type = models.CharField(
        max_length=50,
        choices=[
            ('adhoc', 'Ad-hoc Query'),
            ('scheduled', 'Scheduled Query'),
            ('dashboard', 'Dashboard Query'),
            ('alert', 'Alert Query'),
        ]
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_source_count = models.PositiveIntegerField(default=1)
    time_range_hours = models.FloatField(help_text="Time range of query in hours")
    execution_time_ms = models.PositiveIntegerField()
    planning_time_ms = models.PositiveIntegerField(default=0)
    data_scan_mb = models.FloatField(help_text="Amount of data scanned in MB")
    result_size_mb = models.FloatField(help_text="Size of query results in MB")
    cache_hit = models.BooleanField(default=False)
    optimization_applied = models.JSONField(default=list, help_text="List of optimizations applied")
    performance_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Performance score (0-100)"
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'analytics_query_performance'
        indexes = [
            models.Index(fields=['query_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['performance_score']),
            models.Index(fields=['cache_hit', 'execution_time_ms']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Query {self.query_id} - {self.execution_time_ms}ms"


class AnalyticsResourceUsage(BaseModel):
    """
    Resource usage tracking for analytics operations.
    """
    resource_type = models.CharField(
        max_length=50,
        choices=[
            ('cpu', 'CPU'),
            ('memory', 'Memory'),
            ('disk_io', 'Disk I/O'),
            ('network_io', 'Network I/O'),
            ('database_connections', 'Database Connections'),
        ]
    )
    current_usage = models.FloatField()
    peak_usage = models.FloatField()
    average_usage = models.FloatField()
    usage_unit = models.CharField(max_length=20, help_text="Unit of measurement (%, MB, ops/sec, etc.)")
    threshold_warning = models.FloatField(null=True, blank=True)
    threshold_critical = models.FloatField(null=True, blank=True)
    alert_triggered = models.BooleanField(default=False)
    measurement_window_minutes = models.PositiveIntegerField(default=5)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'analytics_resource_usage'
        indexes = [
            models.Index(fields=['resource_type', 'timestamp']),
            models.Index(fields=['alert_triggered', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.resource_type}: {self.current_usage} {self.usage_unit}"


class AnalyticsPerformanceAlert(BaseModel):
    """
    Performance-based alerts for analytics operations.
    """
    alert_type = models.CharField(
        max_length=50,
        choices=[
            ('slow_query', 'Slow Query'),
            ('high_resource_usage', 'High Resource Usage'),
            ('failed_operation', 'Failed Operation'),
            ('performance_degradation', 'Performance Degradation'),
        ]
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    metric_name = models.CharField(max_length=255)
    threshold_value = models.FloatField()
    actual_value = models.FloatField()
    operation_details = models.JSONField(default=dict)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notification_sent = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'analytics_performance_alert'
        indexes = [
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['is_resolved', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()})"