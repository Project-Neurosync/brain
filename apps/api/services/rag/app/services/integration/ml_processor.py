"""
ML Integration Processor for building knowledge graphs from integration data.

This module provides machine learning capabilities to process data from various 
integrations (GitHub, Jira, Slack, etc.), identify relationships between events,
and build a rich knowledge graph with temporal and causal connections.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import uuid
import re
import json
from enum import Enum
import statistics
import numpy as np
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.knowledge_graph.base import KnowledgeGraphService, Entity, Relationship
from app.services.knowledge_graph.factory import get_knowledge_graph_service
from app.services.embedding.factory import embedding_service
from app.services.llm.factory import llm

# Set up logger
logger = logging.getLogger(__name__)

# Integration event types
class EventType(str, Enum):
    """Types of integration events that can be processed."""
    COMMIT = "commit"
    ISSUE = "issue"
    ISSUE_COMMENT = "issue_comment"
    PULL_REQUEST = "pull_request"
    CODE_REVIEW = "code_review"
    MEETING = "meeting"
    MESSAGE = "message"
    DOCUMENT = "document"
    BUILD = "build"
    DEPLOYMENT = "deployment"
    TEST_RUN = "test_run"
    CUSTOM = "custom"


class EventRelationType(str, Enum):
    """Types of relationships between events."""
    CAUSED = "caused"            # One event directly caused another
    RESOLVED = "resolved"        # One event resolved another (e.g., commit fixed bug)
    REFERENCED = "referenced"    # One event referenced another
    PRECEDED = "preceded"        # Temporal relationship only
    FOLLOWED = "followed"        # Temporal relationship only
    DEPENDS_ON = "depends_on"    # Dependency relationship
    BLOCKS = "blocks"            # Blocking relationship
    RELATED_TO = "related_to"    # Generic relationship
    SAME_COMPONENT = "same_component"  # Events affect same component
    SAME_AUTHOR = "same_author"  # Events have same author


class IntegrationEvent(BaseModel):
    """
    Representation of an event from an integration source.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # e.g., "github", "jira", "slack"
    event_type: EventType
    title: str
    content: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Optional[str] = None
    url: Optional[str] = None
    project_id: Optional[str] = None
    repository: Optional[str] = None
    branch: Optional[str] = None
    component: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    class Config:
        arbitrary_types_allowed = True


