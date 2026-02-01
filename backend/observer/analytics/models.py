"""
Analytics models for the Observer Eye Platform.
Provides data models for business intelligence and analytics capabilities.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
import json

from core.models import BaseModel, User


class DataSource(BaseModel):
    """
    Represents a data source for analytics.
    Can be internal systems, external APIs, or file uploads.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('internal', 'Internal System'),
            ('api', 'External API'),
            ('file', 'File Upload'),
            ('database', 'Database Connection'),
            ('stream', 'Real-time Stream'),
        ]
    )
    connection_config = models.JSONField(default=dict, help_text="Configuration for connecting to the data source")
    schema_definition = models.JSONField(default=dict, help_text="Schema definition for data validation")
    is_enabled = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_frequency = models.CharField(
        max_length=20,
        choices=[
            ('realtime', 'Real-time'),
            ('minute', 'Every Minute'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('manual', 'Manual'),
        ],
        default='hourly'
    )
    
    class Meta:
        db_table = 'analytics_data_source'
        indexes = [
            models.Index(fields=['source_type', 'is_enabled']),
            models.Index(fields=['last_sync']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class AnalyticsData(BaseModel):
    """
    Core analytics data model for storing processed metrics and events.
    Supports flexible schema for different types of analytics data.
    """
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='analytics_data')
    metric_name = models.CharField(max_length=255, db_index=True)
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('counter', 'Counter'),
            ('gauge', 'Gauge'),
            ('histogram', 'Histogram'),
            ('summary', 'Summary'),
            ('event', 'Event'),
        ]
    )
    metric_value = models.JSONField(help_text="Flexible storage for metric values")
    dimensions = models.JSONField(default=dict, help_text="Dimensional data for grouping and filtering")
    tags = models.JSONField(default=dict, help_text="Additional metadata tags")
    timestamp = models.DateTimeField(db_index=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # Computed fields for common queries
    numeric_value = models.FloatField(null=True, blank=True, db_index=True, help_text="Extracted numeric value for aggregations")
    string_value = models.CharField(max_length=500, blank=True, db_index=True, help_text="Extracted string value for grouping")
    
    class Meta:
        db_table = 'analytics_data'
        indexes = [
            models.Index(fields=['data_source', 'metric_name', 'timestamp']),
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['timestamp', 'numeric_value']),
            models.Index(fields=['metric_name', 'string_value']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """Extract common values for indexing."""
        if isinstance(self.metric_value, (int, float)):
            self.numeric_value = float(self.metric_value)
        elif isinstance(self.metric_value, dict) and 'value' in self.metric_value:
            try:
                self.numeric_value = float(self.metric_value['value'])
            except (ValueError, TypeError):
                pass
        
        if isinstance(self.metric_value, str):
            self.string_value = self.metric_value[:500]
        elif isinstance(self.metric_value, dict) and 'label' in self.metric_value:
            self.string_value = str(self.metric_value['label'])[:500]
        
        super().save(*args, **kwargs)


class AnalyticsQuery(BaseModel):
    """
    Stored analytics queries for reusable analysis.
    Supports complex aggregations and filtering.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_queries')
    query_definition = models.JSONField(help_text="Query definition including filters, aggregations, and grouping")
    data_sources = models.ManyToManyField(DataSource, related_name='queries')
    is_public = models.BooleanField(default=False)
    execution_count = models.PositiveIntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    average_execution_time = models.FloatField(null=True, blank=True, help_text="Average execution time in seconds")
    
    class Meta:
        db_table = 'analytics_query'
        indexes = [
            models.Index(fields=['created_by', 'is_public']),
            models.Index(fields=['last_executed']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.created_by.email}"


class AnalyticsReport(BaseModel):
    """
    Generated analytics reports with cached results.
    Supports scheduled generation and sharing.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_reports')
    query = models.ForeignKey(AnalyticsQuery, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('summary', 'Summary Report'),
            ('detailed', 'Detailed Report'),
            ('trend', 'Trend Analysis'),
            ('comparison', 'Comparison Report'),
            ('custom', 'Custom Report'),
        ]
    )
    parameters = models.JSONField(default=dict, help_text="Report parameters and filters")
    results = models.JSONField(default=dict, help_text="Cached report results")
    generated_at = models.DateTimeField(null=True, blank=True)
    generation_time = models.FloatField(null=True, blank=True, help_text="Generation time in seconds")
    is_scheduled = models.BooleanField(default=False)
    schedule_config = models.JSONField(default=dict, help_text="Scheduling configuration")
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_reports')
    
    class Meta:
        db_table = 'analytics_report'
        indexes = [
            models.Index(fields=['created_by', 'report_type']),
            models.Index(fields=['generated_at']),
            models.Index(fields=['is_scheduled']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"


class AnalyticsDashboard(BaseModel):
    """
    Analytics dashboards containing multiple visualizations.
    Supports real-time updates and interactive filtering.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_dashboards')
    layout_config = models.JSONField(default=dict, help_text="Dashboard layout configuration")
    widgets = models.JSONField(default=list, help_text="Dashboard widgets configuration")
    filters = models.JSONField(default=dict, help_text="Global dashboard filters")
    refresh_interval = models.PositiveIntegerField(default=300, help_text="Refresh interval in seconds")
    is_public = models.BooleanField(default=False)
    is_realtime = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_dashboards')
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_dashboard'
        indexes = [
            models.Index(fields=['created_by', 'is_public']),
            models.Index(fields=['last_viewed']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.created_by.email}"


class AnalyticsAlert(BaseModel):
    """
    Analytics-based alerts and notifications.
    Monitors metrics and triggers alerts based on conditions.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_alerts')
    query = models.ForeignKey(AnalyticsQuery, on_delete=models.CASCADE, related_name='alerts')
    condition = models.JSONField(help_text="Alert condition definition")
    threshold_value = models.FloatField()
    comparison_operator = models.CharField(
        max_length=10,
        choices=[
            ('gt', 'Greater Than'),
            ('gte', 'Greater Than or Equal'),
            ('lt', 'Less Than'),
            ('lte', 'Less Than or Equal'),
            ('eq', 'Equal'),
            ('ne', 'Not Equal'),
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
    notification_channels = models.JSONField(default=list, help_text="Notification channels configuration")
    is_enabled = models.BooleanField(default=True)
    check_frequency = models.PositiveIntegerField(default=300, help_text="Check frequency in seconds")
    last_checked = models.DateTimeField(null=True, blank=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'analytics_alert'
        indexes = [
            models.Index(fields=['is_enabled', 'last_checked']),
            models.Index(fields=['severity', 'last_triggered']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_severity_display()}"


class AnalyticsAggregation(BaseModel):
    """
    Pre-computed aggregations for faster query performance.
    Supports various time windows and grouping dimensions.
    """
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='aggregations')
    metric_name = models.CharField(max_length=255, db_index=True)
    aggregation_type = models.CharField(
        max_length=20,
        choices=[
            ('sum', 'Sum'),
            ('avg', 'Average'),
            ('min', 'Minimum'),
            ('max', 'Maximum'),
            ('count', 'Count'),
            ('stddev', 'Standard Deviation'),
            ('percentile', 'Percentile'),
        ]
    )
    time_window = models.CharField(
        max_length=20,
        choices=[
            ('1m', '1 Minute'),
            ('5m', '5 Minutes'),
            ('15m', '15 Minutes'),
            ('1h', '1 Hour'),
            ('6h', '6 Hours'),
            ('1d', '1 Day'),
            ('1w', '1 Week'),
            ('1M', '1 Month'),
        ]
    )
    dimensions = models.JSONField(default=dict, help_text="Grouping dimensions")
    aggregated_value = models.FloatField()
    sample_count = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField(db_index=True)
    window_end = models.DateTimeField(db_index=True)
    computed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_aggregation'
        indexes = [
            models.Index(fields=['data_source', 'metric_name', 'time_window', 'window_start']),
            models.Index(fields=['aggregation_type', 'window_start']),
        ]
        unique_together = [
            ['data_source', 'metric_name', 'aggregation_type', 'time_window', 'dimensions', 'window_start']
        ]
    
    def __str__(self):
        return f"{self.metric_name} {self.aggregation_type} ({self.time_window}): {self.aggregated_value}"


class AnalyticsInsight(BaseModel):
    """
    AI-generated insights and anomaly detection results.
    Provides automated analysis and recommendations.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    insight_type = models.CharField(
        max_length=50,
        choices=[
            ('anomaly', 'Anomaly Detection'),
            ('trend', 'Trend Analysis'),
            ('correlation', 'Correlation Analysis'),
            ('forecast', 'Forecast'),
            ('recommendation', 'Recommendation'),
        ]
    )
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='insights')
    metric_names = models.JSONField(default=list, help_text="List of metric names")
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score between 0 and 1"
    )
    impact_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Impact score between 0 and 1"
    )
    time_range = models.JSONField(help_text="Time range for the insight")
    analysis_data = models.JSONField(default=dict, help_text="Detailed analysis data and evidence")
    recommendations = models.JSONField(default=list, help_text="Actionable recommendations")
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_insights')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_insight'
        indexes = [
            models.Index(fields=['insight_type', 'confidence_score']),
            models.Index(fields=['is_acknowledged', 'created_at']),
        ]
        ordering = ['-confidence_score', '-impact_score', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_insight_type_display()}) - {self.confidence_score:.2f}"
