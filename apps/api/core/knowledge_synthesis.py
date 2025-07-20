"""
Multi-Source Knowledge Synthesis Service for NeuroSync
Connects and synthesizes knowledge across code, meetings, tickets, documentation, and conversations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor

from .vector_db import VectorDatabase
from .knowledge_graph import KnowledgeGraphBuilder
from .context_persistence import ContextPersistenceService, ContextType, ContextScope
from .data_importance_filter import DataImportanceFilter

logger = logging.getLogger(__name__)

class SynthesisType(Enum):
    """Types of knowledge synthesis"""
    CODE_TO_ISSUE = "code_to_issue"
    MEETING_TO_DECISION = "meeting_to_decision"
    ISSUE_TO_CODE_CHANGE = "issue_to_code_change"
    CONVERSATION_TO_ACTION = "conversation_to_action"
    CROSS_SOURCE_PATTERN = "cross_source_pattern"
    TEMPORAL_EVOLUTION = "temporal_evolution"
    TEAM_KNOWLEDGE_MAP = "team_knowledge_map"

@dataclass
class SynthesisResult:
    """Result of knowledge synthesis operation"""
    synthesis_id: str
    synthesis_type: SynthesisType
    project_id: str
    connections: List[Dict[str, Any]]
    insights: List[str]
    confidence_score: float
    evidence: List[Dict[str, Any]]
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class CrossSourceInsight:
    """Insight derived from multiple knowledge sources"""
    insight_id: str
    title: str
    description: str
    sources_involved: List[str]
    evidence_strength: float
    impact_level: str  # low, medium, high, critical
    actionable_items: List[str]
    related_entities: List[str]
    created_at: datetime

class MultiSourceKnowledgeSynthesis:
    """
    Production-ready multi-source knowledge synthesis service
    
    Features:
    - Cross-source relationship discovery
    - Pattern recognition across data types
    - Temporal knowledge evolution tracking
    - Team knowledge mapping
    - Automated insight generation
    """
    
    def __init__(self):
        self.vector_db = VectorDatabase()
        self.knowledge_graph = KnowledgeGraphBuilder()
        self.context_service = ContextPersistenceService()
        self.importance_filter = DataImportanceFilter()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Synthesis cache
        self.synthesis_cache: Dict[str, SynthesisResult] = {}
        
        # Configuration
        self.min_confidence_threshold = 0.6
        self.similarity_threshold = 0.7
    
    async def synthesize_project_knowledge(self, project_id: str, 
                                         focus_areas: Optional[List[str]] = None,
                                         time_window_days: int = 30) -> List[SynthesisResult]:
        """
        Perform comprehensive knowledge synthesis for a project
        
        Args:
            project_id: Project identifier
            focus_areas: Optional list of areas to focus synthesis on
            time_window_days: Time window for analysis
            
        Returns:
            List of synthesis results
        """
        try:
            logger.info(f"Starting knowledge synthesis for project {project_id}")
            
            # Get all project data from different sources
            project_data = await self._gather_project_data(project_id, time_window_days)
            
            # Perform different types of synthesis
            synthesis_tasks = [
                self._synthesize_code_to_issues(project_id, project_data),
                self._synthesize_meetings_to_decisions(project_id, project_data),
                self._synthesize_cross_source_patterns(project_id, project_data),
                self._synthesize_team_knowledge_map(project_id, project_data)
            ]
            
            # Run synthesis tasks concurrently
            synthesis_results = []
            completed_tasks = await asyncio.gather(*synthesis_tasks, return_exceptions=True)
            
            for result in completed_tasks:
                if isinstance(result, Exception):
                    logger.error(f"Synthesis task failed: {str(result)}")
                    continue
                
                if isinstance(result, list):
                    synthesis_results.extend(result)
                else:
                    synthesis_results.append(result)
            
            # Filter by focus areas if specified
            if focus_areas:
                synthesis_results = [
                    result for result in synthesis_results
                    if any(area.lower() in str(result.metadata).lower() for area in focus_areas)
                ]
            
            # Sort by confidence and importance
            synthesis_results.sort(key=lambda x: x.confidence_score, reverse=True)
            
            # Store synthesis results
            for result in synthesis_results:
                self.synthesis_cache[result.synthesis_id] = result
                
                # Store as context for future reference
                await self.context_service.store_context(
                    project_id=project_id,
                    user_id="system",
                    context_type=ContextType.INSIGHT,
                    scope=ContextScope.PROJECT,
                    content=asdict(result),
                    metadata={
                        'synthesis_type': result.synthesis_type.value,
                        'confidence': result.confidence_score,
                        'sources_count': len(set(conn.get('source_type', '') for conn in result.connections))
                    }
                )
            
            logger.info(f"Completed knowledge synthesis: {len(synthesis_results)} results")
            return synthesis_results
            
        except Exception as e:
            logger.error(f"Knowledge synthesis failed: {str(e)}")
            raise
    
    async def generate_cross_source_insights(self, project_id: str,
                                           entity_id: str, entity_type: str) -> List[CrossSourceInsight]:
        """
        Generate insights by analyzing an entity across all data sources
        
        Args:
            project_id: Project identifier
            entity_id: Entity to analyze
            entity_type: Type of entity
            
        Returns:
            List of cross-source insights
        """
        try:
            insights = []
            
            # Find all references to this entity across sources
            references = await self._find_cross_source_references(project_id, entity_id, entity_type)
            
            # Analyze patterns in references
            patterns = await self._analyze_reference_patterns(references)
            
            # Generate insights from patterns
            for pattern in patterns:
                insight = await self._create_insight_from_pattern(project_id, pattern, references)
                if insight and insight.evidence_strength >= self.min_confidence_threshold:
                    insights.append(insight)
            
            # Sort by impact and evidence strength
            insights.sort(key=lambda x: (x.impact_level, x.evidence_strength), reverse=True)
            
            logger.info(f"Generated {len(insights)} cross-source insights for {entity_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Cross-source insight generation failed: {str(e)}")
            return []
    
    async def _gather_project_data(self, project_id: str, time_window_days: int) -> Dict[str, List[Dict]]:
        """Gather all project data from different sources"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
            
            # Get data from vector database
            vector_results = await self.vector_db.get_project_documents(
                project_id=project_id,
                limit=1000,
                filters={'created_after': cutoff_date.isoformat()}
            )
            
            # Get entities and relationships from knowledge graph
            entities = await self.knowledge_graph.get_project_entities(project_id)
            relationships = await self.knowledge_graph.get_project_relationships(project_id)
            
            # Get context from persistence service
            contexts = await self.context_service.retrieve_context(
                project_id=project_id,
                user_id="",  # Get all users
                limit=500
            )
            
            # Organize by source type
            project_data = {
                'vector_documents': vector_results,
                'entities': entities,
                'relationships': relationships,
                'contexts': [asdict(ctx) for ctx in contexts]
            }
            
            # Group by source
            by_source = defaultdict(list)
            for doc in vector_results:
                source = doc.get('metadata', {}).get('source', 'unknown')
                by_source[source].append(doc)
            
            project_data['by_source'] = dict(by_source)
            
            return project_data
            
        except Exception as e:
            logger.error(f"Failed to gather project data: {str(e)}")
            return {}
    
    async def _synthesize_code_to_issues(self, project_id: str, project_data: Dict) -> List[SynthesisResult]:
        """Synthesize connections between code changes and issues"""
        try:
            results = []
            
            # Get code-related documents
            code_docs = project_data.get('by_source', {}).get('github', [])
            issue_docs = project_data.get('by_source', {}).get('jira', [])
            
            # Find connections between code and issues
            for code_doc in code_docs:
                code_content = code_doc.get('content', '')
                code_metadata = code_doc.get('metadata', {})
                
                # Look for issue references in code
                issue_refs = self._extract_issue_references(code_content)
                
                connections = []
                evidence = []
                
                for issue_ref in issue_refs:
                    # Find matching issues
                    matching_issues = [
                        issue for issue in issue_docs
                        if issue_ref.lower() in issue.get('content', '').lower() or
                           issue_ref.lower() in str(issue.get('metadata', {})).lower()
                    ]
                    
                    for issue in matching_issues:
                        connections.append({
                            'source_type': 'github',
                            'source_id': code_metadata.get('id', ''),
                            'target_type': 'jira',
                            'target_id': issue.get('metadata', {}).get('id', ''),
                            'connection_type': 'implements',
                            'confidence': 0.8
                        })
                        
                        evidence.append({
                            'type': 'issue_reference',
                            'reference': issue_ref,
                            'context': code_content[:200]
                        })
                
                if connections:
                    synthesis = SynthesisResult(
                        synthesis_id=f"code_issue_{project_id}_{len(results)}",
                        synthesis_type=SynthesisType.CODE_TO_ISSUE,
                        project_id=project_id,
                        connections=connections,
                        insights=[
                            f"Code changes implement {len(connections)} issue requirements",
                            f"Strong traceability between development and requirements"
                        ],
                        confidence_score=sum(c['confidence'] for c in connections) / len(connections),
                        evidence=evidence,
                        created_at=datetime.utcnow(),
                        metadata={
                            'code_file': code_metadata.get('title', ''),
                            'issues_referenced': len(connections)
                        }
                    )
                    results.append(synthesis)
            
            return results
            
        except Exception as e:
            logger.error(f"Code-to-issue synthesis failed: {str(e)}")
            return []
    
    async def _synthesize_meetings_to_decisions(self, project_id: str, project_data: Dict) -> List[SynthesisResult]:
        """Synthesize connections between meetings and decisions"""
        try:
            results = []
            
            # Get meeting-related contexts
            meeting_contexts = [
                ctx for ctx in project_data.get('contexts', [])
                if ctx.get('context_type') == ContextType.CONVERSATION.value
            ]
            
            # Get decision-related contexts
            decision_contexts = [
                ctx for ctx in project_data.get('contexts', [])
                if ctx.get('context_type') == ContextType.DECISION.value
            ]
            
            # Find connections between meetings and decisions
            for meeting in meeting_contexts:
                meeting_content = meeting.get('content', {})
                meeting_topics = meeting_content.get('topics', [])
                
                related_decisions = []
                for decision in decision_contexts:
                    decision_content = str(decision.get('content', {}))
                    
                    # Check for topic overlap
                    overlap = any(topic.lower() in decision_content.lower() for topic in meeting_topics)
                    if overlap:
                        related_decisions.append(decision)
                
                if related_decisions:
                    connections = [{
                        'source_type': 'meeting',
                        'source_id': meeting.get('id', ''),
                        'target_type': 'decision',
                        'target_id': decision.get('id', ''),
                        'connection_type': 'influences',
                        'confidence': 0.7
                    } for decision in related_decisions]
                    
                    synthesis = SynthesisResult(
                        synthesis_id=f"meeting_decision_{project_id}_{len(results)}",
                        synthesis_type=SynthesisType.MEETING_TO_DECISION,
                        project_id=project_id,
                        connections=connections,
                        insights=[
                            f"Meeting discussion led to {len(related_decisions)} decisions",
                            "Clear decision-making process from team discussions"
                        ],
                        confidence_score=0.7,
                        evidence=[{
                            'type': 'topic_overlap',
                            'topics': meeting_topics,
                            'decisions_count': len(related_decisions)
                        }],
                        created_at=datetime.utcnow(),
                        metadata={
                            'meeting_id': meeting.get('id', ''),
                            'decisions_influenced': len(related_decisions)
                        }
                    )
                    results.append(synthesis)
            
            return results
            
        except Exception as e:
            logger.error(f"Meeting-to-decision synthesis failed: {str(e)}")
            return []
    
    async def _synthesize_cross_source_patterns(self, project_id: str, project_data: Dict) -> List[SynthesisResult]:
        """Identify patterns that span multiple data sources"""
        try:
            results = []
            
            # Analyze entity mentions across sources
            entity_mentions = defaultdict(lambda: defaultdict(int))
            
            # Count mentions in each source
            for source, docs in project_data.get('by_source', {}).items():
                for doc in docs:
                    content = doc.get('content', '').lower()
                    
                    # Extract entities (simple keyword matching)
                    entities = self._extract_entities(content)
                    for entity in entities:
                        entity_mentions[entity][source] += 1
            
            # Find entities mentioned across multiple sources
            cross_source_entities = {
                entity: sources for entity, sources in entity_mentions.items()
                if len(sources) >= 2
            }
            
            for entity, sources in cross_source_entities.items():
                connections = []
                for source in sources.keys():
                    connections.append({
                        'source_type': source,
                        'entity': entity,
                        'mentions': sources[source],
                        'connection_type': 'references'
                    })
                
                synthesis = SynthesisResult(
                    synthesis_id=f"cross_pattern_{project_id}_{len(results)}",
                    synthesis_type=SynthesisType.CROSS_SOURCE_PATTERN,
                    project_id=project_id,
                    connections=connections,
                    insights=[
                        f"Entity '{entity}' is discussed across {len(sources)} different sources",
                        "High cross-source visibility indicates importance"
                    ],
                    confidence_score=min(1.0, len(sources) * 0.3),
                    evidence=[{
                        'type': 'cross_source_mentions',
                        'entity': entity,
                        'sources': list(sources.keys()),
                        'total_mentions': sum(sources.values())
                    }],
                    created_at=datetime.utcnow(),
                    metadata={
                        'entity': entity,
                        'sources_count': len(sources),
                        'total_mentions': sum(sources.values())
                    }
                )
                results.append(synthesis)
            
            return results
            
        except Exception as e:
            logger.error(f"Cross-source pattern synthesis failed: {str(e)}")
            return []
    
    async def _synthesize_team_knowledge_map(self, project_id: str, project_data: Dict) -> List[SynthesisResult]:
        """Create a map of team knowledge and expertise"""
        try:
            results = []
            
            # Analyze contributions by team members
            team_contributions = defaultdict(lambda: defaultdict(int))
            
            for docs in project_data.get('by_source', {}).values():
                for doc in docs:
                    author = doc.get('metadata', {}).get('created_by') or doc.get('metadata', {}).get('author')
                    if author:
                        source = doc.get('metadata', {}).get('source', 'unknown')
                        team_contributions[author][source] += 1
            
            # Analyze expertise areas
            team_expertise = {}
            for author, sources in team_contributions.items():
                # Get documents by this author
                author_docs = []
                for docs in project_data.get('by_source', {}).values():
                    for doc in docs:
                        doc_author = doc.get('metadata', {}).get('created_by') or doc.get('metadata', {}).get('author')
                        if doc_author == author:
                            author_docs.append(doc)
                
                # Extract expertise topics
                expertise_topics = []
                for doc in author_docs:
                    content = doc.get('content', '')
                    topics = self._extract_topics(content)
                    expertise_topics.extend(topics)
                
                team_expertise[author] = {
                    'sources': dict(sources),
                    'total_contributions': sum(sources.values()),
                    'expertise_areas': Counter(expertise_topics).most_common(5)
                }
            
            if team_expertise:
                synthesis = SynthesisResult(
                    synthesis_id=f"team_knowledge_{project_id}",
                    synthesis_type=SynthesisType.TEAM_KNOWLEDGE_MAP,
                    project_id=project_id,
                    connections=[{
                        'type': 'team_member',
                        'member': member,
                        'contributions': data['total_contributions'],
                        'sources': list(data['sources'].keys()),
                        'expertise': [topic for topic, count in data['expertise_areas']]
                    } for member, data in team_expertise.items()],
                    insights=[
                        f"Mapped knowledge for {len(team_expertise)} team members",
                        "Identified expertise areas and contribution patterns",
                        "Team knowledge is distributed across multiple sources"
                    ],
                    confidence_score=0.8,
                    evidence=[{
                        'type': 'team_analysis',
                        'team_size': len(team_expertise),
                        'total_contributions': sum(data['total_contributions'] for data in team_expertise.values())
                    }],
                    created_at=datetime.utcnow(),
                    metadata={
                        'team_members_analyzed': len(team_expertise),
                        'expertise_areas_identified': sum(len(data['expertise_areas']) for data in team_expertise.values())
                    }
                )
                results.append(synthesis)
            
            return results
            
        except Exception as e:
            logger.error(f"Team knowledge map synthesis failed: {str(e)}")
            return []
    
    def _extract_issue_references(self, content: str) -> List[str]:
        """Extract issue references from content"""
        patterns = [
            r'#(\d+)',  # #123
            r'[A-Z]+-\d+',  # JIRA-123
            r'issue[s]?\s*#?(\d+)',  # issue 123
            r'bug[s]?\s*#?(\d+)',  # bug 123
            r'ticket[s]?\s*#?(\d+)'  # ticket 123
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            references.extend(matches)
        
        return list(set(references))
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract entities from content"""
        entities = []
        
        # API endpoints
        api_matches = re.findall(r'/api/[a-zA-Z0-9/_-]+', content)
        entities.extend(api_matches)
        
        # Function/method names
        func_matches = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*\(\)', content)
        entities.extend([m[:-2] for m in func_matches])  # Remove ()
        
        # Class names (CamelCase)
        class_matches = re.findall(r'\b[A-Z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b', content)
        entities.extend(class_matches)
        
        return list(set(entities))
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from content"""
        tech_topics = [
            'api', 'database', 'frontend', 'backend', 'authentication', 'authorization',
            'deployment', 'testing', 'bug', 'feature', 'performance', 'security',
            'ui', 'ux', 'integration', 'migration', 'refactoring', 'optimization'
        ]
        
        content_lower = content.lower()
        found_topics = [topic for topic in tech_topics if topic in content_lower]
        
        return found_topics
    
    async def _find_cross_source_references(self, project_id: str, entity_id: str, entity_type: str) -> List[Dict]:
        """Find references to an entity across all sources"""
        try:
            # Search in vector database
            search_results = await self.vector_db.semantic_search(
                query=entity_id,
                project_id=project_id,
                limit=50
            )
            
            # Search in knowledge graph
            related_entities = await self.knowledge_graph.find_related_entities(
                project_id=project_id,
                entity_id=entity_id,
                entity_type=entity_type,
                max_depth=2
            )
            
            references = []
            for result in search_results:
                references.append({
                    'source': result.get('metadata', {}).get('source', 'unknown'),
                    'type': 'vector_match',
                    'content': result.get('content', ''),
                    'metadata': result.get('metadata', {})
                })
            
            for entity in related_entities:
                references.append({
                    'source': 'knowledge_graph',
                    'type': 'relationship',
                    'entity': entity,
                    'metadata': {}
                })
            
            return references
            
        except Exception as e:
            logger.error(f"Failed to find cross-source references: {str(e)}")
            return []
    
    async def _analyze_reference_patterns(self, references: List[Dict]) -> List[Dict]:
        """Analyze patterns in cross-source references"""
        try:
            patterns = []
            
            # Group by source
            by_source = defaultdict(list)
            for ref in references:
                by_source[ref['source']].append(ref)
            
            # Pattern: Multiple source mentions
            if len(by_source) >= 2:
                patterns.append({
                    'type': 'multi_source_mention',
                    'sources': list(by_source.keys()),
                    'confidence': min(1.0, len(by_source) * 0.3)
                })
            
            # Pattern: High frequency mentions
            total_mentions = len(references)
            if total_mentions >= 5:
                patterns.append({
                    'type': 'high_frequency',
                    'mentions': total_mentions,
                    'confidence': min(1.0, total_mentions * 0.1)
                })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze reference patterns: {str(e)}")
            return []
    
    async def _create_insight_from_pattern(self, project_id: str, pattern: Dict, references: List[Dict]) -> Optional[CrossSourceInsight]:
        """Create insight from detected pattern"""
        try:
            if pattern['type'] == 'multi_source_mention':
                return CrossSourceInsight(
                    insight_id=f"insight_{project_id}_{pattern['type']}",
                    title="Cross-Source Entity Reference",
                    description=f"Entity is referenced across {len(pattern['sources'])} different sources",
                    sources_involved=pattern['sources'],
                    evidence_strength=pattern['confidence'],
                    impact_level='medium',
                    actionable_items=[
                        "Review entity importance across sources",
                        "Consider creating unified documentation"
                    ],
                    related_entities=[],
                    created_at=datetime.utcnow()
                )
            
            elif pattern['type'] == 'high_frequency':
                return CrossSourceInsight(
                    insight_id=f"insight_{project_id}_{pattern['type']}",
                    title="High-Frequency Entity",
                    description=f"Entity mentioned {pattern['mentions']} times across sources",
                    sources_involved=[ref['source'] for ref in references],
                    evidence_strength=pattern['confidence'],
                    impact_level='high',
                    actionable_items=[
                        "Entity appears to be critical to project",
                        "Ensure proper documentation and testing"
                    ],
                    related_entities=[],
                    created_at=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create insight from pattern: {str(e)}")
            return None
