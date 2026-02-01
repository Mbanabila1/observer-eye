import json
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from core.models import BaseModel, User


class NotificationChannel(BaseModel):
    """
    Configuration for different notification delivery channels.
    Supports email, SMS, webhooks, and other messaging platforms.
    """
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('discord', 'Discord'),
        ('pagerduty', 'PagerDuty'),
    ]
    
    name = models.CharField(max_length=100, help_text="Human-readable name for this channel")
    channel_type = models.CharField(max_length=50, choices=CHANNEL_TYPES)
    configuration = models.JSONField(
        help_text="Channel-specific configuration (e.g., email addresses, webhook URLs, API keys)"
    )
    is_enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_channels')
    
    # Rate limiting settings
    rate_limit_per_hour = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text="Maximum notifications per hour for this channel"
    )
    
    # Retry settings
    max_retries = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    retry_delay_seconds = models.PositiveIntegerField(
        default=300,  # 5 minutes
        validators=[MinValueValidator(60), MaxValueValidator(3600)]
    )
    
    class Meta:
        db_table = 'notification_channel'
        indexes = [
            models.Index(fields=['channel_type', 'is_enabled']),
            models.Index(fields=['created_by']),
        ]
        unique_together = ['name', 'created_by']
    
    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"
    
    def validate_configuration(self):
        """Validate channel-specific configuration"""
        if self.channel_type == 'email':
            required_fields = ['recipients']
            if not all(field in self.configuration for field in required_fields):
                raise ValueError("Email channel requires 'recipients' field")
            if not isinstance(self.configuration['recipients'], list):
                raise ValueError("Email recipients must be a list")
                
        elif self.channel_type == 'webhook':
            required_fields = ['url']
            if not all(field in self.configuration for field in required_fields):
                raise ValueError("Webhook channel requires 'url' field")
                
        elif self.channel_type == 'sms':
            required_fields = ['phone_numbers']
            if not all(field in self.configuration for field in required_fields):
                raise ValueError("SMS channel requires 'phone_numbers' field")
    
    def save(self, *args, **kwargs):
        self.validate_configuration()
        super().save(*args, **kwargs)


class AlertRule(BaseModel):
    """
    Configurable alert rules with complex conditions and thresholds.
    Supports multiple conditions, escalation policies, and notification scheduling.
    """
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    CONDITION_OPERATORS = [
        ('gt', 'Greater Than'),
        ('gte', 'Greater Than or Equal'),
        ('lt', 'Less Than'),
        ('lte', 'Less Than or Equal'),
        ('eq', 'Equal'),
        ('ne', 'Not Equal'),
        ('contains', 'Contains'),
        ('not_contains', 'Does Not Contain'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Alert conditions (JSON structure for complex rules)
    conditions = models.JSONField(
        help_text="Complex alert conditions with multiple criteria"
    )
    
    # Threshold and evaluation settings
    threshold_value = models.FloatField(null=True, blank=True)
    evaluation_window_minutes = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],  # 1 minute to 24 hours
        help_text="Time window for evaluating conditions"
    )
    
    # Alert metadata
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    tags = models.JSONField(default=dict, help_text="Key-value tags for categorization")
    
    # Notification settings
    notification_channels = models.ManyToManyField(
        NotificationChannel,
        through='AlertRuleNotificationChannel',
        related_name='alert_rules'
    )
    
    # Escalation and scheduling
    escalation_policy = models.JSONField(
        default=dict,
        help_text="Escalation rules for unacknowledged alerts"
    )
    notification_schedule = models.JSONField(
        default=dict,
        help_text="Schedule for when notifications should be sent"
    )
    
    # Deduplication settings
    deduplication_window_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        help_text="Time window for deduplicating similar alerts"
    )
    deduplication_fields = models.JSONField(
        default=list,
        help_text="Fields to use for alert deduplication"
    )
    
    # Control settings
    is_enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alert_rules')
    
    class Meta:
        db_table = 'notification_alert_rule'
        indexes = [
            models.Index(fields=['is_enabled', 'severity']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"
    
    def evaluate_conditions(self, data):
        """Evaluate alert conditions against provided data"""
        try:
            # This is a simplified evaluation - in practice, you'd want a more robust
            # expression evaluator or rule engine
            for condition in self.conditions.get('rules', []):
                field = condition.get('field')
                operator = condition.get('operator')
                value = condition.get('value')
                
                if field not in data:
                    continue
                    
                data_value = data[field]
                
                if operator == 'gt' and not (data_value > value):
                    return False
                elif operator == 'gte' and not (data_value >= value):
                    return False
                elif operator == 'lt' and not (data_value < value):
                    return False
                elif operator == 'lte' and not (data_value <= value):
                    return False
                elif operator == 'eq' and not (data_value == value):
                    return False
                elif operator == 'ne' and not (data_value != value):
                    return False
                elif operator == 'contains' and value not in str(data_value):
                    return False
                elif operator == 'not_contains' and value in str(data_value):
                    return False
            
            return True
        except Exception:
            return False


class AlertRuleNotificationChannel(BaseModel):
    """
    Through model for AlertRule and NotificationChannel relationship.
    Allows for channel-specific settings per alert rule.
    """
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE)
    notification_channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)
    
    # Channel-specific settings for this alert rule
    delay_minutes = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(1440)],
        help_text="Delay before sending notification through this channel"
    )
    is_escalation = models.BooleanField(
        default=False,
        help_text="Whether this channel is part of escalation policy"
    )
    escalation_level = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    class Meta:
        db_table = 'notification_alert_rule_channel'
        unique_together = ['alert_rule', 'notification_channel']
        indexes = [
            models.Index(fields=['alert_rule', 'escalation_level']),
        ]


