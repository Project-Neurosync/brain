"""
Routes package for NeuroSync API
Contains all API endpoints organized by feature
"""

# Import all routers to make them available for main.py
from routes.auth import router as auth_router
from routes.marketing import router as marketing_router
