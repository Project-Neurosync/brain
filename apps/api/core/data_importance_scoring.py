"""
Advanced Data Importance Scoring for NeuroSync
ML-powered system to intelligently score and filter data relevance
"""

import json
import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict, Counter
import re
import hashlib

from .vector_db import VectorDatabase
from .knowledge_graph import KnowledgeGraphBuilder
from .context_persistence import ContextPersistenceService, ContextType, ContextScope

logger = logging.getLogger(__name__)

class DataType(Enum):
    """Types of data that can be scored"""
    CODE = "code"
    MEETING = "meeting"
    ISSUE = "issue"
    DOCUMENT = "document"
    COMMENT = "comment"
    COMMIT = "commit"
    SLACK_MESSAGE = "slack_message"
    EMAIL = "email"
    CONFLUENCE_PAGE = "confluence_page"
    DECISION = "decision"

class ImportanceLevel(Enum):
    """Importance levels for data"""
    CRITICAL = "critical"      # 0.8-1.0 - Must keep
    HIGH = "high"             # 0.6-0.8 - Very important
    MEDIUM = "medium"         # 0.4-0.6 - Moderately important
    LOW = "low"               # 0.2-0.4 - Less important
    NOISE = "noise"           # 0.0-0.2 - Can be discarded

class TimelineCategory(Enum):
    """Timeline categories for data organization"""
    RECENT = "recent"                    # Last 7 days
    LAST_MONTH = "last_month"           # 8-30 days ago
    LAST_QUARTER = "last_quarter"       # 31-90 days ago
    LAST_YEAR = "last_year"             # 91-365 days ago
    HISTORICAL = "historical"           # Over 1 year ago

@dataclass
class ImportanceScore:
    """Detailed importance scoring result"""
    data_id: str
    data_type: DataType
    overall_score: float
    importance_level: ImportanceLevel
    timeline_category: TimelineCategory
    scoring_factors: Dict[str, float]
    confidence: float
    reasoning: List[str]
    metadata: Dict[str, Any]
    scored_at: datetime

@dataclass
class ScoringFeatures:
    """Features extracted for ML scoring"""
    # Content features
    content_length: int
    word_count: int
    technical_terms_count: int
    
    # Temporal features
    recency_days: float
    
    # Author features
    author_importance: float
    
    # Context features
    project_relevance: float
    keyword_density: float
    
    # Engagement features
    replies_count: int
    reactions_count: int
    
    # Structural features
    has_code: bool
    has_decisions: bool
    has_action_items: bool

