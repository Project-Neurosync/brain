"""
NeuroSync AI Backend - Payment Routes
API endpoints for Stripe payment processing
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Dict, Any
import logging
import json

from core.auth import get_current_user
from services.payment_service import payment_service
from models.database import User

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Request models
class CreateSubscriptionRequest(BaseModel):
    plan: str  # starter, professional, enterprise
    success_url: str
    cancel_url: str

class CreateTokenPurchaseRequest(BaseModel):
    pack: str  # small, medium, large, enterprise
    success_url: str
    cancel_url: str

class CancelSubscriptionRequest(BaseModel):
    pass

# Response models
class CheckoutResponse(BaseModel):
    checkout_url: str
    success: bool
    message: str

class SubscriptionStatusResponse(BaseModel):
    has_subscription: bool
    plan: str = None
    status: str = None
    current_period_end: str = None
    tokens_remaining: int = 0
    bonus_tokens: int = 0

@router.post("/create-subscription-checkout", response_model=CheckoutResponse)
async def create_subscription_checkout(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session for subscription"""
    try:
        checkout_url = await payment_service.create_subscription_checkout(
            user_id=current_user.id,
            plan=request.plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        return CheckoutResponse(
            checkout_url=checkout_url,
            success=True,
            message="Checkout session created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create subscription checkout: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.post("/create-token-purchase-checkout", response_model=CheckoutResponse)
async def create_token_purchase_checkout(
    request: CreateTokenPurchaseRequest,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session for token purchase"""
    try:
        checkout_url = await payment_service.create_token_purchase_checkout(
            user_id=current_user.id,
            pack=request.pack,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        return CheckoutResponse(
            checkout_url=checkout_url,
            success=True,
            message="Checkout session created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create token purchase checkout: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.get("/subscription-status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Get user's current subscription status"""
    try:
        # This would typically query the database for subscription info
        # For now, return basic info from user object
        
        has_subscription = current_user.subscription_tier != 'free'
        
        # Calculate tokens remaining this month
        monthly_quota = current_user.monthly_token_quota or 0
        tokens_used = current_user.tokens_used_this_month or 0
        tokens_remaining = max(0, monthly_quota - tokens_used)
        
        return SubscriptionStatusResponse(
            has_subscription=has_subscription,
            plan=current_user.subscription_tier if has_subscription else None,
            status="active" if has_subscription else "inactive",
            tokens_remaining=tokens_remaining,
            bonus_tokens=current_user.bonus_tokens or 0
        )
        
    except Exception as e:
        logger.error(f"Failed to get subscription status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")

@router.post("/cancel-subscription")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Cancel user's subscription"""
    try:
        success = await payment_service.cancel_subscription(current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        return {"success": True, "message": "Subscription cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price": 19.00,
                "tokens": 200,
                "features": [
                    "200 AI tokens/month",
                    "Basic project management",
                    "Email support"
                ]
            },
            {
                "id": "professional",
                "name": "Professional", 
                "price": 29.00,
                "tokens": 400,
                "features": [
                    "400 AI tokens/month",
                    "Advanced project features",
                    "Priority support",
                    "Team collaboration"
                ]
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 49.00,
                "tokens": 800,
                "features": [
                    "800 AI tokens/month",
                    "All features included",
                    "24/7 phone support",
                    "Custom integrations",
                    "SSO support"
                ]
            }
        ]
    }

@router.get("/token-packs")
async def get_token_packs():
    """Get available token packs for purchase"""
    return {
        "packs": [
            {
                "id": "small",
                "name": "Small Pack",
                "tokens": 100,
                "price": 5.00,
                "savings": "Best for trying out"
            },
            {
                "id": "medium", 
                "name": "Medium Pack",
                "tokens": 500,
                "price": 20.00,
                "savings": "Most popular"
            },
            {
                "id": "large",
                "name": "Large Pack",
                "tokens": 1000,
                "price": 35.00,
                "savings": "Save 30%"
            },
            {
                "id": "enterprise",
                "name": "Enterprise Pack",
                "tokens": 5000,
                "price": 150.00,
                "savings": "Best value - Save 40%"
            }
        ]
    }

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Verify webhook signature
        if not payment_service.verify_webhook_signature(payload, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        # Parse event
        event = json.loads(payload)
        event_type = event['type']
        
        logger.info(f"Received Stripe webhook: {event_type}")
        
        # Handle different event types
        if event_type == 'customer.subscription.created':
            await payment_service.handle_subscription_created(event['data']['object'])
        
        elif event_type == 'customer.subscription.updated':
            await payment_service.handle_subscription_created(event['data']['object'])
        
        elif event_type == 'checkout.session.completed':
            await payment_service.handle_payment_succeeded(event['data']['object'])
        
        elif event_type == 'customer.subscription.deleted':
            # Handle subscription cancellation
            subscription_data = event['data']['object']
            customer_id = subscription_data['customer']
            # Update user subscription status to cancelled
            logger.info(f"Subscription cancelled for customer {customer_id}")
        
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
        
        return {"success": True}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.get("/config")
async def get_payment_config():
    """Get public payment configuration (publishable key, etc.)"""
    from config.settings import get_settings
    settings = get_settings()
    
    return {
        "stripe_publishable_key": settings.stripe_publishable_key,
        "currency": "usd",
        "country": "US"
    }
