"""
Chat API routes for NeuroSync RAG system.
Provides ChatGPT-like interface for querying integrated data.
"""

import logging
import uuid
import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from models.database import get_db
from models.user_models import User
from models.project import Project
from middleware.auth import get_current_user

# Import our working LLM service
try:
    from services.llm.groq import GroqLLM
except ImportError:
    GroqLLM = None

# Create logger
logger = logging.getLogger(__name__)

# Create router for chat operations
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Initialize LLM service with detailed logging
try:
    logger.info("Starting LLM service initialization...")
    
    # Set up Groq API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY environment variable not set"
        )
    logger.info(f"Groq API key configured: {groq_api_key[:20]}...")
    
    # Check if GroqLLM is available
    logger.info(f"GroqLLM class available: {GroqLLM is not None}")
    
    if GroqLLM and groq_api_key:
        logger.info("Attempting to initialize GroqLLM...")
        llm_service = GroqLLM(api_key=groq_api_key, model_name="llama3-8b-8192")
        logger.info(f"Groq LLM service initialized successfully. Using HTTP method.")
    else:
        llm_service = None
        logger.warning(f"Groq LLM service not available. GroqLLM: {GroqLLM}, API key: {bool(groq_api_key)}")
except Exception as e:
    logger.error(f"Failed to initialize LLM service: {e}")
    import traceback
    logger.error(f"Full traceback: {traceback.format_exc()}")
    llm_service = None

logger.info(f"Final LLM service state: {llm_service is not None}")


# Request/Response models
class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    project_id: Optional[str] = Field(None, description="Project context for the query")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    stream: bool = Field(False, description="Whether to stream the response")


class ChatResponse(BaseModel):
    """Chat response model."""
    id: str = Field(..., description="Response ID")
    message: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents")
    confidence: float = Field(..., description="Response confidence score")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(BaseModel):
    """Conversation history model."""
    conversation_id: str
    messages: List[ChatMessage]
    project_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response.
    """
    if not llm_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service is not available"
        )
    
    try:
        logger.info(f"Processing chat query for user: {current_user.email}")
        
        # Validate project access if project_id is provided
        if request.project_id:
            project = db.query(Project).filter(
                Project.id == request.project_id,
                Project.user_id == current_user.id
            ).first()
            
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found or access denied"
                )
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Initialize simple RAG service for document retrieval
        from services.simple_rag import SimpleRAGService
        rag_service = SimpleRAGService()
        await rag_service.initialize()
        
        # Get relevant documents
        documents = await rag_service.search_documents(
            query=request.message,
            project_id=request.project_id,
            top_k=5
        )
        
        # Build context and sources
        context_parts = []
        sources = []
        
        for doc_result in documents:
            doc = doc_result.document
            context_parts.append(f"Source: {doc.title}\nContent: {doc.content}\n")
            sources.append({
                'title': doc.title,
                'type': doc.source_type,
                'url': doc.url,
                'relevance_score': doc_result.score
            })
        
        context = "\n---\n".join(context_parts)
        
        # Create enhanced prompt with context
        project_context = f" about project {request.project_id}" if request.project_id else ""
        
        prompt = f"""You are NeuroSync AI, an intelligent assistant for software development teams.
Based on the following context from the user's integrated data sources, please answer their question{project_context}.

Context from integrated sources:
{context}

Question: {request.message}

Please provide a helpful and accurate answer based on the context provided. If the context doesn't contain enough information to answer the question completely, please say so and provide what information you can. Be specific and reference the sources when relevant."""
        
        # Generate response with LLM
        response = await llm_service.complete(
            prompt=prompt,
            temperature=0.7,
            max_tokens=1024
        )
        
        return ChatResponse(
            id=str(uuid.uuid4()),
            message=response.text or "I'm sorry, I couldn't generate a response.",
            conversation_id=conversation_id,
            sources=sources,
            confidence=0.9 if sources else 0.7
        )
        
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat query"
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stream a chat response in real-time.
    """
    if not llm_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service is not available"
        )
    
    try:
        # Validate project access if project_id is provided
        if request.project_id:
            project = db.query(Project).filter(
                Project.id == request.project_id,
                Project.user_id == current_user.id
            ).first()
            
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found or access denied"
                )
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        async def generate_stream():
            """Generate streaming response with intelligent RAG detection."""
            try:
                # Initialize LLM-powered query classifier
                from services.query_classifier import query_classifier
                query_classifier.llm_service = llm_service  # Inject LLM service
                
                # Classify query to determine if RAG is needed
                needs_rag, confidence, reason = await query_classifier.classify_query(
                    query=request.message,
                    project_id=request.project_id
                )
                
                logger.info(f"Query classification: needs_rag={needs_rag}, confidence={confidence:.2f}, reason={reason}")
                
                if needs_rag:
                    # Initialize simple RAG service for context-aware response
                    from services.simple_rag import SimpleRAGService
                    rag_service = SimpleRAGService()
                    await rag_service.initialize()
                    
                    # Get relevant documents
                    documents = await rag_service.search_documents(
                        query=request.message,
                        project_id=request.project_id,
                        top_k=5
                    )
                else:
                    # No RAG needed - use empty documents list
                    documents = []
                
                # Send sources first
                sources = []
                for doc_result in documents:
                    doc = doc_result.document
                    source = {
                        "title": doc.title,
                        "type": doc.source_type,
                        "url": doc.url,
                        "relevance_score": doc_result.score
                    }
                    sources.append(source)
                
                if sources:
                    import json
                    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
                
                # Create appropriate prompt based on whether RAG is needed
                if needs_rag and documents:
                    # Create context from documents
                    context_parts = []
                    for doc_result in documents:
                        doc = doc_result.document
                        context_parts.append(f"Source: {doc.title}\nContent: {doc.content}\n")
                    
                    context = "\n---\n".join(context_parts)
                    project_context = f" about project {request.project_id}" if request.project_id else ""
                    
                    prompt = f"""You are NeuroSync AI, an intelligent assistant for software development teams.