class AdvancedDataImportanceScoring:
    """
    Advanced ML-powered data importance scoring system
    
    Features:
    - Multi-factor importance scoring with ML models
    - Timeline-based data organization and filtering
    - Context-aware relevance assessment
    - Duplicate detection and deduplication
    - Adaptive learning from user feedback
    """
    
    def __init__(self):
        self.vector_db = VectorDatabase()
        self.knowledge_graph = KnowledgeGraphBuilder()
        self.context_service = ContextPersistenceService()
        
        # Scoring models and weights
        self.scoring_weights = {
            'content_quality': 0.25,
            'temporal_relevance': 0.20,
            'author_importance': 0.15,
            'project_relevance': 0.20,
            'engagement_metrics': 0.10,
            'structural_features': 0.10
        }
        
        # Project-specific configurations
        self.project_configs: Dict[str, Dict[str, Any]] = {}
        
        # Learning and adaptation
        self.feedback_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Duplicate detection
        self.content_hashes: Dict[str, Set[str]] = defaultdict(set)
        self.similarity_threshold = 0.85
        
        # Timeline thresholds
        self.timeline_thresholds = {
            TimelineCategory.RECENT: 7,
            TimelineCategory.LAST_MONTH: 30,
            TimelineCategory.LAST_QUARTER: 90,
            TimelineCategory.LAST_YEAR: 365
        }
        
        # Critical keywords
        self.critical_keywords = {
            'technical': ['bug', 'critical', 'security', 'performance', 'breaking', 'urgent'],
            'business': ['decision', 'milestone', 'deadline', 'budget', 'strategy', 'goal'],
            'process': ['workflow', 'procedure', 'policy', 'standard', 'requirement']
        }
    
    async def score_data_importance(self, project_id: str, data_item: Dict[str, Any]) -> ImportanceScore:
        """Score the importance of a single data item"""
        try:
            data_id = data_item.get('id', str(uuid.uuid4()))
            data_type = DataType(data_item.get('type', 'document'))
            
            # Extract features for scoring
            features = await self._extract_scoring_features(project_id, data_item)
            
            # Calculate individual scoring factors
            scoring_factors = {
                'content_quality': self._score_content_quality(features, data_item),
                'temporal_relevance': self._score_temporal_relevance(features, data_item),
                'author_importance': await self._score_author_importance(project_id, features, data_item),
                'project_relevance': await self._score_project_relevance(project_id, features, data_item),
                'engagement_metrics': self._score_engagement_metrics(features, data_item),
                'structural_features': self._score_structural_features(features, data_item)
            }
            
            # Calculate weighted overall score
            overall_score = sum(
                score * self.scoring_weights[factor]
                for factor, score in scoring_factors.items()
            )
            
            # Apply project-specific adjustments
            overall_score = await self._apply_project_adjustments(
                project_id, overall_score, data_item, features
            )
            
            # Determine importance level and timeline category
            importance_level = self._determine_importance_level(overall_score)
            timeline_category = self._determine_timeline_category(data_item)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(scoring_factors, features)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(scoring_factors, features, data_item)
            
            importance_score = ImportanceScore(
                data_id=data_id,
                data_type=data_type,
                overall_score=overall_score,
                importance_level=importance_level,
                timeline_category=timeline_category,
                scoring_factors=scoring_factors,
                confidence=confidence,
                reasoning=reasoning,
                metadata={
                    'project_id': project_id,
                    'features': asdict(features),
                    'scoring_version': '2.0'
                },
                scored_at=datetime.utcnow()
            )
            
            # Store scoring result for learning
            await self._store_scoring_result(project_id, importance_score)
            
            return importance_score
            
        except Exception as e:
            logger.error(f"Data importance scoring failed: {str(e)}")
            # Return default score
            return ImportanceScore(
                data_id=data_item.get('id', str(uuid.uuid4())),
                data_type=DataType(data_item.get('type', 'document')),
                overall_score=0.5,
                importance_level=ImportanceLevel.MEDIUM,
                timeline_category=TimelineCategory.RECENT,
                scoring_factors={},
                confidence=0.5,
                reasoning=["Default scoring due to error"],
                metadata={},
                scored_at=datetime.utcnow()
            )
    
    async def score_batch(self, project_id: str, data_items: List[Dict[str, Any]]) -> List[ImportanceScore]:
        """Score multiple data items in batch for efficiency"""
        try:
            logger.info(f"Batch scoring {len(data_items)} items for project {project_id}")
            
            # Process items in parallel
            scoring_tasks = [
                self.score_data_importance(project_id, item)
                for item in data_items
            ]
            
            scores = await asyncio.gather(*scoring_tasks, return_exceptions=True)
            
            # Filter out exceptions and log errors
            valid_scores = []
            for i, score in enumerate(scores):
                if isinstance(score, Exception):
                    logger.error(f"Failed to score item {i}: {str(score)}")
                else:
                    valid_scores.append(score)
            
            logger.info(f"Successfully scored {len(valid_scores)}/{len(data_items)} items")
            return valid_scores
            
        except Exception as e:
            logger.error(f"Batch scoring failed: {str(e)}")
            return []
    
    async def detect_duplicates(self, project_id: str, data_items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Detect duplicate or near-duplicate content"""
        try:
            duplicates = {}
            content_signatures = {}
            
            for item in data_items:
                item_id = item.get('id', str(uuid.uuid4()))
                content = item.get('content', '')
                
                # Generate content signature
                signature = self._generate_content_signature(content)
                
                # Check for exact duplicates
                if signature in content_signatures:
                    original_id = content_signatures[signature]
                    if original_id not in duplicates:
                        duplicates[original_id] = []
                    duplicates[original_id].append(item_id)
                else:
                    content_signatures[signature] = item_id
                
                # Check for near-duplicates using semantic similarity
                similar_items = await self._find_similar_content(
                    project_id, content, item_id, threshold=self.similarity_threshold
                )
                
                if similar_items:
                    if item_id not in duplicates:
                        duplicates[item_id] = []
                    duplicates[item_id].extend(similar_items)
            
            logger.info(f"Found {len(duplicates)} duplicate groups in {len(data_items)} items")
            return duplicates
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {str(e)}")
            return {}
    
    async def organize_by_timeline(self, scores: List[ImportanceScore], 
                                 importance_threshold: float = 0.3) -> Dict[TimelineCategory, List[ImportanceScore]]:
        """Organize scored data by timeline categories"""
        try:
            timeline_data = {category: [] for category in TimelineCategory}
            
            # Filter by importance threshold and organize by timeline
            for score in scores:
                if score.overall_score >= importance_threshold:
                    timeline_data[score.timeline_category].append(score)
            
            # Sort each timeline category by importance score
            for category in timeline_data:
                timeline_data[category].sort(
                    key=lambda s: s.overall_score, reverse=True
                )
            
            return timeline_data
            
        except Exception as e:
            logger.error(f"Timeline organization failed: {str(e)}")
            return {category: [] for category in TimelineCategory}
    
    async def learn_from_feedback(self, project_id: str, data_id: str, 
                                feedback_score: float, user_id: str):
        """Learn from user feedback to improve scoring accuracy"""
        try:
            feedback_entry = {
                'data_id': data_id,
                'feedback_score': feedback_score,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'project_id': project_id
            }
            
            self.feedback_history[project_id].append(feedback_entry)
            
            # Store feedback for persistence
            await self.context_service.store_context(
                project_id=project_id,
                user_id=user_id,
                context_type=ContextType.FEEDBACK,
                scope=ContextScope.PROJECT,
                content=feedback_entry,
                metadata={'feedback_type': 'importance_scoring'}
            )
            
            logger.info(f"Recorded feedback for data {data_id} in project {project_id}")
            
        except Exception as e:
            logger.error(f"Learning from feedback failed: {str(e)}")
    
    async def _extract_scoring_features(self, project_id: str, data_item: Dict[str, Any]) -> ScoringFeatures:
        """Extract features from data item for scoring"""
        try:
            content = data_item.get('content', '')
            created_at = data_item.get('created_at', datetime.utcnow().isoformat())
            author = data_item.get('author', 'unknown')
            
            # Parse creation time
            try:
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                created_time = datetime.utcnow()
            
            # Content features
            word_count = len(content.split())
            technical_terms = self._count_technical_terms(content)
            
            # Temporal features
            recency_days = (datetime.utcnow() - created_time).days
            
            # Author features (simplified)
            author_importance = await self._get_author_importance(project_id, author)
            
            # Context features
            project_relevance = await self._calculate_project_relevance(project_id, content)
            keyword_density = self._calculate_keyword_density(content)
            
            # Engagement features
            replies_count = data_item.get('replies_count', 0)
            reactions_count = data_item.get('reactions_count', 0)
            
            # Structural features
            has_code = bool(re.search(r'```[\s\S]*?```|`[^`]+`', content))
            has_decisions = any(keyword in content.lower() for keyword in ['decided', 'decision', 'agreed'])
            has_action_items = any(keyword in content.lower() for keyword in ['todo', 'action item', 'follow up'])
            
            return ScoringFeatures(
                content_length=len(content),
                word_count=word_count,
                technical_terms_count=technical_terms,
                recency_days=recency_days,
                author_importance=author_importance,
                project_relevance=project_relevance,
                keyword_density=keyword_density,
                replies_count=replies_count,
                reactions_count=reactions_count,
                has_code=has_code,
                has_decisions=has_decisions,
                has_action_items=has_action_items
            )
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            # Return default features
            return ScoringFeatures(
                content_length=0, word_count=0, technical_terms_count=0,
                recency_days=0, author_importance=0.5, project_relevance=0.5,
                keyword_density=0.0, replies_count=0, reactions_count=0,
                has_code=False, has_decisions=False, has_action_items=False
            )
    
    def _score_content_quality(self, features: ScoringFeatures, data_item: Dict[str, Any]) -> float:
        """Score content quality based on various factors"""
        try:
            score = 0.0
            
            # Length and structure scoring
            if features.word_count > 50:
                score += 0.3
            if features.word_count > 200:
                score += 0.2
            
            # Technical content scoring
            if features.has_code:
                score += 0.3
            
            if features.technical_terms_count > 2:
                score += 0.2
            
            # Structural elements
            if features.has_decisions:
                score += 0.4
            
            if features.has_action_items:
                score += 0.3
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Content quality scoring failed: {str(e)}")
            return 0.5
    
    def _score_temporal_relevance(self, features: ScoringFeatures, data_item: Dict[str, Any]) -> float:
        """Score temporal relevance based on recency"""
        try:
            # Recency scoring (exponential decay)
            if features.recency_days <= 1:
                return 1.0
            elif features.recency_days <= 7:
                return 0.8
            elif features.recency_days <= 30:
                return 0.6
            elif features.recency_days <= 90:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Temporal relevance scoring failed: {str(e)}")
            return 0.5
    
    async def _score_author_importance(self, project_id: str, features: ScoringFeatures, 
                                     data_item: Dict[str, Any]) -> float:
        """Score based on author importance"""
        try:
            return features.author_importance
            
        except Exception as e:
            logger.error(f"Author importance scoring failed: {str(e)}")
            return 0.5
    
    async def _score_project_relevance(self, project_id: str, features: ScoringFeatures,
                                     data_item: Dict[str, Any]) -> float:
        """Score relevance to project context"""
        try:
            base_score = features.project_relevance
            keyword_boost = min(features.keyword_density * 0.3, 0.3)
            technical_boost = min(features.technical_terms_count * 0.05, 0.2)
            
            return min(base_score + keyword_boost + technical_boost, 1.0)
            
        except Exception as e:
            logger.error(f"Project relevance scoring failed: {str(e)}")
            return 0.5
    
    def _score_engagement_metrics(self, features: ScoringFeatures, data_item: Dict[str, Any]) -> float:
        """Score based on engagement metrics"""
        try:
            score = 0.0
            
            if features.replies_count > 0:
                score += min(features.replies_count * 0.1, 0.4)
            
            if features.reactions_count > 0:
                score += min(features.reactions_count * 0.05, 0.3)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Engagement metrics scoring failed: {str(e)}")
            return 0.0
    
    def _score_structural_features(self, features: ScoringFeatures, data_item: Dict[str, Any]) -> float:
        """Score based on structural features"""
        try:
            score = 0.0
            
            if features.has_code:
                score += 0.3
            
            if features.has_decisions:
                score += 0.4
            
            if features.has_action_items:
                score += 0.3
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Structural features scoring failed: {str(e)}")
            return 0.0
    
    async def _apply_project_adjustments(self, project_id: str, base_score: float,
                                       data_item: Dict[str, Any], features: ScoringFeatures) -> float:
        """Apply project-specific scoring adjustments"""
        try:
            config = self.project_configs.get(project_id, {})
            adjusted_score = base_score
            
            # Critical keyword boost
            content = data_item.get('content', '').lower()
            for keyword_type, keywords in self.critical_keywords.items():
                if any(keyword in content for keyword in keywords):
                    boost = config.get(f'{keyword_type}_boost', 0.1)
                    adjusted_score += boost
            
            return min(adjusted_score, 1.0)
            
        except Exception as e:
            logger.error(f"Project adjustments failed: {str(e)}")
            return base_score
    
    def _determine_importance_level(self, score: float) -> ImportanceLevel:
        """Determine importance level from score"""
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
    
    def _determine_timeline_category(self, data_item: Dict[str, Any]) -> TimelineCategory:
        """Determine timeline category from data item"""
        try:
            created_at = data_item.get('created_at', datetime.utcnow().isoformat())
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_ago = (datetime.utcnow() - created_time).days
            
            if days_ago <= self.timeline_thresholds[TimelineCategory.RECENT]:
                return TimelineCategory.RECENT
            elif days_ago <= self.timeline_thresholds[TimelineCategory.LAST_MONTH]:
                return TimelineCategory.LAST_MONTH
            elif days_ago <= self.timeline_thresholds[TimelineCategory.LAST_QUARTER]:
                return TimelineCategory.LAST_QUARTER
            elif days_ago <= self.timeline_thresholds[TimelineCategory.LAST_YEAR]:
                return TimelineCategory.LAST_YEAR
            else:
                return TimelineCategory.HISTORICAL
                
        except Exception as e:
            logger.error(f"Timeline category determination failed: {str(e)}")
            return TimelineCategory.RECENT
    
    def _calculate_confidence(self, scoring_factors: Dict[str, float], features: ScoringFeatures) -> float:
        """Calculate confidence in the scoring result"""
        try:
            # Base confidence on feature completeness
            feature_completeness = sum([
                1 if features.word_count > 10 else 0,
                1 if features.author_importance > 0 else 0,
                1 if features.project_relevance > 0 else 0,
                1 if features.recency_days >= 0 else 0
            ]) / 4
            
            return min(max(feature_completeness, 0.1), 1.0)
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {str(e)}")
            return 0.5
    
    def _generate_reasoning(self, scoring_factors: Dict[str, float], 
                          features: ScoringFeatures, data_item: Dict[str, Any]) -> List[str]:
        """Generate human-readable reasoning for the score"""
        try:
            reasoning = []
            
            # Top scoring factors
            sorted_factors = sorted(scoring_factors.items(), key=lambda x: x[1], reverse=True)
            
            for factor, score in sorted_factors[:3]:
                if score > 0.6:
                    if factor == 'content_quality':
                        reasoning.append(f"High content quality (score: {score:.2f})")
                    elif factor == 'temporal_relevance':
                        reasoning.append(f"Recent and timely content (score: {score:.2f})")
                    elif factor == 'structural_features':
                        reasoning.append(f"Contains important structural elements (score: {score:.2f})")
            
            if not reasoning:
                reasoning.append("Standard scoring applied")
            
            return reasoning
            
        except Exception as e:
            logger.error(f"Reasoning generation failed: {str(e)}")
            return ["Reasoning unavailable"]
    
    def _generate_content_signature(self, content: str) -> str:
        """Generate a signature for content to detect duplicates"""
        # Normalize content and create hash
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    async def _find_similar_content(self, project_id: str, content: str, 
                                  item_id: str, threshold: float) -> List[str]:
        """Find similar content using semantic search"""
        try:
            if len(content) < 50:  # Skip very short content
                return []
            
            # Use vector database for semantic similarity
            results = await self.vector_db.semantic_search(
                query=content[:500],  # Limit query length
                project_id=project_id,
                limit=5
            )
            
            similar_items = []
            for result in results:
                result_id = result.get('metadata', {}).get('id')
                if result_id and result_id != item_id:
                    # Simple similarity check (can be enhanced)
                    if len(result.get('content', '')) > 50:
                        similar_items.append(result_id)
            
            return similar_items
            
        except Exception as e:
            logger.error(f"Similar content search failed: {str(e)}")
            return []
    
    async def _get_author_importance(self, project_id: str, author: str) -> float:
        """Get author importance score"""
        try:
            # Simple author importance (can be enhanced with actual data)
            if author == 'unknown':
                return 0.3
            
            # Check if author is in knowledge graph
            author_entities = await self.knowledge_graph.find_related_entities(
                project_id=project_id,
                entity_type="person",
                limit=1
            )
            
            # Simple scoring based on presence in knowledge graph
            return 0.7 if author_entities else 0.5
            
        except Exception as e:
            logger.error(f"Author importance calculation failed: {str(e)}")
            return 0.5
    
    async def _calculate_project_relevance(self, project_id: str, content: str) -> float:
        """Calculate relevance to project context"""
        try:
            if len(content) < 20:
                return 0.3
            
            # Use vector search to find related project content
            results = await self.vector_db.semantic_search(
                query=content[:200],
                project_id=project_id,
                limit=3
            )
            
            # Simple relevance based on search results
            if results:
                return 0.8
            else:
                return 0.4
                
        except Exception as e:
            logger.error(f"Project relevance calculation failed: {str(e)}")
            return 0.5
    
    def _calculate_keyword_density(self, content: str) -> float:
        """Calculate density of important keywords"""
        try:
            if not content:
                return 0.0
            
            words = content.lower().split()
            if not words:
                return 0.0
            
            # Count important keywords
            all_keywords = []
            for keywords in self.critical_keywords.values():
                all_keywords.extend(keywords)
            
            keyword_count = sum(1 for word in words if word in all_keywords)
            return keyword_count / len(words)
            
        except Exception as e:
            logger.error(f"Keyword density calculation failed: {str(e)}")
            return 0.0
    
    def _count_technical_terms(self, content: str) -> int:
        """Count technical terms in content"""
        try:
            technical_patterns = [
                r'\b(?:API|SDK|HTTP|JSON|XML|SQL|REST|GraphQL)\b',
                r'\b(?:function|class|method|variable|parameter)\b',
                r'\b(?:database|server|client|endpoint|authentication)\b'
            ]
            
            count = 0
            for pattern in technical_patterns:
                count += len(re.findall(pattern, content, re.IGNORECASE))
            
            return count
            
        except Exception as e:
            logger.error(f"Technical terms counting failed: {str(e)}")
            return 0
    
    async def _store_scoring_result(self, project_id: str, score: ImportanceScore):
        """Store scoring result for learning and analytics"""
        try:
            await self.context_service.store_context(
                project_id=project_id,
                user_id="system",
                context_type=ContextType.ANALYSIS,
                scope=ContextScope.PROJECT,
                content=asdict(score),
                metadata={
                    'analysis_type': 'importance_scoring',
                    'data_type': score.data_type.value,
                    'importance_level': score.importance_level.value,
                    'timeline_category': score.timeline_category.value
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to store scoring result: {str(e)}")
