"""
Django admin configuration for grailobserver app.
Provides administrative interface for specialized observability features.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    ObservabilityTarget, ObservabilityPattern, ServiceLevelIndicator,
    ServiceLevelObjective, ObservabilityTrace, ObservabilityAnomaly,
    ObservabilityPlaybook, ObservabilityExperiment, ObservabilityInsight
)


@admin.register(ObservabilityTarget)
class ObservabilityTargetAdmin(admin.ModelAdmin):
    """Admin interface for observability targets."""
    
    list_display = [
        'name', 'target_type', 'health_status', 'is_critical', 
        'is_monitored', 'last_health_check', 'created_at'
    ]
    list_filter = [
        'target_type', 'health_status', 'is_critical', 'is_monitored', 'is_active'
    ]
    search_fields = ['name', 'description', 'endpoint_url']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_health_check']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'target_type', 'endpoint_url')
        }),
        ('Configuration', {
            'fields': ('health_check_config', 'monitoring_config', 'sla_config', 'tags'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('health_status', 'is_critical', 'is_monitored', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'last_health_check'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(ObservabilityPattern)
class ObservabilityPatternAdmin(admin.ModelAdmin):
    """Admin interface for observability patterns."""
    
    list_display = ['name', 'pattern_type', 'is_active', 'usage_count', 'created_at']
    list_filter = ['pattern_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'usage_count']
    filter_horizontal = ['applicable_targets']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'pattern_type')
        }),
        ('Configuration', {
            'fields': ('pattern_definition', 'metrics_config', 'alerting_rules'),
            'classes': ('collapse',)
        }),
        ('Implementation', {
            'fields': ('implementation_guide', 'applicable_targets')
        }),
        ('Status', {
            'fields': ('is_active', 'usage_count')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ServiceLevelIndicator)
class ServiceLevelIndicatorAdmin(admin.ModelAdmin):
    """Admin interface for Service Level Indicators."""
    
    list_display = [
        'name', 'target', 'sli_type', 'unit', 'calculation_window', 'is_active'
    ]
    list_filter = ['sli_type', 'calculation_window', 'is_active']
    search_fields = ['name', 'description', 'target__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'target', 'sli_type')
        }),
        ('Measurement Configuration', {
            'fields': (
                'measurement_config', 'query_definition', 'unit',
                'good_threshold', 'total_threshold', 'calculation_window'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ServiceLevelObjective)
class ServiceLevelObjectiveAdmin(admin.ModelAdmin):
    """Admin interface for Service Level Objectives."""
    
    list_display = [
        'name', 'sli', 'target_percentage', 'time_window', 
        'current_performance', 'error_budget_remaining', 'is_active'
    ]
    list_filter = ['time_window', 'is_active']
    search_fields = ['name', 'description', 'sli__name', 'sli__target__name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'current_performance', 
        'error_budget_remaining', 'last_calculated'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'sli')
        }),
        ('SLO Configuration', {
            'fields': ('target_percentage', 'time_window', 'error_budget_policy', 'alerting_config')
        }),
        ('Current Status', {
            'fields': ('current_performance', 'error_budget_remaining', 'last_calculated'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sli__target')


@admin.register(ObservabilityTrace)
class ObservabilityTraceAdmin(admin.ModelAdmin):
    """Admin interface for observability traces."""
    
    list_display = [
        'trace_id_short', 'service_name', 'operation_name', 
        'duration_ms', 'status', 'start_time'
    ]
    list_filter = ['service_name', 'status', 'start_time']
    search_fields = ['trace_id', 'span_id', 'service_name', 'operation_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Trace Information', {
            'fields': ('trace_id', 'span_id', 'parent_span_id')
        }),
        ('Operation Details', {
            'fields': ('service_name', 'operation_name', 'status')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'duration_ms')
        }),
        ('Additional Data', {
            'fields': ('tags', 'logs', 'baggage'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def trace_id_short(self, obj):
        """Display shortened trace ID."""
        return f"{obj.trace_id[:8]}..." if obj.trace_id else ""
    trace_id_short.short_description = "Trace ID"


@admin.register(ObservabilityAnomaly)
class ObservabilityAnomalyAdmin(admin.ModelAdmin):
    """Admin interface for observability anomalies."""
    
    list_display = [
        'target', 'anomaly_type', 'metric_name', 'severity',
        'confidence_score', 'deviation_percentage', 'detected_at', 'is_acknowledged'
    ]
    list_filter = [
        'anomaly_type', 'severity', 'is_acknowledged', 'detected_at'
    ]
    search_fields = ['target__name', 'metric_name', 'detection_method']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'detected_at', 
        'confidence_score', 'anomaly_score', 'detection_method'
    ]
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        ('Anomaly Information', {
            'fields': ('target', 'anomaly_type', 'metric_name', 'severity')
        }),
        ('Detection Details', {
            'fields': (
                'detected_at', 'time_window_start', 'time_window_end',
                'confidence_score', 'anomaly_score', 'detection_method'
            )
        }),
        ('Values', {
            'fields': ('baseline_value', 'observed_value', 'deviation_percentage')
        }),
        ('Context', {
            'fields': ('context_data',),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('is_acknowledged', 'acknowledged_by', 'acknowledged_at', 'resolution_notes')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('target', 'acknowledged_by')


@admin.register(ObservabilityPlaybook)
class ObservabilityPlaybookAdmin(admin.ModelAdmin):
    """Admin interface for observability playbooks."""
    
    list_display = [
        'name', 'playbook_type', 'created_by', 'is_active',
        'execution_count', 'success_rate', 'last_executed'
    ]
    list_filter = ['playbook_type', 'is_active', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'execution_count', 
        'success_rate', 'average_execution_time', 'last_executed'
    ]
    filter_horizontal = ['applicable_targets']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'playbook_type', 'created_by')
        }),
        ('Configuration', {
            'fields': ('trigger_conditions', 'steps', 'automation_config'),
            'classes': ('collapse',)
        }),
        ('Applicability', {
            'fields': ('applicable_targets',)
        }),
        ('Statistics', {
            'fields': (
                'execution_count', 'success_rate', 'average_execution_time', 'last_executed'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ObservabilityExperiment)
class ObservabilityExperimentAdmin(admin.ModelAdmin):
    """Admin interface for observability experiments."""
    
    list_display = [
        'name', 'experiment_type', 'target', 'status', 
        'created_by', 'scheduled_at', 'started_at', 'completed_at'
    ]
    list_filter = ['experiment_type', 'status', 'created_by']
    search_fields = ['name', 'description', 'hypothesis']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'experiment_type', 'target', 'created_by')
        }),
        ('Experiment Design', {
            'fields': ('hypothesis', 'experiment_config', 'success_criteria', 'safety_checks')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'started_at', 'completed_at', 'status')
        }),
        ('Results', {
            'fields': ('results', 'lessons_learned'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('target', 'created_by')


@admin.register(ObservabilityInsight)
class ObservabilityInsightAdmin(admin.ModelAdmin):
    """Admin interface for observability insights."""
    
    list_display = [
        'title', 'insight_type', 'confidence_score', 'impact_score',
        'is_actionable', 'is_acknowledged', 'created_at'
    ]
    list_filter = [
        'insight_type', 'is_actionable', 'is_acknowledged', 'generated_by'
    ]
    search_fields = ['title', 'description']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'generated_by',
        'confidence_score', 'impact_score'
    ]
    filter_horizontal = ['targets']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'insight_type', 'targets')
        }),
        ('Scoring', {
            'fields': ('confidence_score', 'impact_score', 'generated_by')
        }),
        ('Analysis', {
            'fields': ('evidence_data', 'recommendations', 'estimated_impact'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_actionable', 'is_acknowledged', 'acknowledged_by', 'acknowledged_at')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('targets')
