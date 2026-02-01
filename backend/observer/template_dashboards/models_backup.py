import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import BaseModel
import json
import re

User = get_user_model()


class DashboardTemplate(BaseModel):
    """
    Dashboard template model for creating reusable dashboard configurations.
    Supports versioning, sharing, and widget configuration management.
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
    """
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name for the dashboard template"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the template's purpose and contents"
    )
    
    # Layout and widget configuration stored as JSON
    layout_config = models.JSONField(
        default=dict,
        help_text="Layout configuration including grid settings, responsive breakpoints"
    )
    widget_configs = models.JSONField(
        default=list,
        help_text="List of widget configurations with types, positions, and data sources"
    )
    
    # Versioning support
    version = models.CharField(
        max_length=20,
        default='1.0.0',
        help_text="Semantic version number (e.g., 1.0.0, 1.2.3)"
    )
    parent_template = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions',
        help_text="Parent template for version tracking"
    )
    
    # Sharing and permissions
    is_public = models.BooleanField(
        default=False,
        help_text="Whether this template is publicly available to all users"
    )
    is_system_template = models.BooleanField(
        default=False,
        help_text="Whether this is a system-provided template"
    )
    
    # Ownership and collaboration
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_templates',
        help_text="User who created this template"
    )
    shared_with = models.ManyToManyField(
        User,
        through='TemplateShare',
        through_fields=('template', 'user'),
        related_name='shared_templates',
        blank=True,
        help_text="Users who have access to this template"
    )
    
    # Template metadata
    category = models.CharField(
        max_length=100,
        blank=True,
        choices=[
            ('monitoring', 'System Monitoring'),
            ('analytics', 'Analytics & BI'),
            ('security', 'Security Dashboard'),
            ('performance', 'Performance Metrics'),
            ('network', 'Network Monitoring'),
            ('application', 'Application Metrics'),
            ('custom', 'Custom Dashboard'),
        ],
        help_text="Template category for organization"
    )
    tags = models.JSONField(
        default=list,
        help_text="List of tags for template discovery and filtering"
    )
    
    # Usage statistics
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this template has been used"
    )
    
    class Meta:
        db_table = 'template_dashboards_template'
        unique_together = [['name', 'version', 'created_by']]
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_public']),
            models.Index(fields=['created_by']),
            models.Index(fields=['version']),
            models.Index(fields=['usage_count']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version} by {self.created_by.email}"
    
    def clean(self):
        """Validate template configuration"""
        super().clean()
        
        # Validate layout configuration
        if self.layout_config:
            required_layout_fields = ['grid_columns', 'grid_rows']
            for field in required_layout_fields:
                if field not in self.layout_config:
                    raise ValidationError(f"Layout config missing required field: {field}")
        
        # Validate widget configurations
        if self.widget_configs:
            for i, widget in enumerate(self.widget_configs):
                if not isinstance(widget, dict):
                    raise ValidationError(f"Widget config {i} must be a dictionary")
                
                required_widget_fields = ['type', 'position', 'config']
                for field in required_widget_fields:
                    if field not in widget:
                        raise ValidationError(f"Widget {i} missing required field: {field}")
        
        # Validate version format (semantic versioning)
        version_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'
        if not re.match(version_pattern, self.version):
            raise ValidationError("Version must follow semantic versioning format (e.g., 1.0.0)")$'
        if not re.match(version_pattern, self.version):
            raise ValidationError("Version must follow semantic versioning format (e.g., 1.0.0)")
    
    def increment_usage(self):
        """Increment usage count when template is used"""
        self.usage_count += 1
        self.save(update_fields=['usage_count', 'updated_at'])
    
    def create_new_version(self, version, user, **kwargs):
        """Create a new version of this template"""
        new_template = DashboardTemplate(
            name=self.name,
            description=kwargs.get('description', self.description),
            layout_config=kwargs.get('layout_config', self.layout_config),
            widget_configs=kwargs.get('widget_configs', self.widget_configs),
            version=version,
            parent_template=self.parent_template or self,
            is_public=kwargs.get('is_public', self.is_public),
            category=kwargs.get('category', self.category),
            tags=kwargs.get('tags', self.tags or []),
            created_by=user,
        )
        new_template.full_clean()
        new_template.save()
        return new_template
    
    def get_all_versions(self):
        """Get all versions of this template"""
        if self.parent_template:
            return self.parent_template.versions.all()
        return self.versions.all()
    
    def get_latest_version(self):
        """Get the latest version of this template"""
        versions = self.get_all_versions()
        if not versions.exists():
            return self
        
        # Sort by semantic version
        def version_key(template):
            parts = template.version.split('-')[0].split('.')
            return tuple(int(part) for part in parts)
        
        return max(versions, key=version_key)
    
    def can_user_access(self, user):
        """Check if user can access this template"""
        if self.is_public or self.is_system_template:
            return True
        if user is None:
            return False
        if self.created_by == user:
            return True
        return self.shared_with.filter(id=user.id).exists()
    
    def share_with_user(self, user, permission_level='view', shared_by=None):
        """Share template with a user"""
        share, created = TemplateShare.objects.get_or_create(
            template=self,
            user=user,
            defaults={
                'permission_level': permission_level,
                'shared_by': shared_by or self.created_by
            }
        )
        return share


