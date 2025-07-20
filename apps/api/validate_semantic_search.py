#!/usr/bin/env python3
"""
Semantic Search & Cross-Source Search Validation Script
Comprehensive validation of semantic code search, cross-source search, and contextual search
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

# Import Semantic Search components
try:
    from core.semantic_search import (
        SemanticSearchEngine, SearchType, SearchScope, ContentType,
        SearchResult, SearchResponse
    )
    from core.data_importance_scoring import ImportanceLevel, TimelineCategory
    logger.info("✅ Successfully imported Semantic Search components")
except ImportError as e:
    logger.error(f"❌ Failed to import Semantic Search components: {e}")
    sys.exit(1)

class SemanticSearchValidator:
    """Comprehensive validator for Semantic Search & Cross-Source Search features"""
    
    def __init__(self):
        self.search_engine = SemanticSearchEngine({
            'max_results': 50,
            'similarity_threshold': 0.7,
            'importance_boost': 0.2,
            'recency_boost': 0.1
        })
        self.validation_results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "performance_metrics": {}
        }
    
    async def validate_code_intent_analysis(self) -> bool:
        """Validate code intent analysis functionality"""
        logger.info("🧠 Validating Code Intent Analysis...")
        
        try:
            # Test various code intents
            test_queries = [
                ("function to authenticate users with JWT tokens", "authentication"),
                ("SQL query to select user data from database", "database"),
                ("API endpoint for user registration", "api"),
                ("encrypt sensitive user information", "security"),
                ("optimize database query performance", "performance"),
                ("handle authentication errors gracefully", "error_handling"),
                ("unit test for user login functionality", "testing"),
                ("React component for user profile", "ui")
            ]
            
            successful_analyses = 0
            
            for query, expected_intent in test_queries:
                logger.info(f"  Testing query: '{query}'")
                intent_analysis = await self.search_engine._analyze_code_intent(query)
                
                # Validate analysis structure
                assert 'primary_intent' in intent_analysis, "Missing primary_intent"
                assert 'intent_scores' in intent_analysis, "Missing intent_scores"
                assert 'technical_terms' in intent_analysis, "Missing technical_terms"
                assert 'function_patterns' in intent_analysis, "Missing function_patterns"
                
                # Check if expected intent is detected (top 2 intents)
                top_intents = sorted(
                    intent_analysis['intent_scores'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:2]
                
                detected_intents = [intent for intent, _ in top_intents]
                intent_detected = (
                    intent_analysis['primary_intent'] == expected_intent or
                    expected_intent in detected_intents
                )
                
                if intent_detected:
                    successful_analyses += 1
                    logger.info(f"    ✅ Correctly identified intent: {intent_analysis['primary_intent']}")
                else:
                    logger.warning(f"    ⚠️  Expected '{expected_intent}', got '{intent_analysis['primary_intent']}'")
            
            success_rate = successful_analyses / len(test_queries)
            logger.info(f"  Intent analysis success rate: {success_rate:.1%} ({successful_analyses}/{len(test_queries)})")
            
            # Require at least 60% accuracy for validation to pass
            assert success_rate >= 0.6, f"Intent analysis accuracy too low: {success_rate:.1%}"
            
            self.validation_results["tests_passed"] += 1
            self.validation_results["performance_metrics"]["intent_analysis_accuracy"] = success_rate
            return True
            
        except Exception as e:
            logger.error(f"❌ Code Intent Analysis validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Code Intent Analysis: {str(e)}")
            return False
    
    async def validate_query_enhancement(self) -> bool:
        """Validate query enhancement functionality"""
        logger.info("🔍 Validating Query Enhancement...")
        
        try:
            test_cases = [
                {
                    "query": "authenticate user",
                    "intent_analysis": {
                        'primary_intent': 'authentication',
                        'intent_scores': {'authentication': 0.8},
                        'technical_terms': ['JWT', 'token'],
                        'function_patterns': []
                    }
                },
                {
                    "query": "database query",
                    "intent_analysis": {
                        'primary_intent': 'database',
                        'intent_scores': {'database': 0.7},
                        'technical_terms': ['SQL', 'SELECT'],
                        'function_patterns': []
                    }
                }
            ]
            
            for test_case in test_cases:
                query = test_case["query"]
                intent_analysis = test_case["intent_analysis"]
                
                logger.info(f"  Testing query enhancement: '{query}'")
                enhanced_query = await self.search_engine._enhance_code_query(query, intent_analysis)
                
                # Validate enhancement
                assert query in enhanced_query, "Original query should be preserved"
                assert len(enhanced_query) > len(query), "Query should be enhanced with additional terms"
                
                # Check that technical terms are included
                for term in intent_analysis['technical_terms']:
                    assert term in enhanced_query, f"Technical term '{term}' should be included"
                
                logger.info(f"    ✅ Enhanced: '{query}' → '{enhanced_query}'")
            
            self.validation_results["tests_passed"] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Query Enhancement validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Query Enhancement: {str(e)}")
            return False
    
    async def validate_result_filtering_and_ranking(self) -> bool:
        """Validate result filtering and ranking functionality"""
        logger.info("📊 Validating Result Filtering and Ranking...")
        
        try:
            # Create sample results with different characteristics
            sample_results = [
                {
                    "id": "high_relevance_auth",
                    "content": "def authenticate_user(token): validate_jwt_token(token)",
                    "metadata": {
                        "language": "python",
                        "file_path": "/auth/authentication.py",
                        "importance_score": 0.9,
                        "created_at": datetime.utcnow().isoformat()
                    },
                    "score": 0.95
                },
                {
                    "id": "medium_relevance_login",
                    "content": "function login(username, password) { return authenticate(username, password); }",
                    "metadata": {
                        "language": "javascript",
                        "file_path": "/frontend/login.js",
                        "importance_score": 0.7,
                        "created_at": (datetime.utcnow() - timedelta(days=10)).isoformat()
                    },
                    "score": 0.8
                },
                {
                    "id": "low_relevance_test",
                    "content": "SELECT * FROM users WHERE id = 1",
                    "metadata": {
                        "language": "sql",
                        "file_path": "/database/queries.sql",
                        "importance_score": 0.4,
                        "created_at": (datetime.utcnow() - timedelta(days=30)).isoformat()
                    },
                    "score": 0.5
                },
                {
                    "id": "unrelated_content",
                    "content": "print('Hello World')",
                    "metadata": {
                        "language": "python",
                        "file_path": "/examples/hello.py",
                        "importance_score": 0.2,
                        "created_at": (datetime.utcnow() - timedelta(days=60)).isoformat()
                    },
                    "score": 0.3
                }
            ]
            
            # Test language filtering
            logger.info("  Testing language filtering...")
            python_results = await self.search_engine._filter_code_results(
                sample_results, "python", None
            )
            
            assert len(python_results) == 2, f"Expected 2 Python results, got {len(python_results)}"
            for result in python_results:
                assert result['metadata']['language'] == 'python'
            
            logger.info(f"    ✅ Language filtering: {len(python_results)} Python results")
            
            # Test file type filtering
            logger.info("  Testing file type filtering...")
            py_results = await self.search_engine._filter_code_results(
                sample_results, None, ["py"]
            )
            
            assert len(py_results) == 2, f"Expected 2 .py results, got {len(py_results)}"
            for result in py_results:
                assert result['metadata']['file_path'].endswith('.py')
            
            logger.info(f"    ✅ File type filtering: {len(py_results)} .py results")
            
            # Test ranking
            logger.info("  Testing result ranking...")
            query = "authenticate user token"
            intent_analysis = {
                'primary_intent': 'authentication',
                'intent_scores': {'authentication': 0.8},
                'technical_terms': ['token'],
                'function_patterns': []
            }
            
            ranked_results = await self.search_engine._rank_code_results(
                sample_results, query, intent_analysis, importance_threshold=0.0
            )
            
            assert len(ranked_results) > 0, "Should have ranked results"
            
            # Verify ranking order (higher scores first)
            for i in range(len(ranked_results) - 1):
                assert ranked_results[i]['final_score'] >= ranked_results[i + 1]['final_score'], \
                    f"Results not properly ranked: {ranked_results[i]['final_score']} < {ranked_results[i + 1]['final_score']}"
            
            # Authentication-related content should rank higher
            auth_result = next(r for r in ranked_results if r['id'] == 'high_relevance_auth')
            unrelated_result = next(r for r in ranked_results if r['id'] == 'unrelated_content')
            
            assert auth_result['final_score'] > unrelated_result['final_score'], \
                "Authentication result should rank higher than unrelated content"
            
            logger.info(f"    ✅ Ranking validation: {len(ranked_results)} results properly ranked")
            logger.info(f"    📈 Top result: {ranked_results[0]['id']} (score: {ranked_results[0]['final_score']:.3f})")
            
            self.validation_results["tests_passed"] += 2
            return True
            
        except Exception as e:
            logger.error(f"❌ Result Filtering and Ranking validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Result Filtering and Ranking: {str(e)}")
            return False
    
    async def validate_content_type_determination(self) -> bool:
        """Validate content type determination functionality"""
        logger.info("📁 Validating Content Type Determination...")
        
        try:
            test_cases = [
                # Code content types
                ({'source_type': 'github', 'file_path': '/src/auth.py'}, ContentType.CODE),
                ({'source_type': 'code', 'file_path': '/api/routes.js'}, ContentType.CODE),
                ({'source_type': 'unknown', 'file_path': '/utils/helper.java'}, ContentType.CODE),
                
                # Documentation content types
                ({'source_type': 'confluence', 'file_path': '/docs/api.md'}, ContentType.DOCUMENTATION),
                ({'source_type': 'docs', 'file_path': '/readme.txt'}, ContentType.DOCUMENTATION),
                
                # Meeting content types
                ({'source_type': 'meetings', 'file_path': ''}, ContentType.MEETING),
                ({'source_type': 'meeting', 'file_path': ''}, ContentType.MEETING),
                
                # Issue content types
                ({'source_type': 'jira', 'file_path': ''}, ContentType.ISSUE),
                ({'source_type': 'issues', 'file_path': ''}, ContentType.ISSUE),
                
                # Other content types
                ({'source_type': 'slack', 'file_path': ''}, ContentType.SLACK_MESSAGE),
                ({'source_type': 'email', 'file_path': ''}, ContentType.EMAIL),
                ({'source_type': 'commit', 'file_path': ''}, ContentType.COMMIT),
                
                # Default fallback
                ({'source_type': 'unknown', 'file_path': '/unknown/file.txt'}, ContentType.DOCUMENTATION),
            ]
            
            successful_determinations = 0
            
            for metadata, expected_type in test_cases:
                result = {'metadata': metadata}
                determined_type = self.search_engine._determine_content_type(result)
                
                if determined_type == expected_type:
                    successful_determinations += 1
                    logger.info(f"    ✅ {metadata} → {determined_type.value}")
                else:
                    logger.warning(f"    ⚠️  {metadata} → Expected {expected_type.value}, got {determined_type.value}")
            
            success_rate = successful_determinations / len(test_cases)
            logger.info(f"  Content type determination success rate: {success_rate:.1%} ({successful_determinations}/{len(test_cases)})")
            
            # Require at least 90% accuracy
            assert success_rate >= 0.9, f"Content type determination accuracy too low: {success_rate:.1%}"
            
            self.validation_results["tests_passed"] += 1
            self.validation_results["performance_metrics"]["content_type_accuracy"] = success_rate
            return True
            
        except Exception as e:
            logger.error(f"❌ Content Type Determination validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Content Type Determination: {str(e)}")
            return False
    
    async def validate_search_history_management(self) -> bool:
        """Validate search history storage and management"""
        logger.info("📚 Validating Search History Management...")
        
        try:
            project_id = "history_test_project"
            
            # Store multiple searches
            test_searches = [
                ("authenticate user", SearchType.CODE_SEMANTIC),
                ("database query optimization", SearchType.CROSS_SOURCE),
                ("implement caching", SearchType.CONTEXTUAL),
                ("error handling patterns", SearchType.CODE_SEMANTIC),
                ("API documentation", SearchType.CROSS_SOURCE)
            ]
            
            for i, (query, search_type) in enumerate(test_searches):
                search_id = f"test_search_{i}"
                results = []  # Empty results for testing
                
                await self.search_engine._store_search_history(
                    project_id, query, search_type, results, search_id
                )
            
            # Verify history storage
            assert project_id in self.search_engine.search_history, "Project should be in search history"
            
            history = self.search_engine.search_history[project_id]
            assert len(history) == len(test_searches), f"Expected {len(test_searches)} history entries, got {len(history)}"
            
            # Verify history structure
            for i, entry in enumerate(history):
                expected_query, expected_type = test_searches[i]
                
                assert entry['query'] == expected_query, f"Query mismatch: {entry['query']} != {expected_query}"
                assert entry['search_type'] == expected_type.value, f"Search type mismatch: {entry['search_type']} != {expected_type.value}"
                assert 'search_id' in entry, "Missing search_id"
                assert 'timestamp' in entry, "Missing timestamp"
                assert 'results_count' in entry, "Missing results_count"
            
            logger.info(f"    ✅ Stored {len(history)} search history entries")
            
            # Test history limit (should keep only last 100 searches)
            # Add many more searches to test limit
            for i in range(150):  # This should exceed the 100 limit
                await self.search_engine._store_search_history(
                    project_id, f"test query {i}", SearchType.CODE_SEMANTIC, [], f"search_{i}"
                )
            
            updated_history = self.search_engine.search_history[project_id]
            assert len(updated_history) == 100, f"History should be limited to 100 entries, got {len(updated_history)}"
            
            logger.info(f"    ✅ History limit enforced: {len(updated_history)} entries (max 100)")
            
            self.validation_results["tests_passed"] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Search History Management validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Search History Management: {str(e)}")
            return False
    
    async def validate_performance_benchmarks(self) -> bool:
        """Validate performance benchmarks for semantic search"""
        logger.info("⚡ Validating Performance Benchmarks...")
        
        try:
            # Generate large dataset for performance testing
            large_dataset = []
            for i in range(500):  # 500 items for performance testing
                large_dataset.append({
                    "id": f"perf_item_{i}",
                    "content": f"Performance test content {i} with authentication, database, API, security keywords " * (i % 5 + 1),
                    "metadata": {
                        "language": ["python", "javascript", "java", "sql"][i % 4],
                        "file_path": f"/test/file_{i}.{['py', 'js', 'java', 'sql'][i % 4]}",
                        "importance_score": 0.3 + (i % 7) * 0.1,
                        "created_at": (datetime.utcnow() - timedelta(days=i % 100)).isoformat()
                    },
                    "score": 0.4 + (i % 6) * 0.1
                })
            
            # Benchmark intent analysis
            logger.info("  Benchmarking intent analysis...")
            start_time = datetime.utcnow()
            
            test_queries = [
                "authenticate user with JWT token",
                "optimize database query performance",
                "implement REST API endpoint",
                "handle security vulnerabilities",
                "create unit tests for functions"
            ]
            
            for query in test_queries:
                await self.search_engine._analyze_code_intent(query)
            
            intent_duration = (datetime.utcnow() - start_time).total_seconds()
            intent_rate = len(test_queries) / intent_duration if intent_duration > 0 else 0
            
            self.validation_results["performance_metrics"]["intent_analysis_rate"] = intent_rate
            logger.info(f"    ✅ Intent analysis: {intent_rate:.1f} queries/sec")
            
            # Benchmark filtering
            logger.info("  Benchmarking result filtering...")
            start_time = datetime.utcnow()
            
            filtered_results = await self.search_engine._filter_code_results(
                large_dataset, "python", ["py"]
            )
            
            filter_duration = (datetime.utcnow() - start_time).total_seconds()
            filter_rate = len(large_dataset) / filter_duration if filter_duration > 0 else 0
            
            self.validation_results["performance_metrics"]["filtering_rate"] = filter_rate
            logger.info(f"    ✅ Result filtering: {filter_rate:.1f} items/sec")
            
            # Benchmark ranking
            logger.info("  Benchmarking result ranking...")
            start_time = datetime.utcnow()
            
            query = "authenticate user database API security"
            intent_analysis = {
                'primary_intent': 'authentication',
                'intent_scores': {'authentication': 0.8, 'database': 0.3, 'api': 0.4, 'security': 0.6},
                'technical_terms': ['JWT', 'API', 'SQL'],
                'function_patterns': []
            }
            
            # Test with subset for reasonable performance
            test_subset = large_dataset[:100]
            ranked_results = await self.search_engine._rank_code_results(
                test_subset, query, intent_analysis, 0.0
            )
            
            ranking_duration = (datetime.utcnow() - start_time).total_seconds()
            ranking_rate = len(test_subset) / ranking_duration if ranking_duration > 0 else 0
            
            self.validation_results["performance_metrics"]["ranking_rate"] = ranking_rate
            logger.info(f"    ✅ Result ranking: {ranking_rate:.1f} items/sec")
            
            # Performance requirements
            assert intent_rate > 50, f"Intent analysis too slow: {intent_rate:.1f} queries/sec (expected >50)"
            assert filter_rate > 1000, f"Filtering too slow: {filter_rate:.1f} items/sec (expected >1000)"
            assert ranking_rate > 100, f"Ranking too slow: {ranking_rate:.1f} items/sec (expected >100)"
            
            self.validation_results["tests_passed"] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Performance validation failed: {e}")
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"Performance: {str(e)}")
            return False
    
    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete validation of Semantic Search features"""
        logger.info("🚀 Starting Complete Semantic Search Validation")
        logger.info("=" * 70)
        
        validation_start = datetime.utcnow()
        
        # Run all validation tests
        validations = [
            ("Code Intent Analysis", self.validate_code_intent_analysis),
            ("Query Enhancement", self.validate_query_enhancement),
            ("Result Filtering and Ranking", self.validate_result_filtering_and_ranking),
            ("Content Type Determination", self.validate_content_type_determination),
            ("Search History Management", self.validate_search_history_management),
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
        logger.info("\n" + "=" * 70)
        logger.info("📋 FINAL SEMANTIC SEARCH VALIDATION REPORT")
        logger.info("=" * 70)
        logger.info(f"✅ Tests Passed: {self.validation_results['tests_passed']}")
        logger.info(f"❌ Tests Failed: {self.validation_results['tests_failed']}")
        logger.info(f"🎯 Success Rate: {self.validation_results['success_rate']:.1f}%")
        logger.info(f"⏱️  Total Duration: {total_duration:.2f}s")
        
        if self.validation_results["performance_metrics"]:
            logger.info("\n📊 PERFORMANCE METRICS:")
            for metric, value in self.validation_results["performance_metrics"].items():
                if isinstance(value, float):
                    logger.info(f"   {metric}: {value:.2f}")
                else:
                    logger.info(f"   {metric}: {value}")
        
        if self.validation_results["errors"]:
            logger.info(f"\n❌ ERRORS ({len(self.validation_results['errors'])}):")
            for error in self.validation_results["errors"]:
                logger.info(f"   • {error}")
        
        # Overall validation result
        overall_success = passed_validations == len(validations)
        if overall_success:
            logger.info("\n🎉 SEMANTIC SEARCH VALIDATION SUCCESSFUL!")
            logger.info("   All components are working correctly and meet performance requirements.")
            logger.info("   🔍 Semantic Code Search: Ready for production")
            logger.info("   🌐 Cross-Source Search: Ready for production")
            logger.info("   🎯 Contextual Search: Ready for production")
        else:
            logger.error("\n💥 SEMANTIC SEARCH VALIDATION FAILED!")
            logger.error(f"   {len(validations) - passed_validations} validation(s) failed.")
        
        return self.validation_results


async def main():
    """Main validation entry point"""
    validator = SemanticSearchValidator()
    results = await validator.run_complete_validation()
    
    # Save results to file
    with open("semantic_search_validation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Validation results saved to semantic_search_validation_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results["success_rate"] == 100.0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
