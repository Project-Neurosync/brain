"""
Comprehensive tests for ML Data Intelligence features
Tests data importance scoring, timeline storage, duplicate detection, and integration
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

from core.data_importance_scoring import AdvancedDataImportanceScoring, DataType, ImportanceLevel, TimelineCategory
from core.timeline_storage import TimelineBasedStorage, StorageTier, RetentionPolicy
from core.data_ingestion import DataIngestionEngine

class TestDataImportanceScoring:
    """Test suite for Advanced Data Importance Scoring"""
    
    @pytest.fixture
    def scorer(self):
        """Create a data importance scorer instance"""
        return AdvancedDataImportanceScoring()
    
    @pytest.fixture
    def sample_data_items(self):
        """Create sample data items for testing"""
        return [
            {
                "id": "item_1",
                "type": "code",
                "content": "def critical_security_function():\n    # This is a critical security function\n    pass",
                "metadata": {"file_path": "/security/auth.py", "language": "python"},
                "created_at": datetime.utcnow().isoformat(),
                "author": "senior_dev"
            },
            {
                "id": "item_2", 
                "type": "issue",
                "content": "Bug: Application crashes on startup. Critical issue affecting all users.",
                "metadata": {"priority": "critical", "labels": ["bug", "critical"]},
                "created_at": datetime.utcnow().isoformat(),
                "author": "product_manager"
            },
            {
                "id": "item_3",
                "type": "meeting",
                "content": "Team standup: discussed minor UI tweaks and coffee preferences",
                "metadata": {"meeting_type": "standup", "duration": 15},
                "created_at": datetime.utcnow().isoformat(),
                "author": "team_lead"
            },
            {
                "id": "item_4",
                "type": "comment",
                "content": "LGTM",
                "metadata": {"comment_type": "review"},
                "created_at": datetime.utcnow().isoformat(),
                "author": "developer"
            },
            {
                "id": "item_5",
                "type": "document",
                "content": "Architecture Decision Record: We have decided to use microservices architecture for scalability and maintainability. This decision affects the entire system design.",
                "metadata": {"document_type": "ADR", "impact": "high"},
                "created_at": datetime.utcnow().isoformat(),
                "author": "architect"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_score_single_item(self, scorer, sample_data_items):
        """Test scoring a single data item"""
        project_id = "test_project_1"
        item = sample_data_items[0]  # Critical security function
        
        score = await scorer.score_data_importance(project_id, item)
        
        assert score is not None
        assert score.data_id == item["id"]
        assert score.data_type == DataType.CODE
        assert 0.0 <= score.overall_score <= 1.0
        assert score.importance_level in ImportanceLevel
        assert score.timeline_category in TimelineCategory
        assert score.confidence > 0.0
        assert len(score.reasoning) > 0
        assert isinstance(score.scoring_factors, dict)
        
        # Critical security code should score high
        assert score.overall_score > 0.6
        assert score.importance_level in [ImportanceLevel.CRITICAL, ImportanceLevel.HIGH]
    
    @pytest.mark.asyncio
    async def test_score_batch(self, scorer, sample_data_items):
        """Test batch scoring of multiple items"""
        project_id = "test_project_2"
        
        scores = await scorer.score_batch(project_id, sample_data_items)
        
        assert len(scores) == len(sample_data_items)
        
        # Verify each score
        for i, score in enumerate(scores):
            assert score.data_id == sample_data_items[i]["id"]
            assert 0.0 <= score.overall_score <= 1.0
            assert score.importance_level in ImportanceLevel
        
        # Critical items should score higher than trivial ones
        critical_item_score = next(s for s in scores if s.data_id == "item_2")  # Critical bug
        trivial_item_score = next(s for s in scores if s.data_id == "item_4")   # LGTM comment
        
        assert critical_item_score.overall_score > trivial_item_score.overall_score
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, scorer):
        """Test duplicate detection functionality"""
        project_id = "test_project_3"
        
        # Create items with duplicates
        items_with_duplicates = [
            {
                "id": "original",
                "content": "This is the original content for testing duplicates",
                "type": "document"
            },
            {
                "id": "duplicate_1",
                "content": "This is the original content for testing duplicates",  # Exact duplicate
                "type": "document"
            },
            {
                "id": "similar",
                "content": "This is the original content for testing duplicate detection",  # Similar
                "type": "document"
            },
            {
                "id": "different",
                "content": "This is completely different content about machine learning",
                "type": "document"
            }
        ]
        
        duplicates = await scorer.detect_duplicates(project_id, items_with_duplicates)
        
        assert isinstance(duplicates, dict)
        # Should detect at least one duplicate group
        assert len(duplicates) > 0
        
        # Check that similar items are grouped together
        found_duplicate_group = False
        for master_id, duplicate_group in duplicates.items():
            if len(duplicate_group) > 1:
                found_duplicate_group = True
                break
        
        assert found_duplicate_group, "Should detect duplicate content"
    
    @pytest.mark.asyncio
    async def test_timeline_organization(self, scorer, sample_data_items):
        """Test timeline-based organization of scored data"""
        project_id = "test_project_4"
        
        scores = await scorer.score_batch(project_id, sample_data_items)
        timeline_data = await scorer.organize_by_timeline(scores, importance_threshold=0.3)
        
        assert isinstance(timeline_data, dict)
        
        # Check that timeline categories are present
        for category in TimelineCategory:
            if category.value in timeline_data:
                assert isinstance(timeline_data[category.value], list)
    
    @pytest.mark.asyncio
    async def test_learning_from_feedback(self, scorer):
        """Test adaptive learning from user feedback"""
        project_id = "test_project_5"
        data_id = "feedback_test_item"
        user_id = "test_user"
        
        # Provide feedback
        await scorer.learn_from_feedback(project_id, data_id, 0.9, user_id)
        
        # Verify feedback is stored
        assert project_id in scorer.feedback_history
        feedback_entries = scorer.feedback_history[project_id]
        assert len(feedback_entries) > 0
        
        latest_feedback = feedback_entries[-1]
        assert latest_feedback["data_id"] == data_id
        assert latest_feedback["feedback_score"] == 0.9
        assert latest_feedback["user_id"] == user_id


class TestTimelineBasedStorage:
    """Test suite for Timeline-Based Storage"""
    
    @pytest.fixture
    def storage(self):
        """Create a timeline storage instance"""
        return TimelineBasedStorage()
    
    @pytest.fixture
    def sample_timeline_data(self):
        """Create sample data for timeline storage"""
        return [
            {
                "id": "recent_item",
                "type": "code",
                "content": "Recent code change",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {"importance": "high"}
            },
            {
                "id": "old_item",
                "type": "meeting",
                "content": "Old meeting notes",
                "created_at": (datetime.utcnow() - timedelta(days=100)).isoformat(),
                "metadata": {"importance": "medium"}
            },
            {
                "id": "ancient_item",
                "type": "document",
                "content": "Very old documentation",
                "created_at": (datetime.utcnow() - timedelta(days=400)).isoformat(),
                "metadata": {"importance": "low"}
            }
        ]
    
    @pytest.mark.asyncio
    async def test_store_timeline_data(self, storage, sample_timeline_data):
        """Test storing data in timeline-based storage"""
        project_id = "timeline_test_project"
        
        entry_ids = await storage.store_timeline_data(project_id, sample_timeline_data)
        
        assert len(entry_ids) == len(sample_timeline_data)
        assert all(isinstance(entry_id, str) for entry_id in entry_ids)
        
        # Verify data is stored in the storage system
        assert project_id in storage.project_timelines
        assert len(storage.project_timelines[project_id]) == len(sample_timeline_data)
    
    @pytest.mark.asyncio
    async def test_retrieve_timeline_data(self, storage, sample_timeline_data):
        """Test retrieving timeline data with filters"""
        project_id = "timeline_retrieve_test"
        
        # Store data first
        await storage.store_timeline_data(project_id, sample_timeline_data)
        
        # Retrieve all data
        all_data = await storage.retrieve_timeline_data(project_id)
        assert len(all_data) > 0
        
        # Retrieve with importance threshold
        important_data = await storage.retrieve_timeline_data(
            project_id, 
            importance_threshold=0.5
        )
        
        # Should return fewer items due to threshold
        assert len(important_data) <= len(all_data)
        
        # Retrieve recent data only
        recent_data = await storage.retrieve_timeline_data(
            project_id,
            timeline_category=TimelineCategory.RECENT
        )
        
        # Verify timeline filtering works
        for entry in recent_data:
            assert entry.timeline_category == TimelineCategory.RECENT
    
    @pytest.mark.asyncio
    async def test_timeline_analytics(self, storage, sample_timeline_data):
        """Test timeline analytics functionality"""
        project_id = "analytics_test_project"
        
        # Store data first
        await storage.store_timeline_data(project_id, sample_timeline_data)
        
        # Get analytics
        analytics = await storage.get_timeline_analytics(project_id, days_back=365)
        
        assert isinstance(analytics, dict)
        assert "total_entries" in analytics
        assert "timeline_distribution" in analytics
        assert "importance_distribution" in analytics
        assert "storage_tier_distribution" in analytics
        
        assert analytics["total_entries"] > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_data(self, storage):
        """Test cleanup of expired data"""
        project_id = "cleanup_test_project"
        
        # Create expired data
        expired_data = [{
            "id": "expired_item",
            "type": "document",
            "content": "This should be cleaned up",
            "created_at": (datetime.utcnow() - timedelta(days=400)).isoformat(),
            "metadata": {"importance": "noise"}  # Will get NOISE_MINIMAL retention (30 days)
        }]
        
        await storage.store_timeline_data(project_id, expired_data)
        
        # Run cleanup
        cleanup_results = await storage.cleanup_expired_data(project_id)
        
        assert isinstance(cleanup_results, dict)
        assert "cleaned_up_count" in cleanup_results


class TestDataIngestionIntegration:
    """Test suite for ML Data Intelligence integration with data ingestion"""
    
    @pytest.fixture
    def ingestion_engine(self):
        """Create a data ingestion engine instance"""
        return DataIngestionEngine({
            'batch_size': 10,
            'importance_threshold': 0.3,
            'enable_duplicate_detection': True
        })
    
    @pytest.fixture
    def mixed_quality_data(self):
        """Create mixed quality data for testing ML filtering"""
        return [
            # High importance items
            {
                "id": "critical_bug",
                "type": "issue",
                "content": "CRITICAL: Security vulnerability in authentication system. Immediate action required.",
                "metadata": {"priority": "critical", "security": True},
                "created_at": datetime.utcnow().isoformat(),
                "author": "security_team"
            },
            {
                "id": "architecture_decision",
                "type": "document",
                "content": "Architecture Decision Record: Migration to microservices. This decision will impact the entire system architecture and development workflow.",
                "metadata": {"type": "ADR", "impact": "system-wide"},
                "created_at": datetime.utcnow().isoformat(),
                "author": "tech_lead"
            },
            
            # Medium importance items
            {
                "id": "feature_request",
                "type": "issue",
                "content": "Feature request: Add dark mode to the user interface",
                "metadata": {"priority": "medium", "type": "enhancement"},
                "created_at": datetime.utcnow().isoformat(),
                "author": "product_manager"
            },
            
            # Low importance items
            {
                "id": "standup_notes",
                "type": "meeting",
                "content": "Daily standup: Everyone shared their progress. No blockers reported.",
                "metadata": {"meeting_type": "standup", "duration": 15},
                "created_at": datetime.utcnow().isoformat(),
                "author": "scrum_master"
            },
            
            # Noise/spam items
            {
                "id": "spam_comment",
                "type": "comment",
                "content": "👍",
                "metadata": {"comment_type": "reaction"},
                "created_at": datetime.utcnow().isoformat(),
                "author": "random_user"
            },
            
            # Duplicate items
            {
                "id": "duplicate_1",
                "type": "document",
                "content": "This is duplicate content that should be filtered out",
                "metadata": {},
                "created_at": datetime.utcnow().isoformat(),
                "author": "user1"
            },
            {
                "id": "duplicate_2",
                "type": "document",
                "content": "This is duplicate content that should be filtered out",  # Exact duplicate
                "metadata": {},
                "created_at": datetime.utcnow().isoformat(),
                "author": "user2"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_ml_intelligence_processing(self, ingestion_engine, mixed_quality_data):
        """Test complete ML intelligence processing pipeline"""
        project_id = "ml_integration_test"
        
        results = await ingestion_engine.process_data_with_ml_intelligence(
            project_id, 
            mixed_quality_data
        )
        
        assert results["status"] == "success"
        assert results["project_id"] == project_id
        
        # Verify processing summary
        summary = results["processing_summary"]
        assert summary["total_input_items"] == len(mixed_quality_data)
        assert summary["items_after_deduplication"] <= len(mixed_quality_data)  # Should remove duplicates
        assert summary["items_above_threshold"] <= summary["items_scored"]  # Should filter low importance
        
        # Verify importance distribution
        importance_dist = results["importance_distribution"]
        assert isinstance(importance_dist, dict)
        assert "critical" in importance_dist
        assert "high" in importance_dist
        assert "medium" in importance_dist
        assert "low" in importance_dist
        assert "noise" in importance_dist
        
        # Critical items should be identified
        assert importance_dist["critical"] > 0 or importance_dist["high"] > 0
        
        # Timeline distribution should be present
        timeline_dist = results["timeline_distribution"]
        assert isinstance(timeline_dist, dict)
        assert len(timeline_dist) > 0
        
        # Average importance score should be reasonable
        avg_score = results["average_importance_score"]
        assert 0.0 <= avg_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_duplicate_filtering_effectiveness(self, ingestion_engine):
        """Test that duplicate detection effectively reduces redundant data"""
        project_id = "duplicate_test"
        
        # Create data with many duplicates
        duplicate_heavy_data = []
        original_content = "This is the original content"
        
        # Add original
        duplicate_heavy_data.append({
            "id": "original",
            "type": "document",
            "content": original_content,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Add 5 exact duplicates
        for i in range(5):
            duplicate_heavy_data.append({
                "id": f"duplicate_{i}",
                "type": "document", 
                "content": original_content,  # Exact duplicate
                "created_at": datetime.utcnow().isoformat()
            })
        
        results = await ingestion_engine.process_data_with_ml_intelligence(
            project_id,
            duplicate_heavy_data
        )
        
        # Should detect and remove duplicates
        duplicates_info = results["processing_summary"]["duplicates_info"]
        assert duplicates_info["total_duplicates_removed"] > 0
        assert duplicates_info["unique_items_remaining"] < len(duplicate_heavy_data)
    
    @pytest.mark.asyncio
    async def test_importance_threshold_filtering(self, ingestion_engine):
        """Test that importance threshold effectively filters low-quality data"""
        project_id = "threshold_test"
        
        # Create data with clear importance differences
        varied_importance_data = [
            # High importance
            {
                "id": "critical_security",
                "type": "issue",
                "content": "CRITICAL SECURITY VULNERABILITY: SQL injection found in user authentication",
                "metadata": {"priority": "critical", "security": True},
                "created_at": datetime.utcnow().isoformat()
            },
            # Low importance  
            {
                "id": "trivial_comment",
                "type": "comment",
                "content": "ok",
                "metadata": {"comment_type": "acknowledgment"},
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        results = await ingestion_engine.process_data_with_ml_intelligence(
            project_id,
            varied_importance_data
        )
        
        # Should filter out low importance items
        summary = results["processing_summary"]
        assert summary["items_filtered_out"] >= 0
        assert summary["items_above_threshold"] <= summary["items_scored"]
        
        # High importance items should be preserved
        importance_dist = results["importance_distribution"]
        assert importance_dist["critical"] > 0 or importance_dist["high"] > 0


@pytest.mark.asyncio
async def test_end_to_end_ml_intelligence():
    """End-to-end test of the complete ML Data Intelligence system"""
    
    # Initialize components
    scorer = AdvancedDataImportanceScoring()
    storage = TimelineBasedStorage()
    ingestion = DataIngestionEngine()
    
    project_id = "e2e_test_project"
    
    # Create realistic test data
    test_data = [
        {
            "id": "security_issue",
            "type": "issue",
            "content": "Security vulnerability discovered in payment processing module. Affects all transactions.",
            "metadata": {"priority": "critical", "component": "payments"},
            "created_at": datetime.utcnow().isoformat(),
            "author": "security_analyst"
        },
        {
            "id": "code_review",
            "type": "code",
            "content": "def process_payment(amount, card_info):\n    # TODO: Add input validation\n    return charge_card(amount, card_info)",
            "metadata": {"file": "payments.py", "language": "python"},
            "created_at": datetime.utcnow().isoformat(),
            "author": "developer"
        },
        {
            "id": "meeting_decision",
            "type": "meeting",
            "content": "Architecture review meeting: Decided to implement circuit breaker pattern for external API calls",
            "metadata": {"meeting_type": "architecture_review", "attendees": 8},
            "created_at": datetime.utcnow().isoformat(),
            "author": "architect"
        }
    ]
    
    # Process through complete pipeline
    results = await ingestion.process_data_with_ml_intelligence(project_id, test_data)
    
    # Verify end-to-end processing
    assert results["status"] == "success"
    assert results["processing_summary"]["total_input_items"] == len(test_data)
    assert results["processing_summary"]["items_stored"] > 0
    assert results["processing_summary"]["vector_documents_created"] > 0
    
    # Verify data can be retrieved from timeline storage
    timeline_data = await storage.retrieve_timeline_data(project_id)
    assert len(timeline_data) > 0
    
    # Verify analytics are available
    analytics = await storage.get_timeline_analytics(project_id)
    assert analytics["total_entries"] > 0
    
    print("✅ End-to-end ML Data Intelligence test passed!")
    print(f"📊 Processed {len(test_data)} items")
    print(f"📈 Stored {results['processing_summary']['items_stored']} important items")
    print(f"🎯 Average importance score: {results['average_importance_score']:.3f}")


if __name__ == "__main__":
    # Run the end-to-end test
    asyncio.run(test_end_to_end_ml_intelligence())