class TemplateShare(BaseModel):
    """
    Through model for sharing templates between users with permission levels.
    """
    template = models.ForeignKey(
        DashboardTemplate,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='template_shares'
    )
    permission_level = models.CharField(
        max_length=20,
        choices=[
            ('view', 'View Only'),
            ('edit', 'Edit Template'),
            ('admin', 'Full Admin'),
        ],
        default='view',
        help_text="Permission level for shared template"
    )
    shared_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shared_templates_by',
        help_text="User who shared the template"
    )
    
    class Meta:
        db_table = 'template_dashboards_share'
        unique_together = [['template', 'user']]
        indexes = [
            models.Index(fields=['template', 'user']),
            models.Index(fields=['user', 'permission_level']),
        ]
    
    def __str__(self):
        return f"{self.template.name} shared with {self.user.email} ({self.permission_level})"


class Dashboard(BaseModel):
    """
    Dashboard instance model for user-created dashboards.
    Can be created from templates or built from scratch.
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
    """
    name = models.CharField(
        max_length=255,
        help_text="User-defined name for the dashboard"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the dashboard"
    )
    
    # Template relationship
    template = models.ForeignKey(
        DashboardTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dashboard_instances',
        help_text="Template this dashboard was created from (if any)"
    )
    template_version = models.CharField(
        max_length=20,
        blank=True,
        help_text="Version of template used to create this dashboard"
    )
    
    # Dashboard configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Complete dashboard configuration including layout and widgets"
    )
    
    # Ownership and sharing
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_dashboards',
        help_text="User who owns this dashboard"
    )
    is_shared = models.BooleanField(
        default=False,
        help_text="Whether this dashboard is shared with other users"
    )
    shared_with = models.ManyToManyField(
        User,
        through='DashboardShare',
        through_fields=('dashboard', 'user'),
        related_name='accessible_dashboards',
        blank=True,
        help_text="Users who have access to this dashboard"
    )
    
    # Dashboard metadata
    is_favorite = models.BooleanField(
        default=False,
        help_text="Whether this is marked as a favorite dashboard"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the user's default dashboard"
    )
    
    # Usage tracking
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this dashboard was last accessed"
    )
    access_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this dashboard has been accessed"
    )
    
    class Meta:
        db_table = 'template_dashboards_dashboard'
        unique_together = [['name', 'owner']]
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['template']),
            models.Index(fields=['is_shared']),
            models.Index(fields=['is_favorite']),
            models.Index(fields=['is_default']),
            models.Index(fields=['last_accessed']),
        ]
        ordering = ['-last_accessed', '-created_at']
    
    def __str__(self):
        return f"{self.name} by {self.owner.email}"
    
    def clean(self):
        """Validate dashboard configuration"""
        super().clean()
        
        # Validate configuration structure
        if self.configuration:
            required_fields = ['layout', 'widgets']
            for field in required_fields:
                if field not in self.configuration:
                    raise ValidationError(f"Configuration missing required field: {field}")
        
        # Ensure only one default dashboard per user
        if self.is_default:
            existing_default = Dashboard.objects.filter(
                owner=self.owner,
                is_default=True
            ).exclude(id=self.id)
            
            if existing_default.exists():
                raise ValidationError("User can only have one default dashboard")
    
    def save(self, *args, **kwargs):
        """Override save to handle template version tracking"""
        if self.template and not self.template_version:
            self.template_version = self.template.version
        super().save(*args, **kwargs)
    
    def increment_access(self):
        """Increment access count and update last accessed time"""
        from django.utils import timezone
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed', 'updated_at'])
    
    def share_with_user(self, user, permission_level='view', shared_by=None):
        """Share dashboard with a user"""
        share, created = DashboardShare.objects.get_or_create(
            dashboard=self,
            user=user,
            defaults={
                'permission_level': permission_level,
                'shared_by': shared_by or self.owner
            }
        )
        if created:
            self.is_shared = True
            self.save(update_fields=['is_shared', 'updated_at'])
        return share
    
    def can_user_access(self, user):
        """Check if user can access this dashboard"""
        if self.owner == user:
            return True
        return self.shared_with.filter(id=user.id).exists()
    
    def can_user_edit(self, user):
        """Check if user can edit this dashboard"""
        if self.owner == user:
            return True
        
        share = DashboardShare.objects.filter(
            dashboard=self,
            user=user,
            permission_level__in=['edit', 'admin']
        ).first()
        return share is not None
    
    def create_from_template(self, template, user, name=None):
        """Create a dashboard instance from a template"""
        dashboard_name = name or f"{template.name} - {user.email}"
        
        # Build configuration from template
        configuration = {
            'layout': template.layout_config,
            'widgets': template.widget_configs,
            'metadata': {
                'created_from_template': template.id,
                'template_version': template.version,
                'created_at': timezone.now().isoformat(),
            }
        }
        
        dashboard = Dashboard(
            name=dashboard_name,
            description=template.description,
            template=template,
            template_version=template.version,
            configuration=configuration,
            owner=user,
        )
        dashboard.full_clean()
        dashboard.save()
        
        # Increment template usage
        template.increment_usage()
        
        return dashboard


