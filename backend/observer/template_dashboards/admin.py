from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import DashboardTemplate, Dashboard, TemplateShare, DashboardShare, DashboardWidget
import json


class TemplateShareInline(admin.TabularInline):
    """Inline admin for template sharing"""
    model = TemplateShare
    extra = 0
    fields = ['user', 'permission_level', 'shared_by']
    readonly_fields = ['shared_by']


class DashboardShareInline(admin.TabularInline):
    """Inline admin for dashboard sharing"""
    model = DashboardShare
    extra = 0
    fields = ['user', 'permission_level', 'shared_by']
    readonly_fields = ['shared_by']


class DashboardWidgetInline(admin.TabularInline):
    """Inline admin for dashboard widgets"""
    model = DashboardWidget
    extra = 0
    fields = ['title', 'widget_type', 'position_x', 'position_y', 'width', 'height', 'is_visible']
    readonly_fields = ['created_at']


@admin.register(DashboardTemplate)
class DashboardTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for Dashboard Templates with enhanced functionality.
    """
    list_display = [
        'name', 'version', 'category', 'created_by', 'is_public', 
        'is_system_template', 'usage_count', 'created_at'
    ]
    list_filter = [
        'category', 'is_public', 'is_system_template', 'created_by', 'created_at'
    ]
    search_fields = ['name', 'description', 'tags', 'created_by__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'usage_count']
    inlines = [TemplateShareInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'tags')
        }),
        ('Version Control', {
            'fields': ('version', 'parent_template')
        }),
        ('Configuration', {
            'fields': ('layout_config_display', 'widget_configs_display'),
            'classes': ('collapse',)
        }),
        ('Sharing & Permissions', {
            'fields': ('is_public', 'is_system_template', 'created_by')
        }),
        ('Statistics', {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def layout_config_display(self, obj):
        """Display formatted layout configuration"""
        if obj.layout_config:
            return format_html(
                '<pre style="white-space: pre-wrap;">{}</pre>',
                json.dumps(obj.layout_config, indent=2)
            )
        return "No layout configuration"
    layout_config_display.short_description = "Layout Configuration"
    
    def widget_configs_display(self, obj):
        """Display formatted widget configurations"""
        if obj.widget_configs:
            return format_html(
                '<pre style="white-space: pre-wrap;">{}</pre>',
                json.dumps(obj.widget_configs, indent=2)
            )
        return "No widget configurations"
    widget_configs_display.short_description = "Widget Configurations"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('created_by', 'parent_template')


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """
    Admin interface for Dashboard instances.
    """
    list_display = [
        'name', 'owner', 'template', 'template_version', 'is_shared', 
        'is_favorite', 'is_default', 'access_count', 'last_accessed'
    ]
    list_filter = [
        'is_shared', 'is_favorite', 'is_default', 'template', 'owner', 'created_at'
    ]
    search_fields = ['name', 'description', 'owner__email', 'template__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'access_count', 'last_accessed']
    inlines = [DashboardShareInline, DashboardWidgetInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'owner')
        }),
        ('Template Information', {
            'fields': ('template', 'template_version')
        }),
        ('Configuration', {
            'fields': ('configuration_display',),
            'classes': ('collapse',)
        }),
        ('Sharing & Settings', {
            'fields': ('is_shared', 'is_favorite', 'is_default')
        }),
        ('Usage Statistics', {
            'fields': ('access_count', 'last_accessed'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def configuration_display(self, obj):
        """Display formatted dashboard configuration"""
        if obj.configuration:
            return format_html(
                '<pre style="white-space: pre-wrap;">{}</pre>',
                json.dumps(obj.configuration, indent=2)
            )
        return "No configuration"
    configuration_display.short_description = "Dashboard Configuration"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('owner', 'template')


@admin.register(TemplateShare)
class TemplateShareAdmin(admin.ModelAdmin):
    """
    Admin interface for template sharing.
    """
    list_display = ['template', 'user', 'permission_level', 'shared_by', 'created_at']
    list_filter = ['permission_level', 'created_at']
    search_fields = ['template__name', 'user__email', 'shared_by__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('template', 'user', 'shared_by')


@admin.register(DashboardShare)
class DashboardShareAdmin(admin.ModelAdmin):
    """
    Admin interface for dashboard sharing.
    """
    list_display = ['dashboard', 'user', 'permission_level', 'shared_by', 'created_at']
    list_filter = ['permission_level', 'created_at']
    search_fields = ['dashboard__name', 'user__email', 'shared_by__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('dashboard', 'user', 'shared_by')


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    """
    Admin interface for dashboard widgets.
    """
    list_display = [
        'title', 'widget_type', 'dashboard', 'position_x', 'position_y', 
        'width', 'height', 'is_visible', 'refresh_interval'
    ]
    list_filter = ['widget_type', 'is_visible', 'dashboard']
    search_fields = ['title', 'dashboard__name', 'dashboard__owner__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'widget_type', 'dashboard')
        }),
        ('Position & Size', {
            'fields': ('position_x', 'position_y', 'width', 'height')
        }),
        ('Configuration', {
            'fields': ('config_display',),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_visible', 'refresh_interval')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def config_display(self, obj):
        """Display formatted widget configuration"""
        if obj.config:
            return format_html(
                '<pre style="white-space: pre-wrap;">{}</pre>',
                json.dumps(obj.config, indent=2)
            )
        return "No configuration"
    config_display.short_description = "Widget Configuration"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('dashboard', 'dashboard__owner')
