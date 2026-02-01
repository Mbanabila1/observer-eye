"""
Application Metrics models for the Observer Eye Platform.
Collects and stores application-level metrics and performance data.
"""

from django.db import models
from django.utils import timezone

from core.models import BaseModel


class ApplicationInstance(BaseModel):
    """
    Represents an application instance being monitored.
    """
    name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=50, blank=True)
    environment = models.CharField(
        max_length=50,
        choices=[
            ('development', 'Development'),
            ('staging', 'Staging'),
            ('production', 'Production'),
        ]
    )
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField(null=True, blank=True)
    process_id = models.PositiveIntegerField(null=True, blank=True)
    start_time = models.DateTimeField()
    last_heartbeat = models.DateTimeField(auto_now=True)
    is_running = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'application_instance'
        indexes = [
            models.Index(fields=['name', 'environment']),
            models.Index(fields=['is_running', 'last_heartbeat']),
        ]
        unique_together = [['name', 'host', 'port']]
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"


class ApplicationMetricData(BaseModel):
    """
    Application metrics data collection.
    """
    instance = models.ForeignKey(ApplicationInstance, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=255, db_index=True)
    metric_category = models.CharField(
        max_length=50,
        choices=[
            ('performance', 'Performance'),
            ('resource', 'Resource Usage'),
            ('business', 'Business Logic'),
            ('error', 'Error Tracking'),
            ('custom', 'Custom Metric'),
        ]
    )
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    tags = models.JSONField(default=dict, help_text="Additional metric tags")
    timestamp = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'application_metric_data'
        indexes = [
            models.Index(fields=['instance', 'metric_name', 'timestamp']),
            models.Index(fields=['metric_category', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.instance.name} - {self.metric_name}: {self.value} {self.unit}"


class ApplicationCounter(BaseModel):
    """
    Application counter metrics (monotonically increasing values).
    """
    instance = models.ForeignKey(ApplicationInstance, on_delete=models.CASCADE, related_name='counters')
    counter_name = models.CharField(max_length=255, db_index=True)
    counter_value = models.BigIntegerField(default=0)
    increment_value = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'application_counter'
        indexes = [
            models.Index(fields=['instance', 'counter_name']),
        ]
        unique_together = [['instance', 'counter_name']]
    
    def __str__(self):
        return f"{self.instance.name} - {self.counter_name}: {self.counter_value}"


class ApplicationGauge(BaseModel):
    """
    Application gauge metrics (values that can go up and down).
    """
    instance = models.ForeignKey(ApplicationInstance, on_delete=models.CASCADE, related_name='gauges')
    gauge_name = models.CharField(max_length=255, db_index=True)
    current_value = models.FloatField()
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'application_gauge'
        indexes = [
            models.Index(fields=['instance', 'gauge_name']),
        ]
        unique_together = [['instance', 'gauge_name']]
    
    def __str__(self):
        return f"{self.instance.name} - {self.gauge_name}: {self.current_value} {self.unit}"


class ApplicationHistogram(BaseModel):
    """
    Application histogram metrics for tracking distributions.
    """
    instance = models.ForeignKey(ApplicationInstance, on_delete=models.CASCADE, related_name='histograms')
    histogram_name = models.CharField(max_length=255, db_index=True)
    bucket_boundaries = models.JSONField(help_text="List of bucket boundaries")
    bucket_counts = models.JSONField(help_text="Count for each bucket")
    total_count = models.PositiveIntegerField(default=0)
    sum_value = models.FloatField(default=0.0)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'application_histogram'
        indexes = [
            models.Index(fields=['instance', 'histogram_name']),
        ]
        unique_together = [['instance', 'histogram_name']]
    
    def __str__(self):
        return f"{self.instance.name} - {self.histogram_name} (count: {self.total_count})"


class ApplicationEvent(BaseModel):
    """
    Application events and custom business logic tracking.
    """
    instance = models.ForeignKey(ApplicationInstance, on_delete=models.CASCADE, related_name='events')
    event_name = models.CharField(max_length=255, db_index=True)
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('user_action', 'User Action'),
            ('system_event', 'System Event'),
            ('business_event', 'Business Event'),
            ('error_event', 'Error Event'),
            ('custom_event', 'Custom Event'),
        ]
    )
    event_data = models.JSONField(default=dict)
    user_id = models.CharField(max_length=255, blank=True)
    session_id = models.CharField(max_length=255, blank=True)
    correlation_id = models.CharField(max_length=255, blank=True)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('debug', 'Debug'),
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('critical', 'Critical'),
        ],
        default='info'
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'application_event'
        indexes = [
            models.Index(fields=['instance', 'event_name', 'timestamp']),
            models.Index(fields=['event_type', 'severity', 'timestamp']),
            models.Index(fields=['user_id', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.instance.name} - {self.event_name}"