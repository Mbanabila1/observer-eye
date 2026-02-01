"""
Authentication utilities for the Observer Eye Platform.
Handles OAuth integration with multiple identity providers.
"""

import requests
import secrets
import hashlib
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
import structlog

from .models import User, IdentityProvider, UserSession
from .utils import SecurityUtils, AuditLogger

logger = structlog.get_logger(__name__)


class OAuthError(Exception):
    """Custom exception for OAuth-related errors."""
    pass


class OAuthManager:
    """
    Manages OAuth authentication flow with multiple identity providers.
    Supports GitHub, GitLab, Google, and Microsoft OAuth.
    """
    
    # OAuth provider configurations
    PROVIDER_CONFIGS = {
        'github': {
            'authorization_url': 'https://github.com/login/oauth/authorize',
            'token_url': 'https://github.com/login/oauth/access_token',
            'user_info_url': 'https://api.github.com/user',
            'scope': 'user:email',
            'user_email_url': 'https://api.github.com/user/emails'
        },
        'gitlab': {
            'authorization_url': 'https://gitlab.com/oauth/authorize',
            'token_url': 'https://gitlab.com/oauth/token',
            'user_info_url': 'https://gitlab.com/api/v4/user',
            'scope': 'read_user'
        },
        'google': {
            'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
            'scope': 'openid email profile'
        },
        'microsoft': {
            'authorization_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            'user_info_url': 'https://graph.microsoft.com/v1.0/me',
            'scope': 'openid email profile'
        }
    }
    
    def __init__(self, provider_name: str):
        """
        Initialize OAuth manager for specific provider.
        
        Args:
            provider_name: Name of the OAuth provider (github, gitlab, google, microsoft)
        """
        self.provider_name = provider_name.lower()
        
        if self.provider_name not in self.PROVIDER_CONFIGS:
            raise ValueError(f"Unsupported OAuth provider: {provider_name}")
        
        self.config = self.PROVIDER_CONFIGS[self.provider_name]
        
        # Get provider configuration from database or settings
        try:
            self.provider = IdentityProvider.objects.get(
                name=self.provider_name,
                is_enabled=True,
                is_active=True
            )
        except IdentityProvider.DoesNotExist:
            # Fallback to settings
            oauth_config = settings.OAUTH_PROVIDERS.get(self.provider_name, {})
            if not oauth_config.get('enabled', False):
                raise OAuthError(f"OAuth provider {provider_name} is not configured or enabled")
            
            self.provider = None
            self.client_id = oauth_config['client_id']
            self.client_secret = oauth_config['client_secret']
        else:
            self.client_id = self.provider.client_id
            self.client_secret = self.provider.client_secret
    
    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            redirect_uri: URI to redirect to after authorization
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        if state is None:
            state = SecurityUtils.generate_secure_token(32)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': self.config['scope'],
            'response_type': 'code',
            'state': state
        }
        
        # Provider-specific parameters
        if self.provider_name == 'google':
            params['access_type'] = 'offline'
            params['prompt'] = 'consent'
        
        authorization_url = self.provider.authorization_url if self.provider else self.config['authorization_url']
        return f"{authorization_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth provider
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            Token response data
        """
        token_url = self.provider.token_url if self.provider else self.config['token_url']
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Observer-Eye-Platform/1.0'
        }
        
        try:
            response = requests.post(token_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            if 'access_token' not in token_data:
                raise OAuthError(f"No access token in response: {token_data}")
            
            return token_data
            
        except requests.RequestException as e:
            logger.error("Failed to exchange code for token", provider=self.provider_name, error=str(e))
            raise OAuthError(f"Failed to exchange authorization code: {str(e)}")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from OAuth provider.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            User information
        """
        user_info_url = self.provider.user_info_url if self.provider else self.config['user_info_url']
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'User-Agent': 'Observer-Eye-Platform/1.0'
        }
        
        try:
            response = requests.get(user_info_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            user_data = response.json()
            
            # Normalize user data across providers
            normalized_data = self._normalize_user_data(user_data, access_token)
            
            return normalized_data
            
        except requests.RequestException as e:
            logger.error("Failed to get user info", provider=self.provider_name, error=str(e))
            raise OAuthError(f"Failed to get user information: {str(e)}")
    
    def _normalize_user_data(self, user_data: Dict[str, Any], access_token: str) -> Dict[str, Any]:
        """
        Normalize user data from different OAuth providers to a common format.
        
        Args:
            user_data: Raw user data from provider
            access_token: OAuth access token
            
        Returns:
            Normalized user data
        """
        normalized = {
            'provider': self.provider_name,
            'external_id': None,
            'email': None,
            'username': None,
            'first_name': None,
            'last_name': None,
            'avatar_url': None
        }
        
        if self.provider_name == 'github':
            normalized.update({
                'external_id': str(user_data.get('id')),
                'username': user_data.get('login'),
                'first_name': user_data.get('name', '').split(' ')[0] if user_data.get('name') else '',
                'last_name': ' '.join(user_data.get('name', '').split(' ')[1:]) if user_data.get('name') else '',
                'avatar_url': user_data.get('avatar_url')
            })
            
            # GitHub requires separate API call for email
            if not user_data.get('email'):
                normalized['email'] = self._get_github_email(access_token)
            else:
                normalized['email'] = user_data.get('email')
                
        elif self.provider_name == 'gitlab':
            normalized.update({
                'external_id': str(user_data.get('id')),
                'email': user_data.get('email'),
                'username': user_data.get('username'),
                'first_name': user_data.get('name', '').split(' ')[0] if user_data.get('name') else '',
                'last_name': ' '.join(user_data.get('name', '').split(' ')[1:]) if user_data.get('name') else '',
                'avatar_url': user_data.get('avatar_url')
            })
            
        elif self.provider_name == 'google':
            normalized.update({
                'external_id': user_data.get('id'),
                'email': user_data.get('email'),
                'username': user_data.get('email'),  # Google doesn't have username
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
                'avatar_url': user_data.get('picture')
            })
            
        elif self.provider_name == 'microsoft':
            normalized.update({
                'external_id': user_data.get('id'),
                'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                'username': user_data.get('userPrincipalName'),
                'first_name': user_data.get('givenName', ''),
                'last_name': user_data.get('surname', ''),
                'avatar_url': None  # Microsoft Graph doesn't provide avatar URL directly
            })
        
        return normalized
    
    def _get_github_email(self, access_token: str) -> Optional[str]:
        """Get primary email from GitHub API."""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'User-Agent': 'Observer-Eye-Platform/1.0'
            }
            
            response = requests.get(self.config['user_email_url'], headers=headers, timeout=30)
            response.raise_for_status()
            
            emails = response.json()
            
            # Find primary email
            for email_data in emails:
                if email_data.get('primary', False):
                    return email_data.get('email')
            
            # Fallback to first email
            if emails:
                return emails[0].get('email')
                
        except requests.RequestException as e:
            logger.warning("Failed to get GitHub email", error=str(e))
        
        return None