class DashboardShare(BaseModel):
    """
    Through model for sharing dashboards between users with permission levels.
    """
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_shares'
    )
    permission_level = models.CharField(
        max_length=20,
        choices=[
            ('view', 'View Only'),
            ('edit', 'Edit Dashboard'),
            ('admin', 'Full Admin'),
        ],
        default='view',
        help_text="Permission level for shared dashboard"
    )
    shared_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shared_dashboards_by',
        help_text="User who shared the dashboard"
    )
    
    class Meta:
        db_table = 'template_dashboards_dashboard_share'
        unique_together = [['dashboard', 'user']]
        indexes = [
            models.Index(fields=['dashboard', 'user']),
            models.Index(fields=['user', 'permission_level']),
        ]
    
    def __str__(self):
        return f"{self.dashboard.name} shared with {self.user.email} ({self.permission_level})"


class DashboardWidget(BaseModel):
    """
    Individual widget configuration within a dashboard.
    Allows for granular widget management and reusability.
    """
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets'
    )
    widget_type = models.CharField(
        max_length=100,
        choices=[
            ('chart', 'Chart Widget'),
            ('metric', 'Metric Display'),
            ('table', 'Data Table'),
            ('gauge', 'Gauge/Meter'),
            ('text', 'Text Widget'),
            ('alert', 'Alert Status'),
            ('log', 'Log Viewer'),
            ('custom', 'Custom Widget'),
        ],
        help_text="Type of widget"
    )
    title = models.CharField(
        max_length=255,
        help_text="Widget title displayed to users"
    )
    
    # Position and sizing
    position_x = models.PositiveIntegerField(
        default=0,
        help_text="X position in grid"
    )
    position_y = models.PositiveIntegerField(
        default=0,
        help_text="Y position in grid"
    )
    width = models.PositiveIntegerField(
        default=1,
        help_text="Widget width in grid units"
    )
    height = models.PositiveIntegerField(
        default=1,
        help_text="Widget height in grid units"
    )
    
    # Widget configuration
    config = models.JSONField(
        default=dict,
        help_text="Widget-specific configuration including data sources and display options"
    )
    
    # Display settings
    is_visible = models.BooleanField(
        default=True,
        help_text="Whether widget is currently visible"
    )
    refresh_interval = models.PositiveIntegerField(
        default=30,
        help_text="Refresh interval in seconds (0 for manual refresh)"
    )
    
    class Meta:
        db_table = 'template_dashboards_widget'
        unique_together = [['dashboard', 'position_x', 'position_y']]
        indexes = [
            models.Index(fields=['dashboard']),
            models.Index(fields=['widget_type']),
            models.Index(fields=['position_x', 'position_y']),
        ]
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.title} ({self.widget_type}) in {self.dashboard.name}"
    
    def clean(self):
        """Validate widget configuration"""
        super().clean()
        
        # Validate position doesn't overlap with existing widgets
        if self.dashboard_id:  # Only check if dashboard is set
            overlapping = DashboardWidget.objects.filter(
                dashboard=self.dashboard,
                position_x__lt=self.position_x + self.width,
                position_x__gte=self.position_x - self.width + 1,
                position_y__lt=self.position_y + self.height,
                position_y__gte=self.position_y - self.height + 1,
            ).exclude(id=self.id)
            
            if overlapping.exists():
                raise ValidationError("Widget position overlaps with existing widget")
        
        # Validate widget configuration based on type
        if self.widget_type == 'chart' and 'chart_type' not in self.config:
            raise ValidationError("Chart widgets must specify chart_type in config")
        
        if self.widget_type == 'metric' and 'metric_source' not in self.config:
            raise ValidationError("Metric widgets must specify metric_source in config")
