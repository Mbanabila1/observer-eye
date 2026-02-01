from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from core.models import BaseModel
import json
from typing import Any, Dict, List, Optional

User = get_user_model()


class ConfigurationCategory(BaseModel):
    """
    Categories for organizing configuration settings.
    """
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Icon class for UI
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'settings_configuration_category'
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Configuration Categories'
    
    def __str__(self):
        return self.display_name


class ConfigurationSetting(BaseModel):
    """
    Individual configuration settings for the platform.
    """
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON Object'),
        ('list', 'List'),
        ('password', 'Password'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('choice', 'Choice'),
    ]
    
    category = models.ForeignKey(
        ConfigurationCategory, 
        on_delete=models.CASCADE,
        related_name='settings'
    )
    key = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES)
    default_value = models.JSONField(null=True, blank=True)
    current_value = models.JSONField(null=True, blank=True)
    is_sensitive = models.BooleanField(default=False)
    is_required = models.BooleanField(default=False)
    is_readonly = models.BooleanField(default=False)
    validation_rules = models.JSONField(default=dict, blank=True)
    choices = models.JSONField(null=True, blank=True)  # For choice type settings
    help_text = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'settings_configuration_setting'
        ordering = ['category__sort_order', 'sort_order', 'key']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['category', 'sort_order']),
        ]
    
    def __str__(self):
        return f"{self.category.name}.{self.key}"
    
    def clean(self):
        """Validate the setting configuration."""
        super().clean()
        
        # Validate that choices are provided for choice type
        if self.setting_type == 'choice' and not self.choices:
            raise ValidationError("Choices must be provided for choice type settings")
        
        # Validate default value against type
        if self.default_value is not None:
            self._validate_value(self.default_value)
        
        # Validate current value against type
        if self.current_value is not None:
            self._validate_value(self.current_value)
    
    def _validate_value(self, value: Any) -> None:
        """Validate a value against the setting type and rules."""
        if self.setting_type == 'string':
            if not isinstance(value, str):
                raise ValidationError(f"Value must be a string for {self.key}")
        elif self.setting_type == 'integer':
            if not isinstance(value, int):
                raise ValidationError(f"Value must be an integer for {self.key}")
        elif self.setting_type == 'float':
            if not isinstance(value, (int, float)):
                raise ValidationError(f"Value must be a number for {self.key}")
        elif self.setting_type == 'boolean':
            if not isinstance(value, bool):
                raise ValidationError(f"Value must be a boolean for {self.key}")
        elif self.setting_type == 'choice':
            if self.choices and value not in [choice['value'] for choice in self.choices]:
                raise ValidationError(f"Value must be one of the allowed choices for {self.key}")
        
        # Apply validation rules
        if self.validation_rules:
            self._apply_validation_rules(value)
    
    def _apply_validation_rules(self, value: Any) -> None:
        """Apply custom validation rules to a value."""
        rules = self.validation_rules
        
        if 'min_length' in rules and isinstance(value, str):
            if len(value) < rules['min_length']:
                raise ValidationError(f"Value must be at least {rules['min_length']} characters")
        
        if 'max_length' in rules and isinstance(value, str):
            if len(value) > rules['max_length']:
                raise ValidationError(f"Value must be at most {rules['max_length']} characters")
        
        if 'min_value' in rules and isinstance(value, (int, float)):
            if value < rules['min_value']:
                raise ValidationError(f"Value must be at least {rules['min_value']}")
        
        if 'max_value' in rules and isinstance(value, (int, float)):
            if value > rules['max_value']:
                raise ValidationError(f"Value must be at most {rules['max_value']}")
        
        if 'pattern' in rules and isinstance(value, str):
            import re
            if not re.match(rules['pattern'], value):
                raise ValidationError(f"Value does not match required pattern for {self.key}")
    
    def get_value(self) -> Any:
        """Get the effective value (current or default)."""
        if self.current_value is not None:
            return self.current_value
        return self.default_value
    
    def set_value(self, value: Any, user: Optional[User] = None) -> None:
        """Set the current value with validation."""
        if self.is_readonly:
            raise ValidationError(f"Setting {self.key} is read-only")
        
        self._validate_value(value)
        self.current_value = value
        self.save()
        
        # Log the change
        if user:
            ConfigurationChangeLog.objects.create(
                setting=self,
                old_value=self.current_value,
                new_value=value,
                changed_by=user
            )


