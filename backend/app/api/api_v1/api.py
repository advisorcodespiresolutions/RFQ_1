"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    quotes, parts, files, auth, dashboard, 
    clients, users, analytics, settings
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
api_router.include_router(parts.router, prefix="/parts", tags=["parts"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])