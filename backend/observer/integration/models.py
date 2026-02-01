import uuid
import json
from django.db import models
from django.core.validators import URLValidator
from django.contrib.postgres.fields import JSONField
from core.models import BaseModel, User


class ExternalSystem(BaseModel):
    """
    Model representing external systems that can be integrated with Observer Eye Platform.
    Supports various types of external systems like monitoring tools, databases, APIs, etc.
    """
    SYSTEM_TYPES = [
        ('api', 'REST API'),
        ('database', 'Database'),
        ('monitoring', 'Monitoring System'),
        ('logging', 'Logging System'),
        ('metrics', 'Metrics System'),
        ('alerting', 'Alerting System'),
        ('webhook', 'Webhook'),
        ('file_system', 'File System'),
        ('cloud_service', 'Cloud Service'),
        ('custom', 'Custom Integration'),
    ]
    
    AUTHENTICATION_TYPES = [
        ('none', 'No Authentication'),
        ('api_key', 'API Key'),
        ('bearer_token', 'Bearer Token'),
        ('basic_auth', 'Basic Authentication'),
        ('oauth2', 'OAuth 2.0'),
        ('custom', 'Custom Authentication'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    system_type = models.CharField(max_length=50, choices=SYSTEM_TYPES)
    base_url = models.URLField(blank=True, null=True)
    version = models.CharField(max_length=50, blank=True)
    
    # Authentication configuration
    auth_type = models.CharField(max_length=50, choices=AUTHENTICATION_TYPES, default='none')
    auth_config = models.JSONField(default=dict, help_text="Authentication configuration (encrypted)")
    
    # Connection settings
    timeout_seconds = models.PositiveIntegerField(default=30)
    retry_attempts = models.PositiveIntegerField(default=3)
    retry_delay_seconds = models.PositiveIntegerField(default=5)
    
    # Health check configuration
    health_check_url = models.URLField(blank=True, null=True)
    health_check_interval_minutes = models.PositiveIntegerField(default=5)
    last_health_check = models.DateTimeField(null=True, blank=True)
    is_healthy = models.BooleanField(default=True)
    
    # Metadata and configuration
    metadata = models.JSONField(default=dict)
    configuration = models.JSONField(default=dict)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_external_systems')
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modified_external_systems')
    
    class Meta:
        db_table = 'integration_external_system'
        indexes = [
            models.Index(fields=['system_type', 'is_active']),
            models.Index(fields=['is_healthy', 'last_health_check']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_system_type_display()})"


class DataConnector(BaseModel):
    """
    Model representing data connectors that define how to extract/import data from external systems.
    """
    CONNECTOR_TYPES = [
        ('pull', 'Pull Data (Import)'),
        ('push', 'Push Data (Export)'),
        ('bidirectional', 'Bidirectional'),
    ]
    
    DATA_FORMATS = [
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('csv', 'CSV'),
        ('yaml', 'YAML'),
        ('binary', 'Binary'),
        ('custom', 'Custom Format'),
    ]
    
    SYNC_FREQUENCIES = [
        ('realtime', 'Real-time'),
        ('continuous', 'Continuous'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('manual', 'Manual'),
    ]
    
    external_system = models.ForeignKey(ExternalSystem, on_delete=models.CASCADE, related_name='connectors')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    connector_type = models.CharField(max_length=20, choices=CONNECTOR_TYPES)
    
    # Data configuration
    data_format = models.CharField(max_length=20, choices=DATA_FORMATS, default='json')
    source_endpoint = models.CharField(max_length=500, blank=True)
    destination_endpoint = models.CharField(max_length=500, blank=True)
    
    # Synchronization settings
    sync_frequency = models.CharField(max_length=20, choices=SYNC_FREQUENCIES, default='manual')
    sync_schedule = models.JSONField(default=dict, help_text="Cron-like schedule configuration")
    
    # Data transformation
    transformation_rules = models.JSONField(default=list, help_text="Data transformation and mapping rules")
    validation_rules = models.JSONField(default=list, help_text="Data validation rules")
    
    # Filtering and processing
    filters = models.JSONField(default=dict, help_text="Data filtering criteria")
    batch_size = models.PositiveIntegerField(default=1000)
    
    # Status tracking
    is_enabled = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, default='pending')
    last_sync_message = models.TextField(blank=True)
    
    # Statistics
    total_records_processed = models.BigIntegerField(default=0)
    total_errors = models.BigIntegerField(default=0)
    
    class Meta:
        db_table = 'integration_data_connector'
        unique_together = ['external_system', 'name']
        indexes = [
            models.Index(fields=['connector_type', 'is_enabled']),
            models.Index(fields=['sync_frequency', 'last_sync']),
            models.Index(fields=['external_system', 'is_enabled']),
        ]
    
    def __str__(self):
        return f"{self.external_system.name} - {self.name}"


class DataImportExportJob(BaseModel):
    """
    Model tracking individual data import/export jobs and their execution status.
    """
    JOB_TYPES = [
        ('import', 'Data Import'),
        ('export', 'Data Export'),
        ('sync', 'Data Synchronization'),
    ]
    
    JOB_STATUSES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('retrying', 'Retrying'),
    ]
    
    connector = models.ForeignKey(DataConnector, on_delete=models.CASCADE, related_name='jobs')
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    status = models.CharField(max_length=20, choices=JOB_STATUSES, default='pending')
    
    # Execution details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Job configuration
    job_config = models.JSONField(default=dict)
    parameters = models.JSONField(default=dict)
    
    # Results and statistics
    records_processed = models.BigIntegerField(default=0)
    records_successful = models.BigIntegerField(default=0)
    records_failed = models.BigIntegerField(default=0)
    
    # Error handling
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Tracking
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'integration_data_import_export_job'
        indexes = [
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['connector', 'job_type', 'status']),
            models.Index(fields=['started_at', 'completed_at']),
        ]
    
    def __str__(self):
        return f"{self.get_job_type_display()} - {self.connector.name} ({self.status})"