class ConfigurationChangeLog(BaseModel):
    """
    Audit log for configuration changes.
    """
    setting = models.ForeignKey(
        ConfigurationSetting,
        on_delete=models.CASCADE,
        related_name='change_logs'
    )
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    change_reason = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'settings_configuration_change_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['setting', '-created_at']),
            models.Index(fields=['changed_by', '-created_at']),
        ]
    
    def __str__(self):
        user_str = self.changed_by.email if self.changed_by else 'System'
        return f"{self.setting.key} changed by {user_str} at {self.created_at}"


class ConfigurationProfile(BaseModel):
    """
    Configuration profiles for different environments or use cases.
    """
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField()
    is_default = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)  # System profiles cannot be deleted
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'settings_configuration_profile'
        ordering = ['name']
    
    def __str__(self):
        return self.display_name
    
    def save(self, *args, **kwargs):
        # Ensure only one default profile
        if self.is_default:
            ConfigurationProfile.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class ConfigurationProfileSetting(BaseModel):
    """
    Setting values for specific configuration profiles.
    """
    profile = models.ForeignKey(
        ConfigurationProfile,
        on_delete=models.CASCADE,
        related_name='profile_settings'
    )
    setting = models.ForeignKey(
        ConfigurationSetting,
        on_delete=models.CASCADE,
        related_name='profile_values'
    )
    value = models.JSONField()
    
    class Meta:
        db_table = 'settings_configuration_profile_setting'
        unique_together = ['profile', 'setting']
        indexes = [
            models.Index(fields=['profile', 'setting']),
        ]
    
    def __str__(self):
        return f"{self.profile.name}.{self.setting.key}"
    
    def clean(self):
        """Validate the profile setting value."""
        super().clean()
        if self.value is not None:
            self.setting._validate_value(self.value)


class ConfigurationDeployment(BaseModel):
    """
    Track configuration deployments and rollbacks.
    """
    DEPLOYMENT_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ]
    
    profile = models.ForeignKey(
        ConfigurationProfile,
        on_delete=models.CASCADE,
        related_name='deployments'
    )
    deployed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=DEPLOYMENT_STATUS, default='pending')
    deployment_notes = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    rollback_deployment = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rollbacks'
    )
    
    class Meta:
        db_table = 'settings_configuration_deployment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Deployment of {self.profile.name} - {self.status}"


class ConfigurationValidationRule(BaseModel):
    """
    Custom validation rules for configuration settings.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    rule_type = models.CharField(
        max_length=50,
        choices=[
            ('regex', 'Regular Expression'),
            ('range', 'Numeric Range'),
            ('length', 'String Length'),
            ('custom', 'Custom Function'),
            ('dependency', 'Setting Dependency'),
        ]
    )
    rule_config = models.JSONField()
    error_message = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'settings_configuration_validation_rule'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def validate_value(self, value: Any, setting: ConfigurationSetting) -> bool:
        """Validate a value against this rule."""
        if not self.is_active:
            return True
        
        try:
            if self.rule_type == 'regex':
                import re
                pattern = self.rule_config.get('pattern', '')
                return bool(re.match(pattern, str(value)))
            
            elif self.rule_type == 'range':
                min_val = self.rule_config.get('min')
                max_val = self.rule_config.get('max')
                if min_val is not None and value < min_val:
                    return False
                if max_val is not None and value > max_val:
                    return False
                return True
            
            elif self.rule_type == 'length':
                min_len = self.rule_config.get('min_length')
                max_len = self.rule_config.get('max_length')
                value_len = len(str(value))
                if min_len is not None and value_len < min_len:
                    return False
                if max_len is not None and value_len > max_len:
                    return False
                return True
            
            elif self.rule_type == 'dependency':
                # Check if dependent setting has required value
                dependent_key = self.rule_config.get('dependent_setting')
                required_value = self.rule_config.get('required_value')
                if dependent_key:
                    try:
                        dependent_setting = ConfigurationSetting.objects.get(key=dependent_key)
                        return dependent_setting.get_value() == required_value
                    except ConfigurationSetting.DoesNotExist:
                        return False
                return True
            
            # Custom validation would require additional implementation
            return True
            
        except Exception:
            return False
