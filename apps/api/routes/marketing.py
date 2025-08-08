"""
Marketing routes for NeuroSync API
Handles landing page functionality like contact form and demo scheduling
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from models.database import get_db
from schemas.marketing import ContactRequest, DemoRequest, MarketingResponse, PricingResponse

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/marketing", tags=["marketing"])

@router.post("/contact", response_model=MarketingResponse)
async def submit_contact_form(
    contact: ContactRequest, 
    db: Session = Depends(get_db)
):
    """
    Submit contact form from landing page
    """
    # Log the contact request
    logger.info(f"Contact request received from {contact.email}")
    
    # TODO: Store contact in database
    # TODO: Send email notification
    
    # Return success response
    return {
        "success": True,
        "message": "Thank you for your message! We'll be in touch soon."
    }

@router.post("/schedule-demo", response_model=MarketingResponse)
async def schedule_demo(
    demo_request: DemoRequest, 
    db: Session = Depends(get_db)
):
    """
    Schedule a demo from landing page
    """
    # Log the demo request
    logger.info(f"Demo request received from {demo_request.email}")
    
    # Generate a unique reference number
    reference = f"DEMO-{datetime.now().strftime('%Y%m%d%H%M')}"
    
    # TODO: Store demo request in database
    # TODO: Integration with scheduling system
    # TODO: Send confirmation email
    
    return {
        "success": True,
        "message": f"Your demo has been scheduled successfully! Reference number: {reference}"
    }

@router.get("/pricing", response_model=PricingResponse)
async def get_pricing_tiers():
    """
    Get pricing tiers for the landing page
    """
    # TODO: Fetch pricing tiers from database
    
    pricing_tiers = {
        "tiers": [
            {
                "name": "Basic",
                "price": 29,
                "features": [
                    "5,000 tokens per month",
                    "Basic AI chat",
                    "Document analysis",
                    "Email support"
                ],
                "popular": False
            },
            {
                "name": "Pro",
                "price": 99,
                "features": [
                    "50,000 tokens per month",
                    "Advanced AI chat",
                    "Document analysis",
                    "GitHub integration",
                    "Priority email support"
                ],
                "popular": True
            },
            {
                "name": "Enterprise",
                "price": 299,
                "features": [
                    "200,000 tokens per month",
                    "Advanced AI chat",
                    "Document analysis",
                    "GitHub integration",
                    "Jira integration",
                    "Slack integration",
                    "Dedicated support"
                ],
                "popular": False
            }
        ]
    }
    
    return pricing_tiers

@router.get("/testimonials")
async def get_testimonials():
    """Get customer testimonials"""
    
    # Return hardcoded testimonials
    # In a real app, these would come from a database
    
    return {
        "testimonials": [
            {
                "id": 1,
                "name": "Sarah Johnson",
                "company": "TechInnovate",
                "role": "CTO",
                "quote": "NeuroSync has transformed our development process. Knowledge transfer between teams is seamless now.",
                "rating": 5
            },
            {
                "id": 2,
                "name": "Michael Chen",
                "company": "CodeNinja",
                "role": "Lead Developer",
                "quote": "The AI assistant has saved us countless hours onboarding new developers.",
                "rating": 5
            },
            {
                "id": 3,
                "name": "Jessica Williams",
                "company": "Startup Accelerator",
                "role": "Product Manager",
                "quote": "Our documentation and knowledge management improved significantly after implementing NeuroSync.",
                "rating": 4
            }
        ]
    }

@router.get("/features")
async def get_features():
    """Get product features"""
    
    # Return hardcoded features
    # In a real app, these would come from a database
    
    return {
        "features": [
            {
                "id": "knowledge-transfer",
                "name": "AI Knowledge Transfer",
                "description": "Automatically extract knowledge from documentation, code, and team communications.",
                "icon": "brain"
            },
            {
                "id": "code-insights",
                "name": "Code Insights",
                "description": "Get AI-powered suggestions and insights directly in your IDE.",
                "icon": "code"
            },
            {
                "id": "context-search",
                "name": "Context-aware Search",
                "description": "Find information across your codebase with semantic search capabilities.",
                "icon": "search"
            },
            {
                "id": "onboarding",
                "name": "Developer Onboarding",
                "description": "Reduce onboarding time with personalized guidance for new team members.",
                "icon": "users"
            },
            {
                "id": "integrations",
                "name": "Seamless Integrations",
                "description": "Connect with your existing tools like GitHub, GitLab, Jira, and Slack.",
                "icon": "puzzle"
            }
        ]
    }
