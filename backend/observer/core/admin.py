from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, IdentityProvider, UserSession, AuditLog, SystemConfiguration


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = ('email', 'username', 'identity_provider', 'is_active', 'is_staff', 'last_login', 'created_at')
    list_filter = ('identity_provider', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email', 'username', 'external_id')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Identity Provider', {'fields': ('identity_provider', 'external_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'identity_provider'),
        }),
    )


@admin.register(IdentityProvider)
class IdentityProviderAdmin(admin.ModelAdmin):
    """Admin interface for IdentityProvider model."""
    
    list_display = ('name', 'is_enabled', 'is_active', 'created_at')
    list_filter = ('name', 'is_enabled', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('name', 'is_enabled')}),
        ('OAuth Configuration', {
            'fields': ('client_id', 'client_secret', 'authorization_url', 'token_url', 'user_info_url', 'scope'),
            'classes': ('collapse',)
        }),
        ('Status', {'fields': ('is_active', 'created_at', 'updated_at')}),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Hide sensitive fields in list view
        if 'client_secret' in form.base_fields:
            form.base_fields['client_secret'].widget.attrs['type'] = 'password'
        return form


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin interface for UserSession model."""
    
    list_display = ('user', 'session_token_short', 'ip_address', 'is_expired', 'expires_at', 'created_at')
    list_filter = ('is_expired', 'expires_at', 'created_at')
    search_fields = ('user__email', 'ip_address', 'session_token')
    readonly_fields = ('id', 'created_at', 'updated_at', 'session_token_short')
    ordering = ('-created_at',)
    
    def session_token_short(self, obj):
        """Display shortened session token for security."""
        return f"{obj.session_token[:8]}..." if obj.session_token else ""
    session_token_short.short_description = "Session Token"
    
    fieldsets = (
        (None, {'fields': ('user', 'session_token_short', 'expires_at', 'is_expired')}),
        ('Client Information', {'fields': ('ip_address', 'user_agent')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def has_add_permission(self, request):
        """Prevent manual session creation through admin."""
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""
    
    list_display = ('user', 'action', 'resource_type', 'resource_id', 'ip_address', 'timestamp')
    list_filter = ('action', 'resource_type', 'timestamp')
    search_fields = ('user__email', 'action', 'resource_type', 'resource_id', 'ip_address')
    readonly_fields = ('id', 'created_at', 'updated_at', 'timestamp')
    ordering = ('-timestamp',)
    
    fieldsets = (
        (None, {'fields': ('user', 'action', 'resource_type', 'resource_id')}),
        ('Client Information', {'fields': ('ip_address', 'user_agent')}),
        ('Details', {'fields': ('details',)}),
        ('Timestamps', {'fields': ('timestamp', 'created_at', 'updated_at')}),
    )
    
    def has_add_permission(self, request):
        """Prevent manual audit log creation through admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent audit log modification."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent audit log deletion."""
        return False


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for SystemConfiguration model."""
    
    list_display = ('key', 'value_display', 'is_sensitive', 'is_active', 'updated_at')
    list_filter = ('is_sensitive', 'is_active', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def value_display(self, obj):
        """Display value with sensitivity handling."""
        if obj.is_sensitive:
            return format_html('<span style="color: #666;">***HIDDEN***</span>')
        return str(obj.value)[:50] + ('...' if len(str(obj.value)) > 50 else '')
    value_display.short_description = "Value"
    
    fieldsets = (
        (None, {'fields': ('key', 'value', 'description')}),
        ('Security', {'fields': ('is_sensitive',)}),
        ('Status', {'fields': ('is_active', 'created_at', 'updated_at')}),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Add help text for sensitive fields
        if 'is_sensitive' in form.base_fields:
            form.base_fields['is_sensitive'].help_text = "Mark as sensitive to hide value in admin interface"
        return form
