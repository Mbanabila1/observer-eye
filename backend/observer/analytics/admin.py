"""
Admin configuration for Analytics models.
Provides comprehensive admin interface for managing analytics data and insights.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    DataSource, AnalyticsData, AnalyticsQuery, AnalyticsReport,
    AnalyticsDashboard, AnalyticsAlert, AnalyticsAggregation, AnalyticsInsight
)


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'is_enabled', 'sync_frequency', 'last_sync', 'created_at']
    list_filter = ['source_type', 'is_enabled', 'sync_frequency', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_sync']
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'description', 'source_type', 'is_enabled']
        }),
        ('Configuration', {
            'fields': ['connection_config', 'schema_definition', 'sync_frequency']
        }),
        ('Status', {
            'fields': ['last_sync', 'is_active']
        }),
        ('Metadata', {
            'fields': ['id', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(AnalyticsData)
class AnalyticsDataAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'metric_type', 'data_source', 'numeric_value', 'timestamp', 'processed_at']
    list_filter = ['metric_type', 'data_source', 'timestamp', 'processed_at']
    search_fields = ['metric_name', 'string_value']
    readonly_fields = ['id', 'processed_at', 'created_at', 'updated_at']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    fieldsets = [
        ('Metric Information', {
            'fields': ['data_source', 'metric_name', 'metric_type', 'timestamp']
        }),
        ('Values', {
            'fields': ['metric_value', 'numeric_value', 'string_value']
        }),
        ('Metadata', {
            'fields': ['dimensions', 'tags']
        }),
        ('System', {
            'fields': ['processed_at', 'is_active', 'id', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('data_source')


@admin.register(AnalyticsQuery)
class AnalyticsQueryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_public', 'execution_count', 'last_executed', 'created_at']
    list_filter = ['is_public', 'created_by', 'last_executed', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'execution_count', 'last_executed', 'average_execution_time', 'created_at', 'updated_at']
    filter_horizontal = ['data_sources']
    
    fieldsets = [
        ('Query Information', {
            'fields': ['name', 'description', 'created_by', 'is_public']
        }),
        ('Configuration', {
            'fields': ['query_definition', 'data_sources']
        }),
        ('Statistics', {
            'fields': ['execution_count', 'last_executed', 'average_execution_time']
        }),
        ('Metadata', {
            'fields': ['id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').prefetch_related('data_sources')


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'generated_at', 'generation_time', 'is_scheduled']
    list_filter = ['report_type', 'is_scheduled', 'generated_at', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'generated_at', 'generation_time', 'created_at', 'updated_at']
    filter_horizontal = ['shared_with']
    
    fieldsets = [
        ('Report Information', {
            'fields': ['name', 'description', 'report_type', 'created_by']
        }),
        ('Configuration', {
            'fields': ['query', 'parameters', 'is_scheduled', 'schedule_config']
        }),
        ('Sharing', {
            'fields': ['shared_with']
        }),
        ('Results', {
            'fields': ['results', 'generated_at', 'generation_time']
        }),
        ('Metadata', {
            'fields': ['id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'query')


@admin.register(AnalyticsDashboard)
class AnalyticsDashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_public', 'is_realtime', 'refresh_interval', 'view_count', 'last_viewed']
    list_filter = ['is_public', 'is_realtime', 'created_by', 'last_viewed', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'view_count', 'last_viewed', 'created_at', 'updated_at']
    filter_horizontal = ['shared_with']
    
    fieldsets = [
        ('Dashboard Information', {
            'fields': ['name', 'description', 'created_by', 'is_public']
        }),
        ('Configuration', {
            'fields': ['layout_config', 'widgets', 'filters', 'refresh_interval', 'is_realtime']
        }),
        ('Sharing', {
            'fields': ['shared_with']
        }),
        ('Statistics', {
            'fields': ['view_count', 'last_viewed']
        }),
        ('Metadata', {
            'fields': ['id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(AnalyticsAlert)
class AnalyticsAlertAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity', 'is_enabled', 'threshold_value', 'comparison_operator', 'trigger_count', 'last_triggered']
    list_filter = ['severity', 'is_enabled', 'comparison_operator', 'last_triggered', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'last_checked', 'last_triggered', 'trigger_count', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Alert Information', {
            'fields': ['name', 'description', 'created_by', 'severity', 'is_enabled']
        }),
        ('Condition', {
            'fields': ['query', 'condition', 'threshold_value', 'comparison_operator']
        }),
        ('Notification', {
            'fields': ['notification_channels', 'check_frequency']
        }),
        ('Statistics', {
            'fields': ['last_checked', 'last_triggered', 'trigger_count']
        }),
        ('Metadata', {
            'fields': ['id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'query')


@admin.register(AnalyticsAggregation)
class AnalyticsAggregationAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'aggregation_type', 'time_window', 'aggregated_value', 'sample_count', 'window_start', 'computed_at']
    list_filter = ['aggregation_type', 'time_window', 'data_source', 'computed_at']
    search_fields = ['metric_name']
    readonly_fields = ['id', 'computed_at', 'created_at', 'updated_at']
    date_hierarchy = 'window_start'
    list_per_page = 50
    
    fieldsets = [
        ('Aggregation Information', {
            'fields': ['data_source', 'metric_name', 'aggregation_type', 'time_window']
        }),
        ('Time Window', {
            'fields': ['window_start', 'window_end']
        }),
        ('Results', {
            'fields': ['aggregated_value', 'sample_count', 'dimensions']
        }),
        ('Metadata', {
            'fields': ['computed_at', 'id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('data_source')


@admin.register(AnalyticsInsight)
class AnalyticsInsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'insight_type', 'confidence_score', 'impact_score', 'is_acknowledged', 'acknowledged_by', 'created_at']
    list_filter = ['insight_type', 'is_acknowledged', 'confidence_score', 'impact_score', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'acknowledged_at', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Insight Information', {
            'fields': ['title', 'description', 'insight_type', 'data_source']
        }),
        ('Metrics', {
            'fields': ['metric_names', 'confidence_score', 'impact_score']
        }),
        ('Analysis', {
            'fields': ['time_range', 'analysis_data', 'recommendations']
        }),
        ('Acknowledgment', {
            'fields': ['is_acknowledged', 'acknowledged_by', 'acknowledged_at']
        }),
        ('Metadata', {
            'fields': ['id', 'created_at', 'updated_at', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('data_source', 'acknowledged_by')
    
    def formatted_confidence(self, obj):
        """Display confidence score as percentage."""
        return f"{obj.confidence_score * 100:.1f}%"
    formatted_confidence.short_description = "Confidence"
    
    def formatted_impact(self, obj):
        """Display impact score as percentage."""
        return f"{obj.impact_score * 100:.1f}%"
    formatted_impact.short_description = "Impact"
