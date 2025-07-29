"""
Pydantic schemas for quotes
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from app.database.models import QuoteStatus, PartComplexity


class PartBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    part_number: Optional[str] = Field(None, max_length=100)
    quantity: int = Field(1, gt=0)
    material: Optional[str] = Field(None, max_length=100)
    dimensions: Optional[Dict[str, Any]] = None
    tolerances: Optional[Dict[str, Any]] = None
    surface_finish: Optional[str] = Field(None, max_length=50)
    heat_treatment: Optional[str] = Field(None, max_length=100)
    complexity: Optional[PartComplexity] = PartComplexity.MEDIUM


class PartCreate(PartBase):
    pass


class PartUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    part_number: Optional[str] = Field(None, max_length=100)
    quantity: Optional[int] = Field(None, gt=0)
    material: Optional[str] = Field(None, max_length=100)
    dimensions: Optional[Dict[str, Any]] = None
    tolerances: Optional[Dict[str, Any]] = None
    surface_finish: Optional[str] = Field(None, max_length=50)
    heat_treatment: Optional[str] = Field(None, max_length=100)
    complexity: Optional[PartComplexity] = None


class PartResponse(PartBase):
    id: int
    material_cost: float
    machining_cost: float
    setup_cost: float
    tooling_cost: float
    overhead_cost: float
    total_cost: float
    estimated_cycle_time: float
    estimated_setup_time: float
    confidence_score: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class QuoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    client_id: int = Field(..., gt=0)
    estimated_delivery_days: int = Field(14, gt=0)
    margin_percentage: float = Field(20.0, ge=0, le=100)
    currency: str = Field("USD", max_length=3)


class QuoteCreate(QuoteBase):
    parts: Optional[List[PartCreate]] = []


class QuoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    client_id: Optional[int] = Field(None, gt=0)
    estimated_delivery_days: Optional[int] = Field(None, gt=0)
    margin_percentage: Optional[float] = Field(None, ge=0, le=100)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[QuoteStatus] = None


class ClientInfo(BaseModel):
    id: int
    name: str
    company: str
    email: str
    currency: str
    
    class Config:
        from_attributes = True


class QuoteResponse(QuoteBase):
    id: int
    quote_number: str
    status: QuoteStatus
    total_cost: float
    total_quote_amount: float
    ai_confidence_score: float
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    approved_at: Optional[datetime]
    client: ClientInfo
    parts_count: Optional[int] = 0
    files_count: Optional[int] = 0
    
    class Config:
        from_attributes = True
    
    @validator('parts_count', pre=True, always=True)
    def set_parts_count(cls, v, values):
        return len(values.get('parts', []) if hasattr(values.get('parts', []), '__len__') else 0)
    
    @validator('files_count', pre=True, always=True)
    def set_files_count(cls, v, values):
        return len(values.get('files', []) if hasattr(values.get('files', []), '__len__') else 0)


class QuoteDetailResponse(QuoteResponse):
    parts: List[PartResponse] = []
    
    class Config:
        from_attributes = True


class QuoteListResponse(BaseModel):
    quotes: List[QuoteResponse]
    total: int
    skip: int
    limit: int


class QuoteAnalysisResult(BaseModel):
    quote_id: int
    overall_confidence: float
    total_estimated_cost: float
    total_estimated_time: float
    parts_analysis: List[Dict[str, Any]]
    recommendations: List[str]
    warnings: List[str]


class QuoteExportRequest(BaseModel):
    format: str = Field(..., regex="^(pdf|excel)$")
    include_internal_costs: bool = False
    include_margins: bool = False
    template: Optional[str] = "standard"