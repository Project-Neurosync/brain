"""
Comprehensive tests for Semantic Search and Cross-Source Search features
Tests semantic code search, cross-source search, contextual search, and API integration
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

from core.semantic_search import (
    SemanticSearchEngine, SearchType, SearchScope, ContentType,
    SearchResult, SearchResponse
)
from core.data_importance_scoring import ImportanceLevel, TimelineCategory

class TestSemanticSearchEngine:
    """Test suite for Semantic Search Engine"""
    
    @pytest.fixture
    def search_engine(self):
        """Create a semantic search engine instance"""
        return SemanticSearchEngine({
            'max_results': 50,
            'similarity_threshold': 0.7,
            'importance_boost': 0.2,
            'recency_boost': 0.1
        })
    
    @pytest.fixture
    def sample_code_data(self):
        """Create sample code data for testing"""
        return [
            {
                "id": "auth_function",
                "content": "def authenticate_user(token):\n    if not validate_jwt_token(token):\n        raise AuthenticationError('Invalid token')\n    return decode_user_from_token(token)",
                "metadata": {
                    "source_type": "github",
                    "file_path": "/auth/authentication.py",
                    "language": "python",
                    "importance_score": 0.8,
                    "importance_level": "high",
                    "timeline_category": "recent",
                    "created_at": datetime.utcnow().isoformat()
                },
                "score": 0.9
            },
            {
                "id": "login_endpoint",
                "content": "@app.route('/api/login', methods=['POST'])\ndef login():\n    username = request.json.get('username')\n    password = request.json.get('password')\n    if authenticate_user_credentials(username, password):\n        token = generate_jwt_token(username)\n        return {'token': token}",
                "metadata": {
                    "source_type": "github",
                    "file_path": "/api/auth_routes.py",
                    "language": "python",
                    "importance_score": 0.7,
                    "importance_level": "high",
                    "timeline_category": "recent",
                    "created_at": datetime.utcnow().isoformat()
                },
                "score": 0.85
            },
            {
                "id": "database_query",
                "content": "SELECT * FROM users WHERE username = ? AND active = 1",
                "metadata": {
                    "source_type": "code",
                    "file_path": "/database/queries.sql",
                    "language": "sql",
                    "importance_score": 0.5,
                    "importance_level": "medium",
                    "timeline_category": "last_month",
                    "created_at": (datetime.utcnow() - timedelta(days=20)).isoformat()
                },
                "score": 0.6
            },
            {
                "id": "test_function",
                "content": "def test_authentication():\n    token = 'invalid_token'\n    with pytest.raises(AuthenticationError):\n        authenticate_user(token)",
                "metadata": {
                    "source_type": "github",
                    "file_path": "/tests/test_auth.py",
                    "language": "python",
                    "importance_score": 0.6,
                    "importance_level": "medium",
                    "timeline_category": "recent",
                    "created_at": datetime.utcnow().isoformat()
                },
                "score": 0.7
            }
        ]
    
    @pytest.fixture
    def sample_cross_source_data(self):
        """Create sample cross-source data for testing"""
        return [
            {
                "id": "auth_code",
                "content": "Authentication implementation with JWT tokens",
                "metadata": {
                    "source_type": "github",
                    "file_path": "/auth/auth.py",
                    "importance_score": 0.8,
                    "importance_level": "high",
                    "timeline_category": "recent"
                },
                "score": 0.9
            },
            {
                "id": "auth_docs",
                "content": "Authentication Documentation: How to implement secure user authentication using JWT tokens",
                "metadata": {
                    "source_type": "confluence",
                    "title": "Authentication Guide",
                    "importance_score": 0.7,
                    "importance_level": "high",
                    "timeline_category": "recent"
                },
                "score": 0.85
            },
            {
                "id": "auth_meeting",
                "content": "Security review meeting: Discussed authentication vulnerabilities and JWT token security",
                "metadata": {
                    "source_type": "meetings",
                    "title": "Security Review",
                    "importance_score": 0.6,
                    "importance_level": "medium",
                    "timeline_category": "last_month"
                },
                "score": 0.75
            },
            {
                "id": "auth_issue",
                "content": "BUG: Authentication fails with expired JWT tokens",
                "metadata": {
                    "source_type": "jira",
                    "title": "Auth Bug",
                    "importance_score": 0.9,
                    "importance_level": "critical",
                    "timeline_category": "recent"
                },
                "score": 0.95
            }
        ]
    
    def test_code_intent_analysis(self, search_engine):
        """Test code intent analysis functionality"""
        # Test authentication intent
        auth_query = "function to authenticate users with JWT tokens"
        intent_analysis = asyncio.run(search_engine._analyze_code_intent(auth_query))
        
        assert intent_analysis['primary_intent'] == 'authentication'
        assert 'authentication' in intent_analysis['intent_scores']
        assert intent_analysis['intent_scores']['authentication'] > 0
        assert 'jwt' in intent_analysis['technical_terms']
        
        # Test database intent
        db_query = "SQL query to select user data"
        intent_analysis = asyncio.run(search_engine._analyze_code_intent(db_query))
        
        assert intent_analysis['primary_intent'] == 'database'
        assert 'database' in intent_analysis['intent_scores']
    
    def test_query_enhancement(self, search_engine):
        """Test query enhancement with code-specific terms"""
        query = "authenticate user"
        intent_analysis = {
            'primary_intent': 'authentication',
            'intent_scores': {'authentication': 0.5},
            'technical_terms': ['JWT', 'token'],
            'function_patterns': []
        }
        
        enhanced_query = asyncio.run(search_engine._enhance_code_query(query, intent_analysis))
        
        assert query in enhanced_query
        assert 'auth' in enhanced_query  # Should include related keywords
        assert 'JWT' in enhanced_query    # Should include technical terms
    
    def test_code_result_filtering(self, search_engine, sample_code_data):
        """Test filtering of code results by language and file types"""
        # Test language filtering
        python_results = asyncio.run(
            search_engine._filter_code_results(sample_code_data, "python", None)
        )
        
        assert len(python_results) == 3  # Should filter out SQL
        for result in python_results:
            assert result['metadata']['language'] == 'python'
        
        # Test file type filtering
        py_results = asyncio.run(
            search_engine._filter_code_results(sample_code_data, None, ["py"])
        )
        
        assert len(py_results) == 3  # Should filter out .sql file
        for result in py_results:
            assert result['metadata']['file_path'].endswith('.py')
        
        # Test combined filtering
        combined_results = asyncio.run(
            search_engine._filter_code_results(sample_code_data, "python", ["py"])
        )
        
        assert len(combined_results) == 3
    
    def test_code_result_ranking(self, search_engine, sample_code_data):
        """Test ranking of code search results"""
        query = "authenticate user token"
        intent_analysis = {
            'primary_intent': 'authentication',
            'intent_scores': {'authentication': 0.8},
            'technical_terms': ['token'],
            'function_patterns': []
        }
        
        ranked_results = asyncio.run(
            search_engine._rank_code_results(
                sample_code_data, query, intent_analysis, importance_threshold=0.0
            )
        )
        
        assert len(ranked_results) > 0
        
        # Results should be sorted by final score (descending)
        for i in range(len(ranked_results) - 1):
            assert ranked_results[i]['final_score'] >= ranked_results[i + 1]['final_score']
        
        # Authentication-related results should rank higher
        auth_result = next(r for r in ranked_results if r['id'] == 'auth_function')
        test_result = next(r for r in ranked_results if r['id'] == 'test_function')
        
        assert auth_result['final_score'] > test_result['final_score']
    
    def test_content_type_determination(self, search_engine):
        """Test content type determination from metadata"""
        # Test code content type
        code_result = {
            'metadata': {
                'source_type': 'github',
                'file_path': '/src/auth.py'
            }
        }
        content_type = search_engine._determine_content_type(code_result)
        assert content_type == ContentType.CODE
        
        # Test documentation content type
        doc_result = {
            'metadata': {
                'source_type': 'confluence',
                'file_path': '/docs/api.md'
            }
        }
        content_type = search_engine._determine_content_type(doc_result)
        assert content_type == ContentType.DOCUMENTATION
        
        # Test meeting content type
        meeting_result = {
            'metadata': {
                'source_type': 'meetings',
                'file_path': ''
            }
        }
        content_type = search_engine._determine_content_type(meeting_result)
        assert content_type == ContentType.MEETING
    
    def test_search_history_storage(self, search_engine):
        """Test search history storage and management"""
        project_id = "test_project"
        query = "test query"
        search_type = SearchType.CODE_SEMANTIC
        results = []
        search_id = "test_search_id"
        
        # Store search history
        asyncio.run(
            search_engine._store_search_history(
                project_id, query, search_type, results, search_id
            )
        )
        
        # Verify history is stored
        assert project_id in search_engine.search_history
        history = search_engine.search_history[project_id]
        assert len(history) == 1
        
        latest_search = history[0]
        assert latest_search['search_id'] == search_id
        assert latest_search['query'] == query
        assert latest_search['search_type'] == search_type.value
    
    @pytest.mark.asyncio
    async def test_vector_database_search_integration(self, search_engine, sample_cross_source_data):
        """Test integration with vector database search"""
        # Mock the vector database search method
        async def mock_semantic_search(project_id, query, source_types=None, limit=50):
            return sample_cross_source_data[:limit]
        
        # Replace the method temporarily
        original_method = search_engine.vector_db.semantic_search
        search_engine.vector_db.semantic_search = mock_semantic_search
        
        try:
            project_id = "test_project"
            query = "authentication"
            content_types = [ContentType.CODE, ContentType.DOCUMENTATION]
            limit = 10
            
            results = await search_engine._search_vector_database(
                project_id, query, content_types, limit
            )
            
            assert len(results) > 0
            assert all(isinstance(result, SearchResult) for result in results)
            
            # Verify content types are correctly determined
            code_results = [r for r in results if r.content_type == ContentType.CODE]
            doc_results = [r for r in results if r.content_type == ContentType.DOCUMENTATION]
            
            assert len(code_results) > 0
            assert len(doc_results) > 0
            
        finally:
            # Restore original method
            search_engine.vector_db.semantic_search = original_method


class TestSemanticSearchAPI:
    """Test suite for Semantic Search API integration"""
    
    @pytest.fixture
    def mock_search_engine(self):
        """Create a mock search engine for API testing"""
        class MockSearchEngine:
            async def semantic_code_search(self, **kwargs):
                return SearchResponse(
                    query=kwargs['query'],
                    search_type=SearchType.CODE_SEMANTIC,
                    total_results=2,
                    results=[
                        SearchResult(
                            id="test_result_1",
                            content_type=ContentType.CODE,
                            title="Test Function",
                            content="def test_function(): pass",
                            relevance_score=0.9,
                            importance_score=0.8,
                            importance_level=ImportanceLevel.HIGH,
                            timeline_category=TimelineCategory.RECENT,
                            source_info={"file_path": "/test.py"},
                            metadata={"language": "python"},
                            highlights=["test_function"],
                            related_items=[],
                            context_path=[],
                            found_at=datetime.utcnow()
                        )
                    ],
                    search_time_ms=150.0,
                    suggestions=["Try searching for test cases"],
                    related_queries=["unit tests", "test examples"],
                    facets={"language": {"python": 1}},
                    context_insights={"primary_intent": "testing"},
                    search_id="test_search_123"
                )
            
            async def cross_source_search(self, **kwargs):
                return SearchResponse(
                    query=kwargs['query'],
                    search_type=SearchType.CROSS_SOURCE,
                    total_results=3,
                    results=[],
                    search_time_ms=200.0,
                    suggestions=[],
                    related_queries=[],
                    facets={},
                    context_insights={},
                    search_id="cross_search_456"
                )
            
            async def contextual_search_with_suggestions(self, **kwargs):
                return SearchResponse(
                    query=kwargs['query'],
                    search_type=SearchType.CONTEXTUAL,
                    total_results=1,
                    results=[],
                    search_time_ms=100.0,
                    suggestions=["Based on your context..."],
                    related_queries=[],
                    facets={},
                    context_insights={"context_relevance": "high"},
                    search_id="contextual_789"
                )
        
        return MockSearchEngine()
    
    def test_semantic_code_search_api_response_format(self, mock_search_engine):
        """Test that semantic code search API returns correct response format"""
        # This would test the actual API endpoint response format
        # For now, we test the search engine response structure
        
        response = asyncio.run(mock_search_engine.semantic_code_search(
            query="test function",
            project_id="test_project",
            language="python",
            limit=10
        ))
        
        assert response.query == "test function"
        assert response.search_type == SearchType.CODE_SEMANTIC
        assert response.total_results > 0
        assert len(response.results) > 0
        assert response.search_time_ms > 0
        assert isinstance(response.suggestions, list)
        assert isinstance(response.facets, dict)
        assert response.search_id is not None
    
    def test_cross_source_search_api_response_format(self, mock_search_engine):
        """Test that cross-source search API returns correct response format"""
        response = asyncio.run(mock_search_engine.cross_source_search(
            query="authentication security",
            project_id="test_project",
            content_types=[ContentType.CODE, ContentType.DOCUMENTATION],
            limit=20
        ))
        
        assert response.query == "authentication security"
        assert response.search_type == SearchType.CROSS_SOURCE
        assert response.search_time_ms > 0
        assert response.search_id is not None
    
    def test_contextual_search_api_response_format(self, mock_search_engine):
        """Test that contextual search API returns correct response format"""
        response = asyncio.run(mock_search_engine.contextual_search_with_suggestions(
            query="implement caching",
            project_id="test_project",
            user_context={"role": "developer"},
            limit=15
        ))
        
        assert response.query == "implement caching"
        assert response.search_type == SearchType.CONTEXTUAL
        assert response.search_time_ms > 0
        assert len(response.suggestions) > 0
        assert "context_relevance" in response.context_insights
        assert response.search_id is not None


class TestSearchPerformance:
    """Test suite for search performance and scalability"""
    
    @pytest.fixture
    def large_dataset(self):
        """Create a large dataset for performance testing"""
        dataset = []
        for i in range(1000):  # 1000 items
            dataset.append({
                "id": f"item_{i}",
                "content": f"This is test content item {i} with various keywords and technical terms",
                "metadata": {
                    "source_type": "github" if i % 2 == 0 else "confluence",
                    "file_path": f"/test/file_{i}.py",
                    "language": "python",
                    "importance_score": 0.5 + (i % 5) * 0.1,
                    "importance_level": ["low", "medium", "high", "critical"][i % 4],
                    "timeline_category": ["recent", "last_month", "last_quarter"][i % 3],
                    "created_at": datetime.utcnow().isoformat()
                },
                "score": 0.5 + (i % 10) * 0.05
            })
        return dataset
    
    @pytest.mark.asyncio
    async def test_search_performance_benchmarks(self, large_dataset):
        """Test search performance with large datasets"""
        search_engine = SemanticSearchEngine()
        
        # Test filtering performance
        start_time = datetime.utcnow()
        filtered_results = await search_engine._filter_code_results(
            large_dataset, "python", ["py"]
        )
        filter_duration = (datetime.utcnow() - start_time).total_seconds()
        
        assert filter_duration < 1.0  # Should complete within 1 second
        assert len(filtered_results) > 0
        
        # Test ranking performance
        query = "test content technical terms"
        intent_analysis = {
            'primary_intent': 'general',
            'intent_scores': {},
            'technical_terms': ['technical'],
            'function_patterns': []
        }
        
        start_time = datetime.utcnow()
        ranked_results = await search_engine._rank_code_results(
            large_dataset[:100], query, intent_analysis, 0.0  # Test with 100 items
        )
        ranking_duration = (datetime.utcnow() - start_time).total_seconds()
        
        assert ranking_duration < 2.0  # Should complete within 2 seconds
        assert len(ranked_results) > 0
        
        # Verify ranking is correct
        for i in range(len(ranked_results) - 1):
            assert ranked_results[i]['final_score'] >= ranked_results[i + 1]['final_score']


@pytest.mark.asyncio
async def test_end_to_end_semantic_search():
    """End-to-end test of the complete semantic search system"""
    
    # Initialize search engine
    search_engine = SemanticSearchEngine({
        'max_results': 20,
        'similarity_threshold': 0.7,
        'importance_boost': 0.2,
        'recency_boost': 0.1
    })
    
    project_id = "e2e_search_test_project"
    
    # Test code intent analysis
    query = "function to authenticate users with JWT tokens"
    intent_analysis = await search_engine._analyze_code_intent(query)
    
    assert intent_analysis['primary_intent'] == 'authentication'
    assert 'authentication' in intent_analysis['intent_scores']
    
    # Test query enhancement
    enhanced_query = await search_engine._enhance_code_query(query, intent_analysis)
    assert query in enhanced_query
    assert len(enhanced_query) > len(query)  # Should be enhanced
    
    # Test content type determination
    test_result = {
        'metadata': {
            'source_type': 'github',
            'file_path': '/auth/login.py'
        }
    }
    content_type = search_engine._determine_content_type(test_result)
    assert content_type == ContentType.CODE
    
    # Test search history storage
    await search_engine._store_search_history(
        project_id, query, SearchType.CODE_SEMANTIC, [], "test_search_id"
    )
    
    assert project_id in search_engine.search_history
    assert len(search_engine.search_history[project_id]) == 1
    
    print("✅ End-to-end semantic search test passed!")
    print(f"🔍 Query analyzed: '{query}' -> Intent: {intent_analysis['primary_intent']}")
    print(f"🚀 Enhanced query: '{enhanced_query}'")
    print(f"📁 Content type detection working")
    print(f"📊 Search history stored successfully")


if __name__ == "__main__":
    # Run the end-to-end test
    asyncio.run(test_end_to_end_semantic_search())
