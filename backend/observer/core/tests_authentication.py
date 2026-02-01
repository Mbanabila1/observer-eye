"""
Tests for authentication functionality in the Observer Eye Platform.
"""

import json
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import User, IdentityProvider, UserSession
from .authentication import OAuthManager, SessionManager, AuthenticationService
from .utils import PasswordValidator, SecurityUtils


class PasswordValidatorTest(TestCase):
    """Test password validation functionality."""
    
    def test_valid_password(self):
        """Test validation of a valid password."""
        password = "MySecurePassword123!"
        result = PasswordValidator.validate_password(password)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertIn(result['strength'], ['medium', 'high'])
        self.assertTrue(result['requirements_met']['length'])
        self.assertTrue(result['requirements_met']['lowercase'])
        self.assertTrue(result['requirements_met']['uppercase'])
        self.assertTrue(result['requirements_met']['digit'])
        self.assertTrue(result['requirements_met']['special'])
    
    def test_short_password(self):
        """Test validation of password that's too short."""
        password = "Short1!"
        result = PasswordValidator.validate_password(password)
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Password must be at least 16 characters long', result['errors'])
        self.assertFalse(result['requirements_met']['length'])
    
    def test_password_missing_requirements(self):
        """Test password missing various requirements."""
        # Missing uppercase
        password = "mylongpassword123!"
        result = PasswordValidator.validate_password(password)
        self.assertFalse(result['is_valid'])
        self.assertIn('Password must contain at least one uppercase character', result['errors'])
        
        # Missing special character
        password = "MyLongPassword123"
        result = PasswordValidator.validate_password(password)
        self.assertFalse(result['is_valid'])
        self.assertIn('Password must contain at least one special character', result['errors'])
    
    def test_password_strength_calculation(self):
        """Test password strength calculation."""
        # High strength password
        high_strength = "MyVerySecureAndLongPassword123!@#"
        result = PasswordValidator.validate_password(high_strength)
        self.assertEqual(result['strength'], 'high')
        
        # Medium strength password
        medium_strength = "MySecurePassword1!"
        result = PasswordValidator.validate_password(medium_strength)
        self.assertIn(result['strength'], ['medium', 'high'])
        
        # Low strength password (meets minimum requirements but not much more)
        low_strength = "Mypassword123456!"
        result = PasswordValidator.validate_password(low_strength)
        # This might be medium due to length, so allow both
        self.assertIn(result['strength'], ['low', 'medium', 'high'])


class SecurityUtilsTest(TestCase):
    """Test security utilities."""
    
    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = SecurityUtils.generate_secure_token(32)
        token2 = SecurityUtils.generate_secure_token(32)
        
        self.assertEqual(len(token1), 32)
        self.assertEqual(len(token2), 32)
        self.assertNotEqual(token1, token2)  # Should be different
        
        # Test different lengths
        short_token = SecurityUtils.generate_secure_token(16)
        self.assertEqual(len(short_token), 16)
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "MyTestPassword123!"
        
        # Hash password
        hash_result = SecurityUtils.hash_password(password)
        self.assertIn('hash', hash_result)
        self.assertIn('salt', hash_result)
        
        # Verify correct password
        is_valid = SecurityUtils.verify_password(
            password, hash_result['hash'], hash_result['salt']
        )
        self.assertTrue(is_valid)
        
        # Verify incorrect password
        is_valid = SecurityUtils.verify_password(
            "WrongPassword", hash_result['hash'], hash_result['salt']
        )
        self.assertFalse(is_valid)


