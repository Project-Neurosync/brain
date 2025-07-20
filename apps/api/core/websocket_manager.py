"""
WebSocket Manager for NeuroSync
Handles real-time communication, live updates, and collaborative features
"""

import json
import logging
import asyncio
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of WebSocket messages"""
    # Connection management
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    
    # Project updates
    PROJECT_UPDATE = "project_update"
    DATA_INGESTION = "data_ingestion"
    SYNC_STATUS = "sync_status"
    
    # AI interactions
    AI_QUERY = "ai_query"
    AI_RESPONSE = "ai_response"
    AI_THINKING = "ai_thinking"
    
    # Collaboration
    USER_ACTIVITY = "user_activity"
    CURSOR_POSITION = "cursor_position"
    SELECTION_CHANGE = "selection_change"
    
    # Notifications
    NOTIFICATION = "notification"
    MENTION = "mention"
    ALERT = "alert"
    
    # File operations
    FILE_CHANGE = "file_change"
    CODE_ANALYSIS = "code_analysis"
    
    # System events
    ERROR = "error"
    STATUS = "status"

class NotificationLevel(Enum):
    """Notification severity levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class WebSocketMessage:
    """Standard WebSocket message format"""
    message_id: str
    message_type: MessageType
    timestamp: datetime
    sender_id: str
    project_id: Optional[str]
    data: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class ConnectedUser:
    """Information about a connected user"""
    user_id: str
    websocket: WebSocket
    project_id: Optional[str]
    connected_at: datetime
    last_heartbeat: datetime
    user_info: Dict[str, Any]
    subscriptions: Set[str]  # Event types user is subscribed to

@dataclass
class ProjectRoom:
    """Represents a project collaboration room"""
    project_id: str
    connected_users: Dict[str, ConnectedUser]
    active_sessions: Set[str]
    shared_state: Dict[str, Any]
    last_activity: datetime

