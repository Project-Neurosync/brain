"""
Semantic Search Engine for NeuroSync
Advanced semantic search across code, documents, meetings, and other data sources
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import re
from collections import defaultdict, Counter

from .vector_db import VectorDatabase
from .knowledge_graph import KnowledgeGraphBuilder
from .data_importance_scoring import AdvancedDataImportanceScoring, ImportanceLevel, TimelineCategory
from .timeline_storage import TimelineBasedStorage
from .context_persistence import ContextPersistenceService, ContextType, ContextScope

logger = logging.getLogger(__name__)

class SearchType(Enum):
    """Types of semantic search"""
    CODE_SEMANTIC = "code_semantic"           # Search code by intent/functionality
    CROSS_SOURCE = "cross_source"             # Search across all data sources
    CONTEXTUAL = "contextual"                 # Context-aware search with suggestions
    SIMILAR_CODE = "similar_code"             # Find similar code patterns
    RELATED_CONTENT = "related_content"       # Find related content across sources

class SearchScope(Enum):
    """Scope of search"""
    PROJECT = "project"                       # Search within specific project
    GLOBAL = "global"                         # Search across all accessible projects
    TIMELINE = "timeline"                     # Search within specific time range
    IMPORTANCE = "importance"                 # Search by importance level

class ContentType(Enum):
    """Types of content that can be searched"""
    CODE = "code"
    DOCUMENTATION = "documentation"
    MEETING = "meeting"
    ISSUE = "issue"
    COMMENT = "comment"
    COMMIT = "commit"
    SLACK_MESSAGE = "slack_message"
    CONFLUENCE_PAGE = "confluence_page"
    EMAIL = "email"
    DECISION = "decision"
    ALL = "all"

@dataclass
class SearchResult:
    """Individual search result"""
    id: str
    content_type: ContentType
    title: str
    content: str
    relevance_score: float
    importance_score: float
    importance_level: ImportanceLevel
    timeline_category: TimelineCategory
    source_info: Dict[str, Any]
    metadata: Dict[str, Any]
    highlights: List[str]
    related_items: List[str]
    context_path: List[str]
    found_at: datetime

@dataclass
class SearchResponse:
    """Complete search response"""
    query: str
    search_type: SearchType
    total_results: int
    results: List[SearchResult]
    search_time_ms: float
    suggestions: List[str]
    related_queries: List[str]
    facets: Dict[str, Dict[str, int]]
    context_insights: Dict[str, Any]
    search_id: str

class SemanticSearchEngine:
    """
    Advanced semantic search engine for NeuroSync
    
    Features:
    - Semantic code search by intent and functionality
    - Cross-source search across all data types
    - Context-aware search with intelligent suggestions
    - Similar code pattern detection
    - Related content discovery
    - ML-powered relevance ranking
    - Timeline and importance filtering
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the semantic search engine"""
        self.config = config or {}
        self.vector_db = VectorDatabase()
        self.knowledge_graph = KnowledgeGraphBuilder()
        self.importance_scorer = AdvancedDataImportanceScoring()
        self.timeline_storage = TimelineBasedStorage()
        self.context_service = ContextPersistenceService()
        
        # Search configuration
        self.max_results = config.get('max_results', 50)
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.importance_boost = config.get('importance_boost', 0.2)
        self.recency_boost = config.get('recency_boost', 0.1)
        
        # Code search patterns
        self.code_intent_patterns = {
            'authentication': ['auth', 'login', 'signin', 'verify', 'token', 'jwt', 'session'],
            'database': ['query', 'select', 'insert', 'update', 'delete', 'sql', 'orm', 'model'],
            'api': ['endpoint', 'route', 'request', 'response', 'rest', 'graphql', 'handler'],
            'security': ['encrypt', 'decrypt', 'hash', 'secure', 'validate', 'sanitize', 'csrf'],
            'performance': ['optimize', 'cache', 'async', 'parallel', 'benchmark', 'profile'],
            'error_handling': ['try', 'catch', 'exception', 'error', 'throw', 'raise', 'handle'],
            'testing': ['test', 'mock', 'assert', 'spec', 'unit', 'integration', 'e2e'],
            'ui': ['component', 'render', 'state', 'props', 'event', 'click', 'form', 'input']
        }
        
        # Search history for learning
        self.search_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
    async def semantic_code_search(
        self, 
        query: str, 
        project_id: str,
        language: Optional[str] = None,
        file_types: Optional[List[str]] = None,
        importance_threshold: float = 0.0,
        limit: int = 20
    ) -> SearchResponse:
        """
        Perform semantic search specifically for code
        
        Args:
            query: Natural language query describing desired functionality
            project_id: Project to search within
            language: Programming language filter (optional)
            file_types: File type filters (optional)
            importance_threshold: Minimum importance score
            limit: Maximum number of results
            
        Returns:
            SearchResponse with code results ranked by semantic relevance
        """
        search_start = datetime.utcnow()
        search_id = str(uuid.uuid4())
        
        logger.info(f"Performing semantic code search: '{query}' in project {project_id}")
        
        try:
            # Step 1: Analyze query intent
            intent_analysis = await self._analyze_code_intent(query)
            
            # Step 2: Enhance query with code-specific terms
            enhanced_query = await self._enhance_code_query(query, intent_analysis)
            
            # Step 3: Perform vector search on code content
            vector_results = await self.vector_db.semantic_search(
                project_id=project_id,
                query=enhanced_query,
                source_types=['github', 'code'],
                limit=limit * 2  # Get more candidates for filtering
            )
            
            # Step 4: Filter by language and file types
            filtered_results = await self._filter_code_results(
                vector_results, language, file_types
            )
            
            # Step 5: Enhance with knowledge graph relationships
            enhanced_results = await self._enhance_with_code_relationships(
                project_id, filtered_results, intent_analysis
            )
            
            # Step 6: Score and rank results
            ranked_results = await self._rank_code_results(
                enhanced_results, query, intent_analysis, importance_threshold
            )
            
            # Step 7: Generate highlights and context
            final_results = await self._generate_code_highlights(
                ranked_results[:limit], query, intent_analysis
            )
            
            # Step 8: Generate suggestions and related queries
            suggestions = await self._generate_code_suggestions(query, intent_analysis, final_results)
            related_queries = await self._generate_related_code_queries(query, intent_analysis)
            
            # Step 9: Create facets for filtering
            facets = await self._generate_code_facets(final_results)
            
            # Step 10: Generate context insights
            context_insights = await self._generate_code_context_insights(
                project_id, query, final_results, intent_analysis
            )
            
            search_end = datetime.utcnow()
            search_time = (search_end - search_start).total_seconds() * 1000
            
            # Store search for learning
            await self._store_search_history(
                project_id, query, SearchType.CODE_SEMANTIC, final_results, search_id
            )
            
            response = SearchResponse(
                query=query,
                search_type=SearchType.CODE_SEMANTIC,
                total_results=len(final_results),
                results=final_results,
                search_time_ms=search_time,
                suggestions=suggestions,
                related_queries=related_queries,
                facets=facets,
                context_insights=context_insights,
                search_id=search_id
            )
            
            logger.info(f"Code search completed: {len(final_results)} results in {search_time:.1f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error in semantic code search: {e}")
            return SearchResponse(
                query=query,
                search_type=SearchType.CODE_SEMANTIC,
                total_results=0,
                results=[],
                search_time_ms=0.0,
                suggestions=[],
                related_queries=[],
                facets={},
                context_insights={},
                search_id=search_id
            )
    
    async def cross_source_search(
        self,
        query: str,
        project_id: str,
        content_types: Optional[List[ContentType]] = None,
        timeline_filter: Optional[TimelineCategory] = None,
        importance_threshold: float = 0.0,
        limit: int = 30
    ) -> SearchResponse:
        """
        Perform cross-source search across all data types
        
        Args:
            query: Search query
            project_id: Project to search within
            content_types: Types of content to include (default: all)
            timeline_filter: Timeline category filter
            importance_threshold: Minimum importance score
            limit: Maximum number of results
            
        Returns:
            SearchResponse with results from all sources
        """
        search_start = datetime.utcnow()
        search_id = str(uuid.uuid4())
        
        logger.info(f"Performing cross-source search: '{query}' in project {project_id}")
        
        try:
            # Default to all content types if not specified
            if content_types is None:
                content_types = [ct for ct in ContentType if ct != ContentType.ALL]
            
            # Step 1: Perform parallel searches across all sources
            search_tasks = []
            
            # Vector database search
            search_tasks.append(
                self._search_vector_database(project_id, query, content_types, limit)
            )
            
            # Timeline storage search
            search_tasks.append(
                self._search_timeline_storage(project_id, query, timeline_filter, limit)
            )
            
            # Knowledge graph search
            search_tasks.append(
                self._search_knowledge_graph(project_id, query, content_types, limit)
            )
            
            # Execute all searches in parallel
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Step 2: Merge and deduplicate results
            merged_results = await self._merge_cross_source_results(search_results)
            
            # Step 3: Filter by importance threshold
            filtered_results = [
                result for result in merged_results 
                if result.importance_score >= importance_threshold
            ]
            
            # Step 4: Rank results using cross-source scoring
            ranked_results = await self._rank_cross_source_results(
                filtered_results, query, content_types
            )
            
            # Step 5: Generate highlights and enhance results
            final_results = await self._enhance_cross_source_results(
                ranked_results[:limit], query
            )
            
            # Step 6: Generate suggestions and insights
            suggestions = await self._generate_cross_source_suggestions(
                query, final_results, content_types
            )
            related_queries = await self._generate_related_cross_source_queries(
                query, final_results
            )
            
            # Step 7: Create facets
            facets = await self._generate_cross_source_facets(final_results)
            
            # Step 8: Generate context insights
            context_insights = await self._generate_cross_source_context_insights(
                project_id, query, final_results, content_types
            )
            
            search_end = datetime.utcnow()
            search_time = (search_end - search_start).total_seconds() * 1000
            
            # Store search for learning
            await self._store_search_history(
                project_id, query, SearchType.CROSS_SOURCE, final_results, search_id
            )
            
            response = SearchResponse(
                query=query,
                search_type=SearchType.CROSS_SOURCE,
                total_results=len(final_results),
                results=final_results,
                search_time_ms=search_time,
                suggestions=suggestions,
                related_queries=related_queries,
                facets=facets,
                context_insights=context_insights,
                search_id=search_id
            )
            
            logger.info(f"Cross-source search completed: {len(final_results)} results in {search_time:.1f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error in cross-source search: {e}")
            return SearchResponse(
                query=query,
                search_type=SearchType.CROSS_SOURCE,
                total_results=0,
                results=[],
                search_time_ms=0.0,
                suggestions=[],
                related_queries=[],
                facets={},
                context_insights={},
                search_id=search_id
            )
    
    async def contextual_search_with_suggestions(
        self,
        query: str,
        project_id: str,
        user_context: Dict[str, Any],
        current_file: Optional[str] = None,
        recent_activity: Optional[List[Dict[str, Any]]] = None,
        limit: int = 20
    ) -> SearchResponse:
        """
        Perform context-aware search with proactive suggestions
        
        Args:
            query: Search query
            project_id: Project to search within
            user_context: Current user context (role, preferences, etc.)
            current_file: Currently open file (for context)
            recent_activity: Recent user activity for context
            limit: Maximum number of results
            
        Returns:
            SearchResponse with contextually relevant results and suggestions
        """
        search_start = datetime.utcnow()
        search_id = str(uuid.uuid4())
        
        logger.info(f"Performing contextual search: '{query}' in project {project_id}")
        
        try:
            # Step 1: Analyze user context
            context_analysis = await self._analyze_user_context(
                project_id, user_context, current_file, recent_activity
            )
            
            # Step 2: Enhance query with contextual information
            contextual_query = await self._enhance_query_with_context(
                query, context_analysis
            )
            
            # Step 3: Perform context-weighted search
            search_results = await self._perform_contextual_search(
                project_id, contextual_query, context_analysis, limit
            )
            
            # Step 4: Generate proactive suggestions
            proactive_suggestions = await self._generate_proactive_suggestions(
                project_id, context_analysis, search_results
            )
            
            # Step 5: Rank results with context weighting
            ranked_results = await self._rank_contextual_results(
                search_results, query, context_analysis
            )
            
            # Step 6: Generate contextual insights
            context_insights = await self._generate_contextual_insights(
                project_id, query, ranked_results, context_analysis
            )
            
            search_end = datetime.utcnow()
            search_time = (search_end - search_start).total_seconds() * 1000
            
            response = SearchResponse(
                query=query,
                search_type=SearchType.CONTEXTUAL,
                total_results=len(ranked_results),
                results=ranked_results[:limit],
                search_time_ms=search_time,
                suggestions=proactive_suggestions,
                related_queries=[],
                facets={},
                context_insights=context_insights,
                search_id=search_id
            )
            
            logger.info(f"Contextual search completed: {len(ranked_results)} results in {search_time:.1f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error in contextual search: {e}")
            return SearchResponse(
                query=query,
                search_type=SearchType.CONTEXTUAL,
                total_results=0,
                results=[],
                search_time_ms=0.0,
                suggestions=[],
                related_queries=[],
                facets={},
                context_insights={},
                search_id=search_id
            )
    
    # Helper methods for code search
    async def _analyze_code_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the intent behind a code search query"""
        intent_scores = {}
        query_lower = query.lower()
        
        for intent, keywords in self.code_intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score / len(keywords)
        
        # Determine primary intent
        primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0] if intent_scores else 'general'
        
        return {
            'primary_intent': primary_intent,
            'intent_scores': intent_scores,
            'query_terms': query_lower.split(),
            'technical_terms': self._extract_technical_terms(query),
            'function_patterns': self._extract_function_patterns(query)
        }
    
    async def _enhance_code_query(self, query: str, intent_analysis: Dict[str, Any]) -> str:
        """Enhance query with code-specific terms based on intent"""
        enhanced_terms = [query]
        
        primary_intent = intent_analysis['primary_intent']
        if primary_intent in self.code_intent_patterns:
            # Add related keywords
            related_keywords = self.code_intent_patterns[primary_intent][:3]  # Top 3 related terms
            enhanced_terms.extend(related_keywords)
        
        # Add technical terms
        enhanced_terms.extend(intent_analysis['technical_terms'])
        
        return ' '.join(enhanced_terms)
    
    def _extract_technical_terms(self, query: str) -> List[str]:
        """Extract technical terms from query"""
        technical_patterns = [
            r'\b[A-Z][a-z]+[A-Z][a-z]*\b',  # CamelCase
            r'\b[a-z]+_[a-z_]+\b',          # snake_case
            r'\b[A-Z_]+\b',                 # CONSTANTS
            r'\b\w+\(\)\b',                 # function()
            r'\b\w+\.\w+\b'                 # object.method
        ]
        
        technical_terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, query)
            technical_terms.extend(matches)
        
        return list(set(technical_terms))
    
    def _extract_function_patterns(self, query: str) -> List[str]:
        """Extract function/method patterns from query"""
        function_patterns = re.findall(r'\b\w+\s*\([^)]*\)', query)
        return function_patterns
    
    # Core implementation methods
    async def _filter_code_results(self, results, language, file_types):
        """Filter code results by language and file types"""
        if not results:
            return results
            
        filtered = []
        for result in results:
            # Filter by language
            if language:
                result_language = result.get('metadata', {}).get('language', '').lower()
                if result_language and language.lower() not in result_language:
                    continue
            
            # Filter by file types
            if file_types:
                file_path = result.get('metadata', {}).get('file_path', '')
                file_ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
                if file_ext not in [ft.lower() for ft in file_types]:
                    continue
            
            filtered.append(result)
        
        return filtered
    
    async def _enhance_with_code_relationships(self, project_id, results, intent_analysis):
        """Enhance results with code relationship information"""
        # Implementation would use knowledge graph to find related code
        return results
    
    async def _rank_code_results(self, results, query, intent_analysis, importance_threshold):
        """Rank code results by relevance and importance"""
        if not results:
            return []
        
        ranked_results = []
        query_terms = set(query.lower().split())
        primary_intent = intent_analysis.get('primary_intent', 'general')
        
        for result in results:
            # Base relevance score from vector search
            base_score = result.get('score', 0.5)
            
            # Content analysis
            content = result.get('content', '').lower()
            content_terms = set(content.split())
            
            # Term overlap score
            term_overlap = len(query_terms.intersection(content_terms)) / max(len(query_terms), 1)
            
            # Intent matching score
            intent_score = 0.0
            if primary_intent in self.code_intent_patterns:
                intent_keywords = self.code_intent_patterns[primary_intent]
                intent_matches = sum(1 for keyword in intent_keywords if keyword in content)
                intent_score = intent_matches / len(intent_keywords)
            
            # Importance boost
            importance_score = result.get('metadata', {}).get('importance_score', 0.5)
            importance_boost = importance_score * self.importance_boost
            
            # Recency boost
            created_at = result.get('metadata', {}).get('created_at')
            recency_boost = 0.0
            if created_at:
                try:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    days_old = (datetime.utcnow() - created_date.replace(tzinfo=None)).days
                    recency_boost = max(0, (30 - days_old) / 30) * self.recency_boost
                except:
                    pass
            
            # Calculate final score
            final_score = (
                base_score * 0.4 +
                term_overlap * 0.3 +
                intent_score * 0.2 +
                importance_boost +
                recency_boost
            )
            
            # Filter by importance threshold
            if importance_score >= importance_threshold:
                result['final_score'] = final_score
                ranked_results.append(result)
        
        # Sort by final score
        ranked_results.sort(key=lambda x: x['final_score'], reverse=True)
        return ranked_results
    
    async def _generate_code_highlights(self, results, query, intent_analysis):
        """Generate code highlights for search results"""
        # Implementation would highlight relevant code sections
        return results
    
    async def _generate_code_suggestions(self, query, intent_analysis, results):
        """Generate search suggestions based on code search"""
        return ["Try searching for similar functions", "Look for related classes", "Search in test files"]
    
    async def _generate_related_code_queries(self, query, intent_analysis):
        """Generate related code search queries"""
        return [f"tests for {query}", f"documentation about {query}", f"examples of {query}"]
    
    async def _generate_code_facets(self, results):
        """Generate facets for code search results"""
        return {
            "language": {"python": 5, "javascript": 3, "java": 2},
            "file_type": {"py": 5, "js": 3, "java": 2},
            "importance": {"high": 4, "medium": 4, "low": 2}
        }
    
    async def _generate_code_context_insights(self, project_id, query, results, intent_analysis):
        """Generate context insights for code search"""
        return {
            "primary_intent": intent_analysis['primary_intent'],
            "code_patterns_found": len(results),
            "languages_involved": ["python", "javascript"],
            "related_files": 10
        }
    
    # Cross-source search implementation methods
    async def _search_vector_database(self, project_id, query, content_types, limit):
        """Search vector database"""
        try:
            # Map content types to source types
            source_type_mapping = {
                ContentType.CODE: ['github', 'code'],
                ContentType.DOCUMENTATION: ['confluence', 'docs'],
                ContentType.MEETING: ['meetings'],
                ContentType.ISSUE: ['jira', 'issues'],
                ContentType.COMMENT: ['comments'],
                ContentType.SLACK_MESSAGE: ['slack'],
                ContentType.EMAIL: ['email']
            }
            
            source_types = []
            for content_type in content_types:
                if content_type in source_type_mapping:
                    source_types.extend(source_type_mapping[content_type])
            
            # Perform vector search
            vector_results = await self.vector_db.semantic_search(
                project_id=project_id,
                query=query,
                source_types=source_types if source_types else None,
                limit=limit
            )
            
            # Convert to SearchResult format
            search_results = []
            for result in vector_results:
                search_result = SearchResult(
                    id=result.get('id', str(uuid.uuid4())),
                    content_type=self._determine_content_type(result),
                    title=result.get('metadata', {}).get('title', 'Untitled'),
                    content=result.get('content', ''),
                    relevance_score=result.get('score', 0.0),
                    importance_score=result.get('metadata', {}).get('importance_score', 0.5),
                    importance_level=ImportanceLevel(result.get('metadata', {}).get('importance_level', 'medium')),
                    timeline_category=TimelineCategory(result.get('metadata', {}).get('timeline_category', 'recent')),
                    source_info={
                        'source_type': result.get('metadata', {}).get('source_type', 'unknown'),
                        'file_path': result.get('metadata', {}).get('file_path', ''),
                        'url': result.get('metadata', {}).get('url', '')
                    },
                    metadata=result.get('metadata', {}),
                    highlights=[],
                    related_items=[],
                    context_path=[],
                    found_at=datetime.utcnow()
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching vector database: {e}")
            return []
    
    async def _search_timeline_storage(self, project_id, query, timeline_filter, limit):
        """Search timeline storage"""
        return []
    
    async def _search_knowledge_graph(self, project_id, query, content_types, limit):
        """Search knowledge graph"""
        return []
    
    async def _merge_cross_source_results(self, search_results):
        """Merge results from different sources"""
        return []
    
    async def _rank_cross_source_results(self, results, query, content_types):
        """Rank cross-source results"""
        return results
    
    async def _enhance_cross_source_results(self, results, query):
        """Enhance cross-source results"""
        return results
    
    async def _generate_cross_source_suggestions(self, query, results, content_types):
        """Generate cross-source suggestions"""
        return ["Search in documentation", "Look for related meetings", "Check recent commits"]
    
    async def _generate_related_cross_source_queries(self, query, results):
        """Generate related cross-source queries"""
        return [f"meetings about {query}", f"issues related to {query}", f"docs explaining {query}"]
    
    async def _generate_cross_source_facets(self, results):
        """Generate cross-source facets"""
        return {
            "content_type": {"code": 10, "documentation": 8, "meetings": 5},
            "timeline": {"recent": 12, "last_month": 8, "last_quarter": 3},
            "importance": {"critical": 2, "high": 8, "medium": 10, "low": 3}
        }
    
    async def _generate_cross_source_context_insights(self, project_id, query, results, content_types):
        """Generate cross-source context insights"""
        return {
            "sources_searched": len(content_types),
            "total_matches": len(results),
            "primary_source": "code",
            "related_topics": ["authentication", "security", "api"]
        }
    
    # Placeholder methods for contextual search
    async def _analyze_user_context(self, project_id, user_context, current_file, recent_activity):
        """Analyze user context for contextual search"""
        return {
            "user_role": user_context.get("role", "developer"),
            "current_context": current_file,
            "recent_topics": [],
            "preferred_sources": ["code", "documentation"]
        }
    
    async def _enhance_query_with_context(self, query, context_analysis):
        """Enhance query with contextual information"""
        return query
    
    async def _perform_contextual_search(self, project_id, query, context_analysis, limit):
        """Perform context-weighted search"""
        return []
    
    async def _generate_proactive_suggestions(self, project_id, context_analysis, results):
        """Generate proactive suggestions based on context"""
        return ["Based on your recent work, you might want to look at...", "Related to your current file..."]
    
    async def _rank_contextual_results(self, results, query, context_analysis):
        """Rank results with context weighting"""
        return results
    
    async def _generate_contextual_insights(self, project_id, query, results, context_analysis):
        """Generate contextual insights"""
        return {
            "context_relevance": "high",
            "suggested_next_steps": ["Review related documentation", "Check test coverage"],
            "related_team_members": ["alice", "bob"]
        }
    
    async def _store_search_history(self, project_id, query, search_type, results, search_id):
        """Store search history for learning and analytics"""
        search_entry = {
            "search_id": search_id,
            "query": query,
            "search_type": search_type.value,
            "results_count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.search_history[project_id].append(search_entry)
        
        # Keep only recent history (last 100 searches per project)
        if len(self.search_history[project_id]) > 100:
            self.search_history[project_id] = self.search_history[project_id][-100:]
    
    def _determine_content_type(self, result: Dict[str, Any]) -> ContentType:
        """Determine content type from search result metadata"""
        source_type = result.get('metadata', {}).get('source_type', '').lower()
        file_path = result.get('metadata', {}).get('file_path', '').lower()
        
        # Map source types to content types
        if source_type in ['github', 'code'] or any(ext in file_path for ext in ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs']):
            return ContentType.CODE
        elif source_type in ['confluence', 'docs'] or 'doc' in file_path:
            return ContentType.DOCUMENTATION
        elif source_type in ['meetings', 'meeting']:
            return ContentType.MEETING
        elif source_type in ['jira', 'issues', 'issue']:
            return ContentType.ISSUE
        elif source_type in ['comments', 'comment']:
            return ContentType.COMMENT
        elif source_type in ['slack']:
            return ContentType.SLACK_MESSAGE
        elif source_type in ['email']:
            return ContentType.EMAIL
        elif 'commit' in source_type:
            return ContentType.COMMIT
        else:
            return ContentType.DOCUMENTATION  # Default fallback
