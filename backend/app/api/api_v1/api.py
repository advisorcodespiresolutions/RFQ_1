"""
Main API Router for Version 1

This module aggregates all API endpoints into a single router that can be
included in the FastAPI application. It organizes endpoints by functional
area and provides a clear structure for the API.

The router includes endpoints for:
- Authentication and user management
- Quote and part management  
- File upload and processing
- Dashboard and analytics
- AI feedback and learning system
- System notifications and alerts
- Multi-dimensional analysis

Each endpoint group is properly tagged and documented for API documentation.
"""

from fastapi import APIRouter

# Import all endpoint modules
from app.api.api_v1.endpoints import (
    auth, quotes, parts, files, dashboard, 
    clients, users, analytics, settings,
    notifications, feedback
)

# Create the main API router for version 1
api_router = APIRouter()

# Authentication endpoints - handles user login, registration, token management
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["authentication"],
    responses={
        401: {"description": "Authentication failed"},
        403: {"description": "Access forbidden"}
    }
)

# Quote management endpoints - core business logic for RFQ processing
api_router.include_router(
    quotes.router, 
    prefix="/quotes", 
    tags=["quotes"],
    responses={
        404: {"description": "Quote not found"},
        400: {"description": "Invalid quote data"}
    }
)

# Part management endpoints - handles individual part data and analysis
api_router.include_router(
    parts.router, 
    prefix="/parts", 
    tags=["parts"],
    responses={
        404: {"description": "Part not found"}
    }
)

# File management endpoints - handles drawing uploads and AI processing
api_router.include_router(
    files.router, 
    prefix="/files", 
    tags=["files"],
    responses={
        413: {"description": "File too large"},
        415: {"description": "Unsupported file type"}
    }
)

# Dashboard and reporting endpoints - provides business intelligence and KPIs
api_router.include_router(
    dashboard.router, 
    prefix="/dashboard", 
    tags=["dashboard"],
    responses={
        500: {"description": "Dashboard data unavailable"}
    }
)

# Client management endpoints - handles customer information and relationships
api_router.include_router(
    clients.router, 
    prefix="/clients", 
    tags=["clients"],
    responses={
        404: {"description": "Client not found"}
    }
)

# User management endpoints - handles user accounts and permissions
api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["users"],
    responses={
        403: {"description": "Insufficient permissions"}
    }
)

# Analytics endpoints - provides detailed analysis and reporting capabilities
api_router.include_router(
    analytics.router, 
    prefix="/analytics", 
    tags=["analytics"],
    responses={
        400: {"description": "Invalid analytics parameters"}
    }
)

# System settings endpoints - handles application configuration
api_router.include_router(
    settings.router, 
    prefix="/settings", 
    tags=["settings"],
    responses={
        403: {"description": "Admin access required"}
    }
)

# Notifications and alerts endpoints - handles system alerts and quote journey tracking
api_router.include_router(
    notifications.router, 
    prefix="/notifications", 
    tags=["notifications"],
    responses={
        404: {"description": "Notification not found"}
    }
)

# Feedback learning endpoints - handles AI model improvement through user feedback
# This is a critical component for continuous learning and model refinement
api_router.include_router(
    feedback.router, 
    prefix="/feedback", 
    tags=["feedback-learning"],
    responses={
        400: {"description": "Invalid feedback data"},
        500: {"description": "Learning system error"}
    }
)