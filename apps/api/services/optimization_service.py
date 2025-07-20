"""
NeuroSync Optimization Service
Provides AI cost optimization through intelligent model selection and query analysis
"""

import logging
import time
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import tiktoken

logger = logging.getLogger(__name__)

class QueryComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate" 
    COMPLEX = "complex"
    CRITICAL = "critical"

class ModelTier(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class ModelConfig:
    name: str
    cost_per_1k_tokens: float
    max_tokens: int
    context_window: int
    quality_score: float
    tier: ModelTier

@dataclass
class OptimizationMetrics:
    total_queries: int
    total_cost_saved: float
    savings_percentage: float
    average_response_time: float
    cache_hit_rate: float
    model_distribution: Dict[str, int]

class OptimizationService:
    """AI Cost Optimization Service with intelligent model selection"""
    
    def __init__(self):
        self.models = self._initialize_models()
        self.query_cache = {}
        self.metrics = {
            "total_queries": 0,
            "total_cost_saved": 0.0,
            "cache_hits": 0,
            "model_usage": {},
            "response_times": []
        }
        
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """Initialize AI model configurations with real pricing"""
        return {
            "gpt-3.5-turbo": ModelConfig(
                name="gpt-3.5-turbo",
                cost_per_1k_tokens=0.0015,
                max_tokens=4096,
                context_window=16385,
                quality_score=7.5,
                tier=ModelTier.BASIC
            ),
            "gpt-4o-mini": ModelConfig(
                name="gpt-4o-mini", 
                cost_per_1k_tokens=0.00015,
                max_tokens=16384,
                context_window=128000,
                quality_score=8.0,
                tier=ModelTier.STANDARD
            ),
            "gpt-4o": ModelConfig(
                name="gpt-4o",
                cost_per_1k_tokens=0.005,
                max_tokens=4096,
                context_window=128000,
                quality_score=9.0,
                tier=ModelTier.PREMIUM
            ),
            "gpt-4": ModelConfig(
                name="gpt-4",
                cost_per_1k_tokens=0.03,
                max_tokens=8192,
                context_window=32768,
                quality_score=9.5,
                tier=ModelTier.ENTERPRISE
            )
        }
    
    def analyze_query_complexity(self, query: str, context: str = "") -> QueryComplexity:
        """Analyze query complexity to determine optimal model"""
        
        # Simple patterns
        simple_patterns = [
            r'^(what|who|when|where|how)\s+is\s+',
            r'^(define|explain)\s+\w+$',
            r'^(list|show)\s+',
            r'^\w+\s*\?$'
        ]
        
        # Complex patterns
        complex_patterns = [
            r'(implement|create|build|design|architect)',
            r'(algorithm|optimization|performance)',
            r'(debug|troubleshoot|fix|error)',
            r'(compare|analyze|evaluate)',
            r'(refactor|improve|optimize)'
        ]
        
        # Critical patterns
        critical_patterns = [
            r'(security|vulnerability|exploit)',
            r'(production|deploy|release)',
            r'(architecture|system\s+design)',
            r'(scale|scalability|performance\s+critical)'
        ]
        
        query_lower = query.lower()
        
        # Check for critical complexity
        if any(re.search(pattern, query_lower) for pattern in critical_patterns):
            return QueryComplexity.CRITICAL
            
        # Check for complex patterns
        if any(re.search(pattern, query_lower) for pattern in complex_patterns):
            return QueryComplexity.COMPLEX
            
        # Check for simple patterns
        if any(re.search(pattern, query_lower) for pattern in simple_patterns):
            return QueryComplexity.SIMPLE
            
        # Consider length and context
        total_length = len(query) + len(context)
        if total_length > 2000:
            return QueryComplexity.COMPLEX
        elif total_length > 500:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def select_optimal_model(self, 
                           complexity: QueryComplexity, 
                           user_tier: str = "starter",
                           context_size: int = 0) -> str:
        """Select the most cost-effective model for the query"""
        
        # Model selection based on complexity and user tier
        if complexity == QueryComplexity.SIMPLE:
            return "gpt-4o-mini"  # Most cost-effective for simple queries
        elif complexity == QueryComplexity.MODERATE:
            if user_tier in ["professional", "enterprise"]:
                return "gpt-4o-mini"
            else:
                return "gpt-3.5-turbo"
        elif complexity == QueryComplexity.COMPLEX:
            if user_tier == "enterprise":
                return "gpt-4o"
            elif user_tier == "professional":
                return "gpt-4o-mini"
            else:
                return "gpt-3.5-turbo"
        else:  # CRITICAL
            if user_tier == "enterprise":
                return "gpt-4"
            else:
                return "gpt-4o"
    
    def estimate_cost(self, model_name: str, token_count: int) -> float:
        """Estimate cost for a query with given model and token count"""
        if model_name not in self.models:
            return 0.0
            
        model = self.models[model_name]
        return (token_count / 1000) * model.cost_per_1k_tokens
    
    def get_optimization_report(self) -> OptimizationMetrics:
        """Generate comprehensive optimization report"""
        
        total_queries = self.metrics["total_queries"]
        if total_queries == 0:
            return OptimizationMetrics(
                total_queries=0,
                total_cost_saved=0.0,
                savings_percentage=0.0,
                average_response_time=0.0,
                cache_hit_rate=0.0,
                model_distribution={}
            )
        
        cache_hit_rate = (self.metrics["cache_hits"] / total_queries) * 100
        avg_response_time = sum(self.metrics["response_times"]) / len(self.metrics["response_times"]) if self.metrics["response_times"] else 0.0
        
        # Calculate savings percentage (assuming baseline cost without optimization)
        baseline_cost = total_queries * 0.037  # Average cost per query without optimization
        actual_cost = baseline_cost - self.metrics["total_cost_saved"]
        savings_percentage = (self.metrics["total_cost_saved"] / baseline_cost) * 100 if baseline_cost > 0 else 0.0
        
        return OptimizationMetrics(
            total_queries=total_queries,
            total_cost_saved=self.metrics["total_cost_saved"],
            savings_percentage=savings_percentage,
            average_response_time=avg_response_time,
            cache_hit_rate=cache_hit_rate,
            model_distribution=self.metrics["model_usage"].copy()
        )
    
    def get_model_recommendations(self, user_tier: str = "starter") -> List[Dict]:
        """Get model recommendations for user tier"""
        recommendations = []
        
        for model_name, config in self.models.items():
            suitable_for = []
            
            if config.tier == ModelTier.BASIC:
                suitable_for = ["Simple queries", "Basic Q&A", "Quick lookups"]
            elif config.tier == ModelTier.STANDARD:
                suitable_for = ["Moderate complexity", "Code explanations", "Documentation"]
            elif config.tier == ModelTier.PREMIUM:
                suitable_for = ["Complex analysis", "Code generation", "Problem solving"]
            elif config.tier == ModelTier.ENTERPRISE:
                suitable_for = ["Critical decisions", "Architecture design", "Security analysis"]
            
            recommendations.append({
                "model": model_name,
                "cost_per_1k_tokens": config.cost_per_1k_tokens,
                "quality_score": config.quality_score,
                "max_tokens": config.max_tokens,
                "suitable_for": suitable_for,
                "recommended": self._is_recommended_for_tier(config.tier, user_tier)
            })
        
        return sorted(recommendations, key=lambda x: x["cost_per_1k_tokens"])
    
    def _is_recommended_for_tier(self, model_tier: ModelTier, user_tier: str) -> bool:
        """Check if model is recommended for user tier"""
        tier_mapping = {
            "starter": [ModelTier.BASIC, ModelTier.STANDARD],
            "professional": [ModelTier.STANDARD, ModelTier.PREMIUM],
            "enterprise": [ModelTier.PREMIUM, ModelTier.ENTERPRISE]
        }
        
        return model_tier in tier_mapping.get(user_tier, [ModelTier.BASIC])
    
    def process_optimized_query(self, 
                              query: str, 
                              context: str = "",
                              user_tier: str = "starter") -> Dict:
        """Process a query with optimization and return results"""
        
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{query}:{context}:{user_tier}"
        if cache_key in self.query_cache:
            self.metrics["cache_hits"] += 1
            return {
                "cached": True,
                "result": self.query_cache[cache_key],
                "model_used": "cached",
                "cost_saved": 0.015,  # Average cost saved from cache hit
                "response_time": time.time() - start_time
            }
        
        # Analyze complexity and select model
        complexity = self.analyze_query_complexity(query, context)
        selected_model = self.select_optimal_model(complexity, user_tier)
        
        # Estimate token count and cost
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        token_count = len(encoding.encode(query + context))
        estimated_cost = self.estimate_cost(selected_model, token_count)
        
        # Calculate cost savings (vs using GPT-4 for everything)
        baseline_cost = self.estimate_cost("gpt-4", token_count)
        cost_saved = max(0, baseline_cost - estimated_cost)
        
        # Update metrics
        self.metrics["total_queries"] += 1
        self.metrics["total_cost_saved"] += cost_saved
        self.metrics["model_usage"][selected_model] = self.metrics["model_usage"].get(selected_model, 0) + 1
        self.metrics["response_times"].append(time.time() - start_time)
        
        result = {
            "cached": False,
            "model_used": selected_model,
            "complexity": complexity.value,
            "estimated_cost": estimated_cost,
            "cost_saved": cost_saved,
            "token_count": token_count,
            "response_time": time.time() - start_time
        }
        
        # Cache the result
        self.query_cache[cache_key] = result
        
        return result
    
    def clear_cache(self) -> Dict:
        """Clear the query cache"""
        cache_size = len(self.query_cache)
        self.query_cache.clear()
        return {
            "message": f"Cache cleared successfully",
            "items_cleared": cache_size
        }

# Global optimization service instance
optimization_service = OptimizationService()
