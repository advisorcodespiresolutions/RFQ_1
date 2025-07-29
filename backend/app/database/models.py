"""
Database models for the RFQ platform
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, 
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database.database import Base


class QuoteStatus(str, enum.Enum):
    """Quote status enumeration"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"
    EXPIRED = "expired"


class PartComplexity(str, enum.Enum):
    """Part complexity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MachiningProcess(str, enum.Enum):
    """Machining process enumeration"""
    CNC_MILLING = "cnc_milling"
    CNC_TURNING = "cnc_turning"
    EDM = "edm"
    GRINDING = "grinding"
    DRILLING = "drilling"
    LASER_CUTTING = "laser_cutting"
    WATERJET = "waterjet"
    MANUAL = "manual"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    role = Column(String(50), default="estimator")  # estimator, admin, client_viewer
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    quotes = relationship("Quote", back_populates="created_by_user")


class Client(Base):
    """Client/Customer model"""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    company = Column(String(200), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    country = Column(String(50), default="US")
    currency = Column(String(3), default="USD")
    tax_rate = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    quotes = relationship("Quote", back_populates="client")


class Quote(Base):
    """Main quote model"""
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Status and timing
    status = Column(SQLEnum(QuoteStatus), default=QuoteStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    
    # Financial
    total_cost = Column(Float, default=0.0)
    total_quote_amount = Column(Float, default=0.0)
    margin_percentage = Column(Float, default=20.0)
    currency = Column(String(3), default="USD")
    
    # Processing
    estimated_delivery_days = Column(Integer, default=14)
    actual_delivery_days = Column(Integer)
    ai_confidence_score = Column(Float, default=0.0)
    
    # Relationships
    client_id = Column(Integer, ForeignKey("clients.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    
    client = relationship("Client", back_populates="quotes")
    created_by_user = relationship("User", back_populates="quotes")
    parts = relationship("Part", back_populates="quote", cascade="all, delete-orphan")
    files = relationship("QuoteFile", back_populates="quote", cascade="all, delete-orphan")


class Part(Base):
    """Individual part within a quote"""
    __tablename__ = "parts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    part_number = Column(String(100))
    quantity = Column(Integer, default=1)
    
    # Dimensions and specifications
    material = Column(String(100))
    dimensions = Column(JSON)  # Store as JSON: {"length": 100, "width": 50, "height": 25}
    tolerances = Column(JSON)  # Store tolerance data
    surface_finish = Column(String(50))
    heat_treatment = Column(String(100))
    
    # Complexity and classification
    complexity = Column(SQLEnum(PartComplexity), default=PartComplexity.MEDIUM)
    machining_processes = Column(JSON)  # List of required processes
    
    # Cost breakdown
    material_cost = Column(Float, default=0.0)
    machining_cost = Column(Float, default=0.0)
    setup_cost = Column(Float, default=0.0)
    tooling_cost = Column(Float, default=0.0)
    overhead_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # Time estimates
    estimated_cycle_time = Column(Float, default=0.0)  # minutes
    estimated_setup_time = Column(Float, default=0.0)  # minutes
    actual_cycle_time = Column(Float)  # minutes - for feedback
    actual_setup_time = Column(Float)  # minutes - for feedback
    
    # AI analysis results
    ai_analysis = Column(JSON)  # Store AI analysis results
    confidence_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    quote = relationship("Quote", back_populates="parts")
    analyses = relationship("PartAnalysis", back_populates="part", cascade="all, delete-orphan")


class QuoteFile(Base):
    """Files associated with a quote (drawings, documents, etc.)"""
    __tablename__ = "quote_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100))
    
    # File processing status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text)
    
    # Extracted metadata
    extracted_data = Column(JSON)
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    quote = relationship("Quote", back_populates="files")


class PartAnalysis(Base):
    """AI analysis results for parts"""
    __tablename__ = "part_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(50), nullable=False)  # dimension_extraction, process_prediction, cost_estimation
    
    # Analysis results
    input_data = Column(JSON)
    output_data = Column(JSON)
    confidence_score = Column(Float, default=0.0)
    processing_time = Column(Float, default=0.0)  # seconds
    
    # Model information
    model_version = Column(String(50))
    model_parameters = Column(JSON)
    
    # Feedback data
    human_verified = Column(Boolean, default=False)
    feedback_score = Column(Float)  # 1-5 rating
    feedback_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_at = Column(DateTime(timezone=True))
    
    # Relationships
    part_id = Column(Integer, ForeignKey("parts.id"))
    part = relationship("Part", back_populates="analyses")


class SystemSettings(Base):
    """System-wide settings and parameters"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String(50), default="general")
    is_public = Column(Boolean, default=False)  # Whether setting is visible to non-admin users
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    """Audit log for tracking changes and actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer)
    changes = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")