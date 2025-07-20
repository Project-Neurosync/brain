"""
NeuroSync AI Backend - Admin API Routes
Administrative endpoints for system management and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.database import User, Project
from models.payment_models import Subscription
from models.payment_models import Payment, TokenPurchase, Invoice
from core.token_models import TokenUsage
from core.auth import AuthManager
from services.database_service import DatabaseService
from config.settings import get_settings

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
security = HTTPBearer()
settings = get_settings()

# Admin role check dependency
async def verify_admin_access(credentials = Depends(security)):
    """Verify admin access - only founders can access admin endpoints"""
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # For now, check against admin tokens in environment
        # In production, implement proper admin role system
        admin_tokens = settings.admin_tokens.split(',') if hasattr(settings, 'admin_tokens') else []
        
        if token not in admin_tokens:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return {"role": "admin", "token": token}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )

@router.post("/login")
async def admin_login(request: dict):
    """Admin login endpoint - validates admin token"""
    try:
        token = request.get('token')
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is required"
            )
        
        # Check against admin tokens in environment
        admin_tokens = settings.admin_tokens.split(',') if settings.admin_tokens else []
        
        if token not in admin_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin token"
            )
        
        return {
            "success": True,
            "message": "Admin authentication successful",
            "token": token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    admin_user = Depends(verify_admin_access),
    db_service: DatabaseService = Depends()
):
    """Get comprehensive dashboard statistics"""
    try:
        with db_service.get_db_session() as db:
            # User statistics
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            new_users_this_month = db.query(User).filter(
                User.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
            
            # Subscription statistics
            total_subscriptions = db.query(Subscription).filter(
                Subscription.status == 'active'
            ).count()
            
            subscription_breakdown = db.query(
                Subscription.plan,
                func.count(Subscription.id).label('count')
            ).filter(
                Subscription.status == 'active'
            ).group_by(Subscription.plan).all()
            
            # Revenue statistics
            total_revenue = db.query(func.sum(Payment.amount)).filter(
                Payment.status == 'succeeded'
            ).scalar() or 0
            
            monthly_revenue = db.query(func.sum(Payment.amount)).filter(
                Payment.status == 'succeeded',
                Payment.created_at >= datetime.utcnow() - timedelta(days=30)
            ).scalar() or 0
            
            # Token usage statistics
            total_tokens_used = db.query(func.sum(TokenUsage.token_count)).scalar() or 0
            monthly_tokens_used = db.query(func.sum(TokenUsage.token_count)).filter(
                TokenUsage.created_at >= datetime.utcnow() - timedelta(days=30)
            ).scalar() or 0
            
            # Project statistics
            total_projects = db.query(Project).count()
            active_projects = db.query(Project).filter(
                Project.is_active == True
            ).count()
            
            return {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "new_this_month": new_users_this_month,
                    "growth_rate": round((new_users_this_month / max(total_users - new_users_this_month, 1)) * 100, 2)
                },
                "subscriptions": {
                    "total": total_subscriptions,
                    "breakdown": {plan: count for plan, count in subscription_breakdown}
                },
                "revenue": {
                    "total": round(total_revenue, 2),
                    "monthly": round(monthly_revenue, 2),
                    "arr": round(monthly_revenue * 12, 2)
                },
                "tokens": {
                    "total_used": total_tokens_used,
                    "monthly_used": monthly_tokens_used,
                    "avg_per_user": round(monthly_tokens_used / max(active_users, 1), 2)
                },
                "projects": {
                    "total": total_projects,
                    "active": active_projects
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )

@router.get("/users")
async def get_users(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    admin_user = Depends(verify_admin_access),
    db_service: DatabaseService = Depends()
):
    """Get paginated list of users with search"""
    try:
        with db_service.get_db_session() as db:
            query = db.query(User)
            
            if search:
                query = query.filter(User.email.ilike(f"%{search}%"))
            
            total = query.count()
            users = query.offset((page - 1) * limit).limit(limit).all()
            
            user_list = []
            for user in users:
                # Get user's subscription
                subscription = db.query(Subscription).filter(
                    Subscription.user_id == user.id,
                    Subscription.status == 'active'
                ).first()
                
                # Get user's token usage this month
                monthly_usage = db.query(func.sum(TokenUsage.token_count)).filter(
                    TokenUsage.user_id == user.id,
                    TokenUsage.created_at >= datetime.utcnow() - timedelta(days=30)
                ).scalar() or 0
                
                user_list.append({
                    "id": str(user.id),
                    "email": user.email,
                    "subscription_tier": user.subscription_tier,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                    "monthly_token_quota": user.monthly_token_quota,
                    "tokens_used_this_month": monthly_usage,
                    "bonus_tokens": user.bonus_tokens or 0,
                    "subscription_status": subscription.status if subscription else "none"
                })
            
            return {
                "users": user_list,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/revenue-analytics")
async def get_revenue_analytics(
    days: int = 30,
    admin_user = Depends(verify_admin_access),
    db_service: DatabaseService = Depends()
):
    """Get detailed revenue analytics"""
    try:
        with db_service.get_db_session() as db:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily revenue breakdown
            daily_revenue = db.query(
                func.date(Payment.created_at).label('date'),
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('transactions')
            ).filter(
                Payment.status == 'succeeded',
                Payment.created_at >= start_date
            ).group_by(func.date(Payment.created_at)).order_by('date').all()
            
            # Revenue by payment type
            revenue_by_type = db.query(
                Payment.payment_type,
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('count')
            ).filter(
                Payment.status == 'succeeded',
                Payment.created_at >= start_date
            ).group_by(Payment.payment_type).all()
            
            # Token pack sales
            token_pack_sales = db.query(
                TokenPurchase.pack,
                func.sum(TokenPurchase.amount).label('revenue'),
                func.sum(TokenPurchase.tokens).label('tokens_sold'),
                func.count(TokenPurchase.id).label('purchases')
            ).filter(
                TokenPurchase.created_at >= start_date
            ).group_by(TokenPurchase.pack).all()
            
            return {
                "period_days": days,
                "daily_revenue": [
                    {
                        "date": date.isoformat(),
                        "revenue": float(revenue),
                        "transactions": transactions
                    }
                    for date, revenue, transactions in daily_revenue
                ],
                "revenue_by_type": [
                    {
                        "type": payment_type,
                        "revenue": float(revenue),
                        "count": count
                    }
                    for payment_type, revenue, count in revenue_by_type
                ],
                "token_pack_sales": [
                    {
                        "pack": pack,
                        "revenue": float(revenue),
                        "tokens_sold": tokens_sold,
                        "purchases": purchases
                    }
                    for pack, revenue, tokens_sold, purchases in token_pack_sales
                ]
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch revenue analytics: {str(e)}"
        )

@router.get("/system-health")
async def get_system_health(
    admin_user = Depends(verify_admin_access),
    db_service: DatabaseService = Depends()
):
    """Get system health and performance metrics"""
    try:
        with db_service.get_db_session() as db:
            # Database health
            db_health = True
            try:
                db.execute("SELECT 1")
            except:
                db_health = False
            
            # Recent errors (if we had error logging)
            recent_errors = []  # Placeholder for error tracking
            
            # Token usage trends
            daily_token_usage = db.query(
                func.date(TokenUsage.created_at).label('date'),
                func.sum(TokenUsage.token_count).label('tokens'),
                func.count(TokenUsage.id).label('queries')
            ).filter(
                TokenUsage.created_at >= datetime.utcnow() - timedelta(days=7)
            ).group_by(func.date(TokenUsage.created_at)).order_by('date').all()
            
            # Cost analysis
            total_cost = db.query(func.sum(TokenUsage.cost_usd)).scalar() or 0
            monthly_cost = db.query(func.sum(TokenUsage.cost_usd)).filter(
                TokenUsage.created_at >= datetime.utcnow() - timedelta(days=30)
            ).scalar() or 0
            
            return {
                "database_health": db_health,
                "recent_errors": recent_errors,
                "token_usage_trend": [
                    {
                        "date": date.isoformat(),
                        "tokens": tokens,
                        "queries": queries
                    }
                    for date, tokens, queries in daily_token_usage
                ],
                "cost_analysis": {
                    "total_cost": round(total_cost, 4),
                    "monthly_cost": round(monthly_cost, 4),
                    "projected_monthly": round(monthly_cost * 30 / min(30, (datetime.utcnow().day)), 4)
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch system health: {str(e)}"
        )

@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    admin_user = Depends(verify_admin_access),
    db_service: DatabaseService = Depends()
):
    """Toggle user active/inactive status"""
    try:
        with db_service.get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user.is_active = not user.is_active
            db.commit()
            
            return {
                "user_id": user_id,
                "is_active": user.is_active,
                "message": f"User {'activated' if user.is_active else 'deactivated'}"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle user status: {str(e)}"
        )

@router.post("/users/{user_id}/add-tokens")
async def add_tokens_to_user(
    user_id: str,
    tokens: int,
    reason: str = "Admin grant",
    admin_user = Depends(verify_admin_access),
    db_service: DatabaseService = Depends()
):
    """Add bonus tokens to a user account"""
    try:
        with db_service.get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user.bonus_tokens = (user.bonus_tokens or 0) + tokens
            db.commit()
            
            return {
                "user_id": user_id,
                "tokens_added": tokens,
                "new_bonus_balance": user.bonus_tokens,
                "reason": reason
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add tokens: {str(e)}"
        )