class SessionManager:
    """
    Manages user sessions for the Observer Eye Platform.
    Handles session creation, validation, and cleanup.
    """
    
    @staticmethod
    def create_session(user: User, ip_address: str, user_agent: str, 
                      expires_hours: int = 24) -> UserSession:
        """
        Create a new user session.
        
        Args:
            user: User instance
            ip_address: Client IP address
            user_agent: Client user agent
            expires_hours: Session expiration in hours
            
        Returns:
            Created UserSession instance
        """
        # Generate secure session token
        session_token = SecurityUtils.generate_secure_token(64)
        
        # Calculate expiration time
        expires_at = timezone.now() + timezone.timedelta(hours=expires_hours)
        
        # Create session
        session = UserSession.objects.create(
            user=user,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Update user's last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Log audit event
        AuditLogger.log_event(
            user=user,
            action='session_created',
            resource_type='user_session',
            resource_id=str(session.id),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(
            "User session created",
            user_id=str(user.id),
            session_id=str(session.id),
            ip_address=ip_address
        )
        
        return session
    
    @staticmethod
    def validate_session(session_token: str) -> Optional[UserSession]:
        """
        Validate a session token and return the session if valid.
        
        Args:
            session_token: Session token to validate
            
        Returns:
            UserSession instance if valid, None otherwise
        """
        try:
            session = UserSession.objects.get(
                session_token=session_token,
                is_expired=False,
                is_active=True
            )
            
            if session.is_valid():
                return session
            else:
                # Session expired, mark as expired
                session.expire()
                return None
                
        except UserSession.DoesNotExist:
            return None
    
    @staticmethod
    def expire_session(session_token: str, user: Optional[User] = None, 
                      ip_address: Optional[str] = None) -> bool:
        """
        Expire a user session.
        
        Args:
            session_token: Session token to expire
            user: User performing the action (for audit)
            ip_address: IP address (for audit)
            
        Returns:
            True if session was expired, False if not found
        """
        try:
            session = UserSession.objects.get(session_token=session_token)
            session.expire()
            
            # Log audit event
            AuditLogger.log_event(
                user=user or session.user,
                action='session_expired',
                resource_type='user_session',
                resource_id=str(session.id),
                ip_address=ip_address
            )
            
            logger.info(
                "User session expired",
                session_id=str(session.id),
                user_id=str(session.user.id)
            )
            
            return True
            
        except UserSession.DoesNotExist:
            return False
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired sessions from the database."""
        expired_count = UserSession.objects.filter(
            expires_at__lt=timezone.now(),
            is_expired=False
        ).update(is_expired=True)
        
        logger.info("Expired sessions cleaned up", count=expired_count)
        
        return expired_count


class AuthenticationService:
    """
    Main authentication service that orchestrates OAuth flow and user management.
    """
    
    @staticmethod
    def initiate_oauth_flow(provider_name: str, redirect_uri: str) -> Tuple[str, str]:
        """
        Initiate OAuth authentication flow.
        
        Args:
            provider_name: OAuth provider name
            redirect_uri: Redirect URI after authentication
            
        Returns:
            Tuple of (authorization_url, state)
        """
        oauth_manager = OAuthManager(provider_name)
        state = SecurityUtils.generate_secure_token(32)
        authorization_url = oauth_manager.get_authorization_url(redirect_uri, state)
        
        return authorization_url, state
    
    @staticmethod
    def complete_oauth_flow(provider_name: str, code: str, redirect_uri: str,
                           ip_address: str, user_agent: str) -> Tuple[User, UserSession]:
        """
        Complete OAuth authentication flow.
        
        Args:
            provider_name: OAuth provider name
            code: Authorization code from provider
            redirect_uri: Redirect URI used in flow
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Tuple of (User, UserSession)
        """
        oauth_manager = OAuthManager(provider_name)
        
        # Exchange code for token
        token_data = oauth_manager.exchange_code_for_token(code, redirect_uri)
        access_token = token_data['access_token']
        
        # Get user information
        user_info = oauth_manager.get_user_info(access_token)
        
        # Find or create user
        user = AuthenticationService._find_or_create_user(user_info)
        
        # Create session
        session = SessionManager.create_session(user, ip_address, user_agent)
        
        # Log successful authentication
        AuditLogger.log_event(
            user=user,
            action='oauth_login',
            resource_type='user',
            resource_id=str(user.id),
            details={'provider': provider_name},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return user, session
    
    @staticmethod
    def _find_or_create_user(user_info: Dict[str, Any]) -> User:
        """
        Find existing user or create new one based on OAuth user info.
        
        Args:
            user_info: Normalized user information from OAuth provider
            
        Returns:
            User instance
        """
        provider = user_info['provider']
        external_id = user_info['external_id']
        email = user_info['email']
        
        if not email:
            raise OAuthError("Email is required for user registration")
        
        # Try to find user by provider and external ID
        try:
            user = User.objects.get(
                identity_provider=provider,
                external_id=external_id,
                is_active=True
            )
            
            # Update user information
            user.email = email
            user.username = user_info.get('username') or email
            user.first_name = user_info.get('first_name', '')
            user.last_name = user_info.get('last_name', '')
            user.save()
            
            return user
            
        except User.DoesNotExist:
            pass
        
        # Try to find user by email
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Link OAuth account to existing user
            user.identity_provider = provider
            user.external_id = external_id
            user.save()
            
            return user
            
        except User.DoesNotExist:
            pass
        
        # Create new user
        user = User.objects.create(
            email=email,
            username=user_info.get('username') or email,
            first_name=user_info.get('first_name', ''),
            last_name=user_info.get('last_name', ''),
            identity_provider=provider,
            external_id=external_id,
            is_active=True
        )
        
        logger.info(
            "New user created via OAuth",
            user_id=str(user.id),
            provider=provider,
            email=email
        )
        
        return user
    
    @staticmethod
    def logout_user(session_token: str, ip_address: Optional[str] = None) -> bool:
        """
        Log out user by expiring their session.
        
        Args:
            session_token: Session token to expire
            ip_address: Client IP address for audit
            
        Returns:
            True if logout successful, False otherwise
        """
        session = SessionManager.validate_session(session_token)
        if session:
            SessionManager.expire_session(session_token, session.user, ip_address)
            
            AuditLogger.log_event(
                user=session.user,
                action='user_logout',
                resource_type='user_session',
                resource_id=str(session.id),
                ip_address=ip_address
            )
            
            return True
        
        return False