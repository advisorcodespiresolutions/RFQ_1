from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.core.auth import get_current_user, require_admin_or_manager
from app.database.database import get_db
from app.database.models import Partner, Feedback, User, Engagement, Analytics as AnalyticsModel

router = APIRouter()

@router.get("/dashboard-overview")
async def get_dashboard_overview(
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get dashboard overview metrics"""
    # Total partners by tier
    tier_counts = db.query(
        Partner.tier,
        func.count(Partner.id).label('count')
    ).group_by(Partner.tier).all()
    
    # Partners by type
    type_counts = db.query(
        Partner.partner_type,
        func.count(Partner.id).label('count')
    ).group_by(Partner.partner_type).all()
    
    # Profile completion status
    complete_profiles = db.query(Partner).filter(Partner.profile_complete == True).count()
    incomplete_profiles = db.query(Partner).filter(Partner.profile_complete == False).count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_feedback = db.query(Feedback).filter(Feedback.created_at >= thirty_days_ago).count()
    recent_profile_updates = db.query(Partner).filter(Partner.last_profile_update >= thirty_days_ago).count()
    
    # Average feedback ratings
    avg_ratings = db.query(
        func.avg(Feedback.overall_rating).label('avg_overall'),
        func.avg(Feedback.communication_rating).label('avg_communication'),
        func.avg(Feedback.technical_competence_rating).label('avg_technical'),
        func.avg(Feedback.delivery_timeliness_rating).label('avg_delivery'),
        func.avg(Feedback.cost_effectiveness_rating).label('avg_cost'),
        func.avg(Feedback.cultural_fit_rating).label('avg_cultural')
    ).first()
    
    return {
        "partner_tiers": [{"tier": tier, "count": count} for tier, count in tier_counts],
        "partner_types": [{"type": ptype, "count": count} for ptype, count in type_counts],
        "profile_completion": {
            "complete": complete_profiles,
            "incomplete": incomplete_profiles,
            "completion_rate": round(complete_profiles / (complete_profiles + incomplete_profiles) * 100, 1) if (complete_profiles + incomplete_profiles) > 0 else 0
        },
        "recent_activity": {
            "feedback_submitted": recent_feedback,
            "profiles_updated": recent_profile_updates
        },
        "average_ratings": {
            "overall": round(avg_ratings.avg_overall or 0, 2),
            "communication": round(avg_ratings.avg_communication or 0, 2),
            "technical": round(avg_ratings.avg_technical or 0, 2),
            "delivery": round(avg_ratings.avg_delivery or 0, 2),
            "cost": round(avg_ratings.avg_cost or 0, 2),
            "cultural": round(avg_ratings.avg_cultural or 0, 2)
        }
    }

@router.get("/partner-performance")
async def get_partner_performance(
    partner_id: int = None,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get partner performance metrics"""
    query = db.query(Partner)
    if partner_id:
        query = query.filter(Partner.id == partner_id)
    
    partners = query.all()
    performance_data = []
    
    for partner in partners:
        # Get feedback for this partner
        feedback_list = db.query(Feedback).filter(Feedback.partner_id == partner.id).all()
        
        if feedback_list:
            # Calculate metrics
            total_feedback = len(feedback_list)
            avg_overall = sum(f.overall_rating or 0 for f in feedback_list) / total_feedback
            
            # Recent vs older feedback comparison
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            recent_feedback = [f for f in feedback_list if f.created_at >= six_months_ago]
            older_feedback = [f for f in feedback_list if f.created_at < six_months_ago]
            
            recent_avg = sum(f.overall_rating or 0 for f in recent_feedback) / len(recent_feedback) if recent_feedback else 0
            older_avg = sum(f.overall_rating or 0 for f in older_feedback) / len(older_feedback) if older_feedback else 0
            
            # Determine trend
            if recent_feedback and older_feedback:
                if recent_avg > older_avg + 0.5:
                    trend = "improving"
                elif recent_avg < older_avg - 0.5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            performance_data.append({
                "partner_id": partner.id,
                "partner_name": partner.company_name,
                "tier": partner.tier,
                "total_feedback": total_feedback,
                "average_rating": round(avg_overall, 2),
                "recent_feedback_count": len(recent_feedback),
                "trend": trend,
                "profile_complete": partner.profile_complete
            })
        else:
            performance_data.append({
                "partner_id": partner.id,
                "partner_name": partner.company_name,
                "tier": partner.tier,
                "total_feedback": 0,
                "average_rating": 0,
                "recent_feedback_count": 0,
                "trend": "no_data",
                "profile_complete": partner.profile_complete
            })
    
    return performance_data

@router.get("/feedback-trends")
async def get_feedback_trends(
    months: int = 12,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get feedback trends over time"""
    trends = []
    
    for i in range(months):
        month_start = datetime.utcnow() - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        # Get feedback for this month
        month_feedback = db.query(Feedback).filter(
            and_(Feedback.created_at >= month_start, Feedback.created_at < month_end)
        ).all()
        
        if month_feedback:
            avg_rating = sum(f.overall_rating or 0 for f in month_feedback) / len(month_feedback)
            trends.append({
                "month": month_start.strftime("%Y-%m"),
                "feedback_count": len(month_feedback),
                "average_rating": round(avg_rating, 2),
                "unique_partners": len(set(f.partner_id for f in month_feedback))
            })
        else:
            trends.append({
                "month": month_start.strftime("%Y-%m"),
                "feedback_count": 0,
                "average_rating": 0,
                "unique_partners": 0
            })
    
    return list(reversed(trends))  # Return in chronological order

@router.get("/top-performers")
async def get_top_performers(
    limit: int = 10,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get top performing partners"""
    # Get partners with their average ratings
    partner_ratings = db.query(
        Partner.id,
        Partner.company_name,
        Partner.tier,
        func.avg(Feedback.overall_rating).label('avg_rating'),
        func.count(Feedback.id).label('feedback_count')
    ).join(Feedback, Partner.id == Feedback.partner_id).group_by(Partner.id).having(
        func.count(Feedback.id) >= 3  # Minimum 3 feedback entries
    ).order_by(func.avg(Feedback.overall_rating).desc()).limit(limit).all()
    
    return [
        {
            "partner_id": partner.id,
            "partner_name": partner.company_name,
            "tier": partner.tier,
            "average_rating": round(partner.avg_rating, 2),
            "feedback_count": partner.feedback_count
        }
        for partner in partner_ratings
    ]

@router.get("/risk-alerts")
async def get_risk_alerts(
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get partners with potential risk indicators"""
    alerts = []
    
    # Partners with low ratings (below 6.0) and recent feedback
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    low_rated_partners = db.query(
        Partner.id,
        Partner.company_name,
        Partner.tier,
        func.avg(Feedback.overall_rating).label('avg_rating'),
        func.count(Feedback.id).label('feedback_count')
    ).join(Feedback, Partner.id == Feedback.partner_id).filter(
        Feedback.created_at >= six_months_ago
    ).group_by(Partner.id).having(
        and_(
            func.avg(Feedback.overall_rating) < 6.0,
            func.count(Feedback.id) >= 2
        )
    ).all()
    
    for partner in low_rated_partners:
        alerts.append({
            "partner_id": partner.id,
            "partner_name": partner.company_name,
            "tier": partner.tier,
            "alert_type": "low_rating",
            "severity": "high" if partner.avg_rating < 4.0 else "medium",
            "details": f"Average rating: {round(partner.avg_rating, 2)} from {partner.feedback_count} recent feedback"
        })
    
    # Partners with incomplete profiles
    incomplete_partners = db.query(Partner).filter(Partner.profile_complete == False).all()
    for partner in incomplete_partners:
        alerts.append({
            "partner_id": partner.id,
            "partner_name": partner.company_name,
            "tier": partner.tier,
            "alert_type": "incomplete_profile",
            "severity": "medium",
            "details": "Profile incomplete - missing required information"
        })
    
    # Partners with no recent activity
    three_months_ago = datetime.utcnow() - timedelta(days=90)
    inactive_partners = db.query(Partner).filter(
        or_(
            Partner.last_profile_update < three_months_ago,
            Partner.last_profile_update.is_(None)
        )
    ).all()
    
    for partner in inactive_partners:
        alerts.append({
            "partner_id": partner.id,
            "partner_name": partner.company_name,
            "tier": partner.tier,
            "alert_type": "inactive",
            "severity": "low",
            "details": "No profile updates in the last 3 months"
        })
    
    return alerts

@router.get("/export-data")
async def export_data(
    format: str = "json",
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Export partner and feedback data"""
    # Get all partners with their feedback
    partners = db.query(Partner).all()
    
    export_data = []
    for partner in partners:
        feedback_list = db.query(Feedback).filter(Feedback.partner_id == partner.id).all()
        
        partner_data = {
            "partner": {
                "id": partner.id,
                "company_name": partner.company_name,
                "tier": partner.tier.value,
                "partner_type": partner.partner_type.value,
                "profile_complete": partner.profile_complete,
                "created_at": partner.created_at.isoformat() if partner.created_at else None,
                "last_updated": partner.last_profile_update.isoformat() if partner.last_profile_update else None
            },
            "feedback": [
                {
                    "id": f.id,
                    "overall_rating": f.overall_rating,
                    "communication_rating": f.communication_rating,
                    "technical_rating": f.technical_competence_rating,
                    "delivery_rating": f.delivery_timeliness_rating,
                    "cost_rating": f.cost_effectiveness_rating,
                    "cultural_rating": f.cultural_fit_rating,
                    "project_name": f.project_name,
                    "created_at": f.created_at.isoformat() if f.created_at else None
                }
                for f in feedback_list
            ]
        }
        export_data.append(partner_data)
    
    return {
        "export_date": datetime.utcnow().isoformat(),
        "total_partners": len(partners),
        "data": export_data
    }