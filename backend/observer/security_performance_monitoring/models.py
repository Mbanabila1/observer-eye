"""
Security Performance Monitoring models for the Observer Eye Platform.
Monitors security-related performance metrics and threat detection.
"""

from django.db import models
from django.utils import timezone

from core.models import BaseModel


class SecurityMetric(BaseModel):
    """
    Security performance metrics.
    """
    metric_name = models.CharField(max_length=255, db_index=True)
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('threat_detection_time', 'Threat Detection Time'),
            ('vulnerability_scan_time', 'Vulnerability Scan Time'),
            ('security_alert_response_time', 'Security Alert Response Time'),
            ('firewall_rule_processing_time', 'Firewall Rule Processing Time'),
            ('intrusion_detection_latency', 'Intrusion Detection Latency'),
        ]
    )
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    target_resource = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'security_metric'
        indexes = [
            models.Index(fields=['metric_type', 'severity', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.metric_name} - {self.get_severity_display()}"


class SecurityIncident(BaseModel):
    """
    Security incident tracking for performance analysis.
    """
    incident_type = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    detection_time_ms = models.PositiveIntegerField(help_text="Time to detect the incident")
    response_time_ms = models.PositiveIntegerField(null=True, blank=True, help_text="Time to respond")
    resolution_time_ms = models.PositiveIntegerField(null=True, blank=True, help_text="Time to resolve")
    source_ip = models.GenericIPAddressField()
    target_resource = models.CharField(max_length=255)
    attack_vector = models.CharField(max_length=100, blank=True)
    is_resolved = models.BooleanField(default=False)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'security_incident'
        indexes = [
            models.Index(fields=['incident_type', 'severity']),
            models.Index(fields=['is_resolved', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.incident_type} - {self.get_severity_display()}"