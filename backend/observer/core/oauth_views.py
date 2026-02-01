"""
OAuth authentication views for the Observer Eye Platform.
Handles OAuth flow endpoints for multiple identity providers.
"""

import json
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
import structlog

from .authentication import AuthenticationService, OAuthError
from .utils import DataValidator, AuditLogger

logger = structlog.get_logger(__name__)


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@require_http_methods(["GET"])
def oauth_providers(request):
    """
    List available OAuth providers.
    Returns configuration for enabled OAuth providers.
    """
    try:
        providers = []
        
        for provider_name, config in settings.OAUTH_PROVIDERS.items():
            if config.get('enabled', False):
                providers.append({
                    'name': provider_name,
                    'display_name': provider_name.title(),
                    'authorization_url': f"/api/auth/oauth/{provider_name}/authorize/"
                })
        
        return JsonResponse({
            'providers': providers,
            'count': len(providers)
        })
        
    except Exception as e:
        logger.error("Failed to list OAuth providers", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve OAuth providers'}, status=500)


@require_http_methods(["GET"])
def oauth_authorize(request, provider):
    """
    Initiate OAuth authorization flow.
    Redirects user to OAuth provider's authorization page.
    """
    try:
        # Validate provider
        provider = provider.lower()
        if provider not in settings.OAUTH_PROVIDERS:
            return JsonResponse({'error': 'Unsupported OAuth provider'}, status=400)
        
        if not settings.OAUTH_PROVIDERS[provider].get('enabled', False):
            return JsonResponse({'error': 'OAuth provider is disabled'}, status=400)
        
        # Get redirect URI from request or use default
        redirect_uri = request.GET.get('redirect_uri')
        if not redirect_uri:
            redirect_uri = request.build_absolute_uri(
                reverse('core:oauth_callback', kwargs={'provider': provider})
            )
        
        # Validate redirect URI
        if not DataValidator.validate_url(redirect_uri):
            return JsonResponse({'error': 'Invalid redirect URI'}, status=400)
        
        # Initiate OAuth flow
        authorization_url, state = AuthenticationService.initiate_oauth_flow(
            provider, redirect_uri
        )
        
        # Store state in cache for validation (expires in 10 minutes)
        cache_key = f"oauth_state_{state}"
        cache.set(cache_key, {
            'provider': provider,
            'redirect_uri': redirect_uri,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }, timeout=600)
        
        # Log authorization attempt
        AuditLogger.log_event(
            user=None,
            action='oauth_authorize_initiated',
            resource_type='oauth_flow',
            details={'provider': provider},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return HttpResponseRedirect(authorization_url)
        
    except OAuthError as e:
        logger.error("OAuth authorization failed", provider=provider, error=str(e))
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error("Unexpected error in OAuth authorization", provider=provider, error=str(e))
        return JsonResponse({'error': 'OAuth authorization failed'}, status=500)


@require_http_methods(["GET"])
def oauth_callback(request, provider):
    """
    Handle OAuth callback from provider.
    Completes the OAuth flow and creates user session.
    """
    try:
        # Validate provider
        provider = provider.lower()
        if provider not in settings.OAUTH_PROVIDERS:
            return JsonResponse({'error': 'Unsupported OAuth provider'}, status=400)
        
        # Get authorization code and state
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        # Check for OAuth errors
        if error:
            error_description = request.GET.get('error_description', error)
            logger.warning("OAuth provider returned error", provider=provider, error=error_description)
            return JsonResponse({
                'error': 'OAuth authorization failed',
                'details': error_description
            }, status=400)
        
        if not code:
            return JsonResponse({'error': 'Authorization code not provided'}, status=400)
        
        if not state:
            return JsonResponse({'error': 'State parameter not provided'}, status=400)
        
        # Validate state parameter
        cache_key = f"oauth_state_{state}"
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            logger.warning("Invalid or expired OAuth state", provider=provider, state=state)
            return JsonResponse({'error': 'Invalid or expired authorization request'}, status=400)
        
        # Remove state from cache
        cache.delete(cache_key)
        
        # Validate that the provider matches
        if cached_data['provider'] != provider:
            return JsonResponse({'error': 'Provider mismatch'}, status=400)
        
        # Complete OAuth flow
        redirect_uri = cached_data['redirect_uri']
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        user, session = AuthenticationService.complete_oauth_flow(
            provider, code, redirect_uri, ip_address, user_agent
        )
        
        # Return session information
        response_data = {
            'success': True,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'identity_provider': user.identity_provider
            },
            'session': {
                'token': session.session_token,
                'expires_at': session.expires_at.isoformat()
            }
        }
        
        # If this is a web request, redirect to frontend with session token
        if request.GET.get('web', '').lower() == 'true':
            frontend_url = settings.CORS_ALLOWED_ORIGINS[0] if settings.CORS_ALLOWED_ORIGINS else 'http://localhost:4200'
            redirect_url = f"{frontend_url}/auth/callback?token={session.session_token}&success=true"
            return HttpResponseRedirect(redirect_url)
        
        return JsonResponse(response_data)
        
    except OAuthError as e:
        logger.error("OAuth callback failed", provider=provider, error=str(e))
        
        # If this is a web request, redirect to frontend with error
        if request.GET.get('web', '').lower() == 'true':
            frontend_url = settings.CORS_ALLOWED_ORIGINS[0] if settings.CORS_ALLOWED_ORIGINS else 'http://localhost:4200'
            redirect_url = f"{frontend_url}/auth/callback?error={str(e)}"
            return HttpResponseRedirect(redirect_url)
        
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error("Unexpected error in OAuth callback", provider=provider, error=str(e))
        
        # If this is a web request, redirect to frontend with error
        if request.GET.get('web', '').lower() == 'true':
            frontend_url = settings.CORS_ALLOWED_ORIGINS[0] if settings.CORS_ALLOWED_ORIGINS else 'http://localhost:4200'
            redirect_url = f"{frontend_url}/auth/callback?error=Authentication failed"
            return HttpResponseRedirect(redirect_url)
        
        return JsonResponse({'error': 'OAuth callback failed'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SessionView(View):
    """Handle session-related operations."""
    
    def get(self, request):
        """Get current session information."""
        try:
            # Get session token from header or query parameter
            session_token = request.META.get('HTTP_AUTHORIZATION')
            if session_token and session_token.startswith('Bearer '):
                session_token = session_token[7:]
            else:
                session_token = request.GET.get('token')
            
            if not session_token:
                return JsonResponse({'error': 'Session token required'}, status=401)
            
            # Validate session
            from .authentication import SessionManager
            session = SessionManager.validate_session(session_token)
            
            if not session:
                return JsonResponse({'error': 'Invalid or expired session'}, status=401)
            
            # Return session and user information
            return JsonResponse({
                'valid': True,
                'user': {
                    'id': str(session.user.id),
                    'email': session.user.email,
                    'username': session.user.username,
                    'first_name': session.user.first_name,
                    'last_name': session.user.last_name,
                    'identity_provider': session.user.identity_provider,
                    'is_staff': session.user.is_staff,
                    'last_login': session.user.last_login.isoformat() if session.user.last_login else None
                },
                'session': {
                    'expires_at': session.expires_at.isoformat(),
                    'created_at': session.created_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error("Failed to validate session", error=str(e))
            return JsonResponse({'error': 'Session validation failed'}, status=500)
    
    def delete(self, request):
        """Logout user by expiring session."""
        try:
            # Get session token from header or request body
            session_token = request.META.get('HTTP_AUTHORIZATION')
            if session_token and session_token.startswith('Bearer '):
                session_token = session_token[7:]
            else:
                # Try to get from request body
                try:
                    data = json.loads(request.body)
                    session_token = data.get('token')
                except (json.JSONDecodeError, AttributeError):
                    session_token = None
            
            if not session_token:
                return JsonResponse({'error': 'Session token required'}, status=400)
            
            # Logout user
            success = AuthenticationService.logout_user(
                session_token,
                get_client_ip(request)
            )
            
            if success:
                return JsonResponse({'success': True, 'message': 'Logged out successfully'})
            else:
                return JsonResponse({'error': 'Invalid session token'}, status=400)
                
        except Exception as e:
            logger.error("Failed to logout user", error=str(e))
            return JsonResponse({'error': 'Logout failed'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def refresh_session(request):
    """
    Refresh user session to extend expiration.
    """
    try:
        # Get session token
        session_token = request.META.get('HTTP_AUTHORIZATION')
        if session_token and session_token.startswith('Bearer '):
            session_token = session_token[7:]
        else:
            try:
                data = json.loads(request.body)
                session_token = data.get('token')
            except (json.JSONDecodeError, AttributeError):
                return JsonResponse({'error': 'Session token required'}, status=400)
        
        if not session_token:
            return JsonResponse({'error': 'Session token required'}, status=400)
        
        # Validate current session
        from .authentication import SessionManager
        session = SessionManager.validate_session(session_token)
        
        if not session:
            return JsonResponse({'error': 'Invalid or expired session'}, status=401)
        
        # Create new session (effectively refreshing)
        new_session = SessionManager.create_session(
            session.user,
            get_client_ip(request),
            request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Expire old session
        SessionManager.expire_session(session_token)
        
        return JsonResponse({
            'success': True,
            'session': {
                'token': new_session.session_token,
                'expires_at': new_session.expires_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error("Failed to refresh session", error=str(e))
        return JsonResponse({'error': 'Session refresh failed'}, status=500)


@require_http_methods(["GET"])
def session_status(request):
    """
    Check session status without full validation.
    Useful for frontend to check if user is logged in.
    """
    try:
        # Get session token
        session_token = request.META.get('HTTP_AUTHORIZATION')
        if session_token and session_token.startswith('Bearer '):
            session_token = session_token[7:]
        else:
            session_token = request.GET.get('token')
        
        if not session_token:
            return JsonResponse({'authenticated': False})
        
        # Quick session check
        from .authentication import SessionManager
        session = SessionManager.validate_session(session_token)
        
        return JsonResponse({
            'authenticated': session is not None,
            'expires_at': session.expires_at.isoformat() if session else None
        })
        
    except Exception as e:
        logger.error("Failed to check session status", error=str(e))
        return JsonResponse({'authenticated': False})