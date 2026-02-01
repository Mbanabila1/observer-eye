"""
Cache Invalidation Strategies

Provides intelligent cache invalidation mechanisms including:
- Time-based invalidation
- Event-driven invalidation
- Dependency-based invalidation
- Pattern-based invalidation
"""

import re
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, Pattern
from dataclasses import dataclass
from enum import Enum
import asyncio
import structlog

logger = structlog.get_logger()


class InvalidationType(Enum):
    """Types of cache invalidation"""
    TIME_BASED = "time_based"
    EVENT_DRIVEN = "event_driven"
    DEPENDENCY_BASED = "dependency_based"
    PATTERN_BASED = "pattern_based"
    MANUAL = "manual"


class InvalidationTrigger(Enum):
    """Triggers for cache invalidation"""
    TTL_EXPIRED = "ttl_expired"
    DATA_UPDATED = "data_updated"
    DEPENDENCY_CHANGED = "dependency_changed"
    PATTERN_MATCHED = "pattern_matched"
    MANUAL_REQUEST = "manual_request"
    MEMORY_PRESSURE = "memory_pressure"


@dataclass
class InvalidationRule:
    """Configuration for cache invalidation rule"""
    name: str
    invalidation_type: InvalidationType
    trigger: InvalidationTrigger
    pattern: Optional[str] = None
    dependencies: Optional[List[str]] = None
    ttl_seconds: Optional[int] = None
    condition: Optional[Callable[[str, Any], bool]] = None
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = None


@dataclass
class InvalidationEvent:
    """Cache invalidation event"""
    rule_name: str
    trigger: InvalidationTrigger
    affected_keys: List[str]
    timestamp: datetime
    metadata: Dict[str, Any] = None


