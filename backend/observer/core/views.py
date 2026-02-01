"""
Core views for the Observer Eye Platform.
Provides basic system endpoints and utilities.
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
import structlog

from .models import User, UserSession, AuditLog, SystemConfiguration
from .utils import AuditLogger

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for monitoring systems.
    Returns basic system health information.
    """
    try:
        # Check database connectivity
        User.objects.exists()
        
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'environment': getattr(settings, 'ENVIRONMENT', 'development'),
            'database': 'connected',
            'services': {
                'django': 'running',
                'database': 'connected',
            }
        }
        
        return JsonResponse(health_data)
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': 'Database connection failed'
        }, status=503)


@require_http_methods(["GET"])
@login_required
def system_status(request):
    """
    Detailed system status endpoint for administrators.
    Requires authentication.
    """
    try:
        # Gather system statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        active_sessions = UserSession.objects.filter(
            is_expired=False,
            expires_at__gt=timezone.now()
        ).count()
        
        # Recent activity
        recent_logins = AuditLog.objects.filter(
            action='user_login',
            timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        status_data = {
            'status': 'operational',
            'timestamp': timezone.now().isoformat(),
            'statistics': {
                'total_users': total_users,
                'active_users': active_users,
                'active_sessions': active_sessions,
                'recent_logins_24h': recent_logins,
            },
            'system_info': {
                'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
                'debug_mode': settings.DEBUG,
                'environment': getattr(settings, 'ENVIRONMENT', 'development'),
            }
        }
        
        return JsonResponse(status_data)
        
    except Exception as e:
        logger.error("System status check failed", error=str(e))
        return JsonResponse({
            'status': 'error',
            'timestamp': timezone.now().isoformat(),
            'error': 'Failed to retrieve system status'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def configuration_list(request):
    """List system configurations (non-sensitive only)."""
    try:
        configs = SystemConfiguration.objects.filter(
            is_active=True,
            is_sensitive=False
        ).values('key', 'value', 'description', 'updated_at')
        
        return JsonResponse({
            'configurations': list(configs),
            'count': len(configs)
        })
        
    except Exception as e:
        logger.error("Failed to retrieve configurations", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve configurations'}, status=500)


@require_http_methods(["GET"])
@login_required
def configuration_detail(request, key):
    """Get specific configuration by key."""
    try:
        config = get_object_or_404(
            SystemConfiguration,
            key=key,
            is_active=True
        )
        
        # Don't expose sensitive configurations
        if config.is_sensitive and not request.user.is_superuser:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        config_data = {
            'key': config.key,
            'value': config.value if not config.is_sensitive else '***HIDDEN***',
            'description': config.description,
            'is_sensitive': config.is_sensitive,
            'updated_at': config.updated_at.isoformat()
        }
        
        return JsonResponse(config_data)
        
    except Exception as e:
        logger.error("Failed to retrieve configuration", key=key, error=str(e))
        return JsonResponse({'error': 'Configuration not found'}, status=404)


@require_http_methods(["GET"])
@login_required
def user_list(request):
    """List users with pagination."""
    try:
        # Only allow staff users to list all users
        if not request.user.is_staff:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        users = User.objects.filter(is_active=True).order_by('-created_at')
        
        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 20)), 100)  # Max 100 per page
        
        paginator = Paginator(users, page_size)
        page_obj = paginator.get_page(page_number)
        
        user_data = []
        for user in page_obj:
            user_data.append({
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'identity_provider': user.identity_provider,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat()
            })
        
        return JsonResponse({
            'users': user_data,
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error("Failed to retrieve users", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve users'}, status=500)


@require_http_methods(["GET"])
@login_required
def user_detail(request, user_id):
    """Get specific user details."""
    try:
        # Users can only view their own details unless they're staff
        if not request.user.is_staff and str(request.user.id) != str(user_id):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        user = get_object_or_404(User, id=user_id, is_active=True)
        
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'identity_provider': user.identity_provider,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
        }
        
        # Add session information for staff users
        if request.user.is_staff:
            active_sessions = UserSession.objects.filter(
                user=user,
                is_expired=False,
                expires_at__gt=timezone.now()
            ).count()
            user_data['active_sessions'] = active_sessions
        
        return JsonResponse(user_data)
        
    except Exception as e:
        logger.error("Failed to retrieve user", user_id=user_id, error=str(e))
        return JsonResponse({'error': 'User not found'}, status=404)


@require_http_methods(["GET"])
@login_required
def session_list(request):
    """List user sessions."""
    try:
        # Users can only view their own sessions unless they're staff
        if request.user.is_staff:
            sessions = UserSession.objects.all().order_by('-created_at')
        else:
            sessions = UserSession.objects.filter(user=request.user).order_by('-created_at')
        
        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        
        paginator = Paginator(sessions, page_size)
        page_obj = paginator.get_page(page_number)
        
        session_data = []
        for session in page_obj:
            session_data.append({
                'id': str(session.id),
                'user_email': session.user.email,
                'session_token': session.session_token[:8] + '...',
                'ip_address': session.ip_address,
                'is_expired': session.is_expired,
                'expires_at': session.expires_at.isoformat(),
                'created_at': session.created_at.isoformat(),
                'is_valid': session.is_valid()
            })
        
        return JsonResponse({
            'sessions': session_data,
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error("Failed to retrieve sessions", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve sessions'}, status=500)


@require_http_methods(["GET"])
@login_required
def session_detail(request, session_id):
    """Get specific session details."""
    try:
        session = get_object_or_404(UserSession, id=session_id)
        
        # Users can only view their own sessions unless they're staff
        if not request.user.is_staff and session.user != request.user:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        session_data = {
            'id': str(session.id),
            'user_email': session.user.email,
            'session_token': session.session_token[:8] + '...',
            'ip_address': session.ip_address,
            'user_agent': session.user_agent,
            'is_expired': session.is_expired,
            'expires_at': session.expires_at.isoformat(),
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'is_valid': session.is_valid()
        }
        
        return JsonResponse(session_data)
        
    except Exception as e:
        logger.error("Failed to retrieve session", session_id=session_id, error=str(e))
        return JsonResponse({'error': 'Session not found'}, status=404)


@require_http_methods(["GET"])
@login_required
def audit_log_list(request):
    """List audit logs (staff only)."""
    try:
        if not request.user.is_staff:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        logs = AuditLog.objects.all().order_by('-timestamp')
        
        # Filtering
        action = request.GET.get('action')
        if action:
            logs = logs.filter(action=action)
        
        resource_type = request.GET.get('resource_type')
        if resource_type:
            logs = logs.filter(resource_type=resource_type)
        
        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 50)), 100)
        
        paginator = Paginator(logs, page_size)
        page_obj = paginator.get_page(page_number)
        
        log_data = []
        for log in page_obj:
            log_data.append({
                'id': str(log.id),
                'user_email': log.user.email if log.user else None,
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'ip_address': log.ip_address,
                'timestamp': log.timestamp.isoformat(),
                'details': log.details
            })
        
        return JsonResponse({
            'logs': log_data,
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error("Failed to retrieve audit logs", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve audit logs'}, status=500)


@require_http_methods(["GET"])
@login_required
def audit_log_detail(request, log_id):
    """Get specific audit log details (staff only)."""
    try:
        if not request.user.is_staff:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        log = get_object_or_404(AuditLog, id=log_id)
        
        log_data = {
            'id': str(log.id),
            'user_email': log.user.email if log.user else None,
            'action': log.action,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'timestamp': log.timestamp.isoformat(),
            'details': log.details,
            'created_at': log.created_at.isoformat()
        }
        
        return JsonResponse(log_data)
        
    except Exception as e:
        logger.error("Failed to retrieve audit log", log_id=log_id, error=str(e))
        return JsonResponse({'error': 'Audit log not found'}, status=404)