Based on the following context from the user's integrated data sources, please answer their question{project_context}.

Context from integrated sources:
{context}

Question: {request.message}

Please provide a helpful and accurate answer based on the context provided. If the context doesn't contain enough information to answer the question completely, please say so and provide what information you can. Be specific and reference the sources when relevant."""
                
                elif needs_rag and not documents:
                    # RAG was requested but no documents found
                    project_context = f" about project {request.project_id}" if request.project_id else ""
                    prompt = f"""You are NeuroSync AI, an intelligent assistant for software development teams.
The user asked a question{project_context}, but I couldn't find any relevant information in their integrated data sources.

Question: {request.message}

Please provide a helpful response acknowledging that you don't have specific project information available, but offer general guidance if possible."""
                
                else:
                    # Direct response without RAG
                    prompt = f"""You are NeuroSync AI, an intelligent assistant for software development teams.
Please provide a helpful and friendly response to the user's message.

User message: {request.message}

Respond naturally and helpfully. If this is a greeting, respond warmly. If it's a general question, provide useful information."""
                
                logger.info(f"Using {'RAG-enhanced' if needs_rag else 'direct'} prompt for response generation")

                # Stream the response using our working LLM service
                async for chunk in llm_service.stream_complete(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=1024
                ):
                    # Create proper JSON structure for streaming
                    import json
                    token_data = {
                        "type": "token",
                        "content": chunk
                    }
                    yield f"data: {json.dumps(token_data)}\n\n"
                
                # Send end marker
                complete_data = {"type": "complete"}
                yield f"data: {json.dumps(complete_data)}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming response: {e}")
                yield f"data: Error: {str(e)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Conversation-ID": conversation_id
            }
        )
        
    except Exception as e:
        logger.error(f"Error setting up chat stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup chat stream"
        )


@router.get("/conversations", response_model=List[ConversationHistory])
async def get_conversations(
    project_id: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's conversation history.
    """
    try:
        # For now, return empty list as we haven't implemented conversation storage yet
        # This would typically query a conversations table in the database
        logger.info(f"Getting conversations for user: {current_user.email}")
        return []
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversations"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation.
    """
    try:
        # For now, just return success as we haven't implemented conversation storage yet
        logger.info(f"Deleting conversation {conversation_id} for user: {current_user.email}")
        return {"message": "Conversation deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.post("/test")
async def chat_test(request: ChatRequest):
    """
    Test chat endpoint without authentication (for testing only).
    """
    print(f"[TEST] Test endpoint called with message: {request.message}")
    print(f"[TEST] LLM service available: {llm_service is not None}")
    
    if not llm_service:
        print("[TEST] LLM service is None, returning error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service is not available"
        )
    
    try:
        # Create a simple prompt for testing
        prompt = f"You are NeuroSync AI, an intelligent assistant for software development teams. Please answer the following question helpfully and accurately:\n\nQuestion: {request.message}"
        print(f"[TEST] About to call llm_service.complete with prompt: {prompt[:50]}...")
        
        # Process the query with LLM
        response = await llm_service.complete(
            prompt=prompt,
            temperature=0.7,
            max_tokens=1024
        )
        
        print(f"[TEST] LLM response received: {response.text[:50] if response.text else 'None'}...")
        
        return ChatResponse(
            id=str(uuid.uuid4()),
            message=f"DEBUG: {response.text or 'I could not generate a response.'}",
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            sources=[],
            confidence=0.8
        )
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process test query"
        )


@router.get("/logs")
async def chat_logs():
    """
    Get recent log messages for debugging.
    """
    # This is a simple way to capture recent log activity
    # In production, you'd use proper log aggregation
    return {
        "message": "Check the FastAPI server console for detailed logs",
        "log_location": "Terminal where 'uvicorn main:app --reload' is running",
        "expected_logs": [
            "Starting LLM service initialization...",
            "GroqLLM.__init__ called with model: llama3-8b-8192",
            "AsyncGroq available: True/False",
            "GroqLLM.complete called. Client available: True/False",
            "HTTP fallback called with prompt: ...",
            "Making HTTP request to: https://api.groq.com/openai/v1/chat/completions",
            "HTTP response status: ...",
            "Any error messages with full tracebacks"
        ]
    }


@router.get("/debug")
async def chat_debug():
    """
    Debug endpoint to check LLM service status.
    """
    debug_info = {
        "llm_service_available": llm_service is not None,
        "groq_llm_class_available": GroqLLM is not None,
        "groq_api_key_configured": bool(os.getenv("GROQ_API_KEY", ""))
    }
    
    if llm_service:
        debug_info.update({
            "llm_client_available": llm_service.client is not None,
            "llm_model_name": getattr(llm_service, 'model_name', 'unknown'),
            "llm_api_key_prefix": getattr(llm_service, 'api_key', '')[:20] + '...' if hasattr(llm_service, 'api_key') else 'not_found'
        })
    
    return debug_info


@router.get("/health")
async def chat_health():
    """
    Check chat service health.
    """
    try:
        if not llm_service:
            return {
                "status": "unhealthy",
                "message": "LLM service not initialized",
                "timestamp": datetime.utcnow()
            }
        
        # Test LLM connection
        test_response = await llm_service.complete("Hello", max_tokens=5)
        
        return {
            "status": "healthy",
            "message": "Chat service is operational",
            "llm_available": bool(test_response.text),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.utcnow()
        }
