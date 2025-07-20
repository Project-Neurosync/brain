"""
Token Tracker for NeuroSync AI Backend
Handles token usage tracking, billing, and quota management.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.token_models import User, TokenQuota, TokenUsage, TokenPack, TokenOptimization
from services.database_service import db_service

class TokenType(Enum):
    """Types of tokens that can be consumed."""
    INPUT = "input"
    OUTPUT = "output"
    EMBEDDING = "embedding"
    SEARCH = "search"

class TokenTracker:
    """
    Tracks token usage, manages quotas, and handles billing calculations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, db_service: Optional[Any] = None):
        """Initialize the Token Tracker."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.db_service = db_service
        # Remove in-memory storage - now using database
        # self.usage_records = {}
        # self.user_quotas = {}
        self.pricing = {
            TokenType.INPUT: 0.0015,    # per 1k tokens
            TokenType.OUTPUT: 0.002,    # per 1k tokens
            TokenType.EMBEDDING: 0.0001,  # per 1k tokens
            TokenType.SEARCH: 0.0005    # per search
        }
        
        # Subscription tier token quotas (monthly limits)
        self.tier_quotas = {
            "starter": 200,      # Starter: 200 tokens/month
            "professional": 400, # Professional: 400 tokens/month  
            "enterprise": 800    # Enterprise: 800 tokens/month
        }
    
    def _get_quota_for_tier(self, tier: str) -> int:
        """Get monthly token quota based on subscription tier"""
        return self.tier_quotas.get(tier.lower(), self.tier_quotas["starter"])
    
    async def initialize(self) -> None:
        """Initialize the token tracking system."""
        self.logger.info("Initializing Token Tracker...")
        # TODO: Initialize database connection for persistent storage
    
    async def track_usage(
        self,
        user_id: str,
        project_id: str,
        token_type: TokenType,
        token_count: int,
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track token usage for a user and project.
        
        Args:
            user_id: User ID
            project_id: Project ID
            token_type: Type of tokens consumed
            token_count: Number of tokens used
            model_name: AI model used (if applicable)
            metadata: Additional metadata
            
        Returns:
            Usage record with cost calculation
        """
        timestamp = datetime.utcnow()
        cost = self._calculate_cost(token_type, token_count, model_name)
        
        usage_record = {
            "id": f"{user_id}_{project_id}_{timestamp.isoformat()}",
            "user_id": user_id,
            "project_id": project_id,
            "token_type": token_type.value,
            "token_count": token_count,
            "model_name": model_name,
            "cost": cost,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        # Store usage record in database
        try:
            if not self.db_service:
                raise Exception("Database service not available")
            
            with self.db_service.get_db_session() as session:
                # Create TokenUsage record
                usage_db_record = TokenUsage(
                    user_id=user_id,
                    project_id=project_id,
                    token_type=token_type.value,
                    token_count=token_count,
                    model_used=model_name,
                    cost_usd=cost,
                    complexity_level="moderate",  # Default complexity
                    query_metadata=str(metadata or {}),
                    created_at=timestamp
                )
                session.add(usage_db_record)
                session.commit()
                
                # Update usage record with database ID
                usage_record["id"] = str(usage_db_record.id)
        except Exception as e:
            self.logger.error(f"Failed to store usage record in database: {e}")
            # Fallback to in-memory storage for this record
            if user_id not in self.usage_records:
                self.usage_records[user_id] = []
            self.usage_records[user_id].append(usage_record)
        
        self.logger.info(f"Tracked {token_count} {token_type.value} tokens for user {user_id}, cost: ${cost:.4f}")
        
        return usage_record
    
    async def get_usage_summary(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary for a user or project.
        
        Args:
            user_id: User ID
            project_id: Optional project filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Usage summary with totals and breakdowns
        """
        try:
            from services.database_service import db_service
            with db_service.get_db_session() as session:
                # Build query
                query = session.query(TokenUsage).filter(TokenUsage.user_id == user_id)
                
                # Apply filters
                if project_id:
                    query = query.filter(TokenUsage.project_id == project_id)
                if start_date:
                    query = query.filter(TokenUsage.created_at >= start_date)
                if end_date:
                    query = query.filter(TokenUsage.created_at <= end_date)
                
                # Get records
                db_records = query.all()
                
                # Convert to dict format
                records = []
                for db_record in db_records:
                    records.append({
                        "id": str(db_record.id),
                        "user_id": db_record.user_id,
                        "project_id": db_record.project_id,
                        "token_type": db_record.token_type,
                        "token_count": db_record.token_count,
                        "model_name": db_record.model_used,
                        "cost": db_record.cost_usd,
                        "timestamp": db_record.created_at,
                        "metadata": db_record.query_metadata or "{}"
                    })
        except Exception as e:
            self.logger.error(f"Failed to get usage from database: {e}")
            # Fallback to in-memory storage
            if user_id not in self.usage_records:
                return {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "breakdown": {},
                    "records": []
                }
            records = self.usage_records[user_id]
            
            # Apply filters for fallback
            if project_id:
                records = [r for r in records if r["project_id"] == project_id]
            if start_date:
                records = [r for r in records if r["timestamp"] >= start_date]
            if end_date:
                records = [r for r in records if r["timestamp"] <= end_date]
        
        # Calculate totals
        total_tokens = sum(r["token_count"] for r in records)
        total_cost = sum(r["cost"] for r in records)
        
        # Create breakdown by token type
        breakdown = {}
        for record in records:
            token_type = record["token_type"]
            if token_type not in breakdown:
                breakdown[token_type] = {"tokens": 0, "cost": 0.0, "count": 0}
            breakdown[token_type]["tokens"] += record["token_count"]
            breakdown[token_type]["cost"] += record["cost"]
            breakdown[token_type]["count"] += 1
        
        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "breakdown": breakdown,
            "records": records[-50:]  # Return last 50 records
        }
    
    async def check_quota(self, user_id: str, token_count: int, subscription_tier: str = "starter") -> Dict[str, Any]:
        """
        Check if user has sufficient quota for token usage.
        
        Args:
            user_id: User ID
            token_count: Tokens to be consumed
            subscription_tier: User's subscription tier (starter, professional, enterprise)
            
        Returns:
            Quota check result
        """
        # Get or create user quota from database
        with db_service.get_db_session() as session:
            # Get user from database
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                # Create new user with default subscription tier
                user = User(
                    id=user_id,
                    email=f"{user_id}@example.com",  # Placeholder email
                    name="New User",
                    subscription_tier=subscription_tier
                )
                session.add(user)
                session.commit()
            
            # Get or create token quota
            quota = session.query(TokenQuota).filter(TokenQuota.user_id == user_id).first()
            if not quota:
                tier_quota = self._get_quota_for_tier(subscription_tier)
                quota = TokenQuota(
                    user_id=user_id,
                    quota_limit=tier_quota,
                    quota_used=0,
                    quota_remaining=tier_quota,
                    reset_date=datetime.utcnow() + timedelta(days=30)
                )
                session.add(quota)
                session.commit()
            
            # Calculate current usage from database
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            total_used = session.query(func.sum(TokenUsage.token_count)).filter(
                TokenUsage.user_id == user_id,
                TokenUsage.created_at >= current_month_start
            ).scalar() or 0
            
            # Update quota with actual usage
            quota.quota_used = total_used
            quota.quota_remaining = quota.quota_limit - total_used
            session.commit()
            
            remaining = quota.quota_remaining
        can_proceed = remaining >= token_count
        
        return {
            "can_proceed": can_proceed,
            "quota_limit": quota.quota_limit,
            "quota_remaining": remaining,
            "quota_used": quota.quota_used,
            "message": "Sufficient quota" if can_proceed else "Insufficient quota",
            "requested_tokens": token_count
        }
    
    async def set_user_quota(self, user_id: str, quota_limit: int) -> None:
        """
        Set quota limit for a user.
        
        Args:
            user_id: User ID
            quota_limit: New quota limit
        """
        self.user_quotas[user_id] = {"limit": quota_limit, "updated_at": datetime.utcnow()}
        self.logger.info(f"Set quota limit for user {user_id}: {quota_limit} tokens")
    
    def _calculate_cost(self, token_type: TokenType, token_count: int, model_name: Optional[str] = None) -> float:
        """
        Calculate cost for token usage.
        
        Args:
            token_type: Type of tokens
            token_count: Number of tokens
            model_name: AI model used
            
        Returns:
            Cost in USD
        """
        base_rate = self.pricing.get(token_type, 0.001)
        
        # Apply model-specific pricing adjustments
        if model_name:
            if "gpt-4" in model_name.lower():
                base_rate *= 20  # GPT-4 is more expensive
            elif "gpt-3.5" in model_name.lower():
                base_rate *= 1  # Base rate
        
        # Calculate cost per 1k tokens
        cost = (token_count / 1000) * base_rate
        return round(cost, 6)
    
    async def get_cost_optimization_suggestions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get cost optimization suggestions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of optimization suggestions
        """
        usage_summary = await self.get_usage_summary(user_id)
        suggestions = []
        
        # Analyze usage patterns
        breakdown = usage_summary.get("breakdown", {})
        
        if breakdown.get("input", {}).get("tokens", 0) > 10000:
            suggestions.append({
                "type": "model_optimization",
                "message": "Consider using GPT-3.5-turbo for simpler queries to reduce costs",
                "potential_savings": "Up to 95% cost reduction"
            })
        
        if breakdown.get("embedding", {}).get("count", 0) > 1000:
            suggestions.append({
                "type": "caching",
                "message": "Enable embedding caching to avoid reprocessing similar content",
                "potential_savings": "30-50% embedding cost reduction"
            })
        
        return suggestions
