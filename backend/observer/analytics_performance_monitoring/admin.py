"""
Admin configuration for Analytics Performance Monitoring models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AnalyticsPerformanceMetric, AnalyticsQueryPerformance,
    AnalyticsResourceUsage, AnalyticsPerformanceAlert
)


@admin.register(AnalyticsPerformanceMetric)
class AnalyticsPerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ['operation_name', 'operation_type', 'execution_time_ms', 'memory_usage_mb', 'success', 'timestamp']
    list_filter = ['operation_type', 'success', 'timestamp']
    search_fields = ['operation_name', 'error_message']
    readonly_fields = ['id', 'timestamp', 'created_at', 'updated_at']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    fieldsets = [
        ('Operation Information', {
            'fields': ['operation_type', 'operation_name', 'success']
        }),
        ('Performance Metrics', {
            'fields': ['execution_time_ms', 'memory_usage_mb', 'cpu_usage_percent', 'data_volume_mb', 'record_count']
        }),
        ('Error Information', {
            'fields': ['error_message']
        }),
        ('Metadata', {
            'fields': ['metadata', 'timestamp', 'id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def colored_success(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        else:
            return format_html('<span style="color: red;">✗ Failed</span>')
    colored_success.short_description = 'Status'


@admin.register(AnalyticsQueryPerformance)
class AnalyticsQueryPerformanceAdmin(admin.ModelAdmin):
    list_display = ['query_id', 'query_type', 'user', 'execution_time_ms', 'performance_score', 'cache_hit', 'timestamp']
    list_filter = ['query_type', 'cache_hit', 'timestamp']
    search_fields = ['query_id', 'user__email']
    readonly_fields = ['id', 'timestamp', 'created_at', 'updated_at']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    fieldsets = [
        ('Query Information', {
            'fields': ['query_id', 'query_type', 'user']
        }),
        ('Performance Metrics', {
            'fields': ['execution_time_ms', 'planning_time_ms', 'data_scan_mb', 'result_size_mb', 'performance_score']
        }),
        ('Optimization', {
            'fields': ['cache_hit', 'optimization_applied']
        }),
        ('Query Details', {
            'fields': ['data_source_count', 'time_range_hours']
        }),
        ('Metadata', {
            'fields': ['timestamp', 'id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AnalyticsResourceUsage)
class AnalyticsResourceUsageAdmin(admin.ModelAdmin):
    list_display = ['resource_type', 'current_usage', 'peak_usage', 'usage_unit', 'alert_triggered', 'timestamp']
    list_filter = ['resource_type', 'alert_triggered', 'timestamp']
    readonly_fields = ['id', 'timestamp', 'created_at', 'updated_at']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    fieldsets = [
        ('Resource Information', {
            'fields': ['resource_type', 'usage_unit', 'measurement_window_minutes']
        }),
        ('Usage Metrics', {
            'fields': ['current_usage', 'peak_usage', 'average_usage']
        }),
        ('Thresholds', {
            'fields': ['threshold_warning', 'threshold_critical', 'alert_triggered']
        }),
        ('Metadata', {
            'fields': ['timestamp', 'id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def colored_alert_status(self, obj):
        if obj.alert_triggered:
            return format_html('<span style="color: red;">⚠ Alert</span>')
        else:
            return format_html('<span style="color: green;">✓ Normal</span>')
    colored_alert_status.short_description = 'Alert Status'


@admin.register(AnalyticsPerformanceAlert)
class AnalyticsPerformanceAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_type', 'severity', 'is_resolved', 'resolved_by', 'timestamp']
    list_filter = ['alert_type', 'severity', 'is_resolved', 'timestamp']
    search_fields = ['title', 'description', 'metric_name']
    readonly_fields = ['id', 'timestamp', 'created_at', 'updated_at']
    date_hierarchy = 'timestamp'
    
    fieldsets = [
        ('Alert Information', {
            'fields': ['alert_type', 'severity', 'title', 'description']
        }),
        ('Metrics', {
            'fields': ['metric_name', 'threshold_value', 'actual_value']
        }),
        ('Resolution', {
            'fields': ['is_resolved', 'resolved_at', 'resolved_by']
        }),
        ('Notification', {
            'fields': ['notification_sent']
        }),
        ('Details', {
            'fields': ['operation_details']
        }),
        ('Metadata', {
            'fields': ['timestamp', 'id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('resolved_by')
    
    def colored_severity(self, obj):
        colors = {
            'low': 'blue',
            'medium': 'orange',
            'high': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.severity, 'black')
        return format_html(f'<span style="color: {color};">{obj.get_severity_display()}</span>')
    colored_severity.short_description = 'Severity'