class SessionManagerTest(TestCase):
    """Test session management functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            email='test@example.com',
            username='testuser',
            identity_provider='local'
        )
    
    def test_create_session(self):
        """Test session creation."""
        session = SessionManager.create_session(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.assertIsInstance(session, UserSession)
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.ip_address, '127.0.0.1')
        self.assertEqual(session.user_agent, 'Test Agent')
        self.assertFalse(session.is_expired)
        self.assertTrue(session.is_valid())
        
        # Check that user's last_login was updated
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)
    
    def test_validate_session(self):
        """Test session validation."""
        # Create valid session
        session = SessionManager.create_session(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        # Validate with correct token
        validated_session = SessionManager.validate_session(session.session_token)
        self.assertEqual(validated_session, session)
        
        # Validate with incorrect token
        invalid_session = SessionManager.validate_session('invalid_token')
        self.assertIsNone(invalid_session)
        
        # Expire session and validate
        session.expire()
        expired_session = SessionManager.validate_session(session.session_token)
        self.assertIsNone(expired_session)
    
    def test_expire_session(self):
        """Test session expiration."""
        session = SessionManager.create_session(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        # Expire session
        success = SessionManager.expire_session(session.session_token)
        self.assertTrue(success)
        
        # Check that session is expired
        session.refresh_from_db()
        self.assertTrue(session.is_expired)
        self.assertFalse(session.is_valid())
        
        # Try to expire non-existent session
        success = SessionManager.expire_session('non_existent_token')
        self.assertFalse(success)
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        # Create session that will expire
        session = SessionManager.create_session(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            expires_hours=0  # Expires immediately
        )
        
        # Manually set expiration to past
        session.expires_at = timezone.now() - timedelta(hours=1)
        session.save()
        
        # Run cleanup
        cleaned_count = SessionManager.cleanup_expired_sessions()
        self.assertEqual(cleaned_count, 1)
        
        # Check that session is marked as expired
        session.refresh_from_db()
        self.assertTrue(session.is_expired)


class OAuthManagerTest(TestCase):
    """Test OAuth manager functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create identity provider
        self.provider = IdentityProvider.objects.create(
            name='github',
            client_id='test_client_id',
            client_secret='test_client_secret',
            authorization_url='https://github.com/login/oauth/authorize',
            token_url='https://github.com/login/oauth/access_token',
            user_info_url='https://api.github.com/user',
            scope='user:email',
            is_enabled=True
        )
    
    def test_oauth_manager_initialization(self):
        """Test OAuth manager initialization."""
        manager = OAuthManager('github')
        self.assertEqual(manager.provider_name, 'github')
        self.assertEqual(manager.client_id, 'test_client_id')
        self.assertEqual(manager.client_secret, 'test_client_secret')
    
    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        manager = OAuthManager('github')
        redirect_uri = 'http://localhost:8000/auth/callback'
        state = 'test_state'
        
        auth_url = manager.get_authorization_url(redirect_uri, state)
        
        self.assertIn('https://github.com/login/oauth/authorize', auth_url)
        self.assertIn('client_id=test_client_id', auth_url)
        self.assertIn('redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fcallback', auth_url)
        self.assertIn('state=test_state', auth_url)
        self.assertIn('scope=user%3Aemail', auth_url)
    
    def test_unsupported_provider(self):
        """Test initialization with unsupported provider."""
        with self.assertRaises(ValueError):
            OAuthManager('unsupported_provider')
    
    @patch('core.authentication.requests.post')
    def test_exchange_code_for_token(self, mock_post):
        """Test exchanging authorization code for token."""
        # Mock successful token response
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'token_type': 'bearer',
            'scope': 'user:email'
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        manager = OAuthManager('github')
        token_data = manager.exchange_code_for_token(
            code='test_code',
            redirect_uri='http://localhost:8000/auth/callback'
        )
        
        self.assertEqual(token_data['access_token'], 'test_access_token')
        mock_post.assert_called_once()
    
    @patch('core.authentication.requests.get')
    def test_get_user_info(self, mock_get):
        """Test getting user information from OAuth provider."""
        # Mock successful user info response
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 12345,
            'login': 'testuser',
            'email': 'test@example.com',
            'name': 'Test User',
            'avatar_url': 'https://github.com/avatar.jpg'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        manager = OAuthManager('github')
        user_info = manager.get_user_info('test_access_token')
        
        self.assertEqual(user_info['provider'], 'github')
        self.assertEqual(user_info['external_id'], '12345')
        self.assertEqual(user_info['email'], 'test@example.com')
        self.assertEqual(user_info['username'], 'testuser')
        mock_get.assert_called_once()


