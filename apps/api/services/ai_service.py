"""
NeuroSync AI Backend - AI Service
Core AI functionality for query processing and reasoning
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import openai
from openai import AsyncOpenAI
from .token_service import TokenService, TokenUsage

from ..models.requests import QueryRequest
from ..models.responses import QueryResponse, StreamingQueryResponse
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

class AIService:
    """Core AI service for processing queries and generating responses"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.ai_model
        self.token_service = TokenService()
        
    async def process_query(
        self, 
        request: QueryRequest, 
        context_documents: List[Dict[str, Any]] = None
    ) -> QueryResponse:
        """Process a user query and return a comprehensive response"""
        try:
            # Calculate token consumption before processing
            token_usage = self.token_service.calculate_token_consumption(
                query=request.query,
                context=self._build_context(context_documents or []),
                documents=context_documents or []
            )
            
            # Validate user has enough tokens
            can_proceed, validation_message = self.token_service.validate_user_tokens(
                request.user_id, token_usage.tokens_consumed
            )
            
            if not can_proceed:
                return QueryResponse(
                    success=False,
                    message="Insufficient tokens. Please upgrade your plan or purchase token packs.",
                    answer="I apologize, but you don't have enough tokens to process this query. Please upgrade your plan or purchase token packs.",
                    sources=[],
                    confidence=0.0,
                    tokens_used=0,
                    response_time=0.0,
                    error=validation_message
                )
            
            # Log token usage preview
            logger.info(f"Query preview - User: {request.user_id}, Tokens: {token_usage.tokens_consumed}, Complexity: {token_usage.complexity_level}")
            
            start_time = datetime.utcnow()
            
            # Build context from retrieved documents
            context = self._build_context(context_documents or [])
            
            # Create the prompt
            prompt = self._create_prompt(request.query, context, request.context)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # Extract response data
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Calculate confidence based on response quality and context relevance
            confidence = self._calculate_confidence(answer, context_documents or [])
            
            # Process sources
            sources = self._process_sources(context_documents or [])
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log actual token usage
            self.token_service.log_token_usage(
                user_id=request.user_id,
                query=request.query,
                usage=token_usage,
                actual_cost=tokens_used
            )
            
            return QueryResponse(
                success=True,
                message="Query processed successfully",
                answer=answer,
                sources=sources,
                confidence=confidence,
                tokens_used=tokens_used,
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            response_time = (datetime.utcnow() - datetime.utcnow()).total_seconds()
            
            return QueryResponse(
                success=False,
                message=f"Error processing query: {str(e)}",
                answer="I apologize, but I encountered an error while processing your query. Please try again.",
                sources=[],
                confidence=0.0,
                tokens_used=0,
                response_time=response_time
            )
    
    async def stream_query(
        self, 
        request: QueryRequest, 
        context_documents: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[StreamingQueryResponse, None]:
        """Stream a response to a user query"""
        
        try:
            # Calculate token consumption before processing
            token_usage = self.token_service.calculate_token_consumption(
                query=request.query,
                context=self._build_context(context_documents or []),
                documents=context_documents or []
            )
            
            # Validate user has enough tokens
            can_proceed, validation_message = self.token_service.validate_user_tokens(
                request.user_id, token_usage.tokens_consumed
            )
            
            if not can_proceed:
                yield StreamingQueryResponse(
                    chunk="Insufficient tokens. Please upgrade your plan or purchase token packs.",
                    is_final=True,
                    tokens_used=0,
                    sources=[]
                )
                return
            
            # Log token usage preview
            logger.info(f"Query preview - User: {request.user_id}, Tokens: {token_usage.tokens_consumed}, Complexity: {token_usage.complexity_level}")
            
            # Build context from retrieved documents
            context = self._build_context(context_documents or [])
            
            # Create the prompt
            prompt = self._create_prompt(request.query, context, request.context)
            
            # Call OpenAI API with streaming
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=True
            )
            
            total_tokens = 0
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield StreamingQueryResponse(
                        chunk=chunk.choices[0].delta.content,
                        is_final=False
                    )
                
                # Track token usage if available
                if hasattr(chunk, 'usage') and chunk.usage:
                    total_tokens = chunk.usage.total_tokens
            
            # Send final chunk with metadata
            sources = self._process_sources(context_documents or [])
            yield StreamingQueryResponse(
                chunk="",
                is_final=True,
                tokens_used=total_tokens,
                sources=sources
            )
            
            # Log actual token usage
            self.token_service.log_token_usage(
                user_id=request.user_id,
                query=request.query,
                usage=token_usage,
                actual_cost=total_tokens
            )
            
        except Exception as e:
            logger.error(f"Error streaming query: {str(e)}")
            yield StreamingQueryResponse(
                chunk=f"Error: {str(e)}",
                is_final=True,
                tokens_used=0,
                sources=[]
            )
    
    async def get_query_preview(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        Get a preview of how many tokens a query will consume
        For user education and optimization
        """
        return self.token_service.get_token_preview(query, context)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI model"""
        return """You are NeuroSync, an advanced AI assistant specialized in developer knowledge transfer and project understanding. 

Your capabilities include:
- Analyzing code repositories and understanding software architecture
- Processing meeting transcripts and extracting key insights
- Understanding project documentation and specifications
- Providing contextual answers based on project knowledge
- Helping with onboarding, debugging, and knowledge sharing

Guidelines:
1. Always provide accurate, helpful responses based on the available context
2. If you don't have enough information, clearly state what additional context would be helpful
3. Structure your responses clearly with relevant code examples when applicable
4. Focus on practical, actionable insights for developers
5. Maintain context awareness across the entire project ecosystem

Remember: You are helping developers and teams work more efficiently by making project knowledge instantly accessible."""
    
    def _create_prompt(self, query: str, context: str, additional_context: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for the AI model"""
        prompt_parts = []
        
        # Add the main query
        prompt_parts.append(f"User Query: {query}")
        
        # Add project context if available
        if context:
            prompt_parts.append(f"\nRelevant Project Context:\n{context}")
        
        # Add additional context (file path, line numbers, etc.)
        if additional_context:
            context_str = "\n".join([f"{k}: {v}" for k, v in additional_context.items()])
            prompt_parts.append(f"\nAdditional Context:\n{context_str}")
        
        # Add instructions
        prompt_parts.append("""
Please provide a comprehensive answer based on the available context. If the context doesn't contain enough information to fully answer the question, please:
1. Answer what you can based on the available information
2. Clearly indicate what additional information would be helpful
3. Suggest specific areas or files that might contain the missing information

Format your response in a clear, structured way that would be helpful for a developer working on this project.""")
        
        return "\n".join(prompt_parts)
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents"""
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents[:10]):  # Limit to top 10 documents
            doc_context = f"Document {i+1}:"
            
            if doc.get('file_path'):
                doc_context += f"\nFile: {doc['file_path']}"
            
            if doc.get('source_type'):
                doc_context += f"\nSource: {doc['source_type']}"
            
            if doc.get('content'):
                # Truncate content if too long
                content = doc['content']
                if len(content) > 1000:
                    content = content[:1000] + "..."
                doc_context += f"\nContent:\n{content}"
            
            if doc.get('metadata'):
                metadata_str = ", ".join([f"{k}: {v}" for k, v in doc['metadata'].items()])
                doc_context += f"\nMetadata: {metadata_str}"
            
            context_parts.append(doc_context)
        
        return "\n\n" + "\n\n".join(context_parts)
    
    def _calculate_confidence(self, answer: str, context_documents: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on answer quality and context relevance"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have relevant context
        if context_documents:
            confidence += min(0.3, len(context_documents) * 0.05)
        
        # Increase confidence based on answer length and structure
        if len(answer) > 100:
            confidence += 0.1
        
        if any(keyword in answer.lower() for keyword in ['based on', 'according to', 'the code shows']):
            confidence += 0.1
        
        # Decrease confidence if answer indicates uncertainty
        uncertainty_phrases = ['i don\'t know', 'unclear', 'not sure', 'might be', 'possibly']
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _process_sources(self, context_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process context documents into source references"""
        sources = []
        
        for doc in context_documents[:5]:  # Limit to top 5 sources
            source = {
                "type": doc.get('source_type', 'unknown'),
                "relevance_score": doc.get('relevance_score', 0.0)
            }
            
            if doc.get('file_path'):
                source["file_path"] = doc['file_path']
            
            if doc.get('line_numbers'):
                source["line_numbers"] = doc['line_numbers']
            
            if doc.get('title'):
                source["title"] = doc['title']
            
            if doc.get('url'):
                source["url"] = doc['url']
            
            sources.append(source)
        
        return sources
    
    async def analyze_code_context(self, code_content: str, file_path: str) -> Dict[str, Any]:
        """Analyze code content and extract key information"""
        try:
            prompt = f"""Analyze the following code from {file_path} and provide a structured summary:

Code:
```
{code_content[:2000]}  # Limit code length
```

Please provide:
1. Main purpose/functionality
2. Key classes and functions
3. Dependencies and imports
4. Notable patterns or architectures
5. Potential areas of interest for developers

Format as JSON with keys: purpose, key_components, dependencies, patterns, notes"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code analysis expert. Provide structured, accurate analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse the response (in a real implementation, you'd want more robust JSON parsing)
            analysis = response.choices[0].message.content
            
            return {
                "file_path": file_path,
                "analysis": analysis,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing code context: {str(e)}")
            return {
                "file_path": file_path,
                "analysis": f"Error analyzing code: {str(e)}",
                "analyzed_at": datetime.utcnow().isoformat()
            }
    
    async def generate_summary(self, content: str, content_type: str = "document") -> str:
        """Generate a summary of content"""
        try:
            prompt = f"""Summarize the following {content_type} in 2-3 concise sentences that capture the key points:

Content:
{content[:1500]}  # Limit content length

Focus on the most important information that would be useful for someone trying to understand this {content_type}."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating concise, informative summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Summary generation failed: {str(e)}"
