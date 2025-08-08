"""
Marketing schemas for NeuroSync API
Contains schemas for contact forms, demo scheduling, pricing tiers
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class ContactRequest(BaseModel):
    """Contact form submission data"""
    name: str = Field(..., description="Full name of the contact")
    email: EmailStr = Field(..., description="Email address of the contact")
    company: Optional[str] = Field(None, description="Company name (optional)")
    message: str = Field(..., description="Contact message content")
    phone: Optional[str] = Field(None, description="Phone number (optional)")
    marketing_consent: bool = Field(False, description="Marketing communication consent")

class DemoRequest(BaseModel):
    """Demo scheduling request data"""
    name: str = Field(..., description="Full name of the requester")
    email: EmailStr = Field(..., description="Email address for demo communication")
    company: str = Field(..., description="Company name")
    role: str = Field(..., description="Job role/title")
    team_size: Optional[int] = Field(None, description="Team size (optional)")
    preferred_date: Optional[datetime] = Field(None, description="Preferred demo date/time")
    questions: Optional[str] = Field(None, description="Any questions or requirements")

class PricingTier(BaseModel):
    """Pricing tier information"""
    name: str = Field(..., description="Tier name (e.g., 'Starter', 'Pro', 'Enterprise')")
    price: float = Field(..., description="Monthly price in USD")
    description: str = Field(..., description="Short tier description")
    features: List[str] = Field(..., description="List of features included in this tier")
    is_popular: bool = Field(False, description="Whether this is the recommended/popular tier")
    billing_cycle: str = Field("monthly", description="Billing cycle (monthly/annual)")

class PricingResponse(BaseModel):
    """Pricing tiers response"""
    tiers: List[PricingTier] = Field(..., description="Available pricing tiers")
    currency: str = Field("USD", description="Currency for pricing")
    
class Testimonial(BaseModel):
    """Customer testimonial"""
    name: str = Field(..., description="Customer name")
    company: str = Field(..., description="Customer company")
    role: str = Field(..., description="Customer role/title")
    quote: str = Field(..., description="Testimonial quote")
    rating: int = Field(..., description="Rating (1-5)")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")

class Feature(BaseModel):
    """Product feature"""
    title: str = Field(..., description="Feature title")
    description: str = Field(..., description="Feature description")
    icon: Optional[str] = Field(None, description="Feature icon identifier")
    benefits: List[str] = Field(..., description="List of benefits")
    
class MarketingResponse(BaseModel):
    """Generic marketing API response"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
