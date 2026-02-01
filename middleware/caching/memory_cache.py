"""
Memory Cache Backend

In-memory caching implementation with LRU/LFU eviction policies,
size limits, and performance optimization.
"""

import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, OrderedDict
from collections import OrderedDict as OrderedDictType
import asyncio
import sys
import structlog

logger = structlog.get_logger()


class MemoryCache:
    """In-memory cache backend with advanced eviction policies"""
    
    def __init__(self, config):
        self.config = config
        self.logger = structlog.get_logger()
        
        # Cache storage
        self._cache: OrderedDictType[str, Dict[str, Any]] = OrderedDict()
        self._access_times: Dict[str, float] = {}
        self._access_counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        
        # Memory tracking
        self._current_memory_usage = 0
        self._max_memory = config.max_memory_size
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
        
        self.logger.info(
            "Memory cache initialized",
            max_memory_mb=self._max_memory // (1024 * 1024),
            eviction_policy=config.eviction_policy.value
        )
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from memory cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        async with self._lock:
            try:
                if key not in self._cache:
                    self._stats['misses'] += 1
                    return default
                
                entry = self._cache[key]
                
                # Check if expired
                if self._is_expired(entry):
                    await self._remove_entry(key)
                    self._stats['misses'] += 1
                    return default
                
                # Update access tracking
                current_time = time.time()
                self._access_times[key] = current_time
                self._access_counts[key] = self._access_counts.get(key, 0) + 1
                
                # Move to end for LRU
                if self.config.eviction_policy.value == 'lru':
                    self._cache.move_to_end(key)
                
                self._stats['hits'] += 1
                return entry['value']
                
            except Exception as e:
                self.logger.error("Memory cache get failed", key=key, error=str(e))
                self._stats['misses'] += 1
                return default
    
    async def set(self, key: str, value: Any, ttl: int) -> bool:
        """
        Set value in memory cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        async with self._lock:
            try:
                current_time = time.time()
                expires_at = current_time + ttl
                
                # Calculate entry size
                entry_size = self._calculate_size(value)
                
                # Check if we need to evict entries
                await self._ensure_space(entry_size)
                
                # Create cache entry
                entry = {
                    'value': value,
                    'created_at': current_time,
                    'expires_at': expires_at,
                    'ttl': ttl,
                    'size_bytes': entry_size
                }
                
                # Remove old entry if exists
                if key in self._cache:
                    old_entry = self._cache[key]
                    self._current_memory_usage -= old_entry['size_bytes']
                
                # Add new entry
                self._cache[key] = entry
                self._access_times[key] = current_time
                self._access_counts[key] = self._access_counts.get(key, 0) + 1
                self._current_memory_usage += entry_size
                
                # Move to end for LRU
                if self.config.eviction_policy.value == 'lru':
                    self._cache.move_to_end(key)
                
                self._stats['sets'] += 1
                return True
                
            except Exception as e:
                self.logger.error("Memory cache set failed", key=key, error=str(e))
                return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from memory cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        async with self._lock:
            try:
                if key in self._cache:
                    await self._remove_entry(key)
                    self._stats['deletes'] += 1
                    return True
                return False
                
            except Exception as e:
                self.logger.error("Memory cache delete failed", key=key, error=str(e))
                return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in memory cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists and not expired, False otherwise
        """
        async with self._lock:
            try:
                if key not in self._cache:
                    return False
                
                entry = self._cache[key]
                
                # Check if expired
                if self._is_expired(entry):
                    await self._remove_entry(key)
                    return False
                
                return True
                
            except Exception as e:
                self.logger.error("Memory cache exists check failed", key=key, error=str(e))
                return False
    
    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Pattern to match keys (supports wildcards)
            
        Returns:
            Number of keys invalidated
        """
        async with self._lock:
            try:
                import fnmatch
                
                keys_to_remove = []
                for key in self._cache.keys():
                    if fnmatch.fnmatch(key, pattern):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    await self._remove_entry(key)
                
                return len(keys_to_remove)
                
            except Exception as e:
                self.logger.error("Memory cache invalidation failed", pattern=pattern, error=str(e))
                return 0
    
    async def clear(self) -> bool:
        """
        Clear all cache entries
        
        Returns:
            True if successful, False otherwise
        """
        async with self._lock:
            try:
                self._cache.clear()
                self._access_times.clear()
                self._access_counts.clear()
                self._current_memory_usage = 0
                
                # Reset stats
                self._stats = {
                    'hits': 0,
                    'misses': 0,
                    'sets': 0,
                    'deletes': 0,
                    'evictions': 0
                }
                
                return True
                
            except Exception as e:
                self.logger.error("Memory cache clear failed", error=str(e))
                return False
    
    async def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries
        
        Returns:
            Number of entries cleaned up
        """
        async with self._lock:
            try:
                current_time = time.time()
                expired_keys = []
                
                for key, entry in self._cache.items():
                    if self._is_expired(entry):
                        expired_keys.append(key)
                
                for key in expired_keys:
                    await self._remove_entry(key)
                
                if expired_keys:
                    self.logger.debug("Cleaned up expired entries", count=len(expired_keys))
                
                return len(expired_keys)
                
            except Exception as e:
                self.logger.error("Memory cache cleanup failed", error=str(e))
                return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        async with self._lock:
            try:
                total_requests = self._stats['hits'] + self._stats['misses']
                hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0.0
                
                return {
                    'total_keys': len(self._cache),
                    'memory_usage_bytes': self._current_memory_usage,
                    'memory_usage_mb': self._current_memory_usage / (1024 * 1024),
                    'memory_limit_mb': self._max_memory / (1024 * 1024),
                    'memory_utilization': self._current_memory_usage / self._max_memory if self._max_memory > 0 else 0.0,
                    'hit_rate': hit_rate,
                    'stats': self._stats.copy()
                }
                
            except Exception as e:
                self.logger.error("Failed to get memory cache stats", error=str(e))
                return {
                    'total_keys': 0,
                    'memory_usage_bytes': 0,
                    'error': str(e)
                }
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from memory cache in batch
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to values
        """
        results = {}
        
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        
        return results
    
    async def batch_set(self, items: Dict[str, Any], ttl: int) -> int:
        """
        Set multiple values in memory cache in batch
        
        Args:
            items: Dictionary mapping keys to values
            ttl: Time to live in seconds
            
        Returns:
            Number of items successfully set
        """
        success_count = 0
        
        for key, value in items.items():
            if await self.set(key, value, ttl):
                success_count += 1
        
        return success_count
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        return time.time() > entry['expires_at']
    
    async def _remove_entry(self, key: str):
        """Remove entry and update tracking"""
        if key in self._cache:
            entry = self._cache[key]
            self._current_memory_usage -= entry['size_bytes']
            del self._cache[key]
        
        if key in self._access_times:
            del self._access_times[key]
        
        if key in self._access_counts:
            del self._access_counts[key]
    
    async def _ensure_space(self, required_size: int):
        """Ensure there's enough space for new entry"""
        # Check if we need to evict entries
        while (self._current_memory_usage + required_size > self._max_memory and 
               len(self._cache) > 0):
            
            await self._evict_entry()
    
    async def _evict_entry(self):
        """Evict one entry based on eviction policy"""
        if not self._cache:
            return
        
        key_to_evict = None
        
        if self.config.eviction_policy.value == 'lru':
            # Least Recently Used - first item in OrderedDict
            key_to_evict = next(iter(self._cache))
            
        elif self.config.eviction_policy.value == 'lfu':
            # Least Frequently Used
            min_count = float('inf')
            for key in self._cache:
                count = self._access_counts.get(key, 0)
                if count < min_count:
                    min_count = count
                    key_to_evict = key
                    
        elif self.config.eviction_policy.value == 'ttl':
            # Shortest TTL remaining
            current_time = time.time()
            min_remaining_ttl = float('inf')
            
            for key, entry in self._cache.items():
                remaining_ttl = entry['expires_at'] - current_time
                if remaining_ttl < min_remaining_ttl:
                    min_remaining_ttl = remaining_ttl
                    key_to_evict = key
                    
        elif self.config.eviction_policy.value == 'fifo':
            # First In First Out - first item in OrderedDict
            key_to_evict = next(iter(self._cache))
        
        if key_to_evict:
            await self._remove_entry(key_to_evict)
            self._stats['evictions'] += 1
            
            self.logger.debug(
                "Evicted cache entry",
                key=key_to_evict,
                policy=self.config.eviction_policy.value
            )
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes"""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, bytes):
                return len(value)
            elif isinstance(value, (int, float)):
                return sys.getsizeof(value)
            elif isinstance(value, bool):
                return sys.getsizeof(value)
            elif isinstance(value, (list, tuple)):
                return sum(self._calculate_size(item) for item in value) + sys.getsizeof(value)
            elif isinstance(value, dict):
                return (sum(self._calculate_size(k) + self._calculate_size(v) for k, v in value.items()) + 
                       sys.getsizeof(value))
            else:
                # For other objects, use sys.getsizeof as approximation
                return sys.getsizeof(value)
                
        except Exception:
            # Fallback to a reasonable estimate
            return 1024  # 1KB default
    
    async def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory usage information"""
        async with self._lock:
            try:
                entries_by_size = []
                total_size = 0
                
                for key, entry in self._cache.items():
                    size = entry['size_bytes']
                    total_size += size
                    entries_by_size.append({
                        'key': key,
                        'size_bytes': size,
                        'created_at': entry['created_at'],
                        'expires_at': entry['expires_at']
                    })
                
                # Sort by size (largest first)
                entries_by_size.sort(key=lambda x: x['size_bytes'], reverse=True)
                
                return {
                    'total_entries': len(self._cache),
                    'total_size_bytes': total_size,
                    'total_size_mb': total_size / (1024 * 1024),
                    'average_entry_size_bytes': total_size / len(self._cache) if self._cache else 0,
                    'largest_entries': entries_by_size[:10],  # Top 10 largest entries
                    'memory_utilization': total_size / self._max_memory if self._max_memory > 0 else 0.0
                }
                
            except Exception as e:
                self.logger.error("Failed to get memory info", error=str(e))
                return {'error': str(e)}
    
    async def optimize(self):
        """Optimize cache by cleaning up expired entries and reorganizing"""
        async with self._lock:
            try:
                # Clean up expired entries
                expired_count = await self.cleanup_expired()
                
                # If using LRU, reorganize based on access times
                if self.config.eviction_policy.value == 'lru':
                    # Sort by access time and rebuild OrderedDict
                    sorted_items = sorted(
                        self._cache.items(),
                        key=lambda x: self._access_times.get(x[0], 0)
                    )
                    
                    self._cache.clear()
                    for key, entry in sorted_items:
                        self._cache[key] = entry
                
                self.logger.info(
                    "Cache optimization completed",
                    expired_cleaned=expired_count,
                    total_entries=len(self._cache),
                    memory_usage_mb=self._current_memory_usage / (1024 * 1024)
                )
                
            except Exception as e:
                self.logger.error("Cache optimization failed", error=str(e))