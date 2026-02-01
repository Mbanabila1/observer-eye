from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    ConfigurationCategory,
    ConfigurationSetting,
    ConfigurationProfile,
    ConfigurationProfileSetting,
    ConfigurationDeployment,
    ConfigurationChangeLog,
    ConfigurationValidationRule
)


@admin.register(ConfigurationCategory)
class ConfigurationCategoryAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'settings_count', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['sort_order', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'display_name', 'description', 'icon', 'sort_order', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def settings_count(self, obj):
        return obj.settings.filter(is_active=True).count()
    settings_count.short_description = 'Active Settings'


@admin.register(ConfigurationSetting)
class ConfigurationSettingAdmin(admin.ModelAdmin):
    list_display = [
        'key', 'display_name', 'category', 'setting_type', 
        'is_required', 'is_sensitive', 'is_readonly', 'is_active'
    ]
    list_filter = [
        'category', 'setting_type', 'is_required', 
        'is_sensitive', 'is_readonly', 'is_active', 'created_at'
    ]
    search_fields = ['key', 'display_name', 'description']
    ordering = ['category__sort_order', 'sort_order', 'key']
    readonly_fields = ['id', 'created_at', 'updated_at', 'effective_value']
    
    fieldsets = (
        (None, {
            'fields': ('category', 'key', 'display_name', 'description', 'setting_type')
        }),
        ('Values', {
            'fields': ('default_value', 'current_value', 'effective_value')
        }),
        ('Configuration', {
            'fields': (
                'is_required', 'is_sensitive', 'is_readonly', 
                'validation_rules', 'choices', 'help_text', 'sort_order'
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
    
    def effective_value(self, obj):
        """Display the effective value (current or default)."""
        value = obj.get_value()
        if obj.is_sensitive and value is not None:
            return '*** (sensitive)'
        return format_html('<code>{}</code>', json.dumps(value, indent=2) if value is not None else 'None')
    effective_value.short_description = 'Effective Value'


class ConfigurationProfileSettingInline(admin.TabularInline):
    model = ConfigurationProfileSetting
    extra = 0
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('setting', 'setting__category')


@admin.register(ConfigurationProfile)
class ConfigurationProfileAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'is_default', 'is_system', 'settings_count', 'created_by', 'created_at']
    list_filter = ['is_default', 'is_system', 'is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [ConfigurationProfileSettingInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Configuration', {
            'fields': ('is_default', 'is_system', 'created_by', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def settings_count(self, obj):
        return obj.profile_settings.count()
    settings_count.short_description = 'Settings Count'


@admin.register(ConfigurationDeployment)
class ConfigurationDeploymentAdmin(admin.ModelAdmin):
    list_display = [
        'profile', 'status', 'deployed_by', 'started_at', 
        'completed_at', 'duration', 'has_error'
    ]
    list_filter = ['status', 'started_at', 'completed_at']
    search_fields = ['profile__name', 'profile__display_name', 'deployed_by__email']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'duration', 
        'rollback_link', 'error_display'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('profile', 'deployed_by', 'status', 'deployment_notes')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration')
        }),
        ('Error Information', {
            'fields': ('error_display', 'rollback_deployment', 'rollback_link'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration(self, obj):
        if obj.started_at and obj.completed_at:
            delta = obj.completed_at - obj.started_at
            return str(delta)
        return 'N/A'
    duration.short_description = 'Duration'
    
    def has_error(self, obj):
        return bool(obj.error_message)
    has_error.boolean = True
    has_error.short_description = 'Has Error'
    
    def error_display(self, obj):
        if obj.error_message:
            return format_html('<pre style="color: red;">{}</pre>', obj.error_message)
        return 'No errors'
    error_display.short_description = 'Error Message'
    
    def rollback_link(self, obj):
        if obj.rollback_deployment:
            url = reverse('admin:settings_configurationdeployment_change', 
                         args=[obj.rollback_deployment.id])
            return format_html('<a href="{}">View Rollback Deployment</a>', url)
        return 'N/A'
    rollback_link.short_description = 'Rollback Deployment'


@admin.register(ConfigurationChangeLog)
class ConfigurationChangeLogAdmin(admin.ModelAdmin):
    list_display = [
        'setting', 'changed_by', 'change_summary', 
        'ip_address', 'created_at'
    ]
    list_filter = ['created_at', 'setting__category']
    search_fields = [
        'setting__key', 'setting__display_name', 
        'changed_by__email', 'change_reason'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'old_value_display', 
        'new_value_display', 'change_summary'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('setting', 'changed_by', 'change_reason')
        }),
        ('Values', {
            'fields': ('old_value_display', 'new_value_display', 'change_summary')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def old_value_display(self, obj):
        if obj.setting.is_sensitive and obj.old_value is not None:
            return '*** (sensitive)'
        return format_html('<code>{}</code>', 
                          json.dumps(obj.old_value, indent=2) if obj.old_value is not None else 'None')
    old_value_display.short_description = 'Old Value'
    
    def new_value_display(self, obj):
        if obj.setting.is_sensitive and obj.new_value is not None:
            return '*** (sensitive)'
        return format_html('<code>{}</code>', 
                          json.dumps(obj.new_value, indent=2) if obj.new_value is not None else 'None')
    new_value_display.short_description = 'New Value'
    
    def change_summary(self, obj):
        if obj.setting.is_sensitive:
            return 'Sensitive setting changed'
        
        old_str = str(obj.old_value) if obj.old_value is not None else 'None'
        new_str = str(obj.new_value) if obj.new_value is not None else 'None'
        
        if len(old_str) > 50:
            old_str = old_str[:47] + '...'
        if len(new_str) > 50:
            new_str = new_str[:47] + '...'
        
        return f'{old_str} → {new_str}'
    change_summary.short_description = 'Change Summary'


@admin.register(ConfigurationValidationRule)
class ConfigurationValidationRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'is_active', 'created_at']
    list_filter = ['rule_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'error_message']
    ordering = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'rule_config_display']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'rule_type', 'error_message')
        }),
        ('Configuration', {
            'fields': ('rule_config', 'rule_config_display', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rule_config_display(self, obj):
        return format_html('<pre>{}</pre>', json.dumps(obj.rule_config, indent=2))
    rule_config_display.short_description = 'Rule Configuration (Formatted)'
