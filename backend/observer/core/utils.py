"""
Core utilities for the Observer Eye Platform.
Provides common functionality used across all Django apps.
"""

import hashlib
import secrets
import string
import re
from typing import Dict, Any, Optional, List
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import structlog

logger = structlog.get_logger(__name__)


class PasswordValidator:
    """
    Password validation utility that enforces Observer Eye Platform password policies.
    Requirements: minimum 16 characters, mixed case, numbers, special characters.
    """
    
    MIN_LENGTH = 16
    REQUIRED_PATTERNS = {
        'lowercase': r'[a-z]',
        'uppercase': r'[A-Z]',
        'digit': r'\d',
        'special': r'[!@#$%^&*(),.?":{}|<>]'
    }
    
    @classmethod
    def validate_password(cls, password: str) -> Dict[str, Any]:
        """
        Validate password against all requirements.
        
        Args:
            password: The password to validate
            
        Returns:
            Dict containing validation results and strength assessment
        """
        results = {
            'is_valid': True,
            'errors': [],
            'strength': 'low',
            'requirements_met': {}
        }
        
        # Check length
        if len(password) < cls.MIN_LENGTH:
            results['is_valid'] = False
            results['errors'].append(f'Password must be at least {cls.MIN_LENGTH} characters long')
            results['requirements_met']['length'] = False
        else:
            results['requirements_met']['length'] = True
        
        # Check pattern requirements
        for requirement, pattern in cls.REQUIRED_PATTERNS.items():
            if re.search(pattern, password):
                results['requirements_met'][requirement] = True
            else:
                results['is_valid'] = False
                results['errors'].append(f'Password must contain at least one {requirement} character')
                results['requirements_met'][requirement] = False
        
        # Calculate strength
        results['strength'] = cls._calculate_strength(password, results['requirements_met'])
        
        return results
    
    @classmethod
    def _calculate_strength(cls, password: str, requirements_met: Dict[str, bool]) -> str:
        """Calculate password strength based on various factors."""
        score = 0
        
        # Base score for meeting requirements
        if requirements_met.get('length', False):
            score += 2
        if requirements_met.get('lowercase', False):
            score += 1
        if requirements_met.get('uppercase', False):
            score += 1
        if requirements_met.get('digit', False):
            score += 1
        if requirements_met.get('special', False):
            score += 1
        
        # Bonus points for extra length
        if len(password) >= 20:
            score += 1
        if len(password) >= 24:
            score += 1
        
        # Bonus for character diversity
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.7:
            score += 1
        
        # Determine strength level
        if score >= 7:
            return 'high'
        elif score >= 5:
            return 'medium'
        else:
            return 'low'


class SecurityUtils:
    """Security utilities for the Observer Eye Platform."""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """
        Hash a password with salt using SHA-256.
        
        Args:
            password: The password to hash
            salt: Optional salt, will generate if not provided
            
        Returns:
            Dict containing hash and salt
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Combine password and salt
        salted_password = f"{password}{salt}"
        
        # Hash using SHA-256
        hash_obj = hashlib.sha256(salted_password.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        
        return {
            'hash': password_hash,
            'salt': salt
        }
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify a password against stored hash and salt."""
        computed_hash = SecurityUtils.hash_password(password, salt)['hash']
        return secrets.compare_digest(computed_hash, stored_hash)


