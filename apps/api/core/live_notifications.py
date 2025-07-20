"""
Live Notifications Service for NeuroSync
Handles real-time notifications, alerts, mentions, and system events
"""

import json
import logging
import asyncio
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict, deque

from .websocket_manager import WebSocketManager, WebSocketMessage, MessageType, NotificationLevel
from .context_persistence import ContextPersistenceService, ContextType, ContextScope

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    # Data ingestion notifications
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    DATA_PROCESSED = "data_processed"
    
    # AI interaction notifications
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"
    INSIGHTS_GENERATED = "insights_generated"
    DECISION_TRACKED = "decision_tracked"
    
    # Collaboration notifications
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    MENTION = "mention"
    COMMENT_ADDED = "comment_added"
    
    # Project notifications
    PROJECT_UPDATED = "project_updated"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    
    # System notifications
    SYSTEM_MAINTENANCE = "system_maintenance"
    QUOTA_WARNING = "quota_warning"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR_OCCURRED = "error_occurred"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationChannel(Enum):
    """Notification delivery channels"""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"

@dataclass
class Notification:
    """Represents a notification"""
    notification_id: str
    notification_type: NotificationType
    title: str
    message: str
    level: NotificationLevel
    priority: NotificationPriority
    recipient_id: str
    project_id: Optional[str]
    created_at: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    channels: List[NotificationChannel]
    read: bool = False
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None

@dataclass
class NotificationRule:
    """Rules for when to send notifications"""
    rule_id: str
    user_id: str
    project_id: Optional[str]
    notification_types: Set[NotificationType]
    conditions: Dict[str, Any]
    channels: List[NotificationChannel]
    enabled: bool = True

@dataclass
class NotificationPreferences:
    """User notification preferences"""
    user_id: str
    email_enabled: bool = True
    push_enabled: bool = True
    websocket_enabled: bool = True
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None
    frequency_limit: int = 10  # Max notifications per hour
    priority_threshold: NotificationPriority = NotificationPriority.NORMAL

