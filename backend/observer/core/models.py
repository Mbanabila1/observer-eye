import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model that provides common fields for all models.
    Includes UUID primary key, timestamps, and soft delete functionality.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        """Soft delete by setting is_active to False"""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def restore(self):
        """Restore soft deleted object"""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class TimestampedModel(models.Model):
    """
    Abstract model for models that only need timestamp tracking.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class User(AbstractUser):
    """
    Extended user model for Observer Eye Platform.
    Supports OAuth authentication from multiple providers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    identity_provider = models.CharField(
        max_length=50, 
        choices=[
            ('github', 'GitHub'),
            ('gitlab', 'GitLab'),
            ('google', 'Google'),
            ('microsoft', 'Microsoft'),
            ('local', 'Local'),
        ],
        default='local'
    )
    external_id = models.CharField(max_length=255, blank=True, null=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override username to make it optional for OAuth users
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'core_user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['identity_provider', 'external_id']),
        ]

    def __str__(self):
        return self.email or self.username or str(self.id)


class IdentityProvider(BaseModel):
    """
    Configuration for OAuth identity providers.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        choices=[
            ('github', 'GitHub'),
            ('gitlab', 'GitLab'),
            ('google', 'Google'),
            ('microsoft', 'Microsoft'),
        ]
    )
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    authorization_url = models.URLField()
    token_url = models.URLField()
    user_info_url = models.URLField()
    scope = models.CharField(max_length=255, default='openid email profile')
    is_enabled = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'core_identity_provider'
    
    def __str__(self):
        return f"{self.get_name_display()} ({'Enabled' if self.is_enabled else 'Disabled'})"


class UserSession(BaseModel):
    """
    User session tracking for security and analytics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_expired = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'core_user_session'
        indexes = [
            models.Index(fields=['session_token']),
            models.Index(fields=['user', 'is_expired']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} - {self.session_token[:8]}..."
    
    def is_valid(self):
        """Check if session is still valid"""
        return not self.is_expired and self.expires_at > timezone.now()
    
    def expire(self):
        """Expire the session"""
        self.is_expired = True
        self.save(update_fields=['is_expired', 'updated_at'])


class AuditLog(BaseModel):
    """
    Audit log for tracking important system events.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_audit_log'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{user_str} - {self.action} on {self.resource_type}"


class SystemConfiguration(BaseModel):
    """
    System-wide configuration settings.
    """
    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    is_sensitive = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'core_system_configuration'
    
    def __str__(self):
        return f"{self.key}: {'***' if self.is_sensitive else str(self.value)}"
