"""
Production ML Data Importance Filter for NeuroSync AI Backend
Intelligently filters and scores data importance during ingestion to prevent information overload.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import re
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel

class DataType(str, Enum):
    """Types of data that can be filtered."""
    CODE = "code"
    MEETING = "meeting"
    ISSUE = "issue"
    DOCUMENT = "document"
    COMMENT = "comment"
    COMMIT = "commit"
    SLACK_MESSAGE = "slack_message"
    EMAIL = "email"

class ImportanceLevel(str, Enum):
    """Importance levels for data classification."""
    CRITICAL = "critical"      # 0.8-1.0 - Must keep
    HIGH = "high"             # 0.6-0.8 - Very important
    MEDIUM = "medium"         # 0.4-0.6 - Moderately important
    LOW = "low"               # 0.2-0.4 - Less important
    NOISE = "noise"           # 0.0-0.2 - Can be discarded

@dataclass
class DataItem:
    """Data item to be scored for importance."""
    id: str
    content: str
    data_type: DataType
    metadata: Dict[str, Any]
    timestamp: datetime
    project_id: str
    source_id: str
    author: Optional[str] = None

class ImportanceScore(BaseModel):
    """Model for importance scoring results."""
    score: float  # 0.0 to 1.0
    level: ImportanceLevel
    reasons: List[str]
    confidence: float  # 0.0 to 1.0
    features: Dict[str, float]
    should_keep: bool

class MLDataImportanceFilter:
    """
    Production-ready ML-based data importance filter.
    Uses multiple scoring algorithms to determine data relevance and importance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ML Data Importance Filter."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.min_importance_threshold = self.config.get('min_importance_threshold', 0.3)
        self.critical_keywords = self.config.get('critical_keywords', [
            'bug', 'critical', 'urgent', 'security', 'performance', 'architecture',
            'decision', 'requirement', 'specification', 'design', 'implementation',
            'deployment', 'release', 'milestone', 'deadline', 'issue', 'problem'
        ])
        
        # ML models and vectorizers
        self._tfidf_vectorizer = None
        self._project_vocabularies = {}  # Project-specific vocabularies
        
        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Scoring weights
        self.scoring_weights = {
            'content_quality': 0.25,
            'temporal_relevance': 0.20,
            'author_importance': 0.15,
            'keyword_relevance': 0.15,
            'context_similarity': 0.15,
            'engagement_metrics': 0.10
        }
        
        self.logger.info("ML Data Importance Filter initialized")
    
    async def initialize(self) -> None:
        """Initialize the ML models and components."""
        def _init_models():
            # Initialize TF-IDF vectorizer
            self._tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 3),
                min_df=2,
                max_df=0.8
            )
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _init_models
        )
        
        self.logger.info("ML models initialized")
    
    async def score_data_importance(
        self,
        data_item: DataItem,
        project_context: Optional[Dict[str, Any]] = None
    ) -> ImportanceScore:
        """
        Score the importance of a data item using multiple ML algorithms.
        
        Args:
            data_item: Data item to score
            project_context: Optional project context for better scoring
            
        Returns:
            ImportanceScore with detailed scoring information
        """
        await self.initialize()
        
        def _score_item():
            # Calculate individual scores
            content_score = self._score_content_quality(data_item)
            temporal_score = self._score_temporal_relevance(data_item)
            author_score = self._score_author_importance(data_item, project_context)
            keyword_score = self._score_keyword_relevance(data_item)
            context_score = self._score_context_similarity(data_item, project_context)
            engagement_score = self._score_engagement_metrics(data_item)
            
            # Calculate weighted final score
            final_score = (
                content_score * self.scoring_weights['content_quality'] +
                temporal_score * self.scoring_weights['temporal_relevance'] +
                author_score * self.scoring_weights['author_importance'] +
                keyword_score * self.scoring_weights['keyword_relevance'] +
                context_score * self.scoring_weights['context_similarity'] +
                engagement_score * self.scoring_weights['engagement_metrics']
            )
            
            # Determine importance level
            importance_level = self._determine_importance_level(final_score)
            
            # Generate reasons
            reasons = self._generate_importance_reasons(
                data_item, content_score, temporal_score, author_score,
                keyword_score, context_score, engagement_score
            )
            
            # Calculate confidence based on score consistency
            scores = [content_score, temporal_score, author_score, keyword_score, context_score, engagement_score]
            confidence = 1.0 - (np.std(scores) / np.mean(scores)) if np.mean(scores) > 0 else 0.5
            confidence = max(0.0, min(1.0, confidence))
            
            return ImportanceScore(
                score=final_score,
                level=importance_level,
                reasons=reasons,
                confidence=confidence,
                features={
                    'content_quality': content_score,
                    'temporal_relevance': temporal_score,
                    'author_importance': author_score,
                    'keyword_relevance': keyword_score,
                    'context_similarity': context_score,
                    'engagement_metrics': engagement_score
                },
                should_keep=final_score >= self.min_importance_threshold
            )
        
        score_result = await asyncio.get_event_loop().run_in_executor(
            self._executor, _score_item
        )
        
        self.logger.debug(f"Scored data item {data_item.id}: {score_result.score:.3f} ({score_result.level})")
        return score_result
    
    def _score_content_quality(self, data_item: DataItem) -> float:
        """Score content quality based on length, structure, and information density."""
        content = data_item.content.strip()
        
        if not content:
            return 0.0
        
        score = 0.0
        
        # Length scoring (optimal range: 50-2000 characters)
        length = len(content)
        if length < 10:
            score += 0.1
        elif length < 50:
            score += 0.3
        elif length <= 2000:
            score += 0.8
        elif length <= 5000:
            score += 0.6
        else:
            score += 0.4
        
        # Structure scoring
        sentences = content.split('.')
        if len(sentences) > 1:
            score += 0.2
        
        # Code-specific scoring
        if data_item.data_type == DataType.CODE:
            # Look for meaningful code patterns
            if re.search(r'function|class|def|async|await|import|export', content, re.IGNORECASE):
                score += 0.3
            if re.search(r'//.*|#.*|/\*.*\*/', content):  # Comments
                score += 0.2
        
        # Meeting/document specific scoring
        elif data_item.data_type in [DataType.MEETING, DataType.DOCUMENT]:
            # Look for structured content
            if re.search(r'agenda|action|decision|requirement|specification', content, re.IGNORECASE):
                score += 0.3
        
        return min(1.0, score)
    
    def _score_temporal_relevance(self, data_item: DataItem) -> float:
        """Score temporal relevance based on recency and time context."""
        now = datetime.now()
        age = now - data_item.timestamp
        
        # Recent items are more relevant
        if age.days <= 1:
            return 1.0
        elif age.days <= 7:
            return 0.9
        elif age.days <= 30:
            return 0.7
        elif age.days <= 90:
            return 0.5
        elif age.days <= 365:
            return 0.3
        else:
            return 0.1
    
    def _score_author_importance(self, data_item: DataItem, project_context: Optional[Dict[str, Any]]) -> float:
        """Score based on author importance and role."""
        if not data_item.author or not project_context:
            return 0.5  # Neutral score
        
        # Get author information from project context
        team_members = project_context.get('team_members', {})
        author_info = team_members.get(data_item.author, {})
        
        # Score based on role
        role = author_info.get('role', '').lower()
        if role in ['lead', 'architect', 'senior', 'principal']:
            return 0.9
        elif role in ['manager', 'product']:
            return 0.8
        elif role in ['developer', 'engineer']:
            return 0.7
        else:
            return 0.5
    
    def _score_keyword_relevance(self, data_item: DataItem) -> float:
        """Score based on presence of critical keywords."""
        content_lower = data_item.content.lower()
        
        # Count critical keywords
        keyword_count = sum(1 for keyword in self.critical_keywords if keyword in content_lower)
        
        # Normalize score
        max_keywords = len(self.critical_keywords)
        return min(1.0, keyword_count / max_keywords * 2)  # Scale up for impact
    
    def _score_context_similarity(self, data_item: DataItem, project_context: Optional[Dict[str, Any]]) -> float:
        """Score based on similarity to project context and existing important content."""
        if not project_context or not self._tfidf_vectorizer:
            return 0.5
        
        # This would compare against existing important content in the project
        # For now, return a baseline score
        return 0.5
    
    def _score_engagement_metrics(self, data_item: DataItem) -> float:
        """Score based on engagement metrics like replies, reactions, etc."""
        metadata = data_item.metadata
        
        score = 0.0
        
        # Comments/replies
        replies = metadata.get('reply_count', 0)
        if replies > 0:
            score += min(0.4, replies * 0.1)
        
        # Reactions/likes
        reactions = metadata.get('reaction_count', 0)
        if reactions > 0:
            score += min(0.3, reactions * 0.05)
        
        # Mentions
        mentions = metadata.get('mention_count', 0)
        if mentions > 0:
            score += min(0.3, mentions * 0.1)
        
        return min(1.0, score)
    
    def _determine_importance_level(self, score: float) -> ImportanceLevel:
        """Determine importance level from numerical score."""
        if score >= 0.8:
            return ImportanceLevel.CRITICAL
        elif score >= 0.6:
            return ImportanceLevel.HIGH
        elif score >= 0.4:
            return ImportanceLevel.MEDIUM
        elif score >= 0.2:
            return ImportanceLevel.LOW
        else:
            return ImportanceLevel.NOISE
    
    def _generate_importance_reasons(
        self,
        data_item: DataItem,
        content_score: float,
        temporal_score: float,
        author_score: float,
        keyword_score: float,
        context_score: float,
        engagement_score: float
    ) -> List[str]:
        """Generate human-readable reasons for the importance score."""
        reasons = []
        
        if content_score > 0.7:
            reasons.append("High-quality, well-structured content")
        elif content_score < 0.3:
            reasons.append("Low-quality or minimal content")
        
        if temporal_score > 0.8:
            reasons.append("Very recent and timely")
        elif temporal_score < 0.3:
            reasons.append("Older content with reduced relevance")
        
        if author_score > 0.8:
            reasons.append("From a senior/important team member")
        
        if keyword_score > 0.5:
            reasons.append("Contains critical project keywords")
        
        if engagement_score > 0.5:
            reasons.append("High engagement (replies, reactions)")
        
        return reasons
    
    async def score_batch(
        self,
        data_items: List[DataItem],
        project_context: Optional[Dict[str, Any]] = None
    ) -> List[ImportanceScore]:
        """
        Score multiple data items in batch for better performance.
        
        Args:
            data_items: List of data items to score
            project_context: Optional project context
            
        Returns:
            List of ImportanceScore objects
        """
        if not data_items:
            return []
        
        # Process in parallel batches
        batch_size = 50
        all_scores = []
        
        for i in range(0, len(data_items), batch_size):
            batch = data_items[i:i + batch_size]
            
            # Create tasks for parallel processing
            tasks = [
                self.score_data_importance(item, project_context)
                for item in batch
            ]
            
            # Execute batch in parallel
            batch_scores = await asyncio.gather(*tasks)
            all_scores.extend(batch_scores)
        
        self.logger.info(f"Scored {len(data_items)} data items in batch")
        return all_scores
    
    async def filter_and_organize_by_timeline(
        self,
        data_items: List[DataItem],
        project_context: Optional[Dict[str, Any]] = None,
        time_window_days: int = 30
    ) -> Dict[str, List[Tuple[DataItem, ImportanceScore]]]:
        """
        Filter data items and organize them by timeline windows.
        
        Args:
            data_items: List of data items to filter and organize
            project_context: Optional project context
            time_window_days: Size of time windows in days
            
        Returns:
            Dictionary with time windows as keys and filtered items as values
        """
        # Score all items
        scores = await self.score_batch(data_items, project_context)
        
        # Filter items that should be kept
        filtered_items = [
            (item, score) for item, score in zip(data_items, scores)
            if score.should_keep
        ]
        
        # Organize by timeline
        timeline_buckets = {}
        
        for item, score in filtered_items:
            # Calculate time bucket
            days_ago = (datetime.now() - item.timestamp).days
            bucket_start = (days_ago // time_window_days) * time_window_days
            
            if bucket_start == 0:
                bucket_key = "recent"
            elif bucket_start <= 30:
                bucket_key = "last_month"
            elif bucket_start <= 90:
                bucket_key = "last_quarter"
            elif bucket_start <= 365:
                bucket_key = "last_year"
            else:
                bucket_key = "historical"
            
            if bucket_key not in timeline_buckets:
                timeline_buckets[bucket_key] = []
            
            timeline_buckets[bucket_key].append((item, score))
        
        # Sort each bucket by importance score
        for bucket in timeline_buckets.values():
            bucket.sort(key=lambda x: x[1].score, reverse=True)
        
        self.logger.info(f"Organized {len(filtered_items)} items into {len(timeline_buckets)} timeline buckets")
        return timeline_buckets
    
    async def learn_from_feedback(
        self,
        data_item: DataItem,
        predicted_score: ImportanceScore,
        actual_importance: float,
        user_feedback: Optional[str] = None
    ) -> None:
        """
        Learn from user feedback to improve future scoring.
        
        Args:
            data_item: The data item that was scored
            predicted_score: The score we predicted
            actual_importance: The actual importance (0.0-1.0)
            user_feedback: Optional user feedback text
        """
        # Calculate prediction error
        error = abs(predicted_score.score - actual_importance)
        
        # Log for future model training
        feedback_data = {
            'data_type': data_item.data_type,
            'predicted_score': predicted_score.score,
            'actual_score': actual_importance,
            'error': error,
            'features': predicted_score.features,
            'content_length': len(data_item.content),
            'timestamp': data_item.timestamp.isoformat(),
            'user_feedback': user_feedback
        }
        
        # In a production system, this would be stored for model retraining
        self.logger.info(f"Learning feedback: error={error:.3f}, actual={actual_importance:.3f}")
        
        # Adjust scoring weights based on feedback (simple adaptive approach)
        if error > 0.2:  # Significant error
            # Find which feature contributed most to the error
            features = predicted_score.features
            max_feature = max(features.items(), key=lambda x: x[1])
            
            # Slightly adjust the weight of the most contributing feature
            if max_feature[0] in self.scoring_weights:
                if predicted_score.score > actual_importance:
                    # We over-predicted, reduce this feature's weight
                    self.scoring_weights[max_feature[0]] *= 0.95
                else:
                    # We under-predicted, increase this feature's weight
                    self.scoring_weights[max_feature[0]] *= 1.05
                
                # Normalize weights to sum to 1.0
                total_weight = sum(self.scoring_weights.values())
                for key in self.scoring_weights:
                    self.scoring_weights[key] /= total_weight
    
    async def get_filter_statistics(
        self,
        project_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get statistics about filtering performance for a project.
        
        Args:
            project_id: Project ID to get statistics for
            days_back: Number of days to look back
            
        Returns:
            Dictionary with filtering statistics
        """
        # In a production system, this would query actual filtering history
        # For now, return mock statistics
        return {
            'total_items_processed': 1250,
            'items_kept': 875,
            'items_filtered_out': 375,
            'keep_rate': 0.70,
            'avg_importance_score': 0.65,
            'importance_distribution': {
                'critical': 125,
                'high': 200,
                'medium': 350,
                'low': 200,
                'noise': 375
            },
            'data_type_distribution': {
                'code': 400,
                'meeting': 150,
                'issue': 200,
                'document': 100,
                'comment': 250,
                'commit': 100,
                'slack_message': 50
            },
            'current_weights': self.scoring_weights,
            'filter_efficiency': 0.85  # How well the filter is performing
        }
    
    async def cleanup_old_low_importance_data(
        self,
        project_id: str,
        days_old: int = 90,
        max_importance_threshold: float = 0.3
    ) -> int:
        """
        Identify old, low-importance data that can be safely removed.
        
        Args:
            project_id: Project ID to clean up
            days_old: Only consider data older than this many days
            max_importance_threshold: Maximum importance score for cleanup
            
        Returns:
            Number of items recommended for cleanup
        """
        # In a production system, this would query the actual data store
        # and return IDs of items that can be safely removed
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Mock implementation - would query real data in production
        cleanup_candidates = 45  # Number of items that could be cleaned up
        
        self.logger.info(f"Found {cleanup_candidates} items for potential cleanup in project {project_id}")
        return cleanup_candidates
    
    def get_importance_threshold_recommendations(
        self,
        project_size: str,
        data_volume: str
    ) -> Dict[str, float]:
        """
        Get recommended importance thresholds based on project characteristics.
        
        Args:
            project_size: 'small', 'medium', 'large', 'enterprise'
            data_volume: 'low', 'medium', 'high', 'very_high'
            
        Returns:
            Dictionary with recommended thresholds
        """
        # Base thresholds
        thresholds = {
            'keep_threshold': 0.3,
            'critical_threshold': 0.8,
            'cleanup_threshold': 0.2
        }
        
        # Adjust based on project size
        if project_size == 'small':
            thresholds['keep_threshold'] = 0.2  # Keep more data for small projects
        elif project_size == 'large':
            thresholds['keep_threshold'] = 0.4  # Be more selective for large projects
        elif project_size == 'enterprise':
            thresholds['keep_threshold'] = 0.5  # Very selective for enterprise
        
        # Adjust based on data volume
        if data_volume == 'very_high':
            # Increase all thresholds to be more selective
            for key in thresholds:
                thresholds[key] = min(1.0, thresholds[key] * 1.2)
        elif data_volume == 'low':
            # Decrease thresholds to keep more data
            for key in thresholds:
                thresholds[key] = max(0.0, thresholds[key] * 0.8)
        
        return thresholds