class Alert(BaseModel):
    """
    Individual alert instances generated from alert rules.
    Tracks alert lifecycle, acknowledgments, and resolution.
    """
    STATUS_CHOICES = [
        ('triggered', 'Triggered'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('suppressed', 'Suppressed'),
    ]
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='alerts')
    
    # Alert identification and deduplication
    fingerprint = models.CharField(
        max_length=64,
        help_text="Unique fingerprint for deduplication"
    )
    
    # Alert timing
    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Alert content
    title = models.CharField(max_length=255)
    message = models.TextField()
    metadata = models.JSONField(default=dict, help_text="Additional alert context and data")
    
    # Alert management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='triggered')
    acknowledged_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='acknowledged_alerts'
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    
    # Escalation tracking
    escalation_level = models.PositiveIntegerField(default=0)
    last_escalated_at = models.DateTimeField(null=True, blank=True)
    
    # Notification tracking
    notification_count = models.PositiveIntegerField(default=0)
    last_notification_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notification_alert'
        indexes = [
            models.Index(fields=['rule', 'status']),
            models.Index(fields=['fingerprint', 'status']),
            models.Index(fields=['triggered_at', 'status']),
            models.Index(fields=['status', 'escalation_level']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def acknowledge(self, user):
        """Acknowledge the alert"""
        if self.status == 'triggered':
            self.status = 'acknowledged'
            self.acknowledged_by = user
            self.acknowledged_at = timezone.now()
            self.save(update_fields=['status', 'acknowledged_by', 'acknowledged_at', 'updated_at'])
    
    def resolve(self, user):
        """Resolve the alert"""
        if self.status in ['triggered', 'acknowledged']:
            self.status = 'resolved'
            self.resolved_by = user
            self.resolved_at = timezone.now()
            self.save(update_fields=['status', 'resolved_by', 'resolved_at', 'updated_at'])
    
    def suppress(self):
        """Suppress the alert"""
        if self.status == 'triggered':
            self.status = 'suppressed'
            self.save(update_fields=['status', 'updated_at'])
    
    def should_escalate(self):
        """Check if alert should be escalated"""
        if self.status != 'triggered':
            return False
            
        escalation_policy = self.rule.escalation_policy
        if not escalation_policy.get('enabled', False):
            return False
            
        escalation_intervals = escalation_policy.get('intervals', [])
        if self.escalation_level >= len(escalation_intervals):
            return False
            
        if not self.last_escalated_at:
            # First escalation based on trigger time
            time_since_trigger = timezone.now() - self.triggered_at
        else:
            # Subsequent escalations based on last escalation
            time_since_escalation = timezone.now() - self.last_escalated_at
            
        required_interval = escalation_intervals[self.escalation_level]
        return time_since_trigger.total_seconds() >= required_interval * 60
    
    def escalate(self):
        """Escalate the alert to the next level"""
        if self.should_escalate():
            self.escalation_level += 1
            self.last_escalated_at = timezone.now()
            self.save(update_fields=['escalation_level', 'last_escalated_at', 'updated_at'])
            return True
        return False


class NotificationDelivery(BaseModel):
    """
    Track individual notification deliveries for audit and retry purposes.
    """
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]
    
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='deliveries')
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)
    
    # Delivery tracking
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Retry tracking
    retry_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery details
    recipient = models.CharField(max_length=255, help_text="Actual recipient (email, phone, etc.)")
    message_content = models.TextField()
    response_data = models.JSONField(default=dict, help_text="Response from delivery service")
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'notification_delivery'
        indexes = [
            models.Index(fields=['alert', 'channel']),
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"Delivery to {self.recipient} via {self.channel.name} - {self.get_status_display()}"
    
    def mark_sent(self):
        """Mark delivery as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_delivered(self):
        """Mark delivery as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])
    
    def mark_failed(self, error_message):
        """Mark delivery as failed and schedule retry if applicable"""
        self.status = 'failed'
        self.error_message = error_message
        
        if self.retry_count < self.channel.max_retries:
            self.status = 'retrying'
            self.retry_count += 1
            self.next_retry_at = timezone.now() + timedelta(seconds=self.channel.retry_delay_seconds)
        
        self.save(update_fields=['status', 'error_message', 'retry_count', 'next_retry_at', 'updated_at'])


class NotificationTemplate(BaseModel):
    """
    Templates for formatting notifications across different channels.
    """
    TEMPLATE_TYPES = [
        ('alert_triggered', 'Alert Triggered'),
        ('alert_acknowledged', 'Alert Acknowledged'),
        ('alert_resolved', 'Alert Resolved'),
        ('alert_escalated', 'Alert Escalated'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    channel_type = models.CharField(max_length=50, choices=NotificationChannel.CHANNEL_TYPES)
    
    # Template content
    subject_template = models.CharField(max_length=255, blank=True)
    body_template = models.TextField()
    
    # Template settings
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_templates')
    
    class Meta:
        db_table = 'notification_template'
        indexes = [
            models.Index(fields=['template_type', 'channel_type']),
            models.Index(fields=['is_default']),
        ]
        unique_together = ['template_type', 'channel_type', 'is_default']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()} - {self.get_channel_type_display()})"
    
    def render(self, context):
        """Render template with provided context"""
        from django.template import Template, Context
        
        subject = Template(self.subject_template).render(Context(context)) if self.subject_template else ""
        body = Template(self.body_template).render(Context(context))
        
        return {
            'subject': subject,
            'body': body
        }
