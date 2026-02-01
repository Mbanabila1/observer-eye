"""
Stream Handler

Manages different types of data streams with configuration, routing,
and processing capabilities for real-time data streaming.
"""

import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import structlog
from .websocket_manager import StreamMessage, MessageType

logger = structlog.get_logger()


class StreamType(Enum):
    """Types of data streams"""
    TELEMETRY = "telemetry"
    PERFORMANCE = "performance"
    LOGS = "logs"
    METRICS = "metrics"
    EVENTS = "events"
    ALERTS = "alerts"
    DASHBOARD = "dashboard"
    CUSTOM = "custom"


class StreamStatus(Enum):
    """Stream status states"""
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class StreamConfig:
    """Configuration for a data stream"""
    stream_id: str
    stream_type: StreamType
    name: str
    description: str = ""
    buffer_size: int = 1000
    batch_size: int = 10
    flush_interval: float = 1.0  # seconds
    max_subscribers: int = 100
    require_auth: bool = True
    allowed_users: Optional[Set[str]] = None
    data_filter: Optional[Callable[[Any], bool]] = None
    data_transformer: Optional[Callable[[Any], Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamStats:
    """Statistics for a data stream"""
    messages_sent: int = 0
    messages_dropped: int = 0
    bytes_sent: int = 0
    active_subscribers: int = 0
    total_subscribers: int = 0
    last_message_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    errors: int = 0


class StreamBuffer:
    """Circular buffer for stream data"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer: List[Any] = []
        self.index = 0
        self.full = False
    
    def add(self, item: Any):
        """Add item to buffer"""
        if len(self.buffer) < self.max_size:
            self.buffer.append(item)
        else:
            self.buffer[self.index] = item
            self.index = (self.index + 1) % self.max_size
            self.full = True
    
    def get_recent(self, count: int) -> List[Any]:
        """Get most recent items from buffer"""
        if not self.buffer:
            return []
        
        if not self.full:
            return self.buffer[-count:] if count < len(self.buffer) else self.buffer
        
        # Handle circular buffer
        if count >= self.max_size:
            # Return all items in correct order
            return self.buffer[self.index:] + self.buffer[:self.index]
        
        # Get recent items
        start_index = (self.index - count) % self.max_size
        if start_index < self.index:
            return self.buffer[start_index:self.index]
        else:
            return self.buffer[start_index:] + self.buffer[:self.index]
    
    def clear(self):
        """Clear buffer"""
        self.buffer.clear()
        self.index = 0
        self.full = False
    
    def size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)


class DataStream:
    """Individual data stream with buffering and subscriber management"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.status = StreamStatus.INACTIVE
        self.buffer = StreamBuffer(config.buffer_size)
        self.stats = StreamStats()
        self.subscribers: Set[str] = set()
        self.logger = structlog.get_logger()
        
        # Batching
        self.pending_batch: List[Any] = []
        self.last_flush_time = time.time()
        
        # Background tasks
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
        
        self.logger.info(
            "Data stream created",
            stream_id=config.stream_id,
            stream_type=config.stream_type.value,
            buffer_size=config.buffer_size
        )
    
    async def start(self):
        """Start the data stream"""
        if self.status != StreamStatus.INACTIVE:
            return
        
        self.status = StreamStatus.STARTING
        self._running = True
        
        # Start flush task
        self._flush_task = asyncio.create_task(self._flush_loop())
        
        self.status = StreamStatus.ACTIVE
        self.logger.info("Data stream started", stream_id=self.config.stream_id)
    
    async def stop(self):
        """Stop the data stream"""
        if self.status == StreamStatus.INACTIVE:
            return
        
        self.status = StreamStatus.STOPPING
        self._running = False
        
        # Cancel flush task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush any remaining data
        if self.pending_batch:
            await self._flush_batch()
        
        self.status = StreamStatus.INACTIVE
        self.logger.info("Data stream stopped", stream_id=self.config.stream_id)
    
    async def pause(self):
        """Pause the data stream"""
        if self.status == StreamStatus.ACTIVE:
            self.status = StreamStatus.PAUSED
            self.logger.info("Data stream paused", stream_id=self.config.stream_id)
    
    async def resume(self):
        """Resume the data stream"""
        if self.status == StreamStatus.PAUSED:
            self.status = StreamStatus.ACTIVE
            self.logger.info("Data stream resumed", stream_id=self.config.stream_id)
    
    def add_subscriber(self, connection_id: str) -> bool:
        """Add subscriber to stream"""
        if len(self.subscribers) >= self.config.max_subscribers:
            self.logger.warning(
                "Stream subscriber limit reached",
                stream_id=self.config.stream_id,
                current_subscribers=len(self.subscribers),
                limit=self.config.max_subscribers
            )
            return False
        
        self.subscribers.add(connection_id)
        self.stats.active_subscribers = len(self.subscribers)
        self.stats.total_subscribers += 1
        
        self.logger.debug(
            "Subscriber added to stream",
            stream_id=self.config.stream_id,
            connection_id=connection_id,
            total_subscribers=len(self.subscribers)
        )
        
        return True
    
    def remove_subscriber(self, connection_id: str):
        """Remove subscriber from stream"""
        self.subscribers.discard(connection_id)
        self.stats.active_subscribers = len(self.subscribers)
        
        self.logger.debug(
            "Subscriber removed from stream",
            stream_id=self.config.stream_id,
            connection_id=connection_id,
            remaining_subscribers=len(self.subscribers)
        )
    
    async def publish_data(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Publish data to stream"""
        if self.status not in [StreamStatus.ACTIVE, StreamStatus.PAUSED]:
            return False
        
        try:
            # Apply data filter if configured
            if self.config.data_filter and not self.config.data_filter(data):
                return False
            
            # Apply data transformer if configured
            if self.config.data_transformer:
                data = self.config.data_transformer(data)
            
            # Add to buffer
            self.buffer.add(data)
            
            # Add to pending batch if stream is active
            if self.status == StreamStatus.ACTIVE:
                self.pending_batch.append({
                    'data': data,
                    'metadata': metadata or {},
                    'timestamp': datetime.now(timezone.utc)
                })
                
                # Check if batch should be flushed
                if (len(self.pending_batch) >= self.config.batch_size or
                    time.time() - self.last_flush_time >= self.config.flush_interval):
                    await self._flush_batch()
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to publish data to stream", stream_id=self.config.stream_id, error=str(e))
            self.stats.errors += 1
            return False
    
    async def _flush_batch(self):
        """Flush pending batch to subscribers"""
        if not self.pending_batch or not self.subscribers:
            self.pending_batch.clear()
            return
        
        try:
            # Create batch message
            batch_message = StreamMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.DATA,
                stream_id=self.config.stream_id,
                data={
                    'stream_type': self.config.stream_type.value,
                    'batch': self.pending_batch.copy(),
                    'batch_size': len(self.pending_batch)
                },
                metadata={
                    'stream_name': self.config.name,
                    'flush_reason': 'batch_full' if len(self.pending_batch) >= self.config.batch_size else 'interval'
                }
            )
            
            # Calculate message size
            message_json = json.dumps(batch_message.data, default=str)
            message_bytes = len(message_json.encode('utf-8'))
            
            # Update statistics
            self.stats.messages_sent += 1
            self.stats.bytes_sent += message_bytes
            self.stats.last_message_time = datetime.now(timezone.utc)
            
            # Clear batch and update flush time
            self.pending_batch.clear()
            self.last_flush_time = time.time()
            
            # Return message for broadcasting (handled by StreamHandler)
            return batch_message
            
        except Exception as e:
            self.logger.error("Failed to flush batch", stream_id=self.config.stream_id, error=str(e))
            self.stats.errors += 1
            self.pending_batch.clear()
            return None
    
    async def _flush_loop(self):
        """Background task to flush batches at regular intervals"""
        while self._running:
            try:
                await asyncio.sleep(self.config.flush_interval)
                
                if self._running and self.pending_batch:
                    await self._flush_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Flush loop error", stream_id=self.config.stream_id, error=str(e))
                await asyncio.sleep(1)  # Brief pause before retrying
    
    def get_recent_data(self, count: int = 10) -> List[Any]:
        """Get recent data from buffer"""
        return self.buffer.get_recent(count)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stream statistics"""
        return {
            'stream_id': self.config.stream_id,
            'stream_type': self.config.stream_type.value,
            'status': self.status.value,
            'stats': {
                'messages_sent': self.stats.messages_sent,
                'messages_dropped': self.stats.messages_dropped,
                'bytes_sent': self.stats.bytes_sent,
                'active_subscribers': self.stats.active_subscribers,
                'total_subscribers': self.stats.total_subscribers,
                'errors': self.stats.errors,
                'last_message_time': self.stats.last_message_time.isoformat() if self.stats.last_message_time else None,
                'created_at': self.stats.created_at.isoformat()
            },
            'buffer_size': self.buffer.size(),
            'pending_batch_size': len(self.pending_batch)
        }


class StreamHandler:
    """Manages multiple data streams with routing and coordination"""
    
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.streams: Dict[str, DataStream] = {}
        self.stream_types: Dict[StreamType, Set[str]] = {stream_type: set() for stream_type in StreamType}
        self.logger = structlog.get_logger()
        
        # Global statistics
        self.global_stats = {
            'total_streams': 0,
            'active_streams': 0,
            'total_messages': 0,
            'total_bytes': 0,
            'total_subscribers': 0
        }
        
        self.logger.info("Stream handler initialized")
    
    async def create_stream(self, config: StreamConfig) -> bool:
        """Create a new data stream"""
        if config.stream_id in self.streams:
            self.logger.warning("Stream already exists", stream_id=config.stream_id)
            return False
        
        try:
            # Create stream
            stream = DataStream(config)
            self.streams[config.stream_id] = stream
            self.stream_types[config.stream_type].add(config.stream_id)
            
            # Update global statistics
            self.global_stats['total_streams'] += 1
            
            self.logger.info(
                "Stream created",
                stream_id=config.stream_id,
                stream_type=config.stream_type.value,
                name=config.name
            )
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to create stream", stream_id=config.stream_id, error=str(e))
            return False
    
    async def start_stream(self, stream_id: str) -> bool:
        """Start a data stream"""
        if stream_id not in self.streams:
            return False
        
        stream = self.streams[stream_id]
        await stream.start()
        
        if stream.status == StreamStatus.ACTIVE:
            self.global_stats['active_streams'] += 1
            return True
        
        return False
    
    async def stop_stream(self, stream_id: str) -> bool:
        """Stop a data stream"""
        if stream_id not in self.streams:
            return False
        
        stream = self.streams[stream_id]
        was_active = stream.status == StreamStatus.ACTIVE
        
        await stream.stop()
        
        if was_active:
            self.global_stats['active_streams'] -= 1
        
        return True
    
    async def delete_stream(self, stream_id: str) -> bool:
        """Delete a data stream"""
        if stream_id not in self.streams:
            return False
        
        stream = self.streams[stream_id]
        
        # Stop stream if active
        if stream.status == StreamStatus.ACTIVE:
            await stream.stop()
            self.global_stats['active_streams'] -= 1
        
        # Remove from type mapping
        self.stream_types[stream.config.stream_type].discard(stream_id)
        
        # Remove stream
        del self.streams[stream_id]
        self.global_stats['total_streams'] -= 1
        
        self.logger.info("Stream deleted", stream_id=stream_id)
        return True
    
    async def subscribe_to_stream(self, connection_id: str, stream_id: str) -> bool:
        """Subscribe connection to stream"""
        if stream_id not in self.streams:
            return False
        
        stream = self.streams[stream_id]
        
        # Check authentication requirements
        if stream.config.require_auth:
            connection_info = self.websocket_manager.connection_manager.get_connection_info(connection_id)
            if not connection_info or not connection_info.get('user_id'):
                self.logger.warning("Unauthenticated connection attempted to subscribe", connection_id=connection_id, stream_id=stream_id)
                return False
            
            # Check allowed users
            if stream.config.allowed_users:
                user_id = connection_info['user_id']
                if user_id not in stream.config.allowed_users:
                    self.logger.warning("User not allowed to subscribe to stream", user_id=user_id, stream_id=stream_id)
                    return False
        
        # Add subscriber to stream
        success = stream.add_subscriber(connection_id)
        
        if success:
            # Subscribe in WebSocket manager
            await self.websocket_manager.connection_manager.subscribe_to_stream(connection_id, stream_id)
            
            # Send recent data to new subscriber
            recent_data = stream.get_recent_data(10)
            if recent_data:
                welcome_message = StreamMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.DATA,
                    stream_id=stream_id,
                    data={
                        'stream_type': stream.config.stream_type.value,
                        'recent_data': recent_data,
                        'message': 'Welcome to stream'
                    },
                    metadata={'stream_name': stream.config.name}
                )
                
                await self.websocket_manager.connection_manager.send_message(connection_id, welcome_message)
        
        return success
    
    async def unsubscribe_from_stream(self, connection_id: str, stream_id: str) -> bool:
        """Unsubscribe connection from stream"""
        if stream_id not in self.streams:
            return False
        
        stream = self.streams[stream_id]
        stream.remove_subscriber(connection_id)
        
        # Unsubscribe in WebSocket manager
        await self.websocket_manager.connection_manager.unsubscribe_from_stream(connection_id, stream_id)
        
        return True
    
    async def publish_to_stream(self, stream_id: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Publish data to a specific stream"""
        if stream_id not in self.streams:
            return False
        
        stream = self.streams[stream_id]
        success = await stream.publish_data(data, metadata)
        
        if success:
            self.global_stats['total_messages'] += 1
            
            # Check if batch was flushed and broadcast if needed
            if stream.pending_batch:
                batch_message = await stream._flush_batch()
                if batch_message:
                    await self.websocket_manager.connection_manager.broadcast_to_stream(stream_id, batch_message)
                    self.global_stats['total_bytes'] += len(json.dumps(batch_message.data, default=str).encode('utf-8'))
        
        return success
    
    async def publish_to_stream_type(self, stream_type: StreamType, data: Any, metadata: Optional[Dict[str, Any]] = None) -> int:
        """Publish data to all streams of a specific type"""
        stream_ids = self.stream_types[stream_type].copy()
        successful_publishes = 0
        
        for stream_id in stream_ids:
            if await self.publish_to_stream(stream_id, data, metadata):
                successful_publishes += 1
        
        return successful_publishes
    
    def get_stream_info(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a stream"""
        if stream_id not in self.streams:
            return None
        
        stream = self.streams[stream_id]
        return {
            'config': {
                'stream_id': stream.config.stream_id,
                'stream_type': stream.config.stream_type.value,
                'name': stream.config.name,
                'description': stream.config.description,
                'buffer_size': stream.config.buffer_size,
                'batch_size': stream.config.batch_size,
                'flush_interval': stream.config.flush_interval,
                'max_subscribers': stream.config.max_subscribers,
                'require_auth': stream.config.require_auth,
                'metadata': stream.config.metadata
            },
            'stats': stream.get_stats()
        }
    
    def list_streams(self, stream_type: Optional[StreamType] = None) -> List[Dict[str, Any]]:
        """List all streams or streams of specific type"""
        if stream_type:
            stream_ids = self.stream_types[stream_type]
        else:
            stream_ids = self.streams.keys()
        
        return [self.get_stream_info(stream_id) for stream_id in stream_ids if stream_id in self.streams]
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global stream handler statistics"""
        # Update subscriber count
        total_subscribers = sum(len(stream.subscribers) for stream in self.streams.values())
        self.global_stats['total_subscribers'] = total_subscribers
        
        return {
            'global_stats': self.global_stats.copy(),
            'streams_by_type': {
                stream_type.value: len(stream_ids) 
                for stream_type, stream_ids in self.stream_types.items()
            },
            'streams_by_status': {
                status.value: len([s for s in self.streams.values() if s.status == status])
                for status in StreamStatus
            }
        }
    
    async def cleanup_inactive_streams(self) -> int:
        """Clean up inactive streams with no subscribers"""
        inactive_streams = []
        
        for stream_id, stream in self.streams.items():
            if (stream.status == StreamStatus.INACTIVE and 
                len(stream.subscribers) == 0 and
                (datetime.now(timezone.utc) - stream.stats.created_at).total_seconds() > 3600):  # 1 hour
                inactive_streams.append(stream_id)
        
        for stream_id in inactive_streams:
            await self.delete_stream(stream_id)
        
        if inactive_streams:
            self.logger.info("Cleaned up inactive streams", count=len(inactive_streams))
        
        return len(inactive_streams)