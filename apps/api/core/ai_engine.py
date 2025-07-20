"""
AI Engine for NeuroSync AI Backend
Handles all AI-related operations including query processing and response generation.
"""

from typing import Dict, Any, List, Optional
import logging
import openai
import asyncio
from datetime import datetime
import tiktoken
from enum import Enum

class ModelType(Enum):
    """AI model types for cost optimization."""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"

class QueryComplexity(Enum):
    """Query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"

class AIEngine:
    """
    Main AI engine for processing queries and generating responses.
    Integrates with OpenAI models and provides cost optimization.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the AI Engine with optional configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.openai_api_key = self.config.get("openai_api_key")
        
        # Model configurations with pricing (per 1k tokens)
        self.model_configs = {
            ModelType.GPT_4O_MINI: {
                "input_cost": 0.00015,
                "output_cost": 0.0006,
                "max_tokens": 128000,
                "quality_score": 0.8
            },
            ModelType.GPT_4O: {
                "input_cost": 0.005,
                "output_cost": 0.015,
                "max_tokens": 128000,
                "quality_score": 0.95
            },
            ModelType.GPT_4: {
                "input_cost": 0.03,
                "output_cost": 0.06,
                "max_tokens": 8192,
                "quality_score": 1.0
            },
            ModelType.GPT_35_TURBO: {
                "input_cost": 0.0015,
                "output_cost": 0.002,
                "max_tokens": 16385,
                "quality_score": 0.7
            }
        }
        
        self.initialize_models()
    
    def initialize_models(self) -> None:
        """Initialize AI models and other required resources."""
        self.logger.info("Initializing AI models...")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.logger.info("OpenAI API key configured")
        else:
            self.logger.warning("OpenAI API key not provided - AI functionality will be limited")
    
    def analyze_query_complexity(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryComplexity:
        """
        Analyze query complexity to determine appropriate model.
        
        Args:
            query: The user's query string
            context: Optional context for the query
            
        Returns:
            QueryComplexity enum value
        """
        query_length = len(query)
        word_count = len(query.split())
        
        # Simple heuristics for complexity analysis
        if query_length < 50 and word_count < 10:
            return QueryComplexity.SIMPLE
        elif query_length < 200 and word_count < 40:
            return QueryComplexity.MODERATE
        elif query_length < 500 and word_count < 100:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.CRITICAL
    
    def select_optimal_model(
        self, 
        complexity: QueryComplexity, 
        user_tier: str = "starter",
        context_size: int = 0
    ) -> ModelType:
        """
        Select the optimal model based on complexity and user tier.
        
        Args:
            complexity: Query complexity level
            user_tier: User's subscription tier
            context_size: Size of context in tokens
            
        Returns:
            Optimal ModelType for the query
        """
        # Enterprise users get premium models
        if user_tier == "enterprise":
            if complexity in [QueryComplexity.CRITICAL, QueryComplexity.COMPLEX]:
                return ModelType.GPT_4O
            else:
                return ModelType.GPT_4O_MINI
        
        # Professional users get balanced optimization
        elif user_tier == "professional":
            if complexity == QueryComplexity.CRITICAL:
                return ModelType.GPT_4O
            elif complexity == QueryComplexity.COMPLEX:
                return ModelType.GPT_4O_MINI
            else:
                return ModelType.GPT_4O_MINI
        
        # Starter users get cost-optimized models
        else:
            if complexity == QueryComplexity.CRITICAL:
                return ModelType.GPT_4O_MINI
            else:
                return ModelType.GPT_4O_MINI
    
    def count_tokens(self, text: str, model: ModelType = ModelType.GPT_4O_MINI) -> int:
        """
        Count tokens in text for the specified model.
        
        Args:
            text: Text to count tokens for
            model: Model type for token counting
            
        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(model.value)
            return len(encoding.encode(text))
        except Exception:
            # Fallback to simple word count estimation
            return len(text.split()) * 1.3  # Rough estimation
    
    async def process_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        user_tier: str = "starter",
        stream: bool = False,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process a user query and generate a response.
        
        Args:
            query: The user's query string
            context: Optional context for the query
            user_tier: User's subscription tier
            stream: Whether to stream the response
            max_tokens: Maximum tokens for response
            temperature: AI temperature setting
            
        Returns:
            Dict containing the response and metadata
        """
        start_time = datetime.utcnow()
        
        if not self.openai_api_key:
            return {
                "response": "AI functionality is not available. Please configure OpenAI API key.",
                "sources": [],
                "confidence": 0.0,
                "tokens_used": 0,
                "cost": 0.0,
                "model_used": "none",
                "processing_time": 0.0
            }
        
        try:
            # Analyze query complexity
            complexity = self.analyze_query_complexity(query, context)
            
            # Select optimal model
            selected_model = self.select_optimal_model(complexity, user_tier)
            
            # Prepare context
            context_text = ""
            if context and context.get("sources"):
                context_text = "\n".join([
                    f"Source: {src.get('title', 'Unknown')}\n{src.get('content', '')}"
                    for src in context["sources"][:5]  # Limit to top 5 sources
                ])
            
            # Build prompt
            system_prompt = """You are NeuroSync AI, an intelligent assistant for developer knowledge transfer. 
            You help developers understand codebases, projects, and technical documentation.
            Provide clear, accurate, and helpful responses based on the provided context."""
            
            user_prompt = query
            if context_text:
                user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}"
            
            # Count tokens
            input_tokens = self.count_tokens(system_prompt + user_prompt, selected_model)
            
            # Make OpenAI API call
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await openai.ChatCompletion.acreate(
                model=selected_model.value,
                messages=messages,
                max_tokens=max_tokens or 1000,
                temperature=temperature or 0.7,
                stream=stream
            )
            
            if stream:
                # Handle streaming response
                return await self._handle_streaming_response(response, selected_model, input_tokens, start_time)
            else:
                # Handle regular response
                response_text = response.choices[0].message.content
                output_tokens = self.count_tokens(response_text, selected_model)
                
                # Calculate cost
                model_config = self.model_configs[selected_model]
                input_cost = (input_tokens / 1000) * model_config["input_cost"]
                output_cost = (output_tokens / 1000) * model_config["output_cost"]
                total_cost = input_cost + output_cost
                
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                return {
                    "response": response_text,
                    "sources": context.get("sources", []) if context else [],
                    "confidence": model_config["quality_score"],
                    "tokens_used": input_tokens + output_tokens,
                    "cost": round(total_cost, 6),
                    "model_used": selected_model.value,
                    "processing_time": processing_time,
                    "complexity": complexity.value,
                    "optimization_applied": True
                }
                
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "response": f"I encountered an error processing your query: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "tokens_used": 0,
                "cost": 0.0,
                "model_used": "error",
                "processing_time": processing_time,
                "error": str(e)
            }
    
    async def _handle_streaming_response(
        self, 
        response_stream, 
        model: ModelType, 
        input_tokens: int, 
        start_time: datetime
    ) -> Dict[str, Any]:
        """Handle streaming response from OpenAI."""
        full_response = ""
        async for chunk in response_stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        
        output_tokens = self.count_tokens(full_response, model)
        model_config = self.model_configs[model]
        
        input_cost = (input_tokens / 1000) * model_config["input_cost"]
        output_cost = (output_tokens / 1000) * model_config["output_cost"]
        total_cost = input_cost + output_cost
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "response": full_response,
            "sources": [],
            "confidence": model_config["quality_score"],
            "tokens_used": input_tokens + output_tokens,
            "cost": round(total_cost, 6),
            "model_used": model.value,
            "processing_time": processing_time,
            "streamed": True
        }
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for the given texts.
        
        Args:
            texts: List of input texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        if not self.openai_api_key:
            # Return dummy embeddings if no API key
            return [[0.0] * 1536 for _ in texts]
        
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-3-small",
                input=texts
            )
            
            return [item.embedding for item in response.data]
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            # Return dummy embeddings on error
            return [[0.0] * 1536 for _ in texts]
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the AI engine."""
        return {
            "status": "operational" if self.openai_api_key else "limited",
            "models_available": list(self.model_configs.keys()),
            "openai_configured": bool(self.openai_api_key),
            "cost_optimization_enabled": True,
            "version": "1.0.0"
        }
    
    def get_cost_estimate(self, query: str, user_tier: str = "starter") -> Dict[str, Any]:
        """
        Get cost estimate for a query without processing it.
        
        Args:
            query: Query to estimate cost for
            user_tier: User's subscription tier
            
        Returns:
            Cost estimate information
        """
        complexity = self.analyze_query_complexity(query)
        selected_model = self.select_optimal_model(complexity, user_tier)
        
        estimated_input_tokens = self.count_tokens(query, selected_model)
        estimated_output_tokens = 200  # Average response length
        
        model_config = self.model_configs[selected_model]
        input_cost = (estimated_input_tokens / 1000) * model_config["input_cost"]
        output_cost = (estimated_output_tokens / 1000) * model_config["output_cost"]
        total_cost = input_cost + output_cost
        
        return {
            "estimated_cost": round(total_cost, 6),
            "selected_model": selected_model.value,
            "complexity": complexity.value,
            "estimated_tokens": estimated_input_tokens + estimated_output_tokens,
            "quality_score": model_config["quality_score"]
        }
