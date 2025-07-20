"""
Collaborative Features Service for NeuroSync
Enables real-time collaboration, shared insights, and team coordination
"""

import json
import logging
import asyncio
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict

from .websocket_manager import WebSocketManager, WebSocketMessage, MessageType
from .live_notifications import LiveNotificationService
from .context_persistence import ContextPersistenceService, ContextType, ContextScope
from .knowledge_synthesis import MultiSourceKnowledgeSynthesis

logger = logging.getLogger(__name__)

class CollaborationEventType(Enum):
    """Types of collaboration events"""
    # Cursor and selection
    CURSOR_MOVED = "cursor_moved"
    TEXT_SELECTED = "text_selected"
    SELECTION_CLEARED = "selection_cleared"
    
    # File operations
    FILE_OPENED = "file_opened"
    FILE_CLOSED = "file_closed"
    FILE_EDITED = "file_edited"
    
    # AI interactions
    AI_QUERY_STARTED = "ai_query_started"
    AI_QUERY_SHARED = "ai_query_shared"
    INSIGHT_SHARED = "insight_shared"
    
    # Comments and discussions
    COMMENT_ADDED = "comment_added"
    COMMENT_REPLIED = "comment_replied"
    DISCUSSION_STARTED = "discussion_started"
    
    # Project activities
    ANALYSIS_SHARED = "analysis_shared"
    DECISION_PROPOSED = "decision_proposed"
    KNOWLEDGE_UPDATED = "knowledge_updated"

class CollaborationScope(Enum):
    """Scope of collaboration"""
    FILE = "file"
    PROJECT = "project"
    GLOBAL = "global"

@dataclass
class CursorPosition:
    """Represents a user's cursor position"""
    user_id: str
    file_path: str
    line: int
    column: int
    timestamp: datetime

@dataclass
class TextSelection:
    """Represents a user's text selection"""
    user_id: str
    file_path: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    selected_text: str
    timestamp: datetime

@dataclass
class SharedInsight:
    """Represents a shared AI insight"""
    insight_id: str
    shared_by: str
    project_id: str
    title: str
    content: str
    insight_type: str
    relevance_score: float
    created_at: datetime
    shared_at: datetime
    context: Dict[str, Any]
    tags: List[str]
    reactions: Dict[str, List[str]]  # reaction_type -> list of user_ids

@dataclass
class CollaborativeComment:
    """Represents a collaborative comment"""
    comment_id: str
    author_id: str
    project_id: str
    content: str
    context: Dict[str, Any]  # file_path, line_number, etc.
    created_at: datetime
    updated_at: Optional[datetime]
    replies: List[str]  # List of reply comment IDs
    mentions: List[str]  # List of mentioned user IDs
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

@dataclass
class CollaborationSession:
    """Represents an active collaboration session"""
    session_id: str
    project_id: str
    participants: Set[str]
    started_at: datetime
    last_activity: datetime
    shared_state: Dict[str, Any]
    active_files: Set[str]
    ai_context: Dict[str, Any]