class EventRelation(BaseModel):
    """
    Representation of a relationship between two integration events.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_event_id: str
    target_event_id: str
    relation_type: EventRelationType
    confidence: float  # ML model confidence in this relationship (0-1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    

class MLProcessorConfig(BaseModel):
    """Configuration for the ML integration processor."""
    threshold_confidence: float = 0.7  # Minimum confidence score to accept a relationship
    max_context_window: int = 10  # Number of previous events to consider for relationships
    enable_semantic_matching: bool = True  # Whether to use semantic similarity for matching
    enable_temporal_analysis: bool = True  # Whether to consider time-based relationships
    enable_causal_inference: bool = True  # Whether to perform causal inference
    embedding_batch_size: int = 32  # Batch size for embedding generation
    store_all_events: bool = False  # Whether to store all events or only those with relationships
    min_similarity_score: float = 0.75  # Minimum similarity score for semantic matching
    max_time_window_days: int = 30  # Maximum time window to consider for relationships
    project_id: Optional[str] = None  # Default project ID
    risk_window_days: int = 90  # Number of days to analyze for risk prediction
    risk_threshold_high: float = 0.8  # Threshold for high risk
    risk_threshold_medium: float = 0.5  # Threshold for medium risk


class MLIntegrationProcessor:
    """
    ML processor for integration data that builds a knowledge graph
    with temporal and causal relationships.
    
    This service processes incoming data from integrations, uses ML to identify
    relationships, and builds a rich knowledge graph that supports complex
    querying about events, bugs, and their solutions.
    """
    
    def __init__(
        self,
        config: Optional[MLProcessorConfig] = None,
        knowledge_graph: Optional[KnowledgeGraphService] = None,
    ):
        """
        Initialize the ML integration processor.
        
        Args:
            config: Optional configuration for the processor
            knowledge_graph: Optional knowledge graph service
        """
        self.config = config or MLProcessorConfig()
        self.knowledge_graph = knowledge_graph or get_knowledge_graph_service()
        self.embedding_service = embedding_service
        
        # Cache of recent events for relationship detection
        self._recent_events_cache: Dict[str, IntegrationEvent] = {}
        self._recent_events_embeddings: Dict[str, List[float]] = {}
        
        # Statistics and metrics
        self.metrics = {
            "events_processed": 0,
            "relationships_detected": 0,
            "causal_relationships": 0,
            "temporal_relationships": 0,
            "reference_relationships": 0,
            "entities_created": 0,
            "start_time": datetime.now(timezone.utc),
            "last_processed": None,
        }
        
        logger.info(f"ML Integration Processor initialized with config: {self.config}")
    
    async def initialize(self) -> None:
        """Initialize the processor and its dependencies."""
        # Initialize knowledge graph
        await self.knowledge_graph.initialize()
        
        # Preload recent events from knowledge graph to warm up cache
        await self._preload_recent_events()
        
        logger.info("ML Integration Processor initialized successfully")
    
    async def _preload_recent_events(self, limit: int = 100) -> None:
        """
        Preload recent events from the knowledge graph to warm up the cache.
        
        Args:
            limit: Maximum number of events to preload
        """
        try:
            # Query knowledge graph for recent events
            entities = await self.knowledge_graph.search_entities(
                filters={"type": "event"},
                project_id=self.config.project_id,
                limit=limit,
                sort_by="created_at",
                sort_direction="desc"
            )
            
            # Convert to IntegrationEvent and add to cache
            for entity in entities:
                try:
                    event = self._entity_to_event(entity)
                    if event:
                        self._recent_events_cache[event.id] = event
                        if "embedding" in entity.properties:
                            # If embedding is stored in entity properties
                            embedding_data = entity.properties.get("embedding")
                            if isinstance(embedding_data, str):
                                try:
                                    # Parse from JSON string if needed
                                    embedding = json.loads(embedding_data)
                                    self._recent_events_embeddings[event.id] = embedding
                                except:
                                    pass
                except Exception as e:
                    logger.warning(f"Error converting entity to event: {str(e)}")
                    
            logger.info(f"Preloaded {len(self._recent_events_cache)} events into cache")
            
        except Exception as e:
            logger.error(f"Error preloading recent events: {str(e)}")
    
    def _entity_to_event(self, entity: Entity) -> Optional[IntegrationEvent]:
        """
        Convert a knowledge graph entity to an IntegrationEvent.
        
        Args:
            entity: The entity to convert
            
        Returns:
            IntegrationEvent or None if conversion failed
        """
        try:
            # Extract properties
            props = entity.properties
            
            # Try to parse event_type
            event_type = EventType.CUSTOM
            if "event_type" in props:
                try:
                    event_type = EventType(props["event_type"])
                except ValueError:
                    pass
            
            # Parse timestamp
            timestamp = datetime.now(timezone.utc)
            if "timestamp" in props:
                try:
                    if isinstance(props["timestamp"], str):
                        timestamp = datetime.fromisoformat(props["timestamp"].replace("Z", "+00:00"))
                    elif isinstance(props["timestamp"], datetime):
                        timestamp = props["timestamp"]
                except:
                    pass
            
            # Parse labels
            labels = []
            if "labels" in props:
                try:
                    if isinstance(props["labels"], str):
                        labels = json.loads(props["labels"])
                    elif isinstance(props["labels"], list):
                        labels = props["labels"]
                except:
                    pass
            
            # Parse metadata
            metadata = {}
            if "metadata" in props:
                try:
                    if isinstance(props["metadata"], str):
                        metadata = json.loads(props["metadata"])
                    elif isinstance(props["metadata"], dict):
                        metadata = props["metadata"]
                except:
                    pass
            
            return IntegrationEvent(
                id=entity.id,
                source=props.get("source", "unknown"),
                event_type=event_type,
                title=props.get("title", "Untitled Event"),
                content=props.get("content"),
                timestamp=timestamp,
                author=props.get("author"),
                url=props.get("url"),
                project_id=props.get("project_id"),
                repository=props.get("repository"),
                branch=props.get("branch"),
                component=props.get("component"),
                labels=labels,
                status=props.get("status"),
                metadata=metadata,
            )
        except Exception as e:
            logger.warning(f"Error converting entity to event: {str(e)}")
            return None
    
    def _event_to_entity(self, event: IntegrationEvent) -> Entity:
        """
        Convert an IntegrationEvent to a knowledge graph entity.
        
        Args:
            event: The event to convert
            
        Returns:
            Entity representation
        """
        # Convert labels and metadata to JSON strings if needed
        labels_json = json.dumps(event.labels) if event.labels else "[]"
        metadata_json = json.dumps(event.metadata) if event.metadata else "{}"
        
        properties = {
            "source": event.source,
            "event_type": event.event_type.value,
            "title": event.title,
            "content": event.content,
            "timestamp": event.timestamp.isoformat(),
            "author": event.author,
            "url": event.url,
            "project_id": event.project_id,
            "repository": event.repository,
            "branch": event.branch,
            "component": event.component,
            "labels": labels_json,
            "status": event.status,
            "metadata": metadata_json,
        }
        
        # Add embedding if available
        if event.embedding:
            properties["embedding"] = json.dumps(event.embedding)
        
        return Entity(
            id=event.id,
            name=event.title,
            type="event",
            properties=properties,
            project_id=event.project_id,
        )
    
    def _relation_to_relationship(self, relation: EventRelation) -> Relationship:
        """
        Convert an EventRelation to a knowledge graph relationship.
        
        Args:
            relation: The relation to convert
            
        Returns:
            Relationship representation
        """
        properties = {
            "relation_type": relation.relation_type.value,
            "confidence": relation.confidence,
            "timestamp": relation.timestamp.isoformat(),
            "metadata": json.dumps(relation.metadata) if relation.metadata else "{}",
        }
        
        return Relationship(
            id=relation.id,
            source_id=relation.source_event_id,
            target_id=relation.target_event_id,
            type="RELATES_TO",
            properties=properties,
            project_id=relation.project_id,
        )
    
    async def process_event(
        self,
        event: IntegrationEvent,
        project_id: Optional[str] = None
    ) -> Tuple[bool, List[EventRelation]]:
        """
        Process an integration event, detect relationships, and update the knowledge graph.
        
        Args:
            event: The integration event to process
            project_id: Optional project ID to associate with this event
            
        Returns:
            Tuple of (success, list of detected relationships)
        """
        try:
            # Update metrics
            self.metrics["events_processed"] += 1
            self.metrics["last_processed"] = datetime.now(timezone.utc)
            
            # Set project ID from config if not provided
            if not event.project_id:
                event.project_id = project_id or self.config.project_id
                
            # Generate embedding for the event
            if not event.embedding and self.config.enable_semantic_matching:
                content_to_embed = f"{event.title} {event.content or ''}"
                embeddings = await self.embedding_service.embed_documents([content_to_embed])
                if embeddings:
                    event.embedding = embeddings[0]
            
            # Detect relationships with existing events
            relations = await self._detect_relationships(event)
            
            # Update metrics for relationships
            self.metrics["relationships_detected"] += len(relations)
            
            # Store event and relationships in knowledge graph
            if relations or self.config.store_all_events:
                # Convert event to entity
                entity = self._event_to_entity(event)
                
                # Store entity in knowledge graph
                success = await self.knowledge_graph.add_entity(entity)
                if success:
                    self.metrics["entities_created"] += 1
                
                # Store relationships
                for relation in relations:
                    relationship = self._relation_to_relationship(relation)
                    await self.knowledge_graph.add_relationship(relationship)
                    
                    # Update relationship type metrics
                    if relation.relation_type in [EventRelationType.CAUSED, EventRelationType.RESOLVED]:
                        self.metrics["causal_relationships"] += 1
                    elif relation.relation_type in [EventRelationType.PRECEDED, EventRelationType.FOLLOWED]:
                        self.metrics["temporal_relationships"] += 1
                    elif relation.relation_type == EventRelationType.REFERENCED:
                        self.metrics["reference_relationships"] += 1
            
            # Update cache with this event
            self._recent_events_cache[event.id] = event
            if event.embedding:
                self._recent_events_embeddings[event.id] = event.embedding
                
            # Prune cache if needed
            self._prune_cache()
            
            return True, relations
            
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
            return False, []

    def _prune_cache(self, max_size: int = 1000):
        """
        Prune the event cache if it exceeds maximum size.
        
        Args:
            max_size: Maximum cache size
        """
        if len(self._recent_events_cache) > max_size:
            # Get events sorted by timestamp (oldest first)
            sorted_events = sorted(
                self._recent_events_cache.items(),
                key=lambda x: x[1].timestamp
            )
            
            # Remove oldest events
            to_remove = sorted_events[:len(sorted_events) - max_size]
            for event_id, _ in to_remove:
                del self._recent_events_cache[event_id]
                if event_id in self._recent_events_embeddings:
                    del self._recent_events_embeddings[event_id]

    async def _detect_relationships(self, event: IntegrationEvent) -> List[EventRelation]:
        """
        Detect relationships between this event and previous events.
        
        This is the core ML logic that identifies temporal and causal relationships.
        
        Args:
            event: The new event to analyze
            
        Returns:
            List of detected relationships
        """
        relations = []
        
        # Skip if no events in cache or this is a new event not in cache
        if not self._recent_events_cache or event.id in self._recent_events_cache:
            return relations
        
        # Apply temporal filtering - only consider events within time window
        recent_events = []
        for cached_event in self._recent_events_cache.values():
            # Skip comparison with self
            if cached_event.id == event.id:
                continue
                
            # Check time window
            if self.config.enable_temporal_analysis:
                time_diff = abs((event.timestamp - cached_event.timestamp).total_seconds())
                max_time_window = self.config.max_time_window_days * 86400  # days to seconds
                if time_diff > max_time_window:
                    continue
            
            recent_events.append(cached_event)
        
        # Sort by recency (most recent first)
        recent_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Limit to configured context window
        recent_events = recent_events[:self.config.max_context_window]
        
        # No events to compare against
        if not recent_events:
            return relations
            
        # 1. Semantic similarity matching
        if self.config.enable_semantic_matching and event.embedding:
            semantic_relations = await self._detect_semantic_relationships(event, recent_events)
            relations.extend(semantic_relations)
            
        # 2. Reference matching (e.g., issue numbers in commit messages)
        reference_relations = self._detect_reference_relationships(event, recent_events)
        relations.extend(reference_relations)
        
        # 3. Component/file overlap matching
        component_relations = self._detect_component_relationships(event, recent_events)
        relations.extend(component_relations)
        
        # 4. Temporal sequence analysis for causal inference
        if self.config.enable_causal_inference:
            causal_relations = await self._detect_causal_relationships(event, recent_events)
            relations.extend(causal_relations)
            
        # 5. Same author matching
        author_relations = self._detect_author_relationships(event, recent_events)
        relations.extend(author_relations)
        
        # Filter by confidence threshold
        relations = [r for r in relations if r.confidence >= self.config.threshold_confidence]
        
        # Remove duplicates (keeping highest confidence)
        unique_relations = {}
        for relation in relations:
            key = (relation.source_event_id, relation.target_event_id, relation.relation_type)
            if key not in unique_relations or unique_relations[key].confidence < relation.confidence:
                unique_relations[key] = relation
                
        return list(unique_relations.values())
    
    async def _detect_semantic_relationships(
        self, 
        event: IntegrationEvent,
        candidates: List[IntegrationEvent]
    ) -> List[EventRelation]:
        """
        Detect relationships based on semantic similarity.
        
        Args:
            event: The event to analyze
            candidates: Candidate events to compare against
            
        Returns:
            List of semantic relationships
        """
        relations = []
        
        if not event.embedding:
            return relations
            
        # Calculate similarity with each candidate
        for candidate in candidates:
            # Get candidate embedding
            candidate_embedding = None
            if candidate.id in self._recent_events_embeddings:
                candidate_embedding = self._recent_events_embeddings[candidate.id]
            elif candidate.embedding:
                candidate_embedding = candidate.embedding
                
            if not candidate_embedding:
                continue
                
            # Calculate cosine similarity
            similarity = self._calculate_similarity(event.embedding, candidate_embedding)
            
            # If similarity exceeds threshold, create relationship
            if similarity >= self.config.min_similarity_score:
                # Create relationship
                relation = EventRelation(
                    source_event_id=event.id,
                    target_event_id=candidate.id,
                    relation_type=EventRelationType.RELATED_TO,
                    confidence=similarity,
                    project_id=event.project_id,
                )
                relations.append(relation)
                
        return relations
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))

    def _detect_reference_relationships(
        self,
        event: IntegrationEvent,
        candidates: List[IntegrationEvent]
    ) -> List[EventRelation]:
        """
        Detect relationships based on explicit references.
        
        Args:
            event: The event to analyze
            candidates: Candidate events to compare against
            
        Returns:
            List of reference relationships
        """
        relations = []
        
        # Extract potential references from event content
        references = self._extract_references(event)
        if not references:
            return relations
        
        # Look for matches in candidates
        for candidate in candidates:
            # Check if this candidate is referenced
            matched_refs = []
            
            # Check ID match
            if candidate.id in references:
                matched_refs.append(candidate.id)
                
            # Check external IDs in metadata
            for ref in references:
                # Common external ID patterns
                external_ids = []
                if candidate.metadata.get("external_id"):
                    external_ids.append(candidate.metadata["external_id"])
                if candidate.metadata.get("issue_number"):
                    external_ids.append(f"#{candidate.metadata['issue_number']}")
                    external_ids.append(str(candidate.metadata["issue_number"]))
                if candidate.metadata.get("pr_number"):
                    external_ids.append(f"#{candidate.metadata['pr_number']}")
                    external_ids.append(str(candidate.metadata["pr_number"]))
                    
                # Check if reference matches any external ID
                if ref in external_ids:
                    matched_refs.append(ref)
            
            # If match found, create relationship
            if matched_refs:
                confidence = min(0.9, 0.7 + (0.05 * len(matched_refs)))  # Higher confidence with more matches
                
                # Determine relationship type based on event types
                relation_type = EventRelationType.REFERENCED
                
                # Check for potential resolution relationship
                if event.event_type == EventType.COMMIT and candidate.event_type == EventType.ISSUE:
                    # Look for resolution keywords in commit message
                    resolution_keywords = ["fix", "resolve", "close", "address", "solve"]
                    event_content = (event.content or "").lower() + " " + event.title.lower()
                    if any(keyword in event_content for keyword in resolution_keywords):
                        relation_type = EventRelationType.RESOLVED
                        confidence = min(0.95, confidence + 0.1)  # Boost confidence
                        
                # Create the relationship
                relation = EventRelation(
                    source_event_id=event.id,
                    target_event_id=candidate.id,
                    relation_type=relation_type,
                    confidence=confidence,
                    metadata={"matched_references": matched_refs},
                    project_id=event.project_id,
                )
                relations.append(relation)
                
        return relations
    
    def _extract_references(self, event: IntegrationEvent) -> Set[str]:
        """
        Extract potential references from event content.
        
        Args:
            event: The event to analyze
            
        Returns:
            Set of potential reference strings
        """
        references = set()
        
        # Combine title and content for analysis
        content = (event.title or "") + " " + (event.content or "")
        
        # Extract patterns:
        # 1. Issue/PR numbers (#123)
        issue_pattern = r'#(\d+)'
        for match in re.finditer(issue_pattern, content):
            references.add(f"#{match.group(1)}")
            references.add(match.group(1))
            
        # 2. Issue/PR/Jira IDs (PROJECT-123)
        jira_pattern = r'([A-Z]+-\d+)'
        for match in re.finditer(jira_pattern, content):
            references.add(match.group(1))
            
        # 3. Commit hashes
        commit_pattern = r'\b([a-f0-9]{7,40})\b'
        for match in re.finditer(commit_pattern, content):
            references.add(match.group(1))
        
        return references

    def _detect_component_relationships(
        self,
        event: IntegrationEvent,
        candidates: List[IntegrationEvent]
    ) -> List[EventRelation]:
        """
        Detect relationships based on shared components or files.
        
        Args:
            event: The event to analyze
            candidates: Candidate events to compare against
            
        Returns:
            List of component relationships
        """
        relations = []
        
        # Extract components from event
        event_components = self._extract_components(event)
        if not event_components:
            return relations
            
        # Look for component matches in candidates
        for candidate in candidates:
            # Extract components from candidate
            candidate_components = self._extract_components(candidate)
            if not candidate_components:
                continue
                
            # Find overlapping components
            common_components = event_components.intersection(candidate_components)
            if not common_components:
                continue
                
            # Calculate confidence based on overlap size
            overlap_ratio = len(common_components) / max(len(event_components), len(candidate_components))
            confidence = min(0.9, 0.6 + (0.3 * overlap_ratio))  # Scale between 0.6 and 0.9
            
            # Create relationship
            relation = EventRelation(
                source_event_id=event.id,
                target_event_id=candidate.id,
                relation_type=EventRelationType.SAME_COMPONENT,
                confidence=confidence,
                metadata={"common_components": list(common_components)},
                project_id=event.project_id,
            )
            relations.append(relation)
            
        return relations
    
    def _extract_components(self, event: IntegrationEvent) -> Set[str]:
        """
        Extract components from an event.
        
        Args:
            event: The event to analyze
            
        Returns:
            Set of components
        """
        components = set()
        
        # Add explicit component if available
        if event.component:
            components.add(event.component.lower())
            
        # Add from metadata
        if event.metadata.get("component"):
            components.add(event.metadata["component"].lower())
            
        if event.metadata.get("components"):
            if isinstance(event.metadata["components"], list):
                for comp in event.metadata["components"]:
                    if comp:
                        components.add(str(comp).lower())
                        
        # Extract file paths from commit data
        if event.event_type == EventType.COMMIT:
            # Check metadata for files
            if event.metadata.get("files"):
                files = event.metadata["files"]
                if isinstance(files, list):
                    for file_path in files:
                        if file_path:
                            # Extract components from file path (e.g., src/utils/parser.js -> utils)
                            parts = file_path.split("/")
                            if len(parts) > 1:
                                components.add(parts[0].lower())  # First directory
                                if len(parts) > 2:
                                    components.add(parts[1].lower())  # Second directory
            
            # Check content for file paths
            if event.content:
                # Look for file patterns in content
                file_pattern = r'([a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+)'
                for match in re.finditer(file_pattern, event.content):
                    file_path = match.group(1)
                    parts = file_path.split("/")
                    if len(parts) > 1:
                        components.add(parts[0].lower())
                        if len(parts) > 2:
                            components.add(parts[1].lower())
        
        # Extract component info from Jira issues
        if event.event_type == EventType.ISSUE and event.source == "jira":
            # Jira often has component field
            if event.metadata.get("jira_components"):
                jira_comps = event.metadata["jira_components"]
                if isinstance(jira_comps, list):
                    for comp in jira_comps:
                        if isinstance(comp, dict) and "name" in comp:
                            components.add(comp["name"].lower())
                        elif isinstance(comp, str):
                            components.add(comp.lower())
                            
        return components
    
    def _detect_author_relationships(
        self,
        event: IntegrationEvent,
        candidates: List[IntegrationEvent]
    ) -> List[EventRelation]:
        """
        Detect relationships based on shared authorship.
        
        Args:
            event: The event to analyze
            candidates: Candidate events to compare against
            
        Returns:
            List of author relationships
        """
        relations = []
        
        # Skip if no author
        if not event.author:
            return relations
            
        # Look for author matches in candidates
        for candidate in candidates:
            # Skip if candidate has no author
            if not candidate.author:
                continue
                
            # Check if authors match
            if event.author.lower() == candidate.author.lower():
                # Calculate confidence
                confidence = 0.8  # Base confidence for author match
                
                # Boost confidence if events are close in time
                if self.config.enable_temporal_analysis:
                    time_diff = abs((event.timestamp - candidate.timestamp).total_seconds())
                    # Higher confidence if events are within 1 hour of each other
                    if time_diff < 3600:  # 1 hour in seconds
                        confidence = min(0.95, confidence + 0.15)
                        
                # Create relationship
                relation = EventRelation(
                    source_event_id=event.id,
                    target_event_id=candidate.id,
                    relation_type=EventRelationType.SAME_AUTHOR,
                    confidence=confidence,
                    project_id=event.project_id,
                )
                relations.append(relation)
                
        return relations
    
    async def _detect_causal_relationships(
        self,
        event: IntegrationEvent,
        candidates: List[IntegrationEvent]
    ) -> List[EventRelation]:
        """
        Detect causal relationships between events.
        
        Args:
            event: The event to analyze
            candidates: Candidate events to compare against
            
        Returns:
            List of causal relationships
        """
        relations = []
        
        # Only certain event types can cause others
        if event.event_type not in [EventType.COMMIT, EventType.DEPLOYMENT, EventType.PULL_REQUEST]:
            return relations
            
        # For commits, check for causality with issues
        if event.event_type == EventType.COMMIT:
            # Get potential issue events that this commit might have caused or resolved
            issue_candidates = [c for c in candidates if c.event_type == EventType.ISSUE]
            
            for issue in issue_candidates:
                # Skip if issue came after commit (can't be caused by it)
                if issue.timestamp > event.timestamp:
                    continue
                    
                # Calculate base confidence
                confidence = 0.5
                
                # Check for explicit references
                references = self._extract_references(event)
                issue_ids = set()
                if issue.metadata.get("issue_number"):
                    issue_ids.add(str(issue.metadata["issue_number"]))
                    issue_ids.add(f"#{issue.metadata['issue_number']}")
                if issue.metadata.get("external_id"):
                    issue_ids.add(issue.metadata["external_id"])
                    
                # Boost confidence if explicit reference
                if issue_ids.intersection(references):
                    confidence += 0.3
                    
                # Check for resolution keywords
                resolution_keywords = ["fix", "solve", "resolve", "close", "address"]
                commit_text = (event.title or "").lower() + " " + (event.content or "").lower()
                if any(keyword in commit_text for keyword in resolution_keywords):
                    confidence += 0.2
                    
                # Use LLM for high-confidence causal inference if still not confident enough
                if confidence >= 0.5 and confidence < self.config.threshold_confidence:
                    llm_confidence = await self._llm_causal_inference(event, issue)
                    # Blend confidences, giving more weight to LLM for close calls
                    confidence = confidence * 0.4 + llm_confidence * 0.6
                    
                # Create relationship if confidence is high enough
                if confidence >= self.config.threshold_confidence:
                    relation = EventRelation(
                        source_event_id=event.id,
                        target_event_id=issue.id,
                        relation_type=EventRelationType.RESOLVED,
                        confidence=confidence,
                        project_id=event.project_id,
                    )
                    relations.append(relation)
                    
        # For deployments, check for causality with commits
        elif event.event_type == EventType.DEPLOYMENT:
            # Get potential commit events that this deployment might contain
            commit_candidates = [c for c in candidates if c.event_type == EventType.COMMIT]
            
            for commit in commit_candidates:
                # Skip if commit came after deployment (can't be included in it)
                if commit.timestamp > event.timestamp:
                    continue
                    
                # Check if commit hash is in deployment metadata
                confidence = 0.5
                commit_hash = None
                if commit.metadata.get("hash"):
                    commit_hash = commit.metadata["hash"]
                elif commit.metadata.get("commit_hash"):
                    commit_hash = commit.metadata["commit_hash"]
                    
                if commit_hash and event.metadata.get("commit_hashes") and isinstance(event.metadata["commit_hashes"], list):
                    if commit_hash in event.metadata["commit_hashes"]:
                        confidence = 0.95
                        
                # Create relationship if confidence is high enough
                if confidence >= self.config.threshold_confidence:
                    relation = EventRelation(
                        source_event_id=event.id,
                        target_event_id=commit.id,
                        relation_type=EventRelationType.CAUSED,
                        confidence=confidence,
                        project_id=event.project_id,
                    )
                    relations.append(relation)
        
        return relations
    
    async def _llm_causal_inference(
        self,
        source_event: IntegrationEvent,
        target_event: IntegrationEvent
    ) -> float:
        """
        Use an LLM to infer causal relationships between events.
        
        Args:
            source_event: Source event
            target_event: Target event
            
        Returns:
            Confidence score (0-1)
        """
        try:
            # Construct prompt
            prompt = f"""
You are an expert software development analyst. Your task is to determine if there is a causal relationship between the following two events:

EVENT 1 (Potential Cause):
Type: {source_event.event_type}
Title: {source_event.title}
Content: {source_event.content or "N/A"}
Author: {source_event.author or "Unknown"}
Timestamp: {source_event.timestamp.isoformat()}

EVENT 2 (Potential Effect):
Type: {target_event.event_type}
Title: {target_event.title}
Content: {target_event.content or "N/A"}
Author: {target_event.author or "Unknown"}
Timestamp: {target_event.timestamp.isoformat()}

