"""
Django signals for the Observer Eye Platform core app.
Handles model lifecycle events and audit logging.
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
import structlog

from .models import User, UserSession, AuditLog
from .utils import AuditLogger

logger = structlog.get_logger(__name__)


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Handle user creation and updates."""
    if created:
        # Log user creation
        AuditLogger.log_event(
            user=instance,
            action='user_created',
            resource_type='user',
            resource_id=str(instance.id),
            details={
                'email': instance.email,
                'identity_provider': instance.identity_provider
            }
        )
        
        logger.info(
            "User created",
            user_id=str(instance.id),
            email=instance.email,
            identity_provider=instance.identity_provider
        )


@receiver(pre_save, sender=UserSession)
def user_session_pre_save(sender, instance, **kwargs):
    """Handle user session updates."""
    if instance.pk:
        try:
            old_instance = UserSession.objects.get(pk=instance.pk)
            
            # Check if session is being expired
            if not old_instance.is_expired and instance.is_expired:
                AuditLogger.log_event(
                    user=instance.user,
                    action='session_expired',
                    resource_type='user_session',
                    resource_id=str(instance.id),
                    details={
                        'ip_address': instance.ip_address,
                        'expires_at': instance.expires_at.isoformat()
                    }
                )
        except UserSession.DoesNotExist:
            # This is a new session, will be handled by post_save
            pass


@receiver(post_save, sender=UserSession)
def user_session_post_save(sender, instance, created, **kwargs):
    """Handle user session creation."""
    if created:
        logger.info(
            "User session created",
            user_id=str(instance.user.id),
            session_id=str(instance.id),
            ip_address=instance.ip_address,
            expires_at=instance.expires_at.isoformat()
        )


@receiver(post_delete, sender=User)
def user_post_delete(sender, instance, **kwargs):
    """Handle user deletion."""
    AuditLogger.log_event(
        user=None,  # User is being deleted
        action='user_deleted',
        resource_type='user',
        resource_id=str(instance.id),
        details={
            'email': instance.email,
            'identity_provider': instance.identity_provider
        }
    )
    
    logger.info(
        "User deleted",
        user_id=str(instance.id),
        email=instance.email
    )


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Handle user login events."""
    # Get client information
    ip_address = request.META.get('REMOTE_ADDR', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Log login event
    AuditLogger.log_event(
        user=user,
        action='user_login',
        resource_type='user',
        resource_id=str(user.id),
        details={
            'login_method': 'django_auth'
        },
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    logger.info(
        "User logged in",
        user_id=str(user.id),
        email=user.email,
        ip_address=ip_address
    )


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """Handle user logout events."""
    if user:
        # Get client information
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Log logout event
        AuditLogger.log_event(
            user=user,
            action='user_logout',
            resource_type='user',
            resource_id=str(user.id),
            details={
                'logout_method': 'django_auth'
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(
            "User logged out",
            user_id=str(user.id),
            email=user.email,
            ip_address=ip_address
        )