"""
Token Service - Smart Token Consumption Model
Implements Windsurf-style variable token consumption based on query complexity
"""

import tiktoken
from typing import Dict, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Token usage calculation result"""
    tokens_consumed: int
    estimated_cost: float
    complexity_level: str
    input_tokens: int
    estimated_output_tokens: int

class TokenService:
    """
    Smart token consumption service that calculates variable token costs
    based on query complexity, similar to Windsurf's model
    """
    
    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        
        # Token consumption tiers
        self.token_tiers = {
            "simple": {"max_input": 500, "tokens": 1, "description": "Simple queries"},
            "medium": {"max_input": 1500, "tokens": 2, "description": "Medium complexity"},
            "complex": {"max_input": 3000, "tokens": 3, "description": "Complex analysis"},
            "advanced": {"max_input": 5000, "tokens": 4, "description": "Advanced queries"},
            "enterprise": {"max_input": 8000, "tokens": 5, "description": "Enterprise-level"}
        }
        
        # Rate limiting and safety
        self.max_tokens_per_query = 5
        self.max_input_tokens = 8000
        self.max_output_tokens = 2000
        
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for given text"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token estimation failed: {e}")
            # Fallback estimation: ~4 chars per token
            return len(text) // 4
    
    def calculate_token_consumption(
        self, 
        query: str, 
        context: str = "", 
        documents: list = None
    ) -> TokenUsage:
        """
        Calculate how many NeuroSync tokens this query will consume
        Based on input complexity and estimated processing requirements
        """
        
        # Calculate total input tokens
        full_input = query
        if context:
            full_input += f"\n\nContext: {context}"
        
        if documents:
            doc_text = "\n".join([doc.get("content", "")[:1000] for doc in documents[:5]])
            full_input += f"\n\nDocuments: {doc_text}"
        
        input_tokens = self.estimate_tokens(full_input)
        
        # Apply safety limits
        if input_tokens > self.max_input_tokens:
            input_tokens = self.max_input_tokens
            logger.warning(f"Input truncated to {self.max_input_tokens} tokens")
        
        # Determine complexity tier and token consumption
        tokens_consumed = self._get_token_tier(input_tokens)
        complexity_level = self._get_complexity_level(input_tokens)
        
        # Estimate output tokens (for cost calculation)
        estimated_output = min(input_tokens // 2, self.max_output_tokens)
        
        # Calculate estimated cost (for internal tracking)
        estimated_cost = self._calculate_cost(input_tokens, estimated_output)
        
        return TokenUsage(
            tokens_consumed=tokens_consumed,
            estimated_cost=estimated_cost,
            complexity_level=complexity_level,
            input_tokens=input_tokens,
            estimated_output_tokens=estimated_output
        )
    
    def _get_token_tier(self, input_tokens: int) -> int:
        """Determine how many NeuroSync tokens to consume based on input complexity"""
        for tier_name, tier_info in self.token_tiers.items():
            if input_tokens <= tier_info["max_input"]:
                return tier_info["tokens"]
        
        # For very large queries, scale up to max
        return self.max_tokens_per_query
    
    def _get_complexity_level(self, input_tokens: int) -> str:
        """Get human-readable complexity level"""
        for tier_name, tier_info in self.token_tiers.items():
            if input_tokens <= tier_info["max_input"]:
                return tier_name
        return "enterprise"
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated OpenAI API cost"""
        # GPT-4 pricing (as of 2024)
        input_cost = input_tokens * 0.00003  # $0.03 per 1K tokens
        output_cost = output_tokens * 0.00006  # $0.06 per 1K tokens
        return input_cost + output_cost
    
    def get_token_preview(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        Get a preview of token consumption for user education
        Returns user-friendly information about the query cost
        """
        usage = self.calculate_token_consumption(query, context)
        
        return {
            "tokens_required": usage.tokens_consumed,
            "complexity": usage.complexity_level,
            "description": self.token_tiers.get(usage.complexity_level, {}).get("description", "Unknown"),
            "input_size": usage.input_tokens,
            "optimization_tips": self._get_optimization_tips(usage.complexity_level)
        }
    
    def _get_optimization_tips(self, complexity: str) -> list:
        """Provide tips to optimize token usage"""
        tips = {
            "simple": ["Your query is efficiently sized!"],
            "medium": ["Consider breaking complex questions into smaller parts"],
            "complex": [
                "Try focusing on specific aspects of your question",
                "Break large analysis requests into multiple queries"
            ],
            "advanced": [
                "Consider splitting this into 2-3 separate questions",
                "Focus on the most critical aspects first",
                "Use more specific keywords"
            ],
            "enterprise": [
                "This is a very large query - consider breaking it down",
                "Focus on one specific area at a time",
                "Use project-specific context to reduce scope"
            ]
        }
        return tips.get(complexity, ["Consider optimizing your query"])
    
    def validate_user_tokens(self, user_id: str, required_tokens: int) -> Tuple[bool, str]:
        """
        Validate if user has enough tokens for the query
        Returns (can_proceed, message)
        """
        # This would integrate with your user/subscription service
        # For now, return a placeholder
        return True, "Token validation would be implemented here"
    
    def log_token_usage(
        self, 
        user_id: str, 
        query: str, 
        usage: TokenUsage,
        actual_cost: float = None
    ):
        """Log token usage for analytics and billing"""
        log_data = {
            "user_id": user_id,
            "query_length": len(query),
            "tokens_consumed": usage.tokens_consumed,
            "complexity": usage.complexity_level,
            "estimated_cost": usage.estimated_cost,
            "actual_cost": actual_cost,
            "input_tokens": usage.input_tokens,
            "estimated_output": usage.estimated_output_tokens
        }
        
        logger.info(f"Token usage: {log_data}")
        # Here you would save to database for analytics
