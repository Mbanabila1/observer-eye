"""
WebSocket Connection Manager

Manages WebSocket connections for real-time streaming with features including:
- Connection lifecycle management
- Authentication and authorization
- Connection pooling and load balancing
- Health monitoring and reconnection
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import structlog
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = structlog.get_logger()


class ConnectionState(Enum):
    """WebSocket connection states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    SUBSCRIBED = "subscribed"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(Enum):
    """WebSocket message types"""
    AUTH = "auth"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    DATA = "data"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    ACK = "ack"
    CONTROL = "control"


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    connection_id: str
    websocket: WebSocket
    state: ConnectionState
    user_id: Optional[str] = None
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0


@dataclass
class StreamMessage:
    """WebSocket stream message"""
    message_id: str
    message_type: MessageType
    stream_id: Optional[str]
    data: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionManager:
    """Manages WebSocket connections and their lifecycle"""
    
    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.stream_subscribers: Dict[str, Set[str]] = {}  # stream_id -> connection_ids
        self.logger = structlog.get_logger()
        
        # Configuration
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 300  # 5 minutes
        self.max_connections_per_user = 10
        self.max_message_size = 1024 * 1024  # 1MB
        
        # Statistics
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'total_messages': 0,
            'total_bytes_sent': 0,
            'total_bytes_received': 0,
            'connections_by_state': {state.value: 0 for state in ConnectionState}
        }
        
        # Background tasks
        self._cleanup_task = None
        self._heartbeat_task = None
        self._running = False
        
        self.logger.info("Connection manager initialized")
    
    async def connect(self, websocket: WebSocket, connection_id: Optional[str] = None) -> str:
        """
        Accept and register a new WebSocket connection
        
        Args:
            websocket: WebSocket instance
            connection_id: Optional custom connection ID
            
        Returns:
            Connection ID
        """
        if connection_id is None:
            connection_id = str(uuid.uuid4())
        
        try:
            await websocket.accept()
            
            # Create connection info
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                websocket=websocket,
                state=ConnectionState.CONNECTED
            )
            
            # Register connection
            self.connections[connection_id] = connection_info
            
            # Update statistics
            self.stats['total_connections'] += 1
            self.stats['active_connections'] += 1
            self.stats['connections_by_state'][ConnectionState.CONNECTED.value] += 1
            
            self.logger.info(
                "WebSocket connection established",
                connection_id=connection_id,
                client_host=websocket.client.host if websocket.client else "unknown"
            )
            
            return connection_id
            
        except Exception as e:
            self.logger.error("Failed to establish WebSocket connection", error=str(e))
            raise
    
    async def disconnect(self, connection_id: str, code: int = 1000, reason: str = "Normal closure"):
        """
        Disconnect and cleanup a WebSocket connection
        
        Args:
            connection_id: Connection ID to disconnect
            code: WebSocket close code
            reason: Disconnect reason
        """
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        
        try:
            # Update state
            connection_info.state = ConnectionState.DISCONNECTING
            
            # Close WebSocket if still connected
            if connection_info.websocket.client_state == WebSocketState.CONNECTED:
                await connection_info.websocket.close(code=code, reason=reason)
            
            # Remove from user connections
            if connection_info.user_id:
                if connection_info.user_id in self.user_connections:
                    self.user_connections[connection_info.user_id].discard(connection_id)
                    if not self.user_connections[connection_info.user_id]:
                        del self.user_connections[connection_info.user_id]
            
            # Remove from stream subscriptions
            for stream_id in connection_info.subscriptions:
                if stream_id in self.stream_subscribers:
                    self.stream_subscribers[stream_id].discard(connection_id)
                    if not self.stream_subscribers[stream_id]:
                        del self.stream_subscribers[stream_id]
            
            # Update statistics
            self.stats['active_connections'] -= 1
            self.stats['connections_by_state'][connection_info.state.value] -= 1
            self.stats['connections_by_state'][ConnectionState.DISCONNECTED.value] += 1
            
            # Remove connection
            del self.connections[connection_id]
            
            self.logger.info(
                "WebSocket connection disconnected",
                connection_id=connection_id,
                reason=reason,
                duration_seconds=(datetime.now(timezone.utc) - connection_info.connected_at).total_seconds()
            )
            
        except Exception as e:
            self.logger.error("Error during WebSocket disconnect", connection_id=connection_id, error=str(e))
    
    async def authenticate_connection(self, connection_id: str, user_id: str, auth_data: Dict[str, Any]) -> bool:
        """
        Authenticate a WebSocket connection
        
        Args:
            connection_id: Connection ID to authenticate
            user_id: User ID for authentication
            auth_data: Authentication data
            
        Returns:
            True if authentication successful, False otherwise
        """
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        
        try:
            # Check connection limits per user
            if user_id in self.user_connections:
                if len(self.user_connections[user_id]) >= self.max_connections_per_user:
                    self.logger.warning(
                        "User connection limit exceeded",
                        user_id=user_id,
                        current_connections=len(self.user_connections[user_id]),
                        limit=self.max_connections_per_user
                    )
                    return False
            
            # Update connection info
            connection_info.user_id = user_id
            connection_info.state = ConnectionState.AUTHENTICATED
            connection_info.metadata.update(auth_data)
            
            # Add to user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Update statistics
            self.stats['connections_by_state'][ConnectionState.CONNECTED.value] -= 1
            self.stats['connections_by_state'][ConnectionState.AUTHENTICATED.value] += 1
            
            self.logger.info(
                "WebSocket connection authenticated",
                connection_id=connection_id,
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            self.logger.error("Authentication failed", connection_id=connection_id, error=str(e))
            return False
    
    async def subscribe_to_stream(self, connection_id: str, stream_id: str) -> bool:
        """
        Subscribe connection to a data stream
        
        Args:
            connection_id: Connection ID to subscribe
            stream_id: Stream ID to subscribe to
            
        Returns:
            True if subscription successful, False otherwise
        """
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        
        try:
            # Add to connection subscriptions
            connection_info.subscriptions.add(stream_id)
            
            # Add to stream subscribers
            if stream_id not in self.stream_subscribers:
                self.stream_subscribers[stream_id] = set()
            self.stream_subscribers[stream_id].add(connection_id)
            
            # Update state if first subscription
            if connection_info.state == ConnectionState.AUTHENTICATED:
                connection_info.state = ConnectionState.SUBSCRIBED
                self.stats['connections_by_state'][ConnectionState.AUTHENTICATED.value] -= 1
                self.stats['connections_by_state'][ConnectionState.SUBSCRIBED.value] += 1
            
            self.logger.info(
                "Connection subscribed to stream",
                connection_id=connection_id,
                stream_id=stream_id,
                total_subscriptions=len(connection_info.subscriptions)
            )
            
            return True
            
        except Exception as e:
            self.logger.error("Stream subscription failed", connection_id=connection_id, stream_id=stream_id, error=str(e))
            return False
    
    async def unsubscribe_from_stream(self, connection_id: str, stream_id: str) -> bool:
        """
        Unsubscribe connection from a data stream
        
        Args:
            connection_id: Connection ID to unsubscribe
            stream_id: Stream ID to unsubscribe from
            
        Returns:
            True if unsubscription successful, False otherwise
        """
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        
        try:
            # Remove from connection subscriptions
            connection_info.subscriptions.discard(stream_id)
            
            # Remove from stream subscribers
            if stream_id in self.stream_subscribers:
                self.stream_subscribers[stream_id].discard(connection_id)
                if not self.stream_subscribers[stream_id]:
                    del self.stream_subscribers[stream_id]
            
            self.logger.info(
                "Connection unsubscribed from stream",
                connection_id=connection_id,
                stream_id=stream_id,
                remaining_subscriptions=len(connection_info.subscriptions)
            )
            
            return True
            
        except Exception as e:
            self.logger.error("Stream unsubscription failed", connection_id=connection_id, stream_id=stream_id, error=str(e))
            return False
    
    async def send_message(self, connection_id: str, message: StreamMessage) -> bool:
        """
        Send message to a specific connection
        
        Args:
            connection_id: Connection ID to send to
            message: Message to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        
        try:
            # Check connection state
            if connection_info.websocket.client_state != WebSocketState.CONNECTED:
                return False
            
            # Prepare message data
            message_data = {
                'id': message.message_id,
                'type': message.message_type.value,
                'stream_id': message.stream_id,
                'data': message.data,
                'timestamp': message.timestamp.isoformat(),
                'metadata': message.metadata
            }
            
            # Serialize message
            message_json = json.dumps(message_data, default=str)
            message_bytes = len(message_json.encode('utf-8'))
            
            # Check message size
            if message_bytes > self.max_message_size:
                self.logger.warning(
                    "Message too large",
                    connection_id=connection_id,
                    message_size=message_bytes,
                    max_size=self.max_message_size
                )
                return False
            
            # Send message
            await connection_info.websocket.send_text(message_json)
            
            # Update statistics
            connection_info.message_count += 1
            connection_info.bytes_sent += message_bytes
            connection_info.last_activity = datetime.now(timezone.utc)
            
            self.stats['total_messages'] += 1
            self.stats['total_bytes_sent'] += message_bytes
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to send message", connection_id=connection_id, error=str(e))
            # Mark connection for cleanup
            connection_info.state = ConnectionState.ERROR
            return False
    
    async def broadcast_to_stream(self, stream_id: str, message: StreamMessage) -> int:
        """
        Broadcast message to all subscribers of a stream
        
        Args:
            stream_id: Stream ID to broadcast to
            message: Message to broadcast
            
        Returns:
            Number of connections message was sent to
        """
        if stream_id not in self.stream_subscribers:
            return 0
        
        subscribers = self.stream_subscribers[stream_id].copy()
        successful_sends = 0
        
        # Send to all subscribers concurrently
        send_tasks = []
        for connection_id in subscribers:
            task = asyncio.create_task(self.send_message(connection_id, message))
            send_tasks.append(task)
        
        # Wait for all sends to complete
        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        # Count successful sends
        for result in results:
            if result is True:
                successful_sends += 1
        
        self.logger.debug(
            "Message broadcast to stream",
            stream_id=stream_id,
            subscribers=len(subscribers),
            successful_sends=successful_sends
        )
        
        return successful_sends
    
    async def receive_message(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Receive message from a connection
        
        Args:
            connection_id: Connection ID to receive from
            
        Returns:
            Received message data or None
        """
        if connection_id not in self.connections:
            return None
        
        connection_info = self.connections[connection_id]
        
        try:
            # Receive message
            message_text = await connection_info.websocket.receive_text()
            message_data = json.loads(message_text)
            
            # Update statistics
            message_bytes = len(message_text.encode('utf-8'))
            connection_info.bytes_received += message_bytes
            connection_info.last_activity = datetime.now(timezone.utc)
            
            self.stats['total_bytes_received'] += message_bytes
            
            return message_data
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id, reason="Client disconnected")
            return None
        except Exception as e:
            self.logger.error("Failed to receive message", connection_id=connection_id, error=str(e))
            connection_info.state = ConnectionState.ERROR
            return None
    
    async def send_heartbeat(self, connection_id: str) -> bool:
        """
        Send heartbeat message to connection
        
        Args:
            connection_id: Connection ID to send heartbeat to
            
        Returns:
            True if heartbeat sent successfully, False otherwise
        """
        heartbeat_message = StreamMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.HEARTBEAT,
            stream_id=None,
            data={'timestamp': datetime.now(timezone.utc).isoformat()}
        )
        
        success = await self.send_message(connection_id, heartbeat_message)
        
        if success and connection_id in self.connections:
            self.connections[connection_id].last_heartbeat = datetime.now(timezone.utc)
        
        return success
    
    async def cleanup_stale_connections(self) -> int:
        """
        Clean up stale and inactive connections
        
        Returns:
            Number of connections cleaned up
        """
        current_time = datetime.now(timezone.utc)
        stale_connections = []
        
        for connection_id, connection_info in self.connections.items():
            # Check for timeout
            time_since_activity = (current_time - connection_info.last_activity).total_seconds()
            
            if time_since_activity > self.connection_timeout:
                stale_connections.append(connection_id)
            elif connection_info.state == ConnectionState.ERROR:
                stale_connections.append(connection_id)
            elif connection_info.websocket.client_state == WebSocketState.DISCONNECTED:
                stale_connections.append(connection_id)
        
        # Clean up stale connections
        for connection_id in stale_connections:
            await self.disconnect(connection_id, reason="Stale connection cleanup")
        
        if stale_connections:
            self.logger.info("Cleaned up stale connections", count=len(stale_connections))
        
        return len(stale_connections)
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a connection"""
        if connection_id not in self.connections:
            return None
        
        connection_info = self.connections[connection_id]
        
        return {
            'connection_id': connection_info.connection_id,
            'state': connection_info.state.value,
            'user_id': connection_info.user_id,
            'subscriptions': list(connection_info.subscriptions),
            'connected_at': connection_info.connected_at.isoformat(),
            'last_heartbeat': connection_info.last_heartbeat.isoformat(),
            'last_activity': connection_info.last_activity.isoformat(),
            'message_count': connection_info.message_count,
            'bytes_sent': connection_info.bytes_sent,
            'bytes_received': connection_info.bytes_received,
            'metadata': connection_info.metadata
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics"""
        return {
            'stats': self.stats.copy(),
            'active_connections': len(self.connections),
            'active_streams': len(self.stream_subscribers),
            'authenticated_users': len(self.user_connections),
            'configuration': {
                'heartbeat_interval': self.heartbeat_interval,
                'connection_timeout': self.connection_timeout,
                'max_connections_per_user': self.max_connections_per_user,
                'max_message_size': self.max_message_size
            }
        }


