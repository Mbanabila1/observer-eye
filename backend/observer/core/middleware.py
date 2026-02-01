"""
Custom middleware for the Observer Eye Platform.
Handles session-based authentication and request logging.
"""

import time
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.urls import resolve
from django.conf import settings
import structlog

from .authentication import SessionManager
from .utils import AuditLogger

logger = structlog.get_logger(__name__)


class SessionAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to handle session-based authentication.
    Validates session tokens and sets request.user.
    """
    
    # URLs that don't require authentication
    EXEMPT_URLS = [
        'core:health_check',
        'core:oauth_providers',
        'core:oauth_authorize',
        'core:oauth_callback',
        'core:session_status',
        'admin:index',  # Django admin
    ]
    
    # URL patterns that don't require authentication
    EXEMPT_PATTERNS = [
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        """Process incoming request for session authentication."""
        # Skip authentication for exempt URLs
        if self._is_exempt_url(request):
            return None
        
        # Get session token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        session_token = None
        
        if auth_header.startswith('Bearer '):
            session_token = auth_header[7:]
        elif auth_header.startswith('Token '):
            session_token = auth_header[6:]
        
        # If no token in header, check query parameter (for WebSocket upgrades)
        if not session_token:
            session_token = request.GET.get('token')
        
        # Validate session if token provided
        if session_token:
            session = SessionManager.validate_session(session_token)
            if session:
                request.user = session.user
                request.session_obj = session
                return None
        
        # For API endpoints, return 401 if no valid session
        if request.path.startswith('/api/') and not hasattr(request, 'user'):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        return None
    
    def _is_exempt_url(self, request):
        """Check if URL is exempt from authentication."""
        # Check exempt patterns
        for pattern in self.EXEMPT_PATTERNS:
            if request.path.startswith(pattern):
                return True
        
        # Check exempt URL names
        try:
            resolved = resolve(request.path)
            url_name = f"{resolved.namespace}:{resolved.url_name}" if resolved.namespace else resolved.url_name
            return url_name in self.EXEMPT_URLS
        except Exception:
            return False


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API requests for monitoring and debugging.
    """
    
    def process_request(self, request):
        """Log incoming request."""
        request._start_time = time.time()
        
        # Log API requests
        if request.path.startswith('/api/'):
            logger.info(
                "API request started",
                method=request.method,
                path=request.path,
                user_id=str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
            )
    
    def process_response(self, request, response):
        """Log response information."""
        if hasattr(request, '_start_time') and request.path.startswith('/api/'):
            duration = time.time() - request._start_time
            
            logger.info(
                "API request completed",
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
                user_id=str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
                ip_address=self._get_client_ip(request)
            )
            
            # Log failed requests as audit events
            if response.status_code >= 400 and hasattr(request, 'user'):
                AuditLogger.log_event(
                    user=request.user if request.user.is_authenticated else None,
                    action='api_request_failed',
                    resource_type='api_endpoint',
                    resource_id=request.path,
                    details={
                        'method': request.method,
                        'status_code': response.status_code,
                        'duration_ms': round(duration * 1000, 2)
                    },
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses.
    """
    
    def process_response(self, request, response):
        """Add security headers to response."""
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP header for API responses
        if request.path.startswith('/api/'):
            response['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none';"
        
        # Add CORS headers for API responses
        if request.path.startswith('/api/'):
            origin = request.META.get('HTTP_ORIGIN')
            if origin and origin in settings.CORS_ALLOWED_ORIGINS:
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Credentials'] = 'true'
                response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Requested-With'
        
        return response


class RateLimitingMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware for API endpoints.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Rate limiting configuration
        self.rate_limits = {
            '/api/auth/': {'requests': 10, 'window': 60},  # 10 requests per minute for auth
            '/api/': {'requests': 100, 'window': 60},      # 100 requests per minute for general API
        }
    
    def process_request(self, request):
        """Check rate limits for incoming requests."""
        if not settings.RATELIMIT_ENABLE:
            return None
        
        # Only apply rate limiting to API endpoints
        if not request.path.startswith('/api/'):
            return None
        
        # Get client identifier (IP address or user ID)
        client_id = self._get_client_id(request)
        
        # Find applicable rate limit
        rate_limit = None
        for path_prefix, limit_config in self.rate_limits.items():
            if request.path.startswith(path_prefix):
                rate_limit = limit_config
                break
        
        if not rate_limit:
            return None
        
        # Check rate limit
        if self._is_rate_limited(client_id, request.path, rate_limit):
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                path=request.path,
                limit=rate_limit
            )
            
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'retry_after': rate_limit['window']
            }, status=429)
        
        return None
    
    def _get_client_id(self, request):
        """Get client identifier for rate limiting."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user_{request.user.id}"
        else:
            # Use IP address for anonymous users
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            return f"ip_{ip}"
    
    def _is_rate_limited(self, client_id, path, rate_limit):
        """Check if client has exceeded rate limit."""
        from django.core.cache import cache
        
        cache_key = f"rate_limit_{client_id}_{path}"
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= rate_limit['requests']:
            return True
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, rate_limit['window'])
        return False