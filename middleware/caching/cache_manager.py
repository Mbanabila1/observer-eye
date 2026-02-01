"""
Cache Manager

Central cache management system with support for multiple backends,
performance monitoring, and intelligent caching strategies.
"""

import json
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import structlog

logger = structlog.get_logger()


class CacheBackend(Enum):
    """Available cache backends"""
    MEMORY = "memory"
    REDIS = "redis"
    HYBRID = "hybrid"  # Memory + Redis


class EvictionPolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out


@dataclass
class CacheConfig:
    """Configuration for cache manager"""
    backend: CacheBackend = CacheBackend.REDIS
    default_ttl: int = 3600  # 1 hour
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    enable_compression: bool = True
    enable_encryption: bool = False
    redis_url: str = "redis://localhost:6379/0"
    key_prefix: str = "observer_eye:"
    enable_metrics: bool = True
    batch_size: int = 100


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    memory_usage_bytes: int = 0
    total_keys: int = 0
    hit_rate: float = 0.0
    average_get_time_ms: float = 0.0
    average_set_time_ms: float = 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    ttl: int
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    compressed: bool = False
    encrypted: bool = False


class CacheManager:
    """Comprehensive cache manager with multiple backend support"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.logger = structlog.get_logger()
        self.stats = CacheStats()
        self.backends = {}
        self._lock = asyncio.Lock()
        
        # Initialize backends
        self._initialize_backends()
        
        # Performance tracking
        self._operation_times = []
        self._last_cleanup = datetime.now(timezone.utc)
        
        self.logger.info(
            "Cache manager initialized",
            backend=self.config.backend.value,
            default_ttl=self.config.default_ttl,
            max_memory_size=self.config.max_memory_size
        )
    
    def _initialize_backends(self):
        """Initialize cache backends based on configuration"""
        if self.config.backend == CacheBackend.MEMORY:
            from .memory_cache import MemoryCache
            self.backends['primary'] = MemoryCache(self.config)
            
        elif self.config.backend == CacheBackend.REDIS:
            from .redis_cache import RedisCache
            self.backends['primary'] = RedisCache(self.config)
            
        elif self.config.backend == CacheBackend.HYBRID:
            from .memory_cache import MemoryCache
            from .redis_cache import RedisCache
            self.backends['memory'] = MemoryCache(self.config)
            self.backends['redis'] = RedisCache(self.config)
            self.backends['primary'] = self.backends['memory']  # Memory is primary for hybrid
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        start_time = time.time()
        
        try:
            # Normalize key
            normalized_key = self._normalize_key(key)
            
            # Try primary backend first
            value = await self._get_from_backend('primary', normalized_key)
            
            if value is not None:
                # Cache hit
                self.stats.hits += 1
                
                # For hybrid mode, promote to memory cache if found in Redis
                if (self.config.backend == CacheBackend.HYBRID and 
                    'memory' in self.backends and 
                    not await self._exists_in_backend('memory', normalized_key)):
                    await self._set_to_backend('memory', normalized_key, value, self.config.default_ttl)
                
                self.logger.debug("Cache hit", key=key, backend="primary")
                return value
            
            # For hybrid mode, try Redis if not in memory
            if (self.config.backend == CacheBackend.HYBRID and 
                'redis' in self.backends):
                value = await self._get_from_backend('redis', normalized_key)
                if value is not None:
                    self.stats.hits += 1
                    # Promote to memory cache
                    await self._set_to_backend('memory', normalized_key, value, self.config.default_ttl)
                    self.logger.debug("Cache hit", key=key, backend="redis")
                    return value
            
            # Cache miss
            self.stats.misses += 1
            self.logger.debug("Cache miss", key=key)
            return default
            
        except Exception as e:
            self.logger.error("Cache get failed", key=key, error=str(e))
            self.stats.misses += 1
            return default
            
        finally:
            # Track performance
            operation_time = (time.time() - start_time) * 1000
            self._update_get_time(operation_time)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            # Normalize key and determine TTL
            normalized_key = self._normalize_key(key)
            cache_ttl = ttl or self.config.default_ttl
            
            # Set in primary backend
            success = await self._set_to_backend('primary', normalized_key, value, cache_ttl)
            
            if success:
                self.stats.sets += 1
                
                # For hybrid mode, also set in Redis for persistence
                if (self.config.backend == CacheBackend.HYBRID and 
                    'redis' in self.backends):
                    await self._set_to_backend('redis', normalized_key, value, cache_ttl)
                
                self.logger.debug("Cache set", key=key, ttl=cache_ttl)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("Cache set failed", key=key, error=str(e))
            return False
            
        finally:
            # Track performance
            operation_time = (time.time() - start_time) * 1000
            self._update_set_time(operation_time)
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        try:
            normalized_key = self._normalize_key(key)
            
            # Delete from all backends
            success = False
            for backend_name, backend in self.backends.items():
                if await self._delete_from_backend(backend_name, normalized_key):
                    success = True
            
            if success:
                self.stats.deletes += 1
                self.logger.debug("Cache delete", key=key)
            
            return success
            
        except Exception as e:
            self.logger.error("Cache delete failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            normalized_key = self._normalize_key(key)
            
            # Check primary backend first
            if await self._exists_in_backend('primary', normalized_key):
                return True
            
            # For hybrid mode, check Redis
            if (self.config.backend == CacheBackend.HYBRID and 
                'redis' in self.backends):
                return await self._exists_in_backend('redis', normalized_key)
            
            return False
            
        except Exception as e:
            self.logger.error("Cache exists check failed", key=key, error=str(e))
            return False
    
    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Pattern to match keys (supports wildcards)
            
        Returns:
            Number of keys invalidated
        """
        try:
            total_invalidated = 0
            
            for backend_name, backend in self.backends.items():
                count = await self._invalidate_in_backend(backend_name, pattern)
                total_invalidated += count
            
            self.logger.info("Cache invalidation", pattern=pattern, count=total_invalidated)
            return total_invalidated
            
        except Exception as e:
            self.logger.error("Cache invalidation failed", pattern=pattern, error=str(e))
            return 0
    
    async def clear(self) -> bool:
        """
        Clear all cache entries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            success = True
            
            for backend_name, backend in self.backends.items():
                if not await self._clear_backend(backend_name):
                    success = False
            
            if success:
                # Reset stats
                self.stats = CacheStats()
                self.logger.info("Cache cleared")
            
            return success
            
        except Exception as e:
            self.logger.error("Cache clear failed", error=str(e))
            return False
    
    async def get_stats(self) -> CacheStats:
        """
        Get cache performance statistics
        
        Returns:
            CacheStats object with current statistics
        """
        try:
            # Update hit rate
            total_requests = self.stats.hits + self.stats.misses
            if total_requests > 0:
                self.stats.hit_rate = self.stats.hits / total_requests
            
            # Get memory usage and key count from backends
            total_memory = 0
            total_keys = 0
            
            for backend_name, backend in self.backends.items():
                backend_stats = await self._get_backend_stats(backend_name)
                total_memory += backend_stats.get('memory_usage_bytes', 0)
                total_keys += backend_stats.get('total_keys', 0)
            
            self.stats.memory_usage_bytes = total_memory
            self.stats.total_keys = total_keys
            
            return self.stats
            
        except Exception as e:
            self.logger.error("Failed to get cache stats", error=str(e))
            return self.stats
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache in batch
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to values
        """
        results = {}
        
        try:
            # Process in chunks
            chunk_size = self.config.batch_size
            
            for i in range(0, len(keys), chunk_size):
                chunk = keys[i:i + chunk_size]
                
                # Get values for this chunk
                chunk_results = await asyncio.gather(
                    *[self.get(key) for key in chunk],
                    return_exceptions=True
                )
                
                # Process results
                for key, result in zip(chunk, chunk_results):
                    if not isinstance(result, Exception) and result is not None:
                        results[key] = result
            
            self.logger.debug("Batch get completed", requested=len(keys), found=len(results))
            return results
            
        except Exception as e:
            self.logger.error("Batch get failed", error=str(e))
            return {}
    
    async def batch_set(self, items: Dict[str, Any], ttl: Optional[int] = None) -> int:
        """
        Set multiple values in cache in batch
        
        Args:
            items: Dictionary mapping keys to values
            ttl: Time to live in seconds
            
        Returns:
            Number of items successfully set
        """
        success_count = 0
        
        try:
            # Process in chunks
            items_list = list(items.items())
            chunk_size = self.config.batch_size
            
            for i in range(0, len(items_list), chunk_size):
                chunk = items_list[i:i + chunk_size]
                
                # Set values for this chunk
                results = await asyncio.gather(
                    *[self.set(key, value, ttl) for key, value in chunk],
                    return_exceptions=True
                )
                
                # Count successes
                success_count += sum(1 for result in results if result is True)
            
            self.logger.debug("Batch set completed", requested=len(items), successful=success_count)
            return success_count
            
        except Exception as e:
            self.logger.error("Batch set failed", error=str(e))
            return 0
    
    async def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries
        
        Returns:
            Number of entries cleaned up
        """
        try:
            total_cleaned = 0
            
            for backend_name, backend in self.backends.items():
                count = await self._cleanup_backend(backend_name)
                total_cleaned += count
            
            self.stats.evictions += total_cleaned
            self._last_cleanup = datetime.now(timezone.utc)
            
            if total_cleaned > 0:
                self.logger.info("Cache cleanup completed", cleaned=total_cleaned)
            
            return total_cleaned
            
        except Exception as e:
            self.logger.error("Cache cleanup failed", error=str(e))
            return 0
    
    def _normalize_key(self, key: str) -> str:
        """Normalize cache key with prefix"""
        return f"{self.config.key_prefix}{key}"
    
    def _generate_key_hash(self, data: Any) -> str:
        """Generate cache key from data"""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True, default=str)
        
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _update_get_time(self, operation_time_ms: float):
        """Update average get time"""
        self._operation_times.append(('get', operation_time_ms))
        
        # Keep only recent operations (last 1000)
        if len(self._operation_times) > 1000:
            self._operation_times = self._operation_times[-1000:]
        
        # Calculate average get time
        get_times = [time for op, time in self._operation_times if op == 'get']
        if get_times:
            self.stats.average_get_time_ms = sum(get_times) / len(get_times)
    
    def _update_set_time(self, operation_time_ms: float):
        """Update average set time"""
        self._operation_times.append(('set', operation_time_ms))
        
        # Keep only recent operations (last 1000)
        if len(self._operation_times) > 1000:
            self._operation_times = self._operation_times[-1000:]
        
        # Calculate average set time
        set_times = [time for op, time in self._operation_times if op == 'set']
        if set_times:
            self.stats.average_set_time_ms = sum(set_times) / len(set_times)
    
    # Backend interface methods
    async def _get_from_backend(self, backend_name: str, key: str) -> Any:
        """Get value from specific backend"""
        backend = self.backends.get(backend_name)
        if backend:
            return await backend.get(key)
        return None
    
    async def _set_to_backend(self, backend_name: str, key: str, value: Any, ttl: int) -> bool:
        """Set value to specific backend"""
        backend = self.backends.get(backend_name)
        if backend:
            return await backend.set(key, value, ttl)
        return False
    
    async def _delete_from_backend(self, backend_name: str, key: str) -> bool:
        """Delete key from specific backend"""
        backend = self.backends.get(backend_name)
        if backend:
            return await backend.delete(key)
        return False
    
    async def _exists_in_backend(self, backend_name: str, key: str) -> bool:
        """Check if key exists in specific backend"""
        backend = self.backends.get(backend_name)
        if backend:
            return await backend.exists(key)
        return False
    
    async def _invalidate_in_backend(self, backend_name: str, pattern: str) -> int:
        """Invalidate keys in specific backend"""
        backend = self.backends.get(backend_name)
        if backend:
            return await backend.invalidate(pattern)
        return 0
    
    async def _clear_backend(self, backend_name: str) -> bool:
        """Clear specific backend"""
        backend = self.backends.get(backend_name)
        if backend:
            return await backend.clear()
        return False
    
    async def _cleanup_backend(self, backend_name: str) -> int:
        """Cleanup expired entries in specific backend"""
        backend = self.backends.get(backend_name)
        if backend and hasattr(backend, 'cleanup_expired'):
            return await backend.cleanup_expired()
        return 0
    
    async def _get_backend_stats(self, backend_name: str) -> Dict[str, Any]:
        """Get statistics from specific backend"""
        backend = self.backends.get(backend_name)
        if backend and hasattr(backend, 'get_stats'):
            return await backend.get_stats()
        return {}
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Cleanup resources
        for backend in self.backends.values():
            if hasattr(backend, 'close'):
                await backend.close()
    
    # Decorator for caching function results
    def cached(self, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
        """
        Decorator for caching function results
        
        Args:
            ttl: Time to live in seconds
            key_func: Function to generate cache key from arguments
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{self._generate_key_hash((args, kwargs))}"
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator