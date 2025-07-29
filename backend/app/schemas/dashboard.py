"""
Pydantic schemas for dashboard data
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MetricChange(BaseModel):
    """Represents a metric change with percentage"""
    current: float
    previous: float
    change_percentage: float
    is_positive: bool


class KPIMetrics(BaseModel):
    """Key Performance Indicators"""
    quotes_generated: MetricChange
    total_revenue: MetricChange
    avg_processing_time: MetricChange  # in minutes
    accuracy_rate: MetricChange  # AI prediction accuracy
    conversion_rate: MetricChange  # quotes approved / quotes sent
    
    # Additional metrics
    active_quotes: int
    pending_quotes: int
    avg_quote_value: float


class QuotePipelineStats(BaseModel):
    """Quote pipeline statistics"""
    pending: int
    in_review: int
    approved: int
    rejected: int
    sent: int
    expired: int
    
    total: int
    value_pending: float
    value_approved: float
    value_total: float


class PerformanceMetrics(BaseModel):
    """Performance and accuracy metrics"""
    ai_accuracy_trend: List[Dict[str, Any]]  # [{date, accuracy}, ...]
    processing_time_trend: List[Dict[str, Any]]  # [{date, avg_time}, ...]
    cost_prediction_accuracy: float
    time_prediction_accuracy: float
    
    # Top performing areas
    best_prediction_categories: List[Dict[str, Any]]
    improvement_areas: List[Dict[str, Any]]


class RecentActivity(BaseModel):
    """Recent activity item"""
    id: int
    type: str  # quote_created, quote_approved, file_uploaded, etc.
    title: str
    description: str
    user_name: str
    timestamp: datetime
    related_id: Optional[int] = None  # quote_id, file_id, etc.
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ChartDataPoint(BaseModel):
    """Single data point for charts"""
    label: str
    value: float
    date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class DashboardOverview(BaseModel):
    """Complete dashboard overview"""
    kpis: KPIMetrics
    pipeline: QuotePipelineStats
    recent_activity: List[RecentActivity]
    
    # Quick stats
    quotes_this_month: int
    revenue_this_month: float
    avg_turnaround_time: float  # in hours
    client_satisfaction: Optional[float] = None


class ChartConfig(BaseModel):
    """Chart configuration"""
    chart_type: str  # line, bar, pie, donut
    title: str
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    show_legend: bool = True
    colors: Optional[List[str]] = None


class ChartResponse(BaseModel):
    """Chart data response"""
    config: ChartConfig
    data: List[ChartDataPoint]
    total_points: int
    last_updated: datetime


# Specific chart schemas
class QuotesByStatusChart(BaseModel):
    """Quotes by status chart data"""
    pending: int
    in_review: int
    approved: int
    rejected: int
    sent: int
    expired: int


class RevenueTrendChart(BaseModel):
    """Revenue trend chart data"""
    data_points: List[Dict[str, Any]]  # [{date, revenue, quote_count}, ...]
    total_revenue: float
    growth_rate: float


class ProcessingTimeChart(BaseModel):
    """Processing time trend chart data"""
    data_points: List[Dict[str, Any]]  # [{date, avg_time, quote_count}, ...]
    avg_time: float
    improvement_rate: float


class AIAccuracyChart(BaseModel):
    """AI accuracy trend chart data"""
    data_points: List[Dict[str, Any]]  # [{date, accuracy, predictions_count}, ...]
    current_accuracy: float
    accuracy_trend: str  # improving, declining, stable


class ClientAnalytics(BaseModel):
    """Client-specific analytics"""
    client_id: int
    client_name: str
    total_quotes: int
    total_value: float
    avg_quote_value: float
    approval_rate: float
    avg_turnaround_time: float
    last_quote_date: Optional[datetime] = None


class UserPerformance(BaseModel):
    """User performance analytics"""
    user_id: int
    user_name: str
    quotes_created: int
    avg_accuracy: float
    avg_processing_time: float
    total_revenue_generated: float
    performance_score: float  # calculated score based on multiple factors