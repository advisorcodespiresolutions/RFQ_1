"""
Application configuration settings
"""

import os
from typing import Optional, List
from decouple import config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Bayer IT Partner Ecosystem Portal"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/bayer_partner_ecosystem"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Azure AD (Bayer SSO)
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://bayer-partner-portal.azurewebsites.net"
    ]
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".pptx", ".jpg", ".png"]
    
    # Email (for vendor notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Analytics
    ENABLE_ANALYTICS: bool = True
    ANALYTICS_RETENTION_DAYS: int = 365
    
    class Config:
        env_file = ".env"

settings = Settings()