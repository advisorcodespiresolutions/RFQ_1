"""
Dashboard endpoints for analytics and KPIs
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database.database import get_db
from app.schemas.dashboard import (
    DashboardOverview, KPIMetrics, QuotePipelineStats, 
    PerformanceMetrics, RecentActivity
)
from app.services.dashboard_service import DashboardService
from app.core.deps import get_current_user
from app.database.models import User

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard overview with key metrics
    """
    dashboard_service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    overview = dashboard_service.get_overview(
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return overview


@router.get("/kpis", response_model=KPIMetrics)
async def get_kpi_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get key performance indicators
    """
    dashboard_service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    kpis = dashboard_service.get_kpi_metrics(
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return kpis


@router.get("/pipeline", response_model=QuotePipelineStats)
async def get_pipeline_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get quote pipeline statistics
    """
    dashboard_service = DashboardService(db)
    
    pipeline_stats = dashboard_service.get_pipeline_stats(
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return pipeline_stats


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance metrics including AI accuracy
    """
    dashboard_service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    performance = dashboard_service.get_performance_metrics(
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return performance


@router.get("/recent-activity", response_model=List[RecentActivity])
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent activity feed
    """
    dashboard_service = DashboardService(db)
    
    activities = dashboard_service.get_recent_activity(
        limit=limit,
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return activities


@router.get("/charts/quotes-by-status")
async def get_quotes_by_status_chart(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get data for quotes by status chart
    """
    dashboard_service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    chart_data = dashboard_service.get_quotes_by_status_chart(
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return chart_data


@router.get("/charts/revenue-trend")
async def get_revenue_trend_chart(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get data for revenue trend chart
    """
    dashboard_service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    chart_data = dashboard_service.get_revenue_trend_chart(
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return chart_data


@router.get("/charts/processing-time")
async def get_processing_time_chart(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get data for processing time chart
    """
    dashboard_service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    chart_data = dashboard_service.get_processing_time_chart(
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return chart_data


@router.get("/charts/ai-accuracy")
async def get_ai_accuracy_chart(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get data for AI accuracy trend chart
    """
    dashboard_service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    chart_data = dashboard_service.get_ai_accuracy_chart(
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return chart_data