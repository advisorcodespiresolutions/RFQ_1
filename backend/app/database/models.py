"""
Database models for the RFQ platform
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    IT_MANAGER = "it_manager"
    VENDOR = "vendor"

class PartnerTier(str, enum.Enum):
    TIER_1_STRATEGIC = "tier_1_strategic"
    TIER_2_PREFERRED = "tier_2_preferred"
    TIER_3_NICHE = "tier_3_niche"

class PartnerType(str, enum.Enum):
    STAFFING = "staffing"
    SOW = "sow"
    NEARSHORE = "nearshore"
    OFFSHORE = "offshore"
    NICHE = "niche"
    SPECIALIZED = "specialized"

class ServiceModel(str, enum.Enum):
    TIME_AND_MATERIALS = "time_and_materials"
    FIXED_FEE = "fixed_fee"
    AGILE_TEAMS = "agile_teams"
    MANAGED_SERVICES = "managed_services"

# Association tables for many-to-many relationships
partner_regions = Table(
    'partner_regions',
    Base.metadata,
    Column('partner_id', Integer, ForeignKey('partners.id')),
    Column('region_id', Integer, ForeignKey('regions.id'))
)

partner_capabilities = Table(
    'partner_capabilities',
    Base.metadata,
    Column('partner_id', Integer, ForeignKey('partners.id')),
    Column('capability_id', Integer, ForeignKey('capabilities.id'))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    feedback_given = relationship("Feedback", back_populates="reviewer", foreign_keys="Feedback.reviewer_id")
    partner = relationship("Partner", back_populates="user", uselist=False)

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)

class Capability(Base):
    __tablename__ = "capabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g., "Technology", "Domain", "Tool"
    description = Column(Text)

class Partner(Base):
    __tablename__ = "partners"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    company_name = Column(String, nullable=False)
    tier = Column(Enum(PartnerTier), nullable=False)
    partner_type = Column(Enum(PartnerType), nullable=False)
    website = Column(String)
    description = Column(Text)
    founded_year = Column(Integer)
    employee_count = Column(Integer)
    annual_revenue = Column(String)  # Range like "10M-50M"
    
    # Contact Information
    primary_contact_name = Column(String)
    primary_contact_email = Column(String)
    primary_contact_phone = Column(String)
    
    # Service Information
    service_models = Column(JSON)  # List of ServiceModel enums
    certifications = Column(JSON)  # List of certification names
    compliance_info = Column(JSON)  # SOC2, ISO, etc.
    
    # Profile Status
    profile_complete = Column(Boolean, default=False)
    last_profile_update = Column(DateTime(timezone=True))
    profile_version = Column(Integer, default=1)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="partner")
    regions = relationship("Region", secondary=partner_regions, back_populates="partners")
    capabilities = relationship("Capability", secondary=partner_capabilities, back_populates="partners")
    feedback_received = relationship("Feedback", back_populates="partner", foreign_keys="Feedback.partner_id")
    case_studies = relationship("CaseStudy", back_populates="partner")
    documents = relationship("Document", back_populates="partner")

class CaseStudy(Base):
    __tablename__ = "case_studies"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    industry = Column(String)
    duration_months = Column(Integer)
    team_size = Column(Integer)
    technologies_used = Column(JSON)
    outcomes = Column(Text)
    client_name = Column(String)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    file_type = Column(String)
    document_type = Column(String)  # "case_study", "certification", "profile", etc.
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    project_name = Column(String)
    project_duration = Column(String)
    
    # Ratings (1-10 scale)
    communication_rating = Column(Integer)
    delivery_timeliness_rating = Column(Integer)
    technical_competence_rating = Column(Integer)
    cost_effectiveness_rating = Column(Integer)
    cultural_fit_rating = Column(Integer)
    overall_rating = Column(Integer)
    
    # Comments
    strengths = Column(Text)
    areas_for_improvement = Column(Text)
    additional_comments = Column(Text)
    
    # Metadata
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    partner = relationship("Partner", back_populates="feedback_received", foreign_keys=[partner_id])
    reviewer = relationship("User", back_populates="feedback_given", foreign_keys=[reviewer_id])

class Engagement(Base):
    __tablename__ = "engagements"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    project_name = Column(String, nullable=False)
    project_type = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String)  # "active", "completed", "cancelled"
    value = Column(Float)
    currency = Column(String, default="USD")
    description = Column(Text)
    outcomes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float)
    metric_data = Column(JSON)
    date_recorded = Column(DateTime(timezone=True), server_default=func.now())
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

# Add back_populates to complete relationships
Region.partners = relationship("Partner", secondary=partner_regions, back_populates="regions")
Capability.partners = relationship("Partner", secondary=partner_capabilities, back_populates="capabilities")
Partner.case_studies = relationship("CaseStudy", back_populates="partner")
Partner.documents = relationship("Document", back_populates="partner")