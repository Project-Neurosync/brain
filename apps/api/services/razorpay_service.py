"""
NeuroSync AI Backend - Razorpay Payment Service
Razorpay integration for subscriptions and token purchases
"""

import razorpay
import logging
import hmac
import hashlib
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config.settings import get_settings
from models.database import User, Subscription, Payment, TokenPurchase
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class RazorpayService:
    """Razorpay payment processing service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_service = DatabaseService()
        
        # Initialize Razorpay client
        self.client = razorpay.Client(auth=(self.settings.razorpay_key_id, self.settings.razorpay_key_secret))
        self.webhook_secret = self.settings.razorpay_webhook_secret
        
        # Subscription plans mapping (amounts in paise for Razorpay)
        self.subscription_plans = {
            "starter": {
                "amount": 1900,  # ₹19 in paise
                "tokens": 200,
                "price": 19.00,
                "name": "Starter",
                "currency": "INR"
            },
            "professional": {
                "amount": 2900,  # ₹29 in paise
                "tokens": 400,
                "price": 29.00,
                "name": "Professional",
                "currency": "INR"
            },
            "enterprise": {
                "amount": 4900,  # ₹49 in paise
                "tokens": 800,
                "price": 49.00,
                "name": "Enterprise",
                "currency": "INR"
            }
        }
        
        # Token pack pricing (amounts in paise)
        self.token_packs = {
            "small": {"amount": 500, "tokens": 100, "name": "Small Pack"},
            "medium": {"amount": 1200, "tokens": 250, "name": "Medium Pack"},
            "large": {"amount": 2000, "tokens": 500, "name": "Large Pack"},
            "enterprise": {"amount": 3500, "tokens": 1000, "name": "Enterprise Pack"}
        }

    async def create_order_for_signup(self, user_data: Dict[str, Any], subscription_tier: str) -> Dict[str, Any]:
        """
        Create a Razorpay order for user signup with subscription
        
        Args:
            user_data: Dictionary containing user registration data (name, email, password)
            subscription_tier: The subscription tier (starter, professional, enterprise)
            
        Returns:
            Dictionary containing order details and user data for frontend
        """
        try:
            if subscription_tier not in self.subscription_plans:
                raise ValueError(f"Invalid subscription tier: {subscription_tier}")
            
            plan = self.subscription_plans[subscription_tier]
            
            # Create order data
            order_data = {
                "amount": plan["amount"],
                "currency": plan["currency"],
                "receipt": f"signup_{uuid.uuid4().hex[:8]}",
                "notes": {
                    "user_name": user_data["name"],
                    "user_email": user_data["email"],
                    "subscription_tier": subscription_tier,
                    "signup_order": "true"
                }
            }
            
            # Create order with Razorpay
            order = self.client.order.create(data=order_data)
            
            logger.info(f"Created Razorpay order for signup: {order['id']} for {user_data['email']}")
            
            return {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "key": self.settings.razorpay_key_id,
                "user_data": user_data,  # Store temporarily for post-payment registration
                "subscription_tier": subscription_tier,
                "plan_name": plan["name"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create signup order: {str(e)}")
            raise Exception(f"Payment setup failed: {str(e)}")

    async def verify_payment_signature(self, payment_data: Dict[str, str]) -> bool:
        """
        Verify Razorpay payment signature
        
        Args:
            payment_data: Dictionary containing razorpay_order_id, razorpay_payment_id, razorpay_signature
            
        Returns:
            Boolean indicating if signature is valid
        """
        try:
            # Generate expected signature
            message = f"{payment_data['razorpay_order_id']}|{payment_data['razorpay_payment_id']}"
            expected_signature = hmac.new(
                self.settings.razorpay_key_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, payment_data['razorpay_signature'])
            
        except Exception as e:
            logger.error(f"Payment signature verification failed: {str(e)}")
            return False

    async def process_successful_signup_payment(self, payment_data: Dict[str, str], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process successful payment and register user
        
        Args:
            payment_data: Razorpay payment details
            user_data: User registration data
            
        Returns:
            User registration result with tokens
        """
        try:
            # Verify payment signature first
            if not await self.verify_payment_signature(payment_data):
                raise Exception("Invalid payment signature")
            
            # Get order details from Razorpay
            order = self.client.order.fetch(payment_data['razorpay_order_id'])
            subscription_tier = order['notes']['subscription_tier']
            
            # Import auth manager here to avoid circular imports
            from core.auth import AuthManager
            
            # Register user in database
            auth_manager = AuthManager(db_service=self.db_service)
            registration_result = await auth_manager.register_user(
                email=user_data['email'],
                password=user_data['password'],
                name=user_data['name'],
                subscription_tier=subscription_tier
            )
            
            # Record payment in database
            await self.record_payment(
                user_id=registration_result['user_id'],
                payment_id=payment_data['razorpay_payment_id'],
                order_id=payment_data['razorpay_order_id'],
                amount=order['amount'] / 100,  # Convert paise to rupees
                subscription_tier=subscription_tier,
                payment_type='subscription'
            )
            
            logger.info(f"Successfully processed signup payment for user: {user_data['email']}")
            
            return registration_result
            
        except Exception as e:
            logger.error(f"Failed to process signup payment: {str(e)}")
            raise Exception(f"Payment processing failed: {str(e)}")

    async def record_payment(self, user_id: str, payment_id: str, order_id: str, 
                           amount: float, subscription_tier: str, payment_type: str) -> None:
        """
        Record payment in database
        
        Args:
            user_id: User ID
            payment_id: Razorpay payment ID
            order_id: Razorpay order ID
            amount: Payment amount in rupees
            subscription_tier: Subscription tier
            payment_type: Type of payment (subscription, token_pack)
        """
        try:
            with self.db_service.get_db_session() as db:
                # Create payment record
                payment = Payment(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(user_id),
                    amount=amount,
                    currency="INR",
                    status="completed",
                    payment_method="razorpay",
                    transaction_id=payment_id,
                    metadata={
                        "order_id": order_id,
                        "subscription_tier": subscription_tier,
                        "payment_type": payment_type
                    }
                )
                
                db.add(payment)
                
                # Create subscription record if it's a subscription payment
                if payment_type == "subscription":
                    subscription = Subscription(
                        id=uuid.uuid4(),
                        user_id=uuid.UUID(user_id),
                        tier=subscription_tier,
                        status="active",
                        started_at=datetime.utcnow(),
                        ends_at=datetime.utcnow() + timedelta(days=30),  # Monthly subscription
                        auto_renew=True
                    )
                    db.add(subscription)
                
                db.commit()
                logger.info(f"Recorded payment: {payment_id} for user: {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to record payment: {str(e)}")
            raise

    async def create_token_pack_order(self, user_id: str, pack_type: str) -> Dict[str, Any]:
        """
        Create order for token pack purchase
        
        Args:
            user_id: User ID
            pack_type: Token pack type (small, medium, large, enterprise)
            
        Returns:
            Order details for frontend
        """
        try:
            if pack_type not in self.token_packs:
                raise ValueError(f"Invalid token pack type: {pack_type}")
            
            pack = self.token_packs[pack_type]
            
            # Get user details
            with self.db_service.get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise Exception("User not found")
            
            # Create order data
            order_data = {
                "amount": pack["amount"],
                "currency": "INR",
                "receipt": f"tokens_{uuid.uuid4().hex[:8]}",
                "notes": {
                    "user_id": user_id,
                    "user_email": user.email,
                    "pack_type": pack_type,
                    "tokens": str(pack["tokens"]),
                    "token_purchase": "true"
                }
            }
            
            # Create order with Razorpay
            order = self.client.order.create(data=order_data)
            
            logger.info(f"Created token pack order: {order['id']} for user: {user_id}")
            
            return {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "key": self.settings.razorpay_key_id,
                "pack_name": pack["name"],
                "tokens": pack["tokens"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create token pack order: {str(e)}")
            raise Exception(f"Token pack order creation failed: {str(e)}")

    async def process_token_pack_payment(self, payment_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Process successful token pack payment
        
        Args:
            payment_data: Razorpay payment details
            
        Returns:
            Payment processing result
        """
        try:
            # Verify payment signature
            if not await self.verify_payment_signature(payment_data):
                raise Exception("Invalid payment signature")
            
            # Get order details
            order = self.client.order.fetch(payment_data['razorpay_order_id'])
            user_id = order['notes']['user_id']
            pack_type = order['notes']['pack_type']
            tokens_to_add = int(order['notes']['tokens'])
            
            # Add tokens to user account
            with self.db_service.get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise Exception("User not found")
                
                # Add bonus tokens
                user.bonus_tokens = (user.bonus_tokens or 0) + tokens_to_add
                
                db.commit()
            
            # Record payment
            await self.record_payment(
                user_id=user_id,
                payment_id=payment_data['razorpay_payment_id'],
                order_id=payment_data['razorpay_order_id'],
                amount=order['amount'] / 100,  # Convert paise to rupees
                subscription_tier="",
                payment_type='token_pack'
            )
            
            logger.info(f"Successfully processed token pack payment for user: {user_id}")
            
            return {
                "success": True,
                "tokens_added": tokens_to_add,
                "pack_type": pack_type
            }
            
        except Exception as e:
            logger.error(f"Failed to process token pack payment: {str(e)}")
            raise Exception(f"Token pack payment processing failed: {str(e)}")

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Razorpay webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature from headers
            
        Returns:
            Boolean indicating if signature is valid
        """
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False

# Global Razorpay service instance
razorpay_service = RazorpayService()
