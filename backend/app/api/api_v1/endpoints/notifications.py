"""
Notifications and Alerts API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.notification_service import (
    NotificationService, QuoteJourneyTracker, AlertType, AlertCategory, QuoteJourneyPhase
)
from app.core.deps import get_current_user
from app.database.models import User

router = APIRouter()


@router.get("/alerts")
async def get_alerts(
    user_id: Optional[int] = Query(None),
    alert_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active alerts for the current user"""
    notification_service = NotificationService(db)
    
    # Use current user's ID if not admin
    target_user_id = user_id if current_user.is_admin else current_user.id
    
    alerts = notification_service.get_active_alerts(target_user_id)
    
    # Filter by type and category if specified
    if alert_type:
        alerts = [a for a in alerts if a["type"] == alert_type]
    if category:
        alerts = [a for a in alerts if a["category"] == category]
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "counts": notification_service.get_alert_counts(target_user_id)
    }


@router.post("/alerts")
async def create_alert(
    title: str,
    message: str,
    alert_type: str,
    category: str,
    quote_id: Optional[int] = None,
    target_user_id: Optional[int] = None,
    auto_dismiss_after: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new alert"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create alerts"
        )
    
    notification_service = NotificationService(db)
    
    try:
        alert_type_enum = AlertType(alert_type)
        category_enum = AlertCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert type or category"
        )
    
    alert = await notification_service.create_alert(
        title=title,
        message=message,
        alert_type=alert_type_enum,
        category=category_enum,
        quote_id=quote_id,
        user_id=target_user_id,
        auto_dismiss_after=auto_dismiss_after
    )
    
    return alert


@router.delete("/alerts/{alert_id}")
async def dismiss_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dismiss an alert"""
    notification_service = NotificationService(db)
    
    success = notification_service.dismiss_alert(alert_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"message": "Alert dismissed successfully"}


@router.get("/alerts/counts")
async def get_alert_counts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alert counts for dashboard"""
    notification_service = NotificationService(db)
    
    user_id = None if current_user.is_admin else current_user.id
    counts = notification_service.get_alert_counts(user_id)
    
    return counts


@router.get("/quotes/{quote_id}/journey")
async def get_quote_journey(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed quote journey information"""
    notification_service = NotificationService(db)
    journey_tracker = QuoteJourneyTracker(db, notification_service)
    
    journey_info = journey_tracker.get_quote_journey(quote_id)
    
    if "error" in journey_info:
        # Create a mock journey for demonstration
        await journey_tracker.update_quote_phase(
            quote_id=quote_id,
            phase=QuoteJourneyPhase.AI_ANALYSIS_PROCESSING,
            metadata={"confidence": 94.8, "files_processed": 3},
            user_id=current_user.id
        )
        journey_info = journey_tracker.get_quote_journey(quote_id)
    
    return journey_info


@router.post("/quotes/{quote_id}/journey/update")
async def update_quote_journey_phase(
    quote_id: int,
    phase: str,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update quote journey phase"""
    try:
        phase_enum = QuoteJourneyPhase(phase)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phase: {phase}"
        )
    
    notification_service = NotificationService(db)
    journey_tracker = QuoteJourneyTracker(db, notification_service)
    
    await journey_tracker.update_quote_phase(
        quote_id=quote_id,
        phase=phase_enum,
        metadata=metadata,
        user_id=current_user.id
    )
    
    return {"message": f"Quote {quote_id} moved to phase: {phase}"}


