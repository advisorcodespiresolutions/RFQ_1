from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from app.core.auth import get_current_user, require_admin_or_manager
from app.database.database import get_db
from app.database.models import Feedback as FeedbackModel, Partner, User
from app.schemas.feedback import Feedback, FeedbackCreate, FeedbackUpdate, FeedbackSummary, FeedbackAnalytics

router = APIRouter()

@router.post("/", response_model=Feedback)
async def create_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Submit feedback for a partner"""
    # Verify partner exists
    partner = db.query(Partner).filter(Partner.id == feedback_data.partner_id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner not found"
        )
    
    # Create feedback
    db_feedback = FeedbackModel(
        **feedback_data.dict(),
        reviewer_id=current_user.id
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return Feedback.from_orm(db_feedback)

@router.get("/", response_model=List[Feedback])
async def get_feedback(
    partner_id: Optional[int] = None,
    reviewer_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get feedback with optional filtering"""
    query = db.query(FeedbackModel)
    
    if partner_id:
        query = query.filter(FeedbackModel.partner_id == partner_id)
    if reviewer_id:
        query = query.filter(FeedbackModel.reviewer_id == reviewer_id)
    
    # Non-admin users can only see their own feedback
    if current_user.role != "admin" and current_user.role != "super_admin":
        query = query.filter(FeedbackModel.reviewer_id == current_user.id)
    
    feedback_list = query.offset(skip).limit(limit).all()
    return [Feedback.from_orm(feedback) for feedback in feedback_list]

@router.get("/{feedback_id}", response_model=Feedback)
async def get_feedback_detail(
    feedback_id: int,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get specific feedback details"""
    feedback = db.query(FeedbackModel).filter(FeedbackModel.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Check access permissions
    if (current_user.role not in ["admin", "super_admin"] and 
        feedback.reviewer_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return Feedback.from_orm(feedback)

@router.put("/{feedback_id}", response_model=Feedback)
async def update_feedback(
    feedback_id: int,
    feedback_data: FeedbackUpdate,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Update feedback (only by original reviewer or admin)"""
    feedback = db.query(FeedbackModel).filter(FeedbackModel.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Check access permissions
    if (current_user.role not in ["admin", "super_admin"] and 
        feedback.reviewer_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update fields
    update_data = feedback_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feedback, field, value)
    
    feedback.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(feedback)
    
    return Feedback.from_orm(feedback)

@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Delete feedback (admin only)"""
    feedback = db.query(FeedbackModel).filter(FeedbackModel.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    db.delete(feedback)
    db.commit()
    
    return {"message": "Feedback deleted successfully"}

@router.get("/partner/{partner_id}/summary", response_model=FeedbackSummary)
async def get_partner_feedback_summary(
    partner_id: int,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get feedback summary for a specific partner"""
    # Verify partner exists
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner not found"
        )
    
    # Get all feedback for this partner
    feedback_list = db.query(FeedbackModel).filter(FeedbackModel.partner_id == partner_id).all()
    
    if not feedback_list:
        return FeedbackSummary(
            partner_id=partner_id,
            partner_name=partner.company_name,
            total_feedback_count=0,
            average_overall_rating=0.0,
            average_communication_rating=0.0,
            average_delivery_timeliness_rating=0.0,
            average_technical_competence_rating=0.0,
            average_cost_effectiveness_rating=0.0,
            average_cultural_fit_rating=0.0,
            recent_feedback_count=0
        )
    
    # Calculate averages
    total_count = len(feedback_list)
    avg_overall = sum(f.overall_rating or 0 for f in feedback_list) / total_count
    avg_communication = sum(f.communication_rating or 0 for f in feedback_list) / total_count
    avg_delivery = sum(f.delivery_timeliness_rating or 0 for f in feedback_list) / total_count
    avg_technical = sum(f.technical_competence_rating or 0 for f in feedback_list) / total_count
    avg_cost = sum(f.cost_effectiveness_rating or 0 for f in feedback_list) / total_count
    avg_cultural = sum(f.cultural_fit_rating or 0 for f in feedback_list) / total_count
    
    # Count recent feedback (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    recent_count = len([f for f in feedback_list if f.created_at >= six_months_ago])
    
    # Determine trend (simplified - could be more sophisticated)
    recent_feedback = [f for f in feedback_list if f.created_at >= six_months_ago]
    older_feedback = [f for f in feedback_list if f.created_at < six_months_ago]
    
    if recent_feedback and older_feedback:
        recent_avg = sum(f.overall_rating or 0 for f in recent_feedback) / len(recent_feedback)
        older_avg = sum(f.overall_rating or 0 for f in older_feedback) / len(older_feedback)
        if recent_avg > older_avg + 0.5:
            trend = "improving"
        elif recent_avg < older_avg - 0.5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = None
    
    return FeedbackSummary(
        partner_id=partner_id,
        partner_name=partner.company_name,
        total_feedback_count=total_count,
        average_overall_rating=round(avg_overall, 2),
        average_communication_rating=round(avg_communication, 2),
        average_delivery_timeliness_rating=round(avg_delivery, 2),
        average_technical_competence_rating=round(avg_technical, 2),
        average_cost_effectiveness_rating=round(avg_cost, 2),
        average_cultural_fit_rating=round(avg_cultural, 2),
        recent_feedback_count=recent_count,
        improvement_trend=trend
    )

@router.get("/analytics/overview", response_model=FeedbackAnalytics)
async def get_feedback_analytics(
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get overall feedback analytics"""
    # Get all feedback
    feedback_list = db.query(FeedbackModel).all()
    
    if not feedback_list:
        return FeedbackAnalytics(
            total_feedback=0,
            average_rating=0.0,
            rating_distribution={},
            top_strengths=[],
            common_improvement_areas=[],
            feedback_trend=[]
        )
    
    # Calculate basic metrics
    total_feedback = len(feedback_list)
    avg_rating = sum(f.overall_rating or 0 for f in feedback_list) / total_feedback
    
    # Rating distribution
    rating_dist = {}
    for i in range(1, 11):
        rating_dist[str(i)] = len([f for f in feedback_list if f.overall_rating == i])
    
    # Extract strengths and improvement areas (simplified)
    all_strengths = []
    all_improvements = []
    
    for feedback in feedback_list:
        if feedback.strengths:
            all_strengths.extend(feedback.strengths.split(','))
        if feedback.areas_for_improvement:
            all_improvements.extend(feedback.areas_for_improvement.split(','))
    
    # Get most common (simplified approach)
    from collections import Counter
    top_strengths = [item.strip() for item, count in Counter(all_strengths).most_common(5)]
    common_improvements = [item.strip() for item, count in Counter(all_improvements).most_common(5)]
    
    # Monthly trend (last 12 months)
    trend_data = []
    for i in range(12):
        month_start = datetime.utcnow() - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        month_feedback = [f for f in feedback_list if month_start <= f.created_at < month_end]
        if month_feedback:
            avg_month_rating = sum(f.overall_rating or 0 for f in month_feedback) / len(month_feedback)
            trend_data.append({
                "month": month_start.strftime("%Y-%m"),
                "count": len(month_feedback),
                "average_rating": round(avg_month_rating, 2)
            })
    
    return FeedbackAnalytics(
        total_feedback=total_feedback,
        average_rating=round(avg_rating, 2),
        rating_distribution=rating_dist,
        top_strengths=top_strengths,
        common_improvement_areas=common_improvements,
        feedback_trend=trend_data
    )