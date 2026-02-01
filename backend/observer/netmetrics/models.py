"""
Network Metrics models for the Observer Eye Platform.
Collects and stores network-level metrics and performance data.
"""

from django.db import models
from django.utils import timezone

from core.models import BaseModel


class NetworkInterface(BaseModel):
    """
    Represents a network interface being monitored.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    interface_type = models.CharField(
        max_length=50,
        choices=[
            ('ethernet', 'Ethernet'),
            ('wifi', 'WiFi'),
            ('loopback', 'Loopback'),
            ('vpn', 'VPN'),
            ('bridge', 'Bridge'),
            ('virtual', 'Virtual'),
        ]
    )
    mac_address = models.CharField(max_length=17, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    subnet_mask = models.GenericIPAddressField(null=True, blank=True)
    gateway = models.GenericIPAddressField(null=True, blank=True)
    mtu = models.PositiveIntegerField(null=True, blank=True)
    speed_mbps = models.PositiveIntegerField(null=True, blank=True, help_text="Interface speed in Mbps")
    is_up = models.BooleanField(default=True)
    is_monitored = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'network_interface'
        indexes = [
            models.Index(fields=['interface_type', 'is_monitored']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class NetworkMetricData(BaseModel):
    """
    Network metrics data collection.
    """
    interface = models.ForeignKey(NetworkInterface, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=255, db_index=True)
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('bytes_sent', 'Bytes Sent'),
            ('bytes_received', 'Bytes Received'),
            ('packets_sent', 'Packets Sent'),
            ('packets_received', 'Packets Received'),
            ('errors_in', 'Input Errors'),
            ('errors_out', 'Output Errors'),
            ('drops_in', 'Input Drops'),
            ('drops_out', 'Output Drops'),
            ('bandwidth_utilization', 'Bandwidth Utilization'),
            ('latency', 'Network Latency'),
            ('jitter', 'Network Jitter'),
            ('packet_loss', 'Packet Loss'),
        ]
    )
    value = models.BigIntegerField()
    unit = models.CharField(max_length=20)
    direction = models.CharField(
        max_length=20,
        choices=[
            ('inbound', 'Inbound'),
            ('outbound', 'Outbound'),
            ('bidirectional', 'Bidirectional'),
        ]
    )
    timestamp = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'network_metric_data'
        indexes = [
            models.Index(fields=['interface', 'metric_name', 'timestamp']),
            models.Index(fields=['metric_type', 'direction', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.interface.name} - {self.metric_name}: {self.value} {self.unit}"


class NetworkConnection(BaseModel):
    """
    Active network connections tracking.
    """
    local_address = models.GenericIPAddressField()
    local_port = models.PositiveIntegerField()
    remote_address = models.GenericIPAddressField()
    remote_port = models.PositiveIntegerField()
    protocol = models.CharField(
        max_length=10,
        choices=[
            ('TCP', 'TCP'),
            ('UDP', 'UDP'),
            ('ICMP', 'ICMP'),
        ]
    )
    state = models.CharField(
        max_length=20,
        choices=[
            ('ESTABLISHED', 'Established'),
            ('LISTEN', 'Listen'),
            ('TIME_WAIT', 'Time Wait'),
            ('CLOSE_WAIT', 'Close Wait'),
            ('SYN_SENT', 'SYN Sent'),
            ('SYN_RECV', 'SYN Received'),
            ('CLOSED', 'Closed'),
        ]
    )
    process_id = models.PositiveIntegerField(null=True, blank=True)
    process_name = models.CharField(max_length=255, blank=True)
    bytes_sent = models.BigIntegerField(default=0)
    bytes_received = models.BigIntegerField(default=0)
    established_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'network_connection'
        indexes = [
            models.Index(fields=['protocol', 'state']),
            models.Index(fields=['local_address', 'local_port']),
            models.Index(fields=['remote_address', 'remote_port']),
            models.Index(fields=['is_active', 'last_activity']),
        ]
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.local_address}:{self.local_port} -> {self.remote_address}:{self.remote_port} ({self.protocol})"


class NetworkLatencyTest(BaseModel):
    """
    Network latency test results.
    """
    target_host = models.CharField(max_length=255, db_index=True)
    target_ip = models.GenericIPAddressField()
    test_type = models.CharField(
        max_length=20,
        choices=[
            ('ping', 'ICMP Ping'),
            ('tcp_connect', 'TCP Connect'),
            ('http_get', 'HTTP GET'),
            ('dns_lookup', 'DNS Lookup'),
        ]
    )
    latency_ms = models.FloatField(help_text="Latency in milliseconds")
    packet_loss_percent = models.FloatField(default=0.0)
    jitter_ms = models.FloatField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    test_duration_ms = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'network_latency_test'
        indexes = [
            models.Index(fields=['target_host', 'test_type', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.target_host} - {self.latency_ms}ms ({self.test_type})"


class NetworkBandwidthTest(BaseModel):
    """
    Network bandwidth test results.
    """
    test_server = models.CharField(max_length=255)
    test_type = models.CharField(
        max_length=20,
        choices=[
            ('download', 'Download'),
            ('upload', 'Upload'),
            ('bidirectional', 'Bidirectional'),
        ]
    )
    bandwidth_mbps = models.FloatField(help_text="Bandwidth in Mbps")
    data_transferred_mb = models.FloatField(help_text="Data transferred in MB")
    test_duration_seconds = models.PositiveIntegerField()
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'network_bandwidth_test'
        indexes = [
            models.Index(fields=['test_server', 'test_type', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.test_server} - {self.bandwidth_mbps} Mbps ({self.test_type})"