class CollaborativeFeaturesService:
    """
    Production-ready collaborative features service
    
    Features:
    - Real-time cursor and selection sharing
    - Collaborative AI query sharing and insights
    - Shared project insights and knowledge
    - Team comments and discussions
    - Live presence and activity tracking
    - Collaborative decision making
    - Knowledge sharing and team learning
    - Project-wide collaboration sessions
    """
    
    def __init__(self, websocket_manager: WebSocketManager, 
                 notification_service: LiveNotificationService):
        self.websocket_manager = websocket_manager
        self.notification_service = notification_service
        self.context_service = ContextPersistenceService()
        self.knowledge_synthesis = MultiSourceKnowledgeSynthesis()
        
        # Collaboration state
        self.cursor_positions: Dict[str, CursorPosition] = {}  # user_id -> position
        self.text_selections: Dict[str, TextSelection] = {}   # user_id -> selection
        self.shared_insights: Dict[str, SharedInsight] = {}   # insight_id -> insight
        self.comments: Dict[str, CollaborativeComment] = {}   # comment_id -> comment
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}  # project_id -> session
        
        # Project-based tracking
        self.project_participants: Dict[str, Set[str]] = defaultdict(set)  # project_id -> user_ids
        self.user_activities: Dict[str, Dict[str, datetime]] = defaultdict(dict)  # user_id -> activity -> timestamp
        
        # File-based collaboration
        self.file_collaborators: Dict[str, Set[str]] = defaultdict(set)  # file_path -> user_ids
        
        # AI collaboration
        self.shared_ai_sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session_data
    
    async def start_collaboration_session(self, project_id: str, user_id: str) -> CollaborationSession:
        """Start or join a collaboration session for a project"""
        try:
            if project_id not in self.collaboration_sessions:
                # Create new session
                session = CollaborationSession(
                    session_id=str(uuid.uuid4()),
                    project_id=project_id,
                    participants=set(),
                    started_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                    shared_state={},
                    active_files=set(),
                    ai_context={}
                )
                self.collaboration_sessions[project_id] = session
            else:
                session = self.collaboration_sessions[project_id]
            
            # Add user to session
            session.participants.add(user_id)
            session.last_activity = datetime.utcnow()
            self.project_participants[project_id].add(user_id)
            
            # Notify other participants
            await self._broadcast_collaboration_event(
                project_id, user_id, CollaborationEventType.AI_QUERY_STARTED,
                {'action': 'user_joined_session', 'user_id': user_id}
            )
            
            # Send current session state to new participant
            await self._send_session_state(project_id, user_id)
            
            logger.info(f"User {user_id} joined collaboration session for project {project_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to start collaboration session: {str(e)}")
            raise
    
    async def update_cursor_position(self, user_id: str, project_id: str,
                                   file_path: str, line: int, column: int):
        """Update and broadcast user's cursor position"""
        try:
            cursor_position = CursorPosition(
                user_id=user_id,
                file_path=file_path,
                line=line,
                column=column,
                timestamp=datetime.utcnow()
            )
            
            self.cursor_positions[user_id] = cursor_position
            self.file_collaborators[file_path].add(user_id)
            
            # Update activity
            self._update_user_activity(user_id, 'cursor_moved')
            
            # Broadcast to other users in the project
            await self._broadcast_collaboration_event(
                project_id, user_id, CollaborationEventType.CURSOR_MOVED,
                {
                    'file_path': file_path,
                    'line': line,
                    'column': column,
                    'timestamp': cursor_position.timestamp.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to update cursor position: {str(e)}")
    
    async def update_text_selection(self, user_id: str, project_id: str,
                                  file_path: str, start_line: int, start_column: int,
                                  end_line: int, end_column: int, selected_text: str):
        """Update and broadcast user's text selection"""
        try:
            text_selection = TextSelection(
                user_id=user_id,
                file_path=file_path,
                start_line=start_line,
                start_column=start_column,
                end_line=end_line,
                end_column=end_column,
                selected_text=selected_text,
                timestamp=datetime.utcnow()
            )
            
            self.text_selections[user_id] = text_selection
            
            # Update activity
            self._update_user_activity(user_id, 'text_selected')
            
            # Broadcast to other users
            await self._broadcast_collaboration_event(
                project_id, user_id, CollaborationEventType.TEXT_SELECTED,
                {
                    'file_path': file_path,
                    'start_line': start_line,
                    'start_column': start_column,
                    'end_line': end_line,
                    'end_column': end_column,
                    'selected_text': selected_text[:100],  # Limit text length
                    'timestamp': text_selection.timestamp.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to update text selection: {str(e)}")
    
    async def share_ai_query(self, user_id: str, project_id: str, query: str,
                           context: Dict[str, Any], response: Optional[str] = None):
        """Share an AI query and response with team members"""
        try:
            session_id = str(uuid.uuid4())
            
            ai_session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'project_id': project_id,
                'query': query,
                'context': context,
                'response': response,
                'timestamp': datetime.utcnow().isoformat(),
                'shared': True
            }
            
            self.shared_ai_sessions[session_id] = ai_session_data
            
            # Update collaboration session
            if project_id in self.collaboration_sessions:
                session = self.collaboration_sessions[project_id]
                session.ai_context[session_id] = ai_session_data
                session.last_activity = datetime.utcnow()
            
            # Broadcast AI query to team
            await self._broadcast_collaboration_event(
                project_id, user_id, CollaborationEventType.AI_QUERY_SHARED,
                {
                    'session_id': session_id,
                    'query': query,
                    'context': context,
                    'response': response,
                    'shared_by': user_id
                }
            )
            
            # Store in context for persistence
            await self.context_service.store_context(
                project_id=project_id,
                user_id=user_id,
                context_type=ContextType.AI_INTERACTION,
                scope=ContextScope.PROJECT,
                content=ai_session_data,
                metadata={
                    'shared': True,
                    'session_id': session_id,
                    'collaboration_event': True
                }
            )
            
            logger.info(f"AI query shared by {user_id} in project {project_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to share AI query: {str(e)}")
            return None
    
    async def share_insight(self, user_id: str, project_id: str, title: str,
                          content: str, insight_type: str, context: Dict[str, Any],
                          tags: List[str] = None) -> str:
        """Share an insight with the team"""
        try:
            insight_id = str(uuid.uuid4())
            
            # Generate relevance score based on context and project knowledge
            relevance_score = await self._calculate_insight_relevance(
                project_id, content, context
            )
            
            shared_insight = SharedInsight(
                insight_id=insight_id,
                shared_by=user_id,
                project_id=project_id,
                title=title,
                content=content,
                insight_type=insight_type,
                relevance_score=relevance_score,
                created_at=datetime.utcnow(),
                shared_at=datetime.utcnow(),
                context=context,
                tags=tags or [],
                reactions={}
            )
            
            self.shared_insights[insight_id] = shared_insight
            
            # Broadcast to team members
            await self._broadcast_collaboration_event(
                project_id, user_id, CollaborationEventType.INSIGHT_SHARED,
                {
                    'insight_id': insight_id,
                    'title': title,
                    'content': content,
                    'insight_type': insight_type,
                    'relevance_score': relevance_score,
                    'tags': tags,
                    'shared_by': user_id
                }
            )
            
            # Send notifications to team members
            team_members = list(self.project_participants.get(project_id, set()))
            for member_id in team_members:
                if member_id != user_id:
                    await self.notification_service.notify_ai_analysis_complete(
                        project_id, member_id, f"Shared {insight_type}", 1
                    )
            
            # Store in context
            await self.context_service.store_context(
                project_id=project_id,
                user_id=user_id,
                context_type=ContextType.INSIGHT,
                scope=ContextScope.PROJECT,
                content=asdict(shared_insight),
                metadata={
                    'insight_id': insight_id,
                    'shared': True,
                    'relevance_score': relevance_score
                }
            )
            
            logger.info(f"Insight shared by {user_id} in project {project_id}")
            return insight_id
            
        except Exception as e:
            logger.error(f"Failed to share insight: {str(e)}")
            return ""
    
    async def add_comment(self, author_id: str, project_id: str, content: str,
                         context: Dict[str, Any]) -> str:
        """Add a collaborative comment"""
        try:
            comment_id = str(uuid.uuid4())
            
            # Detect mentions in content
            mentioned_users = await self.notification_service.detect_mentions(
                content, project_id, author_id, 
                context.get('location', 'project comment')
            )
            
            comment = CollaborativeComment(
                comment_id=comment_id,
                author_id=author_id,
                project_id=project_id,
                content=content,
                context=context,
                created_at=datetime.utcnow(),
                updated_at=None,
                replies=[],
                mentions=mentioned_users,
                resolved=False
            )
            
            self.comments[comment_id] = comment
            
            # Broadcast comment to team
            await self._broadcast_collaboration_event(
                project_id, author_id, CollaborationEventType.COMMENT_ADDED,
                {
                    'comment_id': comment_id,
                    'content': content,
                    'context': context,
                    'mentions': mentioned_users,
                    'author_id': author_id
                }
            )
            
            # Store in context
            await self.context_service.store_context(
                project_id=project_id,
                user_id=author_id,
                context_type=ContextType.COMMENT,
                scope=ContextScope.PROJECT,
                content=asdict(comment),
                metadata={
                    'comment_id': comment_id,
                    'mentions': mentioned_users
                }
            )
            
            logger.info(f"Comment added by {author_id} in project {project_id}")
            return comment_id
            
        except Exception as e:
            logger.error(f"Failed to add comment: {str(e)}")
            return ""
    
    async def reply_to_comment(self, author_id: str, project_id: str,
                             parent_comment_id: str, content: str) -> str:
        """Reply to a collaborative comment"""
        try:
            if parent_comment_id not in self.comments:
                raise ValueError("Parent comment not found")
            
            reply_id = await self.add_comment(
                author_id, project_id, content,
                {'type': 'reply', 'parent_comment_id': parent_comment_id}
            )
            
            # Add reply to parent comment
            parent_comment = self.comments[parent_comment_id]
            parent_comment.replies.append(reply_id)
            
            # Broadcast reply event
            await self._broadcast_collaboration_event(
                project_id, author_id, CollaborationEventType.COMMENT_REPLIED,
                {
                    'reply_id': reply_id,
                    'parent_comment_id': parent_comment_id,
                    'content': content,
                    'author_id': author_id
                }
            )
            
            return reply_id
            
        except Exception as e:
            logger.error(f"Failed to reply to comment: {str(e)}")
            return ""
    
    async def react_to_insight(self, user_id: str, insight_id: str, reaction: str):
        """Add a reaction to a shared insight"""
        try:
            if insight_id not in self.shared_insights:
                return False
            
            insight = self.shared_insights[insight_id]
            
            if reaction not in insight.reactions:
                insight.reactions[reaction] = []
            
            if user_id not in insight.reactions[reaction]:
                insight.reactions[reaction].append(user_id)
            
            # Broadcast reaction
            await self._broadcast_collaboration_event(
                insight.project_id, user_id, CollaborationEventType.INSIGHT_SHARED,
                {
                    'action': 'reaction_added',
                    'insight_id': insight_id,
                    'reaction': reaction,
                    'user_id': user_id,
                    'reactions': insight.reactions
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to react to insight: {str(e)}")
            return False
    
    async def get_project_collaboration_state(self, project_id: str) -> Dict[str, Any]:
        """Get current collaboration state for a project"""
        try:
            # Get active participants
            participants = list(self.project_participants.get(project_id, set()))
            
            # Get cursor positions for project participants
            cursor_positions = {}
            for user_id in participants:
                if user_id in self.cursor_positions:
                    cursor_positions[user_id] = asdict(self.cursor_positions[user_id])
            
            # Get text selections
            text_selections = {}
            for user_id in participants:
                if user_id in self.text_selections:
                    text_selections[user_id] = asdict(self.text_selections[user_id])
            
            # Get recent shared insights
            recent_insights = []
            for insight in self.shared_insights.values():
                if insight.project_id == project_id:
                    recent_insights.append(asdict(insight))
            
            # Sort by creation time
            recent_insights.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Get recent comments
            recent_comments = []
            for comment in self.comments.values():
                if comment.project_id == project_id:
                    recent_comments.append(asdict(comment))
            
            recent_comments.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Get collaboration session info
            session_info = {}
            if project_id in self.collaboration_sessions:
                session = self.collaboration_sessions[project_id]
                session_info = {
                    'session_id': session.session_id,
                    'participants': list(session.participants),
                    'started_at': session.started_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'active_files': list(session.active_files)
                }
            
            return {
                'project_id': project_id,
                'participants': participants,
                'cursor_positions': cursor_positions,
                'text_selections': text_selections,
                'recent_insights': recent_insights[:10],  # Last 10 insights
                'recent_comments': recent_comments[:20],  # Last 20 comments
                'session_info': session_info,
                'active_ai_sessions': len([s for s in self.shared_ai_sessions.values() 
                                         if s.get('project_id') == project_id])
            }
            
        except Exception as e:
            logger.error(f"Failed to get collaboration state: {str(e)}")
            return {}
    
    async def get_file_collaborators(self, file_path: str) -> List[Dict[str, Any]]:
        """Get users currently collaborating on a file"""
        try:
            collaborators = []
            user_ids = self.file_collaborators.get(file_path, set())
            
            for user_id in user_ids:
                collaborator_info = {'user_id': user_id}
                
                # Add cursor position if available
                if user_id in self.cursor_positions:
                    cursor = self.cursor_positions[user_id]
                    if cursor.file_path == file_path:
                        collaborator_info['cursor'] = {
                            'line': cursor.line,
                            'column': cursor.column,
                            'timestamp': cursor.timestamp.isoformat()
                        }
                
                # Add text selection if available
                if user_id in self.text_selections:
                    selection = self.text_selections[user_id]
                    if selection.file_path == file_path:
                        collaborator_info['selection'] = {
                            'start_line': selection.start_line,
                            'start_column': selection.start_column,
                            'end_line': selection.end_line,
                            'end_column': selection.end_column,
                            'timestamp': selection.timestamp.isoformat()
                        }
                
                collaborators.append(collaborator_info)
            
            return collaborators
            
        except Exception as e:
            logger.error(f"Failed to get file collaborators: {str(e)}")
            return []
    
    def _update_user_activity(self, user_id: str, activity_type: str):
        """Update user activity timestamp"""
        self.user_activities[user_id][activity_type] = datetime.utcnow()
    
    async def _broadcast_collaboration_event(self, project_id: str, sender_id: str,
                                           event_type: CollaborationEventType,
                                           data: Dict[str, Any]):
        """Broadcast collaboration event to project participants"""
        try:
            message = WebSocketMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.USER_ACTIVITY,
                timestamp=datetime.utcnow(),
                sender_id=sender_id,
                project_id=project_id,
                data={
                    'event_type': event_type.value,
                    **data
                },
                metadata={'collaboration_event': True}
            )
            
            await self.websocket_manager.broadcast_to_project(
                project_id, message, exclude_user=sender_id
            )
            
        except Exception as e:
            logger.error(f"Failed to broadcast collaboration event: {str(e)}")
    
    async def _send_session_state(self, project_id: str, user_id: str):
        """Send current collaboration session state to a user"""
        try:
            state = await self.get_project_collaboration_state(project_id)
            
            message = WebSocketMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.STATUS,
                timestamp=datetime.utcnow(),
                sender_id="system",
                project_id=project_id,
                data={
                    'type': 'collaboration_state',
                    'state': state
                },
                metadata={}
            )
            
            await self.websocket_manager.send_to_user(user_id, message)
            
        except Exception as e:
            logger.error(f"Failed to send session state: {str(e)}")
    
    async def _calculate_insight_relevance(self, project_id: str, content: str,
                                         context: Dict[str, Any]) -> float:
        """Calculate relevance score for a shared insight"""
        try:
            # Use knowledge synthesis to determine relevance
            relevance_factors = await self.knowledge_synthesis.analyze_content_relevance(
                project_id, content, context
            )
            
            # Simple relevance calculation (can be enhanced)
            base_score = 0.5
            
            if relevance_factors.get('has_code_references'):
                base_score += 0.2
            
            if relevance_factors.get('mentions_key_concepts'):
                base_score += 0.2
            
            if relevance_factors.get('relates_to_recent_activity'):
                base_score += 0.1
            
            return min(base_score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate insight relevance: {str(e)}")
            return 0.5  # Default relevance