class WebSocketManager:
    """High-level WebSocket management with additional features"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.logger = structlog.get_logger()
        
        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # Authentication callback
        self.auth_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[bool]]] = None
        
        self.logger.info("WebSocket manager initialized")
    
    def set_auth_callback(self, callback: Callable[[str, Dict[str, Any]], Awaitable[bool]]):
        """Set authentication callback function"""
        self.auth_callback = callback
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register handler for specific message type"""
        self.message_handlers[message_type] = handler
        self.logger.info("Message handler registered", message_type=message_type.value)
    
    async def handle_connection(self, websocket: WebSocket, connection_id: Optional[str] = None) -> str:
        """Handle new WebSocket connection with full lifecycle management"""
        connection_id = await self.connection_manager.connect(websocket, connection_id)
        
        try:
            while True:
                # Receive message
                message_data = await self.connection_manager.receive_message(connection_id)
                
                if message_data is None:
                    break  # Connection closed
                
                # Process message
                await self._process_message(connection_id, message_data)
                
        except Exception as e:
            self.logger.error("Connection handling error", connection_id=connection_id, error=str(e))
        finally:
            await self.connection_manager.disconnect(connection_id)
        
        return connection_id
    
    async def _process_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Process received message"""
        try:
            message_type_str = message_data.get('type')
            if not message_type_str:
                await self._send_error(connection_id, "Missing message type")
                return
            
            try:
                message_type = MessageType(message_type_str)
            except ValueError:
                await self._send_error(connection_id, f"Invalid message type: {message_type_str}")
                return
            
            # Handle authentication
            if message_type == MessageType.AUTH:
                await self._handle_auth_message(connection_id, message_data)
            
            # Handle subscription
            elif message_type == MessageType.SUBSCRIBE:
                await self._handle_subscribe_message(connection_id, message_data)
            
            # Handle unsubscription
            elif message_type == MessageType.UNSUBSCRIBE:
                await self._handle_unsubscribe_message(connection_id, message_data)
            
            # Handle heartbeat
            elif message_type == MessageType.HEARTBEAT:
                await self._handle_heartbeat_message(connection_id, message_data)
            
            # Handle custom message types
            elif message_type in self.message_handlers:
                await self.message_handlers[message_type](connection_id, message_data)
            
            else:
                await self._send_error(connection_id, f"Unhandled message type: {message_type_str}")
            
        except Exception as e:
            self.logger.error("Message processing error", connection_id=connection_id, error=str(e))
            await self._send_error(connection_id, "Message processing failed")
    
    async def _handle_auth_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle authentication message"""
        auth_data = message_data.get('data', {})
        user_id = auth_data.get('user_id')
        
        if not user_id:
            await self._send_error(connection_id, "Missing user_id in auth data")
            return
        
        # Use auth callback if available
        if self.auth_callback:
            auth_success = await self.auth_callback(user_id, auth_data)
        else:
            # Default authentication (accept all)
            auth_success = True
        
        if auth_success:
            success = await self.connection_manager.authenticate_connection(connection_id, user_id, auth_data)
            if success:
                await self._send_ack(connection_id, "Authentication successful")
            else:
                await self._send_error(connection_id, "Authentication failed")
        else:
            await self._send_error(connection_id, "Authentication rejected")
    
    async def _handle_subscribe_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle stream subscription message"""
        stream_id = message_data.get('stream_id')
        
        if not stream_id:
            await self._send_error(connection_id, "Missing stream_id")
            return
        
        success = await self.connection_manager.subscribe_to_stream(connection_id, stream_id)
        
        if success:
            await self._send_ack(connection_id, f"Subscribed to stream: {stream_id}")
        else:
            await self._send_error(connection_id, f"Failed to subscribe to stream: {stream_id}")
    
    async def _handle_unsubscribe_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle stream unsubscription message"""
        stream_id = message_data.get('stream_id')
        
        if not stream_id:
            await self._send_error(connection_id, "Missing stream_id")
            return
        
        success = await self.connection_manager.unsubscribe_from_stream(connection_id, stream_id)
        
        if success:
            await self._send_ack(connection_id, f"Unsubscribed from stream: {stream_id}")
        else:
            await self._send_error(connection_id, f"Failed to unsubscribe from stream: {stream_id}")
    
    async def _handle_heartbeat_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle heartbeat message"""
        # Send heartbeat response
        await self.connection_manager.send_heartbeat(connection_id)
    
    async def _send_ack(self, connection_id: str, message: str):
        """Send acknowledgment message"""
        ack_message = StreamMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ACK,
            stream_id=None,
            data={'message': message}
        )
        
        await self.connection_manager.send_message(connection_id, ack_message)
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Send error message"""
        error_msg = StreamMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ERROR,
            stream_id=None,
            data={'error': error_message}
        )
        
        await self.connection_manager.send_message(connection_id, error_msg)