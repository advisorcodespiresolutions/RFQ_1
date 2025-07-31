from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class FeedbackBase(BaseModel):
    project_name: Optional[str] = None
    project_duration: Optional[str] = None
    communication_rating: Optional[int] = Field(None, ge=1, le=10)
    delivery_timeliness_rating: Optional[int] = Field(None, ge=1, le=10)
    technical_competence_rating: Optional[int] = Field(None, ge=1, le=10)
    cost_effectiveness_rating: Optional[int] = Field(None, ge=1, le=10)
    cultural_fit_rating: Optional[int] = Field(None, ge=1, le=10)
    overall_rating: Optional[int] = Field(None, ge=1, le=10)
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    additional_comments: Optional[str] = None
    is_anonymous: bool = False

class FeedbackCreate(FeedbackBase):
    partner_id: int

class FeedbackUpdate(BaseModel):
    project_name: Optional[str] = None
    project_duration: Optional[str] = None
    communication_rating: Optional[int] = Field(None, ge=1, le=10)
    delivery_timeliness_rating: Optional[int] = Field(None, ge=1, le=10)
    technical_competence_rating: Optional[int] = Field(None, ge=1, le=10)
    cost_effectiveness_rating: Optional[int] = Field(None, ge=1, le=10)
    cultural_fit_rating: Optional[int] = Field(None, ge=1, le=10)
    overall_rating: Optional[int] = Field(None, ge=1, le=10)
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    additional_comments: Optional[str] = None

class Feedback(FeedbackBase):
    id: int
    partner_id: int
    reviewer_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FeedbackSummary(BaseModel):
    partner_id: int
    partner_name: str
    total_feedback_count: int
    average_overall_rating: float
    average_communication_rating: float
    average_delivery_timeliness_rating: float
    average_technical_competence_rating: float
    average_cost_effectiveness_rating: float
    average_cultural_fit_rating: float
    recent_feedback_count: int  # Last 6 months
    improvement_trend: Optional[str] = None  # "improving", "declining", "stable"

class FeedbackAnalytics(BaseModel):
    total_feedback: int
    average_rating: float
    rating_distribution: dict  # {"1": 5, "2": 10, ...}
    top_strengths: List[str]
    common_improvement_areas: List[str]
    feedback_trend: List[dict]  # Monthly trend data