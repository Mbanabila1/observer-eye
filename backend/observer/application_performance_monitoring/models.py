"""
Application Performance Monitoring models for the Observer Eye Platform.
Monitors application-level performance metrics and health indicators.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from core.models import BaseModel


class ApplicationService(BaseModel):
    """
    Represents an application service being monitored.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    service_type = models.CharField(
        max_length=50,
        choices=[
            ('web_service', 'Web Service'),
            ('api_service', 'API Service'),
            ('background_service', 'Background Service'),
            ('database_service', 'Database Service'),
            ('cache_service', 'Cache Service'),
            ('message_queue', 'Message Queue'),
        ]
    )
    version = models.CharField(max_length=50, blank=True)
    environment = models.CharField(
        max_length=50,
        choices=[
            ('development', 'Development'),
            ('staging', 'Staging'),
            ('production', 'Production'),
        ]
    )
    health_check_url = models.URLField(blank=True)
    is_monitored = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'application_service'
        indexes = [
            models.Index(fields=['service_type', 'environment']),
            models.Index(fields=['is_monitored']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.environment})"


class ApplicationMetric(BaseModel):
    """
    Application performance metrics.
    """
    service = models.ForeignKey(ApplicationService, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=255, db_index=True)
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('response_time', 'Response Time'),
            ('throughput', 'Throughput'),
            ('error_rate', 'Error Rate'),
            ('cpu_usage', 'CPU Usage'),
            ('memory_usage', 'Memory Usage'),
            ('disk_usage', 'Disk Usage'),
            ('network_io', 'Network I/O'),
            ('database_connections', 'Database Connections'),
            ('custom', 'Custom Metric'),
        ]
    )
    value = models.FloatField()
    unit = models.CharField(max_length=20, help_text="Unit of measurement")
    tags = models.JSONField(default=dict, help_text="Additional metric tags")
    timestamp = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'application_metric'
        indexes = [
            models.Index(fields=['service', 'metric_name', 'timestamp']),
            models.Index(fields=['metric_type', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.service.name} - {self.metric_name}: {self.value} {self.unit}"


class ApplicationHealthCheck(BaseModel):
    """
    Application health check results.
    """
    service = models.ForeignKey(ApplicationService, on_delete=models.CASCADE, related_name='health_checks')
    status = models.CharField(
        max_length=20,
        choices=[
            ('healthy', 'Healthy'),
            ('degraded', 'Degraded'),
            ('unhealthy', 'Unhealthy'),
            ('unknown', 'Unknown'),
        ]
    )
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    details = models.JSONField(default=dict, help_text="Additional health check details")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'application_health_check'
        indexes = [
            models.Index(fields=['service', 'status', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.service.name} - {self.get_status_display()}"


class ApplicationError(BaseModel):
    """
    Application error tracking.
    """
    service = models.ForeignKey(ApplicationService, on_delete=models.CASCADE, related_name='errors')
    error_type = models.CharField(max_length=100, db_index=True)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_id = models.CharField(max_length=255, blank=True)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    count = models.PositiveIntegerField(default=1)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'application_error'
        indexes = [
            models.Index(fields=['service', 'error_type']),
            models.Index(fields=['severity', 'is_resolved']),
            models.Index(fields=['last_seen']),
        ]
        ordering = ['-last_seen']
    
    def __str__(self):
        return f"{self.service.name} - {self.error_type}"