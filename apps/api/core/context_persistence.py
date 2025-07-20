"""
Context Persistence Service for NeuroSync
Maintains project memory across sessions, conversation history, and contextual insights
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .vector_db import VectorDatabase
from .knowledge_graph import KnowledgeGraphBuilder
from .data_importance_filter import DataImportanceFilter

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """Types of context that can be persisted"""
    CONVERSATION = "conversation"
    DECISION = "decision"
    INSIGHT = "insight"
    QUERY_PATTERN = "query_pattern"
    USER_PREFERENCE = "user_preference"
    PROJECT_STATE = "project_state"
    CODE_UNDERSTANDING = "code_understanding"
    MEETING_OUTCOME = "meeting_outcome"

class ContextScope(Enum):
    """Scope of context persistence"""
    SESSION = "session"          # Current session only
    PROJECT = "project"          # Project-wide context
    USER = "user"               # User-specific context
    GLOBAL = "global"           # Cross-project insights

@dataclass
class ContextEntry:
    """Individual context entry with metadata"""
    id: str
    project_id: str
    user_id: str
    context_type: ContextType
    scope: ContextScope
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    importance_score: float
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None

@dataclass
class ConversationContext:
    """Conversation-specific context"""
    conversation_id: str
    messages: List[Dict[str, Any]]
    topics: List[str]
    entities_mentioned: List[str]
    decisions_made: List[str]
    follow_up_items: List[str]
    sentiment: str
    summary: str

@dataclass
class ProjectMemory:
    """Project-wide memory state"""
    project_id: str
    key_decisions: List[Dict[str, Any]]
    active_topics: List[str]
    team_preferences: Dict[str, Any]
    code_patterns: List[Dict[str, Any]]
    common_queries: List[Dict[str, Any]]
    project_insights: List[Dict[str, Any]]
    last_updated: datetime

class ContextPersistenceService:
    """
    Production-ready context persistence service for NeuroSync
    
    Features:
    - Multi-scope context management (session, project, user, global)
    - Conversation history and continuity
    - Decision tracking and recall
    - Pattern recognition and learning
    - Contextual insights generation
    - Memory optimization and cleanup
    """
    
    def __init__(self):
        self.vector_db = VectorDatabase()
        self.knowledge_graph = KnowledgeGraphBuilder()
        self.importance_filter = DataImportanceFilter()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # In-memory context cache for fast access
        self.context_cache: Dict[str, ContextEntry] = {}
        self.conversation_cache: Dict[str, ConversationContext] = {}
        self.project_memory_cache: Dict[str, ProjectMemory] = {}
        
        # Configuration
        self.max_cache_size = 1000
        self.default_context_ttl = timedelta(days=30)
        self.session_context_ttl = timedelta(hours=24)
        self.conversation_context_ttl = timedelta(days=7)
        
        # Context importance thresholds
        self.min_importance_for_persistence = 0.3
        self.min_importance_for_long_term = 0.6
    
    async def store_context(self, project_id: str, user_id: str, 
                           context_type: ContextType, scope: ContextScope,
                           content: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None,
                           ttl: Optional[timedelta] = None) -> str:
        """
        Store context with automatic importance scoring and persistence
        
        Args:
            project_id: Project identifier
            user_id: User identifier
            context_type: Type of context being stored
            scope: Scope of context persistence
            content: Context content
            metadata: Additional metadata
            ttl: Time to live for context
            
        Returns:
            Context entry ID
        """
        try:
            # Score context importance
            importance_score = await self._score_context_importance(
                content, context_type, project_id, metadata or {}
            )
            
            # Skip if importance is too low
            if importance_score < self.min_importance_for_persistence:
                logger.debug(f"Skipping context storage - low importance: {importance_score}")
                return ""
            
            # Create context entry
            context_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Determine TTL based on scope and importance
            if ttl is None:
                if scope == ContextScope.SESSION:
                    ttl = self.session_context_ttl
                elif scope == ContextScope.PROJECT and importance_score >= self.min_importance_for_long_term:
                    ttl = None  # No expiration for important project context
                else:
                    ttl = self.default_context_ttl
            
            expires_at = now + ttl if ttl else None
            
            context_entry = ContextEntry(
                id=context_id,
                project_id=project_id,
                user_id=user_id,
                context_type=context_type,
                scope=scope,
                content=content,
                metadata=metadata or {},
                importance_score=importance_score,
                created_at=now,
                updated_at=now,
                expires_at=expires_at
            )
            
            # Store in cache
            self.context_cache[context_id] = context_entry
            
            # Store in vector database for semantic search
            await self._store_context_in_vector_db(context_entry)
            
            # Store in knowledge graph for relationship mapping
            await self._store_context_in_knowledge_graph(context_entry)
            
            # Update project memory if applicable
            if scope in [ContextScope.PROJECT, ContextScope.GLOBAL]:
                await self._update_project_memory(project_id, context_entry)
            
            logger.info(f"Stored context {context_id} with importance {importance_score}")
            return context_id
            
        except Exception as e:
            logger.error(f"Failed to store context: {str(e)}")
            raise
    
    async def retrieve_context(self, project_id: str, user_id: str,
                              context_types: Optional[List[ContextType]] = None,
                              scopes: Optional[List[ContextScope]] = None,
                              query: Optional[str] = None,
                              limit: int = 10) -> List[ContextEntry]:
        """
        Retrieve relevant context based on filters and semantic search
        
        Args:
            project_id: Project identifier
            user_id: User identifier
            context_types: Filter by context types
            scopes: Filter by context scopes
            query: Semantic search query
            limit: Maximum number of results
            
        Returns:
            List of relevant context entries
        """
        try:
            relevant_contexts = []
            
            # Filter cached contexts
            for context in self.context_cache.values():
                # Check expiration
                if context.expires_at and context.expires_at < datetime.utcnow():
                    continue
                
                # Check project and user access
                if context.project_id != project_id:
                    if context.scope not in [ContextScope.GLOBAL, ContextScope.USER]:
                        continue
                
                if context.scope == ContextScope.USER and context.user_id != user_id:
                    continue
                
                # Apply filters
                if context_types and context.context_type not in context_types:
                    continue
                
                if scopes and context.scope not in scopes:
                    continue
                
                relevant_contexts.append(context)
            
            # Semantic search if query provided
            if query:
                semantic_results = await self._semantic_context_search(
                    project_id, query, context_types, scopes, limit * 2
                )
                
                # Merge with filtered results
                semantic_ids = {ctx.id for ctx in semantic_results}
                for ctx in relevant_contexts:
                    if ctx.id not in semantic_ids:
                        semantic_results.append(ctx)
                
                relevant_contexts = semantic_results
            
            # Sort by importance and recency
            relevant_contexts.sort(
                key=lambda x: (x.importance_score, x.updated_at),
                reverse=True
            )
            
            # Update access tracking
            for context in relevant_contexts[:limit]:
                context.access_count += 1
                context.last_accessed = datetime.utcnow()
            
            logger.info(f"Retrieved {len(relevant_contexts[:limit])} context entries")
            return relevant_contexts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {str(e)}")
            return []
    
    async def store_conversation_context(self, project_id: str, user_id: str,
                                       conversation_id: str, messages: List[Dict[str, Any]],
                                       summary: Optional[str] = None) -> str:
        """
        Store conversation context with automatic analysis
        
        Args:
            project_id: Project identifier
            user_id: User identifier
            conversation_id: Conversation identifier
            messages: List of conversation messages
            summary: Optional conversation summary
            
        Returns:
            Context entry ID
        """
        try:
            # Analyze conversation
            analysis = await self._analyze_conversation(messages, project_id)
            
            # Create conversation context
            conversation_context = ConversationContext(
                conversation_id=conversation_id,
                messages=messages,
                topics=analysis['topics'],
                entities_mentioned=analysis['entities'],
                decisions_made=analysis['decisions'],
                follow_up_items=analysis['follow_ups'],
                sentiment=analysis['sentiment'],
                summary=summary or analysis['summary']
            )
            
            # Cache conversation
            self.conversation_cache[conversation_id] = conversation_context
            
            # Store as context
            context_id = await self.store_context(
                project_id=project_id,
                user_id=user_id,
                context_type=ContextType.CONVERSATION,
                scope=ContextScope.PROJECT,
                content=asdict(conversation_context),
                metadata={
                    'conversation_id': conversation_id,
                    'message_count': len(messages),
                    'topics': analysis['topics'],
                    'entities': analysis['entities']
                },
                ttl=self.conversation_context_ttl
            )
            
            logger.info(f"Stored conversation context {conversation_id}")
            return context_id
            
        except Exception as e:
            logger.error(f"Failed to store conversation context: {str(e)}")
            raise
    
    async def get_project_memory(self, project_id: str) -> ProjectMemory:
        """
        Get comprehensive project memory state
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project memory state
        """
        try:
            # Check cache first
            if project_id in self.project_memory_cache:
                memory = self.project_memory_cache[project_id]
                # Refresh if older than 1 hour
                if (datetime.utcnow() - memory.last_updated).total_seconds() < 3600:
                    return memory
            
            # Build project memory from contexts
            project_contexts = await self.retrieve_context(
                project_id=project_id,
                user_id="",  # Get all users' contexts
                scopes=[ContextScope.PROJECT, ContextScope.GLOBAL],
                limit=100
            )
            
            # Extract key information
            key_decisions = []
            active_topics = []
            team_preferences = {}
            code_patterns = []
            common_queries = []
            project_insights = []
            
            for context in project_contexts:
                if context.context_type == ContextType.DECISION:
                    key_decisions.append(context.content)
                elif context.context_type == ContextType.QUERY_PATTERN:
                    common_queries.append(context.content)
                elif context.context_type == ContextType.CODE_UNDERSTANDING:
                    code_patterns.append(context.content)
                elif context.context_type == ContextType.INSIGHT:
                    project_insights.append(context.content)
                elif context.context_type == ContextType.USER_PREFERENCE:
                    team_preferences.update(context.content)
                
                # Extract topics from metadata
                if 'topics' in context.metadata:
                    active_topics.extend(context.metadata['topics'])
            
            # Remove duplicates and sort by relevance
            active_topics = list(set(active_topics))
            
            project_memory = ProjectMemory(
                project_id=project_id,
                key_decisions=key_decisions,
                active_topics=active_topics,
                team_preferences=team_preferences,
                code_patterns=code_patterns,
                common_queries=common_queries,
                project_insights=project_insights,
                last_updated=datetime.utcnow()
            )
            
            # Cache the memory
            self.project_memory_cache[project_id] = project_memory
            
            logger.info(f"Built project memory for {project_id}")
            return project_memory
            
        except Exception as e:
            logger.error(f"Failed to get project memory: {str(e)}")
            raise
    
    async def cleanup_expired_context(self) -> Dict[str, int]:
        """
        Clean up expired context entries
        
        Returns:
            Cleanup statistics
        """
        try:
            now = datetime.utcnow()
            expired_count = 0
            low_importance_count = 0
            
            # Clean up cache
            expired_ids = []
            for context_id, context in self.context_cache.items():
                if context.expires_at and context.expires_at < now:
                    expired_ids.append(context_id)
                    expired_count += 1
                elif (context.importance_score < self.min_importance_for_persistence and 
                      context.access_count == 0 and
                      (now - context.created_at).days > 7):
                    expired_ids.append(context_id)
                    low_importance_count += 1
            
            for context_id in expired_ids:
                del self.context_cache[context_id]
            
            # Clean up conversation cache
            expired_conversations = []
            for conv_id, conv in self.conversation_cache.items():
                # Remove conversations older than TTL with no recent access
                if (now - datetime.fromisoformat(conv.messages[-1]['timestamp'])) > self.conversation_context_ttl:
                    expired_conversations.append(conv_id)
            
            for conv_id in expired_conversations:
                del self.conversation_cache[conv_id]
            
            # Clean up project memory cache (keep recent)
            expired_projects = []
            for project_id, memory in self.project_memory_cache.items():
                if (now - memory.last_updated).days > 1:
                    expired_projects.append(project_id)
            
            for project_id in expired_projects:
                del self.project_memory_cache[project_id]
            
            cleanup_stats = {
                'expired_contexts': expired_count,
                'low_importance_contexts': low_importance_count,
                'expired_conversations': len(expired_conversations),
                'expired_project_memories': len(expired_projects)
            }
            
            logger.info(f"Context cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Context cleanup failed: {str(e)}")
            return {}
    
    async def _score_context_importance(self, content: Dict[str, Any], 
                                       context_type: ContextType, project_id: str,
                                       metadata: Dict[str, Any]) -> float:
        """Score the importance of context for persistence decisions"""
        try:
            # Base importance by context type
            type_importance = {
                ContextType.DECISION: 0.9,
                ContextType.INSIGHT: 0.8,
                ContextType.CODE_UNDERSTANDING: 0.7,
                ContextType.MEETING_OUTCOME: 0.7,
                ContextType.CONVERSATION: 0.5,
                ContextType.QUERY_PATTERN: 0.4,
                ContextType.USER_PREFERENCE: 0.6,
                ContextType.PROJECT_STATE: 0.8
            }.get(context_type, 0.3)
            
            # Content-based scoring
            content_text = json.dumps(content, default=str)
            content_score = await self.importance_filter.score_data_importance(
                content=content_text,
                data_type="CONTEXT",
                project_id=project_id,
                metadata=metadata
            )
            
            # Combine scores
            final_score = (type_importance * 0.6) + (content_score.score * 0.4)
            
            return min(1.0, max(0.0, final_score))
            
        except Exception as e:
            logger.error(f"Failed to score context importance: {str(e)}")
            return 0.5  # Default moderate importance
    
    async def _store_context_in_vector_db(self, context: ContextEntry):
        """Store context in vector database for semantic search"""
        try:
            content_text = json.dumps(context.content, default=str)
            
            document = {
                'id': f"context_{context.id}",
                'content': content_text,
                'metadata': {
                    'source': 'context_persistence',
                    'type': context.context_type.value,
                    'scope': context.scope.value,
                    'project_id': context.project_id,
                    'user_id': context.user_id,
                    'importance_score': context.importance_score,
                    'created_at': context.created_at.isoformat(),
                    **context.metadata
                }
            }
            
            await self.vector_db.add_documents([document])
            
        except Exception as e:
            logger.error(f"Failed to store context in vector DB: {str(e)}")
    
    async def _store_context_in_knowledge_graph(self, context: ContextEntry):
        """Store context relationships in knowledge graph"""
        try:
            # Create context entity
            await self.knowledge_graph.add_entity(
                project_id=context.project_id,
                entity_type="context",
                entity_id=context.id,
                properties={
                    'type': context.context_type.value,
                    'scope': context.scope.value,
                    'importance_score': context.importance_score,
                    'created_at': context.created_at.isoformat(),
                    **context.metadata
                }
            )
            
            # Create user relationship
            await self.knowledge_graph.add_relationship(
                project_id=context.project_id,
                source_type="person",
                source_id=context.user_id,
                target_type="context",
                target_id=context.id,
                relationship_type="CREATED",
                strength=0.8,
                metadata={'created_at': context.created_at.isoformat()}
            )
            
        except Exception as e:
            logger.error(f"Failed to store context in knowledge graph: {str(e)}")
    
    async def _update_project_memory(self, project_id: str, context: ContextEntry):
        """Update project memory with new context"""
        try:
            # Invalidate cached project memory to force refresh
            if project_id in self.project_memory_cache:
                del self.project_memory_cache[project_id]
            
        except Exception as e:
            logger.error(f"Failed to update project memory: {str(e)}")
    
    async def _semantic_context_search(self, project_id: str, query: str,
                                     context_types: Optional[List[ContextType]],
                                     scopes: Optional[List[ContextScope]],
                                     limit: int) -> List[ContextEntry]:
        """Perform semantic search on stored contexts"""
        try:
            # Build search filters
            filters = {'project_id': project_id}
            
            if context_types:
                filters['type'] = [ct.value for ct in context_types]
            
            if scopes:
                filters['scope'] = [s.value for s in scopes]
            
            # Search vector database
            results = await self.vector_db.semantic_search(
                query=query,
                project_id=project_id,
                source_types=['context_persistence'],
                limit=limit,
                filters=filters
            )
            
            # Convert back to context entries
            contexts = []
            for result in results:
                context_id = result['id'].replace('context_', '')
                if context_id in self.context_cache:
                    contexts.append(self.context_cache[context_id])
            
            return contexts
            
        except Exception as e:
            logger.error(f"Semantic context search failed: {str(e)}")
            return []
    
    async def _analyze_conversation(self, messages: List[Dict[str, Any]], 
                                  project_id: str) -> Dict[str, Any]:
        """Analyze conversation to extract topics, entities, and insights"""
        try:
            # Simple analysis (can be enhanced with NLP)
            all_text = " ".join([msg.get('content', '') for msg in messages])
            
            # Extract basic information
            topics = []
            entities = []
            decisions = []
            follow_ups = []
            
            # Simple keyword extraction (enhance with proper NLP)
            words = all_text.lower().split()
            
            # Common technical topics
            tech_keywords = ['api', 'database', 'frontend', 'backend', 'bug', 'feature', 'deployment']
            topics = [word for word in tech_keywords if word in words]
            
            # Look for decision indicators
            decision_indicators = ['decided', 'agreed', 'will do', 'action item']
            for indicator in decision_indicators:
                if indicator in all_text.lower():
                    decisions.append(f"Decision made regarding {indicator}")
            
            # Look for follow-up indicators
            followup_indicators = ['todo', 'follow up', 'next steps', 'action items']
            for indicator in followup_indicators:
                if indicator in all_text.lower():
                    follow_ups.append(f"Follow up on {indicator}")
            
            return {
                'topics': topics,
                'entities': entities,
                'decisions': decisions,
                'follow_ups': follow_ups,
                'sentiment': 'neutral',  # Can be enhanced with sentiment analysis
                'summary': all_text[:200] + "..." if len(all_text) > 200 else all_text
            }
            
        except Exception as e:
            logger.error(f"Conversation analysis failed: {str(e)}")
            return {
                'topics': [],
                'entities': [],
                'decisions': [],
                'follow_ups': [],
                'sentiment': 'neutral',
                'summary': ''
            }
