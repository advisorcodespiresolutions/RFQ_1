"""
Application configuration settings
"""

import os
from typing import Optional, List
from decouple import config


class Settings:
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Manufacturing RFQ Intelligence Platform"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered RFQ workflow management system"
    
    # Security
    SECRET_KEY: str = config("SECRET_KEY", default="your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = config(
        "DATABASE_URL", 
        default="postgresql://rfq_user:rfq_password@localhost/rfq_platform"
    )
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = [
        ".dwg", ".step", ".iges", ".stp", ".igs", 
        ".pdf", ".png", ".jpg", ".jpeg", ".zip"
    ]
    
    # AI/ML Settings
    AI_MODEL_PATH: str = "ai_models/trained"
    CONFIDENCE_THRESHOLD: float = 0.85
    ENABLE_AI_FEEDBACK: bool = True
    
    # Email Configuration
    MAIL_USERNAME: str = config("MAIL_USERNAME", default="")
    MAIL_PASSWORD: str = config("MAIL_PASSWORD", default="")
    MAIL_FROM: str = config("MAIL_FROM", default="noreply@rfqplatform.com")
    MAIL_PORT: int = config("MAIL_PORT", default=587, cast=int)
    MAIL_SERVER: str = config("MAIL_SERVER", default="smtp.gmail.com")
    MAIL_TLS: bool = config("MAIL_TLS", default=True, cast=bool)
    MAIL_SSL: bool = config("MAIL_SSL", default=False, cast=bool)
    
    # External APIs
    CURRENCY_API_KEY: str = config("CURRENCY_API_KEY", default="")
    CURRENCY_API_URL: str = "https://api.exchangerate-api.com/v4/latest"
    
    # Development
    DEBUG: bool = config("DEBUG", default=True, cast=bool)
    TESTING: bool = config("TESTING", default=False, cast=bool)
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8080"
    ]

    # Logging
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
    
    class Config:
        case_sensitive = True


settings = Settings()