class WebSocketManager:
    """
    Production-ready WebSocket manager for real-time collaboration
    
    Features:
    - Connection management with heartbeat monitoring
    - Project-based rooms for collaboration
    - Message broadcasting and targeted delivery
    - Event subscription system
    - Real-time notifications and alerts
    - User presence and activity tracking
    - Collaborative cursor and selection sharing
    - File change notifications
    - AI interaction streaming
    """
    
    def __init__(self):
        # Connection management
        self.connections: Dict[str, ConnectedUser] = {}
        self.project_rooms: Dict[str, ProjectRoom] = {}
        self.user_to_connection: Dict[str, str] = {}  # user_id -> connection_id
        
        # Event handlers
        self.event_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        
        # Heartbeat monitoring
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 60  # seconds
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Message queue for offline users
        self.offline_messages: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        
        # Statistics
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'rooms_active': 0
        }
        
        # Start heartbeat monitoring
        self._start_heartbeat_monitor()
    
    async def connect_user(self, websocket: WebSocket, user_id: str, 
                          project_id: Optional[str] = None,
                          user_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Connect a user to the WebSocket system
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
            project_id: Optional project to join
            user_info: Additional user information
            
        Returns:
            Connection ID
        """
        try:
            await websocket.accept()
            
            connection_id = str(uuid.uuid4())
            
            # Create connected user
            connected_user = ConnectedUser(
                user_id=user_id,
                websocket=websocket,
                project_id=project_id,
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow(),
                user_info=user_info or {},
                subscriptions=set()
            )
            
            # Store connection
            self.connections[connection_id] = connected_user
            self.user_to_connection[user_id] = connection_id
            
            # Join project room if specified
            if project_id:
                await self._join_project_room(connection_id, project_id)
            
            # Send connection confirmation
            await self._send_to_connection(connection_id, WebSocketMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.CONNECT,
                timestamp=datetime.utcnow(),
                sender_id="system",
                project_id=project_id,
                data={
                    'connection_id': connection_id,
                    'status': 'connected',
                    'project_id': project_id
                },
                metadata={}
            ))
            
            # Send any queued offline messages
            await self._deliver_offline_messages(user_id)
            
            # Update statistics
            self.stats['total_connections'] += 1
            self.stats['active_connections'] = len(self.connections)
            
            logger.info(f"User {user_id} connected with connection {connection_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to connect user {user_id}: {str(e)}")
            raise
    
    async def disconnect_user(self, connection_id: str):
        """Disconnect a user and clean up resources"""
        try:
            if connection_id not in self.connections:
                return
            
            connected_user = self.connections[connection_id]
            user_id = connected_user.user_id
            project_id = connected_user.project_id
            
            # Leave project room
            if project_id:
                await self._leave_project_room(connection_id, project_id)
            
            # Close WebSocket if still open
            if connected_user.websocket.client_state == WebSocketState.CONNECTED:
                await connected_user.websocket.close()
            
            # Clean up connections
            del self.connections[connection_id]
            if user_id in self.user_to_connection:
                del self.user_to_connection[user_id]
            
            # Update statistics
            self.stats['active_connections'] = len(self.connections)
            
            logger.info(f"User {user_id} disconnected")
            
        except Exception as e:
            logger.error(f"Failed to disconnect user: {str(e)}")
    
    async def broadcast_to_project(self, project_id: str, message: WebSocketMessage,
                                 exclude_user: Optional[str] = None):
        """
        Broadcast a message to all users in a project room
        
        Args:
            project_id: Project identifier
            message: Message to broadcast
            exclude_user: Optional user ID to exclude from broadcast
        """
        try:
            if project_id not in self.project_rooms:
                return
            
            room = self.project_rooms[project_id]
            
            # Send to all connected users in the room
            for connection_id, user in room.connected_users.items():
                if exclude_user and user.user_id == exclude_user:
                    continue
                
                await self._send_to_connection(connection_id, message)
            
            logger.debug(f"Broadcasted message to {len(room.connected_users)} users in project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast to project {project_id}: {str(e)}")
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """
        Send a message to a specific user
        
        Args:
            user_id: Target user identifier
            message: Message to send
        """
        try:
            connection_id = self.user_to_connection.get(user_id)
            
            if connection_id and connection_id in self.connections:
                await self._send_to_connection(connection_id, message)
            else:
                # User is offline, queue message
                self.offline_messages[user_id].append(message)
                logger.debug(f"Queued message for offline user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {str(e)}")
    
    async def notify_data_ingestion(self, project_id: str, source: str, 
                                  status: str, details: Dict[str, Any]):
        """Notify users about data ingestion progress"""
        message = WebSocketMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.DATA_INGESTION,
            timestamp=datetime.utcnow(),
            sender_id="system",
            project_id=project_id,
            data={
                'source': source,
                'status': status,
                'details': details
            },
            metadata={'notification_level': NotificationLevel.INFO.value}
        )
        
        await self.broadcast_to_project(project_id, message)
    
    async def notify_sync_status(self, project_id: str, integration: str,
                               status: str, progress: float, message_text: str):
        """Notify users about integration sync status"""
        message = WebSocketMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.SYNC_STATUS,
            timestamp=datetime.utcnow(),
            sender_id="system",
            project_id=project_id,
            data={
                'integration': integration,
                'status': status,
                'progress': progress,
                'message': message_text
            },
            metadata={'notification_level': NotificationLevel.INFO.value}
        )
        
        await self.broadcast_to_project(project_id, message)
    
    async def notify_ai_interaction(self, project_id: str, user_id: str,
                                  interaction_type: str, data: Dict[str, Any]):
        """Notify about AI interactions (queries, responses, thinking)"""
        message_type = {
            'query': MessageType.AI_QUERY,
            'response': MessageType.AI_RESPONSE,
            'thinking': MessageType.AI_THINKING
        }.get(interaction_type, MessageType.AI_RESPONSE)
        
        message = WebSocketMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            timestamp=datetime.utcnow(),
            sender_id=user_id,
            project_id=project_id,
            data=data,
            metadata={}
        )
        
        await self.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    async def notify_user_activity(self, project_id: str, user_id: str,
                                 activity_type: str, details: Dict[str, Any]):
        """Notify about user activity (cursor, selection, file changes)"""
        message_type = {
            'cursor': MessageType.CURSOR_POSITION,
            'selection': MessageType.SELECTION_CHANGE,
            'file_change': MessageType.FILE_CHANGE
        }.get(activity_type, MessageType.USER_ACTIVITY)
        
        message = WebSocketMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            timestamp=datetime.utcnow(),
            sender_id=user_id,
            project_id=project_id,
            data=details,
            metadata={'activity_type': activity_type}
        )
        
        await self.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    async def send_notification(self, user_id: str, title: str, message: str,
                              level: NotificationLevel = NotificationLevel.INFO,
                              action_url: Optional[str] = None):
        """Send a notification to a specific user"""
        notification_message = WebSocketMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.NOTIFICATION,
            timestamp=datetime.utcnow(),
            sender_id="system",
            project_id=None,
            data={
                'title': title,
                'message': message,
                'level': level.value,
                'action_url': action_url
            },
            metadata={'notification_level': level.value}
        )
        
        await self.send_to_user(user_id, notification_message)
    
    async def send_mention_notification(self, mentioned_user_id: str, 
                                      mentioning_user_id: str, project_id: str,
                                      context: str, location: str):
        """Send a mention notification"""
        message = WebSocketMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.MENTION,
            timestamp=datetime.utcnow(),
            sender_id=mentioning_user_id,
            project_id=project_id,
            data={
                'mentioned_by': mentioning_user_id,
                'context': context,
                'location': location,
                'project_id': project_id
            },
            metadata={'notification_level': NotificationLevel.INFO.value}
        )
        
        await self.send_to_user(mentioned_user_id, message)
    
    async def handle_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message from client"""
        try:
            if connection_id not in self.connections:
                return
            
            connected_user = self.connections[connection_id]
            
            # Parse message
            message = WebSocketMessage(
                message_id=message_data.get('message_id', str(uuid.uuid4())),
                message_type=MessageType(message_data.get('message_type')),
                timestamp=datetime.utcnow(),
                sender_id=connected_user.user_id,
                project_id=message_data.get('project_id'),
                data=message_data.get('data', {}),
                metadata=message_data.get('metadata', {})
            )
            
            # Update heartbeat
            connected_user.last_heartbeat = datetime.utcnow()
            
            # Handle different message types
            await self._handle_message_by_type(connection_id, message)
            
            # Update statistics
            self.stats['messages_received'] += 1
            
        except Exception as e:
            logger.error(f"Failed to handle message from {connection_id}: {str(e)}")
            await self._send_error(connection_id, f"Message handling failed: {str(e)}")
    
    async def get_project_presence(self, project_id: str) -> Dict[str, Any]:
        """Get presence information for a project"""
        if project_id not in self.project_rooms:
            return {'users': [], 'count': 0}
        
        room = self.project_rooms[project_id]
        
        users = []
        for user in room.connected_users.values():
            users.append({
                'user_id': user.user_id,
                'user_info': user.user_info,
                'connected_at': user.connected_at.isoformat(),
                'last_activity': user.last_heartbeat.isoformat()
            })
        
        return {
            'users': users,
            'count': len(users),
            'last_activity': room.last_activity.isoformat() if room.last_activity else None
        }
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            **self.stats,
            'rooms_active': len(self.project_rooms),
            'offline_message_queues': len(self.offline_messages),
            'heartbeat_interval': self.heartbeat_interval
        }
    
    async def _join_project_room(self, connection_id: str, project_id: str):
        """Join a user to a project room"""
        if project_id not in self.project_rooms:
            self.project_rooms[project_id] = ProjectRoom(
                project_id=project_id,
                connected_users={},
                active_sessions=set(),
                shared_state={},
                last_activity=datetime.utcnow()
            )
        
        room = self.project_rooms[project_id]
        connected_user = self.connections[connection_id]
        
        room.connected_users[connection_id] = connected_user
        room.last_activity = datetime.utcnow()
        
        # Notify other users in the room
        await self.broadcast_to_project(project_id, WebSocketMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.USER_ACTIVITY,
            timestamp=datetime.utcnow(),
            sender_id="system",
            project_id=project_id,
            data={
                'activity': 'user_joined',
                'user_id': connected_user.user_id,
                'user_info': connected_user.user_info
            },
            metadata={}
        ), exclude_user=connected_user.user_id)
    
    async def _leave_project_room(self, connection_id: str, project_id: str):
        """Remove a user from a project room"""
        if project_id not in self.project_rooms:
            return
        
        room = self.project_rooms[project_id]
        
        if connection_id in room.connected_users:
            connected_user = room.connected_users[connection_id]
            del room.connected_users[connection_id]
            
            # Notify other users
            await self.broadcast_to_project(project_id, WebSocketMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.USER_ACTIVITY,
                timestamp=datetime.utcnow(),
                sender_id="system",
                project_id=project_id,
                data={
                    'activity': 'user_left',
                    'user_id': connected_user.user_id
                },
                metadata={}
            ))
            
            # Clean up empty rooms
            if not room.connected_users:
                del self.project_rooms[project_id]
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send a message to a specific connection"""
        try:
            if connection_id not in self.connections:
                return
            
            connected_user = self.connections[connection_id]
            
            if connected_user.websocket.client_state == WebSocketState.CONNECTED:
                message_dict = asdict(message)
                message_dict['timestamp'] = message.timestamp.isoformat()
                message_dict['message_type'] = message.message_type.value
                
                await connected_user.websocket.send_text(json.dumps(message_dict))
                self.stats['messages_sent'] += 1
            
        except WebSocketDisconnect:
            await self.disconnect_user(connection_id)
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_id}: {str(e)}")
    
    async def _deliver_offline_messages(self, user_id: str):
        """Deliver queued messages to a newly connected user"""
        if user_id not in self.offline_messages:
            return
        
        messages = self.offline_messages[user_id]
        connection_id = self.user_to_connection.get(user_id)
        
        if connection_id:
            for message in messages:
                await self._send_to_connection(connection_id, message)
            
            # Clear delivered messages
            del self.offline_messages[user_id]
            logger.info(f"Delivered {len(messages)} offline messages to user {user_id}")
    
    async def _handle_message_by_type(self, connection_id: str, message: WebSocketMessage):
        """Handle message based on its type"""
        if message.message_type == MessageType.HEARTBEAT:
            await self._handle_heartbeat(connection_id, message)
        elif message.message_type == MessageType.USER_ACTIVITY:
            await self._handle_user_activity(connection_id, message)
        elif message.message_type == MessageType.AI_QUERY:
            await self._handle_ai_query(connection_id, message)
        # Add more message type handlers as needed
    
    async def _handle_heartbeat(self, connection_id: str, message: WebSocketMessage):
        """Handle heartbeat message"""
        if connection_id in self.connections:
            self.connections[connection_id].last_heartbeat = datetime.utcnow()
            
            # Send heartbeat response
            response = WebSocketMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.HEARTBEAT,
                timestamp=datetime.utcnow(),
                sender_id="system",
                project_id=None,
                data={'status': 'alive'},
                metadata={}
            )
            
            await self._send_to_connection(connection_id, response)
    
    async def _handle_user_activity(self, connection_id: str, message: WebSocketMessage):
        """Handle user activity message"""
        if message.project_id:
            await self.broadcast_to_project(
                message.project_id, message, exclude_user=message.sender_id
            )
    
    async def _handle_ai_query(self, connection_id: str, message: WebSocketMessage):
        """Handle AI query message"""
        # This would integrate with the AI service
        # For now, just broadcast to project members
        if message.project_id:
            await self.broadcast_to_project(
                message.project_id, message, exclude_user=message.sender_id
            )
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Send error message to connection"""
        error_msg = WebSocketMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ERROR,
            timestamp=datetime.utcnow(),
            sender_id="system",
            project_id=None,
            data={'error': error_message},
            metadata={}
        )
        
        await self._send_to_connection(connection_id, error_msg)
    
    def _start_heartbeat_monitor(self):
        """Start the heartbeat monitoring task"""
        async def heartbeat_monitor():
            while True:
                try:
                    await asyncio.sleep(self.heartbeat_interval)
                    await self._check_heartbeats()
                except Exception as e:
                    logger.error(f"Heartbeat monitor error: {str(e)}")
        
        self.heartbeat_task = asyncio.create_task(heartbeat_monitor())
    
    async def _check_heartbeats(self):
        """Check for stale connections and disconnect them"""
        current_time = datetime.utcnow()
        stale_connections = []
        
        for connection_id, user in self.connections.items():
            time_since_heartbeat = (current_time - user.last_heartbeat).total_seconds()
            
            if time_since_heartbeat > self.heartbeat_timeout:
                stale_connections.append(connection_id)
        
        # Disconnect stale connections
        for connection_id in stale_connections:
            logger.warning(f"Disconnecting stale connection {connection_id}")
            await self.disconnect_user(connection_id)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
