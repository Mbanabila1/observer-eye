"""
Traffic Performance Monitoring models for the Observer Eye Platform.
Monitors network traffic performance and bandwidth utilization.
"""

from django.db import models
from django.utils import timezone

from core.models import BaseModel


class TrafficMetric(BaseModel):
    """
    Network traffic performance metrics.
    """
    interface_name = models.CharField(max_length=100, db_index=True)
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('bandwidth_utilization', 'Bandwidth Utilization'),
            ('packet_loss_rate', 'Packet Loss Rate'),
            ('latency', 'Network Latency'),
            ('throughput', 'Network Throughput'),
            ('connection_count', 'Active Connections'),
        ]
    )
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    direction = models.CharField(
        max_length=20,
        choices=[
            ('inbound', 'Inbound'),
            ('outbound', 'Outbound'),
            ('bidirectional', 'Bidirectional'),
        ]
    )
    protocol = models.CharField(max_length=20, blank=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    destination_ip = models.GenericIPAddressField(null=True, blank=True)
    port = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'traffic_metric'
        indexes = [
            models.Index(fields=['interface_name', 'metric_type', 'timestamp']),
            models.Index(fields=['protocol', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.interface_name} - {self.metric_type}: {self.value} {self.unit}"


class TrafficFlow(BaseModel):
    """
    Network traffic flow analysis.
    """
    flow_id = models.CharField(max_length=255, unique=True, db_index=True)
    source_ip = models.GenericIPAddressField()
    destination_ip = models.GenericIPAddressField()
    source_port = models.PositiveIntegerField()
    destination_port = models.PositiveIntegerField()
    protocol = models.CharField(max_length=20)
    bytes_sent = models.BigIntegerField(default=0)
    bytes_received = models.BigIntegerField(default=0)
    packets_sent = models.PositiveIntegerField(default=0)
    packets_received = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'traffic_flow'
        indexes = [
            models.Index(fields=['source_ip', 'destination_ip']),
            models.Index(fields=['protocol', 'start_time']),
            models.Index(fields=['is_active', 'start_time']),
        ]
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.source_ip}:{self.source_port} -> {self.destination_ip}:{self.destination_port}"