class DataValidator:
    """Data validation utilities for input sanitization and validation."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input by removing potentially harmful content.
        
        Args:
            value: The string to sanitize
            max_length: Optional maximum length to truncate to
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Truncate if max_length specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format using regex."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def validate_json_structure(data: Any, required_fields: List[str]) -> Dict[str, Any]:
        """
        Validate JSON data structure.
        
        Args:
            data: The data to validate
            required_fields: List of required field names
            
        Returns:
            Dict containing validation results
        """
        results = {
            'is_valid': True,
            'errors': [],
            'missing_fields': []
        }
        
        if not isinstance(data, dict):
            results['is_valid'] = False
            results['errors'].append('Data must be a JSON object')
            return results
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                results['is_valid'] = False
                results['missing_fields'].append(field)
        
        if results['missing_fields']:
            results['errors'].append(f"Missing required fields: {', '.join(results['missing_fields'])}")
        
        return results


class AuditLogger:
    """Audit logging utility for tracking system events."""
    
    @staticmethod
    def log_event(user, action: str, resource_type: str, resource_id: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None):
        """
        Log an audit event.
        
        Args:
            user: User instance or None for anonymous actions
            action: The action performed
            resource_type: Type of resource affected
            resource_id: ID of the specific resource
            details: Additional details about the event
            ip_address: IP address of the user
            user_agent: User agent string
        """
        from .models import AuditLog
        
        try:
            AuditLog.objects.create(
                user=user,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent or ''
            )
            
            logger.info(
                "Audit event logged",
                user_id=user.id if user else None,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id
            )
        except Exception as e:
            logger.error(
                "Failed to log audit event",
                error=str(e),
                action=action,
                resource_type=resource_type
            )


class MetricsCollector:
    """Utility for collecting and processing metrics data."""
    
    @staticmethod
    def normalize_metric_value(value: Any, metric_type: str) -> float:
        """
        Normalize metric values to consistent float format.
        
        Args:
            value: The metric value to normalize
            metric_type: Type of metric (cpu, memory, disk, etc.)
            
        Returns:
            Normalized float value
        """
        try:
            # Convert to float
            float_value = float(value)
            
            # Apply type-specific normalization
            if metric_type in ['cpu_usage', 'memory_usage', 'disk_usage']:
                # Ensure percentage values are between 0 and 100
                return max(0.0, min(100.0, float_value))
            elif metric_type in ['response_time', 'latency']:
                # Ensure non-negative values for time metrics
                return max(0.0, float_value)
            else:
                return float_value
                
        except (ValueError, TypeError):
            logger.warning(
                "Failed to normalize metric value",
                value=value,
                metric_type=metric_type
            )
            return 0.0
    
    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile value from a list of numbers."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100.0) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            
            if upper_index >= len(sorted_values):
                return sorted_values[lower_index]
            
            return (sorted_values[lower_index] * (1 - weight) + 
                   sorted_values[upper_index] * weight)


class ConfigurationManager:
    """Utility for managing system configuration."""
    
    @staticmethod
    def get_config(key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        from .models import SystemConfiguration
        
        try:
            config = SystemConfiguration.objects.get(key=key, is_active=True)
            return config.value
        except SystemConfiguration.DoesNotExist:
            return default
    
    @staticmethod
    def set_config(key: str, value: Any, description: str = '', is_sensitive: bool = False):
        """Set configuration value."""
        from .models import SystemConfiguration
        
        config, created = SystemConfiguration.objects.get_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
                'is_sensitive': is_sensitive
            }
        )
        
        if not created:
            config.value = value
            config.description = description
            config.is_sensitive = is_sensitive
            config.save()
        
        logger.info(
            "Configuration updated",
            key=key,
            created=created,
            is_sensitive=is_sensitive
        )


class ErrorHandler:
    """Centralized error handling utility."""
    
    @staticmethod
    def handle_validation_error(error: ValidationError) -> Dict[str, Any]:
        """Handle Django validation errors."""
        return {
            'error_type': 'validation_error',
            'message': 'Validation failed',
            'details': error.message_dict if hasattr(error, 'message_dict') else [str(error)]
        }
    
    @staticmethod
    def handle_generic_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle generic exceptions."""
        logger.error(
            "Unhandled error occurred",
            error=str(error),
            error_type=type(error).__name__,
            context=context or {}
        )
        
        return {
            'error_type': 'internal_error',
            'message': 'An internal error occurred',
            'details': str(error) if settings.DEBUG else 'Please contact support'
        }