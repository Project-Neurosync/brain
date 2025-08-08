"""
Test script to verify the production-ready RAG system is working correctly.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_rag_system():
    """Test the complete RAG system."""
    print("🧪 Testing NeuroSync Production RAG System")
    print("=" * 50)
    
    try:
        # Test 1: Import RAG components
        print("1. Testing RAG component imports...")
        from services.rag.rag_service import RAGService, Document, SearchResult
        from services.rag.retriever import RetrieverService
        from services.vectorstore.pinecone import PineconeVectorStore
        print("✅ All RAG components imported successfully")
        
        # Test 2: Initialize RAG service
        print("\n2. Testing RAG service initialization...")
        rag_service = RAGService()
        await rag_service.initialize()
        print("✅ RAG service initialized successfully")
        
        # Test 3: Test document search
        print("\n3. Testing document search...")
        search_results = await rag_service.search_documents(
            query="authentication bug",
            project_id="test_project",
            top_k=3
        )
        print(f"✅ Found {len(search_results)} documents")
        
        for i, result in enumerate(search_results):
            print(f"   Document {i+1}: {result.document.title} (score: {result.score:.2f})")
        
        # Test 4: Test complete RAG query
        print("\n4. Testing complete RAG query...")
        response = await rag_service.query(
            query="What bugs have been reported recently?",
            project_id="test_project",
            max_results=3,
            include_sources=True
        )
        
        print(f"✅ RAG query completed")
        print(f"   Answer length: {len(response.get('answer', ''))} characters")
        print(f"   Sources found: {len(response.get('sources', []))}")
        print(f"   Confidence: {response.get('confidence', 0):.2f}")
        
        # Test 5: Test RetrieverService
        print("\n5. Testing RetrieverService...")
        retriever = RetrieverService()
        await retriever.initialize()
        
        retriever_results = await retriever.search_by_text(
            query_text="feature request",
            namespace="project_test",
            top_k=2
        )
        
        print(f"✅ RetrieverService found {len(retriever_results)} documents")
        
        # Test 6: Test vector store
        print("\n6. Testing vector store...")
        vector_store = PineconeVectorStore()
        await vector_store.initialize()
        
        vector_results = await vector_store.search(
            query="implementation details",
            namespace="test",
            top_k=2
        )
        
        print(f"✅ Vector store returned {len(vector_results)} results")
        
        print("\n" + "=" * 50)
        print("🎉 All RAG system tests passed!")
        print("The production-ready RAG system is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ RAG system test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_rag_system())
    sys.exit(0 if success else 1)
