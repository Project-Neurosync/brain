"""
NeuroSync AI Backend - Payment Service
Stripe integration for subscriptions and token purchases
"""

import stripe
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config.settings import get_settings
from models.database import User, Subscription, Payment, TokenPurchase
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class PaymentService:
    """Stripe payment processing service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_service = DatabaseService()
        
        # Initialize Stripe
        stripe.api_key = self.settings.stripe_secret_key
        self.webhook_secret = self.settings.stripe_webhook_secret
        
        # Subscription plans mapping
        self.subscription_plans = {
            "starter": {
                "price_id": self.settings.stripe_starter_price_id,
                "tokens": 200,
                "price": 19.00,
                "name": "Starter"
            },
            "professional": {
                "price_id": self.settings.stripe_professional_price_id,
                "tokens": 400,
                "price": 29.00,
                "name": "Professional"
            },
            "enterprise": {
                "price_id": self.settings.stripe_enterprise_price_id,
                "tokens": 800,
                "price": 49.00,
                "name": "Enterprise"
            }
        }
        
        # Token pack options
        self.token_packs = {
            "small": {"tokens": 100, "price": 5.00, "price_id": self.settings.stripe_small_pack_price_id},
            "medium": {"tokens": 500, "price": 20.00, "price_id": self.settings.stripe_medium_pack_price_id},
            "large": {"tokens": 1000, "price": 35.00, "price_id": self.settings.stripe_large_pack_price_id},
            "enterprise": {"tokens": 5000, "price": 150.00, "price_id": self.settings.stripe_enterprise_pack_price_id}
        }
    
    async def create_customer(self, user_id: str, email: str, name: str = None) -> str:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"user_id": user_id}
            )
            
            # Update user with Stripe customer ID
            async with self.db_service.get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.stripe_customer_id = customer.id
                    session.commit()
            
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise Exception(f"Payment processing error: {e}")
    
    async def create_subscription_checkout(self, user_id: str, plan: str, success_url: str, cancel_url: str) -> str:
        """Create a Stripe checkout session for subscription"""
        try:
            if plan not in self.subscription_plans:
                raise ValueError(f"Invalid subscription plan: {plan}")
            
            # Get or create customer
            async with self.db_service.get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError("User not found")
                
                customer_id = user.stripe_customer_id
                if not customer_id:
                    customer_id = await self.create_customer(user_id, user.email, user.name)
            
            plan_info = self.subscription_plans[plan]
            
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan_info['price_id'],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'plan': plan
                }
            )
            
            logger.info(f"Created subscription checkout for user {user_id}, plan {plan}")
            return checkout_session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription checkout: {e}")
            raise Exception(f"Payment processing error: {e}")
    
    async def create_token_purchase_checkout(self, user_id: str, pack: str, success_url: str, cancel_url: str) -> str:
        """Create a Stripe checkout session for token purchase"""
        try:
            if pack not in self.token_packs:
                raise ValueError(f"Invalid token pack: {pack}")
            
            # Get or create customer
            async with self.db_service.get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError("User not found")
                
                customer_id = user.stripe_customer_id
                if not customer_id:
                    customer_id = await self.create_customer(user_id, user.email, user.name)
            
            pack_info = self.token_packs[pack]
            
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': pack_info['price_id'],
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'pack': pack,
                    'tokens': pack_info['tokens']
                }
            )
            
            logger.info(f"Created token purchase checkout for user {user_id}, pack {pack}")
            return checkout_session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create token purchase checkout: {e}")
            raise Exception(f"Payment processing error: {e}")
    
    async def handle_subscription_created(self, subscription_data: Dict[str, Any]) -> bool:
        """Handle successful subscription creation"""
        try:
            customer_id = subscription_data['customer']
            subscription_id = subscription_data['id']
            
            # Get user by customer ID
            async with self.db_service.get_db_session() as session:
                user = session.query(User).filter(User.stripe_customer_id == customer_id).first()
                if not user:
                    logger.error(f"User not found for customer {customer_id}")
                    return False
                
                # Determine plan from subscription
                price_id = subscription_data['items']['data'][0]['price']['id']
                plan = None
                for plan_name, plan_info in self.subscription_plans.items():
                    if plan_info['price_id'] == price_id:
                        plan = plan_name
                        break
                
                if not plan:
                    logger.error(f"Unknown price ID: {price_id}")
                    return False
                
                # Create or update subscription
                existing_subscription = session.query(Subscription).filter(
                    Subscription.user_id == user.id,
                    Subscription.status == 'active'
                ).first()
                
                if existing_subscription:
                    # Cancel existing subscription
                    existing_subscription.status = 'cancelled'
                    existing_subscription.cancelled_at = datetime.utcnow()
                
                # Create new subscription
                new_subscription = Subscription(
                    user_id=user.id,
                    stripe_subscription_id=subscription_id,
                    plan=plan,
                    status='active',
                    current_period_start=datetime.fromtimestamp(subscription_data['current_period_start']),
                    current_period_end=datetime.fromtimestamp(subscription_data['current_period_end'])
                )
                
                session.add(new_subscription)
                
                # Update user subscription tier
                user.subscription_tier = plan
                
                # Reset monthly token quota
                plan_info = self.subscription_plans[plan]
                user.monthly_token_quota = plan_info['tokens']
                user.tokens_used_this_month = 0
                
                session.commit()
                
                logger.info(f"Created subscription for user {user.id}, plan {plan}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to handle subscription creation: {e}")
            return False
    
    async def handle_payment_succeeded(self, payment_data: Dict[str, Any]) -> bool:
        """Handle successful one-time payment (token purchase)"""
        try:
            customer_id = payment_data['customer']
            session_id = payment_data['id']
            
            # Get checkout session to retrieve metadata
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            metadata = checkout_session.metadata
            
            if 'pack' not in metadata:
                # This is a subscription payment, not a token purchase
                return True
            
            user_id = metadata['user_id']
            pack = metadata['pack']
            tokens = int(metadata['tokens'])
            
            # Add tokens to user account
            async with self.db_service.get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    logger.error(f"User not found: {user_id}")
                    return False
                
                # Add tokens to user's balance
                user.bonus_tokens = (user.bonus_tokens or 0) + tokens
                
                # Record the purchase
                purchase = TokenPurchase(
                    user_id=user_id,
                    stripe_payment_id=session_id,
                    pack=pack,
                    tokens=tokens,
                    amount=self.token_packs[pack]['price']
                )
                
                session.add(purchase)
                session.commit()
                
                logger.info(f"Added {tokens} tokens to user {user_id} from {pack} pack")
                return True
                
        except Exception as e:
            logger.error(f"Failed to handle payment success: {e}")
            return False
    
    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel user's subscription"""
        try:
            async with self.db_service.get_db_session() as session:
                subscription = session.query(Subscription).filter(
                    Subscription.user_id == user_id,
                    Subscription.status == 'active'
                ).first()
                
                if not subscription:
                    return False
                
                # Cancel in Stripe
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                
                # Update in database
                subscription.status = 'cancelled'
                subscription.cancelled_at = datetime.utcnow()
                
                # Update user
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.subscription_tier = 'free'
                
                session.commit()
                
                logger.info(f"Cancelled subscription for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return True
        except (ValueError, stripe.error.SignatureVerificationError):
            return False

# Global payment service instance
payment_service = PaymentService()
