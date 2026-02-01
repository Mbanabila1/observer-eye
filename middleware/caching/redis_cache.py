"""
Redis Cache Backend

Redis-based distributed caching implementation with advanced features
including compression, serialization, and connection pooling.
"""

import json
import pickle
import gzip
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import asyncio
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


class RedisCache:
    """Redis-based cache backend with advanced features"""
    
    def __init__(self, config):
        self.config = config
        self.logger = structlog.get_logger()
        self.redis_pool = None
        self.connection_retries = 3
        self.connection_timeout = 5
        self._initialized = False
        
        # Don't initialize connection during __init__ - do it lazily
    
    async def _initialize_connection(self):
        """Initialize Redis connection pool"""
        try:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.config.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=self.connection_timeout,
                socket_connect_timeout=self.connection_timeout
            )
            
            # Test connection
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            await redis_client.ping()
            await redis_client.aclose()
            
            self.logger.info(
                "Redis cache initialized",
                url=self.config.redis_url,
                max_connections=20
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize Redis connection",
                error=str(e),
                url=self.config.redis_url
            )
            raise
    
    async def _ensure_initialized(self):
        """Ensure Redis connection is initialized"""
        if not self._initialized:
            await self._initialize_connection()
            self._initialized = True
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from Redis cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            await self._ensure_initialized()
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Get raw data from Redis
            raw_data = await redis_client.get(key)
            
            if raw_data is None:
                return default
            
            # Deserialize data
            value = self._deserialize(raw_data)
            
            # Update access time for LRU tracking
            if self.config.eviction_policy.value == 'lru':
                await redis_client.zadd(f"{key}:access", {key: time.time()})
            
            await redis_client.aclose()
            return value
            
        except Exception as e:
            self.logger.error("Redis get failed", key=key, error=str(e))
            return default
    
    async def set(self, key: str, value: Any, ttl: int) -> bool:
        """
        Set value in Redis cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self._ensure_initialized()
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Serialize data
            serialized_data = self._serialize(value)
            
            # Set with TTL
            success = await redis_client.setex(key, ttl, serialized_data)
            
            # Track access for eviction policies
            current_time = time.time()
            
            if self.config.eviction_policy.value == 'lru':
                await redis_client.zadd(f"{key}:access", {key: current_time})
            elif self.config.eviction_policy.value == 'lfu':
                await redis_client.zincrby(f"{key}:frequency", 1, key)
            
            # Store metadata
            metadata = {
                'created_at': current_time,
                'size_bytes': len(serialized_data),
                'compressed': self.config.enable_compression,
                'ttl': ttl
            }
            await redis_client.hset(f"{key}:meta", mapping=metadata)
            await redis_client.expire(f"{key}:meta", ttl)
            
            await redis_client.aclose()
            return bool(success)
            
        except Exception as e:
            self.logger.error("Redis set failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Delete main key and metadata
            deleted_count = await redis_client.delete(
                key,
                f"{key}:meta",
                f"{key}:access",
                f"{key}:frequency"
            )
            
            await redis_client.aclose()
            return deleted_count > 0
            
        except Exception as e:
            self.logger.error("Redis delete failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            exists = await redis_client.exists(key)
            await redis_client.aclose()
            return bool(exists)
            
        except Exception as e:
            self.logger.error("Redis exists check failed", key=key, error=str(e))
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
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Find matching keys
            keys = await redis_client.keys(pattern)
            
            if not keys:
                await redis_client.aclose()
                return 0
            
            # Delete keys in batches
            batch_size = 100
            total_deleted = 0
            
            for i in range(0, len(keys), batch_size):
                batch = keys[i:i + batch_size]
                
                # Include metadata keys
                all_keys = []
                for key in batch:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    all_keys.extend([
                        key_str,
                        f"{key_str}:meta",
                        f"{key_str}:access",
                        f"{key_str}:frequency"
                    ])
                
                deleted = await redis_client.delete(*all_keys)
                total_deleted += deleted
            
            await redis_client.aclose()
            return total_deleted
            
        except Exception as e:
            self.logger.error("Redis invalidation failed", pattern=pattern, error=str(e))
            return 0
    
    async def clear(self) -> bool:
        """
        Clear all cache entries with the configured prefix
        
        Returns:
            True if successful, False otherwise
        """
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Find all keys with prefix
            pattern = f"{self.config.key_prefix}*"
            keys = await redis_client.keys(pattern)
            
            if keys:
                # Delete in batches
                batch_size = 100
                for i in range(0, len(keys), batch_size):
                    batch = keys[i:i + batch_size]
                    await redis_client.delete(*batch)
            
            await redis_client.aclose()
            return True
            
        except Exception as e:
            self.logger.error("Redis clear failed", error=str(e))
            return False
    
    async def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries
        
        Returns:
            Number of entries cleaned up
        """
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Redis automatically handles TTL expiration
            # But we can clean up orphaned metadata
            
            pattern = f"{self.config.key_prefix}*:meta"
            meta_keys = await redis_client.keys(pattern)
            
            cleaned_count = 0
            
            for meta_key in meta_keys:
                meta_key_str = meta_key.decode() if isinstance(meta_key, bytes) else meta_key
                main_key = meta_key_str.replace(':meta', '')
                
                # Check if main key exists
                if not await redis_client.exists(main_key):
                    # Clean up orphaned metadata
                    await redis_client.delete(
                        meta_key_str,
                        f"{main_key}:access",
                        f"{main_key}:frequency"
                    )
                    cleaned_count += 1
            
            await redis_client.aclose()
            return cleaned_count
            
        except Exception as e:
            self.logger.error("Redis cleanup failed", error=str(e))
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get Redis cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Get Redis info
            info = await redis_client.info()
            
            # Count keys with prefix
            pattern = f"{self.config.key_prefix}*"
            keys = await redis_client.keys(pattern)
            
            # Calculate total memory usage for our keys
            total_memory = 0
            for key in keys[:100]:  # Sample first 100 keys to avoid performance issues
                try:
                    memory = await redis_client.memory_usage(key)
                    if memory:
                        total_memory += memory
                except:
                    pass  # Key might have expired
            
            # Estimate total memory based on sample
            if len(keys) > 100:
                total_memory = int(total_memory * (len(keys) / 100))
            
            await redis_client.aclose()
            
            return {
                'total_keys': len(keys),
                'memory_usage_bytes': total_memory,
                'redis_memory_usage': info.get('used_memory', 0),
                'redis_connected_clients': info.get('connected_clients', 0),
                'redis_total_commands_processed': info.get('total_commands_processed', 0),
                'redis_keyspace_hits': info.get('keyspace_hits', 0),
                'redis_keyspace_misses': info.get('keyspace_misses', 0)
            }
            
        except Exception as e:
            self.logger.error("Failed to get Redis stats", error=str(e))
            return {
                'total_keys': 0,
                'memory_usage_bytes': 0,
                'error': str(e)
            }
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from Redis in batch
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to values
        """
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Use pipeline for batch operations
            pipe = redis_client.pipeline()
            
            for key in keys:
                pipe.get(key)
            
            results = await pipe.execute()
            
            # Process results
            batch_results = {}
            for key, raw_data in zip(keys, results):
                if raw_data is not None:
                    try:
                        value = self._deserialize(raw_data)
                        batch_results[key] = value
                    except Exception as e:
                        self.logger.warning("Failed to deserialize batch item", key=key, error=str(e))
            
            await redis_client.aclose()
            return batch_results
            
        except Exception as e:
            self.logger.error("Redis batch get failed", error=str(e))
            return {}
    
    async def batch_set(self, items: Dict[str, Any], ttl: int) -> int:
        """
        Set multiple values in Redis in batch
        
        Args:
            items: Dictionary mapping keys to values
            ttl: Time to live in seconds
            
        Returns:
            Number of items successfully set
        """
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Use pipeline for batch operations
            pipe = redis_client.pipeline()
            
            for key, value in items.items():
                try:
                    serialized_data = self._serialize(value)
                    pipe.setex(key, ttl, serialized_data)
                except Exception as e:
                    self.logger.warning("Failed to serialize batch item", key=key, error=str(e))
            
            results = await pipe.execute()
            
            await redis_client.aclose()
            
            # Count successful operations
            success_count = sum(1 for result in results if result)
            return success_count
            
        except Exception as e:
            self.logger.error("Redis batch set failed", error=str(e))
            return 0
    
    def _serialize(self, value: Any) -> bytes:
        """
        Serialize value for storage
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized bytes
        """
        try:
            # Use pickle for Python objects, JSON for simple types
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                serialized = json.dumps(value, default=str).encode('utf-8')
            else:
                serialized = pickle.dumps(value)
            
            # Apply compression if enabled
            if self.config.enable_compression and len(serialized) > 1024:  # Only compress larger data
                serialized = gzip.compress(serialized)
                # Add compression marker
                serialized = b'GZIP:' + serialized
            
            return serialized
            
        except Exception as e:
            self.logger.error("Serialization failed", error=str(e))
            raise
    
    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize value from storage
        
        Args:
            data: Serialized bytes
            
        Returns:
            Deserialized value
        """
        try:
            # Check for compression marker
            if data.startswith(b'GZIP:'):
                data = gzip.decompress(data[5:])  # Remove 'GZIP:' prefix
            
            # Try JSON first (faster for simple types)
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(data)
                
        except Exception as e:
            self.logger.error("Deserialization failed", error=str(e))
            raise
    
    async def close(self):
        """Close Redis connection pool"""
        try:
            if self.redis_pool:
                await self.redis_pool.aclose()
                self.logger.info("Redis connection pool closed")
        except Exception as e:
            self.logger.error("Failed to close Redis connection pool", error=str(e))
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform Redis health check
        
        Returns:
            Health check results
        """
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            start_time = time.time()
            await redis_client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            info = await redis_client.info()
            await redis_client.aclose()
            
            return {
                'status': 'healthy',
                'ping_time_ms': ping_time,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }