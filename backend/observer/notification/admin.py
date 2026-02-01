from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    NotificationChannel, AlertRule, Alert, NotificationDelivery,
    NotificationTemplate, AlertRuleNotificationChannel
)


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_type', 'is_enabled', 'created_by', 'rate_limit_per_hour', 'created_at']
    list_filter = ['channel_type', 'is_enabled', 'created_at']
    search_fields = ['name', 'created_by__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'channel_type', 'is_enabled', 'created_by')
        }),
        ('Configuration', {
            'fields': ('configuration', 'rate_limit_per_hour', 'max_retries', 'retry_delay_seconds'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


class AlertRuleNotificationChannelInline(admin.TabularInline):
    model = AlertRuleNotificationChannel
    extra = 0
    fields = ['notification_channel', 'delay_minutes', 'is_escalation', 'escalation_level']


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity', 'is_enabled', 'created_by', 'alert_count', 'created_at']
    list_filter = ['severity', 'is_enabled', 'created_at']
    search_fields = ['name', 'description', 'created_by__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'alert_count']
    inlines = [AlertRuleNotificationChannelInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'severity', 'is_enabled', 'created_by')
        }),
        ('Alert Conditions', {
            'fields': ('conditions', 'threshold_value', 'evaluation_window_minutes'),
        }),
        ('Notification Settings', {
            'fields': ('escalation_policy', 'notification_schedule'),
            'classes': ('collapse',)
        }),
        ('Deduplication', {
            'fields': ('deduplication_window_minutes', 'deduplication_fields'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('tags', 'id', 'created_at', 'updated_at', 'alert_count'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').annotate(
            alert_count=admin.models.Count('alerts')
        )
    
    def alert_count(self, obj):
        return obj.alert_count if hasattr(obj, 'alert_count') else obj.alerts.count()
    alert_count.short_description = 'Total Alerts'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'rule', 'status', 'severity', 'triggered_at', 'escalation_level', 'notification_count']
    list_filter = ['status', 'rule__severity', 'triggered_at', 'escalation_level']
    search_fields = ['title', 'message', 'rule__name', 'fingerprint']
    readonly_fields = ['id', 'fingerprint', 'triggered_at', 'created_at', 'updated_at', 'rule_link']
    date_hierarchy = 'triggered_at'
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('rule_link', 'title', 'message', 'status', 'fingerprint')
        }),
        ('Timeline', {
            'fields': ('triggered_at', 'acknowledged_at', 'resolved_at', 'acknowledged_by', 'resolved_by')
        }),
        ('Escalation & Notifications', {
            'fields': ('escalation_level', 'last_escalated_at', 'notification_count', 'last_notification_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'rule', 'acknowledged_by', 'resolved_by'
        )
    
    def severity(self, obj):
        return obj.rule.severity.upper()
    severity.short_description = 'Severity'
    
    def rule_link(self, obj):
        if obj.rule:
            url = reverse('admin:notification_alertrule_change', args=[obj.rule.id])
            return format_html('<a href="{}">{}</a>', url, obj.rule.name)
        return '-'
    rule_link.short_description = 'Alert Rule'
    
    actions = ['acknowledge_alerts', 'resolve_alerts']
    
    def acknowledge_alerts(self, request, queryset):
        count = 0
        for alert in queryset.filter(status='triggered'):
            alert.acknowledge(request.user)
            count += 1
        self.message_user(request, f'{count} alerts acknowledged.')
    acknowledge_alerts.short_description = 'Acknowledge selected alerts'
    
    def resolve_alerts(self, request, queryset):
        count = 0
        for alert in queryset.filter(status__in=['triggered', 'acknowledged']):
            alert.resolve(request.user)
            count += 1
        self.message_user(request, f'{count} alerts resolved.')
    resolve_alerts.short_description = 'Resolve selected alerts'


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ['alert_title', 'channel', 'recipient', 'status', 'retry_count', 'sent_at']
    list_filter = ['status', 'channel__channel_type', 'sent_at', 'retry_count']
    search_fields = ['alert__title', 'channel__name', 'recipient', 'error_message']
    readonly_fields = ['id', 'created_at', 'updated_at', 'alert_link', 'channel_link']
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Delivery Information', {
            'fields': ('alert_link', 'channel_link', 'recipient', 'status')
        }),
        ('Timing', {
            'fields': ('sent_at', 'delivered_at', 'retry_count', 'next_retry_at')
        }),
        ('Content & Response', {
            'fields': ('message_content', 'response_data', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('alert', 'channel')
    
    def alert_title(self, obj):
        return obj.alert.title[:50] + '...' if len(obj.alert.title) > 50 else obj.alert.title
    alert_title.short_description = 'Alert'
    
    def alert_link(self, obj):
        if obj.alert:
            url = reverse('admin:notification_alert_change', args=[obj.alert.id])
            return format_html('<a href="{}">{}</a>', url, obj.alert.title)
        return '-'
    alert_link.short_description = 'Alert'
    
    def channel_link(self, obj):
        if obj.channel:
            url = reverse('admin:notification_notificationchannel_change', args=[obj.channel.id])
            return format_html('<a href="{}">{}</a>', url, obj.channel.name)
        return '-'
    channel_link.short_description = 'Channel'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'channel_type', 'is_default', 'created_by', 'created_at']
    list_filter = ['template_type', 'channel_type', 'is_default', 'created_at']
    search_fields = ['name', 'subject_template', 'body_template']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'channel_type', 'is_default', 'created_by')
        }),
        ('Template Content', {
            'fields': ('subject_template', 'body_template')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


# Register the through model for better admin experience
@admin.register(AlertRuleNotificationChannel)
class AlertRuleNotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['alert_rule', 'notification_channel', 'delay_minutes', 'is_escalation', 'escalation_level']
    list_filter = ['is_escalation', 'escalation_level', 'delay_minutes']
    search_fields = ['alert_rule__name', 'notification_channel__name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('alert_rule', 'notification_channel')