class IntegrationEndpoint(BaseModel):
    """
    Model representing API endpoints exposed by the integration system for external systems to connect.
    Supports API versioning and backward compatibility.
    """
    ENDPOINT_TYPES = [
        ('webhook', 'Webhook Receiver'),
        ('api', 'REST API Endpoint'),
        ('graphql', 'GraphQL Endpoint'),
        ('websocket', 'WebSocket Endpoint'),
    ]
    
    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    endpoint_type = models.CharField(max_length=20, choices=ENDPOINT_TYPES)
    
    # URL configuration
    path = models.CharField(max_length=500)
    http_methods = models.JSONField(default=list, help_text="Allowed HTTP methods")
    
    # Versioning
    version = models.CharField(max_length=20, default='v1')
    is_deprecated = models.BooleanField(default=False)
    deprecation_date = models.DateTimeField(null=True, blank=True)
    replacement_endpoint = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Security and access control
    requires_authentication = models.BooleanField(default=True)
    allowed_systems = models.ManyToManyField(ExternalSystem, blank=True, related_name='allowed_endpoints')
    rate_limit_per_minute = models.PositiveIntegerField(default=60)
    
    # Request/Response configuration
    request_schema = models.JSONField(default=dict, help_text="JSON schema for request validation")
    response_schema = models.JSONField(default=dict, help_text="JSON schema for response format")
    
    # Monitoring
    is_enabled = models.BooleanField(default=True)
    total_requests = models.BigIntegerField(default=0)
    total_errors = models.BigIntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'integration_endpoint'
        unique_together = ['path', 'version']
        indexes = [
            models.Index(fields=['endpoint_type', 'is_enabled']),
            models.Index(fields=['version', 'is_deprecated']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.version})"


class IntegrationLog(BaseModel):
    """
    Model for logging integration activities, errors, and audit trail.
    """
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    ACTIVITY_TYPES = [
        ('connection', 'Connection'),
        ('data_transfer', 'Data Transfer'),
        ('authentication', 'Authentication'),
        ('validation', 'Validation'),
        ('transformation', 'Transformation'),
        ('error', 'Error'),
        ('system', 'System'),
    ]
    
    external_system = models.ForeignKey(ExternalSystem, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    connector = models.ForeignKey(DataConnector, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    job = models.ForeignKey(DataImportExportJob, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    endpoint = models.ForeignKey(IntegrationEndpoint, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    message = models.TextField()
    details = models.JSONField(default=dict)
    
    # Request/Response tracking
    request_id = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Performance metrics
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'integration_log'
        indexes = [
            models.Index(fields=['level', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['external_system', 'created_at']),
            models.Index(fields=['request_id']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.activity_type}: {self.message[:50]}..."


class ServiceDiscovery(BaseModel):
    """
    Model for service discovery and load balancing configuration.
    Supports horizontal scaling and service registration.
    """
    SERVICE_TYPES = [
        ('presentation', 'Presentation Layer'),
        ('logic', 'Logic Layer'),
        ('data', 'Data Layer'),
        ('external', 'External Service'),
    ]
    
    HEALTH_STATUSES = [
        ('healthy', 'Healthy'),
        ('unhealthy', 'Unhealthy'),
        ('unknown', 'Unknown'),
        ('maintenance', 'Maintenance'),
    ]
    
    service_name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    instance_id = models.CharField(max_length=255, unique=True)
    
    # Network configuration
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    protocol = models.CharField(max_length=10, default='http')
    base_path = models.CharField(max_length=255, default='/')
    
    # Service metadata
    version = models.CharField(max_length=50)
    environment = models.CharField(max_length=50, default='development')
    region = models.CharField(max_length=100, blank=True)
    availability_zone = models.CharField(max_length=100, blank=True)
    
    # Health and load balancing
    health_status = models.CharField(max_length=20, choices=HEALTH_STATUSES, default='unknown')
    health_check_url = models.CharField(max_length=500, blank=True)
    last_health_check = models.DateTimeField(null=True, blank=True)
    
    # Load balancing weights
    weight = models.PositiveIntegerField(default=100)
    max_connections = models.PositiveIntegerField(default=1000)
    current_connections = models.PositiveIntegerField(default=0)
    
    # Registration tracking
    registered_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integration_service_discovery'
        unique_together = ['service_name', 'instance_id']
        indexes = [
            models.Index(fields=['service_name', 'health_status']),
            models.Index(fields=['service_type', 'environment']),
            models.Index(fields=['last_heartbeat']),
        ]
    
    def __str__(self):
        return f"{self.service_name}:{self.instance_id} ({self.health_status})"
    
    @property
    def full_url(self):
        """Get the full URL for this service instance"""
        return f"{self.protocol}://{self.host}:{self.port}{self.base_path}"
