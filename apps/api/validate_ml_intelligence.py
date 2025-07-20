#!/usr/bin/env python3
"""
ML Data Intelligence Validation Script
Comprehensive validation of data importance scoring, timeline storage, and integration
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import ML Intelligence components
try:
    from core.data_importance_scoring import AdvancedDataImportanceScoring, DataType, ImportanceLevel, TimelineCategory
    from core.timeline_storage import TimelineBasedStorage, StorageTier, RetentionPolicy
    from core.data_ingestion import DataIngestionEngine
    logger.info("✅ Successfully imported ML Intelligence components")
except ImportError as e:
    logger.error(f"❌ Failed to import ML Intelligence components: {e}")
    sys.exit(1)

class MLIntelligenceValidator:
    """Comprehensive validator for ML Data Intelligence features"""
    
    def __init__(self):
        self.scorer = AdvancedDataImportanceScoring()
        self.storage = TimelineBasedStorage()
        self.ingestion = DataIngestionEngine({
            'batch_size': 10,
            'importance_threshold': 0.3,
            'enable_duplicate_detection': True
        })
        self.validation_results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "performance_metrics": {}
        }
    
    async def validate_data_importance_scoring(self) -> bool:
        """Validate data importance scoring functionality"""
        logger.info("🧠 Validating Data Importance Scoring...")
        
        try:
            # Test data with varying importance levels
            test_data = [
                {
                    "id": "critical_security",
                    "type": "issue",
                    "content": "CRITICAL: SQL injection vulnerability in user authentication system. Immediate patch required.",
                    "metadata": {"priority": "critical", "security": True, "impact": "high"},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "security_team"
                },
                {
                    "id": "architecture_decision",
                    "type": "document",
                    "content": "Architecture Decision Record: We have decided to adopt microservices architecture for better scalability and maintainability. This affects the entire system design.",
                    "metadata": {"type": "ADR", "impact": "system-wide"},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "chief_architect"
                },
                {
                    "id": "routine_standup",
                    "type": "meeting",
                    "content": "Daily standup: Team discussed progress on current sprint. No blockers reported.",
                    "metadata": {"meeting_type": "standup", "duration": 15},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "scrum_master"
                },
                {
                    "id": "trivial_comment",
                    "type": "comment",
                    "content": "LGTM 👍",
                    "metadata": {"comment_type": "approval"},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "developer"
                }
            ]
            
            project_id = "validation_project"
            
            # Test single item scoring
            logger.info("  Testing single item scoring...")
            single_score = await self.scorer.score_data_importance(project_id, test_data[0])
            
            assert single_score is not None, "Single item scoring failed"
            assert 0.0 <= single_score.overall_score <= 1.0, "Score out of valid range"
            assert single_score.importance_level in ImportanceLevel, "Invalid importance level"
            assert single_score.timeline_category in TimelineCategory, "Invalid timeline category"
            assert single_score.confidence > 0.0, "Confidence should be positive"
            assert len(single_score.reasoning) > 0, "Reasoning should be provided"
            
            logger.info(f"    ✅ Single item scored: {single_score.overall_score:.3f} ({single_score.importance_level.value})")
            
            # Test batch scoring
            logger.info("  Testing batch scoring...")
            start_time = datetime.utcnow()
            batch_scores = await self.scorer.score_batch(project_id, test_data)
            end_time = datetime.utcnow()
            
            batch_duration = (end_time - start_time).total_seconds()
            self.validation_results["performance_metrics"]["batch_scoring_time"] = batch_duration
            
            assert len(batch_scores) == len(test_data), "Batch scoring count mismatch"
            
            # Verify importance ranking
            critical_score = next(s for s in batch_scores if s.data_id == "critical_security")
            trivial_score = next(s for s in batch_scores if s.data_id == "trivial_comment")
            
            assert critical_score.overall_score > trivial_score.overall_score, "Importance ranking incorrect"
            
            logger.info(f"    ✅ Batch scoring completed in {batch_duration:.3f}s")
            logger.info(f"    📊 Critical item: {critical_score.overall_score:.3f}, Trivial item: {trivial_score.overall_score:.3f}")
            
            # Test duplicate detection
            logger.info("  Testing duplicate detection...")
            duplicate_data = [
                {"id": "orig", "content": "Original content for duplicate testing", "type": "document"},
                {"id": "dup1", "content": "Original content for duplicate testing", "type": "document"},  # Exact duplicate
                {"id": "sim", "content": "Original content for duplicate detection testing", "type": "document"},  # Similar
                {"id": "diff", "content": "Completely different content about machine learning", "type": "document"}
            ]
            
            duplicates = await self.scorer.detect_duplicates(project_id, duplicate_data)
            assert isinstance(duplicates, dict), "Duplicates should be returned as dict"
            
            # Should detect at least one duplicate group
            duplicate_groups = sum(1 for group in duplicates.values() if len(group) > 1)
            assert duplicate_groups > 0, "Should detect duplicate content"
            
            logger.info(f"    ✅ Detected {duplicate_groups} duplicate groups")
            
            # Test timeline organization
            logger.info("  Testing timeline organization...")
            timeline_data = await self.scorer.organize_by_timeline(batch_scores, importance_threshold=0.3)
            
            assert isinstance(timeline_data, dict), "Timeline data should be dict"
            total_organized = sum(len(items) for items in timeline_data.values())
            
            logger.info(f"    ✅ Organized {total_organized} items across {len(timeline_data)} timeline categories")
            
            self.validation_results["tests_passed"] += 4
            return True
            
        except Exception as e:
            logger.error(f"❌ Data Importance Scoring validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Data Importance Scoring: {str(e)}")
            return False
    
    async def validate_timeline_storage(self) -> bool:
        """Validate timeline-based storage functionality"""
        logger.info("📅 Validating Timeline-Based Storage...")
        
        try:
            project_id = "timeline_validation_project"
            
            # Test data with different timeline categories
            timeline_test_data = [
                {
                    "id": "recent_item",
                    "type": "code",
                    "content": "Recent code changes in the main branch",
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {"importance": "high"}
                },
                {
                    "id": "month_old_item",
                    "type": "meeting",
                    "content": "Monthly planning meeting from last month",
                    "created_at": (datetime.utcnow() - timedelta(days=45)).isoformat(),
                    "metadata": {"importance": "medium"}
                },
                {
                    "id": "quarterly_item",
                    "type": "document",
                    "content": "Quarterly business review documentation",
                    "created_at": (datetime.utcnow() - timedelta(days=120)).isoformat(),
                    "metadata": {"importance": "medium"}
                },
                {
                    "id": "old_item",
                    "type": "issue",
                    "content": "Old resolved issue from last year",
                    "created_at": (datetime.utcnow() - timedelta(days=400)).isoformat(),
                    "metadata": {"importance": "low"}
                }
            ]
            
            # Test storage
            logger.info("  Testing timeline data storage...")
            start_time = datetime.utcnow()
            entry_ids = await self.storage.store_timeline_data(project_id, timeline_test_data)
            end_time = datetime.utcnow()
            
            storage_duration = (end_time - start_time).total_seconds()
            self.validation_results["performance_metrics"]["timeline_storage_time"] = storage_duration
            
            assert len(entry_ids) == len(timeline_test_data), "Storage count mismatch"
            assert all(isinstance(entry_id, str) for entry_id in entry_ids), "Entry IDs should be strings"
            
            logger.info(f"    ✅ Stored {len(entry_ids)} items in {storage_duration:.3f}s")
            
            # Test retrieval
            logger.info("  Testing timeline data retrieval...")
            
            # Retrieve all data
            all_data = await self.storage.retrieve_timeline_data(project_id)
            assert len(all_data) == len(timeline_test_data), "Retrieval count mismatch"
            
            # Retrieve with importance threshold
            important_data = await self.storage.retrieve_timeline_data(project_id, importance_threshold=0.5)
            assert len(important_data) <= len(all_data), "Threshold filtering failed"
            
            # Retrieve recent data only
            recent_data = await self.storage.retrieve_timeline_data(
                project_id,
                timeline_category=TimelineCategory.RECENT
            )
            
            # Verify timeline filtering
            for entry in recent_data:
                assert entry.timeline_category == TimelineCategory.RECENT, "Timeline filtering failed"
            
            logger.info(f"    ✅ Retrieved data with filters: all={len(all_data)}, important={len(important_data)}, recent={len(recent_data)}")
            
            # Test analytics
            logger.info("  Testing timeline analytics...")
            analytics = await self.storage.get_timeline_analytics(project_id, days_back=365)
            
            required_analytics_keys = ["total_entries", "timeline_distribution", "importance_distribution", "storage_tier_distribution"]
            for key in required_analytics_keys:
                assert key in analytics, f"Missing analytics key: {key}"
            
            assert analytics["total_entries"] > 0, "Analytics should show stored entries"
            
            logger.info(f"    ✅ Analytics generated: {analytics['total_entries']} total entries")
            
            # Test cleanup
            logger.info("  Testing data cleanup...")
            cleanup_results = await self.storage.cleanup_expired_data(project_id)
            
            assert isinstance(cleanup_results, dict), "Cleanup results should be dict"
            assert "cleaned_up_count" in cleanup_results, "Missing cleanup count"
            
            logger.info(f"    ✅ Cleanup completed: {cleanup_results.get('cleaned_up_count', 0)} items cleaned")
            
            self.validation_results["tests_passed"] += 4
            return True
            
        except Exception as e:
            logger.error(f"❌ Timeline Storage validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Timeline Storage: {str(e)}")
            return False
    
    async def validate_integration_pipeline(self) -> bool:
        """Validate the complete ML intelligence integration pipeline"""
        logger.info("🔄 Validating Integration Pipeline...")
        
        try:
            project_id = "integration_validation_project"
            
            # Comprehensive test data with mixed quality and duplicates
            integration_test_data = [
                # High importance items
                {
                    "id": "critical_bug",
                    "type": "issue",
                    "content": "CRITICAL: Memory leak causing server crashes in production. Affecting 100% of users.",
                    "metadata": {"priority": "critical", "environment": "production", "impact": "high"},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "ops_team"
                },
                {
                    "id": "security_patch",
                    "type": "code",
                    "content": "def authenticate_user(token):\n    # SECURITY: Fixed JWT validation vulnerability\n    if not validate_jwt_signature(token):\n        raise AuthenticationError('Invalid token')\n    return decode_token(token)",
                    "metadata": {"file": "auth.py", "security_fix": True},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "security_engineer"
                },
                
                # Medium importance items
                {
                    "id": "feature_spec",
                    "type": "document",
                    "content": "Feature Specification: New user dashboard with analytics and reporting capabilities",
                    "metadata": {"type": "specification", "feature": "dashboard"},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "product_manager"
                },
                
                # Low importance items
                {
                    "id": "standup_notes",
                    "type": "meeting",
                    "content": "Daily standup: Team velocity is good, sprint on track",
                    "metadata": {"meeting_type": "standup"},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "scrum_master"
                },
                
                # Noise items
                {
                    "id": "emoji_comment",
                    "type": "comment",
                    "content": "🎉",
                    "metadata": {"comment_type": "reaction"},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "team_member"
                },
                
                # Duplicates
                {
                    "id": "duplicate_original",
                    "type": "document",
                    "content": "This is duplicate content for testing deduplication functionality",
                    "metadata": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "user1"
                },
                {
                    "id": "duplicate_copy",
                    "type": "document",
                    "content": "This is duplicate content for testing deduplication functionality",  # Exact duplicate
                    "metadata": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "user2"
                }
            ]
            
            # Run complete ML intelligence processing
            logger.info("  Running complete ML intelligence pipeline...")
            start_time = datetime.utcnow()
            results = await self.ingestion.process_data_with_ml_intelligence(project_id, integration_test_data)
            end_time = datetime.utcnow()
            
            pipeline_duration = (end_time - start_time).total_seconds()
            self.validation_results["performance_metrics"]["pipeline_processing_time"] = pipeline_duration
            
            # Validate results structure
            assert results["status"] == "success", f"Pipeline failed: {results.get('error', 'Unknown error')}"
            assert results["project_id"] == project_id, "Project ID mismatch"
            
            summary = results["processing_summary"]
            required_summary_keys = [
                "total_input_items", "items_after_deduplication", "items_scored",
                "items_above_threshold", "items_filtered_out", "items_stored"
            ]
            for key in required_summary_keys:
                assert key in summary, f"Missing summary key: {key}"
            
            # Validate processing logic
            assert summary["total_input_items"] == len(integration_test_data), "Input count mismatch"
            assert summary["items_after_deduplication"] <= len(integration_test_data), "Deduplication logic error"
            assert summary["items_above_threshold"] <= summary["items_scored"], "Threshold filtering error"
            
            # Validate importance distribution
            importance_dist = results["importance_distribution"]
            total_important_items = sum(importance_dist.values())
            assert total_important_items > 0, "No items classified as important"
            
            # Critical/high importance items should be identified
            critical_and_high = importance_dist.get("critical", 0) + importance_dist.get("high", 0)
            assert critical_and_high > 0, "Critical/high importance items not identified"
            
            # Validate timeline distribution
            timeline_dist = results["timeline_distribution"]
            assert len(timeline_dist) > 0, "Timeline distribution empty"
            
            # Validate performance
            items_per_second = len(integration_test_data) / pipeline_duration if pipeline_duration > 0 else 0
            self.validation_results["performance_metrics"]["items_per_second"] = items_per_second
            
            logger.info(f"    ✅ Pipeline completed in {pipeline_duration:.3f}s ({items_per_second:.1f} items/sec)")
            logger.info(f"    📊 Processed: {summary['total_input_items']} → {summary['items_stored']} stored")
            logger.info(f"    🎯 Average importance: {results['average_importance_score']:.3f}")
            logger.info(f"    🔍 Duplicates removed: {summary.get('duplicates_info', {}).get('total_duplicates_removed', 0)}")
            
            # Validate data persistence
            logger.info("  Validating data persistence...")
            stored_timeline_data = await self.storage.retrieve_timeline_data(project_id)
            assert len(stored_timeline_data) > 0, "No data persisted in timeline storage"
            
            timeline_analytics = await self.storage.get_timeline_analytics(project_id)
            assert timeline_analytics["total_entries"] > 0, "Timeline analytics show no entries"
            
            logger.info(f"    ✅ Data persistence validated: {len(stored_timeline_data)} items in timeline storage")
            
            self.validation_results["tests_passed"] += 3
            return True
            
        except Exception as e:
            logger.error(f"❌ Integration Pipeline validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Integration Pipeline: {str(e)}")
            return False
    
    async def validate_performance_benchmarks(self) -> bool:
        """Validate performance benchmarks for ML intelligence features"""
        logger.info("⚡ Validating Performance Benchmarks...")
        
        try:
            project_id = "performance_validation_project"
            
            # Generate larger dataset for performance testing
            large_dataset = []
            for i in range(100):  # 100 items for performance testing
                large_dataset.append({
                    "id": f"perf_item_{i}",
                    "type": "document",
                    "content": f"Performance test document {i} with varying content length and complexity. " * (i % 10 + 1),
                    "metadata": {"test_item": True, "index": i},
                    "created_at": datetime.utcnow().isoformat(),
                    "author": f"test_user_{i % 5}"
                })
            
            # Benchmark batch scoring
            logger.info("  Benchmarking batch scoring performance...")
            start_time = datetime.utcnow()
            scores = await self.scorer.score_batch(project_id, large_dataset)
            scoring_duration = (datetime.utcnow() - start_time).total_seconds()
            
            scoring_rate = len(large_dataset) / scoring_duration if scoring_duration > 0 else 0
            self.validation_results["performance_metrics"]["scoring_rate_items_per_sec"] = scoring_rate
            
            assert len(scores) == len(large_dataset), "Batch scoring incomplete"
            assert scoring_rate > 10, f"Scoring too slow: {scoring_rate:.1f} items/sec (expected >10)"
            
            logger.info(f"    ✅ Batch scoring: {scoring_rate:.1f} items/sec")
            
            # Benchmark timeline storage
            logger.info("  Benchmarking timeline storage performance...")
            start_time = datetime.utcnow()
            entry_ids = await self.storage.store_timeline_data(project_id, large_dataset)
            storage_duration = (datetime.utcnow() - start_time).total_seconds()
            
            storage_rate = len(large_dataset) / storage_duration if storage_duration > 0 else 0
            self.validation_results["performance_metrics"]["storage_rate_items_per_sec"] = storage_rate
            
            assert len(entry_ids) == len(large_dataset), "Timeline storage incomplete"
            assert storage_rate > 20, f"Storage too slow: {storage_rate:.1f} items/sec (expected >20)"
            
            logger.info(f"    ✅ Timeline storage: {storage_rate:.1f} items/sec")
            
            # Benchmark retrieval
            logger.info("  Benchmarking data retrieval performance...")
            start_time = datetime.utcnow()
            retrieved_data = await self.storage.retrieve_timeline_data(project_id, limit=50)
            retrieval_duration = (datetime.utcnow() - start_time).total_seconds()
            
            retrieval_rate = len(retrieved_data) / retrieval_duration if retrieval_duration > 0 else 0
            self.validation_results["performance_metrics"]["retrieval_rate_items_per_sec"] = retrieval_rate
            
            assert len(retrieved_data) > 0, "Data retrieval failed"
            assert retrieval_rate > 50, f"Retrieval too slow: {retrieval_rate:.1f} items/sec (expected >50)"
            
            logger.info(f"    ✅ Data retrieval: {retrieval_rate:.1f} items/sec")
            
            self.validation_results["tests_passed"] += 3
            return True
            
        except Exception as e:
            logger.error(f"❌ Performance validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Performance: {str(e)}")
            return False
    
    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete validation of ML Data Intelligence features"""
        logger.info("🚀 Starting Complete ML Data Intelligence Validation")
        logger.info("=" * 60)
        
        validation_start = datetime.utcnow()
        
        # Run all validation tests
        validations = [
            ("Data Importance Scoring", self.validate_data_importance_scoring),
            ("Timeline-Based Storage", self.validate_timeline_storage),
            ("Integration Pipeline", self.validate_integration_pipeline),
            ("Performance Benchmarks", self.validate_performance_benchmarks)
        ]
        
        passed_validations = 0
        for name, validation_func in validations:
            logger.info(f"\n🔍 Running {name} validation...")
            try:
                success = await validation_func()
                if success:
                    passed_validations += 1
                    logger.info(f"✅ {name} validation PASSED")
                else:
                    logger.error(f"❌ {name} validation FAILED")
            except Exception as e:
                logger.error(f"💥 {name} validation CRASHED: {e}")
                self.validation_results["errors"].append(f"{name} crashed: {str(e)}")
        
        validation_end = datetime.utcnow()
        total_duration = (validation_end - validation_start).total_seconds()
        
        # Generate final report
        self.validation_results.update({
            "total_validations": len(validations),
            "passed_validations": passed_validations,
            "failed_validations": len(validations) - passed_validations,
            "success_rate": (passed_validations / len(validations)) * 100,
            "total_duration_seconds": total_duration,
            "validation_timestamp": validation_end.isoformat()
        })
        
        # Print final report
        logger.info("\n" + "=" * 60)
        logger.info("📋 FINAL VALIDATION REPORT")
        logger.info("=" * 60)
        logger.info(f"✅ Tests Passed: {self.validation_results['tests_passed']}")
        logger.info(f"❌ Tests Failed: {self.validation_results['tests_failed']}")
        logger.info(f"🎯 Success Rate: {self.validation_results['success_rate']:.1f}%")
        logger.info(f"⏱️  Total Duration: {total_duration:.2f}s")
        
        if self.validation_results["performance_metrics"]:
            logger.info("\n📊 PERFORMANCE METRICS:")
            for metric, value in self.validation_results["performance_metrics"].items():
                logger.info(f"   {metric}: {value:.2f}")
        
        if self.validation_results["errors"]:
            logger.info(f"\n❌ ERRORS ({len(self.validation_results['errors'])}):")
            for error in self.validation_results["errors"]:
                logger.info(f"   • {error}")
        
        # Overall validation result
        overall_success = passed_validations == len(validations)
        if overall_success:
            logger.info("\n🎉 ML DATA INTELLIGENCE VALIDATION SUCCESSFUL!")
            logger.info("   All components are working correctly and meet performance requirements.")
        else:
            logger.error("\n💥 ML DATA INTELLIGENCE VALIDATION FAILED!")
            logger.error(f"   {len(validations) - passed_validations} validation(s) failed.")
        
        return self.validation_results


async def main():
    """Main validation entry point"""
    validator = MLIntelligenceValidator()
    results = await validator.run_complete_validation()
    
    # Save results to file
    with open("ml_intelligence_validation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Validation results saved to ml_intelligence_validation_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results["success_rate"] == 100.0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
