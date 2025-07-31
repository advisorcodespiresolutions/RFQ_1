from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.database.models import PartnerTier, PartnerType, ServiceModel

class RegionBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class Region(RegionBase):
    id: int

    class Config:
        from_attributes = True

class CapabilityBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None

class Capability(CapabilityBase):
    id: int

    class Config:
        from_attributes = True

class PartnerBase(BaseModel):
    company_name: str
    tier: PartnerTier
    partner_type: PartnerType
    website: Optional[HttpUrl] = None
    description: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    service_models: Optional[List[ServiceModel]] = None
    certifications: Optional[List[str]] = None
    compliance_info: Optional[Dict[str, Any]] = None

class PartnerCreate(PartnerBase):
    user_id: int
    region_ids: Optional[List[int]] = None
    capability_ids: Optional[List[int]] = None

class PartnerUpdate(BaseModel):
    company_name: Optional[str] = None
    tier: Optional[PartnerTier] = None
    partner_type: Optional[PartnerType] = None
    website: Optional[HttpUrl] = None
    description: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    service_models: Optional[List[ServiceModel]] = None
    certifications: Optional[List[str]] = None
    compliance_info: Optional[Dict[str, Any]] = None
    region_ids: Optional[List[int]] = None
    capability_ids: Optional[List[int]] = None

class Partner(PartnerBase):
    id: int
    user_id: int
    profile_complete: bool
    last_profile_update: Optional[datetime] = None
    profile_version: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    regions: List[Region] = []
    capabilities: List[Capability] = []

    class Config:
        from_attributes = True

class PartnerList(BaseModel):
    id: int
    company_name: str
    tier: PartnerTier
    partner_type: PartnerType
    website: Optional[HttpUrl] = None
    description: Optional[str] = None
    profile_complete: bool
    regions: List[Region] = []
    capabilities: List[Capability] = []

    class Config:
        from_attributes = True

class PartnerFilter(BaseModel):
    tier: Optional[PartnerTier] = None
    partner_type: Optional[PartnerType] = None
    region_ids: Optional[List[int]] = None
    capability_ids: Optional[List[int]] = None
    service_models: Optional[List[ServiceModel]] = None
    search: Optional[str] = None
    profile_complete: Optional[bool] = None