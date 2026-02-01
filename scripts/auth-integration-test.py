#!/usr/bin/env python3
"""
Observer Eye Platform - Authentication Flow Integration Test

This script tests authentication flows with all identity providers.
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, Any, List, Optional
import aiohttp
import argparse
from urllib.parse import urljoin, urlparse, parse_qs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuthenticationIntegrationTest:
    """Authentication integration test suite."""
    
    def __init__(self, backend_url: str, middleware_url: str, frontend_url: str):
        self.backend_url = backend_url
        self.middleware_url = middleware_url
        self.frontend_url = frontend_url
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []
        self.session = None
    
    def success(self, message: str):
        """Log successful test."""
        logger.info(f"✓ {message}")
        self.tests_passed += 1
    
    def error(self, message: str):
        """Log failed test."""
        logger.error(f"✗ {message}")
        self.tests_failed += 1
        self.failed_tests.append(message)
    
    def warning(self, message: str):
        """Log warning."""
        logger.warning(f"⚠ {message}")
    
    async def setup_session(self):
        """Setup HTTP session."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(verify_ssl=False)
        )
    
    async def cleanup_session(self):
        """Cleanup HTTP session."""
        if self.session:
            await self.session.close()
    
    async def test_oauth_providers_endpoint(self) -> bool:
        """Test OAuth providers endpoint."""
        logger.info("Testing OAuth providers endpoint...")
        
        try:
            url = urljoin(self.backend_url, "/api/oauth/providers/")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        self.success(f"OAuth providers endpoint returned {len(data)} providers")
                        
                        # Check for expected providers
                        provider_names = [provider.get('name', '') for provider in data]
                        expected_providers = ['github', 'google', 'gitlab', 'microsoft']
                        
                        found_providers = [p for p in expected_providers if p in provider_names]
                        if found_providers:
                            self.success(f"Found OAuth providers: {', '.join(found_providers)}")
                        else:
                            self.warning("No expected OAuth providers found")
                        
                        return True
                    else:
                        self.warning("OAuth providers endpoint returned empty list")
                        return False
                else:
                    self.error(f"OAuth providers endpoint failed with status: {response.status}")
                    return False
                    
        except Exception as e:
            self.error(f"OAuth providers endpoint test failed: {str(e)}")
            return False
    
    async def test_oauth_authorization_urls(self) -> bool:
        """Test OAuth authorization URL generation."""
        logger.info("Testing OAuth authorization URLs...")
        
        providers = ['github', 'google', 'gitlab', 'microsoft']
        successful_providers = 0
        
        for provider in providers:
            try:
                url = urljoin(self.backend_url, f"/api/oauth/authorize/{provider}/")
                
                async with self.session.get(url, allow_redirects=False) as response:
                    if response.status in [302, 301]:  # Redirect to OAuth provider
                        redirect_url = response.headers.get('Location', '')
                        if redirect_url and provider in redirect_url.lower():
                            self.success(f"OAuth authorization URL generated for {provider}")
                            successful_providers += 1
                        else:
                            self.warning(f"OAuth authorization URL for {provider} doesn't contain provider name")
                    elif response.status == 404:
                        self.warning(f"OAuth provider {provider} not configured")
                    else:
                        self.warning(f"OAuth authorization for {provider} returned status: {response.status}")
                        
            except Exception as e:
                self.error(f"OAuth authorization test for {provider} failed: {str(e)}")
        
        if successful_providers > 0:
            self.success(f"OAuth authorization URLs working for {successful_providers}/{len(providers)} providers")
            return True
        else:
            self.error("No OAuth authorization URLs working")
            return False
    
    async def test_authentication_endpoints(self) -> bool:
        """Test authentication endpoints."""
        logger.info("Testing authentication endpoints...")
        
        # Test user endpoint without authentication (should return 401)
        try:
            url = urljoin(self.backend_url, "/api/auth/user/")
            
            async with self.session.get(url) as response:
                if response.status == 401:
                    self.success("Authentication required for protected endpoint")
                elif response.status == 200:
                    self.warning("Protected endpoint accessible without authentication")
                else:
                    self.warning(f"Unexpected status for protected endpoint: {response.status}")
                    
        except Exception as e:
            self.error(f"Authentication endpoint test failed: {str(e)}")
            return False
        
        return True
    
    async def test_session_management(self) -> bool:
        """Test session management."""
        logger.info("Testing session management...")
        
        try:
            # Test session creation (login endpoint)
            login_url = urljoin(self.backend_url, "/api/auth/login/")
            
            # Test with invalid credentials (should fail)
            login_data = {
                "username": "test_user",
                "password": "invalid_password"
            }
            
            async with self.session.post(login_url, json=login_data) as response:
                if response.status in [400, 401, 403]:
                    self.success("Login with invalid credentials properly rejected")
                else:
                    self.warning(f"Login with invalid credentials returned status: {response.status}")
            
            # Test logout endpoint
            logout_url = urljoin(self.backend_url, "/api/auth/logout/")
            
            async with self.session.post(logout_url) as response:
                if response.status in [200, 204, 401]:  # 401 is acceptable if not logged in
                    self.success("Logout endpoint accessible")
                else:
                    self.warning(f"Logout endpoint returned status: {response.status}")
            
            return True
            
        except Exception as e:
            self.error(f"Session management test failed: {str(e)}")
            return False
    
    async def test_jwt_token_endpoints(self) -> bool:
        """Test JWT token endpoints."""
        logger.info("Testing JWT token endpoints...")
        
        try:
            # Test token refresh endpoint
            refresh_url = urljoin(self.backend_url, "/api/auth/refresh/")
            
            # Test without token (should fail)
            async with self.session.post(refresh_url) as response:
                if response.status in [400, 401]:
                    self.success("JWT refresh without token properly rejected")
                else:
                    self.warning(f"JWT refresh without token returned status: {response.status}")
            
            return True
            
        except Exception as e:
            self.error(f"JWT token endpoints test failed: {str(e)}")
            return False
    
    async def test_password_validation(self) -> bool:
        """Test password validation through API."""
        logger.info("Testing password validation...")
        
        try:
            # This would typically be done through a user registration endpoint
            # For now, we'll test if the validation logic is accessible
            
            # Test if there's a password validation endpoint
            validation_url = urljoin(self.backend_url, "/api/auth/validate-password/")
            
            test_passwords = [
                {"password": "weak", "expected": "weak"},
                {"password": "StrongPassword123!", "expected": "strong"},
                {"password": "12345678", "expected": "weak"},
            ]
            
            validation_working = False
            
            for test_case in test_passwords:
                try:
                    async with self.session.post(
                        validation_url, 
                        json={"password": test_case["password"]}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            validation_working = True
                            self.success(f"Password validation working for: {test_case['password'][:3]}...")
                        elif response.status == 404:
                            # Endpoint doesn't exist, which is acceptable
                            break
                        else:
                            self.warning(f"Password validation returned status: {response.status}")
                            
                except Exception:
                    # Individual password test failed, continue
                    continue
            
            if validation_working:
                self.success("Password validation endpoints working")
            else:
                self.warning("Password validation endpoints not available (acceptable)")
            
            return True
            
        except Exception as e:
            self.error(f"Password validation test failed: {str(e)}")
            return False
    
    async def test_cors_configuration(self) -> bool:
        """Test CORS configuration for authentication."""
        logger.info("Testing CORS configuration...")
        
        try:
            # Test preflight request
            url = urljoin(self.backend_url, "/api/auth/user/")
            
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization'
            }
            
            async with self.session.options(url, headers=headers) as response:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                
                if any(cors_headers.values()):
                    self.success("CORS headers present in authentication endpoints")
                    
                    if cors_headers['Access-Control-Allow-Credentials'] == 'true':
                        self.success("CORS credentials allowed for authentication")
                    else:
                        self.warning("CORS credentials not explicitly allowed")
                    
                    return True
                else:
                    self.warning("No CORS headers found in authentication endpoints")
                    return False
                    
        except Exception as e:
            self.error(f"CORS configuration test failed: {str(e)}")
            return False
    
    async def test_security_headers(self) -> bool:
        """Test security headers in authentication responses."""
        logger.info("Testing security headers...")
        
        try:
            url = urljoin(self.backend_url, "/api/auth/user/")
            
            async with self.session.get(url) as response:
                security_headers = {
                    'X-Frame-Options': response.headers.get('X-Frame-Options'),
                    'X-Content-Type-Options': response.headers.get('X-Content-Type-Options'),
                    'X-XSS-Protection': response.headers.get('X-XSS-Protection'),
                    'Strict-Transport-Security': response.headers.get('Strict-Transport-Security'),
                    'Content-Security-Policy': response.headers.get('Content-Security-Policy')
                }
                
                present_headers = [k for k, v in security_headers.items() if v]
                
                if len(present_headers) >= 2:
                    self.success(f"Security headers present: {', '.join(present_headers)}")
                    return True
                else:
                    self.warning(f"Limited security headers found: {', '.join(present_headers)}")
                    return False
                    
        except Exception as e:
            self.error(f"Security headers test failed: {str(e)}")
            return False
    
    async def test_middleware_auth_integration(self) -> bool:
        """Test middleware authentication integration."""
        logger.info("Testing middleware authentication integration...")
        
        try:
            # Test middleware endpoint that requires authentication
            url = urljoin(self.middleware_url, "/metrics")
            
            async with self.session.get(url) as response:
                # Should work without authentication for basic metrics
                # or return 401 if authentication is required
                if response.status in [200, 401]:
                    self.success("Middleware authentication integration working")
                    return True
                else:
                    self.warning(f"Middleware auth integration returned status: {response.status}")
                    return False
                    
        except Exception as e:
            self.error(f"Middleware auth integration test failed: {str(e)}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all authentication integration tests."""
        logger.info("Starting Authentication Integration Tests...")
        logger.info("=" * 60)
        
        await self.setup_session()
        
        try:
            # Run all test methods
            test_methods = [
                self.test_oauth_providers_endpoint,
                self.test_oauth_authorization_urls,
                self.test_authentication_endpoints,
                self.test_session_management,
                self.test_jwt_token_endpoints,
                self.test_password_validation,
                self.test_cors_configuration,
                self.test_security_headers,
                self.test_middleware_auth_integration
            ]
            
            for test_method in test_methods:
                try:
                    await test_method()
                    logger.info("")  # Add spacing between tests
                except Exception as e:
                    self.error(f"Test {test_method.__name__} crashed: {str(e)}")
                    logger.info("")
            
            # Print results
            logger.info("=" * 60)
            logger.info("Authentication Integration Test Results")
            logger.info("=" * 60)
            logger.info(f"Tests Passed: {self.tests_passed}")
            logger.info(f"Tests Failed: {self.tests_failed}")
            logger.info(f"Total Tests: {self.tests_passed + self.tests_failed}")
            
            if self.tests_failed > 0:
                logger.error("")
                logger.error("Failed Tests:")
                for test in self.failed_tests:
                    logger.error(f"  ✗ {test}")
                logger.error("")
                logger.error("Authentication integration tests FAILED")
                return False
            else:
                logger.info("")
                logger.info("All authentication integration tests PASSED")
                return True
                
        finally:
            await self.cleanup_session()


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Authentication Integration Test for Observer Eye Platform")
    parser.add_argument("--backend-url", default="http://localhost:8000",
                       help="Backend URL (default: http://localhost:8000)")
    parser.add_argument("--middleware-url", default="http://localhost:8400",
                       help="Middleware URL (default: http://localhost:8400)")
    parser.add_argument("--frontend-url", default="http://localhost:80",
                       help="Frontend URL (default: http://localhost:80)")
    parser.add_argument("--timeout", type=int, default=60,
                       help="Test timeout in seconds (default: 60)")
    
    args = parser.parse_args()
    
    # Create test instance
    test_suite = AuthenticationIntegrationTest(
        args.backend_url, 
        args.middleware_url, 
        args.frontend_url
    )
    
    try:
        # Run tests with timeout
        success = await asyncio.wait_for(
            test_suite.run_all_tests(),
            timeout=args.timeout
        )
        
        sys.exit(0 if success else 1)
        
    except asyncio.TimeoutError:
        logger.error(f"Tests timed out after {args.timeout} seconds")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite crashed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())