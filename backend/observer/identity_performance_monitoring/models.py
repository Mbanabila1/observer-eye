"""
Identity Performance Monitoring models for the Observer Eye Platform.
Monitors authentication and identity-related performance metrics.
"""

from django.db import models
from django.utils import timezone

from core.models import BaseModel, User


class IdentityProviderMetric(BaseModel):
    """
    Performance metrics for identity providers.
    """
    provider_name = models.CharField(max_length=50, db_index=True)
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('auth_response_time', 'Authentication Response Time'),
            ('token_validation_time', 'Token Validation Time'),
            ('user_info_fetch_time', 'User Info Fetch Time'),
            ('auth_success_rate', 'Authentication Success Rate'),
            ('token_refresh_time', 'Token Refresh Time'),
        ]
    )
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'identity_provider_metric'
        indexes = [
            models.Index(fields=['provider_name', 'metric_type', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.provider_name} - {self.metric_type}: {self.value} {self.unit}"


class AuthenticationEvent(BaseModel):
    """
    Authentication event tracking for performance analysis.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    provider_name = models.CharField(max_length=50)
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('login_attempt', 'Login Attempt'),
            ('login_success', 'Login Success'),
            ('login_failure', 'Login Failure'),
            ('logout', 'Logout'),
            ('token_refresh', 'Token Refresh'),
            ('session_timeout', 'Session Timeout'),
        ]
    )
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'authentication_event'
        indexes = [
            models.Index(fields=['provider_name', 'event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.provider_name} - {self.event_type}"