Does EVENT 1 resolve or cause EVENT 2? Respond with a confidence score between 0 and 1, where:
0 = No causal relationship
1 = Definite causal relationship

Your response should include ONLY the numeric confidence score.
"""
            
            # Call LLM
            response = await llm.complete(prompt=prompt, temperature=0.1, max_tokens=10)
            
            # Parse response
            text = response.text.strip()
            # Extract numeric value
            match = re.search(r'([01](?:\.\d+)?)', text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return 0.0
            return 0.0
            
        except Exception as e:
            logger.error(f"Error in LLM causal inference: {str(e)}")
            return 0.0
    
    async def query_bug_history(self, bug_id: str) -> Dict[str, Any]:
        """
        Query the history of a bug, including commits that fixed it and any new bugs caused.
        
        Args:
            bug_id: ID of the bug (issue) to query
            
        Returns:
            Dictionary with bug history
        """
        try:
            # Get the bug entity
            bug_entity = await self.knowledge_graph.get_entity(bug_id)
            if not bug_entity or bug_entity.type != "event":
                return {"error": f"Bug with ID {bug_id} not found"}
                
            # Convert to event
            bug = self._entity_to_event(bug_entity)
            if not bug:
                return {"error": f"Failed to parse bug with ID {bug_id}"}
                
            # Get relationships for this bug
            relationships = await self.knowledge_graph.get_entity_relationships(
                bug_id, 
                project_id=bug.project_id,
                relationship_type="RELATES_TO"
            )
            
            # Process relationships to build history
            fixes = []  # Commits that fixed this bug
            caused_by = []  # What caused this bug
            related_bugs = []  # Related bugs
            
            # Outgoing relationships (this bug -> other)
            for rel in relationships:
                if rel.source_id == bug_id:
                    # Get target entity
                    target = await self.knowledge_graph.get_entity(rel.target_id)
                    if not target:
                        continue
                        
                    target_event = self._entity_to_event(target)
                    if not target_event:
                        continue
                        
                    # Check relationship type
                    rel_type = rel.properties.get("relation_type", "")
                    if rel_type == EventRelationType.CAUSED.value:
                        related_bugs.append({
                            "id": target_event.id,
                            "title": target_event.title,
                            "status": target_event.status,
                            "relationship": "caused_by_this_bug",
                            "confidence": float(rel.properties.get("confidence", 0.0))
                        })
                
            # Incoming relationships (other -> this bug)
            for rel in relationships:
                if rel.target_id == bug_id:
                    # Get source entity
                    source = await self.knowledge_graph.get_entity(rel.source_id)
                    source_event = self._entity_to_event(source) if source else None
                    if not source_event:
                        continue
                        
                    # Check relationship type
                    rel_type = rel.properties.get("relation_type", "")
                    
                    if rel_type == EventRelationType.RESOLVED.value:
                        if source_event.event_type == EventType.COMMIT:
                            fixes.append({
                                "id": source_event.id,
                                "title": source_event.title,
                                "author": source_event.author,
                                "timestamp": source_event.timestamp.isoformat(),
                                "url": source_event.url,
                                "confidence": float(rel.properties.get("confidence", 0.0))
                            })
                    elif rel_type == EventRelationType.CAUSED.value:
                        caused_by.append({
                            "id": source_event.id,
                            "title": source_event.title,
                            "event_type": source_event.event_type,
                            "author": source_event.author,
                            "timestamp": source_event.timestamp.isoformat(),
                            "confidence": float(rel.properties.get("confidence", 0.0))
                        })
                    elif rel_type == EventRelationType.RELATED_TO.value:
                        if source_event.event_type == EventType.ISSUE:
                            related_bugs.append({
                                "id": source_event.id,
                                "title": source_event.title,
                                "status": source_event.status,
                                "relationship": "related",
                                "confidence": float(rel.properties.get("confidence", 0.0))
                            })
            
            # For each fix, check if it caused new bugs
            for fix in fixes:
                fix_id = fix["id"]
                new_bugs = []
                
                # Get relationships for this fix
                fix_rels = await self.knowledge_graph.get_entity_relationships(
                    fix_id,
                    project_id=bug.project_id,
                    relationship_type="RELATES_TO"
                )
                
                for rel in fix_rels:
                    if rel.source_id == fix_id:
                        # Get target entity
                        target = await self.knowledge_graph.get_entity(rel.target_id)
                        if not target:
                            continue
                            
                        target_event = self._entity_to_event(target)
                        if not target_event:
                            continue
                            
                        # Check relationship type
                        rel_type = rel.properties.get("relation_type", "")
                        if rel_type == EventRelationType.CAUSED.value and target_event.event_type == EventType.ISSUE:
                            new_bugs.append({
                                "id": target_event.id,
                                "title": target_event.title,
                                "status": target_event.status,
                                "confidence": float(rel.properties.get("confidence", 0.0))
                            })
                
                # Add new bugs to the fix
                fix["caused_bugs"] = new_bugs
                
            # Build response
            history = {
                "bug": {
                    "id": bug.id,
                    "title": bug.title,
                    "content": bug.content,
                    "status": bug.status,
                    "author": bug.author,
                    "created_at": bug.timestamp.isoformat(),
                    "url": bug.url,
                    "component": bug.component,
                    "labels": bug.labels,
                },
                "fixes": fixes,
                "caused_by": caused_by,
                "related_bugs": related_bugs,
            }
            
            return history
            
        except Exception as e:
            logger.error(f"Error querying bug history: {str(e)}")
            return {"error": str(e)}
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the ML processor.
        
        Returns:
            Dictionary with metrics
        """
        current_time = datetime.now(timezone.utc)
        uptime_seconds = (current_time - self.metrics["start_time"]).total_seconds()
        
        return {
            **self.metrics,
            "uptime_seconds": uptime_seconds,
            "events_per_hour": self.metrics["events_processed"] / (uptime_seconds / 3600) if uptime_seconds > 0 else 0,
            "cache_size": len(self._recent_events_cache),
            "current_time": current_time.isoformat(),
        }
    
    async def suggest_fixes(self, bug_id: str) -> Dict[str, Any]:
        """
        Suggest fixes for a bug based on similar bugs and their solutions.
        
        Args:
            bug_id: ID of the bug to suggest fixes for
            
        Returns:
            Dictionary with suggestions
        """
        try:
            # Get the bug entity
            bug_entity = await self.knowledge_graph.get_entity(bug_id)
            if not bug_entity or bug_entity.type != "event":
                return {"error": f"Bug with ID {bug_id} not found"}
                
            # Convert to event
            bug = self._entity_to_event(bug_entity)
            if not bug:
                return {"error": f"Failed to parse bug with ID {bug_id}"}
                
            # Get embedding for the bug
            if not bug.embedding:
                content_to_embed = f"{bug.title} {bug.content or ''}"
                embeddings = await self.embedding_service.embed_documents([content_to_embed])
                if embeddings:
                    bug.embedding = embeddings[0]
                else:
                    return {"error": "Failed to generate embedding for bug"}
                    
            # Find similar bugs
            similar_bugs = await self._find_similar_bugs(bug)
            
            # Get fixes for similar bugs
            fixes = []
            for similar_bug in similar_bugs:
                bug_fixes = await self._get_bug_fixes(similar_bug["id"])
                for fix in bug_fixes:
                    fixes.append({
                        **fix,
                        "fixed_bug_id": similar_bug["id"],
                        "fixed_bug_title": similar_bug["title"],
                        "similarity": similar_bug["similarity"]
                    })
                    
            # Sort fixes by similarity * confidence
            fixes.sort(key=lambda x: x["similarity"] * x.get("confidence", 0.5), reverse=True)
                    
            # Generate fix suggestion using LLM
            suggestion = await self._generate_fix_suggestion(bug, similar_bugs, fixes[:5])
                
            return {
                "bug": {
                    "id": bug.id,
                    "title": bug.title,
                    "content": bug.content,
                    "status": bug.status,
                },
                "similar_bugs": similar_bugs,
                "previous_fixes": fixes,
                "suggestion": suggestion
            }
            
        except Exception as e:
            logger.error(f"Error generating fix suggestions: {str(e)}")
            return {"error": str(e)}
            
    async def _find_similar_bugs(self, bug: IntegrationEvent, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find bugs similar to the given bug.
        
        Args:
            bug: The bug to find similar bugs for
            limit: Maximum number of similar bugs to return
            
        Returns:
            List of similar bugs
        """
        if not bug.embedding:
            return []
            
        # Query knowledge graph for similar bugs
        similar_entities = await self.knowledge_graph.search_entities_by_vector(
            embedding=bug.embedding,
            limit=limit * 2,  # Get more to filter
            filters={
                "event_type": EventType.ISSUE.value,
                "type": "event"
            },
            project_id=bug.project_id
        )
        
        # Filter out the current bug
        similar_entities = [e for e in similar_entities if e[0].id != bug.id]
        
        # Convert to events
        similar_bugs = []
        for entity, score in similar_entities:
            event = self._entity_to_event(entity)
            if event:
                similar_bugs.append({
                    "id": event.id,
                    "title": event.title,
                    "content": event.content,
                    "status": event.status,
                    "created_at": event.timestamp.isoformat(),
                    "similarity": score
                })
                
        # Sort by similarity and limit
        similar_bugs.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_bugs[:limit]
    
    async def _get_bug_fixes(self, bug_id: str) -> List[Dict[str, Any]]:
        """
        Get fixes for a bug.
        
        Args:
            bug_id: ID of the bug to get fixes for
            
        Returns:
            List of fixes
        """
        # Get relationships for this bug
        relationships = await self.knowledge_graph.get_entity_relationships(
            bug_id, 
            relationship_type="RELATES_TO"
        )
        
        fixes = []
        # Look for incoming RESOLVED relationships
        for rel in relationships:
            if rel.target_id == bug_id:
                # Get source entity
                source = await self.knowledge_graph.get_entity(rel.source_id)
                if not source:
                    continue
                        
                source_event = self._entity_to_event(source)
                if not source_event or source_event.event_type != EventType.COMMIT:
                    continue
                        
                fixes.append({
                    "id": source_event.id,
                    "title": source_event.title,
                    "content": source_event.content,
                    "author": source_event.author,
                    "timestamp": source_event.timestamp.isoformat(),
                    "url": source_event.url,
                    "confidence": float(rel.properties.get("confidence", 0.0))
                })
                    
        return fixes
    
    async def _generate_fix_suggestion(
        self, 
        bug: IntegrationEvent, 
        similar_bugs: List[Dict[str, Any]], 
        fixes: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a fix suggestion for a bug using LLM.
        
        Args:
            bug: The bug to suggest a fix for
            similar_bugs: List of similar bugs
            fixes: List of fixes for similar bugs
            
        Returns:
            Suggestion text
        """
        try:
            # Construct prompt with context
            similar_bugs_context = ""
            for i, similar_bug in enumerate(similar_bugs[:3]):
                similar_bugs_context += f"\nSimilar Bug {i+1} (similarity: {similar_bug['similarity']:.2f}):\nTitle: {similar_bug['title']}\nDescription: {similar_bug['content']}\n"
                
            fixes_context = ""
            for i, fix in enumerate(fixes[:3]):
                fixes_context += f"\nFix {i+1} (for bug: {fix.get('fixed_bug_title', 'Unknown')}):\nCommit Message: {fix['title']}\nChanges: {fix['content']}\n"
                
            prompt = f"""
You are an expert software developer. Your task is to suggest a fix for the following bug based on similar bugs and their fixes:

Bug to Fix:
Title: {bug.title}
Description: {bug.content or "No description available"}
Status: {bug.status or "Unknown"}
Component: {bug.component or "Unknown"}
Labels: {', '.join(bug.labels) if bug.labels else "None"}

Similar Bugs and Their Fixes:
{similar_bugs_context}

Previous Fixes:
{fixes_context}

Based on this information, suggest a detailed fix for the current bug. Include:
1. Root cause analysis
2. Suggested code changes (pseudocode or actual code if possible)
3. Testing recommendations
4. Potential side effects or other issues to watch out for

Your suggestion:
"""
            
            # Call LLM for suggestion
            response = await llm.complete(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000,
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating fix suggestion: {str(e)}")
            return f"Failed to generate suggestion: {str(e)}"

    #
    # Anomaly Detection Features
    #
    
    async def detect_anomalies(self, project_id: str, timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Detect anomalies in integration data for a project.
        
        Args:
            project_id: ID of the project to analyze
            timeframe_days: Number of days to analyze
            
        Returns:
            Dictionary with detected anomalies
        """
        try:
            # Get start and end times for analysis period
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=timeframe_days)
            
            # Get all events for the project in the timeframe
            events = await self._get_events_in_timeframe(project_id, start_time, end_time)
            if not events:
                return {"anomalies": [], "message": "No events found in the specified timeframe"}
                
            # Calculate baselines
            baselines = await self._calculate_baselines(events)
            
            # Detect anomalies
            commit_anomalies = await self._detect_commit_anomalies(events, baselines)
            issue_anomalies = await self._detect_issue_anomalies(events, baselines)
            deployment_anomalies = await self._detect_deployment_anomalies(events, baselines)
            messaging_anomalies = await self._detect_messaging_anomalies(events, baselines)
            
            # Combine anomalies
            all_anomalies = commit_anomalies + issue_anomalies + deployment_anomalies + messaging_anomalies
            
            # Sort by severity (descending)
            all_anomalies.sort(key=lambda a: a["severity"], reverse=True)
            
            return {
                "anomalies": all_anomalies,
                "total_count": len(all_anomalies),
                "high_severity_count": len([a for a in all_anomalies if a["severity"] >= 0.8]),
                "medium_severity_count": len([a for a in all_anomalies if 0.4 <= a["severity"] < 0.8]),
                "low_severity_count": len([a for a in all_anomalies if a["severity"] < 0.4]),
                "analysis_period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "days": timeframe_days,
                },
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return {"error": str(e)}
            
    async def _get_events_in_timeframe(
        self, 
        project_id: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[IntegrationEvent]:
        """
        Get all events for a project within a specific timeframe.
        
        Args:
            project_id: ID of the project
            start_time: Start of the timeframe
            end_time: End of the timeframe
            
        Returns:
            List of events
        """
        # Query knowledge graph for events in the timeframe
        query_results = await self.knowledge_graph.query(
            f"""
            MATCH (e:Event)
            WHERE e.project_id = '{project_id}'
            AND e.timestamp >= '{start_time.isoformat()}'
            AND e.timestamp <= '{end_time.isoformat()}'
            RETURN e
            ORDER BY e.timestamp ASC
            """
        )
        
        # Convert to events
        events = []
        for result in query_results:
            entity = result.get("e")
            if entity:
                event = self._entity_to_event(entity)
                if event:
                    events.append(event)
                    
        return events
        
    async def _calculate_baselines(self, events: List[IntegrationEvent]) -> Dict[str, Any]:
        """
        Calculate baseline metrics from events.
        
        Args:
            events: List of events to analyze
            
        Returns:
            Dictionary with baseline metrics
        """
        # Group events by type
        events_by_type = {}
        for event in events:
            event_type = event.event_type.value
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append(event)
            
        # Group by day to calculate daily averages
        events_by_day = {}
        for event in events:
            day = event.timestamp.date().isoformat()
            if day not in events_by_day:
                events_by_day[day] = {}
            
            event_type = event.event_type.value
            if event_type not in events_by_day[day]:
                events_by_day[day][event_type] = []
                
            events_by_day[day][event_type].append(event)
            
        # Calculate daily averages
        daily_averages = {}
        for event_type in events_by_type.keys():
            daily_counts = [len(events_by_day[day].get(event_type, [])) for day in events_by_day]
            if daily_counts:
                daily_averages[event_type] = {
                    "mean": statistics.mean(daily_counts) if daily_counts else 0,
                    "median": statistics.median(daily_counts) if daily_counts else 0,
                    "stdev": statistics.stdev(daily_counts) if len(daily_counts) > 1 else 0,
                    "max": max(daily_counts) if daily_counts else 0,
                    "min": min(daily_counts) if daily_counts else 0,
                }
            
        # Calculate timing metrics for issues
        issue_resolution_times = []
        for issue in events_by_type.get(EventType.ISSUE.value, []):
            # Skip open issues
            if issue.status and issue.status.lower() not in ["closed", "resolved", "done", "completed", "fixed"]:
                continue
                
            # Get related events to find resolution time
            related = await self.knowledge_graph.get_entity_relationships(
                issue.id, relationship_type="RELATES_TO")
            
            # Find resolution time
            for rel in related:
                if rel.target_id == issue.id:
                    source = await self.knowledge_graph.get_entity(rel.source_id)
                    source_event = self._entity_to_event(source) if source else None
                    if source_event and rel.properties.get("relation_type") == EventRelationType.RESOLVED.value:
                        resolution_time = (source_event.timestamp - issue.timestamp).total_seconds()
                        issue_resolution_times.append(resolution_time)
                        break
        
        # Calculate issue resolution metrics
        issue_metrics = {}
        if issue_resolution_times:
            issue_metrics = {
                "mean_resolution_time": statistics.mean(issue_resolution_times),
                "median_resolution_time": statistics.median(issue_resolution_times),
                "min_resolution_time": min(issue_resolution_times),
                "max_resolution_time": max(issue_resolution_times),
                "stdev_resolution_time": statistics.stdev(issue_resolution_times) if len(issue_resolution_times) > 1 else 0,
            }
            
        return {
            "daily_averages": daily_averages,
            "issue_metrics": issue_metrics,
            "total_events": len(events),
            "events_by_type": {k: len(v) for k, v in events_by_type.items()},
        }
        
    async def _detect_commit_anomalies(
        self, 
        events: List[IntegrationEvent], 
        baselines: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in commit patterns.
        
        Args:
            events: List of events to analyze
            baselines: Baseline metrics
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Extract commit events
        commits = [e for e in events if e.event_type == EventType.COMMIT]
        if not commits:
            return anomalies
            
        # Group commits by author
        commits_by_author = {}
        for commit in commits:
            author = commit.author or "unknown"
            if author not in commits_by_author:
                commits_by_author[author] = []
            commits_by_author[author].append(commit)
            
        # Group commits by day
        commits_by_day = {}
        for commit in commits:
            day = commit.timestamp.date().isoformat()
            if day not in commits_by_day:
                commits_by_day[day] = []
            commits_by_day[day].append(commit)
            
        # Detect unusual daily commit volumes
        daily_commit_baseline = baselines["daily_averages"].get(EventType.COMMIT.value, {})
        if daily_commit_baseline:
            mean = daily_commit_baseline.get("mean", 0)
            stdev = daily_commit_baseline.get("stdev", 0)
            
            for day, day_commits in commits_by_day.items():
                # Skip days with zero or few commits
                if len(day_commits) < 3:
                    continue
                    
                # Check for unusually high commit volume
                if stdev > 0:
                    z_score = (len(day_commits) - mean) / stdev
                    if z_score > 2:  # More than 2 standard deviations above mean
                        # Get the most active author that day
                        author_counts = {}
                        for commit in day_commits:
                            author = commit.author or "unknown"
                            author_counts[author] = author_counts.get(author, 0) + 1
                        most_active = max(author_counts.items(), key=lambda x: x[1])
                        
                        anomalies.append({
                            "type": "high_commit_volume",
                            "day": day,
                            "commit_count": len(day_commits),
                            "expected_count": mean,
                            "z_score": z_score,
                            "most_active_author": most_active[0],
                            "most_active_author_commits": most_active[1],
                            "severity": min(0.9, 0.5 + (0.1 * z_score)),
                            "description": f"Unusually high commit volume detected on {day}. {len(day_commits)} commits were made, which is {z_score:.1f} standard deviations above the mean."
                        })
        
        # Detect unusual commit sizes
        commit_sizes = []
        for commit in commits:
            # Estimate commit size from metadata or content
            size = 0
            if commit.metadata.get("files"):
                size = len(commit.metadata["files"])
            elif commit.metadata.get("stats"):
                stats = commit.metadata["stats"]
                if isinstance(stats, dict):
                    size = stats.get("total", 0)
            
            if size > 0:
                commit_sizes.append((commit, size))
                
        if commit_sizes:
            # Calculate mean and standard deviation
            sizes = [s[1] for s in commit_sizes]
            mean_size = statistics.mean(sizes)
            stdev_size = statistics.stdev(sizes) if len(sizes) > 1 else 0
            
            # Detect unusually large commits
            for commit, size in commit_sizes:
                if stdev_size > 0:
                    z_score = (size - mean_size) / stdev_size
                    if z_score > 3:  # More than 3 standard deviations
                        anomalies.append({
                            "type": "unusually_large_commit",
                            "commit_id": commit.id,
                            "commit_title": commit.title,
                            "author": commit.author,
                            "timestamp": commit.timestamp.isoformat(),
                            "size": size,
                            "expected_size": mean_size,
                            "z_score": z_score,
                            "severity": min(0.95, 0.6 + (0.1 * z_score)),
                            "description": f"Unusually large commit detected: '{commit.title}' by {commit.author}. The commit modified {size} files, which is {z_score:.1f} standard deviations above the mean."
                        })
                        
        return anomalies
        
    async def _detect_issue_anomalies(
        self, 
        events: List[IntegrationEvent], 
        baselines: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in issue patterns.
        
        Args:
            events: List of events to analyze
            baselines: Baseline metrics
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Extract issue events
        issues = [e for e in events if e.event_type == EventType.ISSUE]
        if not issues:
            return anomalies
            
        # Detect components with unusually high issue rates
        components = {}
        for issue in issues:
            component = issue.component or "unknown"
            if component not in components:
                components[component] = []
            components[component].append(issue)
            
        # Skip if only one component or too few issues
        if len(components) <= 1 or len(issues) < 5:
            return anomalies
            
        # Calculate mean issues per component
        component_counts = [len(issues) for _, issues in components.items()]
        mean_count = statistics.mean(component_counts)
        stdev_count = statistics.stdev(component_counts) if len(component_counts) > 1 else 0
        
        # Find components with unusually high issue counts
        for component, component_issues in components.items():
            if component == "unknown" or stdev_count == 0:
                continue
                
            z_score = (len(component_issues) - mean_count) / stdev_count
            if z_score > 1.5:  # More than 1.5 standard deviations
                # Calculate what percentage of total issues this represents
                percentage = len(component_issues) / len(issues) * 100
                
                if percentage > 15:  # Only flag if significant percentage
                    anomalies.append({
                        "type": "high_issue_component",
                        "component": component,
                        "issue_count": len(component_issues),
                        "expected_count": mean_count,
                        "percentage_of_total": percentage,
                        "z_score": z_score,
                        "severity": min(0.9, 0.4 + (0.1 * z_score) + (percentage / 100)),
                        "description": f"Component '{component}' has an unusually high issue count ({len(component_issues)}, {percentage:.1f}% of all issues), which is {z_score:.1f} standard deviations above the mean."
                    })
        
        # Detect unusual resolution time issues
        issue_metrics = baselines.get("issue_metrics", {})
        if not issue_metrics:
            return anomalies
            
        mean_resolution_time = issue_metrics.get("mean_resolution_time", 0)
        stdev_resolution_time = issue_metrics.get("stdev_resolution_time", 0)
        
        if mean_resolution_time == 0 or stdev_resolution_time == 0:
            return anomalies
            
        for issue in issues:
            # Skip open issues
            if issue.status and issue.status.lower() not in ["closed", "resolved", "done", "completed", "fixed"]:
                continue
                
            # Get related events to find resolution time
            related = await self.knowledge_graph.get_entity_relationships(
                issue.id, relationship_type="RELATES_TO")
            
            # Find resolution time
            for rel in related:
                if rel.target_id == issue.id:
                    source = await self.knowledge_graph.get_entity(rel.source_id)
                    source_event = self._entity_to_event(source) if source else None
                    if source_event and rel.properties.get("relation_type") == EventRelationType.RESOLVED.value:
                        resolution_time = (source_event.timestamp - issue.timestamp).total_seconds()
                        
                        # Check if unusually long resolution time
                        z_score = (resolution_time - mean_resolution_time) / stdev_resolution_time
                        if z_score > 2:  # More than 2 standard deviations
                            # Convert to hours for readability
                            resolution_hours = resolution_time / 3600
                            mean_hours = mean_resolution_time / 3600
                            
                            anomalies.append({
                                "type": "long_resolution_time",
                                "issue_id": issue.id,
                                "issue_title": issue.title,
                                "resolution_time_hours": resolution_hours,
                                "expected_time_hours": mean_hours,
                                "z_score": z_score,
                                "severity": min(0.85, 0.4 + (0.1 * z_score)),
                                "description": f"Issue '{issue.title}' took unusually long to resolve ({resolution_hours:.1f} hours), which is {z_score:.1f} standard deviations above the mean."
                            })
                        break
                        
        return anomalies
        
    async def _detect_deployment_anomalies(
        self, 
        events: List[IntegrationEvent], 
        baselines: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in deployment patterns.
        
        Args:
            events: List of events to analyze
            baselines: Baseline metrics
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Extract deployment events
        deployments = [e for e in events if e.event_type == EventType.DEPLOYMENT]
        if not deployments:
            return anomalies
            
        # Calculate time between deployments
        if len(deployments) < 3:  # Need at least a few deployments
            return anomalies
            
        # Sort by timestamp
        sorted_deployments = sorted(deployments, key=lambda d: d.timestamp)
        
        # Calculate time differences
        time_diffs = []
        for i in range(1, len(sorted_deployments)):
            diff = (sorted_deployments[i].timestamp - sorted_deployments[i-1].timestamp).total_seconds()
            time_diffs.append(diff)
            
        # Calculate mean and standard deviation
        mean_diff = statistics.mean(time_diffs)
        stdev_diff = statistics.stdev(time_diffs) if len(time_diffs) > 1 else 0
        
        if stdev_diff == 0:
            return anomalies
            
        # Detect unusually rapid deployments
        for i in range(1, len(sorted_deployments)):
            diff = (sorted_deployments[i].timestamp - sorted_deployments[i-1].timestamp).total_seconds()
            
            # Detect unusually short time between deployments
            if diff < (mean_diff / 2) and len(time_diffs) > 3:
                z_score = (mean_diff - diff) / stdev_diff
                if z_score > 1.5:  # Significant deviation
                    # Convert to hours for readability
                    diff_hours = diff / 3600
                    mean_diff_hours = mean_diff / 3600
                    
                    anomalies.append({
                        "type": "rapid_deployment",
                        "deployment_id": sorted_deployments[i].id,
                        "deployment_title": sorted_deployments[i].title,
                        "previous_deployment_id": sorted_deployments[i-1].id,
                        "time_since_previous_hours": diff_hours,
                        "average_time_between_hours": mean_diff_hours,
                        "z_score": z_score,
                        "timestamp": sorted_deployments[i].timestamp.isoformat(),
                        "severity": min(0.75, 0.3 + (0.1 * z_score)),
                        "description": f"Unusually rapid deployment detected. Only {diff_hours:.1f} hours between deployments, compared to an average of {mean_diff_hours:.1f} hours."
                    })
                    
        # Detect deployments with unusually high commit counts
        commit_counts = []
        deployment_commits = []
        
        for deployment in deployments:
            # Find related commits
            related = await self.knowledge_graph.get_entity_relationships(
                deployment.id, relationship_type="RELATES_TO")
            
            # Count commits for this deployment
            commits = []
            for rel in related:
                if rel.source_id == deployment.id:
                    target = await self.knowledge_graph.get_entity(rel.target_id)
                    target_event = self._entity_to_event(target) if target else None
                    if target_event and rel.properties.get("relation_type") == EventRelationType.CAUSED.value:
                        commits.append(target_event)
                        
            commit_counts.append(len(commits))
            deployment_commits.append((deployment, len(commits)))
            
        if not commit_counts or len(commit_counts) < 3:
            return anomalies
            
        # Calculate mean and standard deviation
        mean_commits = statistics.mean(commit_counts)
        stdev_commits = statistics.stdev(commit_counts) if len(commit_counts) > 1 else 0
        
        if stdev_commits == 0:
            return anomalies
            
        # Detect deployments with unusually high commit counts
        for deployment, count in deployment_commits:
            z_score = (count - mean_commits) / stdev_commits
            if z_score > 2:  # More than 2 standard deviations
                anomalies.append({
                    "type": "large_deployment",
                    "deployment_id": deployment.id,
                    "deployment_title": deployment.title,
                    "commit_count": count,
                    "average_commit_count": mean_commits,
                    "z_score": z_score,
                    "timestamp": deployment.timestamp.isoformat(),
                    "severity": min(0.8, 0.4 + (0.1 * z_score)),
                    "description": f"Unusually large deployment detected. Deployment '{deployment.title}' contained {count} commits, which is {z_score:.1f} standard deviations above the mean."
                })
                
        return anomalies
        
    async def _detect_messaging_anomalies(
        self, 
        events: List[IntegrationEvent], 
        baselines: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in messaging patterns (e.g., Slack).
        
        Args:
            events: List of events to analyze
            baselines: Baseline metrics
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Extract message events (e.g., from Slack)
        messages = [e for e in events if e.event_type == EventType.MESSAGE]
        if not messages or len(messages) < 10:  # Need a reasonable number of messages
            return anomalies
            
        # Group messages by channel/conversation
        messages_by_channel = {}
        for message in messages:
            # Get channel from metadata
            channel = message.metadata.get("channel", "unknown")
            if channel not in messages_by_channel:
                messages_by_channel[channel] = []
            messages_by_channel[channel].append(message)
            
        # Detect spikes in message activity
        # Group by day and channel
        daily_channel_counts = {}
        for channel, channel_messages in messages_by_channel.items():
            for message in channel_messages:
                day = message.timestamp.date().isoformat()
                key = (day, channel)
                if key not in daily_channel_counts:
                    daily_channel_counts[key] = 0
                daily_channel_counts[key] += 1
                
        # Calculate baselines for each channel
        channel_baselines = {}
        for (day, channel), count in daily_channel_counts.items():
            if channel not in channel_baselines:
                channel_baselines[channel] = []
            channel_baselines[channel].append(count)
            
        # Calculate stats for each channel
        for channel, counts in channel_baselines.items():
            if len(counts) < 3:  # Need at least a few data points
                continue
                
            mean = statistics.mean(counts)
            stdev = statistics.stdev(counts) if len(counts) > 1 else 0
            
            if stdev == 0:
                continue
                
            # Check for spikes
            for (day, ch), count in daily_channel_counts.items():
                if ch != channel:
                    continue
                    
                z_score = (count - mean) / stdev
                if z_score > 2:  # More than 2 standard deviations
                    anomalies.append({
                        "type": "message_spike",
                        "channel": channel,
                        "day": day,
                        "message_count": count,
                        "average_count": mean,
                        "z_score": z_score,
                        "severity": min(0.7, 0.3 + (0.1 * z_score)),
                        "description": f"Unusual messaging activity detected in channel '{channel}' on {day}. {count} messages were sent, which is {z_score:.1f} standard deviations above the mean."
                    })
                    
        # Detect sentiment anomalies if sentiment data is available
        sentiment_messages = [m for m in messages if "sentiment" in m.metadata]
        if sentiment_messages and len(sentiment_messages) >= 5:
            # Calculate baseline sentiment
            sentiments = [float(m.metadata["sentiment"]) for m in sentiment_messages 
                        if isinstance(m.metadata["sentiment"], (int, float, str)) and 
                        str(m.metadata["sentiment"]).replace(".", "", 1).replace("-", "", 1).isdigit()]
            
            if sentiments:
                mean_sentiment = statistics.mean(sentiments)
                stdev_sentiment = statistics.stdev(sentiments) if len(sentiments) > 1 else 0
                
                if stdev_sentiment > 0:
                    # Group by channel for sentiment analysis
                    channel_sentiments = {}
                    for message in sentiment_messages:
                        channel = message.metadata.get("channel", "unknown")
                        if channel not in channel_sentiments:
                            channel_sentiments[channel] = []
                            
                        # Convert to float and validate
                        sentiment = message.metadata["sentiment"]
                        if isinstance(sentiment, (int, float)) or (isinstance(sentiment, str) and sentiment.replace(".", "", 1).replace("-", "", 1).isdigit()):
                            channel_sentiments[channel].append(float(sentiment))
                    
                    # Detect channels with unusually negative sentiment
                    for channel, ch_sentiments in channel_sentiments.items():
                        if len(ch_sentiments) < 5:  # Need enough messages
                            continue
                            
                        channel_mean = statistics.mean(ch_sentiments)
                        # Is this channel significantly more negative than the overall average?
                        z_score = (mean_sentiment - channel_mean) / stdev_sentiment
                        if z_score > 1.5:  # More negative than normal
                            # Calculate what percentage of total messages this represents
                            percentage = len(ch_sentiments) / len(sentiment_messages) * 100
                            
                            anomalies.append({
                                "type": "negative_sentiment",
                                "channel": channel,
                                "average_sentiment": channel_mean,
                                "overall_average_sentiment": mean_sentiment,
                                "z_score": z_score,
                                "message_count": len(ch_sentiments),
                                "percentage_of_total": percentage,
                                "severity": min(0.85, 0.4 + (0.1 * z_score)),
                                "description": f"Unusually negative sentiment detected in channel '{channel}'. The average sentiment is {channel_mean:.2f}, which is {z_score:.1f} standard deviations below the overall average."
                            })
                
        return anomalies

    #
    # Developer Productivity Analytics
    #
    
    async def analyze_developer_productivity(
        self,
        project_id: str,
        timeframe_days: int = 30,
        developer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze developer productivity metrics within a project.
        
        Args:
            project_id: ID of the project to analyze
            timeframe_days: Number of days to analyze
            developer_id: Optional developer ID to filter by
            
        Returns:
            Dictionary with developer productivity metrics
        """
        try:
            # Get start and end times for analysis period
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=timeframe_days)
            
            # Get all events for the project in the timeframe
            events = await self._get_events_in_timeframe(project_id, start_time, end_time)
            if not events:
                return {"message": "No events found in the specified timeframe"}
                
            # Filter by developer if specified
            if developer_id:
                events = [e for e in events if e.author and developer_id.lower() in e.author.lower()]
                if not events:
                    return {"message": f"No events found for developer {developer_id} in the specified timeframe"}
            
            # Calculate metrics
            metrics = await self._calculate_productivity_metrics(events, start_time, end_time)
            
            # Add analysis parameters
            metrics["analysis_parameters"] = {
                "project_id": project_id,
                "developer_id": developer_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "timeframe_days": timeframe_days
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing developer productivity: {str(e)}")
            return {"error": str(e)}
    
    async def _calculate_productivity_metrics(
        self,
        events: List[IntegrationEvent],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Calculate productivity metrics from events.
        
        Args:
            events: List of events to analyze
            start_time: Start of analysis period
            end_time: End of analysis period
            
        Returns:
            Dictionary with productivity metrics
        """
        # Initialize metrics
        metrics = {
            "developers": {},
            "teams": {},
            "components": {},
            "overall": {
                "event_count": len(events),
                "active_developers": 0,
                "most_active_time_of_day": None,
                "least_active_time_of_day": None,
                "velocity": {},
                "bottlenecks": [],
                "impact_scores": {}
            }
        }
        
        # Group events by author
        events_by_author = {}
        for event in events:
            author = event.author or "unknown"
            if author not in events_by_author:
                events_by_author[author] = []
            events_by_author[author].append(event)
        
        # Count active developers (excluding unknown)
        active_devs = [author for author in events_by_author.keys() if author != "unknown"]
        metrics["overall"]["active_developers"] = len(active_devs)
        
        # Calculate metrics for each developer
        for author, author_events in events_by_author.items():
            if author == "unknown":
                continue
                
            # Initialize developer metrics
            metrics["developers"][author] = {
                "event_count": len(author_events),
                "event_types": {},
                "commit_stats": {
                    "count": 0,
                    "avg_size": 0,
                    "total_lines": 0
                },
                "issue_stats": {
                    "created": 0,
                    "resolved": 0,
                    "avg_resolution_time": 0
                },
                "components_worked_on": set(),
                "activity_hours": {},
                "collaboration_score": 0,
                "impact_score": 0
            }
            
            # Process events by type
            commits = []
            issues_created = []
            issues_resolved = []
            
            for event in author_events:
                # Count by event type
                event_type = event.event_type.value
                if event_type not in metrics["developers"][author]["event_types"]:
                    metrics["developers"][author]["event_types"][event_type] = 0
                metrics["developers"][author]["event_types"][event_type] += 1
                
                # Track components
                if event.component:
                    metrics["developers"][author]["components_worked_on"].add(event.component)
                
                # Track activity hours
                hour = event.timestamp.hour
                if hour not in metrics["developers"][author]["activity_hours"]:
                    metrics["developers"][author]["activity_hours"][hour] = 0
                metrics["developers"][author]["activity_hours"][hour] += 1
                
                # Process specific event types
                if event.event_type == EventType.COMMIT:
                    commits.append(event)
                elif event.event_type == EventType.ISSUE:
                    issues_created.append(event)
            
            # Find issues resolved by this developer
            for issue in [e for e in events if e.event_type == EventType.ISSUE]:
                related = await self.knowledge_graph.get_entity_relationships(
                    issue.id, relationship_type="RELATES_TO")
                
                for rel in related:
                    if rel.target_id == issue.id:
                        source = await self.knowledge_graph.get_entity(rel.source_id)
                        source_event = self._entity_to_event(source) if source else None
                        if (source_event and 
                            source_event.author == author and
                            rel.properties.get("relation_type") == EventRelationType.RESOLVED.value):
                            issues_resolved.append((issue, source_event))
            
            # Compute commit stats
            if commits:
                metrics["developers"][author]["commit_stats"]["count"] = len(commits)
                
                total_lines = 0
                commits_with_size = 0
                
                for commit in commits:
                    size = 0
                    if commit.metadata.get("stats"):
                        stats = commit.metadata["stats"]
                        if isinstance(stats, dict):
                            additions = stats.get("additions", 0)
                            deletions = stats.get("deletions", 0)
                            size = additions + deletions
                    
                    if size > 0:
                        total_lines += size
                        commits_with_size += 1
                
                metrics["developers"][author]["commit_stats"]["total_lines"] = total_lines
                if commits_with_size > 0:
                    metrics["developers"][author]["commit_stats"]["avg_size"] = total_lines / commits_with_size
                    
            # Compute issue stats
            metrics["developers"][author]["issue_stats"]["created"] = len(issues_created)
            metrics["developers"][author]["issue_stats"]["resolved"] = len(issues_resolved)
            
            if issues_resolved:
                resolution_times = []
                for issue, resolve_event in issues_resolved:
                    time_diff = (resolve_event.timestamp - issue.timestamp).total_seconds()
                    resolution_times.append(time_diff)
                
                avg_time = sum(resolution_times) / len(resolution_times)
                metrics["developers"][author]["issue_stats"]["avg_resolution_time"] = avg_time
                
            # Convert component set to list for JSON serialization
            metrics["developers"][author]["components_worked_on"] = list(
                metrics["developers"][author]["components_worked_on"])
                
            # Calculate impact score
            commits_weight = 0.5
            issues_weight = 0.3
            components_weight = 0.2
            
            commit_count = metrics["developers"][author]["commit_stats"]["count"]
            issues_resolved_count = metrics["developers"][author]["issue_stats"]["resolved"]
            components_count = len(metrics["developers"][author]["components_worked_on"])
            
            impact_score = (
                (commit_count * commits_weight) +
                (issues_resolved_count * issues_weight) +
                (components_count * components_weight)
            )
            
            metrics["developers"][author]["impact_score"] = impact_score
            metrics["overall"]["impact_scores"][author] = impact_score
        
        # Calculate team-level metrics by component
        components = {}
        for event in events:
            component = event.component or "unknown"
            if component not in components:
                components[component] = []
            components[component].append(event)
        
        # Process component metrics
        for component, component_events in components.items():
            if component == "unknown":
                continue
                
            # Initialize component metrics
            metrics["components"][component] = {
                "event_count": len(component_events),
                "active_developers": set(),
                "issue_count": 0,
                "commit_count": 0,
                "avg_resolution_time": 0,
                "health_score": 0,
                "bottleneck_score": 0
            }
            
            # Process events
            issues = []
            commits = []
            resolution_times = []
            
            for event in component_events:
                if event.author:
                    metrics["components"][component]["active_developers"].add(event.author)
                    
                if event.event_type == EventType.ISSUE:
                    issues.append(event)
                    # Find resolution time if available
                    related = await self.knowledge_graph.get_entity_relationships(
                        event.id, relationship_type="RELATES_TO")
                    
                    for rel in related:
                        if rel.target_id == event.id:
                            source = await self.knowledge_graph.get_entity(rel.source_id)
                            source_event = self._entity_to_event(source) if source else None
                            if source_event and rel.properties.get("relation_type") == EventRelationType.RESOLVED.value:
                                resolution_time = (source_event.timestamp - event.timestamp).total_seconds()
                                resolution_times.append(resolution_time)
                                break
                    
                elif event.event_type == EventType.COMMIT:
                    commits.append(event)
            
            # Update metrics
            metrics["components"][component]["issue_count"] = len(issues)
            metrics["components"][component]["commit_count"] = len(commits)
            
            # Convert developer set to list for JSON serialization
            metrics["components"][component]["active_developers"] = list(
                metrics["components"][component]["active_developers"])
            
            # Calculate average resolution time
            if resolution_times:
                avg_time = sum(resolution_times) / len(resolution_times)
                metrics["components"][component]["avg_resolution_time"] = avg_time
                
            # Calculate health score (lower resolution time is better)
            issue_ratio = len(issues) / max(1, len(component_events))
            dev_count = len(metrics["components"][component]["active_developers"])
            
            # More developers and lower issue ratio is healthier
            health_score = (0.7 * (1 - issue_ratio)) + (0.3 * min(1.0, dev_count / 5))
            metrics["components"][component]["health_score"] = health_score
            
            # Calculate bottleneck score
            # High resolution time and high issue ratio indicates bottleneck
            if resolution_times:
                avg_resolution_hours = metrics["components"][component]["avg_resolution_time"] / 3600
                # Normalize to 0-1 range (assuming >1 week is very bad)
                normalized_time = min(1.0, avg_resolution_hours / (24 * 7))
                bottleneck_score = (0.6 * normalized_time) + (0.4 * issue_ratio)
                
                metrics["components"][component]["bottleneck_score"] = bottleneck_score
                
                # Add to overall bottlenecks if score is high
                if bottleneck_score > 0.6:
                    metrics["overall"]["bottlenecks"].append({
                        "component": component,
                        "bottleneck_score": bottleneck_score,
                        "avg_resolution_time_hours": avg_resolution_hours,
                        "issue_count": len(issues),
                        "active_developers": len(metrics["components"][component]["active_developers"])
                    })
        
        # Calculate overall velocity
        # Group by week
        weekly_events = {}
        total_days = (end_time - start_time).days
        weeks = max(1, total_days // 7)
        
        for event in events:
            # Calculate week number from start_time
            days_since_start = (event.timestamp - start_time).days
            week_num = min(weeks - 1, max(0, days_since_start // 7))
            week_key = f"week_{week_num + 1}"
            
            if week_key not in weekly_events:
                weekly_events[week_key] = {
                    "commits": 0,
                    "issues_created": 0,
                    "issues_resolved": 0,
                    "start_date": (start_time + timedelta(days=week_num * 7)).date().isoformat(),
                    "end_date": (start_time + timedelta(days=min(total_days, (week_num + 1) * 7 - 1))).date().isoformat()
                }
            
            # Count by event type
            if event.event_type == EventType.COMMIT:
                weekly_events[week_key]["commits"] += 1
            elif event.event_type == EventType.ISSUE:
                weekly_events[week_key]["issues_created"] += 1
                
            # Check if any issues were resolved this week
            if event.event_type == EventType.ISSUE:
                related = await self.knowledge_graph.get_entity_relationships(
                    event.id, relationship_type="RELATES_TO")
                
                for rel in related:
                    if rel.target_id == event.id:
                        source = await self.knowledge_graph.get_entity(rel.source_id)
                        if not source:
                            continue
                                        
                        source_event = self._entity_to_event(source) if source else None
                        if (source_event and 
                            rel.properties.get("relation_type") == EventRelationType.RESOLVED.value):
                            # Check if resolution happened in this week
                            days_since_start = (source_event.timestamp - start_time).days
                            resolution_week = min(weeks - 1, max(0, days_since_start // 7))
                            resolution_week_key = f"week_{resolution_week + 1}"
                            
                            if resolution_week_key not in weekly_events:
                                weekly_events[resolution_week_key] = {
                                    "commits": 0,
                                    "issues_created": 0,
                                    "issues_resolved": 0,
                                    "start_date": (start_time + timedelta(days=resolution_week * 7)).date().isoformat(),
                                    "end_date": (start_time + timedelta(days=min(total_days, (resolution_week + 1) * 7 - 1))).date().isoformat()
                                }
                                
                            weekly_events[resolution_week_key]["issues_resolved"] += 1
                            break
        
        # Update overall velocity metrics
        metrics["overall"]["velocity"] = weekly_events
        
        # Find most and least active times of day
        hour_activity = {}
        for event in events:
            hour = event.timestamp.hour
            if hour not in hour_activity:
                hour_activity[hour] = 0
            hour_activity[hour] += 1
        
        if hour_activity:
            most_active_hour = max(hour_activity.items(), key=lambda x: x[1])[0]
            least_active_hour = min(hour_activity.items(), key=lambda x: x[1])[0]
            
            metrics["overall"]["most_active_time_of_day"] = f"{most_active_hour}:00"
            metrics["overall"]["least_active_time_of_day"] = f"{least_active_hour}:00"
            
            # Add hourly activity breakdown
            metrics["overall"]["hourly_activity"] = {str(h): count for h, count in hour_activity.items()}
        
        return metrics

    #
    # Integration Health Monitoring
    #
    
    async def monitor_integration_health(
        self,
        project_id: str,
        integration_id: Optional[str] = None,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Monitor and analyze the health of integrations.
        
        Args:
            project_id: ID of the project
            integration_id: Optional specific integration to monitor
            timeframe_days: Number of days to analyze
            
        Returns:
            Dictionary with integration health metrics
        """
        try:
            # Get start and end times for analysis period
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=timeframe_days)
            
            # Get all integration events for the project in the timeframe
            events = await self._get_events_in_timeframe(project_id, start_time, end_time)
            if not events:
                return {"message": "No events found in the specified timeframe"}
                
            # Get integration information
            integrations = await self.knowledge_graph.get_entities(
                entity_type="INTEGRATION",
                filters={"project_id": project_id}
            )
            
            if integration_id:
                integrations = [i for i in integrations if i.id == integration_id]
                if not integrations:
                    return {"message": f"Integration with ID {integration_id} not found"}
            
            # Calculate health metrics
            health_metrics = await self._calculate_integration_health_metrics(
                events, integrations, start_time, end_time
            )
            
            # Add analysis parameters
            health_metrics["analysis_parameters"] = {
                "project_id": project_id,
                "integration_id": integration_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "timeframe_days": timeframe_days
            }
            
            return health_metrics
            
        except Exception as e:
            logger.error(f"Error monitoring integration health: {str(e)}")
            return {"error": str(e)}
    
    async def _calculate_integration_health_metrics(
        self,
        events: List[IntegrationEvent],
        integrations: List[Entity],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Calculate health metrics for integrations.
        
        Args:
            events: List of events to analyze
            integrations: List of integration entities
            start_time: Start of analysis period
            end_time: End of analysis period
            
        Returns:
            Dictionary with integration health metrics
        """
        # Initialize health metrics
        health_metrics = {
            "integrations": {},
            "overall": {
                "total_events": len(events),
                "total_integrations": len(integrations),
                "active_integrations": 0,
                "overall_health_score": 0,
                "daily_event_counts": {},
                "event_type_distribution": {},
                "risk_factors": []
            }
        }
        
        # Group events by integration type
        events_by_integration = {}
        for event in events:
            integration_type = event.source
            if integration_type not in events_by_integration:
                events_by_integration[integration_type] = []
            events_by_integration[integration_type].append(event)
        
        # Count active integrations
        active_integrations = list(events_by_integration.keys())
        health_metrics["overall"]["active_integrations"] = len(active_integrations)
        
        # Process each integration
        for integration in integrations:
            integration_type = integration.metadata.get("type", "unknown")
            integration_id = integration.id
            
            # Initialize integration health metrics
            health_metrics["integrations"][integration_id] = {
                "id": integration_id,
                "type": integration_type,
                "name": integration.metadata.get("name", integration_type),
                "event_count": 0,
                "active": False,
                "last_event_timestamp": None,
                "first_event_timestamp": None,
                "error_rate": 0,
                "event_frequency": {
                    "daily_average": 0,
                    "trend": "stable",
                    "daily_counts": {}
                },
                "response_times": {
                    "average_ms": 0,
                    "trend": "stable",
                    "p95_ms": 0,
                    "p99_ms": 0
                },
                "data_quality": {
                    "completeness": 0,
                    "consistency": 0,
                    "validity": 0,
                    "overall": 0
                },
                "health_score": 0,
                "issues": [],
                "recommendations": []
            }
            
            # Get events for this integration
            integration_events = events_by_integration.get(integration_type, [])
            event_count = len(integration_events)
            health_metrics["integrations"][integration_id]["event_count"] = event_count
            
            # Check if active
            health_metrics["integrations"][integration_id]["active"] = event_count > 0
            
            if event_count > 0:
                # Sort events by timestamp
                integration_events.sort(key=lambda e: e.timestamp)
                
                # Get first and last event timestamps
                first_event = integration_events[0]
                last_event = integration_events[-1]
                
                health_metrics["integrations"][integration_id]["first_event_timestamp"] = first_event.timestamp.isoformat()
                health_metrics["integrations"][integration_id]["last_event_timestamp"] = last_event.timestamp.isoformat()
                
                # Calculate days since last event
                days_since_last_event = (end_time - last_event.timestamp).total_seconds() / 86400
                health_metrics["integrations"][integration_id]["days_since_last_event"] = days_since_last_event
                
                # Calculate error rate
                error_events = [e for e in integration_events if 
                               e.event_type == EventType.ERROR or 
                               e.metadata.get("error") or
                               e.metadata.get("status_code", 200) >= 400]
                
                error_rate = len(error_events) / event_count if event_count > 0 else 0
                health_metrics["integrations"][integration_id]["error_rate"] = error_rate
                
                # Calculate daily event counts
                daily_counts = {}
                total_days = (end_time - start_time).days
                for day in range(total_days + 1):
                    day_date = (start_time + timedelta(days=day)).date()
                    day_key = day_date.isoformat()
                    daily_counts[day_key] = 0
                
                for event in integration_events:
                    day_key = event.timestamp.date().isoformat()
                    if day_key in daily_counts:
                        daily_counts[day_key] += 1
                
                health_metrics["integrations"][integration_id]["event_frequency"]["daily_counts"] = daily_counts
                
                # Calculate daily average
                days_with_events = sum(1 for count in daily_counts.values() if count > 0)
                if days_with_events > 0:
                    daily_average = event_count / days_with_events
                    health_metrics["integrations"][integration_id]["event_frequency"]["daily_average"] = daily_average
                
                # Calculate event trend
                daily_values = list(daily_counts.values())
                if len(daily_values) >= 7:  # At least a week of data
                    first_half = daily_values[:len(daily_values)//2]
                    second_half = daily_values[len(daily_values)//2:]
                    
                    first_half_avg = sum(first_half) / len(first_half) if first_half else 0
                    second_half_avg = sum(second_half) / len(second_half) if second_half else 0
                    
                    if second_half_avg > first_half_avg * 1.2:
                        health_metrics["integrations"][integration_id]["event_frequency"]["trend"] = "increasing"
                    elif second_half_avg < first_half_avg * 0.8:
                        health_metrics["integrations"][integration_id]["event_frequency"]["trend"] = "decreasing"
                    else:
                        health_metrics["integrations"][integration_id]["event_frequency"]["trend"] = "stable"
                
                # Calculate response times if available
                response_times = []
                for event in integration_events:
                    if "response_time_ms" in event.metadata:
                        rt = event.metadata["response_time_ms"]
                        if isinstance(rt, (int, float)) and rt > 0:
                            response_times.append(rt)
                
                if response_times:
                    # Calculate average
                    avg_response_time = sum(response_times) / len(response_times)
                    health_metrics["integrations"][integration_id]["response_times"]["average_ms"] = avg_response_time
                    
                    # Calculate percentiles
                    response_times.sort()
                    p95_index = int(len(response_times) * 0.95)
                    p99_index = int(len(response_times) * 0.99)
                    
                    health_metrics["integrations"][integration_id]["response_times"]["p95_ms"] = response_times[p95_index] if p95_index < len(response_times) else response_times[-1]
                    health_metrics["integrations"][integration_id]["response_times"]["p99_ms"] = response_times[p99_index] if p99_index < len(response_times) else response_times[-1]
                    
                    # Calculate trend
                    if len(response_times) >= 10:
                        first_half = response_times[:len(response_times)//2]
                        second_half = response_times[len(response_times)//2:]
                        
                        first_half_avg = sum(first_half) / len(first_half)
                        second_half_avg = sum(second_half) / len(second_half)
                        
                        if second_half_avg > first_half_avg * 1.2:
                            health_metrics["integrations"][integration_id]["response_times"]["trend"] = "degrading"
                        elif second_half_avg < first_half_avg * 0.8:
                            health_metrics["integrations"][integration_id]["response_times"]["trend"] = "improving"
                        else:
                            health_metrics["integrations"][integration_id]["response_times"]["trend"] = "stable"
                
                # Calculate data quality metrics
                completeness_scores = []
                consistency_scores = []
                validity_scores = []
                
                # Define expected fields for each event type
                expected_fields = {
                    EventType.COMMIT.value: ["id", "author", "message", "timestamp"],
                    EventType.ISSUE.value: ["id", "title", "author", "timestamp"],
                    EventType.MESSAGE.value: ["id", "author", "content", "timestamp"],
                    EventType.DOCUMENT.value: ["id", "title", "content", "timestamp"]
                }
                
                # Format validators for specific fields
                validators = {
                    "email": lambda x: isinstance(x, str) and "@" in x,
                    "url": lambda x: isinstance(x, str) and (x.startswith("http://") or x.startswith("https://")),
                    "timestamp": lambda x: isinstance(x, datetime)
                }
                
                for event in integration_events:
                    event_type = event.event_type.value
                    
                    # Completeness: check if all expected fields are present
                    expected = expected_fields.get(event_type, [])
                    if expected:
                        present_fields = sum(1 for field in expected if field in event.metadata)
                        completeness = present_fields / len(expected)
                        completeness_scores.append(completeness)
                    
                    # Consistency: check if field values are consistent with each other
                    # For example: creation_date should be before update_date
                    consistency = 1.0  # Default perfect score
                    
                    if "created_at" in event.metadata and "updated_at" in event.metadata:
                        created = event.metadata["created_at"]
                        updated = event.metadata["updated_at"]
                        
                        if isinstance(created, datetime) and isinstance(updated, datetime):
                            if updated < created:
                                consistency = 0.0
                    
                    consistency_scores.append(consistency)
                    
                    # Validity: check if fields have valid formats
                    valid_fields = 0
                    total_validated = 0
                    
                    for field, validator in validators.items():
                        if field in event.metadata:
                            total_validated += 1
                            if validator(event.metadata[field]):
                                valid_fields += 1
                    
                    validity = valid_fields / total_validated if total_validated > 0 else 1.0
                    validity_scores.append(validity)
                
                # Calculate average scores
                if completeness_scores:
                    health_metrics["integrations"][integration_id]["data_quality"]["completeness"] = sum(completeness_scores) / len(completeness_scores)
                
                if consistency_scores:
                    health_metrics["integrations"][integration_id]["data_quality"]["consistency"] = sum(consistency_scores) / len(consistency_scores)
                
                if validity_scores:
                    health_metrics["integrations"][integration_id]["data_quality"]["validity"] = sum(validity_scores) / len(validity_scores)
                
                # Overall data quality score
                completeness = health_metrics["integrations"][integration_id]["data_quality"]["completeness"]
                consistency = health_metrics["integrations"][integration_id]["data_quality"]["consistency"]
                validity = health_metrics["integrations"][integration_id]["data_quality"]["validity"]
                
                overall_quality = (completeness * 0.4) + (consistency * 0.3) + (validity * 0.3)
                health_metrics["integrations"][integration_id]["data_quality"]["overall"] = overall_quality
                
                # Calculate health score
                # Factors: error rate, days since last event, data quality, response time trend
                error_factor = 1 - error_rate
                recency_factor = 1.0
                if days_since_last_event > 7:
                    recency_factor = max(0.0, 1.0 - (days_since_last_event - 7) / 30)
                
                response_factor = 1.0
                if health_metrics["integrations"][integration_id]["response_times"]["average_ms"] > 0:
                    # Normalize response time (assume >5000ms is bad)
                    avg_time = health_metrics["integrations"][integration_id]["response_times"]["average_ms"]
                    response_factor = max(0.0, 1.0 - (avg_time / 5000))
                
                # Calculate health score (0-100)
                health_score = (
                    (error_factor * 0.4) +
                    (recency_factor * 0.2) +
                    (overall_quality * 0.3) +
                    (response_factor * 0.1)
                ) * 100
                
                health_metrics["integrations"][integration_id]["health_score"] = round(health_score, 1)
                
                # Identify issues
                issues = []
                
                if error_rate > 0.05:
                    issues.append({
                        "severity": "high" if error_rate > 0.2 else "medium",
                        "issue": f"High error rate ({error_rate:.1%})",
                        "recommendation": "Check error logs and fix integration configuration issues"
                    })
                
                if days_since_last_event > 2:
                    severity = "low" if days_since_last_event <= 5 else "medium" if days_since_last_event <= 10 else "high"
                    issues.append({
                        "severity": severity,
                        "issue": f"No recent activity ({days_since_last_event:.1f} days since last event)",
                        "recommendation": "Verify integration connectivity and credentials"
                    })
                
                if overall_quality < 0.7:
                    issues.append({
                        "severity": "medium",
                        "issue": f"Low data quality score ({overall_quality:.1%})",
                        "recommendation": "Check integration data mapping and field requirements"
                    })
                
                if health_metrics["integrations"][integration_id]["response_times"].get("trend") == "degrading":
                    issues.append({
                        "severity": "medium",
                        "issue": "Degrading response times",
                        "recommendation": "Check API rate limits and integration service health"
                    })
                
                if health_metrics["integrations"][integration_id]["event_frequency"].get("trend") == "decreasing":
                    issues.append({
                        "severity": "medium",
                        "issue": "Decreasing event frequency",
                        "recommendation": "Verify integration is capturing all expected events"
                    })
                
                health_metrics["integrations"][integration_id]["issues"] = issues
                
                # Generate recommendations
                recommendations = []
                
                # Add recommendations based on issues
                for issue in issues:
                    recommendations.append(issue["recommendation"])
                
                # Add general recommendations
                if event_count > 0 and health_score < 70:
                    recommendations.append("Review integration configuration and connectivity settings")
                
                if days_since_last_event > 7:
                    recommendations.append("Test integration connectivity and refresh credentials if needed")
                
                health_metrics["integrations"][integration_id]["recommendations"] = list(set(recommendations))
                
                # Add to overall risk factors if health score is low
                if health_score < 60:
                    health_metrics["overall"]["risk_factors"].append({
                        "integration_id": integration_id,
                        "integration_type": integration_type,
                        "health_score": health_score,
                        "main_issues": [issue["issue"] for issue in issues[:2]] if issues else ["Low health score"]
                    })
        
        # Calculate overall health score (average of all active integrations)
        active_integration_scores = [
            health_metrics["integrations"][i_id]["health_score"]
            for i_id in health_metrics["integrations"]
            if health_metrics["integrations"][i_id]["active"]
        ]
        
        if active_integration_scores:
            health_metrics["overall"]["overall_health_score"] = sum(active_integration_scores) / len(active_integration_scores)
        
        # Calculate event type distribution
        event_types = {}
        for event in events:
            event_type = event.event_type.value
            if event_type not in event_types:
                event_types[event_type] = 0
            event_types[event_type] += 1
        
        health_metrics["overall"]["event_type_distribution"] = event_types
        
        # Calculate daily overall event counts
        daily_counts = {}
        total_days = (end_time - start_time).days
        for day in range(total_days + 1):
            day_date = (start_time + timedelta(days=day)).date()
            day_key = day_date.isoformat()
            daily_counts[day_key] = 0
        
        for event in events:
            day_key = event.timestamp.date().isoformat()
            if day_key in daily_counts:
                daily_counts[day_key] += 1
        
        health_metrics["overall"]["daily_event_counts"] = daily_counts
        
        return health_metrics

    #
    # Team Collaboration Analysis
    #
    
    async def analyze_team_collaboration(
        self,
        project_id: str,
        timeframe_days: int = 30,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze team collaboration patterns within a project.
        
        Args:
            project_id: ID of the project to analyze
            timeframe_days: Number of days to analyze
            team_id: Optional team ID to filter by
            
        Returns:
            Dictionary with team collaboration metrics
        """
        try:
            # Get start and end times for analysis period
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=timeframe_days)
            
            # Get all events for the project in the timeframe
            events = await self._get_events_in_timeframe(project_id, start_time, end_time)
            if not events:
                return {"message": "No events found in the specified timeframe"}
            
            # Get team information if team_id is provided
            team_members = []
            if team_id:
                team = await self.knowledge_graph.get_entity(team_id)
                if not team or team.entity_type != "TEAM":
                    return {"message": f"Team with ID {team_id} not found"}
                    
                team_members = team.metadata.get("members", [])
                
                # Filter events by team members
                if team_members:
                    events = [e for e in events if e.author in team_members]
                    if not events:
                        return {"message": f"No events found for team {team_id} in the specified timeframe"}
            
            # Calculate collaboration metrics
            metrics = await self._calculate_collaboration_metrics(events, start_time, end_time, team_members)
            
            # Add analysis parameters
            metrics["analysis_parameters"] = {
                "project_id": project_id,
                "team_id": team_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "timeframe_days": timeframe_days
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing team collaboration: {str(e)}")
            return {"error": str(e)}
    
    async def _calculate_collaboration_metrics(
        self,
        events: List[IntegrationEvent],
        start_time: datetime,
        end_time: datetime,
        team_members: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate team collaboration metrics from events.
        
        Args:
            events: List of events to analyze
            start_time: Start of analysis period
            end_time: End of analysis period
            team_members: Optional list of team members to filter by
            
        Returns:
            Dictionary with collaboration metrics
        """
        # Initialize metrics
        metrics = {
            "team_members": {},
            "component_collaboration": {},
            "interaction_matrix": {},
            "collaboration_graph": {
                "nodes": [],
                "links": []
            },
            "overall": {
                "event_count": len(events),
                "active_members": 0,
                "collaboration_score": 0,
                "most_collaborative_member": None,
                "most_central_member": None,
                "siloed_members": [],
                "cross_component_collaboration": 0
            }
        }
        
        # Extract unique authors from events
        all_authors = set()
        for event in events:
            if event.author:
                all_authors.add(event.author)
        
        # Filter to team members if specified
        if team_members:
            members = [a for a in all_authors if a in team_members]
        else:
            members = list(all_authors)
        
        # Skip processing if no members found
        if not members:
            metrics["overall"]["active_members"] = 0
            return metrics
            
        metrics["overall"]["active_members"] = len(members)
        
        # Initialize interaction matrix for all members
        for member in members:
            metrics["interaction_matrix"][member] = {other: 0 for other in members if other != member}
            
            # Initialize member metrics
            metrics["team_members"][member] = {
                "event_count": 0,
                "components_touched": set(),
                "collaboration_score": 0,
                "centrality": 0,
                "responsiveness": {
                    "avg_response_time_hours": 0,
                    "response_count": 0
                },
                "most_frequent_collaborators": [],
                "cross_component_ratio": 0
            }
        
        # Group events by component
        components = {}
        for event in events:
            component = event.component or "unknown"
            if component not in components:
                components[component] = []
            components[component].append(event)
        
        # Calculate member-level metrics and component interactions
        events_by_author = {}
        for event in events:
            author = event.author
            if not author or author not in members:
                continue
                
            # Count events per author
            if author not in events_by_author:
                events_by_author[author] = []
            events_by_author[author].append(event)
            
            # Track components touched by this member
            if event.component:
                metrics["team_members"][author]["components_touched"].add(event.component)
            
            # Process specific event types for collaboration signals
            if event.event_type in [EventType.COMMIT, EventType.ISSUE, EventType.MESSAGE, EventType.DEPLOYMENT]:
                # Look for collaboration signals in the event
                collaborators = self._extract_collaborators_from_event(event)
                
                # Update interaction matrix
                for collaborator in collaborators:
                    if collaborator in members and collaborator != author:
                        metrics["interaction_matrix"][author][collaborator] += 1
                        
                        # Find if there are response times we can measure
                        if event.event_type == EventType.ISSUE:
                            # Check if this issue was later commented on by the collaborator
                            related = await self.knowledge_graph.get_entity_relationships(
                                event.id, relationship_type="RELATES_TO")
                            
                            for rel in related:
                                if rel.target_id == event.id:
                                    source = await self.knowledge_graph.get_entity(rel.source_id)
                                    if not source:
                                        continue
                                        
                                    source_event = self._entity_to_event(source) if source else None
                                    if (source_event and 
                                        source_event.author == collaborator):
                                        # Calculate response time
                                        response_time = (source_event.timestamp - event.timestamp).total_seconds() / 3600
                                        
                                        # Update responsiveness metrics
                                        metrics["team_members"][collaborator]["responsiveness"]["response_count"] += 1
                                        current_avg = metrics["team_members"][collaborator]["responsiveness"]["avg_response_time_hours"]
                                        current_count = metrics["team_members"][collaborator]["responsiveness"]["response_count"]
                                        
                                        # Update running average
                                        if current_count > 1:
                                            metrics["team_members"][collaborator]["responsiveness"]["avg_response_time_hours"] = (
                                                (current_avg * (current_count - 1) + response_time) / current_count
                                            )
                                        else:
                                            metrics["team_members"][collaborator]["responsiveness"]["avg_response_time_hours"] = response_time
        
        # Calculate member-specific metrics
        for author, author_events in events_by_author.items():
            # Update event count
            metrics["team_members"][author]["event_count"] = len(author_events)
            
            # Convert components set to list for JSON serialization
            metrics["team_members"][author]["components_touched"] = list(
                metrics["team_members"][author]["components_touched"]
            )
            
            # Calculate cross-component ratio
            if metrics["team_members"][author]["components_touched"]:
                component_count = len(metrics["team_members"][author]["components_touched"])
                cross_ratio = min(1.0, (component_count - 1) / max(1, len(components) - 1))
                metrics["team_members"][author]["cross_component_ratio"] = cross_ratio
            
            # Find most frequent collaborators
            if author in metrics["interaction_matrix"]:
                collaborations = [(other, count) for other, count in metrics["interaction_matrix"][author].items() if count > 0]
                collaborations.sort(key=lambda x: x[1], reverse=True)
                
                # Get top 3 collaborators
                top_collaborators = collaborations[:3]
                metrics["team_members"][author]["most_frequent_collaborators"] = [
                    {"name": collab[0], "interaction_count": collab[1]}
                    for collab in top_collaborators
                ]
                
                # Calculate collaboration score
                total_interactions = sum(count for _, count in collaborations)
                unique_collaborators = len([c for c in collaborations if c[1] > 0])
                
                # Collaboration score is based on total interactions and number of unique collaborators
                if unique_collaborators > 0:
                    metrics["team_members"][author]["collaboration_score"] = (
                        0.7 * (total_interactions / max(1, len(members) - 1)) +
                        0.3 * (unique_collaborators / max(1, len(members) - 1))
                    )
        
        # Generate collaboration graph
        # Add nodes
        for member in members:
            collab_score = metrics["team_members"][member]["collaboration_score"]
            event_count = metrics["team_members"][member]["event_count"]
            
            metrics["collaboration_graph"]["nodes"].append({
                "id": member,
                "name": member,
                "event_count": event_count,
                "collaboration_score": collab_score
            })
        
        # Add links between members who collaborated
        for source in members:
            for target, weight in metrics["interaction_matrix"][source].items():
                if weight > 0:
                    metrics["collaboration_graph"]["links"].append({
                        "source": source,
                        "target": target,
                        "weight": weight
                    })
        
        # Calculate centrality for each member
        for member in members:
            # Degree centrality: number of direct connections
            connections = sum(1 for other, weight in metrics["interaction_matrix"][member].items() if weight > 0)
            max_possible = len(members) - 1
            
            if max_possible > 0:
                degree_centrality = connections / max_possible
                metrics["team_members"][member]["centrality"] = degree_centrality
        
        # Calculate component-level collaboration metrics
        for component, component_events in components.items():
            if component == "unknown":
                continue
                
            # Find authors who worked on this component
            component_authors = set()
            for event in component_events:
                if event.author in members:
                    component_authors.add(event.author)
            
            # Skip components with fewer than 2 authors
            if len(component_authors) < 2:
                continue
                
            # Initialize component metrics
            metrics["component_collaboration"][component] = {
                "event_count": len(component_events),
                "active_members": list(component_authors),
                "collaboration_density": 0,
                "primary_owner": None,
                "ownership_distribution": {}
            }
            
            # Calculate ownership distribution
            author_counts = {}
            for event in component_events:
                if event.author in members:
                    if event.author not in author_counts:
                        author_counts[event.author] = 0
                    author_counts[event.author] += 1
            
            total_events = sum(author_counts.values())
            if total_events > 0:
                # Calculate ownership percentages
                ownership = {author: count / total_events for author, count in author_counts.items()}
                metrics["component_collaboration"][component]["ownership_distribution"] = ownership
                
                # Find primary owner
                primary = max(author_counts.items(), key=lambda x: x[1])
                metrics["component_collaboration"][component]["primary_owner"] = primary[0]
                
                # Calculate collaboration density
                # (ratio of actual interactions to possible interactions)
                interaction_count = 0
                for author1 in component_authors:
                    for author2 in component_authors:
                        if author1 != author2:
                            interaction_count += metrics["interaction_matrix"][author1][author2]
                
                max_possible_interactions = len(component_authors) * (len(component_authors) - 1)
                if max_possible_interactions > 0:
                    density = min(1.0, interaction_count / max_possible_interactions)
                    metrics["component_collaboration"][component]["collaboration_density"] = density
        
        # Calculate overall team metrics
        # Find most collaborative member
        most_collaborative = None
        highest_score = -1
        
        for member, data in metrics["team_members"].items():
            if data["collaboration_score"] > highest_score:
                highest_score = data["collaboration_score"]
                most_collaborative = member
        
        metrics["overall"]["most_collaborative_member"] = most_collaborative
        
        # Find most central member
        most_central = None
        highest_centrality = -1
        
        for member, data in metrics["team_members"].items():
            if data["centrality"] > highest_centrality:
                highest_centrality = data["centrality"]
                most_central = member
        
        metrics["overall"]["most_central_member"] = most_central
        
        # Find siloed members (low collaboration score)
        siloed_threshold = 0.2
        siloed_members = []
        
        for member, data in metrics["team_members"].items():
            if data["event_count"] > 5 and data["collaboration_score"] < siloed_threshold:
                siloed_members.append({
                    "name": member,
                    "collaboration_score": data["collaboration_score"],
                    "event_count": data["event_count"]
                })
        
        metrics["overall"]["siloed_members"] = siloed_members
        
        # Calculate cross-component collaboration
        cross_component_scores = [data["cross_component_ratio"] for _, data in metrics["team_members"].items()]
        if cross_component_scores:
            metrics["overall"]["cross_component_collaboration"] = sum(cross_component_scores) / len(cross_component_scores)
        
        # Calculate overall collaboration score
        if members:
            # Average of individual collaboration scores
            individual_scores = [data["collaboration_score"] for _, data in metrics["team_members"].items()]
            metrics["overall"]["collaboration_score"] = sum(individual_scores) / len(individual_scores)
        
        return metrics
    
    def _extract_collaborators_from_event(self, event: IntegrationEvent) -> List[str]:
        """
        Extract potential collaborators from an event.
        
        Args:
            event: The event to analyze
            
        Returns:
            List of collaborator IDs
        """
        collaborators = set()
        
        # Check event metadata
        if "mentioned_users" in event.metadata:
            mentions = event.metadata["mentioned_users"]
            if isinstance(mentions, list):
                collaborators.update(mentions)
        
        if "assignee" in event.metadata:
            assignee = event.metadata["assignee"]
            if assignee:
                collaborators.add(assignee)
        
        if "reviewers" in event.metadata:
            reviewers = event.metadata["reviewers"]
            if isinstance(reviewers, list):
                collaborators.update(reviewers)
        
        # For commits, look for co-authors in the message
        if event.event_type == EventType.COMMIT and "message" in event.metadata:
            message = event.metadata["message"]
            if isinstance(message, str):
                # Look for "Co-authored-by: Name <email>" pattern
                co_author_pattern = r"Co-authored-by:\s*([^<]+)\s*<([^>]+)>"
                matches = re.findall(co_author_pattern, message)
                for match in matches:
                    name, email = match
                    collaborators.add(name.strip())
        
        # For issues and PRs, look in comments
        if event.event_type in [EventType.ISSUE, EventType.PULL_REQUEST] and "comments" in event.metadata:
            comments = event.metadata["comments"]
            if isinstance(comments, list):
                for comment in comments:
                    if isinstance(comment, dict) and "author" in comment:
                        collaborators.add(comment["author"])
        
        # Remove the original author if present
        if event.author in collaborators:
            collaborators.remove(event.author)
            
        return list(collaborators)

    #
    # Risk Prediction
    #
    
    async def predict_risks(
        self,
        project_id: Optional[str] = None,
        component: Optional[str] = None,
        author: Optional[str] = None,
        repository: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Predict potential risks based on analysis of past events and patterns.
        
        This method analyzes historical data to identify patterns that may indicate
        future issues or risks. It considers factors like component stability, 
        author experience, code complexity, and prior bug patterns.
        
        Args:
            project_id: Optional project ID to filter risks by
            component: Optional component to analyze for risks
            author: Optional author to analyze for risks
            repository: Optional repository to analyze for risks
            limit: Maximum number of risks to return
            
        Returns:
            Dictionary with predicted risks and their details
        """
        try:
            # Use project ID from config if not provided
            if not project_id:
                project_id = self.config.project_id
                
            # Prepare filters
            filters = {"type": "event"}
            if project_id:
                filters["project_id"] = project_id
                
            # Component filter
            if component:
                filters["component"] = component
                
            # Get recent events from the knowledge graph
            recent_events_entities = await self.knowledge_graph.search_entities(
                filters=filters,
                limit=1000,  # Get sufficient history
                sort_by="timestamp",
                sort_direction="desc"
            )
            
            # Convert to events
            recent_events = []
            for entity in recent_events_entities:
                event = self._entity_to_event(entity)
                if event:
                    recent_events.append(event)
                    
            # No events to analyze
            if not recent_events:
                return {
                    "risks": [],
                    "risk_count": 0,
                    "risk_factors": {},
                }
                
            # Calculate risk window - how far back to look for patterns
            risk_window = timedelta(days=self.config.risk_window_days)
            
            # Risk calculation factors
            risks = []
            component_risks = {}
            author_risks = {}
            temporal_patterns = {}
            
            # Find components with high issue rates
            component_issues = {}
            component_commits = {}
            
            # Find authors with high issue rates
            author_issues = {}
            author_commits = {}
            
            # Process events to collect metrics
            for event in recent_events:
                # Skip old events outside risk window
                if event.timestamp < (datetime.now(timezone.utc) - risk_window):
                    continue
                    
                # Track issues by component
                if event.event_type == EventType.ISSUE:
                    component = event.component or "unknown"
                    if component not in component_issues:
                        component_issues[component] = []
                    component_issues[component].append(event)
                    
                    # Track by author too
                    if event.author:
                        if event.author not in author_issues:
                            author_issues[event.author] = []
                        author_issues[event.author].append(event)
                    
                # Track commits by component
                elif event.event_type == EventType.COMMIT:
                    # Extract components from commit
                    components = self._extract_components(event)
                    for component in components:
                        if component not in component_commits:
                            component_commits[component] = []
                        component_commits[component].append(event)
                    
                    # Track by author
                    if event.author:
                        if event.author not in author_commits:
                            author_commits[event.author] = []
                        author_commits[event.author].append(event)
            
            # Calculate component risk scores
            for component, issues in component_issues.items():
                commit_count = len(component_commits.get(component, []))
                issue_count = len(issues)
                
                # Skip components with very few events
                if issue_count + commit_count < 5:
                    continue
                    
                # Calculate issue-to-commit ratio (higher is riskier)
                issue_ratio = issue_count / max(1, commit_count)
                
                # Calculate average bug severity (if available in metadata)
                severity_sum = 0
                severity_count = 0
                for issue in issues:
                    severity = issue.metadata.get("severity") or issue.metadata.get("priority")
                    if isinstance(severity, (int, float)):
                        severity_sum += float(severity)
                        severity_count += 1
                        
                avg_severity = severity_sum / max(1, severity_count)
                
                # Calculate recency - more weight to recent issues
                now = datetime.now(timezone.utc)
                recency_score = 0
                for issue in issues:
                    days_ago = (now - issue.timestamp).days
                    recency_score += max(0, (self.config.risk_window_days - days_ago)) / self.config.risk_window_days
                    
                recency_factor = recency_score / max(1, issue_count)
                
                # Combine factors for final risk score
                risk_score = (0.5 * issue_ratio) + (0.3 * avg_severity) + (0.2 * recency_factor)
                
                # Determine risk level
                risk_level = RiskLevel.LOW
                if risk_score >= self.config.risk_threshold_high:
                    risk_level = RiskLevel.HIGH
                elif risk_score >= self.config.risk_threshold_medium:
                    risk_level = RiskLevel.MEDIUM
                    
                # Create risk entry
                component_risks[component] = {
                    "component": component,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "issue_count": issue_count,
                    "commit_count": commit_count,
                    "recent_issues": [
                        {
                            "id": issue.id,
                            "title": issue.title,
                            "timestamp": issue.timestamp.isoformat(),
                            "status": issue.status
                        }
                        for issue in sorted(issues, key=lambda x: x.timestamp, reverse=True)[:3]
                    ]
                }
                
                # Add to main risks list
                if risk_level != RiskLevel.LOW:
                    risks.append({
                        "risk_type": "component_risk",
                        "component": component,
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "details": component_risks[component]
                    })
            
            # Calculate author risk scores
            for author, issues in author_issues.items():
                commit_count = len(author_commits.get(author, []))
                issue_count = len(issues)
                
                # Skip authors with very few events
                if issue_count + commit_count < 5:
                    continue
                
                # Calculate issue-to-commit ratio (higher is riskier)
                issue_ratio = issue_count / max(1, commit_count)
                
                # Calculate recency factor
                now = datetime.now(timezone.utc)
                recency_score = 0
                for issue in issues:
                    days_ago = (now - issue.timestamp).days
                    recency_score += max(0, (self.config.risk_window_days - days_ago)) / self.config.risk_window_days
                
                recency_factor = recency_score / max(1, issue_count)
                
                # Combine for risk score
                risk_score = (0.7 * issue_ratio) + (0.3 * recency_factor)
                
                # Determine risk level
                risk_level = RiskLevel.LOW
                if risk_score >= self.config.risk_threshold_high:
                    risk_level = RiskLevel.HIGH
                elif risk_score >= self.config.risk_threshold_medium:
                    risk_level = RiskLevel.MEDIUM
                    
                # Create author risk entry
                if risk_level != RiskLevel.LOW:
                    risks.append({
                        "risk_type": "author_risk",
                        "author": author,
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "details": {
                            "issue_count": issue_count,
                            "commit_count": commit_count,
                            "components": list(set([i.component for i in issues if i.component]))
                        }
                    })
            
            # Analyze temporal patterns and recurring issues
            if len(recent_events) > 5:
                # Find cyclical patterns in issues
                issue_timestamps = [e.timestamp for e in recent_events if e.event_type == EventType.ISSUE]
                if len(issue_timestamps) > 5:
                    # Calculate average time between issues
                    issue_timestamps.sort()
                    intervals = [(issue_timestamps[i] - issue_timestamps[i-1]).total_seconds() 
                                for i in range(1, len(issue_timestamps))]
                    
                    if intervals:
                        avg_interval = statistics.mean(intervals) / 86400  # Convert to days
                        std_dev = statistics.stdev(intervals) / 86400 if len(intervals) > 1 else 0
                        
                        # If standard deviation is low, we have a consistent pattern
                        if std_dev < avg_interval / 2 and avg_interval < self.config.risk_window_days / 2:
                            # Predict next issue based on pattern
                            last_issue_time = issue_timestamps[-1]
                            next_predicted = last_issue_time + timedelta(days=avg_interval)
                            
                            # Calculate risk based on consistency and proximity
                            days_until_next = (next_predicted - datetime.now(timezone.utc)).total_seconds() / 86400
                            pattern_confidence = 1.0 - (std_dev / avg_interval)
                            
                            if days_until_next < 7:  # Within a week
                                risk_level = RiskLevel.HIGH if pattern_confidence > 0.7 else RiskLevel.MEDIUM
                                risks.append({
                                    "risk_type": "temporal_pattern",
                                    "risk_level": risk_level,
                                    "risk_score": pattern_confidence,
                                    "details": {
                                        "pattern_type": "cyclical_issues",
                                        "avg_days_between_issues": avg_interval,
                                        "next_predicted_issue": next_predicted.isoformat(),
                                        "days_until_next": days_until_next,
                                        "pattern_confidence": pattern_confidence
                                    }
                                })
            
            # Sort risks by score (descending)
            risks.sort(key=lambda x: x["risk_score"], reverse=True)
            
            # Limit results
            risks = risks[:limit]
            
            # Count risks by level
            risk_counts = {
                "high": len([r for r in risks if r["risk_level"] == RiskLevel.HIGH]),
                "medium": len([r for r in risks if r["risk_level"] == RiskLevel.MEDIUM]),
                "low": len([r for r in risks if r["risk_level"] == RiskLevel.LOW])
            }
            
            # Return risk prediction results
            return {
                "risks": risks,
                "risk_count": len(risks),
                "risk_levels": risk_counts,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting risks: {str(e)}")
            return {"error": str(e)}
            
    async def get_component_risk_metrics(
        self, 
        component: str,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed risk metrics for a specific component.
        
        Args:
            component: Component to analyze
            project_id: Optional project ID
            
        Returns:
            Dictionary with risk metrics
        """
        try:
            # Use project ID from config if not provided
            if not project_id:
                project_id = self.config.project_id
                
            # Get events related to this component
            filters = {"type": "event"}
            if project_id:
                filters["project_id"] = project_id
                
            # Get events from knowledge graph
            events_entities = await self.knowledge_graph.search_entities(
                filters=filters,
                limit=500,
                sort_by="timestamp",
                sort_direction="desc"
            )
            
            # Convert to events and filter by component
            component_events = []
            for entity in events_entities:
                event = self._entity_to_event(entity)
                if event and (
                    event.component == component or 
                    component in self._extract_components(event)
                ):
                    component_events.append(event)
            
            # Group events by type
            issues = [e for e in component_events if e.event_type == EventType.ISSUE]
            commits = [e for e in component_events if e.event_type == EventType.COMMIT]
            pull_requests = [e for e in component_events if e.event_type == EventType.PULL_REQUEST]
            
            # Calculate metrics
            issue_count = len(issues)
            commit_count = len(commits)
            pr_count = len(pull_requests)
            
            # Calculate change frequency
            if commits:
                first_commit = min([c.timestamp for c in commits])
                last_commit = max([c.timestamp for c in commits])
                days_span = max(1, (last_commit - first_commit).days)
                changes_per_day = commit_count / days_span
            else:
                changes_per_day = 0
                
            # Calculate issue frequency
            if issues:
                first_issue = min([i.timestamp for i in issues])
                last_issue = max([i.timestamp for i in issues])
                days_span = max(1, (last_issue - first_issue).days)
                issues_per_day = issue_count / days_span
            else:
                issues_per_day = 0
                
            # Count open issues
            open_issues = [i for i in issues if i.status and i.status.lower() not in ["resolved", "closed", "done", "complete", "fixed"]]
            open_issue_count = len(open_issues)
            
            # Count recent issues (last 30 days)
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            recent_issues = [i for i in issues if i.timestamp >= thirty_days_ago]
            recent_issue_count = len(recent_issues)
            
            # Determine risk level based on metrics
            risk_score = (
                (0.4 * issues_per_day * 30) +  # Monthly issue rate
                (0.2 * open_issue_count) +     # Open issues
                (0.3 * recent_issue_count) +   # Recent issues
                (0.1 * changes_per_day * 30)   # Monthly change rate
            )
            
            risk_level = RiskLevel.LOW
            if risk_score >= self.config.risk_threshold_high:
                risk_level = RiskLevel.HIGH
            elif risk_score >= self.config.risk_threshold_medium:
                risk_level = RiskLevel.MEDIUM
                
            # Get top contributors
            authors = {}
            for commit in commits:
                if commit.author:
                    authors[commit.author] = authors.get(commit.author, 0) + 1
                    
            top_contributors = [{"author": author, "commits": count} 
                               for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]]
            
            # Return detailed metrics
            return {
                "component": component,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "metrics": {
                    "issue_count": issue_count,
                    "commit_count": commit_count,
                    "pull_request_count": pr_count,
                    "open_issues": open_issue_count,
                    "issues_per_day": issues_per_day,
                    "changes_per_day": changes_per_day,
                    "recent_issues_30d": recent_issue_count
                },
                "top_contributors": top_contributors,
                "recent_issues": [
                    {
                        "id": issue.id,
                        "title": issue.title,
                        "status": issue.status,
                        "timestamp": issue.timestamp.isoformat()
                    }
                    for issue in sorted(recent_issues, key=lambda x: x.timestamp, reverse=True)[:5]
                ],
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
                
        except Exception as e:
            logger.error(f"Error getting component risk metrics: {str(e)}")
            return {"error": str(e)}
            
class RiskLevel(str, Enum):
    """Risk levels for predicted risks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