class LiveNotificationService:
    """
    Production-ready live notification service
    
    Features:
    - Real-time notification delivery via WebSocket
    - Multi-channel notification support (WebSocket, email, push)
    - User preferences and quiet hours
    - Notification rules and filtering
    - Rate limiting and frequency control
    - Mention detection and alerts
    - System event notifications
    - Notification history and read status
    - Integration sync status notifications
    """
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.context_service = ContextPersistenceService()
        
        # Notification storage
        self.notifications: Dict[str, Notification] = {}
        self.user_notifications: Dict[str, List[str]] = defaultdict(list)
        self.notification_rules: Dict[str, List[NotificationRule]] = defaultdict(list)
        self.user_preferences: Dict[str, NotificationPreferences] = {}
        
        # Rate limiting
        self.rate_limits: Dict[str, deque] = defaultdict(deque)  # user_id -> timestamps
        
        # Mention detection patterns
        self.mention_patterns = [
            r'@(\w+)',  # @username
            r'@\[([^\]]+)\]',  # @[Full Name]
        ]
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    async def send_notification(self, notification: Notification) -> bool:
        """
        Send a notification through appropriate channels
        
        Args:
            notification: Notification to send
            
        Returns:
            True if notification was sent successfully
        """
        try:
            # Check user preferences and rate limits
            if not await self._should_send_notification(notification):
                return False
            
            # Store notification
            self.notifications[notification.notification_id] = notification
            self.user_notifications[notification.recipient_id].append(notification.notification_id)
            
            # Send through each channel
            success = False
            
            for channel in notification.channels:
                if channel == NotificationChannel.WEBSOCKET:
                    success |= await self._send_websocket_notification(notification)
                elif channel == NotificationChannel.EMAIL:
                    success |= await self._send_email_notification(notification)
                elif channel == NotificationChannel.PUSH:
                    success |= await self._send_push_notification(notification)
                elif channel == NotificationChannel.IN_APP:
                    success |= await self._store_in_app_notification(notification)
            
            # Update rate limiting
            self._update_rate_limit(notification.recipient_id)
            
            # Store in context for history
            await self.context_service.store_context(
                project_id=notification.project_id or "system",
                user_id=notification.recipient_id,
                context_type=ContextType.NOTIFICATION,
                scope=ContextScope.USER,
                content=asdict(notification),
                metadata={
                    'notification_type': notification.notification_type.value,
                    'priority': notification.priority.value,
                    'channels': [c.value for c in notification.channels]
                }
            )
            
            logger.info(f"Sent notification {notification.notification_id} to user {notification.recipient_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    async def notify_sync_started(self, project_id: str, integration: str, user_id: str):
        """Notify that a sync has started"""
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.SYNC_STARTED,
            title=f"{integration.title()} Sync Started",
            message=f"Synchronization with {integration} has begun",
            level=NotificationLevel.INFO,
            priority=NotificationPriority.LOW,
            recipient_id=user_id,
            project_id=project_id,
            created_at=datetime.utcnow(),
            data={'integration': integration, 'status': 'started'},
            metadata={},
            channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP]
        )
        
        await self.send_notification(notification)
        
        # Also send WebSocket sync status
        await self.websocket_manager.notify_sync_status(
            project_id, integration, 'started', 0.0, 'Sync started'
        )
    
    async def notify_sync_completed(self, project_id: str, integration: str, 
                                  user_id: str, items_processed: int, duration: float):
        """Notify that a sync has completed successfully"""
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.SYNC_COMPLETED,
            title=f"{integration.title()} Sync Complete",
            message=f"Successfully processed {items_processed} items in {duration:.1f}s",
            level=NotificationLevel.SUCCESS,
            priority=NotificationPriority.NORMAL,
            recipient_id=user_id,
            project_id=project_id,
            created_at=datetime.utcnow(),
            data={
                'integration': integration,
                'status': 'completed',
                'items_processed': items_processed,
                'duration': duration
            },
            metadata={},
            channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP]
        )
        
        await self.send_notification(notification)
        
        # Send WebSocket sync status
        await self.websocket_manager.notify_sync_status(
            project_id, integration, 'completed', 100.0, 
            f'Completed - {items_processed} items processed'
        )
    
    async def notify_sync_failed(self, project_id: str, integration: str,
                               user_id: str, error_message: str):
        """Notify that a sync has failed"""
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.SYNC_FAILED,
            title=f"{integration.title()} Sync Failed",
            message=f"Sync failed: {error_message}",
            level=NotificationLevel.ERROR,
            priority=NotificationPriority.HIGH,
            recipient_id=user_id,
            project_id=project_id,
            created_at=datetime.utcnow(),
            data={
                'integration': integration,
                'status': 'failed',
                'error': error_message
            },
            metadata={},
            channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP, NotificationChannel.EMAIL]
        )
        
        await self.send_notification(notification)
        
        # Send WebSocket sync status
        await self.websocket_manager.notify_sync_status(
            project_id, integration, 'failed', 0.0, f'Failed: {error_message}'
        )
    
    async def notify_data_processed(self, project_id: str, source: str,
                                  items_count: int, user_ids: List[str]):
        """Notify that data has been processed and indexed"""
        for user_id in user_ids:
            notification = Notification(
                notification_id=str(uuid.uuid4()),
                notification_type=NotificationType.DATA_PROCESSED,
                title="New Data Available",
                message=f"{items_count} new items from {source} are now searchable",
                level=NotificationLevel.INFO,
                priority=NotificationPriority.LOW,
                recipient_id=user_id,
                project_id=project_id,
                created_at=datetime.utcnow(),
                data={
                    'source': source,
                    'items_count': items_count
                },
                metadata={},
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP]
            )
            
            await self.send_notification(notification)
    
    async def notify_ai_analysis_complete(self, project_id: str, user_id: str,
                                        analysis_type: str, insights_count: int):
        """Notify that AI analysis is complete"""
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.AI_ANALYSIS_COMPLETE,
            title="AI Analysis Complete",
            message=f"{analysis_type} analysis generated {insights_count} new insights",
            level=NotificationLevel.SUCCESS,
            priority=NotificationPriority.NORMAL,
            recipient_id=user_id,
            project_id=project_id,
            created_at=datetime.utcnow(),
            data={
                'analysis_type': analysis_type,
                'insights_count': insights_count
            },
            metadata={},
            channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP]
        )
        
        await self.send_notification(notification)
    
    async def notify_mention(self, mentioned_user_id: str, mentioning_user_id: str,
                           project_id: str, context: str, location: str):
        """Notify a user they've been mentioned"""
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.MENTION,
            title="You were mentioned",
            message=f"You were mentioned by a team member in {location}",
            level=NotificationLevel.INFO,
            priority=NotificationPriority.HIGH,
            recipient_id=mentioned_user_id,
            project_id=project_id,
            created_at=datetime.utcnow(),
            data={
                'mentioned_by': mentioning_user_id,
                'context': context,
                'location': location
            },
            metadata={},
            channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP, NotificationChannel.EMAIL]
        )
        
        await self.send_notification(notification)
        
        # Also send WebSocket mention
        await self.websocket_manager.send_mention_notification(
            mentioned_user_id, mentioning_user_id, project_id, context, location
        )
    
    async def notify_user_joined_project(self, project_id: str, new_user_id: str,
                                       existing_user_ids: List[str]):
        """Notify existing users that someone joined the project"""
        for user_id in existing_user_ids:
            notification = Notification(
                notification_id=str(uuid.uuid4()),
                notification_type=NotificationType.USER_JOINED,
                title="New Team Member",
                message=f"A new member has joined the project",
                level=NotificationLevel.INFO,
                priority=NotificationPriority.LOW,
                recipient_id=user_id,
                project_id=project_id,
                created_at=datetime.utcnow(),
                data={'new_user_id': new_user_id},
                metadata={},
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP]
            )
            
            await self.send_notification(notification)
    
    async def notify_quota_warning(self, user_id: str, quota_type: str,
                                 usage_percentage: float):
        """Notify user about quota usage warning"""
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.QUOTA_WARNING,
            title="Quota Warning",
            message=f"Your {quota_type} usage is at {usage_percentage:.0f}%",
            level=NotificationLevel.WARNING,
            priority=NotificationPriority.HIGH,
            recipient_id=user_id,
            project_id=None,
            created_at=datetime.utcnow(),
            data={
                'quota_type': quota_type,
                'usage_percentage': usage_percentage
            },
            metadata={},
            channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP, NotificationChannel.EMAIL]
        )
        
        await self.send_notification(notification)
    
    async def notify_system_error(self, user_id: str, error_type: str,
                                error_message: str, project_id: Optional[str] = None):
        """Notify user about system errors"""
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.ERROR_OCCURRED,
            title=f"System Error: {error_type}",
            message=error_message,
            level=NotificationLevel.ERROR,
            priority=NotificationPriority.URGENT,
            recipient_id=user_id,
            project_id=project_id,
            created_at=datetime.utcnow(),
            data={
                'error_type': error_type,
                'error_message': error_message
            },
            metadata={},
            channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP]
        )
        
        await self.send_notification(notification)
    
    async def get_user_notifications(self, user_id: str, 
                                   unread_only: bool = False,
                                   limit: int = 50) -> List[Notification]:
        """Get notifications for a user"""
        try:
            user_notification_ids = self.user_notifications.get(user_id, [])
            notifications = []
            
            for notification_id in user_notification_ids[-limit:]:
                if notification_id in self.notifications:
                    notification = self.notifications[notification_id]
                    
                    if unread_only and notification.read:
                        continue
                    
                    notifications.append(notification)
            
            # Sort by creation time (newest first)
            notifications.sort(key=lambda n: n.created_at, reverse=True)
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {str(e)}")
            return []
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            if notification_id not in self.notifications:
                return False
            
            notification = self.notifications[notification_id]
            
            if notification.recipient_id != user_id:
                return False
            
            notification.read = True
            notification.read_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False
    
    async def mark_all_notifications_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        try:
            user_notification_ids = self.user_notifications.get(user_id, [])
            marked_count = 0
            
            for notification_id in user_notification_ids:
                if notification_id in self.notifications:
                    notification = self.notifications[notification_id]
                    if not notification.read:
                        notification.read = True
                        notification.read_at = datetime.utcnow()
                        marked_count += 1
            
            return marked_count
            
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {str(e)}")
            return 0
    
    async def set_user_preferences(self, user_id: str, preferences: NotificationPreferences):
        """Set notification preferences for a user"""
        self.user_preferences[user_id] = preferences
        
        # Store preferences in context
        await self.context_service.store_context(
            project_id="system",
            user_id=user_id,
            context_type=ContextType.PREFERENCES,
            scope=ContextScope.USER,
            content=asdict(preferences),
            metadata={'type': 'notification_preferences'}
        )
    
    async def detect_mentions(self, content: str, project_id: str,
                            author_id: str, location: str) -> List[str]:
        """Detect mentions in content and send notifications"""
        import re
        
        mentioned_users = []
        
        for pattern in self.mention_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                # In a real implementation, you'd resolve usernames to user IDs
                # For now, assume the match is a user ID
                mentioned_user_id = match.strip()
                
                if mentioned_user_id != author_id:  # Don't notify self-mentions
                    mentioned_users.append(mentioned_user_id)
                    
                    await self.notify_mention(
                        mentioned_user_id, author_id, project_id, content, location
                    )
        
        return mentioned_users
    
    async def _should_send_notification(self, notification: Notification) -> bool:
        """Check if notification should be sent based on preferences and rate limits"""
        user_id = notification.recipient_id
        
        # Check user preferences
        preferences = self.user_preferences.get(user_id)
        if preferences:
            # Check if notifications are enabled for this channel
            if NotificationChannel.WEBSOCKET in notification.channels and not preferences.websocket_enabled:
                return False
            
            # Check priority threshold
            priority_levels = {
                NotificationPriority.LOW: 0,
                NotificationPriority.NORMAL: 1,
                NotificationPriority.HIGH: 2,
                NotificationPriority.URGENT: 3
            }
            
            if priority_levels[notification.priority] < priority_levels[preferences.priority_threshold]:
                return False
            
            # Check quiet hours
            if await self._is_quiet_hours(preferences):
                # Only allow urgent notifications during quiet hours
                if notification.priority != NotificationPriority.URGENT:
                    return False
        
        # Check rate limiting
        if self._is_rate_limited(user_id, preferences):
            return False
        
        return True
    
    async def _is_quiet_hours(self, preferences: NotificationPreferences) -> bool:
        """Check if current time is within user's quiet hours"""
        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False
        
        # Simple quiet hours check (can be enhanced for timezone support)
        current_time = datetime.utcnow().time()
        start_time = datetime.strptime(preferences.quiet_hours_start, "%H:%M").time()
        end_time = datetime.strptime(preferences.quiet_hours_end, "%H:%M").time()
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            # Quiet hours span midnight
            return current_time >= start_time or current_time <= end_time
    
    def _is_rate_limited(self, user_id: str, preferences: Optional[NotificationPreferences]) -> bool:
        """Check if user has exceeded rate limit"""
        if not preferences:
            return False
        
        current_time = datetime.utcnow()
        hour_ago = current_time - timedelta(hours=1)
        
        # Clean old timestamps
        user_timestamps = self.rate_limits[user_id]
        while user_timestamps and user_timestamps[0] < hour_ago:
            user_timestamps.popleft()
        
        # Check if limit exceeded
        return len(user_timestamps) >= preferences.frequency_limit
    
    def _update_rate_limit(self, user_id: str):
        """Update rate limit tracking for user"""
        self.rate_limits[user_id].append(datetime.utcnow())
    
    async def _send_websocket_notification(self, notification: Notification) -> bool:
        """Send notification via WebSocket"""
        try:
            await self.websocket_manager.send_notification(
                notification.recipient_id,
                notification.title,
                notification.message,
                notification.level,
                notification.action_url
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {str(e)}")
            return False
    
    async def _send_email_notification(self, notification: Notification) -> bool:
        """Send notification via email (placeholder)"""
        # Email integration would go here
        logger.info(f"Email notification sent to {notification.recipient_id}: {notification.title}")
        return True
    
    async def _send_push_notification(self, notification: Notification) -> bool:
        """Send push notification (placeholder)"""
        # Push notification integration would go here
        logger.info(f"Push notification sent to {notification.recipient_id}: {notification.title}")
        return True
    
    async def _store_in_app_notification(self, notification: Notification) -> bool:
        """Store in-app notification"""
        # Already stored in self.notifications, just return success
        return True
    
    def _start_cleanup_task(self):
        """Start background task to clean up old notifications"""
        async def cleanup_old_notifications():
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    await self._cleanup_old_notifications()
                except Exception as e:
                    logger.error(f"Notification cleanup error: {str(e)}")
        
        self.cleanup_task = asyncio.create_task(cleanup_old_notifications())
    
    async def _cleanup_old_notifications(self):
        """Clean up old notifications"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)  # Keep 30 days
        
        notifications_to_remove = []
        
        for notification_id, notification in self.notifications.items():
            if notification.created_at < cutoff_date:
                notifications_to_remove.append(notification_id)
        
        # Remove old notifications
        for notification_id in notifications_to_remove:
            notification = self.notifications[notification_id]
            
            # Remove from user notifications list
            if notification.recipient_id in self.user_notifications:
                user_notifications = self.user_notifications[notification.recipient_id]
                if notification_id in user_notifications:
                    user_notifications.remove(notification_id)
            
            # Remove notification
            del self.notifications[notification_id]
        
        if notifications_to_remove:
            logger.info(f"Cleaned up {len(notifications_to_remove)} old notifications")
