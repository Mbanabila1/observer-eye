from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    ExternalSystem, DataConnector, DataImportExportJob, 
    IntegrationEndpoint, IntegrationLog, ServiceDiscovery
)


@admin.register(ExternalSystem)
class ExternalSystemAdmin(admin.ModelAdmin):
    list_display = ['name', 'system_type', 'is_healthy', 'last_health_check', 'is_active', 'created_at']
    list_filter = ['system_type', 'auth_type', 'is_healthy', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'base_url']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_health_check']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'system_type', 'version')
        }),
        ('Connection Settings', {
            'fields': ('base_url', 'timeout_seconds', 'retry_attempts', 'retry_delay_seconds')
        }),
        ('Authentication', {
            'fields': ('auth_type', 'auth_config'),
            'classes': ('collapse',)
        }),
        ('Health Monitoring', {
            'fields': ('health_check_url', 'health_check_interval_minutes', 'last_health_check', 'is_healthy')
        }),
        ('Configuration', {
            'fields': ('metadata', 'configuration'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('created_by', 'last_modified_by', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'last_modified_by')


@admin.register(DataConnector)
class DataConnectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'external_system', 'connector_type', 'data_format', 'sync_frequency', 'is_enabled', 'last_sync_status']
    list_filter = ['connector_type', 'data_format', 'sync_frequency', 'is_enabled', 'last_sync_status', 'created_at']
    search_fields = ['name', 'description', 'external_system__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_sync', 'total_records_processed', 'total_errors']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('external_system', 'name', 'description', 'connector_type')
        }),
        ('Data Configuration', {
            'fields': ('data_format', 'source_endpoint', 'destination_endpoint', 'batch_size')
        }),
        ('Synchronization', {
            'fields': ('sync_frequency', 'sync_schedule', 'is_enabled')
        }),
        ('Data Processing', {
            'fields': ('transformation_rules', 'validation_rules', 'filters'),
            'classes': ('collapse',)
        }),
        ('Status & Statistics', {
            'fields': ('last_sync', 'last_sync_status', 'last_sync_message', 'total_records_processed', 'total_errors'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('external_system')


@admin.register(DataImportExportJob)
class DataImportExportJobAdmin(admin.ModelAdmin):
    list_display = ['connector', 'job_type', 'status', 'started_at', 'duration_seconds', 'records_processed', 'records_successful', 'records_failed']
    list_filter = ['job_type', 'status', 'started_at', 'completed_at']
    search_fields = ['connector__name', 'connector__external_system__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'duration_seconds']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Job Information', {
            'fields': ('connector', 'job_type', 'status', 'triggered_by')
        }),
        ('Execution Details', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Configuration', {
            'fields': ('job_config', 'parameters'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('records_processed', 'records_successful', 'records_failed')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'error_details', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('connector', 'connector__external_system', 'triggered_by')


@admin.register(IntegrationEndpoint)
class IntegrationEndpointAdmin(admin.ModelAdmin):
    list_display = ['name', 'endpoint_type', 'path', 'version', 'is_deprecated', 'is_enabled', 'total_requests', 'total_errors']
    list_filter = ['endpoint_type', 'version', 'is_deprecated', 'is_enabled', 'requires_authentication']
    search_fields = ['name', 'description', 'path']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_requests', 'total_errors', 'last_accessed']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'endpoint_type', 'path')
        }),
        ('HTTP Configuration', {
            'fields': ('http_methods', 'requires_authentication', 'rate_limit_per_minute')
        }),
        ('Versioning', {
            'fields': ('version', 'is_deprecated', 'deprecation_date', 'replacement_endpoint')
        }),
        ('Schema Definition', {
            'fields': ('request_schema', 'response_schema'),
            'classes': ('collapse',)
        }),
        ('Access Control', {
            'fields': ('allowed_systems',),
            'classes': ('collapse',)
        }),
        ('Monitoring', {
            'fields': ('is_enabled', 'total_requests', 'total_errors', 'last_accessed')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['allowed_systems']


@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'level', 'activity_type', 'external_system', 'connector', 'message_preview', 'duration_ms']
    list_filter = ['level', 'activity_type', 'created_at']
    search_fields = ['message', 'external_system__name', 'connector__name', 'request_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Log Information', {
            'fields': ('level', 'activity_type', 'message')
        }),
        ('Related Objects', {
            'fields': ('external_system', 'connector', 'job', 'endpoint')
        }),
        ('Request Details', {
            'fields': ('request_id', 'ip_address', 'user_agent', 'duration_ms'),
            'classes': ('collapse',)
        }),
        ('Additional Details', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'external_system', 'connector', 'job', 'endpoint'
        )


@admin.register(ServiceDiscovery)
class ServiceDiscoveryAdmin(admin.ModelAdmin):
    list_display = ['service_name', 'instance_id', 'service_type', 'host', 'port', 'health_status', 'environment', 'last_heartbeat']
    list_filter = ['service_type', 'health_status', 'environment', 'protocol', 'last_heartbeat']
    search_fields = ['service_name', 'instance_id', 'host']
    readonly_fields = ['id', 'created_at', 'updated_at', 'registered_at', 'last_heartbeat', 'full_url']
    
    fieldsets = (
        ('Service Information', {
            'fields': ('service_name', 'instance_id', 'service_type', 'version')
        }),
        ('Network Configuration', {
            'fields': ('host', 'port', 'protocol', 'base_path', 'full_url')
        }),
        ('Environment', {
            'fields': ('environment', 'region', 'availability_zone')
        }),
        ('Health & Load Balancing', {
            'fields': ('health_status', 'health_check_url', 'last_health_check', 'weight', 'max_connections', 'current_connections')
        }),
        ('Registration Tracking', {
            'fields': ('registered_at', 'last_heartbeat')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)