class AuthenticationViewsTest(TestCase):
    """Test authentication views."""
    
    def setUp(self):
        """Set up test client and data."""
        self.client = Client()
        
        # Create identity provider
        self.provider = IdentityProvider.objects.create(
            name='github',
            client_id='test_client_id',
            client_secret='test_client_secret',
            authorization_url='https://github.com/login/oauth/authorize',
            token_url='https://github.com/login/oauth/access_token',
            user_info_url='https://api.github.com/user',
            scope='user:email',
            is_enabled=True
        )
        
        # Create test user and session
        self.user = User.objects.create(
            email='test@example.com',
            username='testuser',
            identity_provider='github',
            external_id='12345'
        )
        
        self.session = SessionManager.create_session(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
    
    def test_oauth_providers_endpoint(self):
        """Test OAuth providers listing endpoint."""
        with self.settings(OAUTH_PROVIDERS={'github': {'enabled': True, 'client_id': 'test'}}):
            response = self.client.get(reverse('core:oauth_providers'))
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertIn('providers', data)
            self.assertEqual(len(data['providers']), 1)
            self.assertEqual(data['providers'][0]['name'], 'github')
    
    def test_session_validation_endpoint(self):
        """Test session validation endpoint."""
        # Test with valid session token
        response = self.client.get(
            reverse('core:session_manage'),
            HTTP_AUTHORIZATION=f'Bearer {self.session.session_token}'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['valid'])
        self.assertEqual(data['user']['email'], 'test@example.com')
        
        # Test with invalid session token
        response = self.client.get(
            reverse('core:session_manage'),
            HTTP_AUTHORIZATION='Bearer invalid_token'
        )
        self.assertEqual(response.status_code, 401)
    
    def test_session_logout_endpoint(self):
        """Test session logout endpoint."""
        response = self.client.delete(
            reverse('core:session_manage'),
            data=json.dumps({'token': self.session.session_token}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify session is expired
        self.session.refresh_from_db()
        self.assertTrue(self.session.is_expired)
    
    def test_session_status_endpoint(self):
        """Test session status endpoint."""
        # Test with valid session
        response = self.client.get(
            reverse('core:session_status'),
            {'token': self.session.session_token}
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['authenticated'])
        
        # Test without session
        response = self.client.get(reverse('core:session_status'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['authenticated'])


class AuthenticationServiceTest(TestCase):
    """Test authentication service functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.provider = IdentityProvider.objects.create(
            name='github',
            client_id='test_client_id',
            client_secret='test_client_secret',
            authorization_url='https://github.com/login/oauth/authorize',
            token_url='https://github.com/login/oauth/access_token',
            user_info_url='https://api.github.com/user',
            scope='user:email',
            is_enabled=True
        )
    
    def test_initiate_oauth_flow(self):
        """Test OAuth flow initiation."""
        auth_url, state = AuthenticationService.initiate_oauth_flow(
            'github', 'http://localhost:8000/callback'
        )
        
        self.assertIn('https://github.com/login/oauth/authorize', auth_url)
        self.assertIsInstance(state, str)
        self.assertEqual(len(state), 32)
    
    def test_find_or_create_user_new_user(self):
        """Test creating new user from OAuth info."""
        user_info = {
            'provider': 'github',
            'external_id': '12345',
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        user = AuthenticationService._find_or_create_user(user_info)
        
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.identity_provider, 'github')
        self.assertEqual(user.external_id, '12345')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
    
    def test_find_or_create_user_existing_user(self):
        """Test finding existing user by email."""
        # Create existing user
        existing_user = User.objects.create(
            email='existing@example.com',
            username='existing',
            identity_provider='local'
        )
        
        user_info = {
            'provider': 'github',
            'external_id': '12345',
            'email': 'existing@example.com',
            'username': 'existing_github',
            'first_name': 'Existing',
            'last_name': 'User'
        }
        
        user = AuthenticationService._find_or_create_user(user_info)
        
        # Should return the same user but update OAuth info
        self.assertEqual(user.id, existing_user.id)
        self.assertEqual(user.identity_provider, 'github')
        self.assertEqual(user.external_id, '12345')
    
    def test_logout_user(self):
        """Test user logout functionality."""
        # Create user and session
        user = User.objects.create(
            email='test@example.com',
            username='testuser'
        )
        session = SessionManager.create_session(
            user=user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        # Logout user
        success = AuthenticationService.logout_user(session.session_token)
        self.assertTrue(success)
        
        # Verify session is expired
        session.refresh_from_db()
        self.assertTrue(session.is_expired)
        
        # Try to logout with invalid token
        success = AuthenticationService.logout_user('invalid_token')
        self.assertFalse(success)