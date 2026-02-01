"""
Backpressure Handler

Manages backpressure in streaming systems to prevent system overload
and ensure stable performance under high load conditions.
"""

import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import structlog

logger = structlog.get_logger()


class BackpressureStrategy(Enum):
    """Backpressure handling strategies"""
    DROP_OLDEST = "drop_oldest"
    DROP_NEWEST = "drop_newest"
    THROTTLE = "throttle"
    BUFFER = "buffer"
    REJECT = "reject"
    ADAPTIVE = "adaptive"


class LoadLevel(Enum):
    """System load levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BackpressureConfig:
    """Configuration for backpressure handling"""
    strategy: BackpressureStrategy = BackpressureStrategy.ADAPTIVE
    max_queue_size: int = 10000
    max_memory_mb: int = 100
    throttle_rate_limit: int = 1000  # messages per second
    drop_threshold: float = 0.8  # Drop when queue is 80% full
    critical_threshold: float = 0.95  # Critical when queue is 95% full
    measurement_window: int = 60  # seconds
    adaptive_adjustment_factor: float = 0.1
    enable_metrics: bool = True


@dataclass
class BackpressureMetrics:
    """Metrics for backpressure monitoring"""
    messages_processed: int = 0
    messages_dropped: int = 0
    messages_throttled: int = 0
    messages_rejected: int = 0
    queue_size: int = 0
    memory_usage_mb: float = 0.0
    processing_rate: float = 0.0  # messages per second
    drop_rate: float = 0.0
    current_load_level: LoadLevel = LoadLevel.LOW
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int, burst: int = None):
        self.rate = rate  # tokens per second
        self.burst = burst or rate  # maximum tokens
        self.tokens = self.burst
        self.last_update = time.time()
    
    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens"""
        now = time.time()
        
        # Add tokens based on elapsed time
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait for tokens to be available"""
        if self.tokens >= tokens:
            return 0.0
        
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.rate


class LoadMonitor:
    """Monitors system load and determines load levels"""
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.measurements: List[Tuple[float, Dict[str, float]]] = []
        self.current_load = LoadLevel.LOW
    
    def add_measurement(self, queue_size: int, memory_usage: float, processing_rate: float):
        """Add a load measurement"""
        timestamp = time.time()
        measurement = {
            'queue_size': queue_size,
            'memory_usage': memory_usage,
            'processing_rate': processing_rate
        }
        
        self.measurements.append((timestamp, measurement))
        
        # Remove old measurements
        cutoff_time = timestamp - self.window_size
        self.measurements = [(t, m) for t, m in self.measurements if t > cutoff_time]
        
        # Update current load level
        self._update_load_level()
    
    def _update_load_level(self):
        """Update current load level based on recent measurements"""
        if not self.measurements:
            self.current_load = LoadLevel.LOW
            return
        
        # Get recent measurements
        recent_measurements = [m for _, m in self.measurements[-10:]]  # Last 10 measurements
        
        if not recent_measurements:
            self.current_load = LoadLevel.LOW
            return
        
        # Calculate averages
        avg_queue_size = sum(m['queue_size'] for m in recent_measurements) / len(recent_measurements)
        avg_memory_usage = sum(m['memory_usage'] for m in recent_measurements) / len(recent_measurements)
        avg_processing_rate = sum(m['processing_rate'] for m in recent_measurements) / len(recent_measurements)
        
        # Determine load level based on multiple factors
        load_score = 0
        
        # Queue size factor (0-40 points)
        if avg_queue_size > 8000:
            load_score += 40
        elif avg_queue_size > 5000:
            load_score += 30
        elif avg_queue_size > 2000:
            load_score += 20
        elif avg_queue_size > 500:
            load_score += 10
        
        # Memory usage factor (0-30 points)
        if avg_memory_usage > 80:
            load_score += 30
        elif avg_memory_usage > 60:
            load_score += 20
        elif avg_memory_usage > 40:
            load_score += 10
        
        # Processing rate factor (0-30 points)
        if avg_processing_rate < 10:
            load_score += 30
        elif avg_processing_rate < 50:
            load_score += 20
        elif avg_processing_rate < 100:
            load_score += 10
        
        # Determine load level
        if load_score >= 80:
            self.current_load = LoadLevel.CRITICAL
        elif load_score >= 60:
            self.current_load = LoadLevel.HIGH
        elif load_score >= 30:
            self.current_load = LoadLevel.MEDIUM
        else:
            self.current_load = LoadLevel.LOW
    
    def get_load_level(self) -> LoadLevel:
        """Get current load level"""
        return self.current_load


class BackpressureHandler:
    """Handles backpressure in streaming systems"""
    
    def __init__(self, config: Optional[BackpressureConfig] = None):
        self.config = config or BackpressureConfig()
        self.logger = structlog.get_logger()
        
        # Components
        self.rate_limiter = RateLimiter(self.config.throttle_rate_limit)
        self.load_monitor = LoadMonitor(self.config.measurement_window)
        
        # Message queue
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        
        # Metrics
        self.metrics = BackpressureMetrics()
        
        # Adaptive parameters
        self.adaptive_rate_limit = self.config.throttle_rate_limit
        self.adaptive_drop_threshold = self.config.drop_threshold
        
        # Background tasks
        self._processor_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Message processor callback
        self.message_processor: Optional[Callable[[Any], Awaitable[bool]]] = None
        
        self.logger.info(
            "Backpressure handler initialized",
            strategy=self.config.strategy.value,
            max_queue_size=self.config.max_queue_size,
            throttle_rate_limit=self.config.throttle_rate_limit
        )
    
    def set_message_processor(self, processor: Callable[[Any], Awaitable[bool]]):
        """Set the message processor callback"""
        self.message_processor = processor
    
    async def start(self):
        """Start backpressure handler"""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        self._processor_task = asyncio.create_task(self._process_messages())
        self._monitor_task = asyncio.create_task(self._monitor_load())
        
        self.logger.info("Backpressure handler started")
    
    async def stop(self):
        """Stop backpressure handler"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel background tasks
        if self._processor_task and not self._processor_task.done():
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Backpressure handler stopped")
    
    async def handle_message(self, message: Any, priority: int = 0) -> bool:
        """
        Handle incoming message with backpressure
        
        Args:
            message: Message to handle
            priority: Message priority (higher = more important)
            
        Returns:
            True if message was accepted, False if rejected/dropped
        """
        try:
            # Check current load and apply strategy
            current_load = self.load_monitor.get_load_level()
            queue_utilization = self.message_queue.qsize() / self.config.max_queue_size
            
            # Apply backpressure strategy
            if self.config.strategy == BackpressureStrategy.DROP_OLDEST:
                return await self._handle_drop_oldest(message, queue_utilization)
            
            elif self.config.strategy == BackpressureStrategy.DROP_NEWEST:
                return await self._handle_drop_newest(message, queue_utilization)
            
            elif self.config.strategy == BackpressureStrategy.THROTTLE:
                return await self._handle_throttle(message)
            
            elif self.config.strategy == BackpressureStrategy.BUFFER:
                return await self._handle_buffer(message)
            
            elif self.config.strategy == BackpressureStrategy.REJECT:
                return await self._handle_reject(message, queue_utilization)
            
            elif self.config.strategy == BackpressureStrategy.ADAPTIVE:
                return await self._handle_adaptive(message, current_load, queue_utilization)
            
            else:
                # Default to buffer strategy
                return await self._handle_buffer(message)
                
        except Exception as e:
            self.logger.error("Error handling message with backpressure", error=str(e))
            return False
    
    async def _handle_drop_oldest(self, message: Any, queue_utilization: float) -> bool:
        """Handle message with drop oldest strategy"""
        if queue_utilization > self.config.drop_threshold:
            # Drop oldest messages to make room
            dropped_count = 0
            while (self.message_queue.qsize() >= self.config.max_queue_size * 0.9 and
                   not self.message_queue.empty()):
                try:
                    self.message_queue.get_nowait()
                    dropped_count += 1
                except asyncio.QueueEmpty:
                    break
            
            if dropped_count > 0:
                self.metrics.messages_dropped += dropped_count
                self.logger.debug("Dropped oldest messages", count=dropped_count)
        
        # Add new message
        try:
            self.message_queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            self.metrics.messages_dropped += 1
            return False
    
    async def _handle_drop_newest(self, message: Any, queue_utilization: float) -> bool:
        """Handle message with drop newest strategy"""
        if queue_utilization > self.config.drop_threshold:
            # Drop the new message
            self.metrics.messages_dropped += 1
            return False
        
        # Add new message
        try:
            self.message_queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            self.metrics.messages_dropped += 1
            return False
    
    async def _handle_throttle(self, message: Any) -> bool:
        """Handle message with throttling strategy"""
        # Check rate limit
        if not self.rate_limiter.acquire():
            # Wait for rate limit or drop message
            wait_time = self.rate_limiter.get_wait_time()
            if wait_time > 1.0:  # Don't wait more than 1 second
                self.metrics.messages_throttled += 1
                return False
            
            await asyncio.sleep(wait_time)
            self.metrics.messages_throttled += 1
        
        # Add message to queue
        try:
            await self.message_queue.put(message)
            return True
        except asyncio.QueueFull:
            self.metrics.messages_dropped += 1
            return False
    
    async def _handle_buffer(self, message: Any) -> bool:
        """Handle message with buffering strategy"""
        try:
            await self.message_queue.put(message)
            return True
        except asyncio.QueueFull:
            self.metrics.messages_dropped += 1
            return False
    
    async def _handle_reject(self, message: Any, queue_utilization: float) -> bool:
        """Handle message with rejection strategy"""
        if queue_utilization > self.config.drop_threshold:
            self.metrics.messages_rejected += 1
            return False
        
        try:
            self.message_queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            self.metrics.messages_rejected += 1
            return False
    
    async def _handle_adaptive(self, message: Any, current_load: LoadLevel, queue_utilization: float) -> bool:
        """Handle message with adaptive strategy"""
        # Adjust parameters based on load
        if current_load == LoadLevel.CRITICAL:
            # Very aggressive dropping
            if queue_utilization > 0.7:
                self.metrics.messages_dropped += 1
                return False
            # Reduce rate limit
            self.adaptive_rate_limit = max(100, self.adaptive_rate_limit * 0.8)
            
        elif current_load == LoadLevel.HIGH:
            # Moderate dropping
            if queue_utilization > 0.85:
                self.metrics.messages_dropped += 1
                return False
            # Slightly reduce rate limit
            self.adaptive_rate_limit = max(500, self.adaptive_rate_limit * 0.9)
            
        elif current_load == LoadLevel.MEDIUM:
            # Light throttling
            self.adaptive_rate_limit = min(self.config.throttle_rate_limit, 
                                         self.adaptive_rate_limit * 1.05)
            
        else:  # LOW load
            # Restore normal rate limit
            self.adaptive_rate_limit = min(self.config.throttle_rate_limit,
                                         self.adaptive_rate_limit * 1.1)
        
        # Update rate limiter
        self.rate_limiter.rate = self.adaptive_rate_limit
        
        # Apply throttling if needed
        if current_load in [LoadLevel.HIGH, LoadLevel.CRITICAL]:
            if not self.rate_limiter.acquire():
                self.metrics.messages_throttled += 1
                return False
        
        # Add message to queue
        try:
            self.message_queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            self.metrics.messages_dropped += 1
            return False
    
    async def _process_messages(self):
        """Background task to process messages from queue"""
        while self._running:
            try:
                # Get message with timeout
                try:
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Process message
                if self.message_processor:
                    try:
                        success = await self.message_processor(message)
                        if success:
                            self.metrics.messages_processed += 1
                        else:
                            self.metrics.messages_dropped += 1
                    except Exception as e:
                        self.logger.error("Message processor error", error=str(e))
                        self.metrics.messages_dropped += 1
                else:
                    # No processor set, just count as processed
                    self.metrics.messages_processed += 1
                
                # Mark task as done
                self.message_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Message processing error", error=str(e))
                await asyncio.sleep(0.1)
    
    async def _monitor_load(self):
        """Background task to monitor system load"""
        while self._running:
            try:
                # Calculate metrics
                queue_size = self.message_queue.qsize()
                memory_usage = self._estimate_memory_usage()
                processing_rate = self._calculate_processing_rate()
                
                # Update load monitor
                self.load_monitor.add_measurement(queue_size, memory_usage, processing_rate)
                
                # Update metrics
                self.metrics.queue_size = queue_size
                self.metrics.memory_usage_mb = memory_usage
                self.metrics.processing_rate = processing_rate
                self.metrics.current_load_level = self.load_monitor.get_load_level()
                self.metrics.drop_rate = self._calculate_drop_rate()
                self.metrics.last_updated = datetime.now(timezone.utc)
                
                # Log metrics if enabled
                if self.config.enable_metrics:
                    self.logger.debug(
                        "Backpressure metrics",
                        queue_size=queue_size,
                        memory_usage_mb=memory_usage,
                        processing_rate=processing_rate,
                        load_level=self.metrics.current_load_level.value,
                        drop_rate=self.metrics.drop_rate
                    )
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Load monitoring error", error=str(e))
                await asyncio.sleep(5)
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        # Simple estimation based on queue size
        # In practice, this could use more sophisticated memory tracking
        estimated_mb = (self.message_queue.qsize() * 1024) / (1024 * 1024)  # Assume 1KB per message
        return min(estimated_mb, self.config.max_memory_mb)
    
    def _calculate_processing_rate(self) -> float:
        """Calculate current processing rate"""
        # Simple rate calculation based on recent processed messages
        # In practice, this would track messages over time windows
        return self.metrics.messages_processed / max(1, 
            (datetime.now(timezone.utc) - self.metrics.last_updated).total_seconds())
    
    def _calculate_drop_rate(self) -> float:
        """Calculate current drop rate"""
        total_messages = (self.metrics.messages_processed + 
                         self.metrics.messages_dropped + 
                         self.metrics.messages_rejected)
        
        if total_messages == 0:
            return 0.0
        
        dropped_messages = self.metrics.messages_dropped + self.metrics.messages_rejected
        return dropped_messages / total_messages
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current backpressure metrics"""
        return {
            'metrics': {
                'messages_processed': self.metrics.messages_processed,
                'messages_dropped': self.metrics.messages_dropped,
                'messages_throttled': self.metrics.messages_throttled,
                'messages_rejected': self.metrics.messages_rejected,
                'queue_size': self.metrics.queue_size,
                'memory_usage_mb': self.metrics.memory_usage_mb,
                'processing_rate': self.metrics.processing_rate,
                'drop_rate': self.metrics.drop_rate,
                'current_load_level': self.metrics.current_load_level.value,
                'last_updated': self.metrics.last_updated.isoformat()
            },
            'configuration': {
                'strategy': self.config.strategy.value,
                'max_queue_size': self.config.max_queue_size,
                'max_memory_mb': self.config.max_memory_mb,
                'throttle_rate_limit': self.config.throttle_rate_limit,
                'drop_threshold': self.config.drop_threshold,
                'critical_threshold': self.config.critical_threshold
            },
            'adaptive_parameters': {
                'adaptive_rate_limit': self.adaptive_rate_limit,
                'adaptive_drop_threshold': self.adaptive_drop_threshold
            }
        }
    
    async def reset_metrics(self):
        """Reset backpressure metrics"""
        self.metrics = BackpressureMetrics()
        self.logger.info("Backpressure metrics reset")