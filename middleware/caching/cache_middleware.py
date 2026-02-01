"""
Cache Middleware for FastAPI

Provides automatic caching for HTTP requests and responses with
intelligent cache key generation and invalidation.
"""

import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Set
from urllib.parse import urlencode
import asyncio
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = structlog.get_logger()


class CacheMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic HTTP response caching"""
    
    def __init__(
        self,
        app,
        cache_manager,
        default_ttl: int = 300,  # 5 minutes
        cache_get_requests: bool = True,
        cache_post_requests: bool = False,
        excluded_paths: Optional[List[str]] = None,
        cache_headers: Optional[List[str]] = None,
        vary_headers: Optional[List[str]] = None,
        enable_etag: bool = True,
        enable_last_modified: bool = True
    ):
        super().__init__(app)
        self.cache_manager = cache_manager
        self.default_ttl = default_ttl
        self.cache_get_requests = cache_get_requests
        self.cache_post_requests = cache_post_requests
        self.excluded_paths = excluded_paths or ['/health', '/docs', '/redoc', '/openapi.json']
        self.cache_headers = cache_headers or ['Authorization', 'User-Agent']
        self.vary_headers = vary_headers or ['Accept', 'Accept-Encoding', 'Accept-Language']
        self.enable_etag = enable_etag
        self.enable_last_modified = enable_last_modified
        self.logger = structlog.get_logger()
        
        # Statistics
        self.stats = {
            'requests_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_sets': 0,
            'cache_errors': 0,
            'average_response_time_ms': 0.0
        }
        
        self._response_times = []
        
        self.logger.info(
            "Cache middleware initialized",
            default_ttl=default_ttl,
            cache_get=cache_get_requests,
            cache_post=cache_post_requests,
            excluded_paths=len(self.excluded_paths)
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process request with caching logic"""
        start_time = time.time()
        
        try:
            self.stats['requests_processed'] += 1
            
            # Check if request should be cached
            if not self._should_cache_request(request):
                response = await call_next(request)
                self._update_response_time(start_time)
                return response
            
            # Generate cache key
            cache_key = await self._generate_cache_key(request)
            
            # Try to get cached response
            cached_response = await self._get_cached_response(cache_key, request)
            if cached_response:
                self.stats['cache_hits'] += 1
                self._update_response_time(start_time)
                self.logger.debug("Cache hit", path=request.url.path, cache_key=cache_key)
                return cached_response
            
            # Cache miss - process request
            self.stats['cache_misses'] += 1
            response = await call_next(request)
            
            # Cache response if appropriate
            if self._should_cache_response(request, response):
                await self._cache_response(cache_key, request, response)
                self.stats['cache_sets'] += 1
            
            self._update_response_time(start_time)
            self.logger.debug("Cache miss", path=request.url.path, cache_key=cache_key)
            return response
            
        except Exception as e:
            self.stats['cache_errors'] += 1
            self.logger.error("Cache middleware error", error=str(e), path=request.url.path)
            
            # Fall back to normal processing
            response = await call_next(request)
            self._update_response_time(start_time)
            return response
    
    def _should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached"""
        # Check excluded paths
        for excluded_path in self.excluded_paths:
            if request.url.path.startswith(excluded_path):
                return False
        
        # Check HTTP method
        if request.method == 'GET' and self.cache_get_requests:
            return True
        elif request.method == 'POST' and self.cache_post_requests:
            return True
        
        return False
    
    def _should_cache_response(self, request: Request, response: Response) -> bool:
        """Determine if response should be cached"""
        # Only cache successful responses
        if response.status_code >= 400:
            return False
        
        # Check for cache control headers
        cache_control = response.headers.get('Cache-Control', '')
        if 'no-cache' in cache_control or 'no-store' in cache_control:
            return False
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if content_type.startswith('text/event-stream'):
            return False
        
        return True
    
    async def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        key_components = []
        
        # Add method and path
        key_components.append(f"method:{request.method}")
        key_components.append(f"path:{request.url.path}")
        
        # Add query parameters (sorted for consistency)
        if request.query_params:
            sorted_params = sorted(request.query_params.items())
            query_string = urlencode(sorted_params)
            key_components.append(f"query:{query_string}")
        
        # Add relevant headers
        for header_name in self.cache_headers:
            header_value = request.headers.get(header_name)
            if header_value:
                key_components.append(f"header:{header_name}:{header_value}")
        
        # Add request body for POST requests (if caching is enabled)
        if request.method == 'POST' and self.cache_post_requests:
            try:
                body = await request.body()
                if body:
                    body_hash = hashlib.sha256(body).hexdigest()[:16]
                    key_components.append(f"body:{body_hash}")
            except Exception as e:
                self.logger.warning("Failed to read request body for cache key", error=str(e))
        
        # Create final cache key
        key_string = "|".join(key_components)
        cache_key = f"http_cache:{hashlib.sha256(key_string.encode()).hexdigest()[:16]}"
        
        return cache_key
    
    async def _get_cached_response(self, cache_key: str, request: Request) -> Optional[Response]:
        """Get cached response if available"""
        try:
            cached_data = await self.cache_manager.get(cache_key)
            if not cached_data:
                return None
            
            # Validate cached data structure
            if not isinstance(cached_data, dict) or 'content' not in cached_data:
                return None
            
            # Check conditional headers
            if self._check_conditional_headers(request, cached_data):
                return self._create_not_modified_response()
            
            # Create response from cached data
            response = JSONResponse(
                content=cached_data['content'],
                status_code=cached_data.get('status_code', 200),
                headers=cached_data.get('headers', {})
            )
            
            # Add cache headers
            response.headers['X-Cache'] = 'HIT'
            response.headers['X-Cache-Key'] = cache_key
            
            if self.enable_etag and 'etag' in cached_data:
                response.headers['ETag'] = cached_data['etag']
            
            if self.enable_last_modified and 'last_modified' in cached_data:
                response.headers['Last-Modified'] = cached_data['last_modified']
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get cached response", cache_key=cache_key, error=str(e))
            return None
    
    async def _cache_response(self, cache_key: str, request: Request, response: Response):
        """Cache response data"""
        try:
            # Read response content
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Parse content
            try:
                content = json.loads(response_body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                content = response_body.decode('utf-8', errors='ignore')
            
            # Prepare cache data
            cache_data = {
                'content': content,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'request_method': request.method,
                'request_path': request.url.path
            }
            
            # Add ETag if enabled
            if self.enable_etag:
                etag = self._generate_etag(response_body)
                cache_data['etag'] = etag
                response.headers['ETag'] = etag
            
            # Add Last-Modified if enabled
            if self.enable_last_modified:
                last_modified = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
                cache_data['last_modified'] = last_modified
                response.headers['Last-Modified'] = last_modified
            
            # Determine TTL
            ttl = self._get_response_ttl(response)
            
            # Cache the response
            await self.cache_manager.set(cache_key, cache_data, ttl)
            
            # Add cache headers to response
            response.headers['X-Cache'] = 'MISS'
            response.headers['X-Cache-Key'] = cache_key
            response.headers['Cache-Control'] = f'max-age={ttl}'
            
            # Recreate response with cached content
            new_response = JSONResponse(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
            # Copy response attributes
            for attr in ['status_code', 'headers', 'media_type', 'background']:
                if hasattr(response, attr):
                    setattr(new_response, attr, getattr(response, attr))
            
            return new_response
            
        except Exception as e:
            self.logger.error("Failed to cache response", cache_key=cache_key, error=str(e))
    
    def _check_conditional_headers(self, request: Request, cached_data: Dict[str, Any]) -> bool:
        """Check conditional headers for 304 Not Modified response"""
        # Check If-None-Match (ETag)
        if_none_match = request.headers.get('If-None-Match')
        if if_none_match and 'etag' in cached_data:
            if if_none_match == cached_data['etag'] or if_none_match == '*':
                return True
        
        # Check If-Modified-Since
        if_modified_since = request.headers.get('If-Modified-Since')
        if if_modified_since and 'last_modified' in cached_data:
            try:
                from email.utils import parsedate_to_datetime
                request_time = parsedate_to_datetime(if_modified_since)
                cached_time = parsedate_to_datetime(cached_data['last_modified'])
                
                if cached_time <= request_time:
                    return True
            except Exception:
                pass  # Ignore parsing errors
        
        return False
    
    def _create_not_modified_response(self) -> Response:
        """Create 304 Not Modified response"""
        response = Response(status_code=304)
        response.headers['X-Cache'] = 'HIT-304'
        return response
    
    def _generate_etag(self, content: bytes) -> str:
        """Generate ETag for response content"""
        return f'"{hashlib.sha256(content).hexdigest()[:16]}"'
    
    def _get_response_ttl(self, response: Response) -> int:
        """Get TTL for response caching"""
        # Check Cache-Control header
        cache_control = response.headers.get('Cache-Control', '')
        
        # Parse max-age directive
        import re
        max_age_match = re.search(r'max-age=(\d+)', cache_control)
        if max_age_match:
            return int(max_age_match.group(1))
        
        # Check Expires header
        expires = response.headers.get('Expires')
        if expires:
            try:
                from email.utils import parsedate_to_datetime
                expires_time = parsedate_to_datetime(expires)
                now = datetime.now(timezone.utc)
                ttl = int((expires_time - now).total_seconds())
                return max(0, ttl)
            except Exception:
                pass
        
        # Use default TTL
        return self.default_ttl
    
    def _update_response_time(self, start_time: float):
        """Update average response time statistics"""
        response_time = (time.time() - start_time) * 1000
        self._response_times.append(response_time)
        
        # Keep only recent response times (last 1000)
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-1000:]
        
        # Update average
        self.stats['average_response_time_ms'] = sum(self._response_times) / len(self._response_times)
    
    async def invalidate_cache_for_path(self, path_pattern: str) -> int:
        """
        Invalidate cached responses for path pattern
        
        Args:
            path_pattern: Path pattern to match
            
        Returns:
            Number of cache entries invalidated
        """
        try:
            # Create pattern for cache keys
            cache_pattern = f"http_cache:*path:{path_pattern}*"
            
            # Invalidate matching cache entries
            invalidated_count = await self.cache_manager.invalidate(cache_pattern)
            
            self.logger.info(
                "Cache invalidated for path pattern",
                path_pattern=path_pattern,
                invalidated_count=invalidated_count
            )
            
            return invalidated_count
            
        except Exception as e:
            self.logger.error("Failed to invalidate cache for path", path_pattern=path_pattern, error=str(e))
            return 0
    
    async def invalidate_cache_for_user(self, user_id: str) -> int:
        """
        Invalidate cached responses for specific user
        
        Args:
            user_id: User ID to invalidate cache for
            
        Returns:
            Number of cache entries invalidated
        """
        try:
            # Create pattern for user-specific cache keys
            cache_pattern = f"http_cache:*header:Authorization:*{user_id}*"
            
            # Invalidate matching cache entries
            invalidated_count = await self.cache_manager.invalidate(cache_pattern)
            
            self.logger.info(
                "Cache invalidated for user",
                user_id=user_id,
                invalidated_count=invalidated_count
            )
            
            return invalidated_count
            
        except Exception as e:
            self.logger.error("Failed to invalidate cache for user", user_id=user_id, error=str(e))
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache middleware statistics"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = self.stats['cache_hits'] / total_requests if total_requests > 0 else 0.0
        
        return {
            'middleware_stats': self.stats.copy(),
            'hit_rate': hit_rate,
            'configuration': {
                'default_ttl': self.default_ttl,
                'cache_get_requests': self.cache_get_requests,
                'cache_post_requests': self.cache_post_requests,
                'excluded_paths': self.excluded_paths,
                'enable_etag': self.enable_etag,
                'enable_last_modified': self.enable_last_modified
            }
        }
    
    def reset_stats(self):
        """Reset middleware statistics"""
        self.stats = {
            'requests_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_sets': 0,
            'cache_errors': 0,
            'average_response_time_ms': 0.0
        }
        self._response_times = []
        
        self.logger.info("Cache middleware statistics reset")