"""
Production Slack Integration System for NeuroSync AI Backend
Handles Slack API connections, channel/message ingestion, and thread context.
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from pydantic import BaseModel

class SlackChannelType(str, Enum):
    """Slack channel types."""
    PUBLIC_CHANNEL = "public_channel"
    PRIVATE_CHANNEL = "private_channel"
    DIRECT_MESSAGE = "im"
    GROUP_MESSAGE = "mpim"

class SlackUser(BaseModel):
    """Slack user information."""
    id: str
    name: str
    real_name: Optional[str]
    display_name: Optional[str]
    email: Optional[str]
    is_bot: bool = False

class SlackChannel(BaseModel):
    """Slack channel information."""
    id: str
    name: str
    is_private: bool
    is_archived: bool
    creator: Optional[str]
    created: datetime
    topic: Optional[str]
    purpose: Optional[str]
    num_members: int = 0

class SlackMessage(BaseModel):
    """Slack message information."""
    ts: str  # Timestamp (unique message ID)
    channel: str
    user: Optional[str]
    text: str
    type: str
    subtype: Optional[str]
    thread_ts: Optional[str]  # Parent message timestamp for replies
    reply_count: int = 0
    reactions: List[Dict[str, Any]] = []
    files: List[Dict[str, Any]] = []
    created: datetime

class SlackThread(BaseModel):
    """Slack thread information."""
    parent_ts: str
    channel: str
    parent_message: SlackMessage
    replies: List[SlackMessage] = []
    reply_count: int = 0
    participants: Set[str] = set()

class SlackIntegrationConfig(BaseModel):
    """Slack integration configuration."""
    bot_token: str  # Bot User OAuth Token (xoxb-)
    include_private_channels: bool = False
    include_direct_messages: bool = False
    max_messages_per_channel: int = 1000
    excluded_channels: Set[str] = set()
    excluded_users: Set[str] = set()  # Bot users to exclude

class SlackIntegrationSystem:
    """
    Production-ready Slack integration system.
    Handles channel/message ingestion, thread context, and team communication analysis.
    """
    
    def __init__(
        self,
        config: SlackIntegrationConfig,
        file_processor=None,
        vector_service=None,
        knowledge_graph_service=None,
        importance_filter=None
    ):
        """Initialize the Slack Integration System."""
        self.config = config
        self.file_processor = file_processor
        self.vector_service = vector_service
        self.knowledge_graph_service = knowledge_graph_service
        self.importance_filter = importance_filter
        
        # HTTP session for API calls
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Thread pool for CPU-intensive operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # API base URL
        self.api_base = "https://slack.com/api"
        
        self.logger.info("Slack Integration System initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is available."""
        if not self._session or self._session.closed:
            headers = {
                'Authorization': f'Bearer {self.config.bot_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'NeuroSync-AI/1.0'
            }
            self._session = aiohttp.ClientSession(headers=headers)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Slack API connection and get workspace info."""
        await self._ensure_session()
        
        try:
            async with self._session.post(f"{self.api_base}/auth.test") as response:
                if response.status == 200:
                    auth_data = await response.json()
                    
                    if auth_data.get('ok'):
                        team_info = await self._get_team_info()
                        
                        return {
                            'status': 'connected',
                            'user': {
                                'user_id': auth_data.get('user_id'),
                                'user': auth_data.get('user'),
                                'bot_id': auth_data.get('bot_id')
                            },
                            'team': team_info,
                            'url': auth_data.get('url')
                        }
                    else:
                        return {
                            'status': 'error',
                            'error': auth_data.get('error', 'Authentication failed')
                        }
                else:
                    error_text = await response.text()
                    return {
                        'status': 'error',
                        'error': f'HTTP {response.status}: {error_text}',
                        'status_code': response.status
                    }
                    
        except Exception as e:
            self.logger.error(f"Slack connection test failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_channels(self, include_private: bool = None) -> List[SlackChannel]:
        """Get list of Slack channels."""
        await self._ensure_session()
        channels = []
        
        try:
            # Get public channels
            public_channels = await self._get_conversations_list(types="public_channel")
            channels.extend(public_channels)
            
            # Get private channels if requested and allowed
            if (include_private if include_private is not None else self.config.include_private_channels):
                private_channels = await self._get_conversations_list(types="private_channel")
                channels.extend(private_channels)
            
            # Filter excluded channels
            filtered_channels = [
                ch for ch in channels 
                if ch.id not in self.config.excluded_channels and ch.name not in self.config.excluded_channels
            ]
            
        except Exception as e:
            self.logger.error(f"Error fetching Slack channels: {str(e)}")
            return []
        
        self.logger.info(f"Retrieved {len(filtered_channels)} Slack channels")
        return filtered_channels
    
    async def get_channel_messages(
        self,
        channel_id: str,
        project_id: str,
        limit: int = None,
        oldest: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get messages from a Slack channel."""
        start_time = datetime.now()
        
        try:
            max_messages = limit or self.config.max_messages_per_channel
            
            # Get channel info
            channel_info = await self._get_channel_info(channel_id)
            if not channel_info:
                return {
                    'status': 'error',
                    'error': 'Channel not found or not accessible'
                }
            
            # Get messages
            messages = await self._get_conversation_history(
                channel_id=channel_id,
                limit=max_messages,
                oldest=oldest
            )
            
            # Process messages and threads
            processed_messages = 0
            processed_threads = 0
            failed_items = 0
            
            # Group messages by thread
            threads = {}
            standalone_messages = []
            
            for message in messages:
                if message.thread_ts and message.thread_ts != message.ts:
                    # This is a thread reply
                    if message.thread_ts not in threads:
                        threads[message.thread_ts] = []
                    threads[message.thread_ts].append(message)
                else:
                    standalone_messages.append(message)
            
            # Process standalone messages
            for message in standalone_messages:
                try:
                    await self._process_message_content(message, channel_info, project_id)
                    
                    # Create entities in knowledge graph
                    if self.knowledge_graph_service:
                        await self._create_message_entities(message, channel_info, project_id)
                    
                    processed_messages += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing message {message.ts}: {str(e)}")
                    failed_items += 1
            
            # Process threads
            for parent_ts, replies in threads.items():
                try:
                    # Find parent message
                    parent_message = next((m for m in standalone_messages if m.ts == parent_ts), None)
                    if not parent_message:
                        parent_message = await self._get_single_message(channel_id, parent_ts)
                    
                    if parent_message:
                        thread = SlackThread(
                            parent_ts=parent_ts,
                            channel=channel_id,
                            parent_message=parent_message,
                            replies=replies,
                            reply_count=len(replies),
                            participants=set([parent_message.user] + [r.user for r in replies if r.user])
                        )
                        
                        await self._process_thread_content(thread, channel_info, project_id)
                        processed_threads += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing thread {parent_ts}: {str(e)}")
                    failed_items += 1
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'status': 'completed',
                'channel': {
                    'id': channel_id,
                    'name': channel_info.name,
                    'type': 'private' if channel_info.is_private else 'public'
                },
                'total_messages': len(messages),
                'processed_messages': processed_messages,
                'processed_threads': processed_threads,
                'failed_items': failed_items,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error getting channel messages for {channel_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
    
    async def sync_workspace_data(
        self,
        neurosync_project_id: str,
        channel_filter: Optional[List[str]] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Synchronize Slack workspace data with NeuroSync."""
        start_time = datetime.now()
        
        try:
            # Get channels
            channels = await self.get_channels()
            
            # Filter channels if specified
            if channel_filter:
                channels = [
                    ch for ch in channels 
                    if ch.id in channel_filter or ch.name in channel_filter
                ]
            
            # Set time window
            oldest = datetime.now() - timedelta(days=days_back)
            
            # Process each channel
            total_messages = 0
            total_threads = 0
            failed_channels = 0
            
            for channel in channels:
                try:
                    result = await self.get_channel_messages(
                        channel_id=channel.id,
                        project_id=neurosync_project_id,
                        oldest=oldest
                    )
                    
                    if result.get('status') == 'completed':
                        total_messages += result.get('processed_messages', 0)
                        total_threads += result.get('processed_threads', 0)
                    else:
                        failed_channels += 1
                        
                except Exception as e:
                    self.logger.error(f"Error syncing channel {channel.name}: {str(e)}")
                    failed_channels += 1
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'status': 'completed',
                'neurosync_project': neurosync_project_id,
                'channels_processed': len(channels) - failed_channels,
                'channels_failed': failed_channels,
                'total_messages': total_messages,
                'total_threads': total_threads,
                'days_back': days_back,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error syncing workspace data: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
    
    async def _get_team_info(self) -> Dict[str, Any]:
        """Get Slack team/workspace information."""
        try:
            async with self._session.post(f"{self.api_base}/team.info") as response:
                if response.status == 200:
                    team_data = await response.json()
                    if team_data.get('ok'):
                        team = team_data.get('team', {})
                        return {
                            'id': team.get('id'),
                            'name': team.get('name'),
                            'domain': team.get('domain'),
                            'email_domain': team.get('email_domain')
                        }
        except Exception as e:
            self.logger.error(f"Error getting team info: {str(e)}")
        
        return {}
    
    async def _get_conversations_list(self, types: str = "public_channel") -> List[SlackChannel]:
        """Get list of conversations (channels)."""
        await self._ensure_session()
        channels = []
        cursor = None
        
        try:
            while True:
                params = {
                    'types': types,
                    'limit': 200
                }
                if cursor:
                    params['cursor'] = cursor
                
                async with self._session.post(f"{self.api_base}/conversations.list", json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('ok'):
                            for channel_data in data.get('channels', []):
                                channel = self._parse_channel(channel_data)
                                if channel:
                                    channels.append(channel)
                            
                            # Check for pagination
                            cursor = data.get('response_metadata', {}).get('next_cursor')
                            if not cursor:
                                break
                        else:
                            self.logger.error(f"Error getting conversations: {data.get('error')}")
                            break
                    else:
                        break
                        
        except Exception as e:
            self.logger.error(f"Error fetching conversations: {str(e)}")
        
        return channels
    
    async def _get_channel_info(self, channel_id: str) -> Optional[SlackChannel]:
        """Get detailed channel information."""
        await self._ensure_session()
        
        try:
            params = {'channel': channel_id}
            
            async with self._session.post(f"{self.api_base}/conversations.info", json=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('ok'):
                        return self._parse_channel(data.get('channel', {}))
                    else:
                        self.logger.error(f"Error getting channel info: {data.get('error')}")
                        
        except Exception as e:
            self.logger.error(f"Error getting channel info for {channel_id}: {str(e)}")
        
        return None
    
    async def _get_conversation_history(
        self,
        channel_id: str,
        limit: int = 100,
        oldest: Optional[datetime] = None
    ) -> List[SlackMessage]:
        """Get conversation history for a channel."""
        await self._ensure_session()
        messages = []
        cursor = None
        
        try:
            while len(messages) < limit:
                params = {
                    'channel': channel_id,
                    'limit': min(200, limit - len(messages))
                }
                
                if oldest:
                    params['oldest'] = str(oldest.timestamp())
                if cursor:
                    params['cursor'] = cursor
                
                async with self._session.post(f"{self.api_base}/conversations.history", json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('ok'):
                            for message_data in data.get('messages', []):
                                message = self._parse_message(message_data, channel_id)
                                if message and self._should_process_message(message):
                                    messages.append(message)
                            
                            # Check for pagination
                            cursor = data.get('response_metadata', {}).get('next_cursor')
                            if not cursor or not data.get('has_more'):
                                break
                        else:
                            self.logger.error(f"Error getting conversation history: {data.get('error')}")
                            break
                    else:
                        break
                        
        except Exception as e:
            self.logger.error(f"Error fetching conversation history for {channel_id}: {str(e)}")
        
        return messages
    
    async def _get_single_message(self, channel_id: str, ts: str) -> Optional[SlackMessage]:
        """Get a single message by timestamp."""
        await self._ensure_session()
        
        try:
            params = {
                'channel': channel_id,
                'latest': ts,
                'oldest': ts,
                'inclusive': True,
                'limit': 1
            }
            
            async with self._session.post(f"{self.api_base}/conversations.history", json=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('ok') and data.get('messages'):
                        message_data = data['messages'][0]
                        return self._parse_message(message_data, channel_id)
                        
        except Exception as e:
            self.logger.error(f"Error getting single message {ts}: {str(e)}")
        
        return None
    
    def _parse_channel(self, channel_data: Dict[str, Any]) -> Optional[SlackChannel]:
        """Parse channel data from Slack API response."""
        try:
            created_timestamp = channel_data.get('created', 0)
            created = datetime.fromtimestamp(created_timestamp) if created_timestamp else datetime.now()
            
            return SlackChannel(
                id=channel_data['id'],
                name=channel_data.get('name', ''),
                is_private=channel_data.get('is_private', False),
                is_archived=channel_data.get('is_archived', False),
                creator=channel_data.get('creator'),
                created=created,
                topic=channel_data.get('topic', {}).get('value'),
                purpose=channel_data.get('purpose', {}).get('value'),
                num_members=channel_data.get('num_members', 0)
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing channel data: {str(e)}")
            return None
    
    def _parse_message(self, message_data: Dict[str, Any], channel_id: str) -> Optional[SlackMessage]:
        """Parse message data from Slack API response."""
        try:
            ts = message_data.get('ts', '')
            created = datetime.fromtimestamp(float(ts)) if ts else datetime.now()
            
            return SlackMessage(
                ts=ts,
                channel=channel_id,
                user=message_data.get('user'),
                text=message_data.get('text', ''),
                type=message_data.get('type', 'message'),
                subtype=message_data.get('subtype'),
                thread_ts=message_data.get('thread_ts'),
                reply_count=message_data.get('reply_count', 0),
                reactions=message_data.get('reactions', []),
                files=message_data.get('files', []),
                created=created
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing message data: {str(e)}")
            return None
    
    def _should_process_message(self, message: SlackMessage) -> bool:
        """Determine if a message should be processed."""
        # Skip messages from excluded users
        if message.user in self.config.excluded_users:
            return False
        
        # Skip certain subtypes
        excluded_subtypes = {'channel_join', 'channel_leave', 'channel_topic', 'channel_purpose'}
        if message.subtype in excluded_subtypes:
            return False
        
        # Skip empty messages
        if not message.text.strip() and not message.files:
            return False
        
        return True
    
    async def _process_message_content(
        self,
        message: SlackMessage,
        channel: SlackChannel,
        project_id: str
    ) -> None:
        """Process message content for vector storage."""
        if not self.file_processor:
            return
        
        try:
            content_parts = [
                f"Slack Message in #{channel.name}",
                f"User: {message.user or 'Unknown'}",
                f"Timestamp: {message.created.isoformat()}",
                f"Content: {message.text}"
            ]
            
            # Add reaction information
            if message.reactions:
                reactions_text = ", ".join([
                    f"{reaction.get('name', 'unknown')} ({reaction.get('count', 0)})"
                    for reaction in message.reactions
                ])
                content_parts.append(f"Reactions: {reactions_text}")
            
            content = "\n\n".join(content_parts)
            
            await self.file_processor.upload_file(
                file_content=content.encode('utf-8'),
                filename=f"slack_message_{message.ts}.txt",
                project_id=project_id,
                user_id='slack_integration',
                source='slack'
            )
            
        except Exception as e:
            self.logger.error(f"Error processing message content for {message.ts}: {str(e)}")
    
    async def _process_thread_content(
        self,
        thread: SlackThread,
        channel: SlackChannel,
        project_id: str
    ) -> None:
        """Process thread content for vector storage."""
        if not self.file_processor:
            return
        
        try:
            content_parts = [
                f"Slack Thread in #{channel.name}",
                f"Started by: {thread.parent_message.user or 'Unknown'}",
                f"Started: {thread.parent_message.created.isoformat()}",
                f"Participants: {len(thread.participants)}",
                f"Replies: {thread.reply_count}",
                "",
                f"Original Message: {thread.parent_message.text}",
                ""
            ]
            
            # Add replies
            for i, reply in enumerate(thread.replies, 1):
                content_parts.append(f"Reply {i} by {reply.user or 'Unknown'}: {reply.text}")
            
            content = "\n\n".join(content_parts)
            
            await self.file_processor.upload_file(
                file_content=content.encode('utf-8'),
                filename=f"slack_thread_{thread.parent_ts}.txt",
                project_id=project_id,
                user_id='slack_integration',
                source='slack'
            )
            
        except Exception as e:
            self.logger.error(f"Error processing thread content for {thread.parent_ts}: {str(e)}")
    
    async def _create_message_entities(
        self,
        message: SlackMessage,
        channel: SlackChannel,
        project_id: str
    ) -> None:
        """Create message entities in knowledge graph."""
        if not self.knowledge_graph_service:
            return
        
        try:
            # Create message entity
            await self.knowledge_graph_service.add_entity(
                project_id=project_id,
                entity_type='SlackMessage',
                entity_id=f"slack_msg_{message.ts}",
                properties={
                    'text': message.text,
                    'channel': channel.name,
                    'user': message.user or 'unknown',
                    'type': message.type,
                    'subtype': message.subtype,
                    'created': message.created.isoformat(),
                    'reply_count': message.reply_count,
                    'has_reactions': len(message.reactions) > 0,
                    'platform': 'slack'
                }
            )
            
            # Create user entity if user exists
            if message.user:
                await self.knowledge_graph_service.add_entity(
                    project_id=project_id,
                    entity_type='Person',
                    entity_id=message.user,
                    properties={
                        'platform': 'slack'
                    }
                )
                
                # Create relationship
                await self.knowledge_graph_service.add_relationship(
                    project_id=project_id,
                    from_entity_type='Person',
                    from_entity_id=message.user,
                    to_entity_type='SlackMessage',
                    to_entity_id=f"slack_msg_{message.ts}",
                    relationship_type='POSTED',
                    properties={
                        'platform': 'slack',
                        'channel': channel.name,
                        'timestamp': message.created.isoformat()
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error creating message entities: {str(e)}")