@router.get("/quotes/{quote_id}/timeline")
async def get_quote_timeline(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quote timeline with all phase transitions"""
    notification_service = NotificationService(db)
    journey_tracker = QuoteJourneyTracker(db, notification_service)
    
    # For demonstration, create a sample timeline
    sample_timeline = [
        {
            "phase": "created",
            "title": "Quote Created",
            "timestamp": "2024-01-15T10:00:00Z",
            "duration": {"hours": 0, "minutes": 0, "display": "0m"},
            "completed": True,
            "user": "John Doe",
            "metadata": {"initial_files": 2}
        },
        {
            "phase": "files_uploaded",
            "title": "Files Uploaded",
            "timestamp": "2024-01-15T10:15:00Z",
            "duration": {"hours": 0, "minutes": 15, "display": "15m"},
            "completed": True,
            "user": "John Doe",
            "metadata": {"files_count": 3, "total_size": "15.2MB"}
        },
        {
            "phase": "ai_analysis_processing",
            "title": "AI Analysis",
            "timestamp": "2024-01-15T10:30:00Z",
            "duration": {"hours": 0, "minutes": 45, "display": "45m"},
            "completed": True,
            "user": "AI System",
            "metadata": {"confidence": 94.8, "dimensions_extracted": 12}
        },
        {
            "phase": "technical_review",
            "title": "Technical Review",
            "timestamp": "2024-01-15T11:15:00Z",
            "duration": {"hours": 2, "minutes": 30, "display": "2h 30m"},
            "completed": True,
            "user": "Sarah Wilson",
            "metadata": {"review_notes": "Approved with minor adjustments"}
        },
        {
            "phase": "pending_approval",
            "title": "Pending Approval",
            "timestamp": "2024-01-15T13:45:00Z",
            "duration": {"hours": 1, "minutes": 20, "display": "1h 20m"},
            "completed": False,
            "current": True,
            "user": None,
            "metadata": {"assigned_to": "Manager"}
        }
    ]
    
    return {
        "quote_id": quote_id,
        "timeline": sample_timeline,
        "current_phase": "pending_approval",
        "total_duration": {"hours": 4, "minutes": 50, "display": "4h 50m"},
        "sla_status": {
            "status": "on_track",
            "remaining_hours": 42.3,
            "threshold_hours": 48
        }
    }


@router.get("/system/alerts/demo")
async def create_demo_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create demo alerts for demonstration"""
    notification_service = NotificationService(db)
    
    demo_alerts = []
    
    # Create various types of alerts
    alerts_config = [
        {
            "title": "AI Analysis Complete",
            "message": "Quote #QUO-2024-001 analysis completed with 96.2% confidence",
            "type": AlertType.SUCCESS,
            "category": AlertCategory.AI_ANALYSIS,
            "quote_id": 1,
            "auto_dismiss": 15
        },
        {
            "title": "Approval Required",
            "message": "Quote #QUO-2024-002 requires manager approval (Value: $15,450)",
            "type": AlertType.WARNING,
            "category": AlertCategory.APPROVAL,
            "quote_id": 2
        },
        {
            "title": "SLA Violation",
            "message": "Quote #QUO-2024-003 has been in review for 25 hours (SLA: 24h)",
            "type": AlertType.ERROR,
            "category": AlertCategory.DEADLINE,
            "quote_id": 3
        },
        {
            "title": "File Processing Error",
            "message": "Failed to process CAD file 'bracket_v2.step' - Invalid format",
            "type": AlertType.ERROR,
            "category": AlertCategory.FILE_PROCESSING,
            "quote_id": 4
        },
        {
            "title": "New Quote Created",
            "message": "Quote #QUO-2024-005 created by client Aerospace Corp",
            "type": AlertType.INFO,
            "category": AlertCategory.QUOTE_STATUS,
            "quote_id": 5
        },
        {
            "title": "System Maintenance",
            "message": "Scheduled system maintenance will begin at 2:00 AM EST",
            "type": AlertType.INFO,
            "category": AlertCategory.SYSTEM
        },
        {
            "title": "Quality Alert",
            "message": "Quote #QUO-2024-006 flagged for quality review due to tight tolerances",
            "type": AlertType.WARNING,
            "category": AlertCategory.QUALITY,
            "quote_id": 6
        }
    ]
    
    for alert_config in alerts_config:
        alert = await notification_service.create_alert(
            title=alert_config["title"],
            message=alert_config["message"],
            alert_type=alert_config["type"],
            category=alert_config["category"],
            quote_id=alert_config.get("quote_id"),
            user_id=current_user.id,
            auto_dismiss_after=alert_config.get("auto_dismiss")
        )
        demo_alerts.append(alert)
    
    return {
        "message": "Demo alerts created successfully",
        "alerts_created": len(demo_alerts),
        "alerts": demo_alerts
    }


@router.get("/phases")
async def get_available_phases():
    """Get list of all available quote journey phases"""
    phases = []
    
    for phase in QuoteJourneyPhase:
        phases.append({
            "value": phase.value,
            "name": phase.name,
            "title": phase.value.replace("_", " ").title()
        })
    
    return {
        "phases": phases,
        "total": len(phases)
    }


@router.get("/alert-types")
async def get_alert_types():
    """Get list of all available alert types and categories"""
    return {
        "alert_types": [{"value": t.value, "name": t.name} for t in AlertType],
        "categories": [{"value": c.value, "name": c.name} for c in AlertCategory]
    }