class CacheInvalidationStrategy:
    """Comprehensive cache invalidation strategy manager"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.logger = structlog.get_logger()
        
        # Invalidation rules
        self.rules: List[InvalidationRule] = []
        self.rule_index: Dict[str, InvalidationRule] = {}
        
        # Dependency tracking
        self.dependencies: Dict[str, Set[str]] = {}  # key -> set of dependent keys
        self.reverse_dependencies: Dict[str, Set[str]] = {}  # key -> set of keys it depends on
        
        # Event tracking
        self.invalidation_events: List[InvalidationEvent] = []
        self.max_events_history = 1000
        
        # Background tasks
        self._cleanup_task = None
        self._running = False
        
        # Statistics
        self.stats = {
            'total_invalidations': 0,
            'invalidations_by_trigger': {trigger.value: 0 for trigger in InvalidationTrigger},
            'invalidations_by_type': {inv_type.value: 0 for inv_type in InvalidationType}
        }
        
        self.logger.info("Cache invalidation strategy initialized")
    
    def add_rule(self, rule: InvalidationRule):
        """
        Add invalidation rule
        
        Args:
            rule: InvalidationRule to add
        """
        self.rules.append(rule)
        self.rule_index[rule.name] = rule
        
        # Sort rules by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        
        self.logger.info(
            "Invalidation rule added",
            rule_name=rule.name,
            invalidation_type=rule.invalidation_type.value,
            trigger=rule.trigger.value
        )
    
    def remove_rule(self, rule_name: str):
        """
        Remove invalidation rule
        
        Args:
            rule_name: Name of rule to remove
        """
        if rule_name in self.rule_index:
            rule = self.rule_index[rule_name]
            self.rules.remove(rule)
            del self.rule_index[rule_name]
            
            self.logger.info("Invalidation rule removed", rule_name=rule_name)
    
    def add_dependency(self, key: str, depends_on: str):
        """
        Add dependency relationship between cache keys
        
        Args:
            key: Cache key that depends on another
            depends_on: Cache key that this key depends on
        """
        # Add to dependencies map
        if depends_on not in self.dependencies:
            self.dependencies[depends_on] = set()
        self.dependencies[depends_on].add(key)
        
        # Add to reverse dependencies map
        if key not in self.reverse_dependencies:
            self.reverse_dependencies[key] = set()
        self.reverse_dependencies[key].add(depends_on)
        
        self.logger.debug("Cache dependency added", key=key, depends_on=depends_on)
    
    def remove_dependency(self, key: str, depends_on: str):
        """
        Remove dependency relationship between cache keys
        
        Args:
            key: Cache key that depends on another
            depends_on: Cache key that this key depends on
        """
        # Remove from dependencies map
        if depends_on in self.dependencies:
            self.dependencies[depends_on].discard(key)
            if not self.dependencies[depends_on]:
                del self.dependencies[depends_on]
        
        # Remove from reverse dependencies map
        if key in self.reverse_dependencies:
            self.reverse_dependencies[key].discard(depends_on)
            if not self.reverse_dependencies[key]:
                del self.reverse_dependencies[key]
        
        self.logger.debug("Cache dependency removed", key=key, depends_on=depends_on)
    
    async def invalidate_by_key(self, key: str, trigger: InvalidationTrigger = InvalidationTrigger.MANUAL_REQUEST) -> int:
        """
        Invalidate cache entry by key and handle dependencies
        
        Args:
            key: Cache key to invalidate
            trigger: Trigger that caused the invalidation
            
        Returns:
            Number of keys invalidated
        """
        invalidated_keys = set()
        
        try:
            # Invalidate the key itself
            if await self.cache_manager.exists(key):
                await self.cache_manager.delete(key)
                invalidated_keys.add(key)
            
            # Invalidate dependent keys
            if key in self.dependencies:
                for dependent_key in self.dependencies[key]:
                    if await self.cache_manager.exists(dependent_key):
                        await self.cache_manager.delete(dependent_key)
                        invalidated_keys.add(dependent_key)
            
            # Record invalidation event
            if invalidated_keys:
                event = InvalidationEvent(
                    rule_name="manual_invalidation",
                    trigger=trigger,
                    affected_keys=list(invalidated_keys),
                    timestamp=datetime.now(timezone.utc),
                    metadata={"original_key": key}
                )
                self._record_event(event)
            
            self.logger.info(
                "Cache invalidation by key completed",
                key=key,
                trigger=trigger.value,
                invalidated_count=len(invalidated_keys)
            )
            
            return len(invalidated_keys)
            
        except Exception as e:
            self.logger.error("Cache invalidation by key failed", key=key, error=str(e))
            return 0
    
    async def invalidate_by_pattern(self, pattern: str, trigger: InvalidationTrigger = InvalidationTrigger.PATTERN_MATCHED) -> int:
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Pattern to match keys
            trigger: Trigger that caused the invalidation
            
        Returns:
            Number of keys invalidated
        """
        try:
            # Use cache manager's invalidate method
            invalidated_count = await self.cache_manager.invalidate(pattern)
            
            # Record invalidation event
            if invalidated_count > 0:
                event = InvalidationEvent(
                    rule_name="pattern_invalidation",
                    trigger=trigger,
                    affected_keys=[f"pattern:{pattern}"],
                    timestamp=datetime.now(timezone.utc),
                    metadata={"pattern": pattern, "count": invalidated_count}
                )
                self._record_event(event)
            
            self.logger.info(
                "Cache invalidation by pattern completed",
                pattern=pattern,
                trigger=trigger.value,
                invalidated_count=invalidated_count
            )
            
            return invalidated_count
            
        except Exception as e:
            self.logger.error("Cache invalidation by pattern failed", pattern=pattern, error=str(e))
            return 0
    
    async def invalidate_by_event(self, event_type: str, event_data: Dict[str, Any]) -> int:
        """
        Invalidate cache entries based on event
        
        Args:
            event_type: Type of event that occurred
            event_data: Data associated with the event
            
        Returns:
            Number of keys invalidated
        """
        total_invalidated = 0
        
        try:
            # Find applicable rules
            applicable_rules = [
                rule for rule in self.rules
                if (rule.enabled and 
                    rule.invalidation_type == InvalidationType.EVENT_DRIVEN and
                    self._rule_matches_event(rule, event_type, event_data))
            ]
            
            for rule in applicable_rules:
                try:
                    invalidated_count = await self._apply_invalidation_rule(rule, event_data)
                    total_invalidated += invalidated_count
                    
                    # Record event
                    if invalidated_count > 0:
                        event = InvalidationEvent(
                            rule_name=rule.name,
                            trigger=InvalidationTrigger.EVENT_DRIVEN,
                            affected_keys=[f"rule:{rule.name}"],
                            timestamp=datetime.now(timezone.utc),
                            metadata={"event_type": event_type, "event_data": event_data, "count": invalidated_count}
                        )
                        self._record_event(event)
                    
                except Exception as e:
                    self.logger.error(
                        "Failed to apply invalidation rule",
                        rule_name=rule.name,
                        event_type=event_type,
                        error=str(e)
                    )
            
            self.logger.info(
                "Event-driven cache invalidation completed",
                event_type=event_type,
                applicable_rules=len(applicable_rules),
                total_invalidated=total_invalidated
            )
            
            return total_invalidated
            
        except Exception as e:
            self.logger.error("Event-driven cache invalidation failed", event_type=event_type, error=str(e))
            return 0
    
    async def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries based on TTL rules
        
        Returns:
            Number of entries cleaned up
        """
        try:
            # Use cache manager's cleanup method
            cleaned_count = await self.cache_manager.cleanup_expired()
            
            # Apply TTL-based invalidation rules
            ttl_rules = [
                rule for rule in self.rules
                if (rule.enabled and 
                    rule.invalidation_type == InvalidationType.TIME_BASED and
                    rule.trigger == InvalidationTrigger.TTL_EXPIRED)
            ]
            
            for rule in ttl_rules:
                try:
                    rule_cleaned = await self._apply_ttl_rule(rule)
                    cleaned_count += rule_cleaned
                except Exception as e:
                    self.logger.error("Failed to apply TTL rule", rule_name=rule.name, error=str(e))
            
            # Record cleanup event
            if cleaned_count > 0:
                event = InvalidationEvent(
                    rule_name="ttl_cleanup",
                    trigger=InvalidationTrigger.TTL_EXPIRED,
                    affected_keys=[f"cleanup:{cleaned_count}"],
                    timestamp=datetime.now(timezone.utc),
                    metadata={"count": cleaned_count}
                )
                self._record_event(event)
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error("TTL cleanup failed", error=str(e))
            return 0
    
    async def start_background_cleanup(self, interval_seconds: int = 300):
        """
        Start background cleanup task
        
        Args:
            interval_seconds: Cleanup interval in seconds
        """
        if self._cleanup_task and not self._cleanup_task.done():
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._background_cleanup_loop(interval_seconds))
        
        self.logger.info("Background cache cleanup started", interval_seconds=interval_seconds)
    
    async def stop_background_cleanup(self):
        """Stop background cleanup task"""
        self._running = False
        
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Background cache cleanup stopped")
    
    async def _background_cleanup_loop(self, interval_seconds: int):
        """Background cleanup loop"""
        while self._running:
            try:
                await asyncio.sleep(interval_seconds)
                
                if self._running:
                    cleaned_count = await self.cleanup_expired()
                    if cleaned_count > 0:
                        self.logger.debug("Background cleanup completed", cleaned_count=cleaned_count)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Background cleanup error", error=str(e))
                await asyncio.sleep(60)  # Wait before retrying
    
    def _rule_matches_event(self, rule: InvalidationRule, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Check if invalidation rule matches event"""
        try:
            # Check pattern matching
            if rule.pattern:
                if not re.search(rule.pattern, event_type):
                    return False
            
            # Check custom condition
            if rule.condition:
                return rule.condition(event_type, event_data)
            
            return True
            
        except Exception as e:
            self.logger.error("Rule matching failed", rule_name=rule.name, error=str(e))
            return False
    
    async def _apply_invalidation_rule(self, rule: InvalidationRule, event_data: Dict[str, Any]) -> int:
        """Apply invalidation rule"""
        if rule.pattern:
            return await self.invalidate_by_pattern(rule.pattern, InvalidationTrigger.EVENT_DRIVEN)
        
        # For more complex rules, implement specific logic
        return 0
    
    async def _apply_ttl_rule(self, rule: InvalidationRule) -> int:
        """Apply TTL-based invalidation rule"""
        if rule.pattern and rule.ttl_seconds:
            # This would require more sophisticated tracking of entry creation times
            # For now, rely on the cache manager's built-in TTL handling
            return 0
        
        return 0
    
    def _record_event(self, event: InvalidationEvent):
        """Record invalidation event"""
        self.invalidation_events.append(event)
        
        # Keep only recent events
        if len(self.invalidation_events) > self.max_events_history:
            self.invalidation_events = self.invalidation_events[-self.max_events_history:]
        
        # Update statistics
        self.stats['total_invalidations'] += 1
        self.stats['invalidations_by_trigger'][event.trigger.value] += 1
    
    def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get invalidation statistics"""
        return {
            'stats': self.stats.copy(),
            'active_rules': len([rule for rule in self.rules if rule.enabled]),
            'total_rules': len(self.rules),
            'dependencies_count': len(self.dependencies),
            'recent_events': len(self.invalidation_events),
            'rules_by_type': {
                inv_type.value: len([rule for rule in self.rules if rule.invalidation_type == inv_type])
                for inv_type in InvalidationType
            }
        }
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent invalidation events"""
        recent_events = self.invalidation_events[-limit:] if limit > 0 else self.invalidation_events
        
        return [
            {
                'rule_name': event.rule_name,
                'trigger': event.trigger.value,
                'affected_keys': event.affected_keys,
                'timestamp': event.timestamp.isoformat(),
                'metadata': event.metadata or {}
            }
            for event in reversed(recent_events)
        ]
    
    def create_default_rules(self):
        """Create default invalidation rules"""
        default_rules = [
            InvalidationRule(
                name="user_data_update",
                invalidation_type=InvalidationType.EVENT_DRIVEN,
                trigger=InvalidationTrigger.DATA_UPDATED,
                pattern=r"user:.*",
                priority=100
            ),
            InvalidationRule(
                name="performance_metrics_update",
                invalidation_type=InvalidationType.EVENT_DRIVEN,
                trigger=InvalidationTrigger.DATA_UPDATED,
                pattern=r"metrics:.*",
                priority=90
            ),
            InvalidationRule(
                name="dashboard_config_update",
                invalidation_type=InvalidationType.EVENT_DRIVEN,
                trigger=InvalidationTrigger.DATA_UPDATED,
                pattern=r"dashboard:.*",
                priority=80
            ),
            InvalidationRule(
                name="memory_pressure_cleanup",
                invalidation_type=InvalidationType.PATTERN_BASED,
                trigger=InvalidationTrigger.MEMORY_PRESSURE,
                pattern=r"temp:.*",
                priority=50
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
        
        self.logger.info("Default invalidation rules created", count=len(default_rules))