"""
Timeline-Based Storage System for NeuroSync
Chronological data organization with intelligent archiving and retrieval
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict, deque

from .vector_db import VectorDatabase
from .knowledge_graph import KnowledgeGraphBuilder
from .context_persistence import ContextPersistenceService, ContextType, ContextScope
from .data_importance_scoring import AdvancedDataImportanceScoring, TimelineCategory, ImportanceLevel

logger = logging.getLogger(__name__)

class StorageTier(Enum):
    """Storage tiers based on access patterns and importance"""
    HOT = "hot"           # Frequently accessed, recent data
    WARM = "warm"         # Occasionally accessed, important historical data
    COLD = "cold"         # Rarely accessed, archived data
    FROZEN = "frozen"     # Long-term archive, minimal access

class RetentionPolicy(Enum):
    """Data retention policies"""
    CRITICAL_PERMANENT = "critical_permanent"     # Keep forever
    HIGH_LONG_TERM = "high_long_term"            # Keep for 5 years
    MEDIUM_STANDARD = "medium_standard"          # Keep for 2 years
    LOW_SHORT_TERM = "low_short_term"            # Keep for 6 months
    NOISE_MINIMAL = "noise_minimal"              # Keep for 1 month

@dataclass
class TimelineEntry:
    """Represents a data entry in the timeline"""
    entry_id: str
    project_id: str
    data_type: str
    content_hash: str
    importance_score: float
    importance_level: ImportanceLevel
    timeline_category: TimelineCategory
    storage_tier: StorageTier
    retention_policy: RetentionPolicy
    created_at: datetime
    last_accessed: datetime
    access_count: int
    metadata: Dict[str, Any]
    tags: List[str]
    relationships: List[str]

class TimelineBasedStorage:
    """
    Production-ready timeline-based storage system
    
    Features:
    - Chronological data organization with smart categorization
    - Multi-tier storage optimization (hot, warm, cold, frozen)
    - Intelligent data retention policies
    - Access pattern tracking and optimization
    - Automated archiving and cleanup
    """
    
    def __init__(self):
        self.vector_db = VectorDatabase()
        self.knowledge_graph = KnowledgeGraphBuilder()
        self.context_service = ContextPersistenceService()
        self.importance_scorer = AdvancedDataImportanceScoring()
        
        # Timeline storage
        self.timeline_entries: Dict[str, TimelineEntry] = {}
        self.project_timelines: Dict[str, List[str]] = defaultdict(list)
        
        # Storage tier management
        self.tier_thresholds = {
            StorageTier.HOT: 30,      # Last 30 days
            StorageTier.WARM: 180,    # 30-180 days
            StorageTier.COLD: 730,    # 180 days - 2 years
            StorageTier.FROZEN: float('inf')  # Over 2 years
        }
        
        # Retention policies mapping
        self.retention_mapping = {
            ImportanceLevel.CRITICAL: RetentionPolicy.CRITICAL_PERMANENT,
            ImportanceLevel.HIGH: RetentionPolicy.HIGH_LONG_TERM,
            ImportanceLevel.MEDIUM: RetentionPolicy.MEDIUM_STANDARD,
            ImportanceLevel.LOW: RetentionPolicy.LOW_SHORT_TERM,
            ImportanceLevel.NOISE: RetentionPolicy.NOISE_MINIMAL
        }
        
        # Retention periods (in days)
        self.retention_periods = {
            RetentionPolicy.CRITICAL_PERMANENT: float('inf'),
            RetentionPolicy.HIGH_LONG_TERM: 1825,  # 5 years
            RetentionPolicy.MEDIUM_STANDARD: 730,  # 2 years
            RetentionPolicy.LOW_SHORT_TERM: 180,   # 6 months
            RetentionPolicy.NOISE_MINIMAL: 30      # 1 month
        }
        
        # Access tracking
        self.access_patterns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    
    async def store_timeline_data(self, project_id: str, data_items: List[Dict[str, Any]]) -> List[str]:
        """Store data items in timeline-based storage with intelligent organization"""
        try:
            logger.info(f"Storing {len(data_items)} items in timeline for project {project_id}")
            
            # Score importance for all items
            importance_scores = await self.importance_scorer.score_batch(project_id, data_items)
            
            stored_entry_ids = []
            
            for i, (data_item, score) in enumerate(zip(data_items, importance_scores)):
                try:
                    # Create timeline entry
                    entry_id = str(uuid.uuid4())
                    
                    # Determine storage tier and retention policy
                    storage_tier = self._determine_storage_tier(score.timeline_category, score.importance_level)
                    retention_policy = self.retention_mapping.get(score.importance_level, RetentionPolicy.MEDIUM_STANDARD)
                    
                    # Generate content hash for deduplication
                    content_hash = self._generate_content_hash(data_item.get('content', ''))
                    
                    # Extract relationships
                    relationships = await self._extract_relationships(project_id, data_item, score)
                    
                    # Create timeline entry
                    timeline_entry = TimelineEntry(
                        entry_id=entry_id,
                        project_id=project_id,
                        data_type=data_item.get('type', 'unknown'),
                        content_hash=content_hash,
                        importance_score=score.overall_score,
                        importance_level=score.importance_level,
                        timeline_category=score.timeline_category,
                        storage_tier=storage_tier,
                        retention_policy=retention_policy,
                        created_at=datetime.utcnow(),
                        last_accessed=datetime.utcnow(),
                        access_count=0,
                        metadata={
                            'original_data': data_item,
                            'scoring_metadata': score.metadata,
                            'storage_version': '1.0'
                        },
                        tags=self._extract_tags(data_item, score),
                        relationships=relationships
                    )
                    
                    # Store in timeline
                    self.timeline_entries[entry_id] = timeline_entry
                    self.project_timelines[project_id].append(entry_id)
                    
                    # Store in appropriate storage tier
                    await self._store_in_tier(timeline_entry)
                    
                    stored_entry_ids.append(entry_id)
                    
                except Exception as e:
                    logger.error(f"Failed to store item {i}: {str(e)}")
                    continue
            
            # Sort project timeline by creation time
            self.project_timelines[project_id].sort(
                key=lambda eid: self.timeline_entries[eid].created_at,
                reverse=True
            )
            
            logger.info(f"Successfully stored {len(stored_entry_ids)} items in timeline")
            return stored_entry_ids
            
        except Exception as e:
            logger.error(f"Timeline storage failed: {str(e)}")
            return []
    
    async def retrieve_timeline_data(self, project_id: str, 
                                   timeline_category: Optional[TimelineCategory] = None,
                                   importance_threshold: float = 0.0,
                                   limit: int = 100,
                                   include_archived: bool = False) -> List[Dict[str, Any]]:
        """Retrieve data from timeline with filtering options"""
        try:
            project_entry_ids = self.project_timelines.get(project_id, [])
            
            if not project_entry_ids:
                return []
            
            # Filter entries based on criteria
            filtered_entries = []
            
            for entry_id in project_entry_ids:
                entry = self.timeline_entries.get(entry_id)
                if not entry:
                    continue
                
                # Apply filters
                if timeline_category and entry.timeline_category != timeline_category:
                    continue
                
                if entry.importance_score < importance_threshold:
                    continue
                
                if not include_archived and entry.storage_tier == StorageTier.FROZEN:
                    continue
                
                filtered_entries.append(entry)
            
            # Sort by importance and recency
            filtered_entries.sort(
                key=lambda e: (e.importance_score, -e.created_at.timestamp()),
                reverse=True
            )
            
            # Limit results
            limited_entries = filtered_entries[:limit]
            
            # Track access patterns
            for entry in limited_entries:
                await self._track_access(entry.entry_id)
            
            # Convert to response format
            result_data = []
            for entry in limited_entries:
                data_item = entry.metadata.get('original_data', {})
                data_item.update({
                    'timeline_metadata': {
                        'entry_id': entry.entry_id,
                        'importance_score': entry.importance_score,
                        'importance_level': entry.importance_level.value,
                        'timeline_category': entry.timeline_category.value,
                        'storage_tier': entry.storage_tier.value,
                        'created_at': entry.created_at.isoformat(),
                        'last_accessed': entry.last_accessed.isoformat(),
                        'access_count': entry.access_count,
                        'tags': entry.tags,
                        'relationships': entry.relationships
                    }
                })
                result_data.append(data_item)
            
            logger.info(f"Retrieved {len(result_data)} timeline items for project {project_id}")
            return result_data
            
        except Exception as e:
            logger.error(f"Timeline retrieval failed: {str(e)}")
            return []
    
    async def get_timeline_analytics(self, project_id: str, days_back: int = 90) -> Dict[str, Any]:
        """Get analytics on timeline data distribution and patterns"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            project_entries = [
                self.timeline_entries[eid] 
                for eid in self.project_timelines.get(project_id, [])
                if eid in self.timeline_entries and self.timeline_entries[eid].created_at >= cutoff_date
            ]
            
            if not project_entries:
                return {}
            
            # Calculate distributions
            storage_distribution = defaultdict(int)
            importance_distribution = defaultdict(int)
            timeline_distribution = defaultdict(int)
            
            for entry in project_entries:
                storage_distribution[entry.storage_tier] += 1
                importance_distribution[entry.importance_level] += 1
                timeline_distribution[entry.timeline_category] += 1
            
            analytics = {
                'total_entries': len(project_entries),
                'average_importance': sum(e.importance_score for e in project_entries) / len(project_entries),
                'storage_distribution': {tier.value: count for tier, count in storage_distribution.items()},
                'importance_distribution': {level.value: count for level, count in importance_distribution.items()},
                'timeline_distribution': {cat.value: count for cat, count in timeline_distribution.items()}
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Timeline analytics generation failed: {str(e)}")
            return {}
    
    async def cleanup_expired_data(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Clean up expired data based on retention policies"""
        try:
            cleanup_stats = {
                'entries_analyzed': 0,
                'entries_deleted': 0,
                'entries_archived': 0
            }
            
            # Get entries to analyze
            if project_id:
                entry_ids = self.project_timelines.get(project_id, [])
            else:
                entry_ids = list(self.timeline_entries.keys())
            
            current_time = datetime.utcnow()
            
            for entry_id in entry_ids:
                entry = self.timeline_entries.get(entry_id)
                if not entry:
                    continue
                
                cleanup_stats['entries_analyzed'] += 1
                
                # Check if entry has expired
                retention_period = self.retention_periods.get(entry.retention_policy, 730)
                age_days = (current_time - entry.created_at).days
                
                if age_days > retention_period:
                    # Delete expired entry
                    await self._delete_timeline_entry(entry)
                    cleanup_stats['entries_deleted'] += 1
                    
                elif entry.storage_tier != StorageTier.FROZEN and age_days > self.tier_thresholds[StorageTier.COLD]:
                    # Archive old entries
                    await self._archive_timeline_entry(entry)
                    cleanup_stats['entries_archived'] += 1
            
            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {str(e)}")
            return {}
    
    def _determine_storage_tier(self, timeline_category: TimelineCategory, 
                              importance_level: ImportanceLevel) -> StorageTier:
        """Determine appropriate storage tier"""
        # Critical data always goes to hot storage
        if importance_level == ImportanceLevel.CRITICAL:
            return StorageTier.HOT
        
        # Recent data goes to hot/warm based on importance
        if timeline_category == TimelineCategory.RECENT:
            return StorageTier.HOT if importance_level in [ImportanceLevel.HIGH, ImportanceLevel.CRITICAL] else StorageTier.WARM
        
        # Last month data goes to warm/cold
        if timeline_category == TimelineCategory.LAST_MONTH:
            return StorageTier.WARM if importance_level == ImportanceLevel.HIGH else StorageTier.COLD
        
        # Older data goes to cold/frozen
        if timeline_category in [TimelineCategory.LAST_QUARTER, TimelineCategory.LAST_YEAR]:
            return StorageTier.COLD if importance_level in [ImportanceLevel.HIGH, ImportanceLevel.MEDIUM] else StorageTier.FROZEN
        
        # Historical data goes to frozen
        return StorageTier.FROZEN
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        import hashlib
        normalized_content = content.strip().lower()
        return hashlib.sha256(normalized_content.encode()).hexdigest()
    
    async def _extract_relationships(self, project_id: str, data_item: Dict[str, Any], score) -> List[str]:
        """Extract relationships to other timeline entries"""
        try:
            relationships = []
            
            # Simple relationship extraction based on content similarity
            content = data_item.get('content', '')
            if len(content) > 50:
                # Find similar entries
                similar_results = await self.vector_db.semantic_search(
                    query=content[:200],
                    project_id=project_id,
                    limit=3
                )
                
                for result in similar_results:
                    related_id = result.get('metadata', {}).get('timeline_entry_id')
                    if related_id:
                        relationships.append(related_id)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Relationship extraction failed: {str(e)}")
            return []
    
    def _extract_tags(self, data_item: Dict[str, Any], score) -> List[str]:
        """Extract tags from data item and scoring results"""
        tags = []
        
        # Add importance level as tag
        tags.append(f"importance_{score.importance_level.value}")
        
        # Add timeline category as tag
        tags.append(f"timeline_{score.timeline_category.value}")
        
        # Add data type as tag
        data_type = data_item.get('type', 'unknown')
        tags.append(f"type_{data_type}")
        
        # Extract content-based tags
        content = data_item.get('content', '').lower()
        if 'bug' in content or 'error' in content:
            tags.append('bug_related')
        if 'feature' in content or 'enhancement' in content:
            tags.append('feature_related')
        if 'decision' in content or 'decided' in content:
            tags.append('decision_related')
        
        return tags
    
    async def _store_in_tier(self, entry: TimelineEntry):
        """Store entry in appropriate storage tier"""
        try:
            # Store in vector database with tier information
            await self.vector_db.add_documents([{
                'id': f"timeline_{entry.entry_id}",
                'content': str(entry.metadata.get('original_data', {})),
                'metadata': {
                    'timeline_entry_id': entry.entry_id,
                    'project_id': entry.project_id,
                    'storage_tier': entry.storage_tier.value,
                    'importance_level': entry.importance_level.value,
                    'timeline_category': entry.timeline_category.value,
                    'created_at': entry.created_at.isoformat()
                }
            }])
            
            # Store in context service for persistence
            await self.context_service.store_context(
                project_id=entry.project_id,
                user_id="system",
                context_type=ContextType.DATA,
                scope=ContextScope.PROJECT,
                content=asdict(entry),
                metadata={
                    'storage_type': 'timeline_entry',
                    'storage_tier': entry.storage_tier.value,
                    'entry_id': entry.entry_id
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to store in tier: {str(e)}")
    
    async def _track_access(self, entry_id: str):
        """Track access to timeline entry"""
        try:
            if entry_id in self.timeline_entries:
                entry = self.timeline_entries[entry_id]
                entry.last_accessed = datetime.utcnow()
                entry.access_count += 1
                
                # Record access pattern
                self.access_patterns[entry_id].append(datetime.utcnow())
                
        except Exception as e:
            logger.error(f"Access tracking failed: {str(e)}")
    
    async def _delete_timeline_entry(self, entry: TimelineEntry):
        """Delete expired timeline entry"""
        try:
            # Remove from timeline entries
            if entry.entry_id in self.timeline_entries:
                del self.timeline_entries[entry.entry_id]
            
            # Remove from project timeline
            if entry.entry_id in self.project_timelines[entry.project_id]:
                self.project_timelines[entry.project_id].remove(entry.entry_id)
            
            # Clean up access patterns
            if entry.entry_id in self.access_patterns:
                del self.access_patterns[entry.entry_id]
            
        except Exception as e:
            logger.error(f"Timeline entry deletion failed: {str(e)}")
    
    async def _archive_timeline_entry(self, entry: TimelineEntry):
        """Archive timeline entry to frozen storage"""
        try:
            entry.storage_tier = StorageTier.FROZEN
            
        except Exception as e:
            logger.error(f"Timeline entry archiving failed: {str(e)}")
